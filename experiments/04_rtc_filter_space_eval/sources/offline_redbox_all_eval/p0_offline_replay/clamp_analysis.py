"""실제 rollout(20k sync)의 8° clamp 분석 + 관절별 서보 추종 모델 맞추기. 읽기만 한다. CPU.

clamp 판정: |action − observation.state| > 8 (lerobot 은 보낼 때 Present_Position 을 다시 읽으므로 경고 수 635 와 조금 다름)
분류 (관절별 clamp 구간 = 연속 프레임 run):
  시작 원인  — jump: 시작 프레임의 목표 변화 |dA| ≥ 4°   / lag: 그보다 작은 변화로 오차가 8° 를 넘음
  지속 양상  — moving: 구간 동안 관절이 빠르게 따라감 (|dS| 중앙값 ≥ 1°/프레임)
              stalled: 거의 안 움직이는데 오차 유지 (|dS| 중앙값 < 0.3°/프레임) → 중력·접촉·기구 한계 의심
서보 모델: S[t+1] − S[t] = k·(sent[t−d] − S[t]) + b,  sent = S + clip(A − S, ±8)  (관절별 k, b, d∈{0..3})
          앞 60% 로 맞추고 뒤 40% 를 자유 실행(free-run)으로 검증.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
R = Path.home() / "so101_runs/main/redbox_all/eval/rollouts/20261019_091114_20k_t1_test1/dataset"
df = pd.concat(pd.read_parquet(f) for f in sorted(R.glob("data/*/*.parquet"))).sort_values("index")
A = np.stack(df["action"]).astype(float)
S = np.stack(df["observation.state"]).astype(float)
n = len(A)
LIM = 8.0

# ---------- clamp 구간 분석 ----------
rows = []
for j, name in enumerate(J):
    e = A[:, j] - S[:, j]
    over = np.abs(e) > LIM
    t = 0
    while t < n:
        if not over[t]:
            t += 1
            continue
        s = t
        while t < n and over[t]:
            t += 1
        seg = slice(s, t)
        dA = A[s, j] - A[s - 1, j] if s > 0 else np.nan
        e_prev = e[s - 1] if s > 0 else np.nan
        dS = np.abs(np.diff(S[max(s - 1, 0):t, j]))
        rows.append(dict(joint=name, start=s, frames=t - s, sec=s / 30, chunk_pos=s % 50,
                         target=A[s, j], actual=S[s, j], err=e[s], err_max=np.abs(e[seg]).max(),
                         dA=dA, err_prev=e_prev, dS_median=float(np.median(dS)) if len(dS) else 0.0,
                         direction="up" if e[s] > 0 else "down"))
C = pd.DataFrame(rows)
C["onset"] = np.where(C.dA.abs() >= 4, "jump", "lag")
C["mode"] = np.select([C.dS_median >= 1.0, C.dS_median < 0.3], ["moving", "stalled"], "slow")
C.to_csv(OUT / "clamp_runs.csv", index=False)

summ = {"clamp_frames_any_joint": int((np.abs(A - S) > LIM).any(1).sum()), "frames": n,
        "runs_by_joint": C.groupby("joint").size().to_dict(),
        "frames_by_joint": C.groupby("joint").frames.sum().to_dict(),
        "onset": C.groupby(["joint", "onset"]).size().unstack(fill_value=0).to_dict(orient="index"),
        "mode_frames": C.groupby(["joint", "mode"]).frames.sum().unstack(fill_value=0).to_dict(orient="index"),
        "onset_at_chunk_boundary(pos0-2)": int((C.chunk_pos <= 2).sum()), "runs": len(C),
        "longest_runs": C.sort_values("frames", ascending=False).head(8)[["joint", "sec", "frames", "err_max", "dS_median", "mode", "direction", "target", "actual"]].round(1).to_dict(orient="records")}

# ---------- 서보 모델 ----------
def sent_of(a, s):
    return s + np.clip(a - s, -LIM, LIM)


def fit_joint(a, s, d, lo, hi):
    sent = sent_of(a, s)
    t = np.arange(max(lo, d), hi - 1)
    X = np.stack([sent[t - d] - s[t], np.ones(len(t))], 1)
    y = s[t + 1] - s[t]
    (k, b), *_ = np.linalg.lstsq(X, y, rcond=None)
    return k, b


def free_run(a, s0, k, b, d, lo, hi, s_hist):
    s = s_hist.copy()
    for t in range(lo, hi - 1):
        sent_d = sent_of(a[t - d], s[t - d])
        s[t + 1] = s[t] + k * (sent_d - s[t]) + b
    return s


cut = int(n * 0.6)
model = {}
val = {}
for j, name in enumerate(J):
    best = None
    for d in range(4):
        k, b = fit_joint(A[:, j], S[:, j], d, 0, cut)
        sim = free_run(A[:, j], S[cut, j], k, b, d, cut, n, S[:, j].copy())
        rmse = float(np.sqrt(np.mean((sim[cut:] - S[cut:, j]) ** 2)))
        if best is None or rmse < best[0]:
            best = (rmse, d, k, b, sim)
    rmse, d, k, b, sim = best
    # 기준: '모델 없이 목표값을 그대로 실제값으로 본 경우'의 오차
    naive = float(np.sqrt(np.mean((A[cut:, j] - S[cut:, j]) ** 2)))
    model[name] = dict(k=float(k), b=float(b), d=int(d), val_rmse=rmse, naive_rmse=naive)
    val[name] = sim[cut:]
summ["servo_model"] = model
np.savez_compressed(OUT / "servo_model_val.npz", cut=cut, **{f"sim|{k}": v for k, v in val.items()}, A=A, S=S)
json.dump(summ, open(OUT / "clamp_summary.json", "w"), indent=1, default=float)
print(json.dumps(summ, indent=1, default=float)[:6000])
