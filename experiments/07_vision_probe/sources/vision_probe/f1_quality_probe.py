"""F1-E 영상 품질 변형 probe (CPU, f1_extract.py · f1_quality.py 결과 필요).

wrist (1,000 프레임 × 변형):
  transfer: 원본 특징(f1_features train 행, 그 fold 의 train 판)으로 학습한 ridge → test 판의 변형 특징에 적용.
            영상 축 (rel_u, rel_v) 예측 → roll 회전 (img_rot) → tan/rad MAE. 원본 대비 예측 이동량 |Δtan|.
  within:   같은 변형으로 학습·평가 (1,000 프레임 안 5-fold). 정보가 남아 있는지.
front (256편 × 프레임 0·30·60 × {orig, crop1.6}):
  같은 변형으로 학습·평가, 표적 = 탁자 위 큐브 위치 cube_x, cube_y (cm). 전체 · 창 안(in_crop) 판만.
  기준선: front RGB 32×24 (같은 변형 영상).
fold = folds.json (판·위치 누출 없음, f1_leak_check).
출력: f1_results/quality.json
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f1_probe as FP  # noqa: E402
import f1_quality as Q  # noqa: E402

OUT = FP.OUT
FEAT = FP.FEAT
QF = OUT / "f1_quality_features"
W_KEYS = ["sig_w26", "sig_w13"] + [f"kv_w:{li}:1" for li in range(6)] + ["kv_w:5:0"]
F_KEYS = ["sig_f26", "sig_f13"] + [f"kv_f:{li}:1" for li in range(6)]


def load(base, key, rows):
    if ":" in key:
        arr, li, kv = key.split(":")
        A = np.load(base / f"{arr}.npy", mmap_mode="r")
        return np.stack([np.asarray(A[r, int(li), int(kv)], np.float32) for r in rows])
    A = np.load(base / f"{key}.npy", mmap_mode="r")
    return np.stack([np.asarray(A[r], np.float32) for r in rows])


def tab_mae(P_img, rows):
    tn, rd = FP.img_to_tab(P_img[:, 0], P_img[:, 1], rows.roll.values)
    e_t, e_r = tn - rows.tan_cm.values, rd - rows.rad_cm.values
    sd_t = rows.tan_cm.values.std()
    return dict(tan_mae=float(np.abs(e_t).mean()), rad_mae=float(np.abs(e_r).mean()),
                tan_r2=float(1 - (e_t ** 2).mean() / sd_t ** 2)), tn


def wrist_part(folds):
    M = pd.read_csv(FEAT / "meta.csv")
    T = M[(M.src == "train") & M.valid].reset_index(drop=True)
    QM = pd.read_csv(QF / "meta.csv")
    W = QM[QM.src == "wrist_q"].reset_index(drop=True)
    key_ix = {(e, f): r for e, f, r in zip(T.ep, T.frame, T.row)}
    W["main_row"] = [key_ix.get((e, f), -1) for e, f in zip(W.ep, W.frame)]
    assert (W.main_row >= 0).all()
    out = {"n_frames": int((W.variant == "orig").sum())}
    for key in W_KEYS:
        Xtr_all = FP.token_project(load(FEAT, key, T.row.values))
        Xq = FP.token_project(load(QF, key, W.row.values))
        o = W.variant.values == "orig"
        # 결정성: quality orig == main 특징
        Xm = FP.token_project(load(FEAT, key, W.main_row.values[o]))
        r = {"orig_vs_main_maxabs": float(np.abs(Xm - Xq[o]).max())}
        pred = np.full((len(W), 2), np.nan)
        for fo in folds:
            tr = T.ep.isin(fo["train_eps"]).values
            te = W.ep.isin(fo["test_eps"]).values
            if not te.any():
                continue
            m, _ = FP.ridge_cv(Xtr_all[tr], T[FP.TGT_IMG].values[tr], T.ep.values[tr])
            pred[te] = FP.ridge_pred(m, Xq[te])
        ok = ~np.isnan(pred[:, 0])
        base_tan = {}
        for v in Q.W_VARIANTS:
            s = (W.variant.values == v) & ok
            met, tn = tab_mae(pred[s], W[s])
            if v == "orig":
                base_tan = dict(zip(zip(W.ep[s], W.frame[s]), tn))
            else:
                d = np.array([t - base_tan[(e, f)] for e, f, t in zip(W.ep[s], W.frame[s], tn)])
                met["shift_tan_mean_abs"] = float(np.abs(d).mean())
                met["shift_tan_mean"] = float(d.mean())
            # within: 같은 변형으로 학습·평가
            Wv = W[W.variant == v].reset_index(drop=True)
            Xv = Xq[W.variant.values == v]
            pw = np.full((len(Wv), 2), np.nan)
            for fo in folds:
                tr = Wv.ep.isin(fo["train_eps"]).values
                te = Wv.ep.isin(fo["test_eps"]).values
                if te.any() and tr.sum() > 50:
                    m, _ = FP.ridge_cv(Xv[tr], Wv[FP.TGT_IMG].values[tr], Wv.ep.values[tr])
                    pw[te] = FP.ridge_pred(m, Xv[te])
            okw = ~np.isnan(pw[:, 0])
            wm, _ = tab_mae(pw[okw], Wv[okw])
            met["within"] = wm
            met["n"] = int(s.sum())
            r[v] = met
        out[key] = r
        print("wrist", key, {v: (round(r[v]["tan_mae"], 3), round(r[v]["within"]["tan_mae"], 3)) for v in Q.W_VARIANTS}, flush=True)
    return out


def front_part(folds):
    QM = pd.read_csv(QF / "meta.csv")
    Fm = QM[QM.src == "front_q"].reset_index(drop=True)
    cache = {}
    out = {"crop_window": list(Q.crop_window()) + [Q.CROP_W, Q.CROP_H],
           "n_eps_in_crop": int(Fm[(Fm.variant == "orig") & (Fm.frame == 0)].in_crop.sum())}
    sets = [(k, None) for k in F_KEYS] + [("front_rgb32", "rgb")]
    for key, kind in sets:
        r = {}
        for v in Q.F_VARIANTS:
            Fv = Fm[Fm.variant == v].reset_index(drop=True)
            if kind == "rgb":
                X = np.stack([cv2.resize(Q.transform(C_frame(cache, e, f), v), (32, 24), interpolation=cv2.INTER_AREA).ravel()
                              for e, f in zip(Fv.ep, Fv.frame)]).astype(np.float32) / 255
            else:
                X = FP.token_project(load(QF, key, Fv.row.values))
            Y = Fv[["cube_x", "cube_y"]].values
            P = np.full_like(Y, np.nan, dtype=float)
            for fo in folds:
                tr = Fv.ep.isin(fo["train_eps"]).values
                te = Fv.ep.isin(fo["test_eps"]).values
                if te.any():
                    m, _ = FP.ridge_cv(X[tr], Y[tr], Fv.ep.values[tr])
                    P[te] = FP.ridge_pred(m, X[te])
            ok = ~np.isnan(P[:, 0])
            res = {}
            for nm, sel in (("all", ok), ("in_crop", ok & Fv.in_crop.values.astype(bool))):
                e = np.linalg.norm(P[sel] - Y[sel], axis=1)
                ex, ey = P[sel, 0] - Y[sel, 0], P[sel, 1] - Y[sel, 1]
                res[nm] = dict(n=int(sel.sum()), dist_mae_cm=float(e.mean()), x_mae=float(np.abs(ex).mean()), y_mae=float(np.abs(ey).mean()),
                               x_r2=float(1 - (ex ** 2).sum() / ((Y[sel, 0] - Y[sel, 0].mean()) ** 2).sum()),
                               y_r2=float(1 - (ey ** 2).sum() / ((Y[sel, 1] - Y[sel, 1].mean()) ** 2).sum()))
            for f in Q.F_FRAMES:
                sel = ok & (Fv.frame.values == f)
                res[f"frame{f}_dist_mae_cm"] = float(np.linalg.norm(P[sel] - Y[sel], axis=1).mean())
            r[v] = res
        out[key] = r
        print("front", key, {v: round(r[v]["all"]["dist_mae_cm"], 2) for v in Q.F_VARIANTS},
              {v: round(r[v]["in_crop"]["dist_mae_cm"], 2) for v in Q.F_VARIANTS}, flush=True)
    return out


def C_frame(cache, e, f):
    return Q.C.frames(str(Q.C.D2 / "dataset"), int(e), "front", int(f), int(f), cache)[0]


def main():
    folds = json.load(open(OUT / "folds.json"))["folds"]
    res = {"wrist": wrist_part(folds), "front": front_part(folds)}
    json.dump(res, open(OUT / "f1_results/quality.json", "w"), indent=1)


if __name__ == "__main__":
    main()
