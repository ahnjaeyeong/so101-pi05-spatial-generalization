"""4단계: 표·프로브 결과의 수치 요약 → summary.json (+ 화면 출력). 읽기만 함.
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python summarize.py
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

import common as C


def ols(y, X):
    X = np.column_stack([np.ones(len(y))] + list(X))
    b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    r2 = 1 - (r ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, float(r.std()), float(r2)


def main():
    out = {}
    T = pd.read_csv(C.OUT / "grasp_train.csv")
    E = pd.read_csv(C.OUT / "grasp_eval.csv")
    K = C.load_known()
    T["dK"] = [min(np.hypot(x - v[0], y - v[1]) for v in K.values()) for x, y in zip(T.cube_x, T.cube_y)]

    tr = {}
    for md, g in T.groupby("mode"):
        b, sd, r2 = ols(g.s_shoulder_pan.values, [g.pan_exp.values])
        tr[md] = dict(n=len(g), pan_slope=b[1], pan_icpt=b[0], resid_sd=sd, r2=r2, pan_res_mean=g.pan_res.mean(),
                      pan_res_sd=g.pan_res.std(), dK_median=float(g.dK.median()), wrist_u_mean=g.wu.mean(), wrist_v_mean=g.wv.mean(),
                      grasp_t_mean=g.grasp_t.mean())
    tr["K_vs_R_pan_res_p"] = float(stats.ttest_ind(T[T["mode"] == "K"].pan_res, T[T["mode"] == "R"].pan_res).pvalue)
    tr["T1_vs_T3_pan_res_p"] = float(stats.ttest_ind(T[T.task == "T1"].pan_res, T[T.task == "T3"].pan_res).pvalue)
    tr["T1_vs_T3_grasp_t"] = [float(T[T.task == "T1"].grasp_t.mean()), float(T[T.task == "T3"].grasp_t.mean()),
                              float(stats.ttest_ind(T[T.task == "T1"].grasp_t, T[T.task == "T3"].grasp_t).pvalue)]
    tr["random_within3cm_of_K"] = float((T[T["mode"] == "R"].dK < 3).mean())
    tr["wrist_u_range_5_95"] = [float(T.wu.quantile(.05)), float(T.wu.quantile(.95))]
    tr["wrist_v_range_5_95"] = [float(T.wv.quantile(.05)), float(T.wv.quantile(.95))]
    out["train"] = tr

    first = E[E.event == 0]
    out["eval_first_close"] = first[["run", "ep", "t", "cube_x", "cube_y", "nearest_K", "nearest_K_cm", "pan_exp", "s_shoulder_pan",
                                     "pan_res", "d_shoulder_pan", "wu", "wv", "s_gripper"]].round(2).to_dict("records")

    p = C.OUT / "probe_start.csv"
    if p.exists():
        S = pd.read_csv(p)
        S["mode"] = S.group.str[2]
        ps = {}
        for md, g in S.groupby("mode"):
            b, sd, r2 = ols(g.pred_pan.values, [g.s_shoulder_pan.values])
            ps[md] = dict(n=len(g), slope=b[1], icpt=b[0], resid_sd=sd, r2=r2, mae=float(g.pred_minus_human.abs().median()),
                          bias=float(g.pred_minus_human.mean()), seed_sd=float(g.pred_pan_sd.median()))
        out["probe_start"] = ps
    p = C.OUT / "probe_pregrasp.csv"
    if p.exists():
        Q = pd.read_csv(p)
        Q["mode"] = Q.group.str[2]
        pg = {}
        for md, g in Q.groupby("mode"):
            pg[md] = {j: dict(bias=float(g[f"err_{j}"].mean()), abs_median=float(g[f"err_{j}"].abs().median()))
                      for j in C.JOINTS[:5]}
            pg[md]["pred_close_idx_median"] = float(g.pred_close_idx.median())
            pg[md]["pred_close_found"] = float(g.pred_close_idx.notna().mean())
        pg["pan_abs_err_K_vs_R_p"] = float(stats.mannwhitneyu(Q[Q["mode"] == "K"].err_shoulder_pan.abs(),
                                                              Q[Q["mode"] == "R"].err_shoulder_pan.abs()).pvalue)
        out["probe_pregrasp"] = pg
    p = C.OUT / "probe_swap.csv"
    if p.exists():
        W = pd.read_csv(p)
        sw = {}
        for md, g in W.groupby("mode"):
            b, sd, r2 = ols(g.pred_pan.values, [g.pan_B.values, g.pan_A.values])
            sw[md] = dict(n=len(g), coef_image_B=b[1], coef_state_A=b[2], icpt=b[0], resid_sd=sd, r2=r2)
        out["probe_swap"] = sw
    p = C.OUT / "probe_grid.csv"
    if p.exists():
        G = pd.read_csv(p)
        b, sd, r2 = ols(G.pred_pan.values, [G.pan_exp.values])
        gk = dict(n=len(G), slope=b[1], icpt=b[0], resid_sd=sd, r2=r2, bias_mean=float(G.pred_minus_exp.mean()),
                  bias_median=float(G.pred_minus_exp.median()), abs_err_median=float(G.pred_minus_exp.abs().median()),
                  frac_right=float((G.pred_minus_exp > 0).mean()))
        # 가장 가까운 K 쪽으로 끌리는지: (pred − exp) 를 (K − exp) 방향으로 나눈 비율 (1 = K 에 도착, 0 = 큐브)
        far = G[(G.K_pan_exp - G.pan_exp).abs() > 4]
        att = (far.pred_pan - far.pan_exp) / (far.K_pan_exp - far.pan_exp)
        gk["K_attraction_median"] = float(att.median())
        gk["K_attraction_toward_frac"] = float((att > 0).mean())
        gk["n_attr"] = len(far)
        # 한쪽 쏠림 vs K 끌림: 가장 가까운 K 가 로봇 왼쪽(K pan < exp)인 점에서도 오른쪽(+)으로 틀리는지
        left = far[far.K_pan_exp < far.pan_exp]
        right = far[far.K_pan_exp > far.pan_exp]
        gk["err_when_K_is_robot_left"] = [float(left.pred_minus_exp.mean()), len(left)]
        gk["err_when_K_is_robot_right"] = [float(right.pred_minus_exp.mean()), len(right)]
        for lo, hi in ((0, 2), (2, 4), (4, 6), (6, 99)):
            d = G[(G.nearest_train_cm >= lo) & (G.nearest_train_cm < hi)]
            gk[f"abs_err_median_train_dist_{lo}_{hi}cm"] = [float(d.pred_minus_exp.abs().median()) if len(d) else None, len(d)]
        for lo, hi in ((0, 3), (3, 6), (6, 99)):
            d = G[(G.nearest_K_cm >= lo) & (G.nearest_K_cm < hi)]
            gk[f"abs_err_median_K_dist_{lo}_{hi}cm"] = [float(d.pred_minus_exp.abs().median()) if len(d) else None, len(d)]
        out["probe_grid"] = gk
    p = C.OUT / "probe_eval.csv"
    if p.exists():
        out["probe_eval"] = pd.read_csv(p).round(2).to_dict("records")

    def conv(o):
        if isinstance(o, dict):
            return {k: conv(v) for k, v in o.items()}
        if isinstance(o, list):
            return [conv(v) for v in o]
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
        return o

    out = conv(out)
    json.dump(out, open(C.OUT / "summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
