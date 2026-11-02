"""Joint ranges + FK workspace: reference (aswinkumar99 sponge) vs ours (redbox). Run with system python3."""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from fk import fk

HERE = Path(__file__).parent
FPS = 30
JN = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CAL = {"ref": Path.home() / "so101_runs/reference/aswinkumar99_so101_pick_place/calibration/my_follower_arm.json",
       "our": Path.home() / ".cache/huggingface/lerobot/calibration/robots/so_follower/my_arm.json"}
d = np.load(HERE / "states.npz")
GROUPS = sorted({k.split("/")[0][4:] for k in d.files})


def first_close(g):
    """First gripper close after first opening: frame where g settles (15 frames |dg|<0.4) after dropping >=5 from its open peak."""
    g0 = np.median(g[:10])
    op = np.flatnonzero(g > g0 + 8)
    if not len(op):
        return None
    peak = g[op[0]]
    for j in range(op[0], len(g) - 15):
        peak = max(peak, g[j])
        if peak - g[j] >= 5 and np.all(np.abs(np.diff(g[j:j + 16])) < 0.4):
            return j
    return None


rows, grasps = [], []
for src in ("ref", "our"):
    for grp in GROUPS:
        s, ep = d[f"{src}_{grp}/state"], d[f"{src}_{grp}/ep"]
        for e in np.unique(ep):
            se = s[ep == e]
            j = first_close(se[:, 5])
            if j is None:
                continue
            p, _ = fk(se[j:j + 1, :5])
            x, y, z = p[0] * 100
            grasps.append(dict(src=src, group=grp, episode=int(e), t_close_s=j / FPS, x_cm=x, y_cm=y, z_cm=z,
                               r_cm=np.hypot(x, y), az_deg=np.degrees(np.arctan2(-y, x)),
                               **{n: se[j, i] for i, n in enumerate(JN)},
                               droll_from_start=se[j, 4] - se[0, 4]))

# ---- grasp detector check against the census (ours only) ----
fg = pd.read_csv(Path.home() / "so101_runs/main/redbox_all/eval/train_roll_census/first_grasps.csv")
G = pd.DataFrame(grasps)
our = G[G.src == "our"].copy()
our["key"] = our.group.str.lower().str.replace("-k", "_known").str.replace("-r", "_random")
m = our.merge(fg.assign(key=fg.group.str.replace("t", "T", 1).str.lower()), left_on=["key", "episode"], right_on=["key", "episode"])
dt = (m.t_close_s_x - m.t_close_s_y).abs()
check = dict(matched=len(m), within_0_5s=int((dt <= 0.5).sum()), median_abs_dt_s=float(dt.median()))

# ---- FK vs measured cube position (ours): 2D rigid fit gives base pose in table frame ----
mm = m[m.cube_x.notna() & ~m.ambiguous.astype(bool)]
P, Q = mm[["x_cm", "y_cm"]].to_numpy(), mm[["cube_x", "cube_y"]].to_numpy()
mp, mq = P.mean(0), Q.mean(0)
U, S, Vt = np.linalg.svd((P - mp).T @ (Q - mq))
Rm = Vt.T @ np.diag([1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
t = mq - Rm @ mp
res = np.linalg.norm(P @ Rm.T + t - Q, axis=1)
fit = dict(n=len(mm), rot_deg=float(np.degrees(np.arctan2(Rm[1, 0], Rm[0, 0]))), base_table_cm=t.round(2).tolist(),
           resid_cm_median=float(np.median(res)), resid_cm_p90=float(np.percentile(res, 90)))


def table_to_base(xy):
    return (np.asarray(xy, float) - t) @ Rm  # inverse of base->table


cfg = (Path.home() / "so101_boxpick/config/redbox_layouts.yaml").read_text()
K = {k: table_to_base([float(v) for v in re.search(rf"^\s*{k}:\s*\{{xy_cm:\s*\[([-\d.]+),\s*([-\d.]+)\]", cfg, re.M).groups()])
     for k in ("K1", "K2", "K3", "K4")}
bc = [float(v) for v in re.search(r"center_cm:\s*\[([-\d.]+),\s*([-\d.]+)\]", cfg).groups()]
bs = [float(v) for v in re.search(r"inner_size_cm:\s*\[([-\d.]+),\s*([-\d.]+)\]", cfg).groups()]
box = table_to_base([[bc[0] + sx * bs[0] / 2, bc[1] + sy * bs[1] / 2] for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))])

