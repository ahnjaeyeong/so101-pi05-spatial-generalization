"""06 wrist roll × 접선 위치 오차 조합 (읽기만 함). 입력 vision_probe/labels_v2.csv, tables/a05_frames_rel.parquet, a02_events.csv,
기존 action_bottleneck/c5_cells_roll_x_tan_episodes.csv · sampling_ablation/s1_cells.csv (재현 비교용)
출력 tables/a06_*.csv/json, _facts/06.md

오차 측정 두 가지
  L (영상): labels_v2 tan_cm — wrist 영상 큐브 중심 − 사람 파지 기준점, roll 로 돌린 탁자 접선 (cm). 닫힘 3 s 전 ~ 닫힘, probe_ok 프레임
            (닫힘 1 s 안 3 프레임 간격). 부호: 큐브 − 집게 (a05: r_t 와 상관 −0.66, 2–3 s 기울기 −0.92).
  F (관절): a05 r_t — TCP(t) − TCP(c) 접선 (집게 − 최종 위치). 모든 프레임.
기본 칸 = 기존 정의 roll 15° (−60…60) × tan 0.5 cm (−2.5…2.0). 판 수 = 고유 episode 수 (프레임 수와 따로).
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a06_roll_error.py
"""
import json

import numpy as np
import pandas as pd

import ac

RB = np.arange(-60, 61, 15)
TB = np.arange(-2.5, 2.01, 0.5)


def table(P, rcol, tcol, rb, tb, what="eps"):
    r = pd.cut(P[rcol], rb)
    t = pd.cut(P[tcol], tb)
    g = P.groupby([r, t], observed=False)
    return (g.ep.nunique() if what == "eps" else g.size()).unstack(fill_value=0)


def cell_stats(tab):
    v = tab.values
    holes = 0
    for i in range(v.shape[0]):
        nz = np.where(v[i] > 0)[0]
        if len(nz):
            holes += int((v[i, nz.min():nz.max() + 1] == 0).sum())
    return dict(cells=int(v.size), ge1=int((v >= 1).sum()), rare_1_4=int(((v >= 1) & (v <= 4)).sum()), ge5=int((v >= 5).sum()),
                empty=int((v == 0).sum()), interior_holes=holes)


