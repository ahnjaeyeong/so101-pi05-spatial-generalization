"""3단계: 그림 (시스템 python3 — so101-env 에는 matplotlib 이 없다). 읽기만 함.
사용: PYTHONDONTWRITEBYTECODE=1 python3 plots.py
입력: grasp_train.csv, grasp_eval.csv, (있으면) probe_*.csv  ·  출력: fig_*.png
"""
import glob
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load(open(Path.home() / "so101_boxpick/config/redbox8_layouts.yaml"))
BASE = np.array(CFG["robot"]["base_xy_cm"], float)
KN = {k: v["xy_cm"] for k, v in CFG["known_positions"].items()}
GCOL = {"T1K": "#1f77b4", "T1R": "#9ecae1", "T3K": "#d62728", "T3R": "#fc9272"}


def pan_exp(x, y):
    return -math.degrees(math.atan2(y - BASE[1], x - BASE[0])) - 1.4


def topview(ax):
    """C frame 를 로봇에서 상자를 보는 방향으로: 가로 = y (왼쪽이 +y = 로봇 왼쪽), 세로 = x (위가 상자 쪽)."""
    for k, (x, y) in KN.items():
        ax.plot(y, x, "s", ms=11, mfc="none", mec="k", lw=1)
        ax.text(y + 1.0, x + 0.8, k, fontsize=8)
    ax.plot(BASE[1], BASE[0], "k^", ms=10)
    ax.text(BASE[1] + 1, BASE[0] - 1.5, "robot base (est.)", fontsize=8)
    ax.axhspan(0, 13, color="#c8a27a", alpha=0.25)
    ax.text(12, 6, "box", fontsize=9)
    ax.set_xlim(45, -25)
    ax.set_ylim(-40, 14)
    ax.set_xlabel("y cm (← robot left   |   robot right →)")
    ax.set_ylabel("x cm (box ↑)")
    ax.set_aspect("equal")


