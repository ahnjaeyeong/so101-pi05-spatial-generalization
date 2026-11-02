"""F1 위치 추종 민감도 g_rep · 평가 롤아웃 (CPU, f1_extract.py 결과 필요).

g_rep (표현 이득): 편집 세트(meta src=edit, T1 128편 × 닫힘 1·2 s 전)에서
  wrist u/v ±1 cm 상당 이동: (예측(+) − 예측(−)) / 2 를 가한 이동(cm)으로 나눔 → 영상 축 이득 g_u, g_v,
  탁자 좌우 이득 g_tan = 예측 tan 변화 / 라벨 tan 변화 (라벨 변화 > 0.5 cm 인 쌍):
    g_tan_img_rot  : 영상 축 probe (rel_u, rel_v) 예측을 roll 로 회전 (roll 보정)
    g_tan_tab      : roll 없이 tan 을 직접 예측하는 probe (roll 미보정)
  front 접선 ±2 cm 이동: 예측 tan 변화 / 4 cm (wrist 특징 probe 는 따라가지 않는 것이 맞음)
  probe 는 그 판이 test 인 fold 에서 학습한 것 (판을 본 적 없는 probe). 특징 = f1_probe ridge 와 같은 token_project.
  비교 기준: 정책 행동 이득 (exp2b roll 모델, 같은 편집 방식) G_tt 0.10, G_rr 0.34, front pre 이득 0.006.
평가 롤아웃: train 프레임 전체로 학습한 probe → 평가 판 프레임 MAE.
  평가 라벨에 train 과 같은 조건 적용 (큐브 면적 ≥ MIN_AREA, 영상 경계에 닿지 않음) → eval_label_qc.csv.
  추가로 '라벨이 train 범위 안' 부분집합도 따로 (probe 외삽 구분).
사용: f1_sensitivity.py [--keys k1,k2] [--tag t]   출력: f1_results/sensitivity[_t].json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f1_probe as FP  # noqa: E402

OUT = FP.OUT
FEAT = FP.FEAT
MIN_AREA = 3000     # splits.py 와 같음
KEYS = ["sig_w26", "sig_w13"] + [f"kv_w:{li}:1" for li in range(6)] + ["kv_w:5:0", "sig_f26"]


def feats(key, rows_idx):
    if ":" in key:
        arr, li, kv = key.split(":")
        A = np.load(FEAT / f"{arr}.npy", mmap_mode="r")
        return np.concatenate([np.asarray(A[rows_idx[i:i + 512], int(li), int(kv)], np.float32) for i in range(0, len(rows_idx), 512)])
    A = np.load(FEAT / f"{key}.npy", mmap_mode="r")
    return np.concatenate([np.asarray(A[rows_idx[i:i + 512]], np.float32) for i in range(0, len(rows_idx), 512)])


def project(key, rows_idx):
    return np.concatenate([FP.token_project(feats(key, rows_idx[i:i + 512])) for i in range(0, len(rows_idx), 512)])


def eval_label_qc(Ev):
    """평가 프레임 wrist 큐브의 면적·경계 (train 의 probe_ok 와 같은 조건)."""
    p = OUT / "f1_results/eval_label_qc.csv"
    if p.exists():
        return pd.read_csv(p)
    import exp2_sensitivity as X2
    import cv2  # noqa: F401
    C = FP.C
    cache, out = {}, []
    for _, r in Ev.iterrows():
        wr = C.frames(r.ds, int(r.ep), "wrist", int(r.frame), int(r.frame), cache)[0]
        b = X2.find_blob(wr, None, min_area=200)
        h, w = wr.shape[:2]
        if b is None:
            out.append(dict(row=r.row, carea=np.nan, border=True))
            continue
        ys, xs = np.nonzero(b[2])
        out.append(dict(row=r.row, carea=b[0], border=bool(xs.min() <= 1 or ys.min() <= 1 or xs.max() >= w - 2 or ys.max() >= h - 2)))
    Q = pd.DataFrame(out)
    Q.to_csv(p, index=False)
    return Q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default=",".join(KEYS))
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    T, Ed, Ev, folds, ev_ok, ev_in = load_sets()
    lo_t, hi_t = T.tan_cm.min(), T.tan_cm.max()
    lo_r, hi_r = T.rad_cm.min(), T.rad_cm.max()
    out = {"eval_qc": dict(n_all=int(len(Ev)), n_ok=int(ev_ok.sum()), n_ok_in_train_range=int(ev_in.sum()),
                           train_tan_range=[float(lo_t), float(hi_t)], train_rad_range=[float(lo_r), float(hi_r)])}
    print(out["eval_qc"], flush=True)
    for key in args.keys.split(","):
        r = analyze(project(key, T.row.values), project(key, Ed.row.values), project(key, Ev.row.values), T, Ed, Ev, folds, ev_ok, ev_in)
        out[key] = r
        print(key, json.dumps(r), flush=True)
        json.dump(out | {"policy_reference": dict(G_tt=0.10, G_tt_ci=[0.02, 0.20], G_rr=0.34, front_pre_gain=0.006, source="exp2b roll model / exp2")},
                  open(OUT / f"f1_results/sensitivity{'_' + args.tag if args.tag else ''}.json", "w"), indent=1)


def load_sets():
    M = pd.read_csv(FEAT / "meta.csv")
    folds = json.load(open(OUT / "folds.json"))["folds"]
    T = M[(M.src == "train") & M.valid].reset_index(drop=True)
    Ed = M[(M.src == "edit") & M.valid].reset_index(drop=True)
    Ev = M[(M.src == "eval") & M.valid].reset_index(drop=True)
    Ev = Ev.merge(eval_label_qc(Ev), on="row", how="left")
    ev_ok = (Ev.carea >= MIN_AREA) & (Ev.border == False)  # noqa: E712
    ev_in = ev_ok & Ev.tan_cm.between(T.tan_cm.min(), T.tan_cm.max()) & Ev.rad_cm.between(T.rad_cm.min(), T.rad_cm.max())
    return T, Ed, Ev, folds, ev_ok, ev_in


def analyze(Xtr_all, Xed, Xev, T, Ed, Ev, folds, ev_ok, ev_in):
    """특징 (train 전체 · 편집 · 평가) → g_rep · 평가 MAE."""
    pred = {k: np.full((len(Ed), 2), np.nan) for k in ("img", "tab")}
    for fo in folds:
        tr = T.ep.isin(fo["train_eps"]).values
        te = Ed.ep.isin(fo["test_eps"]).values
        if not te.any():
            continue
        for k, tg in (("img", FP.TGT_IMG), ("tab", FP.TGT_TAB)):
            m, _ = FP.ridge_cv(Xtr_all[tr], T[tg].values[tr], T.ep.values[tr])
            pred[k][te] = FP.ridge_pred(m, Xed[te])
    rt, _ = FP.img_to_tab(pred["img"][:, 0], pred["img"][:, 1], Ed.roll.values)
    Ed2 = Ed.assign(pu=pred["img"][:, 0], pv=pred["img"][:, 1], pt_rot=rt, pt_tab=pred["tab"][:, 0])
    piv = Ed2.pivot_table(index=["ep", "frame"], columns="edit", values=["pu", "pv", "pt_rot", "pt_tab", "tan_cm"])
    r = {}
    try:
        r["g_u"] = float(np.nanmedian((piv["pu"]["wu+"] - piv["pu"]["wu-"]) / 2.0))
        r["g_v"] = float(np.nanmedian((piv["pv"]["wv+"] - piv["pv"]["wv-"]) / 2.0))
        for nm, col in (("g_tan_img_rot", "pt_rot"), ("g_tan_tab", "pt_tab")):
            gt = []
            for a, b in (("wu+", "wu-"), ("wv+", "wv-")):
                d_lab = piv["tan_cm"][a] - piv["tan_cm"][b]
                d_pred = piv[col][a] - piv[col][b]
                ok = d_lab.abs() > 0.5
                gt.append((d_pred[ok] / d_lab[ok]).values)
            gt = np.concatenate(gt)
            r[nm] = float(np.nanmedian(gt))
            r[nm + "_iqr"] = [float(np.nanpercentile(gt, 25)), float(np.nanpercentile(gt, 75))]
            r[nm + "_n"] = int(np.isfinite(gt).sum())
        r["g_tan_front_edit_img_rot"] = float(np.nanmedian((piv["pt_rot"]["f+"] - piv["pt_rot"]["f-"]) / 4.0))
        r["g_tan_front_edit_tab"] = float(np.nanmedian((piv["pt_tab"]["f+"] - piv["pt_tab"]["f-"]) / 4.0))
        r["n_edit_frames"] = int(len(piv))
    except KeyError as e:
        r["error"] = f"missing edit {e}"
    m_img, _ = FP.ridge_cv(Xtr_all, T[FP.TGT_IMG].values, T.ep.values)
    m_tab, _ = FP.ridge_cv(Xtr_all, T[FP.TGT_TAB].values, T.ep.values)
    pi = FP.ridge_pred(m_img, Xev)
    prt, prr = FP.img_to_tab(pi[:, 0], pi[:, 1], Ev.roll.values)
    pt = FP.ridge_pred(m_tab, Xev)
    for nm, sel in (("ok", ev_ok.values), ("ok_in_range", ev_in.values)):
        e = {}
        for pn, (a, b) in (("img_rot", (prt, prr)), ("tab", (pt[:, 0], pt[:, 1]))):
            et, er = a[sel] - Ev.tan_cm.values[sel], b[sel] - Ev.rad_cm.values[sel]
            e[pn] = dict(tan_mae=float(np.abs(et).mean()), rad_mae=float(np.abs(er).mean()),
                         tan_r2=float(1 - (et ** 2).sum() / ((Ev.tan_cm.values[sel] - Ev.tan_cm.values[sel].mean()) ** 2).sum()))
        e["n"] = int(sel.sum())
        r[f"eval_{nm}"] = e
    return r


if __name__ == "__main__":
    main()