# ---- joint range table (lerobot degrees; gripper 0-100) ----
cal = {k: json.loads(v.read_text()) for k, v in CAL.items()}
for src in ("ref", "our"):
    for grp in GROUPS + ["ALL"]:
        s = np.concatenate([d[f"{src}_{g}/state"] for g in GROUPS]) if grp == "ALL" else d[f"{src}_{grp}/state"]
        for i, n in enumerate(JN):
            q = np.percentile(s[:, i], [1, 5, 50, 95, 99])
            rows.append(dict(src=src, group=grp, joint=n, frames=len(s), min=s[:, i].min(), p1=q[0], p5=q[1], p50=q[2],
                             p95=q[3], p99=q[4], max=s[:, i].max(), span_p1_p99=q[4] - q[0], span_p5_p95=q[3] - q[1]))
R = pd.DataFrame(rows)

# calibration: lerobot zero = mid of swept range; homing pose = tick 2047. offset between the two conventions per arm
calrows = []
for n in JN:
    r = {"joint": n}
    for src in ("ref", "our"):
        c = cal[src][n]
        mid = (c["range_min"] + c["range_max"]) / 2
        r[f"{src}_range_ticks"] = f"{c['range_min']}–{c['range_max']}"
        r[f"{src}_span_deg"] = (c["range_max"] - c["range_min"]) * 360 / 4095
        r[f"{src}_mid_minus_home_deg"] = (mid - 2047) * 360 / 4095
    r["convention_shift_deg"] = r["ref_mid_minus_home_deg"] - r["our_mid_minus_home_deg"]
    calrows.append(r)
C = pd.DataFrame(calrows)

# ---- all-frame tip positions (subsampled every 3rd frame) ----
tips = {}
for src in ("ref", "our"):
    s = np.concatenate([d[f"{src}_{g}/state"] for g in GROUPS])[::3]
    tips[src] = fk(s[:, :5])[0] * 100

# FK robustness: grasp radius/azimuth under the homing-pose convention instead of range-mid
alt = []
for src in ("ref", "our"):
    sh = np.array([(lambda c: ((c["range_min"] + c["range_max"]) / 2 - 2047) * 360 / 4095)(cal[src][n]) for n in JN[:5]])
    gs = G[G.src == src]
    p = fk(gs[JN[:5]].to_numpy(float) + sh)[0] * 100
    alt.append(dict(src=src, r_median_mid=gs.r_cm.median(), r_median_home=float(np.median(np.hypot(p[:, 0], p[:, 1]))),
                    az_p5_p95_mid=np.percentile(gs.az_deg, [5, 95]).round(1).tolist(),
                    az_p5_p95_home=np.percentile(np.degrees(np.arctan2(-p[:, 1], p[:, 0])), [5, 95]).round(1).tolist()))

R.to_csv(HERE / "joint_ranges.csv", index=False, float_format="%.2f")
C.to_csv(HERE / "calibration_compare.csv", index=False, float_format="%.2f")
G.to_csv(HERE / "first_close_points.csv", index=False, float_format="%.2f")
np.savez_compressed(HERE / "plotdata.npz", tip_ref=tips["ref"], tip_our=tips["our"], box=box,
                    K=np.array([K[k] for k in ("K1", "K2", "K3", "K4")]))
json.dump(dict(detector_check=check, fk_fit=fit, convention_alt=alt,
               n_first_close={s: int((G.src == s).sum()) for s in ("ref", "our")}),
          open(HERE / "checks.json", "w"), ensure_ascii=False, indent=1, default=float)
print(json.dumps(dict(detector_check=check, fk_fit=fit, convention_alt=alt), ensure_ascii=False, indent=1, default=float))
print(C.to_string())
print(R[R.group == "ALL"][["src", "joint", "p1", "p5", "p50", "p95", "p99", "span_p5_p95"]].to_string())
