"""필터 검증 그래프 (시스템 python3 / matplotlib)."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e6e5e0", "#fcfcfb"
C_NONE, C_ARMF, C_STATE = "#2a78d6", "#eb6834", "#6b6a64"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "lines.linewidth": 1.6})
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

T = pd.read_csv(HERE / "wide_table.csv")
T = T[T.lat == "lat1.55"]
tasks = ["rollout(T1)", "T1", "T2", "T3"]
pan = [("boundary_max", "max boundary jump (°)"), ("boundary_gt8", "boundary jumps > 8°"), ("noise_arm", "in-chunk noise (°)"),
       ("grasp_err", "grasp-pose error (°)"), ("grip_abs_dt", "gripper timing |Δ| (frames)"), ("clamp_pct", "servo-sim clamp (%)")]
fig, axs = plt.subplots(2, 6, figsize=(17, 6.5))
for r, cfg in enumerate(["sync_s10", "rtc_h20_exp_s5"]):
    for c, (m, lab) in enumerate(pan):
        ax = axs[r, c]; x = np.arange(len(tasks))
        for i, (f, col) in enumerate([("none", C_NONE), ("armf", C_ARMF)]):
            sub = T[(T.cfg == cfg) & (T["filter"] == f)].set_index("task")
            v = [sub.loc[t, m] if t in sub.index else np.nan for t in tasks]
            ax.bar(x + (i - 0.5) * 0.38, np.nan_to_num(v), 0.36, color=col, label="no filter" if f == "none" else "arm filter")
        ax.set_xticks(x, ["rollout", "T1", "T2", "T3"])
        ax.set_title(f"{lab}" + ("" if c else f"\n[{cfg}]"), loc="left", color=INK, fontsize=8.5)
fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper right", ncol=2, frameon=False)
fig.suptitle("Arm filter (actual arm_filter.py) on 24 human-demo replays + rollout, realistic latency ×1.55 — open-loop", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "figV1_by_task.png", dpi=130); plt.close(fig)

X = np.load(HERE / "examples_fast.npz")
ep, lo, j = X["hum_meta"]
fig, axs = plt.subplots(2, 1, figsize=(13, 6.5))
t = (np.arange(len(X["hum_raw"])) + lo) / 30
axs[0].plot(t, X["hum_raw"][:, j], color=C_NONE, label="human teleop action (raw)")
axs[0].plot(t, X["hum_out"][:, j], color=C_ARMF, label="after arm filter")
axs[0].plot(t, X["hum_state"][:, j], color=C_STATE, ls="--", lw=1.1, label="follower state (recorded)")
axs[0].set_title(f"Largest filter deviation on human data: episode {ep} (T3), {J[j]}", loc="left", color=INK); axs[0].set_ylabel("°")
axs[0].legend(frameon=False, fontsize=8)
pr, po = X["pol_raw"], X["pol_out"]; tp = int(X["pol_meta"][0])
tt = (np.arange(len(pr)) + max(tp - 60, 0)) / 30
jj = int(np.nanargmax(np.nanmax(np.abs(np.diff(pr[:, :5], axis=0)), axis=0)))
axs[1].plot(tt, pr[:, jj], color=C_NONE, marker=".", ms=3, label="policy command (RTC h20 EXP s5, raw)")
axs[1].plot(tt, po[:, jj], color=C_ARMF, marker=".", ms=3, label="after arm filter")
axs[1].set_title(f"Largest raw jump in rollout replay: {J[jj]}", loc="left", color=INK); axs[1].set_ylabel("°"); axs[1].set_xlabel("time (s)")
axs[1].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(HERE / "figV2_fast_motion.png", dpi=130); plt.close(fig)
print("plots done")
