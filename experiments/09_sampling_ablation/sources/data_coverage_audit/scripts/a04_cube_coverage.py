"""04 큐브 위치 · 각도 분포 (읽기만 함). 입력 tables/a01_cube_table.csv, a02_events.csv, a03_pan_first_move.csv
출력 tables/a04_*.csv/json, _facts/04.md

큐브 위치 = 세션 QA positions.csv (front 첫 화면 빨강 덩어리 중심 → config H 역산, C frame cm). 실측 좌표가 아니다 (영상 추정).
  Known: 계획 K 좌표와의 차로 추정 오차 범위를 본다.
각도 = QA cube_angle (front 첫 화면 윗면 모서리, 측정 못 한 판은 계획 각도) — yaw_src 열.
필요 손목 회전 roll_need_rel = wrap90(yaw − bearing) (QA roll_check 와 같은 정의, 90° 주기).
구역: K 격자 중간선 (config heatmap 과 같음) x −12.75 / −21.25, y 4 / 19 → 행 (상자쪽 · 가운데 · 로봇쪽) × 열 (로봇 왼쪽 · 가운데 · 오른쪽).
빈 곳: 모든 학습 큐브 위치의 볼록 껍질 안 0.5 cm 격자점에서 가장 가까운 학습 큐브까지 거리, 반경 3 cm 안 판 수.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a04_cube_coverage.py
"""
import json

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, Delaunay

import ac

ROWS = [("상자쪽", -12.75, 99), ("가운데", -21.25, -12.75), ("로봇쪽", -99, -21.25)]
COLS = [("왼쪽", 19, 99), ("가운데", 4, 19), ("오른쪽", -99, 4)]


def zone(x, y):
    r = next(n for n, lo, hi in ROWS if lo <= x < hi)
    c = next(n for n, lo, hi in COLS if lo <= y < hi)
    return f"{r}·{c}"


