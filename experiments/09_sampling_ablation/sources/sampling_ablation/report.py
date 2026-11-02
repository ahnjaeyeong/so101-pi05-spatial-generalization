"""eval/<run>_<step>/ 결과 → eval/결과표.md · eval/report.json (사실 · 측정값만; 판정 규칙은 실험설계.md 8 절 v2 를 그대로 적용).

O1 (초기 접근, 주 지표 — 오프라인 대리값):
  pre_err   닫힘 1 s 전 관측 → chunk idx 30 pan 과 사람 닫힘 pan 의 |차| (학습 판, in-sample), K / R
  start_err 움직임 시작 관측 → chunk 끝 (idx 49) pan 과 사람 닫힘 pan 의 |차| (in-sample, chunk 가 닫힘까지 못 감)
  grid      front 합성 격자 (1.5 cm) + U1–U8 시작 관측 → chunk 끝 pan, 보정 (학습 Random 판으로 맞춘 p0 · k±, diag exp1 와 같음) 뒤
            기대 pan (−bearing − 1.4°) 과의 |차|. 새 위치 = 최근접 학습 큐브 ≥ 2 cm. K 당김 aK (diag exp1 회귀).
O2 (roll 조건부): G1 w_rot (닫힘 1.0 · 1.5 s), G_tt · G_rr (닫힘 1.0 s), S1 정책/사람 기울기 비, S6 평가 롤아웃 프레임 기울기.
O3: 칸 등급별 in-sample flow loss.
비교: 판 (O1 학습 판 · O2 G1 판) 또는 격자 점 짝 bootstrap 2000 회, 95 % CI. δ = |A0′ − A0|.
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python report.py
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SA = Path(__file__).resolve().parent
D2 = SA.parent
sys.path.insert(0, str(D2 / "action_bottleneck"))
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
sys.path.insert(0, str(SA))
import common as C  # noqa: E402

EV = Path(os.environ.get("SA_EVAL_DIR", SA / "eval"))   # 시험용으로만 바꿈
NB = 2000
RNG = np.random.default_rng(0)
K = C.load_known()
KPAN = {k: C.pan_expected(*v) for k, v in K.items()}
D = (-30.0, -15.0, 15.0, 30.0)
RUNS = ["d2", "A0_s2001", "A1_s2001", "A2_s2001", "A2r_s2001", "A0_s2002"]
COMPARE = [("A1_s2001", "A0_s2001", "A1 − A0 (접근 · 정렬 표집)"),
           ("A2r_s2001", "A0_s2001", "A2r − A0 (Random 비중)"),
           ("A2_s2001", "A2r_s2001", "A2 − A2r (희소 roll×접선 칸 가중의 추가 효과)"),
           ("A2_s2001", "A0_s2001", "A2 − A0 (Random + 칸, 합)"),
           ("A0_s2002", "A0_s2001", "A0′ − A0 (seed 변동)")]
D2CMP = [(r, "d2", f"{r} − d2 (추가 4k step 효과 포함)") for r in RUNS[1:]]


def edir(run, step="004000"):
    return EV / f"{run}_{'020000' if run == 'd2' else step}"


def nearest_k(x, y):
    return min(K, key=lambda k: math.hypot(x - K[k][0], y - K[k][1]))


def ols(y, cols):
    X = np.column_stack([np.ones(len(y))] + list(cols))
    return np.linalg.lstsq(X, y, rcond=None)[0]


# ---------------- O1 ----------------
def o1_table(run, step="004000"):
    d = edir(run, step)
    if not (d / "o1.npz").exists():
        return None
    Z = np.load(d / "o1.npz")
    T = pd.read_csv(D2 / "diag_grasp_bias/grasp_train.csv")
    hp = T.s_shoulder_pan.values
    st = Z["start"].mean(0)                          # 256 × 50 × 6 (noise 평균)
    pr = Z["pregrasp"].mean(0)
    gr = Z["grid"].mean(0)
    R = (T["mode"] == "R").values
    ep = pd.DataFrame(dict(ep=np.arange(256), mode=T["mode"], start_err=np.abs(st[:, 49, 0] - hp), pre_err=np.abs(pr[:, 30, 0] - hp)))
    # 보정 (diag exp1 calib_fit): pred − p0 = k± (human − p0), 학습 Random 판
    p0 = float(np.median(st[:, 0, 0]))
    k = {}
    for sg in (1, -1):
        m = R & (np.sign(hp - p0) == sg)
        h, p = hp[m] - p0, st[m, 49, 0] - p0
        k[sg] = float((h * p).sum() / (h * h).sum())
    G = pd.read_csv(d / "o1_points.csv")
    G["pan_exp"] = [C.pan_expected(x, y) for x, y in zip(G.x, G.y)]
    G["pred"] = gr[:, 49, 0]
    dd = G.pan_exp - p0
    G["pred_cal_target"] = p0 + np.where(dd >= 0, k[1], k[-1]) * dd
    G["err_raw"] = G.pred - G.pan_exp
    G["err_cal"] = G.pred - G.pred_cal_target
    G["abs_cal"] = G.err_cal.abs()
    G["nK"] = [nearest_k(x, y) for x, y in zip(G.x, G.y)]
    G["K_pan"] = G.nK.map(KPAN)
    G["usable"] = usable_mask(G, T)
    # 새 위치 (주): U1–U8 + 격자 중 최근접 학습 큐브 ≥ 2 cm 이고 학습 위치 볼록 껍질 안 · 어려운 영역 밖 · 화면 끝 아래 (U 와 같은 기준)
    G["novel"] = (G.kind != "grid") | ((G.d_train >= 2.0) & G.usable)
    G["edge"] = (G.kind == "grid") & (G.d_train >= 2.0) & ~G.usable      # 껍질 밖 · 어려운 영역 (외삽, 따로 표시)
    return dict(ep=ep, G=G, p0=p0, k=k)


def usable_mask(G, T):
    """s1_design_numbers.untrained_candidates 와 같은 조건 (학습 큐브 256 개 볼록 껍질 안, 어려운 영역 밖, front y ≥ MIN_Y_PX + 10)."""
    from scipy.spatial import ConvexHull
    import cube_angle as ca
    import s1_design_numbers as S1
    xy = T[["cube_x", "cube_y"]].values
    P = G[["x", "y"]].values
    hull = S1.MPath(xy[ConvexHull(xy).vertices]).contains_points(P)
    hz = np.zeros(len(P), bool)
    for z in C.CFG["workspace"].get("hard_zones_cm", []):
        hz |= S1.MPath(np.array(z["polygon"])).contains_points(P)
    vpx = np.array([C.cm_to_px(x, y)[1] for x, y in P])
    return hull & ~hz & (vpx >= ca.MIN_Y_PX + 10)


def o1_metrics(t):
    ep, G = t["ep"], t["G"]
    nov = G[G.novel]
    near = G[G.d_train < 1.0]
    ind = G[G.d_train <= 3]
    aK = ols(ind.err_cal.values, [(ind.K_pan - ind.pan_exp).values, (0 - ind.pan_exp).values])
    return dict(pre_err_R=float(ep[ep["mode"] == "R"].pre_err.median()), pre_err_K=float(ep[ep["mode"] == "K"].pre_err.median()),
                start_err_R=float(ep[ep["mode"] == "R"].start_err.median()),
                grid_novel_abs_cal_mean=float(nov.abs_cal.mean()), grid_novel_n=len(nov),
                grid_U_abs_cal_mean=float(G[G.kind != "grid"].abs_cal.mean()),
                grid_edge_abs_cal_mean=float(G[G.edge].abs_cal.mean()), grid_edge_n=int(G.edge.sum()),
                grid_near_abs_cal_mean=float(near.abs_cal.mean()), grid_all_abs_cal_mean=float(G.abs_cal.mean()),
                grid_aK=float(aK[1]), grid_cC=float(aK[2]), calib_k_pos=t["k"][1], calib_k_neg=t["k"][-1])


def o1_diff(tx, ty):
    """짝 비교: 새 위치 격자 점 |err_cal| 평균 차 (점 bootstrap), 학습 R 판 pre_err 중앙값 차 (판 bootstrap), aK 차."""
    Gx, Gy = tx["G"], ty["G"]
    RNG = np.random.default_rng(0)  # 비교마다 같은 seed — CI 가 다른 비교 수 · 순서에 따라 바뀌지 않게
    assert len(Gx) == len(Gy)
    nov = Gx.novel.values
    dx = Gx.abs_cal.values[nov] - Gy.abs_cal.values[nov]
    bs = [dx[RNG.integers(0, len(dx), len(dx))].mean() for _ in range(NB)]
    ex, ey = tx["ep"], ty["ep"]
    Rm = (ex["mode"] == "R").values
    px, py = ex.pre_err.values[Rm], ey.pre_err.values[Rm]
    bp = []
    for _ in range(NB):
        i = RNG.integers(0, len(px), len(px))
        bp.append(np.median(px[i]) - np.median(py[i]))
    ind = (Gx.d_train <= 3).values
    ba = []
    for _ in range(NB):
        i = np.flatnonzero(ind)[RNG.integers(0, ind.sum(), ind.sum())]
        a = [ols(g.err_cal.values[i], [(g.K_pan - g.pan_exp).values[i], (0 - g.pan_exp).values[i]])[1] for g in (Gx, Gy)]
        ba.append(a[0] - a[1])
    aK = [ols(g[g.d_train <= 3].err_cal.values, [(g[g.d_train <= 3].K_pan - g[g.d_train <= 3].pan_exp).values,
                                                    (0 - g[g.d_train <= 3].pan_exp).values])[1] for g in (Gx, Gy)]
    return dict(grid_novel_abs_cal=dict(est=float(dx.mean()), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], n=int(nov.sum())),
                pre_err_R=dict(est=float(np.median(px) - np.median(py)), ci=[float(np.percentile(bp, 2.5)), float(np.percentile(bp, 97.5))]),
                grid_aK=dict(est=float(aK[0] - aK[1]), ci=[float(np.percentile(ba, 2.5)), float(np.percentile(ba, 97.5))]))


# ---------------- O2 ----------------
def g1_frames(run):
    p = edir(run) / "a1_g1_frames.csv"
    return pd.read_csv(p) if p.exists() else None


def w_rot(dd):
    num = sum((dd[f"psi_{d:+.0f}"] * dd[f"psi_ideal_{d:+.0f}"]).sum() for d in D if f"psi_{d:+.0f}" in dd)
    den = sum((dd[f"psi_ideal_{d:+.0f}"] ** 2).where(dd[f"psi_{d:+.0f}"].notna()).sum() for d in D if f"psi_{d:+.0f}" in dd)
    return num / den if den else np.nan


def o2_metrics(F, s1s6):
    out = {}
    for ph in ("t1.0", "t1.5", "t2.5"):
        Fp = F[F.phase == ph]
        out[f"w_rot_{ph}"] = float(w_rot(Fp[Fp.R0_norm >= 0.1]))
        out[f"G_tt_{ph}"] = float(Fp.G_tt.median())
        out[f"G_rr_{ph}"] = float(Fp.G_rr.median())
    out["w_rot_t1.0_t1.5"] = (out["w_rot_t1.0"] + out["w_rot_t1.5"]) / 2
    if s1s6:
        for k in ("0-1s", "1-2s", "2-3s"):
            r = s1s6.get(f"S1_{k}")
            if r:
                out[f"S1_ratio_{k}"] = r["pol_tan_slope"] / r["hum_a_tan_slope"] if r["hum_a_tan_slope"] else None
        s6 = s1s6.get("S6_eval", {})
        if "in_range" in s6:
            out["S6_in_range_slope"] = s6["in_range"]["pol_tan_slope"]
    return out


def o2_diff(Fx, Fy):
    key = ["ep", "phase"]
    RNG = np.random.default_rng(0)
    M = Fx.merge(Fy, on=key, suffixes=("_x", "_y"))
    eps = M.ep.unique()
    g = {e: d for e, d in M.groupby("ep")}

    def wr(d, s):
        cols = {c[:-2]: d[c] for c in d.columns if c.endswith(s)}
        df = pd.DataFrame(cols).assign(phase=d.phase.values)
        df = df[df.R0_norm >= 0.1]
        return np.mean([w_rot(df[df.phase == ph]) for ph in ("t1.0", "t1.5")])

    def stat(d):
        t1 = d[d.phase == "t1.0"]
        return np.array([wr(d, "_x") - wr(d, "_y"), t1.G_tt_x.median() - t1.G_tt_y.median(), t1.G_rr_x.median() - t1.G_rr_y.median()])
    est = stat(M)
    bs = np.array([stat(pd.concat([g[e] for e in RNG.choice(eps, len(eps))])) for _ in range(NB // 4)])
    names = ["w_rot_t1.0_t1.5", "G_tt_t1.0", "G_rr_t1.0"]
    return {n: dict(est=float(est[i]), ci=[float(np.nanpercentile(bs[:, i], 2.5)), float(np.nanpercentile(bs[:, i], 97.5))])
            for i, n in enumerate(names)}


# ---------------- O3 ----------------
def o3(run, step="004000"):
    p = edir(run, step) / "o3_loss.csv"
    return pd.read_csv(p) if p.exists() else None


def o3_diff(Lx, Ly):
    M = Lx.merge(Ly[["index", "loss"]], on="index", suffixes=("_x", "_y"))
    r = {}
    for t, d in M.groupby("tier"):
        r[t] = dict(n=len(d), x=float(d.loss_x.mean()), y=float(d.loss_y.mean()), rel_change=float(d.loss_x.mean() / d.loss_y.mean() - 1))
    drop = {t: -v["rel_change"] for t, v in r.items()}
    r["memorization_ratio_rare_over_common"] = float(drop["희소"] / drop["보통"]) if drop.get("보통") and drop["보통"] > 0 else None
    return r


# ---------------- 판정 ----------------
def judge(name, dO1, dO2, dO3, delta):
    """실험설계.md v2 8.2 · 8.3 (오프라인 부분만; O1-H · 로봇 은 보류)."""
    if dO1 is None or dO2 is None:
        return None
    dl = delta or {}

    def thr(m, base):
        return max(base, 2 * abs(dl.get(m, 0.0))) if delta else base
    g = dO1["grid_novel_abs_cal"]
    o1 = (g["est"] <= -thr("grid_novel_abs_cal", 1.5) and g["ci"][1] < 0) and dO1["grid_aK"]["est"] <= 0.0 + (
        2 * abs(dl.get("grid_aK", 0.0)) if delta else 0.0)
    w, gt = dO2["w_rot_t1.0_t1.5"], dO2["G_tt_t1.0"]
    o2 = (w["est"] >= thr("w_rot_t1.0_t1.5", 0.2) and w["ci"][0] > 0) and (gt["est"] >= thr("G_tt_t1.0", 0.05) and gt["ci"][0] > 0)
    worse = dO2["G_rr_t1.0"]["est"] < -0.05 or (dO3 and dO3.get("보통", {}).get("rel_change", 0) > 0.05)
    mem = dO3 and (dO3.get("memorization_ratio_rare_over_common") or 0) >= 2
    cell = {(True, True): "둘 다", (True, False): "O1 만", (False, True): "O2 만", (False, False): "없음"}[(bool(o1), bool(o2))]
    return dict(O1_offline=bool(o1), O2=bool(o2), cell=cell, worsening=bool(worse), memorization_flag=bool(mem),
                delta_available=bool(delta), note="O1 은 합성 격자 (새 위치 ≥ 2 cm) 대리값 — O1-H (held-out) · 로봇 평가는 보류")


def main():
    T1 = {r: o1_table(r) for r in RUNS}
    F = {r: g1_frames(r) for r in RUNS}
    S = {r: (json.load(open(edir(r) / "s1s6.json")) if (edir(r) / "s1s6.json").exists() else None) for r in RUNS}
    L = {r: o3(r) for r in RUNS}
    rep = dict(runs={}, compare={}, d2_compare={}, stability_2000={})
    for r in RUNS:
        m = {}
        if T1[r]:
            m["O1"] = o1_metrics(T1[r])
        if F[r] is not None:
            m["O2"] = o2_metrics(F[r], S[r])
        if L[r] is not None:
            m["O3_loss_by_tier"] = L[r].groupby("tier").loss.mean().round(5).to_dict()
        rep["runs"][r] = m
    delta = None
    if T1.get("A0_s2002") and T1.get("A0_s2001") and F.get("A0_s2002") is not None and F.get("A0_s2001") is not None:
        d1 = o1_diff(T1["A0_s2002"], T1["A0_s2001"])
        d2_ = o2_diff(F["A0_s2002"], F["A0_s2001"])
        delta = {"grid_novel_abs_cal": d1["grid_novel_abs_cal"]["est"], "grid_aK": d1["grid_aK"]["est"],
                 "w_rot_t1.0_t1.5": d2_["w_rot_t1.0_t1.5"]["est"], "G_tt_t1.0": d2_["G_tt_t1.0"]["est"]}
    rep["delta_seed"] = delta
    for x, y, nm in COMPARE + D2CMP:
        if T1.get(x) is None or T1.get(y) is None or F.get(x) is None or F.get(y) is None:
            continue
        dO1, dO2 = o1_diff(T1[x], T1[y]), o2_diff(F[x], F[y])
        dO3 = o3_diff(L[x], L[y]) if L.get(x) is not None and L.get(y) is not None else None
        tgt = rep["d2_compare"] if y == "d2" else rep["compare"]
        tgt[nm] = dict(O1=dO1, O2=dO2, O3=dO3, judge=judge(nm, dO1, dO2, dO3, delta if "seed" not in nm else None))
    for r in RUNS[1:]:
        t2, t4 = o1_table(r, "002000"), T1.get(r)
        l2, l4 = o3(r, "002000"), L.get(r)
        if t2 and t4:
            rep["stability_2000"][r] = dict(O1_2000=o1_metrics(t2), O1_4000=o1_metrics(t4),
                                            O3_2000=l2.groupby("tier").loss.mean().round(5).to_dict() if l2 is not None else None,
                                            O3_4000=l4.groupby("tier").loss.mean().round(5).to_dict() if l4 is not None else None)
    json.dump(rep, open(EV / "report.json", "w"), indent=1, ensure_ascii=False, default=float)
    write_md(rep)
    print(json.dumps({k: (v.get("judge") if isinstance(v, dict) else v) for k, v in rep["compare"].items()}, ensure_ascii=False, indent=1))


def f(x, n=3):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def write_md(rep):
    L = ["# d2 sampling ablation — 오프라인 결과표 (자동 생성: report.py)", "",
         "- 모든 정책은 d2 020000 에서 같은 조건 (새 FT, LR 1e-5, 4000 step, bs 32) 으로 학습. 최종 비교 = 4000 step. 2000 step 은 안정성 점검용.",
         "- **held-out 아님**: O1 의 학습 판 지표 · O2 G1 · O3 는 d2 256 판 (모든 정책이 학습한 데이터) 기준. 격자 '새 위치' 는 front 합성 영상 (최근접 학습 큐브 ≥ 2 cm).",
         "- d2 대비 차이에는 추가 4k step 학습 자체의 효과가 섞여 있다. 표본 효과 비교는 A0 기준.",
         "- O1-H (H 사람 시연) · 로봇 평가는 아직 없음 (보류).", ""]
    L += ["## 1. 실험별 값", "", "| 지표 | " + " | ".join(RUNS) + " |", "|---|" + "---|" * len(RUNS)]
    rows = [("O1 닫힘 1 s 전 pan 절대 오차 중앙 (R 판, °)", "O1", "pre_err_R"), ("O1 같은 값 (K 판, °)", "O1", "pre_err_K"),
            ("O1 시작 관측 pan 절대 오차 중앙 (R 판, °)", "O1", "start_err_R"),
            ("O1 새 위치 (U1–U8 + 격자 ≥2 cm, 껍질 안) 보정 절대 오차 평균 (°)", "O1", "grid_novel_abs_cal_mean"), ("O1 새 위치 점 수", "O1", "grid_novel_n"), ("O1 U1–U8 보정 절대 오차 평균 (°)", "O1", "grid_U_abs_cal_mean"),
            ("O1 격자 학습 근처 (<1 cm) (°)", "O1", "grid_near_abs_cal_mean"), ("O1 격자 가장자리 · 어려운 영역 ≥2 cm (외삽, °)", "O1", "grid_edge_abs_cal_mean"), ("O1 K 당김 aK", "O1", "grid_aK"),
            ("O2 w_rot 닫힘 1.0·1.5 s 평균", "O2", "w_rot_t1.0_t1.5"), ("O2 w_rot 1.0 s", "O2", "w_rot_t1.0"), ("O2 w_rot 1.5 s", "O2", "w_rot_t1.5"),
            ("O2 G_tt 1.0 s", "O2", "G_tt_t1.0"), ("O2 G_rr 1.0 s", "O2", "G_rr_t1.0"), ("O2 G_tt 1.5 s", "O2", "G_tt_t1.5"),
            ("O2 S1 정책/사람 접선 기울기 비 0–1 s", "O2", "S1_ratio_0-1s"), ("O2 S1 비 1–2 s", "O2", "S1_ratio_1-2s"),
            ("O2 S6 평가 프레임 (범위 안) 기울기", "O2", "S6_in_range_slope")]
    for nm, grp, k in rows:
        L.append(f"| {nm} | " + " | ".join(f(rep["runs"].get(r, {}).get(grp, {}).get(k)) for r in RUNS) + " |")
    tiers = ["희소", "얇음", "보통", "정렬_칸없음", "접근", "닫힘 뒤", "정지"]
    for t in tiers:
        L.append(f"| O3 loss {t} | " + " | ".join(f(rep["runs"].get(r, {}).get("O3_loss_by_tier", {}).get(t), 5) for r in RUNS) + " |")
    L += ["", f"seed 변동 δ (A0′ − A0): {json.dumps(rep.get('delta_seed'), ensure_ascii=False)}", ""]
    for title, key in (("2. 비교 (표본 효과)", "compare"), ("3. d2 대비 (추가 학습 효과 포함)", "d2_compare")):
        L += [f"## {title}", "", "| 비교 | O1 새 위치 절대 오차 차 [CI] | O1 R 판 pre 차 [CI] | O1 aK 차 [CI] | O2 w_rot 차 [CI] | O2 G_tt 1.0 차 [CI] | O2 G_rr 1.0 차 [CI] | O3 희소/보통 loss 변화 | 판정 칸 (O1 · O2) |",
              "|---|---|---|---|---|---|---|---|---|"]
        for nm, v in rep[key].items():
            o1, o2, o3_, j = v["O1"], v["O2"], v["O3"] or {}, v["judge"] or {}
            ci = lambda d: f"{d['est']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]"  # noqa: E731
            L.append(f"| {nm} | {ci(o1['grid_novel_abs_cal'])} (n {o1['grid_novel_abs_cal']['n']}) | {ci(o1['pre_err_R'])} | {ci(o1['grid_aK'])} | "
                     f"{ci(o2['w_rot_t1.0_t1.5'])} | {ci(o2['G_tt_t1.0'])} | {ci(o2['G_rr_t1.0'])} | "
                     f"{f(o3_.get('희소', {}).get('rel_change'))} / {f(o3_.get('보통', {}).get('rel_change'))} | "
                     f"{j.get('cell', '—')}{' · 악화' if j.get('worsening') else ''}{' · 외움 의심' if j.get('memorization_flag') else ''}{'' if j.get('delta_available', True) else ' · δ 없음'} |")
        L.append("")
    if rep["stability_2000"]:
        L += ["## 4. 2000 step (안정성 점검용 — 판정에 쓰지 않음)", "", "| 실험 | O1 새 위치 2000 / 4000 | O1 pre R 2000 / 4000 | O3 보통 loss 2000 / 4000 |", "|---|---|---|---|"]
        for r, v in rep["stability_2000"].items():
            L.append(f"| {r} | {f(v['O1_2000']['grid_novel_abs_cal_mean'])} / {f(v['O1_4000']['grid_novel_abs_cal_mean'])} | "
                     f"{f(v['O1_2000']['pre_err_R'])} / {f(v['O1_4000']['pre_err_R'])} | "
                     f"{f((v['O3_2000'] or {}).get('보통'), 5)} / {f((v['O3_4000'] or {}).get('보통'), 5)} |")
    (EV / "결과표.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
