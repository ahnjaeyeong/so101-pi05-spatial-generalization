"""2차 실험 분석 (읽기만): exp1–exp4 결과 → exp_summary.json + exp_*.csv. 그림은 exp_plots.py (시스템 python3).

측정 아티팩트 분리 (실험 5) 방법
  A. 보정 곡선: 학습 Random 판(학습에 쓴 표본) start 프로브에서 chunk 끝 pan = p0 + k±·(사람 pan − p0) 를 맞춘다
     (p0 = 시작 pan 중앙값, 회전 방향(±)마다 k 따로). 이 곡선은 '학습 위치에서 1.67 s 안에 덜 돈 정도'다.
     grid 예측에서 이 곡선값을 뺀 잔차를 K 방향·중앙 방향에 회귀 → 보정 후 계수.
     같은 회귀를 학습 Random 판 잔차에도 해서 '학습 위치에서도 있는 K 끌림'과 '새 위치에서만 생기는 끌림'을 나눈다.
  B. chunk 끝에서의 남은 속도: index 40→49 pan 변화. 0 에 가까우면 chunk 끝이 이미 평탄 (덜 돈 것이 아니라 그 방향을 고른 것).
  C. 아티팩트 없는 국소 측정: exp2 'pre' 단계 (파지 1 s 전, chunk index 30 = 실제 닫힘 시각) 의 큐브 이동 민감도.
"""
import json
import math

import numpy as np
import pandas as pd

import common as C

OUT = C.OUT
K = C.load_known()
KPAN = {k: C.pan_expected(*v) for k, v in K.items()}


def nearest_k(x, y):
    return min(K, key=lambda k: math.hypot(x - K[k][0], y - K[k][1]))


def ols(y, cols):
    X = np.column_stack([np.ones(len(y))] + list(cols))
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return b


def boot_ols(y, cols, n=2000, seed=0):
    y = np.asarray(y)
    cols = [np.asarray(c) for c in cols]
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        bs.append(ols(y[i], [c[i] for c in cols]))
    bs = np.array(bs)
    b = ols(y, cols)
    return [dict(est=float(b[j]), lo=float(np.percentile(bs[:, j], 2.5)), hi=float(np.percentile(bs[:, j], 97.5))) for j in range(len(b))]


def calib_fit(human, pred, p0):
    """pred − p0 = k± (human − p0), 회전 방향별."""
    out = {}
    for sg in (1, -1):
        msk = np.sign(human - p0) == sg
        h, p = human[msk] - p0, pred[msk] - p0
        out[sg] = float((h * p).sum() / (h * h).sum())
    return out


def calib_apply(target, p0, k):
    d = target - p0
    return p0 + np.where(d >= 0, k[1], k[-1]) * d


