"""replay_sim.py 결과(명령 흐름)로 지표·표·그래프를 만든다. CPU. 사용: python3 analyze_runs.py <runs_dir> [tag]

⚠ 열린 루프 재생 결과다. 추종 오차·clamp 는 rollout 데이터로 맞춘 서보 모델(servo_model_v2.json)로 '명령 흐름을 따라갔다면'을
  시뮬레이션한 값이며, 실제 로봇 자세 변화가 다음 관측에 주는 영향은 들어 있지 않다.

후처리 필터 (엔진 출력 → 필터 → robot; RTC 큐·leftover 는 필터 전 값 사용 = PR #3893 위치와 같음)
  ema25   : α=0.25, 관절별 |x − y_prev| > 10 이면 그대로 통과 (PR #3893 기본값)
  ema50   : α=0.5, 리셋 10
  vc_pr   : 프레임당 최대 변화 1.25 (PR #3893 기본값, 모든 관절)
  vc_tel  : 관절별 사람 조작 action |Δ| p99.5 (학습 데이터)
  ema50vc : ema50 → vc_tel
  ema50vc_arm : 팔 5관절만 ema50, 그리퍼는 그대로 → vc_tel
"""

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUNS = Path(sys.argv[1]).resolve()
TAG = sys.argv[2] if len(sys.argv) > 2 else RUNS.name
OUT = RUNS.parent
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
ARM = slice(0, 5)
LIM = 8.0
K9 = np.ones(9) / 9
SERVO = json.load(open(OUT / "servo_model_v2.json"))
SV = [SERVO[k] for k in ["pan", "lift", "elbow", "wflex", "wroll", "grip"]]

# 사람 조작 action 의 관절별 |Δ| p99.5 (vc_tel)
_tel = []
for f in glob.glob(str(Path.home() / "so101_runs/main/redbox_all/dataset/data/*/*.parquet")):
    d = pd.read_parquet(f, columns=["episode_index", "frame_index", "action"]).sort_values(["episode_index", "frame_index"])
    for _, g in d.groupby("episode_index"):
        _tel.append(np.abs(np.diff(np.stack(g["action"]), axis=0)))
VC_TEL = np.percentile(np.concatenate(_tel), 99.5, axis=0)


def ema(x, a, reset=10.0):
    y = x.copy()
    for t in range(1, len(x)):
        if np.isnan(y[t - 1]).any():
            continue
        jump = np.abs(x[t] - y[t - 1]) > reset
        y[t] = np.where(jump, x[t], a * x[t] + (1 - a) * y[t - 1])
    return y


def vclip(x, lim):
    y = x.copy()
    for t in range(1, len(x)):
        if np.isnan(y[t - 1]).any():
            continue
        y[t] = y[t - 1] + np.clip(x[t] - y[t - 1], -lim, lim)
    return y


FILTERS = {"none": lambda x: x, "ema25": lambda x: ema(x, 0.25), "ema50": lambda x: ema(x, 0.5),
           "vc_pr": lambda x: vclip(x, np.full(6, 1.25)), "vc_tel": lambda x: vclip(x, VC_TEL),
           "ema50vc": lambda x: vclip(ema(x, 0.5), VC_TEL),
           "ema50vc_arm": lambda x: vclip(np.concatenate([ema(x, 0.5)[:, :5], x[:, 5:]], 1), VC_TEL)}


def lowpass(x):
    return np.stack([np.convolve(np.pad(x[:, j], 4, mode="edge"), K9, "valid") for j in range(x.shape[1])], 1)


def servo(c, s0):
    """서보 모델 v2 로 명령 c 를 따라가는 관절 상태 시뮬레이션 (8° clamp 포함)."""
    s = np.zeros_like(c); s[0] = s0
    for t in range(len(c) - 1):
        for j in range(6):
            m = SV[j]; d = m["d"]
            td = max(t - d, 0)
            tgt = c[td, j] if not np.isnan(c[td, j]) else s[td, j]
            sent = s[td, j] + np.clip(tgt - s[td, j], -LIM, LIM)
            e = sent - s[t, j]
            k = m["kp"] if e > 0 else m["kn"]
            s[t + 1, j] = s[t, j] + np.clip(k * e, -m["vmax"], m["vmax"])
    return s