def main():
    T = pd.read_csv(HERE / "grasp_train.csv")
    E = pd.read_csv(HERE / "grasp_eval.csv")
    E0 = E[E.event == 0]

    # 1. 위치 + 첫 파지 pan 잔차
    fig, axs = plt.subplots(1, 2, figsize=(15, 7))
    ax = axs[0]
    topview(ax)
    for g, d in T.groupby("group"):
        ax.scatter(d.cube_y, d.cube_x, s=14, c=GCOL[g], label=f"train {g} (n={len(d)})", alpha=0.8)
    for _, r in E0.iterrows():
        ax.plot(r.cube_y, r.cube_x, "*", ms=16, c="gold", mec="k")
        L = 6
        b = math.radians(-(r.s_shoulder_pan + 1.4))
        ax.annotate("", xy=(BASE[1] + r.range_cm * math.sin(b), BASE[0] + r.range_cm * math.cos(b)),
                    xytext=(BASE[1], BASE[0]), arrowprops=dict(arrowstyle="->", color="orange", lw=1.2))
        ax.text(r.cube_y - 1, r.cube_x + 1.2, f"{r.run[9:15]} e{r.ep}\nΔpan {r.d_shoulder_pan:+.1f}°", fontsize=7)
    ax.legend(fontsize=7, loc="lower left")
    ax.set_title("cube start positions (train d2) · eval cubes ★ + policy pan direction at 1st close (orange)")
    ax = axs[1]
    for g, d in T.groupby("group"):
        ax.scatter(d.pan_exp, d.s_shoulder_pan, s=12, c=GCOL[g], label=g)
    ax.scatter(E0.pan_exp, E0.s_shoulder_pan, marker="*", s=200, c="gold", edgecolors="k", label="eval 1st close")
    lim = [-110, 110]
    ax.plot(lim, lim, "k--", lw=0.8)
    ax.set_xlabel("pan expected from cube bearing (°)  [+ = robot right]")
    ax.set_ylabel("pan at first close (state, °)")
    ax.legend(fontsize=8)
    ax.set_title("pan at grasp vs cube direction")
    fig.tight_layout()
    fig.savefig(HERE / "fig1_positions_pan.png", dpi=110)

    # 2. 평가 pan(t)
    Z = np.load(HERE / "eval_traj.npz")
    eps = sorted({(k.split("|")[0], int(k.split("|")[1])) for k in Z.files})
    fig, axs = plt.subplots(len(eps), 1, figsize=(12, 2.6 * len(eps)), squeeze=False)
    for ax, (r, e) in zip(axs[:, 0], eps):
        a, s = Z[f"{r}|{e}|action"], Z[f"{r}|{e}|state"]
        t = np.arange(len(a)) / 30
        ev = E[(E.run == r) & (E.ep == e)]
        ax.plot(t, a[:, 0], lw=0.8, label="pan action")
        ax.plot(t, s[:, 0], lw=0.8, label="pan state")
        ax2 = ax.twinx()
        ax2.plot(t, s[:, 5], c="gray", lw=0.6)
        ax2.set_ylabel("gripper", color="gray")
        x0, y0 = ev.start_x.iloc[0], ev.start_y.iloc[0]
        ax.axhline(pan_exp(x0, y0), c="gold", lw=2, label="cube (start) expected pan")
        dk = sorted(KN.items(), key=lambda kv: math.hypot(kv[1][0] - x0, kv[1][1] - y0))[:2]
        for k, (kx, ky) in dk:
            ax.axhline(pan_exp(kx, ky), c="k", ls=":", lw=1)
            ax.text(t[-1], pan_exp(kx, ky), f" {k}", fontsize=8, va="center")
        for _, q in ev.iterrows():
            ax.axvline(q.t, c="r", lw=0.6)
        ax.set_title(f"{r} ep{e}  cube ({x0:.1f}, {y0:.1f})", fontsize=9)
        ax.set_ylabel("pan °")
        ax.legend(fontsize=7, loc="upper right")
    axs[-1, 0].set_xlabel("s (red = close events)")
    fig.tight_layout()
    fig.savefig(HERE / "fig2_eval_pan_time.png", dpi=100)

    # 3. wrist 영상 큐브 중심 (닫힘 2 프레임 전)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(T.wu, T.wv, s=10, c=[GCOL[g] for g in T.group], label="train first grasp")
    ev = E.copy()
    vis = ev.wu.notna()
    ax.scatter(ev.wu[vis], ev.wv[vis], marker="x", s=60, c="k", label="eval close (cube visible)")
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.set_xlabel("u (wrist image, 0 = left)")
    ax.set_ylabel("v")
    ax.set_title(f"wrist cube centre at close · eval closes with no red in wrist: {(~vis).sum()}/{len(ev)}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "fig3_wrist_uv.png", dpi=110)

    # 4. 프로브
    p = HERE / "probe_start.csv"
    if p.exists():
        S = pd.read_csv(p)
        fig, axs = plt.subplots(1, 2, figsize=(13, 5.5))
        for g, d in S.groupby("group"):
            axs[0].errorbar(d.s_shoulder_pan, d.pred_pan, yerr=d.pred_pan_sd, fmt="o", ms=3, c=GCOL[g], label=g, alpha=0.7, lw=0.6)
        axs[0].plot(lim, lim, "k--", lw=0.8)
        axs[0].set_xlabel("human pan at grasp (°)")
        axs[0].set_ylabel("predicted pan, chunk end, obs at move start (°)")
        axs[0].legend(fontsize=8)
        axs[0].set_title("probe 'start' (in-sample): predicted vs demonstrated direction")
        axs[1].hist([S[S.group.str.endswith("K")].pred_minus_human, S[S.group.str.endswith("R")].pred_minus_human],
                    bins=np.arange(-40, 41, 2.5), label=["Known", "Random"], color=["#1f77b4", "#fc9272"])
        axs[1].set_xlabel("pred − human pan (°)  [+ = robot right]")
        axs[1].legend()
        fig.tight_layout()
        fig.savefig(HERE / "fig4_probe_start.png", dpi=110)
    p = HERE / "probe_swap.csv"
    if p.exists():
        W = pd.read_csv(p)
        modes = ["none", "both", "front_only", "wrist_only"]
        fig, axs = plt.subplots(1, 4, figsize=(18, 4.6), sharey=True)
        for ax, md in zip(axs, modes):
            d = W[W["mode"] == md]
            ax.scatter(d.pan_B, d.pred_pan, s=12, c="C0", label="vs pan_B (image source)")
            ax.scatter(d.pan_A, d.pred_pan, s=12, c="C3", marker="x", label="vs pan_A (state source)")
            ax.plot(lim, lim, "k--", lw=0.8)
            ax.set_title(f"images: {md}")
            ax.set_xlabel("demonstrated pan of episode (°)")
        axs[0].set_ylabel("predicted pan (°)")
        axs[0].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(HERE / "fig5_probe_swap.png", dpi=110)
    p = HERE / "probe_grid.csv"
    if p.exists():
        G = pd.read_csv(p)
        fig, axs = plt.subplots(1, 2, figsize=(16, 7))
        ax = axs[0]
        topview(ax)
        sc = ax.scatter(G.y, G.x, c=G.pred_minus_exp, cmap="coolwarm", vmin=-25, vmax=25, s=60, edgecolors="k", linewidths=0.3)
        plt.colorbar(sc, ax=ax, label="pred − expected pan (°)  red = robot right")
        ax.scatter(T.cube_y, T.cube_x, s=4, c="k", alpha=0.3)
        ax.set_title("probe 'grid' (synthetic front cube): direction error")
        ax = axs[1]
        ax.scatter(G.pan_exp, G.pred_pan, c=G.nearest_train_cm, cmap="viridis", s=25)
        for k, (kx, ky) in KN.items():
            ax.axhline(pan_exp(kx, ky), c="gray", ls=":", lw=0.8)
            ax.text(-108, pan_exp(kx, ky), k, fontsize=7)
        ax.plot(lim, lim, "k--", lw=0.8)
        ax.set_xlabel("expected pan for grid position (°)")
        ax.set_ylabel("predicted pan (°)  (dotted = K directions)")
        ax.set_title("colour = distance to nearest training cube (cm)")
        fig.tight_layout()
        fig.savefig(HERE / "fig6_probe_grid.png", dpi=110)
    print("figures written")


if __name__ == "__main__":
    main()