def exp1():
    T = pd.read_csv(OUT / "grasp_train.csv")
    G = pd.read_csv(OUT / "exp1/grid_info.csv")
    G["pan_exp"] = [C.pan_expected(x, y) for x, y in zip(G.x, G.y)]
    G["nearest_train_cm"] = [float(np.min(np.hypot(T.cube_x - x, T.cube_y - y))) for x, y in zip(G.x, G.y)]
    G["nK"] = [nearest_k(x, y) for x, y in zip(G.x, G.y)]
    G["nK_cm"] = [math.hypot(x - K[k][0], y - K[k][1]) for x, y, k in zip(G.x, G.y, G.nK)]
    G["K_pan"] = G.nK.map(KPAN)
    T["nK"] = [nearest_k(x, y) for x, y in zip(T.cube_x, T.cube_y)]
    T["K_pan"] = T.nK.map(KPAN)
    T["mode"] = T.group.str[2]
    res, rows = {}, []
    for step in ("005000", "010000", "015000", "020000"):
        p = OUT / f"exp1/ckpt_{step}.npz"
        if not p.exists():
            continue
        Z = np.load(p)
        st = Z["start_pan"]          # noise × 256 × 50
        pr = Z["pregrasp"]           # noise × 256 × 50 × 6
        gr = Z["grid_pan"]           # noise × G × 50
        meta = json.load(open(OUT / f"exp1/ckpt_{step}.json"))
        r = dict(step=step, gpu_busy_s=meta["gpu_busy_s"])
        sp = st[:, :, 49].mean(0)
        R = (T["mode"] == "R").values
        for md, msk in (("K", ~R), ("R", R)):
            b = ols(sp[msk], [T.s_shoulder_pan.values[msk]])
            r[f"start_slope_{md}"] = float(b[1])
            r[f"start_abs_err_med_{md}"] = float(np.median(np.abs(sp[msk] - T.s_shoulder_pan.values[msk])))
            pe = pr[:, :, 30, 0].mean(0)[msk] - T.s_shoulder_pan.values[msk]
            r[f"pre_pan_abs_err_med_{md}"] = float(np.median(np.abs(pe)))
            r[f"pre_pan_bias_{md}"] = float(pe.mean())
        r["start_tail_vel_med"] = float(np.median(np.abs(st[:, :, 49] - st[:, :, 40]).mean(0)))
        r["grid_tail_vel_med"] = float(np.median(np.abs(gr[:, :, 49] - gr[:, :, 40]).mean(0)))
        r["start_seed_sd_med"] = float(np.median(st[:, :, 49].std(0)))
        r["grid_seed_sd_med"] = float(np.median(gr[:, :, 49].std(0)))
        # A. 보정 곡선 (학습 Random)
        p0 = float(np.median(st[:, :, 0].mean(0)))
        k = calib_fit(T.s_shoulder_pan.values[R], sp[R], p0)
        r["calib_p0"], r["calib_k_pos"], r["calib_k_neg"] = p0, k[1], k[-1]
        gp = gr[:, :, 49].mean(0)
        g = G.assign(pred=gp, err_raw=gp - G.pan_exp, err_cal=gp - calib_apply(G.pan_exp.values, p0, k))
        ind = g[g.nearest_train_cm <= 3]
        r["grid_slope_raw"] = float(ols(ind.pred.values, [ind.pan_exp.values])[1])
        r["grid_abs_err_raw_med"] = float(ind.err_raw.abs().median())
        r["grid_abs_err_cal_med"] = float(ind.err_cal.abs().median())
        for tag, col in (("raw", "err_raw"), ("cal", "err_cal")):
            bb = boot_ols(ind[col].values, [(ind.K_pan - ind.pan_exp).values, (0 - ind.pan_exp).values])
            r[f"grid_{tag}_aK"], r[f"grid_{tag}_cC"] = bb[1], bb[2]
        # 같은 회귀를 학습 Random 판 (보정 후) — 학습 위치에서도 있는 끌림
        tr = T[R].assign(pred=sp[R])
        tr_err = tr.pred.values - calib_apply(tr.s_shoulder_pan.values, p0, k)
        bb = boot_ols(tr_err, [(tr.K_pan - tr.s_shoulder_pan).values, (0 - tr.s_shoulder_pan).values])
        r["trainR_cal_aK"], r["trainR_cal_cC"] = bb[1], bb[2]
        for lo, hi in ((0, 2), (2, 4), (4, 6)):
            d = g[(g.nearest_train_cm >= lo) & (g.nearest_train_cm < hi)]
            r[f"grid_abs_err_cal_med_{lo}_{hi}cm"] = [float(d.err_cal.abs().median()), len(d)]
        res[step] = r
        g.assign(step=step).to_csv(OUT / f"exp1/grid_eval_{step}.csv", index=False)
        rows.append(r)
    return res


def fk_tip(j5):
    import fk  # noqa
    fit = json.load(open(OUT / "fk_fit.json"))
    Rm, t = np.array(fit["R"]), np.array(fit["t"])
    p, _ = C.fk_xy(j5)
    return (Rm @ (p[:, :2] * 100).T).T + t