def main():
    out = {}
    Lb = pd.read_csv(ac.D2 / "vision_probe/labels_v2.csv")
    P = Lb[Lb.probe_ok].copy()
    W = pd.read_parquet(ac.TAB / "a05_frames_rel.parquet")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    # ---- 1. 재현 ----
    c5 = pd.read_csv(ac.D2 / "action_bottleneck/c5_cells_roll_x_tan_episodes.csv", index_col=0)
    mine15 = table(P[P.t_to_close <= 1.5], "roll", "tan_cm", RB, TB)
    s1 = pd.read_csv(ac.D2 / "sampling_ablation/s1_cells.csv", index_col=0)
    mine3 = table(P, "roll", "tan_cm", RB, TB)
    rep = dict(c5_equal=bool((c5.values == mine15.values).all()), c5_stats=cell_stats(mine15),
               s1_equal=bool((s1.values == mine3.values).all()), s1_stats=cell_stats(mine3),
               label_frames=int(len(P)), label_eps=int(P.ep.nunique()))
    # ---- 2. 민감도 ----
    sens = []
    for win in (1.0, 1.5, 3.0):
        D = P[P.t_to_close <= win]
        for nm, rb, tb in (("roll15×tan0.5 (기존)", RB, TB), ("경계 반칸 이동 (+7.5°, +0.25)", RB + 7.5, TB + 0.25),
                           ("roll10×tan0.5", np.arange(-60, 61, 10), TB), ("roll20×tan0.5", np.arange(-60, 61, 20), TB),
                           ("roll30×tan0.5", np.arange(-60, 61, 30), TB), ("roll15×tan0.25", RB, np.arange(-2.5, 2.01, 0.25)),
                           ("roll15×tan1.0", RB, np.arange(-3.0, 2.01, 1.0))):
            st = cell_stats(table(D, "roll", "tan_cm", rb, tb))
            sens.append(dict(window_s=win, binning=nm, **st))
    # L' = 판마다 닫힘 프레임 라벨값을 뺀 tan (최종 파지 위치 기준, 영상)
    lastv = P.sort_values("frame").groupby("ep").tail(1).set_index("ep")
    P["tan_rel_close"] = P.tan_cm - P.ep.map(lastv.tan_cm)
    for win in (1.5, 3.0):
        D = P[P.t_to_close <= win]
        for nm, rb, tb in (("L′: roll15×(tan−tan(c))0.5", RB, TB), ("L′: 경계 반칸 이동", RB + 7.5, TB + 0.25)):
            sens.append(dict(window_s=win, binning=nm, **cell_stats(table(D, "roll", "tan_rel_close", rb, tb))))
    # 관절 측정 F (r_t) 로 같은 표
    WF = W[(W.t_to_grasp >= 0) & (W.t_to_grasp <= 3)].rename(columns={"s_wrist_roll": "roll"})
    WF = WF.assign(neg_rt=-WF.r_t)     # 라벨과 같은 부호 (큐브 − 집게)
    for win in (1.5, 3.0):
        D = WF[WF.t_to_grasp <= win]
        for nm, rb, tb in (("F: roll15×(−r_t)0.5", RB, TB), ("F: 경계 반칸 이동", RB + 7.5, TB + 0.25)):
            sens.append(dict(window_s=win, binning=nm, **cell_stats(table(D, "roll", "neg_rt", rb, tb))))
    SENS = pd.DataFrame(sens)
    # ---- 3. 칸별 상세 (기본 칸, L, ≤ 3 s) ----
    P = P.merge(W[["ep", "frame", "phase", "r_t", "r_r", "e_t", "s_shoulder_pan", "tip_x", "tip_y"]], on=["ep", "frame"], how="left")
    # 1 s 뒤 값
    Wi = W.set_index(["ep", "frame"])
    fut = []
    for e, f in zip(P.ep, P.frame):
        c = int(E.grasp[e])
        f1 = min(f + 30, c)
        a, b = Wi.loc[(e, f)], Wi.loc[(e, f1)]
        fut.append((abs(b.r_t) - abs(a.r_t), b.s_shoulder_pan - a.s_shoulder_pan, b.r_t - a.r_t, b.r_r - a.r_r, (f1 - f) / ac.FPS))
    P["d_abs_rt_1s"], P["dpan_1s"], P["drt_1s"], P["drr_1s"], P["fut_s"] = np.array(fut).T
    P["roll_bin"] = pd.cut(P.roll, RB)
    P["tan_bin"] = pd.cut(P.tan_cm, TB)
    P["move_dir_deg"] = np.degrees(np.arctan2(P.drt_1s, P.drr_1s))
    g = P.groupby(["roll_bin", "tan_bin"], observed=True)
    CELL = g.agg(eps=("ep", "nunique"), frames=("ep", "size"), eps_K=("group", lambda s: int(s.str.endswith("K").sum())),
                 fr_approach=("phase", lambda s: int((s == "approach").sum())), fr_fine=("phase", lambda s: int((s == "fine_align").sum())),
                 fr_closing=("phase", lambda s: int((s == "closing").sum())),
                 d_abs_rt_1s=("d_abs_rt_1s", "mean"), dpan_1s=("dpan_1s", "mean"), drt_1s=("drt_1s", "mean"), drr_1s=("drr_1s", "mean")).reset_index()
    epK = P.groupby(["roll_bin", "tan_bin"], observed=True).apply(lambda d: d.drop_duplicates("ep").group.str.endswith("K").sum()).reset_index(name="eps_K_unique")
    CELL = CELL.merge(epK, on=["roll_bin", "tan_bin"])
    CELL["frames_per_ep"] = CELL.frames / CELL.eps
    CELL["final_success_eps"] = CELL.eps   # 사람 첫 파지 256/256 성공 (a02)
    CELL.to_csv(ac.TAB / "a06_cells_detail.csv", index=False)
    # ---- 4a. 라벨 기준점 · 시간별 평균 (roll 누설 점검) ----
    leak = []
    for lo, hi in ((-0.01, 0.1), (0.1, 0.5), (0.5, 1.0), (1, 2), (2, 3)):
        d = P[(P.t_to_close > lo) & (P.t_to_close <= hi)]
        leak.append(dict(t_to_close=f"({lo:g}, {hi:g}] s", frames=len(d), rel_u_mean=d.rel_u_cm.mean(), rel_v_mean=d.rel_v_cm.mean(),
                         corr_tan_roll=np.corrcoef(d.tan_cm, d.roll)[0, 1], corr_tanrel_roll=np.corrcoef(d.tan_rel_close, d.roll)[0, 1],
                         corr_negrt_roll=np.corrcoef(-d.r_t, d.roll)[0, 1]))
    LEAK = pd.DataFrame(leak)
    l0 = lastv[lastv.t_to_close <= 0.1]
    leak_close = dict(n=len(l0), corr=float(np.corrcoef(l0.tan_cm, l0.roll)[0, 1]), slope_cm_per_deg=float(np.polyfit(l0.roll, l0.tan_cm, 1)[0]), sd=float(l0.tan_cm.std()))
    Ftab = table(WF, "roll", "neg_rt", RB, TB)
    Ftab_fr = table(WF, "roll", "neg_rt", RB, TB, "frames")
    Ltab = table(P, "roll", "tan_rel_close", RB, TB)
    Ltab_fr = table(P, "roll", "tan_rel_close", RB, TB, "frames")
    Ftab.to_csv(ac.TAB / "a06_cells_eps_F_3s.csv")
    Ltab.to_csv(ac.TAB / "a06_cells_eps_Lrel_3s.csv")
    # ---- 4. roll ~ tan 상관, roll 칸별 tan 부호 ----
    rc = dict(corr_all=float(np.corrcoef(P.roll, P.tan_cm)[0, 1]),
              corr_within_ep_mean=float(P.groupby("ep").apply(lambda d: np.corrcoef(d.roll, d.tan_cm)[0, 1] if d.roll.std() > 0.5 and len(d) > 4 else np.nan).mean()),
              corr_between_ep=float(np.corrcoef(P.groupby("ep").roll.mean(), P.groupby("ep").tan_cm.mean())[0, 1]),
              corr_roll_rt_F=float(np.corrcoef(WF.roll, WF.neg_rt)[0, 1]),
              corr_roll_tanrel=float(np.corrcoef(P.roll, P.tan_rel_close)[0, 1]),
              corr_between_ep_F_m2s=float(np.corrcoef(WF[(WF.t_to_grasp - 2).abs() < 0.02].roll, WF[(WF.t_to_grasp - 2).abs() < 0.02].neg_rt)[0, 1]),
              corr_label_vs_F_rel=float(np.corrcoef(P.tan_rel_close, -P.r_t)[0, 1]))
    P["tan_side"] = np.select([P.tan_cm <= -0.5, P.tan_cm >= 0.5], ["tan ≤ −0.5", "tan ≥ +0.5"], "abs(tan) < 0.5")
    SIDE = P.groupby(["roll_bin", "tan_side"], observed=False).ep.nunique().unstack(fill_value=0)
    SIDEf = P.groupby(["roll_bin", "tan_side"], observed=False).size().unstack(fill_value=0)
    # 판 단위 '보정 사례': 3 s 안에 |tan| ≥ 1 cm 였고 닫힘 때 |tan| < 0.5 cm
    ep_rows = []
    for e, d in P.groupby("ep"):
        d = d.sort_values("frame")
        mx = d.loc[d.tan_cm.abs().idxmax()]
        last = d.iloc[-1]
        ep_rows.append(dict(ep=e, group=d.group.iloc[0], max_abs_tan=abs(mx.tan_cm), tan_at_max=mx.tan_cm, roll_at_max=mx.roll, t_at_max=mx.t_to_close,
                            tan_last=last.tan_cm, t_last=last.t_to_close))
    EP = pd.DataFrame(ep_rows)
    EP["corrected_1cm"] = (EP.max_abs_tan >= 1) & (EP.tan_last.abs() < 0.5)
    EP["roll_bin"] = pd.cut(EP.roll_at_max, RB)
    EP["side"] = np.where(EP.tan_at_max > 0, "+", "−")
    CORR = EP[EP.max_abs_tan >= 1].groupby(["roll_bin", "side"], observed=False).agg(eps=("ep", "size"), corrected=("corrected_1cm", "sum")).unstack(fill_value=0)
    EP.to_csv(ac.TAB / "a06_episode_max_tan.csv", index=False)
    # F 측정 판 단위 보정 사례 (닫힘 3 s 안 최대 |r_t|)
    epF = WF.groupby("ep").apply(lambda d: pd.Series(dict(max_abs=d.r_t.abs().max(), roll_at=d.loc[d.r_t.abs().idxmax(), "roll"],
                                                         side=np.sign(-d.loc[d.r_t.abs().idxmax(), "r_t"])))).reset_index()
    epF["roll_bin"] = pd.cut(epF.roll_at, RB)
    CORR_F = epF[epF.max_abs >= 1].groupby(["roll_bin", "side"], observed=False).size().unstack(fill_value=0)
    out["F_eps_max_ge1"] = int((epF.max_abs >= 1).sum())
    out["F_eps_max_ge15"] = int((epF.max_abs >= 1.5).sum())
    out["leak_close"] = leak_close
    out.update(reproduce=rep, roll_tan_corr=rc, n_eps_maxtan_ge1=int((EP.max_abs_tan >= 1).sum()), n_corrected_1cm=int(EP.corrected_1cm.sum()),
               n_eps_maxtan_ge15=int((EP.max_abs_tan >= 1.5).sum()), n_eps_maxtan_ge2=int((EP.max_abs_tan >= 2).sum()))
    json.dump(out, open(ac.TAB / "a06_roll_error.json", "w"), indent=1, default=str)
    SENS.to_csv(ac.TAB / "a06_sensitivity.csv", index=False)
    mine3.to_csv(ac.TAB / "a06_cells_eps_label_3s.csv")
    table(P, "roll", "tan_cm", RB, TB, "frames").to_csv(ac.TAB / "a06_cells_frames_label_3s.csv")

    def fmt_tab(eps, fr):
        return pd.DataFrame({str(c): [f"{eps.loc[i, c]} ({fr.loc[i, c]})" for i in eps.index] for c in eps.columns}, index=[str(i) for i in eps.index])
    fr3 = table(P, "roll", "tan_cm", RB, TB, "frames")
    cd = CELL[CELL.eps <= 4].sort_values(["roll_bin", "tan_bin"])
    t = ["## 측정 사실 (스크립트 생성: `scripts/a06_roll_error.py`)\n",
         "### 6.1 기존 결과 재현\n",
         f"- labels_v2 probe_ok {rep['label_frames']} 프레임 / {rep['label_eps']} 편.",
         f"- 닫힘 1.5 s 안, roll 15° × tan 0.5 cm 판 수 표: action_bottleneck c5_cells_roll_x_tan_episodes.csv 와 {'모든 칸 같음' if rep['c5_equal'] else '다름'} "
         f"({rep['c5_stats']['cells']} 칸 중 ≥1편 {rep['c5_stats']['ge1']}, 1–4편 {rep['c5_stats']['rare_1_4']}, ≥5편 {rep['c5_stats']['ge5']}, 빈 칸 {rep['c5_stats']['empty']}).",
         f"- 닫힘 3 s 안 같은 칸: sampling_ablation s1_cells.csv 와 {'모든 칸 같음' if rep['s1_equal'] else '다름'} "
         f"(≥1편 {rep['s1_stats']['ge1']}, 1–4편 {rep['s1_stats']['rare_1_4']}, ≥5편 {rep['s1_stats']['ge5']}, 빈 칸 {rep['s1_stats']['empty']}, "
         f"데이터 범위 안쪽 빈 칸 (같은 roll 행에서 채워진 칸 사이) {rep['s1_stats']['interior_holes']}).\n",
         "### 6.2 기본 칸 표 (L 라벨, 닫힘 3 s 안): 판 수 (프레임 수)\n",
         "열 = tan_cm (큐브 − 집게 기준점, + = 로봇 왼쪽으로 도는 쪽에 큐브), 행 = roll (°).\n",
         ac.md_table(fmt_tab(mine3, fr3), index=True), "\n",
         "### 6.2b 같은 칸, 측정 방법만 바꿈 (닫힘 3 s 안): 판 수 (프레임 수)\n",
         "L′ = 라벨에서 그 판 닫힘 프레임 라벨값을 뺀 값 (최종 파지 위치 기준, 영상). F = −r_t (관절 측정, 최종 파지 TCP 기준, 모든 프레임).\n",
         "L′:\n", ac.md_table(fmt_tab(Ltab, Ltab_fr), index=True), "\n",
         "F:\n", ac.md_table(fmt_tab(Ftab, Ftab_fr), index=True), "\n",
         "### 6.2c 라벨 기준점과 roll 상관 (시간 창별)\n",
         f"사람이 실제로 잡은 프레임 (닫힘 ≤ 0.1 s, {leak_close['n']}편) 의 라벨 tan: roll 과 r = {leak_close['corr']:.2f}, 기울기 {leak_close['slope_cm_per_deg']:.4f} cm/°, SD {leak_close['sd']:.2f} cm.\n",
         ac.md_table(LEAK, {"frames": "{:.0f}"}), "\n",
         "### 6.3 칸 나누기 · 시간 창 · 측정 방법 민감도\n",
         "interior_holes = 같은 roll 행에서 채워진 칸 사이의 빈 칸. F = 관절 측정 (−r_t, 모든 프레임).\n",
         ac.md_table(SENS, {c: "{:.0f}" for c in ("cells", "ge1", "rare_1_4", "ge5", "empty", "interior_holes")}), "\n",
         "### 6.4 roll ↔ tan 상관\n",
         f"- 라벨 L: 프레임 전체 r = {rc['corr_all']:.2f}; 판 평균끼리 r = {rc['corr_between_ep']:.2f}; 판 안 상관 평균 {rc['corr_within_ep_mean']:.2f}.",
         f"- L′ (닫힘 값 기준): r = {rc['corr_roll_tanrel']:.2f}. F (−r_t, 3 s 안 모든 프레임): r = {rc['corr_roll_rt_F']:.2f}; F 의 −2 s 시점 판 간 r = {rc['corr_between_ep_F_m2s']:.2f}. L′ 와 F 의 상관 {rc['corr_label_vs_F_rel']:.2f}.\n",
         "roll 칸 × tan 쪽 (|tan| ≥ 0.5 cm) 판 수 (프레임 수):\n", ac.md_table(fmt_tab(SIDE, SIDEf), index=True), "\n",
         "### 6.5 판 단위: 닫힘 3 s 안 최대 |tan| 과 닫힐 때 |tan|\n",
         f"- 최대 |tan| ≥ 1 cm 판 {out['n_eps_maxtan_ge1']}, ≥ 1.5 cm {out['n_eps_maxtan_ge15']}, ≥ 2 cm {out['n_eps_maxtan_ge2']}. "
         f"그중 마지막 라벨 프레임 |tan| < 0.5 cm (보정됨) {out['n_corrected_1cm']}편.",
         "최대 |tan| ≥ 1 cm 판의 roll 칸 × 부호 (판 수 / 보정된 판 수):\n", ac.md_table(CORR, index=True), "\n",
         f"- 같은 집계를 F (관절, 닫힘 3 s 안 최대 |r_t|) 로: ≥ 1 cm {out['F_eps_max_ge1']}편, ≥ 1.5 cm {out['F_eps_max_ge15']}편 (모두 사람 첫 파지 성공). roll 칸 × 부호 (+ = 큐브가 로봇 왼쪽으로 도는 쪽):\n",
         ac.md_table(CORR_F, index=True), "\n",
         "### 6.6 희소 칸 (1–4편) 상세 — 1 s 뒤 변화 평균\n",
         "d_abs_rt_1s = 1 s 뒤 |r_t| 변화 (cm, − = 줄어듦), dpan_1s (°), drt/drr = TCP 접선/반지름 이동 (cm). frames_per_ep = 한 판이 그 칸에 머문 프레임 수 (라벨 표본 간격 3–10 프레임).\n",
         ac.md_table(cd[["roll_bin", "tan_bin", "eps", "frames", "frames_per_ep", "eps_K_unique", "fr_approach", "fr_fine", "fr_closing", "d_abs_rt_1s", "dpan_1s", "drt_1s", "drr_1s"]],
                     {c: "{:.0f}" for c in ("eps", "frames", "eps_K_unique", "fr_approach", "fr_fine", "fr_closing")}), "\n"]
    ac.write_facts("06.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
