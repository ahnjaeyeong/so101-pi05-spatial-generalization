"""p11 파일럿 그림 (읽기만, CPU, /usr/bin/python3 — matplotlib).

figs/fig6_pilot_pan_timeline.png : 판마다 (저장된 시도만) pan 시간축
  - 실제 위치 state (실측, filter_log), 실행 명령 raw (실측, queue 출력)
  - 판 첫 chunk 전체 50 index (실측 기록, RTC 안내 없는 출력) — index 0–29 실행, 30–49 는 실행 안 된 계획
  - pe (사진 좌표 기준 pan, valid_* 만) 와 ± 사람 파지 산포 띠 (pe_sigma_grasp), 첫 닫힘 시각
figs/fig7_pilot_first_chunk.png  : 판 첫 chunk 의 need 대비 이동 비율 (index 29 / 49), 첫 닫힘 때 남은 오차 — 판별 점, K / free 구분
입력: pilot/pilot_episodes.csv (p09), 각 실행 analysis_pan/ (p07), diag/chunks/*.npz
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 /usr/bin/python3 p11_pilot_figs.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

D2 = Path.home() / "so101_runs/main_k8/d2"
OUT = D2 / "pan_inference_diagnostic"
FIG = OUT / "figs"
ROLL = D2 / "eval/rollouts"
FPS = 30
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                     "lines.linewidth": 2, "axes.unicode_minus": False})


def fig6(P):
    n = len(P)
    cols = 4
    rows = int(np.ceil(n / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(17, 3.4 * rows))
    axs = np.atleast_1d(axs).ravel()
    for ax, (_, r) in zip(axs, P.iterrows()):
        run = ROLL / r.run
        FL = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        f = FL[(FL.event == "cmd") & (FL.episode == r.episode)].sort_values("tick")
        t = np.arange(len(f)) / FPS
        if not np.isnan(r.pe if r.pe is not None else np.nan):
            sg = r.pe_sigma_grasp_deg if not pd.isna(r.pe_sigma_grasp_deg) else 0
            ax.axhspan(r.pe - sg, r.pe + sg, color=INK2, alpha=0.12, lw=0)
            ax.axhline(r.pe, color=INK2, lw=1, ls="--", label="pe ± 사람 파지 SD")
        if not pd.isna(r.get("first_chunk_id", np.nan)):
            z = np.load(run / "diag/chunks" / f"c{int(r.first_chunk_id):05d}.npz")["processed"][:, 0]
            ax.plot(np.arange(30) / FPS, z[:30], color=AQUA, lw=2.2, label="첫 chunk idx 0-29 (실행)")
            ax.plot(np.arange(29, 50) / FPS, z[29:], color=AQUA, lw=1.4, ls=":", label="첫 chunk idx 30-49 (실행 안 됨)")
        ax.plot(t, f.raw_shoulder_pan.values, color=ORANGE, lw=1.4, label="실행 명령 raw")
        ax.plot(t, f.state_shoulder_pan.values, color=BLUE, lw=1.4, label="실제 위치 state")
        if not pd.isna(r.get("first_close_s", np.nan)):
            ax.axvline(r.first_close_s, color=INK2, lw=0.8, ls=":")
        ttl = f"{r.label} ({r.group}, {r.coord_status})"
        ax.set_title(ttl, fontsize=9)
        ax.set_xlim(0, min(t[-1] if len(t) else 10, 20))
        ax.set_xlabel("판 시작 뒤 s (점선 = 첫 닫힘)")
    for ax in axs[n:]:
        ax.axis("off")
    axs[0].set_ylabel("shoulder_pan (°)")
    axs[0].legend(fontsize=7, frameon=False, loc="best")
    fig.suptitle("파일럿 12 판 pan: 실측 (state · 실행 명령 · 첫 chunk 전체) vs pe (판 시작 사진 좌표, 정책 행동 안 씀). 처음 20 s", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig6_pilot_pan_timeline.png", dpi=120)


def fig7(P):
    Q = P[P.pe.notna()]
    fig, axs = plt.subplots(1, 3, figsize=(15, 3.8))
    for ax, col, ttl in zip(axs, ["first_chunk_gain29", "first_chunk_gain49", "pan_err_at_close_sg"],
                            ["첫 chunk idx 29 (≈1 s) 이동 / need", "첫 chunk idx 49 (실행 안 됨) 이동 / need", "첫 닫힘 때 pe - pan (need 부호, 양수 = 못 미침, °)"]):
        for g, c, mk in (("K", BLUE, "o"), ("free", ORANGE, "s"), ("K_off", YELLOW, "^")):
            s = Q[Q.group == g]
            if len(s):
                ax.scatter(s.dist_K_cm, s[col], color=c, marker=mk, s=40, label=g, zorder=3)
                for _, r in s.iterrows():
                    ax.annotate(r.label, (r.dist_K_cm, r[col]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        if col == "pan_err_at_close_sg":
            sg = Q.pe_sigma_grasp_deg.median()
            ax.axhspan(-sg, sg, color=INK2, alpha=0.12, lw=0)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(ttl, fontsize=9)
        ax.set_xlabel("가장 가까운 K 까지 거리 (cm, 사진 좌표)")
    axs[0].legend(fontsize=8, frameon=False)
    fig.suptitle("판별 첫 Pan 행동 vs K 거리 (K 3 cm 넘으면 좌표 정확도 미검증). 띠 = ± 사람 파지 SD", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig7_pilot_first_chunk.png", dpi=120)


if __name__ == "__main__":
    from matplotlib import font_manager
    for nm in ("NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"):
        if any(nm in f.name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = nm
            break
    P = pd.read_csv(OUT / "pilot/pilot_episodes.csv")
    fig6(P)
    fig7(P)
    print("ok")
