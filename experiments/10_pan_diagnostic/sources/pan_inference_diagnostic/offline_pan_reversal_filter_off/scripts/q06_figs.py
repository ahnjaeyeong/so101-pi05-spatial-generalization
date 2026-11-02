"""q06 그림 (CPU, 기록 · 오프라인 표만 읽음).

fig1_A0_B1_timeline.png      A0 (필터 켬) · B1 (필터 끔): pan present / 보낸 Goal / RTC 출력 / RTC 끔 재구성 (같은 noise), 목표대, 손목 · front 가시성 띠
fig2_normal_vs_fail.png      20 판 s·(pan − 목표대 중앙) 시간축 (첫 닫힘 전), 사람 256 편 s·(pan − pan_c) p5–p95 띠 (onset 기준 아님, 판 시작 기준)
fig3_state_dir_dist.png      상태 묶음별 noise 재추론 실행 구간 (idx 10–29) 방향 비율: U vs G
fig4_rtc_on_off_A0B1.png     A0 · B1 chunk 별 실행 구간 Δpan 중앙 (U · G, 64 seed) + 기록 chunk (RTC) · 같은 noise RTC 끔
fig5_human_coverage.png      사람 256 편 지나침 크기 (자기 파지 pan 기준) 분포 vs A0 · B1 의 목표대 끝 기준 지나침
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 python3 q06_figs.py  (시스템 python3: matplotlib 있음, so101-env 에는 없음)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off"
TB, FG = OUT / "tables", OUT / "figs"
C1, C2, C3, C4, C7 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
GRAY, INK, MUTED = "#b0aea5", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": ["NanumGothic", "DejaVu Sans"], "axes.unicode_minus": False, "font.size": 9,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})


def fig1():
    T = pd.read_csv(TB / "q01b_ticks.csv.gz")
    E = pd.read_csv(TB / "q01b_episodes.csv").set_index("tag")
    fig, axs = plt.subplots(2, 1, figsize=(11, 8), sharex=False)
    for ax, tag in zip(axs, ("A0", "B1")):
        g, e = T[T.tag == tag], E.loc[tag]
        t = g.t_s.values
        ax.axhspan(e.bandf_lo, e.bandf_hi, color=C3, alpha=0.12, lw=0)
        far = e.bandf_lo if e.s_sign < 0 else e.bandf_hi
        ax.axhline(far + (-8 if e.s_sign < 0 else 8), color=MUTED, lw=0.8, ls="--")
        ax.plot(t, g.pan_raw, color=C3, lw=1.2, label="RTC 끔 재구성 (같은 noise) [재구성]")
        ax.plot(t, g.pan_rtc, color=C2, lw=1.4, label="RTC 출력 (queue) [실측]")
        ax.plot(t, g.pan_sent, color=C4, lw=1.2, label="보낸 Goal (필터 · clamp 뒤) [실측]")
        ax.plot(t, g.pan_present, color=C1, lw=2.0, label="Present pan [실측]")
        y0 = -132
        ws = np.where(g.wrist_vis & ~((g.wrist_u < .05) | (g.wrist_u > .95) | (g.wrist_v < .08) | (g.wrist_v > .92)), 2, np.where(g.wrist_vis, 1, 0))
        for val, col, lab in ((2, C1, "손목: 큐브 보임"), (1, C4, "손목: 테두리"), (0, C2, "손목: 안 보임")):
            m = ws == val
            ax.scatter(t[m], np.full(m.sum(), y0), s=6, color=col, marker="s", label=lab)
        fm = g.front_vis.values.astype(bool)
        ax.scatter(t[fm], np.full(fm.sum(), y0 - 6), s=6, color=MUTED, marker="s", label="front: 큐브 보임")
        ax.set_ylim(-142, 15)
        ax.set_title(f"{tag} ({'Arm Filter 켬' if e['cond'] == 'ON' else 'Arm Filter 끔'}) — 녹색 띠 = 목표대 (사람 ∪ 정책 성공 파지 pan), 점선 = over 경계 (+8°)", loc="left", fontsize=10)
        ax.set_ylabel("shoulder_pan (°)")
        ax.set_xlabel("판 시작 뒤 시간 (s)")
    axs[0].legend(loc="lower left", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.0, 0.05))
    fig.tight_layout()
    fig.savefig(FG / "fig1_A0_B1_timeline.png", dpi=130)


def fig2():
    T = pd.read_csv(TB / "q01b_ticks.csv.gz")
    E = pd.read_csv(TB / "q01b_episodes.csv").set_index("tag")
    H = pd.read_csv(TB / "q04_human_episodes.csv")
    L = pd.read_csv(TB / "q04c_human_pan_preclose.csv.gz").rename(columns={"ep": "episode_id", "frame": "frame_index", "pan": "measured_position"})
    grid = np.arange(0, 20 * 30)
    M = np.full((len(H), len(grid)), np.nan)
    for k, h in enumerate(H.itertuples()):
        if not h.s:
            continue
        x = L[L.episode_id == h.ep].sort_values("frame_index").measured_position.values[:h.close_start + 1]
        y = h.s * (x - h.pan_c)
        M[k, :min(len(y), len(grid))] = y[:len(grid)]
    fig, ax = plt.subplots(figsize=(11, 5))
    p5, p95 = np.nanpercentile(M, 5, axis=0), np.nanpercentile(M, 95, axis=0)
    n = np.sum(np.isfinite(M), axis=0)
    ok = n >= 20
    ax.fill_between(grid[ok] / 30, p5[ok], p95[ok], color=GRAY, alpha=0.35, lw=0, label="사람 256 편 s·(pan − 자기 파지 pan) p5–p95 (닫힘 전, ≥ 20 편 남은 시각)")
    ax.plot(grid[ok] / 30, np.nanmax(M, axis=0)[ok], color=MUTED, lw=0.8, ls=":", label="사람 최대")
    for tag, e in E.iterrows():
        g = T[(T.tag == tag) & T.before_first_close]
        y = e.s_sign * (g.pan_present.values - e.bandf_mid)
        if tag in ("A0", "B1"):
            ax.plot(g.t_s, y, color=C2 if tag == "A0" else C7, lw=2.0, label=f"{tag} (지나침 → −109°)")
        else:
            ax.plot(g.t_s, y, color=C1 if e.verdict == "P" else C4, lw=0.9, alpha=0.8)
    ax.plot([], [], color=C1, lw=0.9, label="정책 성공 판 (P)")
    ax.plot([], [], color=C4, lw=0.9, label="정책 실패 판 (F, A0 · B1 제외)")
    ax.axhline(0, color=INK, lw=0.6)
    ax.set_ylabel("목표 쪽 부호 s · (pan − 목표) (°)  — 0 위 = 지나침")
    ax.set_xlabel("판 시작 뒤 시간 (s), 첫 닫힘 전까지")
    ax.set_title("정상 접근 vs 실패 접근 — 정책 20 판은 목표대 중앙 기준, 사람은 자기 첫 파지 pan 기준", loc="left", fontsize=10)
    ax.set_ylim(-100, 95)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FG / "fig2_normal_vs_fail.png", dpi=130)


def fig3():
    M = pd.read_csv(TB / "q02b_state_metrics.csv")
    M = M[M.tdir != 0]
    M["grp"] = np.where(M.category == "dense_A0B1", M.tag + " " + M.zone + " · " + M.wstate.str.replace("wrist_", ""), M.category.str.replace("_", " ") + " · " + M.zone)
    rows = []
    for (grp, cond), g in M[M.cond.isin(["U", "G"])].groupby(["grp", "cond"]):
        n = g.n_seeds.sum()
        rows.append(dict(grp=grp, cond=cond, toward=g.exec_toward.sum() / n, hold=g.exec_hold.sum() / n, away=g.exec_away.sum() / n, n_states=len(g), n=n))
    D = pd.DataFrame(rows)
    grps = sorted(D.grp.unique())
    fig, ax = plt.subplots(figsize=(11, 0.45 * len(grps) * 2 + 1.5))
    y = 0
    yt, yl = [], []
    for grp in grps:
        for cond in ("U", "G"):
            r = D[(D.grp == grp) & (D.cond == cond)]
            if not len(r):
                continue
            r = r.iloc[0]
            left = 0
            for k, col in (("toward", C1), ("hold", GRAY), ("away", C2)):
                ax.barh(y, r[k], left=left, color=col, height=0.8, edgecolor="#fcfcfb", linewidth=1)
                left += r[k]
            ax.text(1.01, y, f"{r.n_states} 상태 × 64", va="center", fontsize=7, color=MUTED)
            yt.append(y)
            yl.append(f"{grp} [{cond}]")
            y += 1
        y += 0.6
    ax.set_yticks(yt, yl, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("실행 구간 (index 10–29) Δpan 방향 비율 (seed 합산)  — U = RTC 없음, G = 기록 prefix RTC")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=col, label=k) for k, col in (("목표 쪽 ≥ 2°", C1), ("|Δ| < 2°", GRAY), ("반대쪽 ≥ 2°", C2))], ncol=3, fontsize=8, frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0))
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(FG / "fig3_state_dir_dist.png", dpi=130)


def fig4():
    M = pd.read_csv(TB / "q02b_state_metrics.csv")
    Ch = pd.read_csv(TB / "q01b_chunks.csv")
    E = pd.read_csv(TB / "q01b_episodes.csv").set_index("tag")
    fig, axs = plt.subplots(2, 1, figsize=(11, 7))
    for ax, tag in zip(axs, ("A0", "B1")):
        e = E.loc[tag]
        for cond, col, lab in (("U", C3, "U 재추론 64 seed 중앙 (RTC 없음)"), ("G", C2, "G 재추론 64 seed 중앙 (RTC)")):
            g = M[(M.tag == tag) & (M.cond == cond)].sort_values("t_s")
            ax.plot(g.t_s, -e.s_sign * g.exec_med, color=col, lw=1.6, marker="o", ms=3, label=lab)
        c = Ch[Ch.tag == tag].sort_values("t_s")
        ax.plot(c.t_s, -e.s_sign * c.rtc_exec, color=INK, lw=0.8, ls="--", label="기록 chunk (RTC) [실측 chunk]")
        ax.plot(c.t_s, -e.s_sign * c.raw_exec, color=C7, lw=0.8, ls=":", label="기록 noise · RTC 끔 [재구성]")
        ax.axhline(0, color=INK, lw=0.6)
        fo = e.first_over_i / 30
        ax.axvline(fo, color=MUTED, lw=0.8)
        ax.text(fo, ax.get_ylim()[1] * 0.9, " over 진입", fontsize=8, color=MUTED)
        if np.isfinite(e.first_wrist_lost_i):
            ax.axvline(e.first_wrist_lost_i / 30, color=MUTED, lw=0.8, ls="--")
            ax.text(e.first_wrist_lost_i / 30, ax.get_ylim()[1] * 0.75, " 손목 1 s 놓침", fontsize=8, color=MUTED)
        ax.set_ylabel("실행 구간 Δpan (°)\n+ = 오른쪽 (over 에서 목표 쪽), − = 왼쪽 (계속)")
        ax.set_xlabel("chunk 관측 시각 (s)")
        ax.set_title(f"{tag} — chunk 마다 실행 구간 (index 10–29) pan 변화", loc="left", fontsize=10)
    axs[0].legend(fontsize=8, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FG / "fig4_rtc_on_off_A0B1.png", dpi=130)


def fig5():
    H = pd.read_csv(TB / "q04_human_episodes.csv")
    E = pd.read_csv(TB / "q01b_episodes.csv").set_index("tag")
    fig, ax = plt.subplots(figsize=(9, 4))
    bins = np.arange(-6, 80, 1)
    ax.hist(H.ovs.dropna(), bins=bins, color=C1, edgecolor="#fcfcfb", linewidth=0.5, label="사람 256 편: 닫힘 전 자기 파지 pan 을 지나친 최대 각 (248 편, need < 1° 8 편 제외)")
    for tag, col in (("A0", C2), ("B1", C7)):
        v = E.loc[tag].max_past_far_edge
        ax.axvline(v, color=col, lw=2)
        ax.text(v, ax.get_ylim()[1] * 0.85, f" {tag} {v:.0f}°\n (목표대 끝 기준)", color=INK, fontsize=8)
    ax.set_xlabel("지나친 최대 각 (°)")
    ax.set_ylabel("판 수")
    ax.set_title("d2 시연의 Pan 지나침 커버리지 vs 실패 2 판", loc="left", fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="center right")
    fig.tight_layout()
    fig.savefig(FG / "fig5_human_coverage.png", dpi=130)


if __name__ == "__main__":
    fig1()
    fig2()
    fig5()
    if (TB / "q02b_state_metrics.csv").exists():
        fig3()
        fig4()
