"""Figures for range comparison. system python3."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from scipy.spatial import ConvexHull
from scipy.stats import gaussian_kde

HERE = Path(__file__).parent
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
COL = {"ref": "#2a78d6", "our": "#eb6834"}
LBL = {"ref": "레퍼런스 (aswinkumar99, 스펀지)", "our": "우리 (redbox, 큐브)"}
plt.rcParams.update({"font.family": "NanumSquare", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.unicode_minus": False})
pd_ = np.load(HERE / "plotdata.npz")
G = pd.read_csv(HERE / "first_close_points.csv")
W = pd.read_csv(HERE / "joint_ranges_working.csv")


def view(xy):  # base (x fwd, y left) -> plot (right +, forward up)
    xy = np.atleast_2d(xy)
    return -xy[:, 1], xy[:, 0]


# ---------- fig1: top view ----------
fig, ax = plt.subplots(figsize=(7.4, 7.4))
for src in ("ref", "our"):
    tip = pd_[f"tip_{src}"]
    tip = tip[tip[:, 2] < 6]  # near-table frames (tip z < 6 cm)
    h, v = view(tip[:, :2])
    kde = gaussian_kde(np.vstack([h, v])[:, ::7], bw_method=0.12)
    gx, gy = np.mgrid[-50:50:200j, -10:50:120j]
    z = kde(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    zs = np.sort(z.ravel())[::-1]
    lvl = zs[np.searchsorted(np.cumsum(zs) / zs.sum(), 0.9)]
    ax.contour(gx, gy, z, levels=[lvl], colors=COL[src], linewidths=1.2, linestyles="--")
    g = G[G.src == src]
    h, v = view(g[["x_cm", "y_cm"]].to_numpy())
    ax.scatter(h, v, s=16, color=COL[src], alpha=0.75, edgecolor=SURF, linewidth=0.6, label=f"{LBL[src]} 첫 집기 {len(g)}편", zorder=3)
    P = np.c_[h, v]
    hull = P[ConvexHull(P).vertices]
    ax.fill(hull[:, 0], hull[:, 1], color=COL[src], alpha=0.07, zorder=1)
bh, bv = view(pd_["box"])
ax.plot(bh, bv, color=MUTED, lw=1.2)
ax.text(bh.mean(), bv.max() + 1, "우리 상자", color=MUTED, ha="center", fontsize=8)
for k, (x, y) in zip(("K1", "K2", "K3", "K4"), pd_["K"]):
    h, v = view([x, y])
    ax.plot(h, v, marker="x", color=INK, ms=7, mew=1.6, zorder=4)
    ax.annotate(k, (h[0], v[0]), xytext=(4, 4), textcoords="offset points", color=INK, fontsize=8)
for r in (10, 20, 30, 40):
    th = np.linspace(-np.pi / 2, np.pi / 2, 100)
    ax.plot(r * np.sin(th), r * np.cos(th), color=GRID, lw=0.8, zorder=0)
    ax.text(r * np.sin(np.radians(-62)), r * np.cos(np.radians(-62)), f"{r} cm", color=MUTED, fontsize=7)
ax.plot(0, 0, marker="s", color=INK, ms=8)
ax.text(0, -2.5, "로봇 base", ha="center", va="top", fontsize=8, color=INK)
ax.plot([], [], color=MUTED, ls="--", label="점선: 그리퍼 끝 높이 < 6 cm 프레임의 90% 영역")
ax.set_aspect("equal"); ax.set_xlim(-48, 48); ax.set_ylim(-6, 54)
ax.set_xlabel("← 로봇 왼쪽   (cm)   로봇 오른쪽 →"); ax.set_ylabel("로봇 정면 방향 (cm)")
ax.set_title("위에서 본 그리퍼 끝 위치 (FK, 각자 로봇 base 기준)", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
fig.tight_layout(); fig.savefig(HERE / "fig1_top_view.png", dpi=150); plt.close(fig)

# ---------- fig2: joint ranges (working frames) ----------
JN = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
fig, ax = plt.subplots(figsize=(7.4, 4.2))
for i, j in enumerate(JN):
    for k, src in enumerate(("ref", "our")):
        r = W[(W.src == src) & (W.joint == j)].iloc[0]
        y = i * 1.0 + (0.17 if src == "ref" else -0.17)
        ax.plot([r.p1, r.p99], [y, y], color=COL[src], lw=1.2, solid_capstyle="round")
        ax.plot([r.p5, r.p95], [y, y], color=COL[src], lw=6, solid_capstyle="round", label=LBL[src] if i == 0 else None)
        ax.plot([r.p50], [y], marker="|", color=SURF, ms=7, mew=2)
        ax.text(r.p99 + 3, y, f"{r.span_p5_p95:.0f}°", va="center", fontsize=7.5, color=MUTED)
ax.set_yticks(range(len(JN)), [j + (" (0–100)" if j == "gripper" else "") for j in JN])
ax.invert_yaxis(); ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_xlabel("lerobot 각도 (°) — 굵은 막대 5–95%, 가는 선 1–99%, 숫자 = 5–95% 폭")
ax.set_title("작업 구간 관절 범위 (첫 그리퍼 열림 ~ 마지막 닫힘)", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(HERE / "fig2_joint_ranges.png", dpi=150); plt.close(fig)

# ---------- fig3: at-grasp distributions ----------
items = [("r_cm", "집는 거리 r (cm)", np.arange(8, 44, 2)), ("az_deg", "집는 방향 (°, + = 오른쪽)", np.arange(-75, 66, 7.5)),
         ("droll_from_start", "손목 roll 변화 (시작→집기, °)", np.arange(-120, 81, 10)), ("wrist_flex", "wrist_flex at 집기 (°)", np.arange(0, 101, 5))]
fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.2))
for ax, (c, t, b) in zip(axs.ravel(), items):
    for src in ("ref", "our"):
        ax.hist(G[G.src == src][c], bins=b, histtype="step", lw=2, color=COL[src], label=LBL[src])
    ax.set_title(t, loc="left", color=INK, fontsize=9.5); ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
axs[0, 0].set_ylabel("에피소드 수"); axs[1, 0].set_ylabel("에피소드 수")
fig.legend(*axs[0, 0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "fig3_at_grasp.png", dpi=150); plt.close(fig)
print("ok")