def gt_closes(a):
    ev, st = [], 0
    for t in range(len(a)):
        if st == 0 and a[t, 5] > 15: st = 1
        elif st == 1 and a[t, 5] < 8: ev.append(t); st = 0
    return ev


def xcorr_lag(a, b, maxlag=15):
    """b 가 a 보다 몇 프레임 늦는가 (속도 상호상관 최대)."""
    va, vb = np.diff(a, axis=0), np.diff(b, axis=0)
    best, bl = -np.inf, 0
    for L in range(0, maxlag + 1):
        x, y = va[: len(va) - L], vb[L:]
        c = np.nansum(x * y) / (np.sqrt(np.nansum(x * x) * np.nansum(y * y)) + 1e-9)
        if c > best: best, bl = c, L
    return bl


def metrics(c, sw, obs_t, src, base_c=None):
    valid = ~np.isnan(c).any(1)
    first = int(np.argmax(valid))
    c = c.copy(); c[~valid] = c[first]
    m = {}
    # 1) 경계 점프 (switch 틱에서 직전 틱 대비)
    sw = [i for i in sw if i > first and i < len(c)]
    bj = np.array([np.abs(c[i, ARM] - c[i - 1, ARM]).max() for i in sw]) if sw else np.array([0.0])
    m["boundary_max"] = float(bj.max()); m["boundary_gt8"] = int((bj > 8).sum()); m["n_switch"] = len(sw)
    fj = np.abs(np.diff(c[first:, ARM], axis=0)).max(1)
    m["anyframe_gt8"] = int((fj > 8).sum())
    # 2) chunk 안 잡음: 이동평균 잔차, 경계 ±4 제외
    lp = lowpass(c)
    mask = np.ones(len(c), bool); mask[:first + 4] = False; mask[-4:] = False
    for i in sw: mask[max(i - 4, 0):i + 5] = False
    res = (c - lp)[mask]
    m["noise_arm"] = float(res[:, ARM].std(0).mean())
    for j, n in enumerate(J): m[f"noise|{n}"] = float(res[:, j].std())
    # 3) 속도·가속도 (보내는 명령 전체)
    d1 = np.abs(np.diff(c[first:], axis=0)) * 30; d2 = np.abs(np.diff(c[first:], 2, axis=0)) * 900
    for j, n in enumerate(J):
        m[f"vel_p99|{n}"] = float(np.percentile(d1[:, j], 99)); m[f"acc_rms|{n}"] = float(np.sqrt((d2[:, j] ** 2).mean()))
    m["acc_rms_arm"] = float(np.mean([m[f"acc_rms|{n}"] for n in J[:5]]))
    # 4) 필터 지연
    if base_c is not None:
        b = base_c.copy(); b[np.isnan(b).any(1)] = c[first]
        m["lag_frames"] = int(np.median([xcorr_lag(lowpass(b)[first:, j], lp[first:, j]) for j in range(5)]))
    # 5·6) 파지 자세·그리퍼 타이밍 (사람 GT 있는 학습 에피소드만)
    if src["gt"]:
        A = src["action"]; ev = gt_closes(A); pe, dt, miss = [], [], 0
        for tc in ev:
            k = np.where(obs_t == tc)[0]
            if len(k) == 0: continue
            k = int(k[0])
            pe.append(np.abs(lp[k, ARM] - A[tc, ARM]).mean())
            lo, hi = max(k - 45, first), min(k + 45, len(c))
            hit = None
            for q in range(lo, hi):
                if c[q, 5] < 10 and np.nanmax(c[max(q - 30, first):q + 1, 5]) > 15:
                    hit = q; break
            if hit is None: miss += 1
            else: dt.append(hit - k)
        m["grasp_err"] = float(np.mean(pe)) if pe else np.nan; m["n_grasp"] = len(pe)
        m["grip_dt_med"] = float(np.median(dt)) if dt else np.nan; m["grip_abs_dt"] = float(np.mean(np.abs(dt))) if dt else np.nan
        m["grip_miss"] = miss
    # 7) 서보 시뮬레이션: 추종 오차·clamp
    s = servo(c, src["state"][min(obs_t[first], len(src["state"]) - 1)])
    e = np.abs(c - s)[first:]
    m["track_mean_arm"] = float(e[:, ARM].mean()); m["track_p95_lift"] = float(np.percentile(e[:, 1], 95))
    over = (e[:, :] > LIM).any(1); m["clamp_ticks"] = int(over.sum()); m["clamp_pct"] = float(over.mean() * 100)
    near = np.zeros(len(c), bool)
    for i in sw: near[i:i + 6] = True
    m["clamp_near_switch"] = int((over & near[first:]).sum())
    return m, s


