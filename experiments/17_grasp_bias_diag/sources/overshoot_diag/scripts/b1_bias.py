#!/home/user/so101-env/bin/python
"""닫을 때 편향 P1 · P2 · P3 (CPU, 원본 읽기만). 설계: ../10_bias_design.md
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python b1_bias.py → ../data/bias.json
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import o1_real_chain as O  # noqa: E402  (경로 · 검출 · 닫기 규칙 재사용)
import sg_fk  # noqa: E402
import sg_phase  # noqa: E402

rc = O.rc
cfg = rc.load_config(os.environ["R12_CONFIG"])
RAW = os.path.expanduser("~/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001/eval/raw")
CLOSES = json.load(open(os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/reports/data/per_episode_closes.json")))


def tip(q):
    p, _ = sg_fk.fk(np.atleast_2d(np.asarray(q, float))[:, :5])
    return p * 100.0  # cm


# 옆 성분 부호: pan + 방향이 + 가 되게
_p0, _p1 = tip([0, -60, 60, 70, 90])[0], tip([10, -60, 60, 70, 90])[0]
_r = _p0[:2] / np.linalg.norm(_p0[:2])
TSIGN = 1.0 if (_p1[:2] - _p0[:2]) @ np.array([-_r[1], _r[0]]) > 0 else -1.0


def decomp(p_ref, d):
    """기준 끝 위치 p_ref (cm) 에서의 차 d → (바깥 = 반지름 +, 옆 = pan + 방향, 높이)."""
    r = p_ref[:2] / max(np.linalg.norm(p_ref[:2]), 1e-9)
    t = TSIGN * np.array([-r[1], r[0]])
    return np.array([d[:2] @ r, d[:2] @ t, d[2]])


def quad(xy):
    xy = np.atleast_2d(xy)
    x, y = xy[:, 0], xy[:, 1]
    return np.c_[np.ones(len(x)), x, y, x * x, x * y, y * y]


def fit_loo(XY, Y):
    A = quad(XY)
    W = np.linalg.lstsq(A, Y, rcond=None)[0]
    res = []
    for i in range(len(XY)):
        m = np.arange(len(XY)) != i
        w = np.linalg.lstsq(A[m], Y[m], rcond=None)[0]
        res.append(Y[i] - A[i] @ w)
    return W, np.array(res)


def sign_p(k, n):
    """양쪽 부호 검정 p (k = 많은 쪽 수)."""
    from math import comb
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def mwu_p(a, b):
    from scipy.stats import mannwhitneyu
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    return float(mannwhitneyu(a, b, alternative="two-sided").pvalue) if len(a) and len(b) else None


def human():
    info, em, d3 = O.load_ds(f"{O.P3}/dataset")
    rows = []
    for ep in range(3, 43):
        e = d3[d3.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        ci = sg_phase.analyze(st, ac, 30)["_idx"]["close"]
        fr = O.frames(f"{O.P3}/dataset", info, em, ep, [0], cam="front")[0]
        xy = rc.vision(fr, None, cfg)["front"]["xy_cm"]
        w = O.frames(f"{O.P3}/dataset", info, em, ep, [ci - 3])[ci - 3]
        rows.append(dict(ep=ep, xy=list(xy), q=st[ci, :5].tolist(), tip=tip(st[ci])[0].tolist(), **O.err_of(w)))
    return rows


def main():
    H = human()
    XY = np.array([r["xy"] for r in H], float)
    Q = np.array([r["q"] for r in H])
    P = np.array([r["tip"] for r in H])
    Wq, Rq = fit_loo(XY, Q)
    Wp, Rp = fit_loo(XY, P)
    Rp_d = np.array([decomp(P[i], Rp[i]) for i in range(len(P))])
    out = {"human": {"n": len(H), "loo_sd_joint": dict(zip(O.J, Rq.std(0).tolist())), "loo_sd_tip_out_side_up": Rp_d.std(0).tolist(),
                     "wrist_close": {k: [float(np.mean([r[k] for r in H])), float(np.std([r[k] for r in H]))] for k in ("du", "dv", "size", "dangle")},
                     "rows": H}}
    # 실물
    info, em, df = O.load_ds(f"{O.R}/dataset")
    T = pd.read_csv(f"{O.R}/diag/ticks.csv")
    robot = []
    gcols = [f"goal_in_{j}" for j in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")]
    for de, ep in O.DIAG2DS.items():
        e = df[df.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        gi = T[T.episode == de].reset_index(drop=True)[gcols].values.astype(float)
        closes, held = O.close_attempts(st, ac)
        xy = np.array(CLOSES[ep]["cube"], float)
        q_exp = (quad(xy) @ Wq)[0]
        p_exp = (quad(xy) @ Wp)[0]
        imgs = O.frames(f"{O.R}/dataset", info, em, ep, [max(0, k - 3) for k in closes]) if closes else {}
        att = []
        for k in closes:
            p_act, p_goal = tip(st[k])[0], tip(gi[k])[0]
            er = O.err_of(imgs[max(0, k - 3)]) if max(0, k - 3) in imgs else {}
            att.append(dict(frame=int(k), t=round(k / 30, 2), held=k in held, dq_act=(st[k, :5] - q_exp).tolist(), dq_goal=(gi[k] - q_exp).tolist(),
                            d_act=decomp(p_exp, p_act - p_exp).tolist(), d_goal=decomp(p_exp, p_goal - p_exp).tolist(),
                            d_exec=decomp(p_exp, p_act - p_goal).tolist(), **er))
        robot.append(dict(ep=ep, lab=O.LAB[ep], verdict=O.VER[ep], cube_xy=xy.tolist(), q_exp=q_exp.tolist(), tip_exp=p_exp.tolist(), attempts=att))
    out["robot"] = robot
    # 판 대표값 + 검정
    def rep(r, key, how):
        A = [a for a in r["attempts"] if not (isinstance(a.get("du"), float) and math.isnan(a["du"]))] or r["attempts"]
        if not A:
            return None
        if how == "first":
            A = A[:1]
        elif how == "closest":
            A = [min(A, key=lambda a: math.hypot(a.get("du", 9) if a.get("du") == a.get("du") else 9, a.get("dv", 9) if a.get("dv") == a.get("dv") else 9))]
        v = np.array([a[key] for a in A], float)
        return np.nanmedian(v, 0)

    tests = {}
    hsd = Rp_d.std(0)
    for how in ("median", "first", "closest"):
        t = {}
        for key in ("d_act", "d_goal", "d_exec"):
            V = np.array([rep(r, key, how) for r in robot])
            comp = {}
            for c, nm in enumerate(("out", "side", "up")):
                v = V[:, c]
                kpos = int(np.sum(v > 0))
                k = max(kpos, len(v) - kpos)
                comp[nm] = dict(per_trial=[round(float(x), 2) for x in v], median=float(np.median(v)), n_pos=kpos, n=len(v), sign_p=sign_p(k, len(v)),
                                median_over_human_sd=float(np.median(v) / hsd[c]))
            t[key] = comp
        W = {}
        for k in ("du", "dv", "size", "dangle"):
            v = np.array([rep(r, k, how) for r in robot], float)
            kpos = int(np.sum(v > (1 if k == "size" else 0)))
            W[k] = dict(per_trial=[round(float(x), 3) for x in v], median=float(np.nanmedian(v)), n_pos=kpos, sign_p=sign_p(max(kpos, len(v) - kpos), len(v)),
                        mwu_p_vs_human=mwu_p(v, [r[k] for r in H]))
        t["wrist"] = W
        tests[how] = t
    out["tests"] = tests
    # P3 오프라인 pre_close
    off = {}
    for tag in sorted(os.listdir(RAW)):
        for s in ("A", "B"):
            f = os.path.join(RAW, tag, f"{s}.npz")
            if not os.path.exists(f):
                continue
            z = np.load(f)
            m = z["phase"] == "pre_close"
            pred, hum, eps = z["pred"][m], z["human"][m], z["ep"][m]
            D_h, D_p, nclose = [], [], 0
            for i in range(len(pred)):
                g0 = hum[i, 0, 5]
                kh = int(np.argmax(hum[i, :, 5] < g0 - 8)) if np.any(hum[i, :, 5] < g0 - 8) else 10
                ph = tip(hum[i, kh])[0]
                pp = tip(pred[i, :, kh, :5]).mean(0)
                D_h.append(decomp(ph, pp - ph))
                ks = [int(np.argmax(pred[i, n, :, 5] < pred[i, n, 0, 5] - 8)) for n in range(pred.shape[1]) if np.any(pred[i, n, :, 5] < pred[i, n, 0, 5] - 8)]
                if ks:
                    nclose += 1
                    pk = np.mean([tip(pred[i, n, k, :5])[0] for n, k in zip(range(pred.shape[1]), ks)], 0)
                    D_p.append(decomp(ph, pk - ph))
                else:
                    D_p.append(np.full(3, np.nan))
            D_h, D_p = np.array(D_h), np.array(D_p)
            rng = np.random.default_rng(0)
            ue = np.unique(eps)

            def boot(D):
                bs = []
                for _ in range(2000):
                    pick = rng.choice(ue, len(ue))
                    idx = np.concatenate([np.where(eps == e_)[0] for e_ in pick])
                    bs.append(np.nanmean(D[idx], 0))
                bs = np.array(bs)
                return np.nanmean(D, 0).tolist(), np.percentile(bs, 2.5, 0).tolist(), np.percentile(bs, 97.5, 0).tolist()

            off[f"{tag}/{s}"] = dict(n=int(len(pred)), at_human_close=boot(D_h), at_pred_close=boot(D_p), n_pred_close=nclose,
                                     n_pos_at_human_close=(D_h > 0).sum(0).tolist())
    out["offline_pre_close"] = off
    json.dump(out, open(os.path.join(O.OUT, "bias.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print("B1_DONE")


if __name__ == "__main__":
    main()
