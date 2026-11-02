"""visibility_frames.csv 분석 (CPU, 읽기만) → vis_summary.json + 화면.
  1) 닫힘까지 시간 구간별 중앙값 (front 가림·그림자·조명, wrist 밝기·그림자·손가락 가림·선명도·화면 위치, 기울기)
  2) front 가시성 손실 분해 (0–1 s): 1 − red_vis = 로봇(검정) 가림 + 다른 변화 + 분류 안 됨(빨강 마스크만 빠짐 = 어두워진 큐브 등)
  3) 판 사이 편상관: 같은 시점(닫힘 2 s · 1 s · 0 s 전)에서 기울기 ↔ 가시성 지표, 큐브 거리·방향을 선형으로 뺀 잔차의 Spearman
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).resolve().parent
FRONT = ["red_vis", "occ_dark", "occ_other", "cube_shade", "ring_shade", "ambient", "vis_px224"]
WRIST = ["w_cube_V", "w_shade_near", "w_finger_cover", "w_sharp", "w_cu", "w_cv", "w_area", "w_top_V"]


def resid(y, X):
    X = np.column_stack([np.ones(len(X))] + [X[:, i] for i in range(X.shape[1])])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return y - X @ b


def main():
    D = pd.read_csv(OUT / "visibility_frames.csv")
    S = {}
    bins = [(3, 99), (2, 3), (1, 2), (0.5, 1), (-0.01, 0.5)]
    tab = {}
    for lo, hi in bins:
        d = D[(D.t_to_close > lo) & (D.t_to_close <= hi)]
        tab[f"{lo}-{hi}s"] = {c: float(d[c].median()) for c in ["tilt_A", "tilt_B", "tip_z_B"] + FRONT + WRIST} | {"n": len(d)}
    S["by_time"] = tab
    d = D[D.t_to_close <= 1.0]
    loss = 1 - d.red_vis
    S["front_loss_0_1s"] = dict(mean_loss=float(loss.mean()), occ_dark=float(d.occ_dark.mean()), occ_other=float(d.occ_other.mean()),
                                unclassified=float((loss - d.occ_dark - d.occ_other).mean()),
                                frac_frames_red_vis_lt_50=float((d.red_vis < 0.5).mean()),
                                cube_shade_med=float(d.cube_shade.median()), ring_shade_med=float(d.ring_shade.median()),
                                ambient_p05_p95=[float(D.ambient.quantile(.05)), float(D.ambient.quantile(.95))])
    pc = {}
    for lag_s in (2.0, 1.0, 0.0):
        g = D.loc[D.assign(dt=(D.t_to_close - lag_s).abs()).groupby("ep").dt.idxmin()]
        g = g[(g.t_to_close - lag_s).abs() <= 0.11]
        X = g[["range_cm", "bearing"]].values
        res = {}
        for conv in ("A", "B"):
            tr = resid(g[f"tilt_{conv}"].values, X)
            for c in FRONT + WRIST:
                ok = g[c].notna().values
                if ok.sum() < 40:
                    continue
                yr = resid(g[c].values[ok], X[ok])
                rho, p = stats.spearmanr(tr[ok], yr)
                res[f"{conv}|{c}"] = dict(rho=float(rho), p=float(p), n=int(ok.sum()))
        pc[f"{lag_s:.0f}s_before"] = res
        pc[f"{lag_s:.0f}s_before_tilt_sd"] = dict(A=float(g.tilt_A.std()), B=float(g.tilt_B.std()), n=len(g))
    S["partial_spearman_tilt_vs_metric"] = pc
    json.dump(S, open(OUT / "vis_summary.json", "w"), indent=1)
    return S


if __name__ == "__main__":
    S = main()
    pd.set_option("display.width", 250)
    print(pd.DataFrame(S["by_time"]).T.round(3).to_string())
    print("front_loss_0_1s", json.dumps(S["front_loss_0_1s"]))
    for k, v in S["partial_spearman_tilt_vs_metric"].items():
        if k.endswith("tilt_sd"):
            print(k, v)
            continue
        print(k, {kk: (round(vv["rho"], 2), f"{vv['p']:.0e}") for kk, vv in v.items() if kk.startswith("B|")})