def load_run(path):
    z = np.load(path, allow_pickle=True)
    srcs = sorted({k.split("|")[0] for k in z.files})
    return {sn: {k.split("|")[1]: z[k] for k in z.files if k.startswith(sn + "|")} for sn in srcs}


def main():
    srcdata = {}
    for f in glob.glob(str(RUNS / "src_*.npz")):
        sn = Path(f).stem[4:]; z = np.load(f)
        srcdata[sn] = {"action": z["action"], "state": z["state"], "gt": sn.startswith("train")}
    rows, keep = [], {}
    for f in sorted(glob.glob(str(RUNS / "run_*.npz"))):
        name = Path(f).stem[4:]
        meta = json.load(open(str(f).replace(".npz", ".json")))
        run = load_run(f)
        for filt, fn in FILTERS.items():
            agg = {"rollout": [], "train": []}
            for sn, r in run.items():
                c0 = r["cmds"].astype(float)
                c = fn(c0)
                m, s = metrics(c, list(r["switch"].astype(int)), r["obs_t"].astype(int), srcdata[sn], None if filt == "none" else c0)
                m["lat_ms"] = meta["sources"][sn]["lat_ms_median"]; m["hold"] = meta["sources"][sn]["hold_or_starved"]
                m["n_infer"] = meta["sources"][sn]["n_infer"]; m["ticks"] = len(c)
                agg["rollout" if sn.startswith("rollout") else "train"].append(m)
                if sn.startswith("rollout") and filt in ("none", "ema50", "ema50vc", "ema25", "ema50vc_arm"):
                    keep[(name, filt)] = (c, s, r["switch"].astype(int))
            for part, ms in agg.items():
                if not ms: continue
                row = {"config": name, "filter": filt, "part": part}
                tot = sum(x["ticks"] for x in ms)
                for k in ms[0]:
                    vals = [x[k] for x in ms if k in x and not (isinstance(x[k], float) and np.isnan(x[k]))]
                    if not vals: row[k] = np.nan; continue
                    if k in ("boundary_max",): row[k] = max(vals)
                    elif k in ("boundary_gt8", "anyframe_gt8", "n_switch", "clamp_ticks", "clamp_near_switch", "hold", "n_infer", "ticks", "grip_miss", "n_grasp"): row[k] = int(sum(vals))
                    else: row[k] = float(np.average(vals, weights=[x["ticks"] for x in ms if k in x and not (isinstance(x[k], float) and np.isnan(x[k]))]))
                row["clamp_pct"] = 100 * row["clamp_ticks"] / tot; row["hold_pct"] = 100 * row["hold"] / tot
                rows.append(row)
        print("analyzed", name, flush=True)
    T = pd.DataFrame(rows)
    T.to_csv(OUT / f"metrics_{TAG}.csv", index=False)
    # 실측 rollout 에 같은 서보 모델을 적용했을 때 clamp 재현 정도 (모델 검증)
    src = srcdata["rollout_20k_t1"]
    s_real = servo(src["action"], src["state"][0])
    real = {"servo_model_clamp_pct_on_real_actions": float(((np.abs(src["action"] - s_real) > LIM).any(1)).mean() * 100),
            "measured_clamp_pct_on_real": float(((np.abs(src["action"] - src["state"]) > LIM).any(1)).mean() * 100),
            "VC_TEL": VC_TEL.round(2).tolist()}
    json.dump(real, open(OUT / f"servo_check_{TAG}.json", "w"), indent=1)
    np.savez_compressed(OUT / f"keep_{TAG}.npz", **{f"{a}|{b}|{k}": v for (a, b), (c, s, sw) in keep.items() for k, v in (("c", c), ("s", s), ("sw", sw))})
    print(json.dumps(real))


if __name__ == "__main__":
    main()
