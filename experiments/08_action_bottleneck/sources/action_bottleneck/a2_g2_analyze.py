"""G2 (+ G1 hidden) 분석 (CPU). 입력: g2/{chunks,expert_hidden,attn_mass}.npy, g2/rows.csv, g1/expert_hidden.npy, a1_g1_rows.csv,
vision_probe (labels_v2, folds.json, f1_features). 출력 a2_g2.json, a2_*.csv. 로봇·GPU 안 씀.

  S1 같은 프레임 · 같은 라벨 · 같은 시간 범위 (h = min(50, 닫힘까지 프레임)) 의 '이후 이동' 기울기
       사람: 행동(목표 관절) a[f0+h] 의 집게 끝 − 현재 state 집게 끝 (state 기준 값도 같이)
       정책: chunk[min(h, 50) − 1] 의 집게 끝 − 현재 state 집게 끝
       fut_tan ~ tan_cm + rad_cm 회귀 기울기 (닫힘 0–1 · 1–2 · 2–3 s), 판 bootstrap. 정책 ~ 사람 R².
  S2 Expert 층별 probe (첫 denoise step 행동 토큰 평균 hidden, 1024): F1 과 같은 fold · ridge
       img→rot (영상 축 예측을 state roll 로 회전), tab (탁자 좌우를 바로), roll (도)
  S3 같은 probe 를 G1 편집 hidden 에 (그 판이 test 인 fold 의 probe):
       g_img (영상 이동 → 해독 tab 이동 / 기대), g_state (state roll 만 바꿈 → 해독 tab 이동 / 기대 dC), RC (기대 0) / RI
  S4 주의 질량 (층별, front · wrist · 문장 · state · roll · suffix)
  S5 F1 특징 해독값 (wrist Gemma L11 V · SigLIP L26, ridge img→rot, F1 fold 교차 예측) ~ 정책 pan · 집게 끝 이동, 사람과 비교
  S6 평가 프레임 (조건 통과): 정책 예측 이후 이동 ~ 라벨 tan (train 범위 안/밖)
"""
import json
import sys

import numpy as np
import pandas as pd

import ab_core as A
from ab_core import C

sys.path.insert(0, str(A.D2 / "vision_probe"))
import f1_probe as FP  # noqa: E402

G2 = A.AB / "g2"
VP = A.D2 / "vision_probe"
RNG = np.random.default_rng(0)
FPS = 30
PH = ((0, 1), (1, 2), (2, 3))


def axes(cx, cy):
    ur = np.stack([cx - C.BASE[0], cy - C.BASE[1]], 1)
    ur /= np.linalg.norm(ur, axis=1, keepdims=True)
    return np.stack([-ur[:, 1], ur[:, 0]], 1), ur


def slope_fit(d, ycol):
    X = np.column_stack([d.tan_cm, d.rad_cm, np.ones(len(d))])
    w = np.linalg.lstsq(X, d[ycol].values, rcond=None)[0]
    r = d[ycol].values - X @ w
    return w, float(1 - (r ** 2).sum() / ((d[ycol] - d[ycol].mean()) ** 2).sum())