def exp2():
    p = OUT / "exp2/sens.npz"
    if not p.exists():
        return None
    ch = np.load(p)["chunks"]   # noise × N × 50 × 6
    D = pd.read_csv(OUT / "exp2/rows.csv")
    D["mode"] = D.group.str[2]
    mean = ch.mean(0)
    D["idx"] = np.where(D.phase == "pre", 30, 49)
    D["pan"] = mean[np.arange(len(D)), D.idx.values, 0]
    tip = fk_tip(mean[np.arange(len(D)), 30, :5])
    D["tip_x"], D["tip_y"] = tip[:, 0], tip[:, 1]
    out = {}
    key = ["ep", "phase"]
    base = D[D.cond == "base"].set_index(key)
    for ph in ("start", "mid", "pre"):
        r = {}
        b = base.xs(ph, level="phase")
        # 단계별 측정 기울기 (base 예측 pan vs 사람 파지 pan)
        r["n_obs"] = int(len(b))
        r["meas_slope_vs_human"] = float(ols(b.pan.values, [b.human_pan.values])[1])
        fp = D[(D.phase == ph) & (D.cond == "f+")].set_index("ep")
        fm = D[(D.phase == ph) & (D.cond == "f-")].set_index("ep")
        f0 = D[(D.phase == ph) & (D.cond == "f0")].set_index("ep")
        eps = fp.index.intersection(fm.index)
        r["front_n"] = int(len(eps))
        if len(eps):
            dgeom = fp.loc[eps, "d_pan_geom"] - fm.loc[eps, "d_pan_geom"]
            gain = (fp.loc[eps, "pan"] - fm.loc[eps, "pan"]) / dgeom
            r["front_pan_gain_med"] = float(gain.median())
            r["front_pan_gain_iqr"] = [float(gain.quantile(.25)), float(gain.quantile(.75))]
            r["front_pan_gain_by_mode"] = {md: float(gain[fp.loc[eps, "mode"] == md].median()) for md in ("K", "R")}
            r["front_repaste_abs_dpan_med"] = float((f0.loc[eps, "pan"] - b.loc[eps, "pan"]).abs().median())
            if ph == "pre":
                # 집게 끝(FK) 접선 이동 / 큐브 이동 (4 cm)
                x, y = b.loc[eps, "cube_x"], b.loc[eps, "cube_y"]
                ur = np.stack([x - C.BASE[0], y - C.BASE[1]], 1)
                ur /= np.linalg.norm(ur, axis=1, keepdims=True)
                ut = np.stack([-ur[:, 1], ur[:, 0]], 1)
                dt = np.stack([fp.loc[eps, "tip_x"] - fm.loc[eps, "tip_x"], fp.loc[eps, "tip_y"] - fm.loc[eps, "tip_y"]], 1)
                g_t = (dt * ut).sum(1) / 4.0
                r["front_tip_tan_gain_med"] = float(np.median(g_t))
                # K 쪽으로 옮겼을 때 vs 반대로 옮겼을 때 (Random 판만)
                R = b.loc[eps]
                kdir = []
                for e in eps:
                    nk = nearest_k(R.loc[e, "cube_x"], R.loc[e, "cube_y"])
                    kdir.append(np.sign(KPAN[nk] - R.loc[e, "pan_exp"]))
                kdir = np.array(kdir)
                # f+ 는 로봇 왼쪽 = pan 감소. pan 이 K 쪽으로 가는 이동 = sign(Δpan_geom) == kdir
                toK = np.where(np.sign(fp.loc[eps, "d_pan_geom"]) == kdir, fp.loc[eps, "pan"], fm.loc[eps, "pan"]) - b.loc[eps, "pan"]
                awK = np.where(np.sign(fp.loc[eps, "d_pan_geom"]) == kdir, fm.loc[eps, "pan"], fp.loc[eps, "pan"]) - b.loc[eps, "pan"]
                half = (dgeom.abs() / 2).values
                gK = toK * kdir / half          # 1 = 큐브를 K 쪽으로 옮긴 만큼 정확히 따라감
                gA = awK * (-kdir) / half       # 1 = K 반대쪽으로 옮긴 만큼 정확히 따라감
                isR = (b.loc[eps, "mode"] == "R").values
                r["front_gain_toward_K_R"] = float(np.median(gK[isR])) if isR.any() else None
                r["front_gain_away_K_R"] = float(np.median(gA[isR])) if isR.any() else None
                r["front_toward_away_n_R"] = int(isR.sum())
        # wrist: (wu+ − wu−)/2 cm, (wv+ − wv−)/2 cm → 집게 끝 이동 야코비안 (pre), pan 이동 (전 단계)
        Wd = {c: D[(D.phase == ph) & (D.cond == c)].set_index("ep") for c in ("wu+", "wu-", "wv+", "wv-", "w0")}
        epw = Wd["wu+"].index
        r["wrist_n"] = int(len(epw))
        if len(epw):
            pu = (Wd["wu+"].loc[epw, "pan"] - Wd["wu-"].loc[epw, "pan"]) / 2
            pv = (Wd["wv+"].loc[epw, "pan"] - Wd["wv-"].loc[epw, "pan"]) / 2
            ideal = 180 / math.pi / b.loc[epw, "range_cm"]   # 큐브 1 cm 접선 이동 = pan 변화 (°)
            r["wrist_pan_grad_norm_over_ideal_med"] = float((np.hypot(pu, pv) / ideal).median())
            r["wrist_repaste_abs_dpan_med"] = float((Wd["w0"].loc[epw, "pan"] - b.loc[epw, "pan"]).abs().median())
            if ph == "pre":
                du = np.stack([Wd["wu+"].loc[epw, "tip_x"] - Wd["wu-"].loc[epw, "tip_x"], Wd["wu+"].loc[epw, "tip_y"] - Wd["wu-"].loc[epw, "tip_y"]], 1) / 2
                dv = np.stack([Wd["wv+"].loc[epw, "tip_x"] - Wd["wv-"].loc[epw, "tip_x"], Wd["wv+"].loc[epw, "tip_y"] - Wd["wv-"].loc[epw, "tip_y"]], 1) / 2
                sv = [np.linalg.svd(np.stack([du[i], dv[i]], 1), compute_uv=False) for i in range(len(epw))]
                sv = np.array(sv)
                r["wrist_tip_jac_sv_med"] = [float(np.median(sv[:, 0])), float(np.median(sv[:, 1]))]
                r["wrist_tip_gain_u_med"] = float(np.median(np.linalg.norm(du, axis=1)))
                r["wrist_tip_gain_v_med"] = float(np.median(np.linalg.norm(dv, axis=1)))
        out[ph] = r
    D.to_csv(OUT / "exp2/rows_eval.csv", index=False)
    return out


