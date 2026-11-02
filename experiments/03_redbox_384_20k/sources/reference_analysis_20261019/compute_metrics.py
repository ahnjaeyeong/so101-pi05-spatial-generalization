"""레퍼런스(aswinkumar99 SO101 sponge) vs Redbox 원본 teleop action 품질 비교 — 읽기만 한다.

실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python -I compute_metrics.py
결과 (이 폴더): metrics_groups.csv, metrics_episodes.csv, norm_ranges.csv, task_shift.csv, plotdata.npz

지표는 모두 에피소드 안에서만 계산한다 (에피소드 경계 차분 제외). 두 데이터셋 모두 30 fps.
- d1      : |a[t+1]-a[t]|           (°/프레임)  → ×30 = 속도 °/s
- d2      : |a[t+2]-2a[t+1]+a[t]|   (°/프레임²) → ×900 = 가속도 °/s²
- 방향 반전 : 0 이 아닌 차분의 부호가 바뀌는 점(turning point). 반전 사이의 진폭(swing)으로 나눈다
             micro <0.3° (엔코더 1틱 0.088° 수준) · small 0.3–2° (떨림) · large ≥5° (의도된 방향 전환)
- hf3/hf6 : 속도 신호 파워 중 3 Hz / 6 Hz 이상 비율 (Hann 창 FFT, 에피소드 합)
"""

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
FPS = 30
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
REF = Path.home() / "so101_runs/reference/aswinkumar99_so101_pick_place"
RB = Path.home() / "so101_runs/main"
MIN_LEN = 60  # 2초보다 짧은 에피소드는 제외 (레퍼런스 T2 fixed 에 31프레임짜리 1편)

GROUPS = [
    ("ref", "T1", "known", REF / "task1-single-sponge-no-distractors/fixed-locations"),
    ("ref", "T1", "random", REF / "task1-single-sponge-no-distractors/random-locations"),
    ("ref", "T2", "known", REF / "task2-multiple-sponges-no-distractors/fixed-locations"),
    ("ref", "T2", "random", REF / "task2-multiple-sponges-no-distractors/random-locations"),
    ("ref", "T3", "known", REF / "task3-single-sponge-with-distractors/fixed-locations"),
    ("ref", "T3", "random", REF / "task3-single-sponge-with-distractors/random-locations"),
    ("redbox", "T1", "known", RB / "redbox_t1_known/dataset"),
    ("redbox", "T1", "random", RB / "redbox_t1_random/dataset"),
    ("redbox", "T2", "known", RB / "redbox_t2_known/dataset"),
    ("redbox", "T2", "random", RB / "redbox_t2_random/dataset"),
    ("redbox", "T3", "known", RB / "redbox_t3_known/dataset"),
    ("redbox", "T3", "random", RB / "redbox_t3_random/dataset"),
]


def load(root):
    files = sorted(glob.glob(str(root / "data/*/*.parquet")))
    df = pd.concat(pd.read_parquet(f, columns=["episode_index", "frame_index", "action"]) for f in files)
    return df.sort_values(["episode_index", "frame_index"])


def swings(x):
    """1차원 신호의 방향 반전점 사이 진폭 목록."""
    d = np.diff(x)
    nz = np.nonzero(d)[0]
    if len(nz) < 2:
        return np.array([])
    s = np.sign(d[nz])
    tp = nz[1:][s[1:] != s[:-1]]  # 부호가 바뀐 차분의 시작 인덱스 = 반전점
    pts = np.concatenate([[0], tp, [len(x) - 1]])
    return np.abs(np.diff(x[pts]))


def episode_metrics(a):
    n = len(a)
    sec = n / FPS
    d1 = np.abs(np.diff(a, axis=0))
    d2 = np.abs(np.diff(a, 2, axis=0))
    v = np.diff(a, axis=0) * FPS
    w = np.hanning(len(v))[:, None]
    P = np.abs(np.fft.rfft((v - v.mean(0)) * w, axis=0)) ** 2
    f = np.fft.rfftfreq(len(v), 1 / FPS)
    m = {"frames": n}
    for j, name in enumerate(J):
        sw = swings(a[:, j])
        tot = P[:, j].sum() + 1e-12
        m |= {
            f"d1_mean|{name}": d1[:, j].mean(),
            f"d1_p99|{name}": np.percentile(d1[:, j], 99),
            f"d1_max|{name}": d1[:, j].max(),
            f"d2_rms|{name}": np.sqrt((d2[:, j] ** 2).mean()),
            f"d2_p99|{name}": np.percentile(d2[:, j], 99),
            f"rev_micro|{name}": (sw < 0.3).sum() / sec,
            f"rev_small|{name}": ((sw >= 0.3) & (sw < 2)).sum() / sec,
            f"rev_large|{name}": (sw >= 5).sum() / sec,
            f"hf3|{name}": P[f >= 3, j].sum() / tot,
            f"hf6|{name}": P[f >= 6, j].sum() / tot,
            f"jump10|{name}": int((d1[:, j] > 10).sum()),
            f"P_raw|{name}": P[:, j],
            f"f_raw|{name}": f,
        }
    return m


rows, ep_rows, psd = [], [], {}
all_actions = {}
FGRID = np.linspace(0, 15, 151)
for src, task, split, root in GROUPS:
    df = load(root)
    acts = []
    for e, g in df.groupby("episode_index"):
        a = np.stack(g["action"].to_numpy()).astype(np.float64)
        if len(a) < MIN_LEN:
            print(f"skip short episode {src} {task} {split} ep{e} ({len(a)} frames)")
            continue
        acts.append(a)
        m = episode_metrics(a)
        for j, name in enumerate(J):  # PSD 를 공통 주파수 격자로 보간해 평균
            key = (src, task, name)
            psd.setdefault(key, []).append(np.interp(FGRID, m.pop(f"f_raw|{name}"), m.pop(f"P_raw|{name}") / len(a)))
        ep_rows.append({"src": src, "task": task, "split": split, "episode": int(e)} | m)
    all_actions[(src, task, split)] = acts
    print(f"{src:6s} {task} {split:6s} episodes={len(acts)} frames={sum(len(a) for a in acts)}")