def boot_eps(d, fn, n=1000):
    g = {e: x for e, x in d.groupby("ep")}
    ue = list(g)
    v = [fn(pd.concat([g[e] for e in RNG.choice(ue, len(ue))])) for _ in range(n)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip_s2s3", action="store_true", help="S2·S3 는 a2_s2s3_fromlog.json (이전 실행 로그) 에서 읽음")
    args = ap.parse_args()
    R = pd.read_csv(G2 / "rows.csv")
    ch = np.load(G2 / "chunks.npy").astype(np.float32).mean(0)
    H = np.load(G2 / "expert_hidden.npy", mmap_mode="r")
    AM = np.load(G2 / "attn_mass.npy")
    assert len(R) == len(ch) == len(H)
    tip = A.tip_fn()
    out = {}

    # ---------- S1 ----------
    data = {}
    fut = []
    for i, r in R.iterrows():
        if r.ds not in data:
            data[r.ds] = C.load_parquet(r.ds)
        s, a = data[r.ds][int(r.ep)]
        f0 = int(r.frame)
        h = int(min(50, max(1, round(r.t_to_close * FPS))))
        f1 = min(f0 + h, len(s) - 1)
        p0 = tip(s[f0, :5])[0]
        fut.append(np.concatenate([tip(a[f1, :5])[0] - p0, tip(s[f1, :5])[0] - p0, tip(ch[i, h - 1, :5])[0] - p0,
                                   [ch[i, h - 1, 0] - s[f0, 0], a[f1, 0] - s[f0, 0], h]]))
    fut = np.array(fut)
    ut, ur = axes(R.cube_x.values, R.cube_y.values)
    for nm, sl in (("hum_a", slice(0, 2)), ("hum_s", slice(2, 4)), ("pol", slice(4, 6))):
        R[f"{nm}_tan"] = (fut[:, sl] * ut).sum(1)
        R[f"{nm}_rad"] = (fut[:, sl] * ur).sum(1)
    R["pol_dpan"], R["hum_dpan"], R["h"] = fut[:, 6], fut[:, 7], fut[:, 8]
    Tr = R[R.src == "train"].copy()
    s1 = {}
    for lo, hi in PH:
        d = Tr[(Tr.t_to_close > lo) & (Tr.t_to_close <= hi)] if lo else Tr[Tr.t_to_close <= hi]
        row = {"n": len(d)}
        for who in ("hum_a", "hum_s", "pol"):
            for ax in ("tan", "rad"):
                w, r2 = slope_fit(d, f"{who}_{ax}")
                row[f"{who}_{ax}_slope"] = float(w[0] if ax == "tan" else w[1])
                row[f"{who}_{ax}_r2"] = r2
        for ax in ("tan", "rad"):
            row[f"diff_{ax}_ci"] = boot_eps(d, lambda x, ax=ax: slope_fit(x, f"pol_{ax}")[0][0 if ax == "tan" else 1]
                                            - slope_fit(x, f"hum_a_{ax}")[0][0 if ax == "tan" else 1], 500)
            c = np.corrcoef(d[f"pol_{ax}"], d[f"hum_a_{ax}"])[0, 1]
            row[f"pol_vs_hum_{ax}_r"] = float(c)
        s1[f"{lo}-{hi}s"] = row
    out["S1_future_slopes"] = s1

    # ---------- S2 Expert hidden probes ----------
    folds = json.load(open(VP / "folds.json"))["folds"]
    Tr = Tr.reset_index(drop=True)
    idx_tr = np.where(R.src.values == "train")[0]
    L = pd.read_csv(VP / "labels_v2.csv", low_memory=False)
    L = L[L.probe_ok.astype(bool)].reset_index(drop=True)
    key = list(zip(L.ep, L.frame))
    pos = {k: i for i, k in enumerate(zip(Tr.ep, Tr.frame))}
    order = np.array([pos[k] for k in key])            # labels_v2 순서 → G2 train 행
    rows = L.copy()
    nL = H.shape[1]
    s2, probes = {}, {}
    for li in ([] if args.skip_s2s3 else range(nL)):
        X = np.asarray(H[idx_tr[order], li], np.float32)
        res, preds = FP.run_cv(f"expert_L{li}", lambda tr, te, X=X: (X[tr], X[te]), rows, folds, "ridge")
        # roll 해독
        pr = np.full(len(rows), np.nan)
        for fo in folds:
            tr = np.where(rows.ep.isin(fo["train_eps"]).values)[0]
            te = np.where(rows.ep.isin(fo["test_eps"]).values)[0]
            m, _ = FP.ridge_cv(X[tr], rows.roll.values[tr, None], rows.ep.values[tr])
            pr[te] = FP.ridge_pred(m, X[te])[:, 0]
        ok = ~np.isnan(pr)
        e = pr[ok] - rows.roll.values[ok]
        s2[f"L{li}"] = dict(img_rot_tan=res["img_rot"]["tan_cm"]["mae"], img_rot_tan_r2=res["img_rot"]["tan_cm"]["r2"],
                            img_rot_rad=res["img_rot"]["rad_cm"]["mae"], tab_tan=res["tab"]["tan_cm"]["mae"], tab_tan_r2=res["tab"]["tan_cm"]["r2"],
                            tab_rad=res["tab"]["rad_cm"]["mae"], img_u=res["img"]["rel_u_cm"]["mae"], img_v=res["img"]["rel_v_cm"]["mae"],
                            roll_mae=float(np.abs(e).mean()), roll_r2=float(1 - (e ** 2).sum() / ((rows.roll.values[ok] - rows.roll.values[ok].mean()) ** 2).sum()))
        # fold 별 probe 저장 (S3)
        probes[li] = []
        for fo in folds:
            tr = np.where(rows.ep.isin(fo["train_eps"]).values)[0]
            mi, _ = FP.ridge_cv(X[tr], rows[FP.TGT_IMG].values[tr], rows.ep.values[tr])
            mt, _ = FP.ridge_cv(X[tr], rows[FP.TGT_TAB].values[tr], rows.ep.values[tr])
            probes[li].append((set(fo["test_eps"]), mi, mt))
        print("S2", li, s2[f"L{li}"], flush=True)
    out["S2_expert_probe"] = s2
    if args.skip_s2s3:
        out.update(json.load(open(A.AB / "a2_s2s3_fromlog.json")))

    # ---------- S3 G1 hidden ----------
    p1 = A.AB / "a1_g1_rows.csv"
    if p1.exists() and not args.skip_s2s3:
        G = pd.read_csv(p1)
        _, _, HG = A.load_g1(hidden=True)
        assert len(HG) == len(G)
        s3 = {}
        for li in range(nL):
            X = np.asarray(HG[:, li], np.float32)
            dec_tab = np.full((len(G), 2), np.nan)
            dec_img = np.full((len(G), 2), np.nan)
            for te_eps, mi, mt in probes[li]:
                m = G.ep.isin(te_eps).values
                if m.any():
                    dec_tab[m] = FP.ridge_pred(mt, X[m])
                    dec_img[m] = FP.ridge_pred(mi, X[m])
            G["dt_tan"], G["dt_rad"] = dec_tab[:, 0], dec_tab[:, 1]
            G["di_u"], G["di_v"] = dec_img[:, 0], dec_img[:, 1]
            num_i = den_i = num_s = den_s = num_rc = den_rc = 0.0
            gi_u = []
            for (e, ph), g in G.groupby(["ep", "phase"]):
                g = g.set_index(["cond", "droll"])
                if ("F:base", 0.0) not in g.index or np.isnan(g.loc[("F:base", 0.0)].dt_tan):
                    continue
                b0 = g.loc[("F:base", 0.0)]
                roll = b0.roll
                rel = np.array([b0.rel_u, b0.rel_v])
                M0 = A.M_img2tab(roll)
                tb = np.array([b0.dt_tan, b0.dt_rad])
                # 영상 이동: 기대 tab 변화 = M0 · e
                for c, ev in (("F:wu+", (1, 0)), ("F:wu-", (-1, 0)), ("F:wv+", (0, 1)), ("F:wv-", (0, -1))):
                    if (c, 0.0) in g.index:
                        y = np.array([g.loc[(c, 0.0)].dt_tan, g.loc[(c, 0.0)].dt_rad]) - tb
                        x = M0 @ np.array(ev, float)
                        num_i += x @ y
                        den_i += x @ x
                        gi_u.append(np.array([g.loc[(c, 0.0)].di_u, g.loc[(c, 0.0)].di_v]) - np.array([b0.di_u, b0.di_v]))
                for d in (-30.0, -15.0, 15.0, 30.0):
                    if ("F:base", d) in g.index:
                        y = np.array([g.loc[("F:base", d)].dt_tan, g.loc[("F:base", d)].dt_rad]) - tb
                        x = (A.M_img2tab(roll + d) - M0) @ rel
                        num_s += x @ y
                        den_s += x @ x
                    if (f"RC:{d:+.0f}", d) in g.index and (f"RI:{d:+.0f}", 0.0) in g.index:
                        yc = np.array([g.loc[(f"RC:{d:+.0f}", d)].dt_tan, g.loc[(f"RC:{d:+.0f}", d)].dt_rad]) - tb
                        yi = np.array([g.loc[(f"RI:{d:+.0f}", 0.0)].dt_tan, g.loc[(f"RI:{d:+.0f}", 0.0)].dt_rad]) - tb
                        num_rc += yi @ yc
                        den_rc += yi @ yi
            s3[f"L{li}"] = dict(g_img_tab=num_i / den_i if den_i else None, g_state_tab=num_s / den_s if den_s else None,
                                w_RC_tab=1 - num_rc / den_rc if den_rc else None,
                                img_axis_follow=float(np.median(np.abs(np.array(gi_u)).max(1))) if gi_u else None)
            print("S3", li, s3[f"L{li}"], flush=True)
        out["S3_expert_hidden_edits"] = s3

    # ---------- S4 attention mass ----------
    names = ["front", "wrist", "task", "state_other", "roll", "suffix", "pad"]
    tr_m = R.src.values == "train"
    s4 = {}
    for lo, hi in PH:
        m = tr_m & (R.t_to_close.values > lo - 1e-9) & (R.t_to_close.values <= hi)
        s4[f"{lo}-{hi}s"] = {f"L{li}": dict(zip(names, AM[m, li].mean(0).round(4).tolist())) for li in range(nL)}
    s4["n_roll_tokens"] = R.roll_tokens.fillna("").str.split().str.len().value_counts().to_dict()
    out["S4_attention"] = s4

    # ---------- S5 F1 특징 해독값 ~ 정책 · 사람 ----------
    M = pd.read_csv(VP / "f1_features/meta.csv")
    trm = M[(M.src == "train") & M.valid].reset_index(drop=True)
    idx = trm.row.values
    s5 = {}
    for keyf, lab in (("kv_w:3:1", "Gemma L11 V"), ("sig_w26", "SigLIP L26")):
        if ":" in keyf:
            arr, li, kv = keyf.split(":")
            Af = np.load(VP / "f1_features" / f"{arr}.npy", mmap_mode="r")
            Tf = lambda ii, Af=Af, li=int(li), kv=int(kv): np.asarray(Af[idx[ii], li, kv], np.float32)  # noqa: E731
        else:
            Af = np.load(VP / "f1_features" / f"{keyf}.npy", mmap_mode="r")
            Tf = lambda ii, Af=Af: np.asarray(Af[idx[ii]], np.float32)  # noqa: E731
        flat = np.concatenate([FP.token_project(Tf(np.arange(i, min(len(rows), i + 512)))) for i in range(0, len(rows), 512)])
        _, preds = FP.run_cv(keyf.replace(":", "_"), lambda tr, te: (flat[tr], flat[te]), rows, folds, "ridge")
        dec = preds["img_rot"]
        D = rows[["ep", "frame", "t_to_close", "tan_cm", "rad_cm", "cube_x", "cube_y", "group"]].copy()
        D["dec_tan"], D["dec_rad"] = dec[:, 0], dec[:, 1]
        G2r = Tr.iloc[order].reset_index(drop=True)
        for c in ("pol_tan", "pol_rad", "hum_a_tan", "hum_a_rad", "pol_dpan", "hum_dpan"):
            D[c] = G2r[c].values
        D["range_cm"] = np.hypot(D.cube_x - C.BASE[0], D.cube_y - C.BASE[1])
        D = D.dropna(subset=["dec_tan"])
        row = {}
        for lo, hi in PH:
            d = D[(D.t_to_close > lo) & (D.t_to_close <= hi)] if lo else D[D.t_to_close <= hi]
            r = {"n": len(d)}
            for who in ("pol", "hum_a"):
                X = np.column_stack([d.dec_tan, d.dec_rad, np.ones(len(d))])
                w = np.linalg.lstsq(X, d[f"{who}_tan"].values, rcond=None)[0]
                r[f"{who}_tan_on_dec_slope"] = float(w[0])
                # pan: 접선 1 cm 당 기하 기대 57.3/range 도 → 정규화 이득
                y = d["pol_dpan" if who == "pol" else "hum_dpan"].values / (-57.2958 / d.range_cm.values)    # pan + = 로봇 오른쪽 = 접선 − (C 좌표 규약)
                w2 = np.linalg.lstsq(X, y, rcond=None)[0]
                r[f"{who}_pan_on_dec_gain"] = float(w2[0])
            r["dec_vs_label_tan_r"] = float(np.corrcoef(d.dec_tan, d.tan_cm)[0, 1])
            row[f"{lo}-{hi}s"] = r
        s5[lab] = row
        print("S5", lab, row, flush=True)
        D.to_csv(A.AB / f"a2_s5_{keyf.replace(':', '_')}.csv", index=False)
    out["S5_feature_to_action"] = s5

    # ---------- S6 eval ----------
    Ev = R[R.src == "eval"].copy()
    qc = pd.read_csv(VP / "f1_results/eval_label_qc.csv")
    Ev = Ev.merge(qc, on="row", how="left")
    Ev = Ev[(Ev.carea >= 3000) & (~Ev.border.astype(bool))]
    inr = Ev.tan_cm.between(-2.20, 1.46) & Ev.rad_cm.between(-3.96, 1.54)
    s6 = {"n": len(Ev), "n_in_range": int(inr.sum())}
    for nm, d in (("in_range", Ev[inr]), ("out_range", Ev[~inr])):
        if len(d) > 10:
            w, r2 = slope_fit(d, "pol_tan")
            s6[nm] = dict(n=len(d), pol_tan_slope=float(w[0]), r2=r2, label_tan_absmed=float(d.tan_cm.abs().median()),
                          pol_tan_absmed=float(d.pol_tan.abs().median()))
    out["S6_eval"] = s6
    R.to_csv(A.AB / "a2_g2_rows.csv", index=False)
    json.dump(out, open(A.AB / "a2_g2.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "S4_attention"}, indent=1, default=float)[:5000])


if __name__ == "__main__":
    main()
