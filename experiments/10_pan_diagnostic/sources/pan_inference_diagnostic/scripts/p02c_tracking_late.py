"""p02c 관절별 추종 지연·오차 (정책 5 판) + 사람 pan 같은 방법 + 정책 판 늦은 구간 접선 오차 (읽기만, CPU).
출력 tables/p02_tracking_joints.csv, p02c_human_lag.json, p02c_late_phase.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p02c_tracking_late.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
TAB = D2 / "pan_inference_diagnostic/tables"
ATAB = D2 / "data_coverage_audit/tables"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def best_lag(s, x):
    v = np.abs(np.gradient(s))

    def f(L):
        m = v[: len(s) - L] > 0.2
        return np.mean(np.abs(x[L:] - s[: len(s) - L])[m]) if m.sum() > 10 else 1e9
    return min(range(11), key=f)


T = pd.read_parquet(TAB / "p01_ticks.parquet")
P = pd.read_csv(TAB / "p02_policy_episodes.csv")
out = []
for (r, e), g in T.groupby(["run", "ep"]):
    tag = f"{r[16:]}/ep{e}"
    p = P[P.ep == tag].iloc[0]
    on, c = int(round(p.onset_s * 30)), int(round(p.first_close_s * 30))
    g = g.iloc[on:c + 1]
    for j in J:
        s, x = g["sent_" + j].values, g["state_" + j].values
        te = np.abs(s - x)[np.abs(np.gradient(s)) > 1.0]
        out.append(dict(ep=tag, joint=j, lag=best_lag(s, x), te_fast_p50=np.median(te) if len(te) else np.nan,
                        te_fast_p95=np.percentile(te, 95) if len(te) else np.nan, n_fast=len(te), clamp=int(g["clamp_" + j].sum())))
pd.DataFrame(out).to_csv(TAB / "p02_tracking_joints.csv", index=False)
W = pd.read_parquet(ATAB / "a02_frames.parquet", columns=["ep", "a_shoulder_pan", "s_shoulder_pan"])
E = pd.read_csv(ATAB / "a02_events.csv")
lags, tes = [], []
for e in range(256):
    g = W[W.ep == e]
    on, c = int(E.onset[e]), int(E.grasp[e])
    s, x = g.a_shoulder_pan.values[on:c + 1], g.s_shoulder_pan.values[on:c + 1]
    if (np.abs(np.gradient(s)) > 0.2).sum() < 20:
        continue
    lags.append(best_lag(s, x))
    tes += list(np.abs(s - x)[np.abs(np.gradient(s)) > 1.0])
json.dump(dict(n=len(lags), lag_med=float(np.median(lags)), lag_p10=float(np.percentile(lags, 10)), lag_p90=float(np.percentile(lags, 90)),
               te_fast_p50=float(np.median(tes)), te_fast_p95=float(np.percentile(tes, 95))), open(TAB / "p02c_human_lag.json", "w"), indent=1)
TR = pd.read_csv(ATAB / "a07_policy_trace.csv")
rows = []
for (r, e), g in TR.groupby(["run", "ep"]):
    d = {"ep": f"{r[16:]}/ep{e}"}
    for s in (3, 2, 1, 0):
        k = (g.t_to_close - s).abs().idxmin()
        d.update({f"e_t_m{s}": g.e_t[k], f"pan_err_m{s}": g.pan_err[k], f"roll_m{s}": g.roll[k]})
    rows.append(d)
pd.DataFrame(rows).to_csv(TAB / "p02c_late_phase.csv", index=False)
print(pd.DataFrame(out).groupby("joint")[["lag", "te_fast_p50", "te_fast_p95", "clamp"]].median())
print(open(TAB / "p02c_human_lag.json").read())
