"""Joint ranges on working frames only (first gripper opening .. last gripper re-close), plus grasp-point spread."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

HERE = Path(__file__).parent
JN = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
d = np.load(HERE / "states.npz")
GROUPS = sorted({k.split("/")[0][4:] for k in d.files})


def work_mask(g):
    g0 = np.median(g[:10])
    op = np.flatnonzero(g > g0 + 8)
    m = np.zeros(len(g), bool)
    if len(op):
        m[op[0]:op[-1] + 1] = True
    return m


rows, rest = [], []
for src in ("ref", "our"):
    W, S0 = [], []
    for grp in GROUPS:
        s, ep = d[f"{src}_{grp}/state"], d[f"{src}_{grp}/ep"]
        for e in np.unique(ep):
            se = s[ep == e]
            W.append(se[work_mask(se[:, 5])])
            S0.append(se[0])
    W, S0 = np.concatenate(W), np.array(S0)
    for i, n in enumerate(JN):
        q = np.percentile(W[:, i], [1, 5, 50, 95, 99])
        rows.append(dict(src=src, joint=n, frames=len(W), p1=q[0], p5=q[1], p50=q[2], p95=q[3], p99=q[4],
                         span_p5_p95=q[3] - q[1], span_p1_p99=q[4] - q[0]))
        rest.append(dict(src=src, joint=n, start_pose_median=np.median(S0[:, i])))
W = pd.DataFrame(rows)
W.to_csv(HERE / "joint_ranges_working.csv", index=False, float_format="%.2f")
pd.DataFrame(rest).pivot(index="joint", columns="src", values="start_pose_median").to_csv(HERE / "start_pose.csv", float_format="%.2f")

G = pd.read_csv(HERE / "first_close_points.csv")
spread = []
for src in ("ref", "our"):
    for grp in GROUPS + ["ALL"]:
        g = G[G.src == src] if grp == "ALL" else G[(G.src == src) & (G.group == grp)]
        P = g[["x_cm", "y_cm"]].to_numpy()
        spread.append(dict(src=src, group=grp, n=len(g), hull_area_cm2=ConvexHull(P).volume,
                           r_p5=np.percentile(g.r_cm, 5), r_p50=g.r_cm.median(), r_p95=np.percentile(g.r_cm, 95),
                           az_p5=np.percentile(g.az_deg, 5), az_p50=g.az_deg.median(), az_p95=np.percentile(g.az_deg, 95),
                           droll_abs_p50=g.droll_from_start.abs().median(), droll_p5=np.percentile(g.droll_from_start, 5),
                           droll_p95=np.percentile(g.droll_from_start, 95),
                           wflex_p50=g.wrist_flex.median(), z_p50=g.z_cm.median()))
Sp = pd.DataFrame(spread)
Sp.to_csv(HERE / "grasp_spread.csv", index=False, float_format="%.2f")
print(W.to_string()); print(pd.read_csv(HERE / "start_pose.csv").to_string()); print(Sp.round(1).to_string())