def in_poly(P, poly):
    """ray casting. P (N,2), poly (M,2) → bool (N,)."""
    poly = np.asarray(poly, float)
    x, y = P[:, 0], P[:, 1]
    ins = np.zeros(len(P), bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        ins ^= cond
        j = i
    return ins


def main():
    T = pd.read_csv(ac.TAB / "a01_cube_table.csv")
    E = pd.read_csv(ac.TAB / "a02_events.csv")
    F = pd.read_csv(ac.TAB / "a03_pan_first_move.csv")
    out = {}
    T["zone"] = [zone(x, y) for x, y in zip(T.cube_x, T.cube_y)]
    xy = T[["cube_x", "cube_y"]].values
    K = np.array(list(ac.KNOWN.values()))
    Kn = list(ac.KNOWN.keys())
    dK = np.hypot(xy[:, None, 0] - K[None, :, 0], xy[:, None, 1] - K[None, :, 1])
    T["dist_K_min"] = dK.min(1)
    T["nearest_K_calc"] = [Kn[i] for i in dK.argmin(1)]
    # 1. 그룹별 범위
    g = T.groupby("group").agg(n=("ep", "size"), x_min=("cube_x", "min"), x_max=("cube_x", "max"), y_min=("cube_y", "min"), y_max=("cube_y", "max"),
                               bearing_min=("bearing", "min"), bearing_max=("bearing", "max"), range_min=("range_cm", "min"), range_max=("range_cm", "max"),
                               dK_med=("dist_K_min", "median")).reset_index()
    # Known 배치 오차
    k = T["mode"] == "K"
    dplan = np.hypot(T.cube_x[k] - T.plan_x[k], T.cube_y[k] - T.plan_y[k])
    plan_err = dict(n=int(k.sum()), p50=float(dplan.median()), p90=float(dplan.quantile(.9)), max=float(dplan.max()),
                    mismatch_nearestK=int((T.plan_K[k] != T.nearest_K_calc[k]).sum()))
    # 2. K 집중도
    conc = []
    for lab, sel in (("전체 256", T.index), ("Random 128", T.index[T["mode"] == "R"]), ("T1-R", T.index[T.group == "T1R"]), ("T3-R", T.index[T.group == "T3R"])):
        d = T.dist_K_min[sel]
        conc.append(dict(set=lab, n=len(d), le1=f"{int((d <= 1).sum())}", le2=f"{int((d <= 2).sum())}", le3=f"{int((d <= 3).sum())}",
                         le5=f"{int((d <= 5).sum())}", gt5=f"{int((d > 5).sum())}", median=float(d.median()), max=float(d.max())))
    # 3. 구역표
    Z = T.pivot_table(index="zone", columns="group", values="ep", aggfunc="size", fill_value=0)
    Z["합"] = Z.sum(1)
    Z = Z.reindex([f"{r}·{c}" for r, _, _ in ROWS for c, _, _ in COLS]).fillna(0).astype(int)
    # 4. 빈 곳 (볼록 껍질 안 격자)
    hull = ConvexHull(xy)
    tri = Delaunay(xy[hull.vertices])
    gx, gy = np.meshgrid(np.arange(xy[:, 0].min(), xy[:, 0].max() + 0.01, 0.5), np.arange(xy[:, 1].min(), xy[:, 1].max() + 0.01, 0.5))
    G = np.column_stack([gx.ravel(), gy.ravel()])
    G = G[tri.find_simplex(G) >= 0]
    hz = np.zeros(len(G), bool)
    for z in ac.CFG["workspace"].get("hard_zones_cm", []):
        hz |= in_poly(G, z["polygon"])
    dG = np.hypot(G[:, None, 0] - xy[None, :, 0], G[:, None, 1] - xy[None, :, 1])
    nearest = dG.min(1)
    n3 = (dG <= 3).sum(1)
    nR3 = (dG[:, (T["mode"] == "R").values] <= 3).sum(1)
    nb = np.digitize(T.roll_need_rel.values, [-15, 15])          # 0: ↻ ≥15°, 1: |need| < 15°, 2: ↺ ≥ 15°
    within = dG <= 3
    n_needcls = np.array([len(np.unique(nb[w])) for w in within])
    n_need_cw = (within & (nb == 0)[None]).sum(1)
    n_need_ccw = (within & (nb == 2)[None]).sum(1)
    n_need_0 = (within & (nb == 1)[None]).sum(1)
    grid = pd.DataFrame(dict(x=G[:, 0], y=G[:, 1], nearest_cm=nearest, n_eps_3cm=n3, n_R_eps_3cm=nR3, hard_zone=hz,
                             n_need_classes_3cm=n_needcls, n_need_cw_3cm=n_need_cw, n_need_0_3cm=n_need_0, n_need_ccw_3cm=n_need_ccw, zone=[zone(a, b) for a, b in G]))
    grid.to_csv(ac.TAB / "a04_gap_grid.csv", index=False)
    gap = dict(hull_area_cm2=float(hull.volume), grid_pts=len(G), nearest_max=float(nearest.max()), nearest_p95=float(np.percentile(nearest, 95)),
               frac_gt2=float((nearest > 2).mean()), frac_gt2_5=float((nearest > 2.5).mean()),
               frac_n3_le2=float((n3 <= 2).mean()), frac_n3_le5=float((n3 <= 5).mean()), n3_median=float(np.median(n3)),
               frac_nR3_eq0=float((nR3 == 0).mean()), hard_zone_pts=int(hz.sum()),
               ok_pts=int((~hz).sum()), ok_nearest_max=float(nearest[~hz].max()), ok_nearest_p95=float(np.percentile(nearest[~hz], 95)),
               ok_frac_gt2=float((nearest[~hz] > 2).mean()), ok_frac_gt2_5=float((nearest[~hz] > 2.5).mean()),
               ok_n3_median=float(np.median(n3[~hz])), ok_frac_n3_le2=float((n3[~hz] <= 2).mean()), ok_frac_n3_le5=float((n3[~hz] <= 5).mean()),
               ok_frac_nR3_eq0=float((nR3[~hz] == 0).mean()),
               ok_frac_all3_need=float((n_needcls[~hz] == 3).mean()), ok_frac_need_cls_le1=float((n_needcls[~hz] <= 1).mean()),
               ok_min_need_cls_med=float(np.median(np.minimum(np.minimum(n_need_cw, n_need_ccw), n_need_0)[~hz])),
               ok_frac_any_need_cls_le1=float((np.minimum(np.minimum(n_need_cw, n_need_ccw), n_need_0)[~hz] <= 1).mean()))
    gz = grid[~grid.hard_zone].groupby("zone").agg(pts=("x", "size"), nearest_max=("nearest_cm", "max"), n3_median=("n_eps_3cm", "median"), n3_min=("n_eps_3cm", "min"),
                                  frac_n3_le5=("n_eps_3cm", lambda s: float((s <= 5).mean()))).reset_index()
    # 극좌표 구간 (bearing 15° × range 4 cm): 판 수
    T["bear_bin"] = pd.cut(T.bearing, np.arange(-105, 106, 15))
    T["range_bin"] = pd.cut(T.range_cm, np.arange(4, 37, 4))
    PB = T.pivot_table(index="range_bin", columns="bear_bin", values="ep", aggfunc="size", fill_value=0, observed=False)
    PB.to_csv(ac.TAB / "a04_polar_bins.csv")
    # 5. 각도
    ang = T.groupby(["group", "yaw_plan_code"]).size().unstack(fill_value=0)
    T["need_abs"] = T.roll_need_rel.abs()
    T["need_bin"] = pd.cut(T.roll_need_rel, [-45.01, -30, -15, 0, 15, 30, 45.01])
    NZ = T.pivot_table(index="zone", columns="need_bin", values="ep", aggfunc="size", fill_value=0, observed=False)
    NZ = NZ.reindex([f"{r}·{c}" for r, _, _ in ROWS for c, _, _ in COLS]).fillna(0).astype(int)
    meas = T[T.yaw_meas.notna() & T.yaw_plan.notna()]
    ang_err = ac.wrap90(meas.yaw_meas - meas.yaw_plan)
    ang_stat = dict(n_measured=int(T.yaw_meas.notna().sum()), meas_minus_plan_abs_p50=float(np.median(np.abs(ang_err))),
                    meas_minus_plan_abs_p90=float(np.percentile(np.abs(ang_err), 90)))
    # 6. 위치 ~ pan 행동
    F2 = F.merge(T[["ep", "zone", "dist_K_min"]], on="ep")
    F2["pan_res_c"] = E.pan_c - T.pan_expected
    pz = F2.groupby("zone").agg(n=("ep", "size"), pan_total_med=("pan_total", "median"), sub1_frac_med=("sub1_frac", "median"),
                                reach2_s_med=("pan_reach2_from_onset_s", "median"), settle2_before_grasp_med=("pan_settle2_before_grasp_s", "median"),
                                pan_res_c_sd=("pan_res_c", "std"), approach_s_med=("approach_s", "median")).reset_index()
    pz = pz.set_index("zone").reindex([f"{r}·{c}" for r, _, _ in ROWS for c, _, _ in COLS]).reset_index()
    near = F2.dist_K_min <= 2
    kr = dict(pan_res_sd_nearK=float(F2.pan_res_c[near].std()), pan_res_sd_farK=float(F2.pan_res_c[~near].std()), n_near=int(near.sum()), n_far=int((~near).sum()))
    # 평가 위치 (참고)
    GE = pd.read_csv(ac.D2 / "diag_grasp_bias/grasp_eval.csv")
    ev = GE[GE.event == 0][["run", "ep", "start_x", "start_y"]].drop_duplicates()
    dE = np.hypot(ev.start_x.values[:, None] - xy[None, :, 0], ev.start_y.values[:, None] - xy[None, :, 1])
    ev["nearest_train_cm"] = dE.min(1)
    ev["n_train_3cm"] = (dE <= 3).sum(1)
    dKe = np.hypot(ev.start_x.values[:, None] - K[None, :, 0], ev.start_y.values[:, None] - K[None, :, 1])
    ev["nearest_K"] = [Kn[i] for i in dKe.argmin(1)]
    ev["dist_K"] = dKe.min(1)
    ev.to_csv(ac.TAB / "a04_eval_positions.csv", index=False)
    T.to_csv(ac.TAB / "a04_cube_positions.csv", index=False)
    out.update(plan_err=plan_err, gap=gap, ang=ang_stat, pan_res_K=kr)
    json.dump(out, open(ac.TAB / "a04_cube_coverage.json", "w"), indent=1)

    t = ["## 측정 사실 (스크립트 생성: `scripts/a04_cube_coverage.py`)\n",
         "큐브 위치는 front 첫 화면 영상에서 H 로 역산한 값이다 (실측 아님). Known 판의 잰 위치 − 계획 K 거리: "
         f"중앙값 {plan_err['p50']:.2f} cm, 90% {plan_err['p90']:.2f} cm, 최대 {plan_err['max']:.2f} cm; 가장 가까운 K 가 계획 K 와 다른 판 {plan_err['mismatch_nearestK']}개.\n",
         "### 4.1 그룹별 범위 (C frame cm, bearing ° (+ = 로봇 왼쪽), range = 베이스에서 cm)\n", ac.md_table(g, {"n": "{:.0f}", "dK_med": "{:.2f}"}), "\n",
         "### 4.2 K 위치 집중도 (가장 가까운 K 중심까지 거리별 판 수)\n", ac.md_table(pd.DataFrame(conc), {"n": "{:.0f}"}), "\n",
         "### 4.3 구역별 판 수 (행 = 로봇에서 거리 방향, 열 = 좌우)\n", ac.md_table(Z, index=True), "\n",
         "### 4.4 극좌표 구간별 판 수 (행 range 4 cm, 열 bearing 15°)\n", ac.md_table(PB.astype(int), index=True), "\n",
         "### 4.5 빈 곳 (모든 학습 큐브 위치의 볼록 껍질 안, 0.5 cm 격자)\n",
         f"- 볼록 껍질 넓이 {gap['hull_area_cm2']:.0f} cm², 격자점 {gap['grid_pts']}. 가장 가까운 학습 큐브까지 최대 {gap['nearest_max']:.2f} cm, 95% {gap['nearest_p95']:.2f} cm; "
         f"> 2 cm 인 격자 {gap['frac_gt2']:.1%}, > 2.5 cm {gap['frac_gt2_5']:.1%}.",
         f"- 반경 3 cm 안 학습 판 수: 중앙값 {gap['n3_median']:.0f}, ≤ 2편인 격자 {gap['frac_n3_le2']:.1%}, ≤ 5편 {gap['frac_n3_le5']:.1%}; 반경 3 cm 안 Random 판 0 인 격자 {gap['frac_nR3_eq0']:.1%}.",
         f"- 위 격자 중 config `workspace.hard_zones_cm` '로봇 앞' (사용자가 원격조종으로 닿기 어렵다고 표시한 구역, 10-22) 안 {gap['hard_zone_pts']}점을 빼면 ({gap['ok_pts']}점): "
         f"가장 가까운 학습 큐브까지 최대 {gap['ok_nearest_max']:.2f} cm, 95% {gap['ok_nearest_p95']:.2f} cm; > 2 cm {gap['ok_frac_gt2']:.1%}, > 2.5 cm {gap['ok_frac_gt2_5']:.1%}; "
         f"반경 3 cm 안 판 수 중앙값 {gap['ok_n3_median']:.0f}, ≤ 2편 {gap['ok_frac_n3_le2']:.1%}, ≤ 5편 {gap['ok_frac_n3_le5']:.1%}; 반경 3 cm 안 Random 0 {gap['ok_frac_nR3_eq0']:.1%}.\n",
         f"- 필요 손목 회전을 3 묶음 (↻ ≥ 15° / |.| < 15° / ↺ ≥ 15°) 으로 나누면, hard zone 밖 격자 중 반경 3 cm 안에 세 묶음이 모두 있는 곳 {gap['ok_frac_all3_need']:.1%}, "
         f"한 묶음 이하 {gap['ok_frac_need_cls_le1']:.1%}; 세 묶음 중 가장 적은 묶음의 판 수 중앙값 {gap['ok_min_need_cls_med']:.0f}, ≤ 1편인 격자 {gap['ok_frac_any_need_cls_le1']:.1%}.\n",
         "구역별 (hard zone 제외):\n", ac.md_table(gz, {"pts": "{:.0f}", "n3_min": "{:.0f}", "frac_n3_le5": "{:.1%}"}), "\n",
         "### 4.6 큐브 각도\n",
         f"- 각도 측정된 판 {ang_stat['n_measured']}/256 (나머지는 계획 각도 사용). |측정 − 계획| (90° 주기) 중앙값 {ang_stat['meas_minus_plan_abs_p50']:.1f}°, 90% {ang_stat['meas_minus_plan_abs_p90']:.1f}°.\n",
         "계획 각도 코드별 판 수:\n", ac.md_table(ang, index=True), "\n",
         "구역 × 필요 손목 회전 (wrap90(yaw − bearing), °) 판 수:\n", ac.md_table(NZ, index=True), "\n",
         "### 4.7 구역별 pan 행동\n",
         "pan_res_c = 첫 파지 pan − 큐브 bearing 기대 pan (°).\n", ac.md_table(pz, {"n": "{:.0f}"}), "\n",
         f"- 첫 파지 pan 잔차 SD: K 2 cm 안 판 {kr['pan_res_sd_nearK']:.2f}° (n {kr['n_near']}) vs 그 밖 {kr['pan_res_sd_farK']:.2f}° (n {kr['n_far']}).\n",
         "### 4.8 d2 실물 평가 5판의 큐브 위치 (front 첫 화면 추정, 참고)\n", ac.md_table(ev, {"ep": "{:.0f}", "n_train_3cm": "{:.0f}"}), "\n"]
    ac.write_facts("04.md", "\n".join(t))
    print("\n".join(t))


if __name__ == "__main__":
    main()
