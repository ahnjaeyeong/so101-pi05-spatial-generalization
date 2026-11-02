"""00 TCP (집게 끝) 모델 검증 (읽기만 함). 출력 tables/a00_tcp_model.json

비교하는 모델 (모두 파지 순간 = check_dataset.first_grasp, 큐브 = front 첫 화면 H 역산 위치):
  M0  기존 diag_grasp_bias/fk_fit.json: FK gripper_frame_link 를 2D 강체 변환 (학습 첫 파지에 맞춤)
  베이스 · pan 오프셋을 256편 첫 파지 pan 으로 다시 맞춤 (5-fold CV) → tables/a00_base_fit.json (이후 모든 스크립트가 씀)
  M1  pan 축 극좌표: 방향 = pan (다시 맞춘 베이스, bearing = (pan − off)/(−1)), 반지름 = FK 팔 평면 거리 A, 옆 = +L (URDF 부호 그대로)
  M2  M1 과 같되 옆 = -L (부호 반대)   ← 채택
  M2b M2 에서 옆 오프셋 0 (pan 만)
각 모델의 파지 순간 접선 · 반지름 오차 (평균 · SD · roll 상관 · bearing 상관).
M2 의 반지름 편향 dA 는 5-fold 교차검증으로 맞추고 (훈련 fold 평균), 시험 fold 오차를 보고한다.
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a00_tcp_model.py
"""
import json

import numpy as np
import pandas as pd

import ac


def tr_err(X, cube):
    et, er = [], []
    for k in range(len(X)):
        ut, ur = ac.axes(*cube[k])
        d = X[k, :2] - cube[k]
        et.append(d @ ut)
        er.append(d @ ur)
    return np.array(et), np.array(er)


def summ(et, er, roll, bear):
    return dict(tan_mean=float(et.mean()), tan_sd=float(et.std()), tan_abs_p50=float(np.median(np.abs(et))), tan_abs_p90=float(np.percentile(np.abs(et), 90)),
                rad_mean=float(er.mean()), rad_sd=float(er.std()), corr_tan_roll=float(np.corrcoef(et, roll)[0, 1]),
                corr_tan_bearing=float(np.corrcoef(et, bear)[0, 1]))


def fit_base(T, pan):
    """pan(c) = -atan2(y - by, x - bx) + off 를 256편 첫 파지에 맞춤 (scipy least_squares). 5-fold CV 잔차도."""
    from scipy.optimize import least_squares
    x, y = T.cube_x.values, T.cube_y.values

    def res(p, i):
        b = np.degrees(np.arctan2(y[i] - p[1], x[i] - p[0]))
        return ac.wrap180(pan[i] - (-b + p[2]))
    idx = np.arange(len(x))
    p0 = [float(ac.BASE_CFG[0]), float(ac.BASE_CFG[1]), float(ac.ROB["pan_offset_deg"])]
    cv = np.zeros(len(x))
    for f in range(5):
        te, tr = idx[f::5], np.setdiff1d(idx, idx[f::5])
        cv[te] = res(least_squares(lambda p: res(p, tr), p0).x, te)
    p = least_squares(lambda p: res(p, idx), p0).x
    cfg_res = res(p0, idx)
    bear_cfg = np.degrees(np.arctan2(y - p0[1], x - p0[0]))
    return dict(base_xy_cm=[float(p[0]), float(p[1])], pan_offset_deg=float(p[2]), cv_resid_sd_deg=float(cv.std()), cv_resid_mean_deg=float(cv.mean()),
                cv_corr_bearing=float(np.corrcoef(cv, bear_cfg)[0, 1]), config=dict(base_xy_cm=p0[:2], pan_offset_deg=p0[2]),
                config_resid_sd_deg=float(cfg_res.std()), config_resid_mean_deg=float(cfg_res.mean()),
                config_corr_bearing=float(np.corrcoef(cfg_res, bear_cfg)[0, 1]))


def main():
    import check_dataset as cd
    data = ac.load_d2()
    T = ac.cube_table()
    c = np.array([cd.first_grasp(data[e][0]) for e in range(256)])
    Q = np.array([data[e][0][c[e]] for e in range(256)])
    bf = fit_base(ac.cube_table(), Q[:, 0])
    json.dump(bf, open(ac.TAB / "a00_base_fit.json", "w"), indent=1)
    import importlib
    importlib.reload(ac)
    T = ac.cube_table()
    cube = T[["cube_x", "cube_y"]].values
    roll, bear = Q[:, 4], T.bearing.values
    out = {"base_fit": bf}
    P0, _ = ac.tip(Q)
    out["M0_fkfit_rigid"] = summ(*tr_err(P0, cube), roll, bear)
    A, L, Z = ac.armplane(Q)
    b = np.radians((Q[:, 0] - ac.PAN_OFF) / ac.PAN_SIGN)
    ur = np.column_stack([np.cos(b), np.sin(b)])
    ut = np.column_stack([-np.sin(b), np.cos(b)])
    for nm, lat in (("M1_polar_lat_plus", L), ("M2_polar_lat_minus", -L), ("M2b_polar_lat0", 0 * L)):
        X = ac.BASE + A[:, None] * ur + lat[:, None] * ut
        out[nm] = summ(*tr_err(X, cube), roll, bear)
    # M2 + dA 교차검증
    idx = np.arange(256)
    ets, ers, dAs = np.zeros(256), np.zeros(256), []
    for f in range(5):
        te, trn = idx[f::5], np.setdiff1d(idx, idx[f::5])
        _, er_tr = tr_err(ac.tcp(Q[trn], dA=0.0), cube[trn])
        dA = -float(er_tr.mean())
        dAs.append(dA)
        a, b2 = tr_err(ac.tcp(Q[te], dA=dA), cube[te])
        ets[te], ers[te] = a, b2
    _, er_all = tr_err(ac.tcp(Q, dA=0.0), cube)
    dA_all = -float(er_all.mean())
    out["M2_dA_cv"] = summ(ets, ers, roll, bear) | dict(dA_folds=dAs)
    out["dA_cm"] = dA_all
    out["pan_residual_deg_sd"] = float(np.std(Q[:, 0] - T.pan_expected.values))
    out["pan_residual_deg_mean"] = float(np.mean(Q[:, 0] - T.pan_expected.values))
    out["reach_A_cm"] = dict(mean=float(A.mean()), sd=float(A.std()))
    out["lateral_L_cm"] = dict(mean=float(L.mean()), sd=float(L.std()), corr_roll=float(np.corrcoef(L, roll)[0, 1]))
    out["tip_z_cm_at_grasp"] = dict(mean=float(Z.mean()), sd=float(Z.std()))
    # 큐브 위치 측정 오차 (Known: 잰 위치 − 계획 K)
    k = T["mode"] == "K"
    dk = np.hypot(T.cube_x[k] - T.plan_x[k], T.cube_y[k] - T.plan_y[k])
    out["known_meas_minus_plan_cm"] = dict(p50=float(dk.median()), p90=float(dk.quantile(.9)), max=float(dk.max()))
    pd.DataFrame(dict(ep=idx, e_t_cv=ets, e_r_cv=ers, roll=roll, bearing=bear)).to_csv(ac.TAB / "a00_tcp_grasp_residuals.csv", index=False)
    json.dump(out, open(ac.TAB / "a00_tcp_model.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
    main()