E = pd.DataFrame(ep_rows)
# 에피소드 점수 (H3): 팔 5개 관절의 small 반전율 평균 + hf3 평균
arm = J[:5]
E["score_small_rev"] = E[[f"rev_small|{n}" for n in arm]].mean(1)
E["score_hf3"] = E[[f"hf3|{n}" for n in arm]].mean(1)
E.to_csv(OUT / "metrics_episodes.csv", index=False)

# 그룹 집계: 에피소드 프레임 수 가중 평균 (속도·반전율) — 그룹은 src×task, src×task×split, src 전체
def agg(sub):
    w = sub["frames"].to_numpy()
    out = {"episodes": len(sub), "frames": int(w.sum()), "ep_sec_median": round(float(np.median(w)) / FPS, 1)}
    for c in E.columns:
        if "|" in c:
            if c.startswith(("d1_max", "jump10")):
                out[c] = sub[c].max() if c.startswith("d1_max") else int(sub[c].sum())
            else:
                out[c] = float(np.average(sub[c], weights=w))
    return out


G = []
for keys, sub in list(E.groupby(["src", "task", "split"])) + list(E.groupby(["src", "task"])) + list(E.groupby(["src"])):
    keys = keys if isinstance(keys, tuple) else (keys,)
    label = {"src": keys[0], "task": keys[1] if len(keys) > 1 else "ALL", "split": keys[2] if len(keys) > 2 else "ALL"}
    G.append(label | agg(sub))
G = pd.DataFrame(G)
G.to_csv(OUT / "metrics_groups.csv", index=False)

# 정규화 범위 (H4)
nr = []
def pooled(src, task=None):
    return np.concatenate([a for (s, t, _), acts in all_actions.items() if s == src and (task is None or t == task) for a in acts])

for src in ["ref", "redbox"]:
    A = pooled(src)
    split_stats = [json.load(open(root / "meta/stats.json"))["action"] for s, _, _, root in GROUPS if s == src]
    lerobot_q01 = np.min([s["q01"] for s in split_stats], 0)  # lerobot 0.6.2 merge 와 같은 envelope 규칙
    lerobot_q99 = np.max([s["q99"] for s in split_stats], 0)
    for j, name in enumerate(J):
        nr.append({"src": src, "joint": name, "true_q01": np.quantile(A[:, j], .01), "true_q99": np.quantile(A[:, j], .99),
                   "merged_stats_q01": lerobot_q01[j], "merged_stats_q99": lerobot_q99[j], "min": A[:, j].min(), "max": A[:, j].max()})
NR = pd.DataFrame(nr)
NR["true_width"] = NR.true_q99 - NR.true_q01
NR["merged_width"] = NR.merged_stats_q99 - NR.merged_stats_q01
NR["inflation"] = NR.merged_width / NR.true_width
ck = Path.home() / "so101_runs/main/redbox_all/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
from safetensors.numpy import load_file
st = load_file(str(ck / "policy_preprocessor_step_3_normalizer_processor.safetensors"))
NR.loc[NR.src == "redbox", "ckpt_width"] = (st["action.q99"] - st["action.q01"])
NR.to_csv(OUT / "norm_ranges.csv", index=False)

# 작업 간 분포 차이 (H2): 관절별 작업 분포와 전체 분포의 Wasserstein-1 (분위수 함수 차이 평균) / 전체 q01–q99 폭
qs = np.linspace(0.005, 0.995, 199)
ts = []
for src in ["ref", "redbox"]:
    A = pooled(src)
    for task in ["T1", "T2", "T3"]:
        T = pooled(src, task)
        for j, name in enumerate(J):
            width = np.quantile(A[:, j], .99) - np.quantile(A[:, j], .01)
            w1 = np.abs(np.quantile(T[:, j], qs) - np.quantile(A[:, j], qs)).mean()
            ts.append({"src": src, "task": task, "joint": name, "w1_deg": w1, "w1_rel": w1 / width,
                       "task_q01": np.quantile(T[:, j], .01), "task_q99": np.quantile(T[:, j], .99),
                       "task_width_over_pooled": (np.quantile(T[:, j], .99) - np.quantile(T[:, j], .01)) / width})
pd.DataFrame(ts).to_csv(OUT / "task_shift.csv", index=False)

# 그래프용 데이터
np.savez_compressed(OUT / "plotdata.npz", fgrid=FGRID,
                    **{f"psd|{s}|{t}|{n}": np.mean(v, 0) for (s, t, n), v in psd.items()})
# 예시 에피소드 원본 action (각 src×task 에서 score_small_rev 중앙값 에피소드, 최댓값 에피소드)
ex = {}
for (src, task), sub in E.groupby(["src", "task"]):
    for kind, idx in [("median", (sub.score_small_rev - sub.score_small_rev.median()).abs().idxmin()), ("worst", sub.score_small_rev.idxmax())]:
        r = E.loc[idx]
        acts = all_actions[(src, task, r.split)]
        eps = sorted(E[(E.src == src) & (E.task == task) & (E.split == r.split)].episode)
        ex[f"ex|{src}|{task}|{kind}|{r.split}|{r.episode}"] = acts[eps.index(r.episode)]
np.savez_compressed(OUT / "examples.npz", **ex)
print("done")
