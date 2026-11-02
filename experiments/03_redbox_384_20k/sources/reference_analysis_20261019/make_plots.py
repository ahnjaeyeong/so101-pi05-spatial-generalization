"""compute_metrics.py 결과로 그래프를 만든다. 실행: python3 make_plots.py (시스템 python — matplotlib 사용)"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
C = {"ref": "#2a78d6", "redbox": "#eb6834"}  # dataviz 기본 팔레트 1·2번 (검증된 인접 쌍)
LBL = {"ref": "Reference (sponge)", "redbox": "Redbox"}
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e6e5e0"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "lines.linewidth": 2})

G = pd.read_csv(OUT / "metrics_groups.csv")
E = pd.read_csv(OUT / "metrics_episodes.csv")
P = np.load(OUT / "plotdata.npz")
f = P["fgrid"]

# 1. 속도 PSD — 관절별, 작업 평균
fig, axs = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
for ax, j in zip(axs.flat, J):
    for src in ["ref", "redbox"]:
        p = np.mean([P[f"psd|{src}|{t}|{j}"] for t in ["T1", "T2", "T3"]], 0)
        ax.semilogy(f, p, color=C[src], label=LBL[src])
    ax.axvspan(3, 15, color=GRID, alpha=0.5, lw=0)
    ax.set_title(j, color=INK, loc="left")
    ax.set_xlim(0, 15)
axs[1, 0].set_xlabel("Hz"); axs[1, 1].set_xlabel("Hz"); axs[1, 2].set_xlabel("Hz")
axs[0, 0].set_ylabel("velocity power (log)"); axs[1, 0].set_ylabel("velocity power (log)")
axs[0, 0].legend(frameon=False)
fig.suptitle("Teleop action velocity spectrum (shaded: ≥3 Hz band)", x=0.01, ha="left", color=INK)
fig.tight_layout(); fig.savefig(OUT / "fig1_velocity_psd.png", dpi=130); plt.close(fig)

# 2. 작업별 지표 — 행: 지표, 열: 관절
metrics = [("rev_small", "small reversals /s\n(0.3–2° swings)"), ("rev_large", "large reversals /s\n(≥5° swings)"),
           ("d2_rms", "2nd diff RMS\n(°/frame²)"), ("hf3", "velocity power ≥3 Hz\n(share)")]
S = G[G.split == "ALL"]
fig, axs = plt.subplots(len(metrics), 6, figsize=(14, 9))
x = np.arange(3)
for r, (m, lab) in enumerate(metrics):
    for c, j in enumerate(J):
        ax = axs[r, c]
        for k, src in enumerate(["ref", "redbox"]):
            v = [S[(S.src == src) & (S.task == t)][f"{m}|{j}"].item() for t in ["T1", "T2", "T3"]]
            ax.bar(x + (k - 0.5) * 0.38, v, 0.36, color=C[src], label=LBL[src])
        ax.set_xticks(x, ["T1", "T2", "T3"])
        if r == 0: ax.set_title(j, color=INK, loc="left")
        if c == 0: ax.set_ylabel(lab)
fig.legend(*axs[0, 0].get_legend_handles_labels(), frameon=False, fontsize=8.5, loc="upper right", ncol=2)
fig.suptitle("Teleop action quality by task (frame-weighted, within-episode only)", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(OUT / "fig2_metrics_by_task.png", dpi=130); plt.close(fig)


# 3. 예시 에피소드 — 의도된 방향 전환(≥5°) vs 작은 반전(0.3–2°)
def turning(x):
    d = np.diff(x); nz = np.nonzero(d)[0]; s = np.sign(d[nz])
    tp = nz[1:][s[1:] != s[:-1]]
    pts = np.concatenate([[0], tp, [len(x) - 1]])
    amp = np.abs(np.diff(x[pts]))
    return pts[1:-1], np.minimum(amp[:-1], amp[1:])  # 반전점 양쪽 swing 중 작은 쪽


X = np.load(OUT / "examples.npz")
keys = sorted(X.files)
pick = [k for k in keys if "|median|" in k and "|T1|" in k] + [k for k in keys if "|redbox|T1|worst|" in k]
show = ["shoulder_pan", "elbow_flex", "wrist_roll"]
fig, axs = plt.subplots(len(pick), len(show), figsize=(14, 2.6 * len(pick)), squeeze=False)
for r, k in enumerate(pick):
    _, src, task, kind, split, ep = k.split("|")
    a = X[k]; t = np.arange(len(a)) / 30
    for c, j in enumerate(show):
        ax = axs[r, c]; y = a[:, J.index(j)]
        ax.plot(t, y, color=C[src], lw=1.4)
        tp, amp = turning(y)
        big = tp[amp >= 5]; small = tp[(amp >= 0.3) & (amp < 2)]
        ax.plot(t[big], y[big], "o", ms=6, mfc="none", mec=INK, mew=1.2, label="direction change (≥5°)")
        ax.plot(t[small], y[small], "x", ms=5, color="#e34948", mew=1.2, label="small reversal (0.3–2°)")
        ax.set_title(f"{LBL[src]} {task} {split} ep{ep} ({kind}) — {j}", color=INK, loc="left", fontsize=8.5)
        if c == 0: ax.set_ylabel("action (°)")
axs[0, 0].legend(frameon=False, fontsize=7.5, loc="best")
axs[-1, 1].set_xlabel("time (s)")
fig.tight_layout(); fig.savefig(OUT / "fig3_example_episodes.png", dpi=130); plt.close(fig)

# 3b. 확대: Redbox T1 worst 의 shoulder_pan 4초 구간
k = [k for k in keys if "|redbox|T1|worst|" in k][0]
a = X[k][:, 0]; t = np.arange(len(a)) / 30
v = np.abs(np.diff(a)); w = 120
i0 = int(np.argmax(np.convolve((np.diff(np.sign(np.diff(a))) != 0).astype(float), np.ones(w), "valid")))
fig, ax = plt.subplots(figsize=(10, 3))
seg = slice(i0, i0 + w)
ax.plot(t[seg], a[seg], color=C["redbox"], marker=".", ms=4)
ax.set_title(f"Redbox {k.split('|')[4]} ep{k.split('|')[5]} shoulder_pan — densest 4 s window (dots = 30 fps frames)", color=INK, loc="left")
ax.set_xlabel("time (s)"); ax.set_ylabel("action (°)")
fig.tight_layout(); fig.savefig(OUT / "fig3b_redbox_pan_zoom.png", dpi=130); plt.close(fig)

# 4. 에피소드별 고주파 점수 분포 (H3)
fig, ax = plt.subplots(figsize=(10, 3.6))
pos = 0; ticks = []
rng = np.random.default_rng(0)
for src in ["ref", "redbox"]:
    s = E[E.src == src]; med = s.score_hf3.median(); mad = (s.score_hf3 - med).abs().median()
    for t in ["T1", "T2", "T3"]:
        v = s[s.task == t].score_hf3.to_numpy()
        ax.plot(pos + rng.uniform(-0.25, 0.25, len(v)), v, "o", ms=3.5, color=C[src], alpha=0.7)
        ticks.append((pos, f"{LBL[src].split()[0]}\n{t}")); pos += 1
    ax.hlines(med + 5 * mad, pos - 3.4, pos - 0.6, color=INK, lw=1, ls="--")
    pos += 0.6
ax.set_xticks([p for p, _ in ticks], [l for _, l in ticks])
ax.set_ylabel("per-episode velocity power ≥3 Hz\n(mean of 5 arm joints)")
ax.set_title("Per-episode high-frequency share (dashed: median + 5·MAD outlier line per dataset)", color=INK, loc="left")
fig.tight_layout(); fig.savefig(OUT / "fig4_episode_hf_scores.png", dpi=130); plt.close(fig)

# 5. 정규화 범위 (H4)
NR = pd.read_csv(OUT / "norm_ranges.csv")
fig, axs = plt.subplots(1, 6, figsize=(14, 3.4))
for ax, j in zip(axs, J):
    rows = [("ref", "true q01–q99", "true_q01", "true_q99"), ("redbox", "true q01–q99", "true_q01", "true_q99"),
            ("redbox", "ckpt normalizer", "merged_stats_q01", "merged_stats_q99")]
    for i, (src, lab, lo, hi) in enumerate(rows):
        r = NR[(NR.src == src) & (NR.joint == j)].iloc[0]
        ax.plot([i, i], [r[lo], r[hi]], color=C[src], lw=6 if "true" in lab else 2.5, solid_capstyle="round")
    ax.set_xticks(range(3), ["Ref\ntrue", "Redbox\ntrue", "Redbox\nckpt"], fontsize=7.5)
    ax.set_title(j, color=INK, loc="left"); ax.set_xlim(-0.6, 2.6)
axs[0].set_ylabel("action (°)")
fig.suptitle("Action normalization range: true 1–99% quantiles vs the range the Redbox checkpoint normalizes with", x=0.01, ha="left", color=INK)
fig.tight_layout(); fig.savefig(OUT / "fig5_norm_ranges.png", dpi=130); plt.close(fig)

# 6. 모델 출력 잡음 — 도 단위 vs 정규화 단위
D = pd.read_csv(OUT / "model_jitter_normalized.csv", index_col=0)
jj = ["pan", "lift", "elbow", "wflex", "wroll", "grip"]
cols = {"redbox_20k (expert, bs32)": C["redbox"], "cubemark_15k (full, bs4)": "#1baf7a", "cubemark_3k (expert, bs8)": "#6250d6"}
fig, axs = plt.subplots(1, 2, figsize=(13, 3.6))
xx = np.arange(6)
for ax, pre, lab in [(axs[0], "jit_deg_", "chunk residual std (°)"), (axs[1], "jit_norm_", "chunk residual std (normalized ×1e-3)")]:
    for i, (ck, col) in enumerate(cols.items()):
        ax.bar(xx + (i - 1) * 0.27, D.loc[ck, [pre + j for j in jj]], 0.25, color=col, label=ck)
    ax.set_xticks(xx, jj); ax.set_ylabel(lab)
fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, fontsize=8.5, loc="upper right", ncol=3)
fig.suptitle("Offline policy output jitter (same metric, 10 denoise steps): degrees vs normalized units", x=0.01, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(OUT / "fig6_model_jitter.png", dpi=130); plt.close(fig)
print("plots done")
