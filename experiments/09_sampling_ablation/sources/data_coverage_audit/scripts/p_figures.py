"""그림 (시스템 python3 + matplotlib; so101-env 에는 matplotlib 없음). 입력은 tables/*.csv 만 (parquet 은 a05 가 csv 로 내보낸 요약 사용).
출력 figs/fig01–fig07 *.png
사용: nice -n 19 /usr/bin/python3 p_figures.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

AUD = Path(__file__).resolve().parent.parent
TAB, FIG = AUD / "tables", AUD / "figs"
plt.rcParams.update({"font.family": ["NanumSquare", "DejaVu Sans"], "axes.unicode_minus": False, "font.size": 9,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
GC = {"T1K": "#2a78d6", "T1R": "#eb6834", "T3K": "#1baf7a", "T3R": "#eda100"}   # 검증된 기본 categorical 1–4 순서
POL = "#e34948"
CFG = yaml.safe_load(open(Path.home() / "so101_boxpick/config/redbox8_layouts.yaml"))
KN = {k: (v["xy_cm"] if isinstance(v, dict) else v) for k, v in CFG["known_positions"].items()}


def fig01():
    T = pd.read_csv(TAB / "a04_cube_positions.csv")
    G = pd.read_csv(TAB / "a04_gap_grid.csv")
    EV = pd.read_csv(TAB / "a04_eval_positions.csv")
    base = json.load(open(TAB / "a00_base_fit.json"))["base_xy_cm"]
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.4))
    for a in ax:
        a.set_aspect("equal")
        a.set_xlabel("y (cm, + = 로봇 왼쪽)")
        a.set_ylabel("x (cm, + = 상자 쪽)")
    # 왼쪽: 판 위치 (y 를 가로, x 를 세로, 로봇 시점처럼 왼쪽이 + y 가 되도록 가로축 뒤집음)
    a = ax[0]
    for g, c in GC.items():
        d = T[T.group == g]
        a.scatter(d.cube_y, d.cube_x, s=16, color=c, label=f"{g} ({len(d)})", edgecolor="#fcfcfb", linewidth=0.6, zorder=3)
    for k, (x, y) in KN.items():
        a.scatter(y, x, s=160, facecolor="none", edgecolor="#0b0b0b", linewidth=1.2, zorder=4)
        a.annotate(k, (y, x), xytext=(6, 6), textcoords="offset points", fontsize=8)
    for z in CFG["workspace"].get("hard_zones_cm", []):
        p = np.array(z["polygon"] + [z["polygon"][0]])
        a.plot(p[:, 1], p[:, 0], color="#52514e", lw=1, ls="--")
        a.annotate("hard zone (로봇 앞)", (p[:, 1].mean(), p[:, 0].mean()), ha="center", fontsize=8, color="#52514e")
    a.scatter(EV.start_y, EV.start_x, marker="x", s=60, color=POL, label="d2 실물 평가 5판", zorder=5)
    a.scatter(base[1], base[0], marker="+", s=120, color="#0b0b0b", label="베이스 (pan 맞춤 추정)")
    a.invert_xaxis()
    a.legend(loc="lower left", fontsize=8, frameon=False)
    a.set_title("큐브 시작 위치 (front 영상 + H 추정)")
    # 오른쪽: 반경 3 cm 안 학습 판 수
    b = ax[1]
    Gk = G[~G.hard_zone]
    sc = b.scatter(Gk.y, Gk.x, c=np.minimum(Gk.n_eps_3cm, 20), cmap="Blues", s=6, marker="s", vmin=0, vmax=20)
    b.scatter(T.cube_y, T.cube_x, s=3, color="#0b0b0b", zorder=3)
    b.invert_xaxis()
    plt.colorbar(sc, ax=b, label="반경 3 cm 안 학습 판 수 (20 이상은 20)")
    b.set_title("위치 밀도 (볼록 껍질 안, hard zone 제외)")
    fig.tight_layout()
    fig.savefig(FIG / "fig01_cube_positions.png", dpi=140)


def fig02():
    S = pd.read_csv(TAB / "a03_initial_states.csv")
    J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
    fig, ax = plt.subplots(1, 5, figsize=(13, 3.6))
    for i, j in enumerate(J):
        a = ax[i]
        for k, g in enumerate(GC):
            d = S[S.group == g]
            x0 = np.full(len(d), k) + np.random.default_rng(k).uniform(-0.18, 0.18, len(d))
            a.scatter(x0, d[f"s0_{j}"], s=8, color=GC[g])
            a.scatter(x0 + 5, d[f"sg_{j}"], s=8, color=GC[g])
        a.set_xticks([1.5, 6.5], ["시작", "첫 파지"])
        a.set_title(j)
        a.axvline(3.5, color="#c3c2b7", lw=0.8)
    ax[0].set_ylabel("팔로워 관절 (°)")
    fig.legend([plt.Line2D([], [], marker="o", ls="", color=c) for c in GC.values()], list(GC), loc="upper right", ncol=4, frameon=False)
    fig.suptitle("시작 프레임 vs 첫 파지 순간 관절값 (판 = 점)", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG / "fig02_start_vs_grasp.png", dpi=140)


def fig03():
    F = pd.read_csv(TAB / "a03_pan_first_move.csv")
    R = pd.read_csv(TAB / "a07_policy_episodes.csv")
    E = pd.read_csv(TAB / "a09_events.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    a = ax[0]
    bins = np.arange(0, 6.01, 0.2)
    a.hist(F.pan_reach2_from_onset_s.clip(upper=6), bins=bins, color="#2a78d6", label="pan 최종 ±2° 처음 도달 (onset 뒤)")
    a.hist(F.pan_settle2_before_grasp_s.clip(upper=6), bins=bins, color="#eb6834", alpha=0.75, label="pan 최종 ±2° 머물기 시작 (파지 전)")
    a.set_xlabel("s")
    a.set_ylabel("판 수 (d2 256편)")
    a.legend(frameon=False, fontsize=8)
    a.set_title("사람 시연 pan 정렬 시점")
    b = ax[1]
    sets = ["ref T1K", "ref T1R", "ref T3K", "ref T3R", "ref T2K", "ref T2R", "d2 T1K", "d2 T1R", "d2 T3K", "d2 T3R"]
    data = [E[E.set == s].pan_t90_s.dropna().values for s in sets]
    bp = b.boxplot(data, vert=False, labels=sets, showfliers=False, widths=0.6, patch_artist=True)
    for p, s in zip(bp["boxes"], sets):
        p.set_facecolor("#cde2fb" if s.startswith("ref") else "#9ec5f4")
    for i, v in enumerate(R.pan_t90_s.values):
        b.scatter(v, len(sets) + 1, marker="x", color=POL, s=40)
    b.set_yticks(list(range(1, len(sets) + 2)), sets + ["d2 정책 (실물 5판)"])
    b.set_xlabel("pan 이 필요 회전의 90% 를 넘긴 시간 (s, 구간 시작 뒤)")
    b.set_title("pan 회전 속도: 외부 SO-101 · d2 사람 · d2 정책")
    fig.tight_layout()
    fig.savefig(FIG / "fig03_pan_alignment_timing.png", dpi=140)


def fig04():
    S = pd.read_csv(TAB / "a05_snapshots.csv")
    Q4 = pd.read_csv(TAB / "a05_q4.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    a = ax[0]
    t = [5, 3, 2, 1, 0.5, 0]
    a.plot(t, S.rt_abs_med, marker="o", color="#2a78d6", lw=2, label="|r_t| 중앙값 (접선)")
    a.plot(t, S.rt_abs_p90, marker="o", color="#2a78d6", lw=1, ls="--", label="|r_t| 90%")
    a.plot(t, S.rr_abs_med, marker="s", color="#eb6834", lw=2, label="|r_r| 중앙값 (반지름)")
    a.plot(t, S.rz_med, marker="^", color="#1baf7a", lw=2, label="높이 차 r_z 중앙값")
    a.invert_xaxis()
    a.set_xlabel("첫 파지까지 남은 시간 (s)")
    a.set_ylabel("최종 파지 TCP 까지 (cm)")
    a.legend(frameon=False, fontsize=8)
    a.set_title("사람 시연: 파지 전 남은 거리 (256편)")
    b = ax[1]
    for thr, c in ((0.5, "#86b6ef"), (1.0, "#2a78d6"), (1.5, "#184f95")):
        d = Q4[Q4.thr_cm == thr]
        b.plot([3, 2, 1.5, 1], d.n_eps, marker="o", color=c, label=f"|r_t| ≥ {thr} cm")
    b.invert_xaxis()
    b.set_xlabel("첫 파지까지 남은 시간 (s)")
    b.set_ylabel("판 수 (256 중)")
    b.legend(frameon=False, fontsize=8)
    b.set_title("큰 접선 거리가 남은 시연 수")
    fig.tight_layout()
    fig.savefig(FIG / "fig04_pregrasp_residual.png", dpi=140)


def fig05():
    names = [("a06_cells_eps_label_3s.csv", "L: 기존 영상 라벨 tan"), ("a06_cells_eps_Lrel_3s.csv", "L′: 라벨 − 닫힘 순간 값"), ("a06_cells_eps_F_3s.csv", "F: 관절 −r_t")]
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    for a, (f, t) in zip(ax, names):
        M = pd.read_csv(TAB / f, index_col=0)
        im = a.imshow(M.values, cmap="Blues", vmin=0, vmax=60, aspect="auto", origin="lower")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M.values[i, j]
                a.text(j, i, str(v), ha="center", va="center", fontsize=7, color="#fcfcfb" if v > 35 else "#0b0b0b")
        a.set_xticks(range(M.shape[1]), [c.replace("(", "").replace("]", "") for c in M.columns], rotation=60, fontsize=7)
        a.set_yticks(range(M.shape[0]), M.index, fontsize=7)
        a.set_xlabel("접선 (cm, + = 큐브가 로봇 왼쪽으로 도는 쪽)")
        a.set_title(t)
        a.grid(False)
    ax[0].set_ylabel("wrist roll (°)")
    fig.colorbar(im, ax=ax, label="고유 판 수 (닫힘 3 s 안)", shrink=0.8)
    fig.suptitle("roll 15° × 접선 0.5 cm 칸의 판 수 — 측정 방법별", x=0.01, ha="left")
    fig.savefig(FIG / "fig05_roll_tan_cells.png", dpi=140, bbox_inches="tight")


def fig06():
    TR = pd.read_csv(TAB / "a07_policy_trace.csv")
    B = pd.read_csv(TAB / "a07_human_band.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    a = ax[0]
    a.fill_between(B.tb, B.pan_err_p5, B.pan_err_p95, color="#cde2fb", label="사람 5–95% (같은 남은 시간)")
    a.fill_between(B.tb, B.z_p5 * 0, B.z_p5 * 0, color="none")
    for (run, ep), d in TR.groupby(["run", "ep"]):
        a.plot(d.t_to_close, d.pan_err, lw=1.2, label=f"{run[16:]} ep{ep}")
    a.set_xlim(20, 0)
    a.set_xlabel("첫 닫힘까지 남은 시간 (s)")
    a.set_ylabel("pan − 큐브 기대 pan (°)")
    a.legend(frameon=False, fontsize=7)
    a.set_title("정책 실물 5판 pan 오차 vs 사람 분포")
    b = ax[1]
    for (run, ep), d in TR.groupby(["run", "ep"]):
        b.plot(d.t_to_close, np.hypot(d.e_t, d.e_r), lw=1.2, label=f"{run[16:]} ep{ep}")
    b.set_xlim(20, 0)
    b.set_ylim(0, 25)
    b.set_xlabel("첫 닫힘까지 남은 시간 (s)")
    b.set_ylabel("TCP–큐브 수평 거리 (cm)")
    b.set_title("정책: 큐브까지 거리")
    fig.tight_layout()
    fig.savefig(FIG / "fig06_policy_vs_human.png", dpi=140)


def fig07():
    E = pd.read_csv(TAB / "a09_events.csv")
    sets = ["ref T1K", "ref T1R", "ref T3K", "ref T3R", "ref T2K", "ref T2R", "d2 T1K", "d2 T1R", "d2 T3K", "d2 T3R"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    a = ax[0]
    bp = a.boxplot([E[E.set == s].roll_change.abs().values for s in sets], vert=False, labels=sets, showfliers=False, patch_artist=True)
    for p, s in zip(bp["boxes"], sets):
        p.set_facecolor("#cde2fb" if s.startswith("ref") else "#9ec5f4")
    a.set_xlabel("|wrist roll 변화| 접근 시작 → 닫힘 (°)")
    a.set_title("wrist roll 사용량")
    b = ax[1]
    bp = b.boxplot([E[E.set == s].seg0_shoulder_pan.values - E[E.set == s].seg0_shoulder_pan.median() for s in sets], vert=False, labels=sets,
                   showfliers=False, patch_artist=True)
    for p, s in zip(bp["boxes"], sets):
        p.set_facecolor("#cde2fb" if s.startswith("ref") else "#9ec5f4")
    b.set_xlabel("접근 시작 pan − 그 세트 중앙값 (°)")
    b.set_title("접근 시작 상태 다양성 (외부 T2 = 연속 파지)")
    fig.tight_layout()
    fig.savefig(FIG / "fig07_reference_compare.png", dpi=140)


if __name__ == "__main__":
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07):
        f()
        print(f.__name__)