def exp3():
    p = OUT / "exp3/replans.npz"
    if not p.exists():
        return None
    Tk = pd.read_csv(OUT / "exp3/ticks.csv")
    M = pd.read_csv(OUT / "exp3/merges.csv")
    Z = np.load(p)
    rows = []
    for i, r in M.iterrows():
        d = int(r.real_delay)
        f0 = int(r.frame_merge)
        seg = Tk[(Tk.frame >= f0) & (Tk.frame < f0 + 20)]
        for s in (5, 10):
            ch = Z[f"s{s}"][:, i, :, 0]   # noise × 50
            n = len(seg)
            rows.append(dict(merge=i, steps=s, t=f0 / 30, frame_obs=int(r.frame_obs), real_delay=d,
                             state_pan_obs=Tk.loc[Tk.frame == r.frame_obs, "state_shoulder_pan"].iloc[0] if (Tk.frame == r.frame_obs).any() else np.nan,
                             model_exec_mean=float(ch[:, d:d + n].mean()) if n else np.nan,
                             model_end=float(ch[:, 49].mean()), model_end_sd=float(ch[:, 49].std()),
                             raw_exec_mean=float(seg.raw_shoulder_pan.mean()) if n else np.nan,
                             out_exec_mean=float(seg.out_shoulder_pan.mean()) if n else np.nan,
                             sent_exec_mean=float(seg.sent_shoulder_pan.mean()) if n else np.nan,
                             state_exec_mean=float(seg.state_shoulder_pan.mean()) if n else np.nan))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "exp3/merge_compare.csv", index=False)
    s5 = R[R.steps == 5]
    w = s5[(s5.t >= 14) & (s5.t <= 29)]
    out = dict(
        window="14–29 s",
        n_merges=int(len(w)),
        raw_minus_model_exec_mean=float((w.raw_exec_mean - w.model_exec_mean).mean()),
        raw_minus_model_exec_absmed=float((w.raw_exec_mean - w.model_exec_mean).abs().median()),
        model_end_minus_state_mean=float((w.model_end - w.state_pan_obs).mean()),
        out_minus_raw_mean=float((w.out_exec_mean - w.raw_exec_mean).mean()),
        sent_minus_out_mean=float((w.sent_exec_mean - w.out_exec_mean).mean()),
        state_minus_sent_mean=float((w.state_exec_mean - w.sent_exec_mean).mean()),
        model_end_first_last=[float(w.model_end.iloc[0]), float(w.model_end.iloc[-1])],
        raw_first_last=[float(w.raw_exec_mean.iloc[0]), float(w.raw_exec_mean.iloc[-1])],
        model_end_seed_sd_med=float(w.model_end_sd.median()),
        steps10_minus_steps5_end_mean=float((R[R.steps == 10].model_end.values - s5.model_end.values)[(s5.t >= 14).values & (s5.t <= 29).values].mean()),
    )
    return out


def exp4():
    p = OUT / "exp4/seeds.npz"
    if not p.exists():
        return None
    Z = np.load(p)
    D = pd.read_csv(OUT / "exp4/rows.csv")
    out = {}
    rows = []
    for s in (5, 10):
        ch = Z[f"s{s}"]   # noise × N × 50 × 6
        for i, r in D.iterrows():
            idx = 30 if r["set"] == "train_pre" else 49
            v = ch[:, i, idx, 0]
            med = np.median(v)
            rows.append(dict(r.to_dict(), steps=s, idx=idx, pan_med=float(med), pan_sd=float(v.std()),
                             pan_p05=float(np.percentile(v, 5)), pan_p95=float(np.percentile(v, 95)),
                             frac_within3=float((np.abs(v - med) <= 3).mean()),
                             grip_min_sd=float(ch[:, i, :, 5].min(1).std())))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "exp4/seed_stats.csv", index=False)
    for st, g in R.groupby(["set", "steps"]):
        out[f"{st[0]}|steps{st[1]}"] = dict(n=len(g), pan_sd_med=float(g.pan_sd.median()), pan_sd_max=float(g.pan_sd.max()),
                                             p90_width_med=float((g.pan_p95 - g.pan_p05).median()),
                                             frac_within3_med=float(g.frac_within3.median()))
    return out


def main():
    S = dict(exp1=exp1(), exp2=exp2(), exp3=exp3(), exp4=exp4())

    def conv(o):
        if isinstance(o, dict):
            return {k: conv(v) for k, v in o.items()}
        if isinstance(o, list):
            return [conv(v) for v in o]
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
        return o

    S = conv(S)
    json.dump(S, open(OUT / "exp_summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(S, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
