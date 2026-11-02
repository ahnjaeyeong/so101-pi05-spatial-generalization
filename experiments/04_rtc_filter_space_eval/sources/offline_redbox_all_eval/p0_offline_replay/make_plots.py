"""P0 그래프. 시스템 python3 (matplotlib). 사용: python3 make_plots.py <tag> <best_rtc_config>"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
TAG, BEST = sys.argv[1], sys.argv[2]
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e6e5e0", "#fcfcfb"
# dataviz 기본 범주 팔레트 순서 고정: sync / rtc / ramp / 필터
COL = {"sync": "#2a78d6", "rtc": "#eb6834", "ramp": "#1baf7a", "filt": "#6250d6", "state": "#6b6a64"}
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "lines.linewidth": 1.6})
T = pd.read_csv(OUT / f"metrics_{TAG}.csv")


def kind(c):
    return "sync" if c.startswith("sync") else "rtc" if c.startswith("rtc") else "ramp"


# A. 기본 설정 12개 요약 (필터 없음)
base = T[T["filter"] == "none"]
order = [c for c in ["sync_s10", "sync_s5", "ramp_s10", "ramp_s5", "rtc_h10_lin_s10", "rtc_h10_exp_s10", "rtc_h20_lin_s10",
                     "rtc_h20_exp_s10", "rtc_h10_lin_s5", "rtc_h10_exp_s5", "rtc_h20_lin_s5", "rtc_h20_exp_s5"] if c in set(base.config)]
panels = [("boundary_max", "rollout", "max boundary jump (°)\n[rollout replay]"), ("boundary_gt8", "rollout", "boundary jumps > 8°\n[rollout replay]"),
          ("noise_arm", "rollout", "in-chunk noise (°)\n[rollout replay]"), ("grasp_err", "train", "grasp-pose error (°)\n[human episodes]"),
          ("grip_abs_dt", "train", "gripper timing |Δ| (frames)\n[human episodes]"), ("clamp_pct", "rollout", "servo-sim clamp (% ticks)\n[rollout replay]"),
          ("hold_pct", "rollout", "no-new-command ticks (%)"), ("lat_ms", "rollout", "inference latency (ms, median)")]
fig, axs = plt.subplots(2, 4, figsize=(15, 7.5), sharey=True)
y = np.arange(len(order))
for ax, (m, part, lab) in zip(axs.flat, panels):
    sub = base[base.part == part].set_index("config")
    v = [sub.loc[c, m] if c in sub.index else np.nan for c in order]
    ax.barh(y, v, 0.7, color=[COL[kind(c)] for c in order])
    for yy, vv in zip(y, v):
        if not np.isnan(vv): ax.text(vv, yy, f" {vv:.1f}", va="center", fontsize=7, color=INK)
    ax.set_title(lab, loc="left", color=INK, fontsize=8.5); ax.invert_yaxis() if ax is axs.flat[0] else None
axs[0, 0].set_yticks(y, order); axs[1, 0].set_yticks(y, order)
fig.suptitle("Inference modes, no post-filter (open-loop replay — not a closed-loop result)", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(OUT / f"figA_modes_{TAG}.png", dpi=130); plt.close(fig)

# B. 필터 효과 — sync_s10, BEST, ramp_s10
cfgs = [c for c in ["sync_s10", BEST, "ramp_s10"] if c in set(T.config)]
filts = ["none", "ema25", "ema50", "vc_tel", "ema50vc", "ema50vc_arm", "vc_pr"]
pan = [("noise_arm", "rollout", "in-chunk noise (°)"), ("boundary_max", "rollout", "max boundary jump (°)"),
       ("lag_frames", "train", "added lag (frames)"), ("grasp_err", "train", "grasp-pose error (°)"),
       ("grip_abs_dt", "train", "gripper timing |Δ| (frames)"), ("clamp_pct", "rollout", "servo-sim clamp (%)")]
fig, axs = plt.subplots(2, 3, figsize=(14, 7))
x = np.arange(len(filts))
for ax, (m, part, lab) in zip(axs.flat, pan):
    for i, c in enumerate(cfgs):
        sub = T[(T.config == c) & (T.part == part)].set_index("filter")
        v = [sub.loc[f, m] if f in sub.index else np.nan for f in filts]
        ax.bar(x + (i - 1) * 0.27, np.nan_to_num(v), 0.25, color=COL[kind(c)], label=c)
    ax.set_xticks(x, filts); ax.set_title(lab, loc="left", color=INK)
fig.legend(*axs[0, 0].get_legend_handles_labels(), loc="upper right", ncol=3, frameon=False)
fig.suptitle("Post-filters on three inference modes (open-loop replay)", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(OUT / f"figB_filters_{TAG}.png", dpi=130); plt.close(fig)

# C. 관절 시간 그래프 — rollout replay 구간
K = np.load(OUT / f"keep_{TAG}.npz")
show = [("sync_s10", "none", COL["sync"]), (BEST, "none", COL["rtc"]), ("ramp_s10", "none", COL["ramp"]), (BEST, "ema50", COL["filt"])]
show = [s for s in show if f"{s[0]}|{s[1]}|c" in K.files]
w0, w1 = 1380, 1620
fig, axs = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
for ax, j in zip(axs, [1, 2, 3, 5]):
    for name, f, col in show:
        c = K[f"{name}|{f}|c"]; sw = K[f"{name}|{f}|sw"]; s = K[f"{name}|{f}|s"]
        t = np.arange(len(c))
        ax.plot(t[w0:w1] / 30, c[w0:w1, j], color=col, lw=1.3, label=f"{name} {f} (command)")
        if name == BEST and f == "none":
            ax.plot(t[w0:w1] / 30, s[w0:w1, j], color=COL["state"], lw=1.0, ls="--", label=f"{name} servo-sim state")
        for i in sw:
            if w0 <= i < w1: ax.axvline(i / 30, color=col, lw=0.6, alpha=0.35)
    ax.set_ylabel(f"{J[j]} (°)")
axs[0].legend(ncol=3, fontsize=7.5, frameon=False, loc="upper left")
axs[-1].set_xlabel("replay time (s) — thin vertical lines = chunk switch / RTC merge")
fig.suptitle("Commanded targets on the recorded rollout observations (open-loop replay)", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(OUT / f"figC_timeseries_{TAG}.png", dpi=130); plt.close(fig)

# D. 관절별 잡음·속도·가속도
sel = [("sync_s10", "none"), (BEST, "none"), ("ramp_s10", "none"), (BEST, "ema50"), (BEST, "ema50vc_arm")]
sel = [s for s in sel if ((T.config == s[0]) & (T["filter"] == s[1])).any()]
cols = [COL["sync"], COL["rtc"], COL["ramp"], COL["filt"], "#e87ba4"]
fig, axs = plt.subplots(1, 3, figsize=(15, 3.8))
xx = np.arange(6)
for ax, (pre, lab) in zip(axs, [("noise|", "in-chunk noise (°)"), ("vel_p99|", "command speed p99 (°/s)"), ("acc_rms|", "command accel RMS (°/s²)")]):
    for i, ((c, f), col) in enumerate(zip(sel, cols)):
        r = T[(T.config == c) & (T["filter"] == f) & (T.part == "rollout")].iloc[0]
        ax.bar(xx + (i - 2) * 0.16, [r[pre + j] for j in J], 0.15, color=col, label=f"{c} {f}")
    ax.set_xticks(xx, [j.replace("shoulder_", "sh_").replace("_flex", "_fl") for j in J]); ax.set_title(lab, loc="left", color=INK)
fig.legend(*axs[0].get_legend_handles_labels(), loc="upper right", ncol=5, frameon=False, fontsize=7.5)
fig.suptitle("Per-joint command quality on rollout replay", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.88)); fig.savefig(OUT / f"figD_joints_{TAG}.png", dpi=130); plt.close(fig)

# E. clamp 분석 + 서보 모델 검증
C = pd.read_csv(OUT / "clamp_runs.csv")
Z = np.load(OUT / "servo_model_val.npz")
SV = json.load(open(OUT / "servo_model_v2.json"))
fig = plt.figure(figsize=(15, 7.5))
ax1 = fig.add_subplot(2, 3, 1)
for o, col in [("lag", COL["sync"]), ("jump", COL["rtc"])]:
    s = C[C.onset == o]
    ax1.scatter(s.err_prev.abs(), s.dA.abs(), s=10 + s.frames, color=col, alpha=0.7, label=f"{o} onset ({len(s)})")
ax1.axhline(4, color=MUTED, lw=0.8, ls=":"); ax1.set_xlabel("|tracking error| previous frame (°)"); ax1.set_ylabel("|target change| at onset (°)")
ax1.set_title("clamp onsets (size = run length)", loc="left", color=INK); ax1.legend(frameon=False, fontsize=7.5)
ax2 = fig.add_subplot(2, 3, 2)
ax2.hist(C.dS_median, bins=30, color=COL["sync"]); ax2.set_xlabel("joint speed during clamp run, median (°/frame)")
ax2.set_title("joints keep moving during clamps", loc="left", color=INK)
ax3 = fig.add_subplot(2, 3, 3)
ax3.hist(C.chunk_pos, bins=50, color=COL["sync"]); ax3.set_xlabel("onset position within 50-step chunk")
ax3.set_title("clamp onsets vs chunk position", loc="left", color=INK)
A, S, cut = Z["A"], Z["S"], int(Z["cut"])
sys.path.insert(0, str(OUT))
for k, j in enumerate([1, 2, 3]):
    ax = fig.add_subplot(2, 3, 4 + k)
    m = SV[["pan", "lift", "elbow", "wflex", "wroll", "grip"][j]]
    s = S[:, j].copy()
    for t in range(cut, len(A) - 1):
        td = t - m["d"]; sent = s[td] + np.clip(A[td, j] - s[td], -8, 8); e = sent - s[t]
        s[t + 1] = s[t] + np.clip((m["kp"] if e > 0 else m["kn"]) * e, -m["vmax"], m["vmax"])
    tt = np.arange(cut, min(cut + 400, len(A)))
    ax.plot(tt / 30, A[tt, j], color=COL["rtc"], lw=1.0, label="command (recorded)")
    ax.plot(tt / 30, S[tt, j], color=INK, lw=1.4, label="actual state")
    ax.plot(tt / 30, s[tt], color=COL["sync"], lw=1.2, ls="--", label=f"servo model v2 (val RMSE {m['val_rmse']}°)")
    ax.set_title(f"{J[j]} — servo model on held-out 40%", loc="left", color=INK); ax.set_xlabel("time (s)")
    if k == 0: ax.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(OUT / "figE_clamp_servo.png", dpi=130); plt.close(fig)
print("plots done")
