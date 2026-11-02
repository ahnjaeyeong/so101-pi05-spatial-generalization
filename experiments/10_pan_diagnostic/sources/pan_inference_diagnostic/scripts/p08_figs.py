"""p08 그림 (읽기만, CPU). figs/fig1_pan_timeline.png (판별 pan: 실제 위치 · 실행 명령 · 기준 pe · 가까운 사람 명령),
figs/fig2_closed_loop_gain.png (남은 오차 구간별 1 s 뒤 명령 이동 비율, 사람 vs 정책),
figs/fig3_raw_vs_rtc_focus.png (p06c: 집중 chunk 기록 vs 재구성 U/G), fig4_seam_counterfactual.png (p03c: filt/ep0 경계 inference_delay 0 vs 11),
figs/fig5_chunk0_distribution.png (p03c/p06d: 첫 chunk noise 256 개 분포 vs 기록)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 /usr/bin/python3 p08_figs.py  (so101-env 에 matplotlib 없음. 입력 csv.gz 는 so101-env 로 parquet 에서 내보냄)
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

D2 = Path.home() / "so101_runs/main_k8/d2"
ATAB = D2 / "data_coverage_audit/tables"
OUT = D2 / "pan_inference_diagnostic"
TAB, FIG = OUT / "tables", OUT / "figs"
FPS = 30
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                     "lines.linewidth": 2, "axes.unicode_minus": False})


def human_traces(cx, cy, k=10):
    W = pd.read_csv(TAB / "p08_human_pan.csv.gz")  # a02_frames.parquet 의 pan 열 (시스템 python3 에 pyarrow 없음)
    E = pd.read_csv(ATAB / "a02_events.csv")
    T = pd.read_csv(ATAB / "a01_cube_table.csv")
    idx = np.argsort(np.hypot(T.cube_x - cx, T.cube_y - cy).values)[:k]
    out = []
    for e in idx:
        g = W[W.ep == e]
        on = int(E.onset[e])
        a = g.a_shoulder_pan.values[on:on + 6 * FPS]
        out.append(a - g.s_shoulder_pan.values[on] + 0.0)
    n = min(len(x) for x in out)
    return np.array([x[:n] for x in out])


def fig1():
    T = pd.read_csv(TAB / "p01_ticks.csv.gz")
    P = pd.read_csv(TAB / "p02_policy_episodes.csv")
    M = pd.read_csv(TAB / "p01_merges.csv")
    fig, axs = plt.subplots(1, 5, figsize=(17, 3.6), sharex=True)
    for ax, (_, r) in zip(axs, P.iterrows()):
        run = "20261026_" + ("135128_" if r.ep.startswith("20k_t1_try3/") else "140246_") + r.ep.split("/")[0]
        e = int(r.ep[-1])
        g = T[(T.run == run) & (T.ep == e)]
        on = int(round(r.onset_s * FPS))
        t = (np.arange(len(g)) - on) / FPS
        m = (t >= -0.5) & (t <= 6)
        cx, cy = map(float, r.cube.strip("()").split(","))
        H = human_traces(cx, cy) + r.s_on
        th = np.arange(H.shape[1]) / FPS
        ax.fill_between(th, np.percentile(H, 10, 0), np.percentile(H, 90, 0), color=GRID, lw=0, label="사람 명령 (가까운 10 편, 10–90%)")
        ax.axhline(r.pe, color=INK2, lw=1, ls="--", label="기준 pe (큐브 추정)")
        mf = M[(M.run == run) & (M.ep == e)].merge_frame.values
        for f in mf:
            tf = (f - on) / FPS
            if -0.5 <= tf <= 6:
                ax.axvline(tf, color=GRID, lw=0.8, zorder=0)
        ax.plot(t[m], g.raw_shoulder_pan.values[m], color=ORANGE, label="실행 명령 raw (queue 출력)")
        ax.plot(t[m], g.state_shoulder_pan.values[m], color=BLUE, label="실제 위치 state")
        ax.set_title(f"{r.ep}  필요 {r.need:+.0f}°  K 거리 {r.dist_K:.1f} cm", fontsize=9)
        ax.set_xlabel("onset 뒤 시간 (s)")
    axs[0].set_ylabel("shoulder_pan (°)")
    axs[0].legend(loc="best", fontsize=7, frameon=False)
    fig.suptitle("d2 020000 실물 5 판 — 처음 6 s pan (세로 회색선 = chunk merge)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_pan_timeline.png", dpi=130)


def fig2():
    G = pd.read_csv(TAB / "p02_closed_loop_gain.csv")
    bins = [3, 6, 12, 25, 200]
    lab = ["3–6°", "6–12°", "12–25°", "≥25°"]
    G["b"] = pd.cut(G.resid.abs(), bins, right=False, labels=lab)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for k, (who, col, nm) in enumerate((("human", BLUE, "사람 256 편 (리더 명령)"), ("policy", ORANGE, "정책 5 판 (raw 명령)"))):
        s = G[G.who == who].groupby("b", observed=False).g30
        x = np.arange(len(lab)) + (k - 0.5) * 0.25
        med, q1, q3, n = s.median(), s.quantile(.25), s.quantile(.75), s.size()
        ax.vlines(x, q1, q3, color=col, lw=2)
        ax.plot(x, med, "o", color=col, ms=8, mec=SURF, mew=2, label=nm)
        for xi, mi, ni in zip(x, med, n):
            ax.annotate(f"n {ni}", (xi, mi), textcoords="offset points", xytext=(6, -3), fontsize=7, color=INK2)
    ax.axhline(1, color=INK2, lw=1, ls="--")
    ax.set_xticks(np.arange(len(lab)), lab)
    ax.set_xlabel("그 시점 남은 pan 오차 |pe - state|")
    ax.set_ylabel("1 s 뒤 명령이 덮은 비율\n(a[t+30] - s[t]) / (pe - s[t])")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("남은 pan 오차 대비 1 s 동안의 명령 이동 (중앙값, 막대 = IQR)", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_closed_loop_gain.png", dpi=130)


def _off(tr):
    """chunk index → 판 프레임 오프셋 (실행된 index 의 frame - idx)."""
    ex = tr.dropna(subset=["frame"])
    return int((ex.frame - ex.idx).median())


def fig3():
    """집중 chunk: 기록된 실행 명령 (실측) vs 재구성 U (RTC 안내 없음) / G (RTC 안내) noise 32 개 p10–p90 · 중앙값."""
    f = TAB / "p06c_traj.csv"
    if not f.exists():
        return False
    TR = pd.read_csv(f)
    P = pd.read_csv(TAB / "p02_policy_episodes.csv")
    cases = [("20k_t1_try3_filt/ep1", [0], "filt/ep1 (새 위치): 첫 chunk"), ("20k_t1_try3_filt/ep0", [0, 1], "filt/ep0: chunk 0 → 1 경계"),
             ("20k_t1_try3_filt/ep2", [0, 1], "filt/ep2: chunk 0 → 1")]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (ep, ks, title) in zip(axs, cases):
        pe = float(P[P.ep == ep].pe.iloc[0])
        ax.axhline(pe, color=INK2, lw=1, ls="--", label="기준 pe (영상 추정)")
        for k in ks:
            tr = TR[(TR.ep == ep) & (TR.chunk_id == k)].sort_values("idx")
            fr = (tr.idx + _off(tr)) / FPS
            ax.fill_between(fr, tr.U_p10, tr.U_p90, color=AQUA, alpha=0.15, lw=0)
            ax.plot(fr, tr.U_p50, color=AQUA, lw=1.2, label="재구성 U: RTC 안내 없음 (p10–p90, 중앙)" if k == ks[-1] else None)
            if k > 0:
                ax.plot(fr, tr.G_p50, color=YELLOW, lw=1.2, label="재구성 G: RTC 안내 (중앙)")
            ex = tr.dropna(subset=["frame"])
            ax.plot(ex.frame / FPS, ex.L, color=ORANGE, lw=2.2, label="기록된 실행 명령 (실측)" if k == ks[0] else None)
            ax.plot(ex.frame / FPS, ex.state, color=BLUE, lw=1.4, label="실제 위치 state (실측)" if k == ks[0] else None)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("판 시작 뒤 시간 (s)")
    axs[0].set_ylabel("shoulder_pan (°)")
    axs[0].legend(loc="best", fontsize=7, frameon=False)
    for ax in axs[1:]:
        h, l = ax.get_legend_handles_labels()
        if "재구성 G: RTC 안내 (중앙)" in l:
            i = l.index("재구성 G: RTC 안내 (중앙)")
            ax.legend([h[i]], [l[i]], loc="lower right", fontsize=7, frameon=False)
    fig.suptitle("기록 (실측) vs 오프라인 재구성 — 같은 관측 (dataset 프레임) · noise 32 개. 재구성 값은 실물 기록이 아님", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_raw_vs_rtc_focus.png", dpi=130)
    return True


def fig4():
    """filt/ep0 chunk 1 반사실: inference_delay 0 (기록 당시 규칙) vs 11. prefix 미기록 부분 = 앞 chunk 마지막 값 고정 (hold)."""
    f = TAB / "p03c_counterfactual.npz"
    if not f.exists():
        return False
    Z = np.load(f)
    TR = pd.read_csv(TAB / "p06c_traj.csv")
    ep = "20k_t1_try3_filt/ep0"
    t1 = TR[(TR.ep == ep) & (TR.chunk_id == 1)].sort_values("idx")
    t0 = TR[(TR.ep == ep) & (TR.chunk_id == 0)].sort_values("idx")
    off = _off(t1)
    x = (np.arange(50) + off) / FPS
    fig, axs = plt.subplots(1, 3, figsize=(15, 3.8), sharey=True)
    for ax, (cond, nm, col) in zip(axs, [("U", "RTC 안내 없음 (U)", AQUA), ("G_d0_hold", "RTC 안내, inference_delay 0 (기록 당시)", YELLOW),
                                          ("G_d11_hold", "RTC 안내, inference_delay 11 (반사실)", "#8a5cd0")]):
        A = Z[f"filt_ep0_c1__{cond}"][:, :, 0]
        for a in A:
            ax.plot(x, a, color=col, lw=0.6, alpha=0.35)
        ax.plot(x, np.median(A, 0), color=col, lw=2, label=f"{nm}: noise 32 개, 굵은 선 = 중앙")
        e0 = t0.dropna(subset=["frame"])
        e1 = t1.dropna(subset=["frame"])
        ax.plot(e0.frame / FPS, e0.L, color=ORANGE, lw=2.2, label="기록된 실행 명령 (실측)")
        ax.plot(e1.frame / FPS, e1.L, color=ORANGE, lw=2.2)
        ax.axvline((10 + off) / FPS, color=INK2, lw=0.8, ls=":")
        ax.set_title(nm, fontsize=9)
        ax.set_xlabel("판 시작 뒤 시간 (s) — 점선 = chunk 1 첫 실행 index 10")
        ax.legend(loc="lower right", fontsize=7, frameon=False)
    axs[0].set_ylabel("shoulder_pan (°)")
    fig.suptitle("filt/ep0 chunk 경계 (기록 -14.7°): 같은 관측 · noise 로 오프라인 반사실. 실물에 적용하지 않음", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_seam_counterfactual.png", dpi=130)
    return True


def fig5():
    """chunk 0 (prefix 없음) noise 256 개: index 29 (관측 뒤 ≈1 s) 에서 need 대비 이동 비율 분포 + 기록값."""
    f = TAB / "p03c_counterfactual.npz"
    if not f.exists():
        return False
    Z = np.load(f)
    U = pd.read_csv(TAB / "p06d_chunk0_u256.csv")
    T = pd.read_csv(TAB / "p01_ticks.csv.gz")
    fig, axs = plt.subplots(1, 5, figsize=(16, 3.2), sharey=True)
    runs = {"try3": "20261026_135128_20k_t1_try3", "filt": "20261026_140246_20k_t1_try3_filt"}
    for ax, (_, r) in zip(axs, U.iterrows()):
        key, ep = r.ep.split("/")
        g = T[(T.run == runs[key]) & (T.ep == int(ep[2:]))]
        s0 = g.state_shoulder_pan.values[0]
        A = Z[f"{key}_{ep}_c0__U256"][:, 29, 0]
        fr = (A - s0) / r.resid
        ax.hist(np.clip(fr, -0.3, 1.3), bins=np.linspace(-0.3, 1.3, 33), color=AQUA, edgecolor=SURF, linewidth=1)
        ax.axvline(r.logged_f29, color=ORANGE, lw=2.2, label=f"기록 {r.logged_f29:.2f} (백분위 {r.logged_rank_in_u256:.2f})")
        ax.set_title(f"{r.ep}  need {r.resid:+.0f}°", fontsize=9)
        ax.set_xlabel("(U[29] - s0) / need")
        ax.legend(loc="upper right", fontsize=7, frameon=False)
    axs[0].set_ylabel("noise 개수 (256 중)")
    fig.suptitle("첫 chunk (RTC 없음) 1 s 지점 이동 비율: 재구성 noise 256 개 분포 vs 기록 (실측)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig5_chunk0_distribution.png", dpi=130)
    return True


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    from matplotlib import font_manager
    for nm in ("NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"):
        if any(nm in f.name for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = nm
            break
    fig1()
    fig2()
    print("fig3", fig3(), "fig4", fig4(), "fig5", fig5())
