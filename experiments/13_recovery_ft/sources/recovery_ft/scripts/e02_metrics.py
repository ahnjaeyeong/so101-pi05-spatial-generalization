"""e02 학습 전후 오프라인 지표 (CPU). 입력: eval/raw/<tag>/*.npz (e01). 로봇 연결 없음.

모든 값은 [재추론]: 저장 관측을 체크포인트에 다시 넣은 출력이다. 실물 성공률이 아니다. noise seed 는 실물 반복이 아니다 —
분모로 상태 수 · 판 수를 같이 적는다. 비교는 같은 상태 · 같은 noise 끼리 짝 (체크포인트만 다름).

R1 (q02 223 상태; 정의는 offline_pan_reversal_filter_off q02b · q02c 와 같음 — 그 함수를 import):
  first = a0 − s0, exec = a29 − a9 (실행 구간 근사), cum30 = a29 − s0, late = a49 − a29. 방향 문턱 2° (first 0.5°),
  toward = 목표대 중앙 쪽. 유형 typ(): T1 정상 접근 / T2 거의 정렬 / T3 지나침·손목 봄 / T4 손목 놓침·front 보임 / T5 / T6.
  T2 는 직전 0.5 s 이동 대비 continue / reverse / hold.
R2 · 정상 파지 (vd_b 168 실물 상태 + vd_h 96 사람 상태; 정의는 vd v06 과 같음):
  close_idx = r2_analyze.chunk_close_idx (state 그리퍼를 앞에 붙인 hysteresis), p_close30 = index ≤ 29 닫힘 계획 비율, p_close50,
  p_open30/50 = 관측 그리퍼 < 15 인 상태에서 계획 그리퍼가 ≥ 15 가 되는 비율, d{joint}29 = a29 − s (°).
사람 상태 (vd_h) 는 사람 action chunk (같은 프레임부터 50 개) 와도 비교: pan 방향 일치 (a29 − s0, 문턱 2°), 관절 L1 (index 0–29, 관절 0–4).
demo (새 세션 프레임): 사람 chunk 와 비교 (pan 방향 a49 − s0 · 그리퍼 열기/닫기 30 안 · L1). approved = [in-sample] (새 체크포인트),
  제외 편 = 학습 미사용 (같은 세션 · 작업자 — held-out 아님).
짝 차이 (ckpt − base) 의 95% CI: 판 (tag / ep) 단위 bootstrap 2000 회 (seed 0).
출력: eval/tables/e02_*.csv, eval/e02_summary.json
사용: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python scripts/e02_metrics.py --base d2_020000 --tags rft01_000250,rft01_000500,...
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
HOME = Path.home()
D2 = HOME / "so101_runs/main_k8/d2"
RF = D2 / "recovery_ft"
VD = D2 / "visual_dependency/vd_20261103_01"
OPR = D2 / "pan_inference_diagnostic/offline_pan_reversal_filter_off"
for p in (VD / "scripts", OPR / "scripts"):
    sys.path.insert(0, str(p))
import v_common as V  # noqa: E402
import r2_analyze as RA  # noqa: E402
import q02c_report_table as QC  # noqa: E402
import common as GB  # noqa: E402

THR = 2.0
OUT = RF / "eval/tables"


def dir3(d, tdir, thr=THR):
    d = np.asarray(d, float)
    return np.where(np.abs(d) < thr, "hold", np.where(np.sign(d) == tdir, "toward", "away"))


def close_idx(A, g0):
    return np.array([np.nan if (c := RA.chunk_close_idx(a[:, 5], g0)) is None else c for a in A], float)


def boot_diff(df, col_a, col_b, unit, n=2000, seed=0):
    """짝 차이 평균 (b − a) 과 단위 (판) bootstrap 95% CI."""
    d = (df[col_b] - df[col_a]).to_numpy(float)
    u = df[unit].to_numpy()
    ok = np.isfinite(d)
    d, u = d[ok], u[ok]
    if len(d) == 0:
        return np.nan, np.nan, np.nan, 0, 0
    units = np.unique(u)
    idx = {k: np.where(u == k)[0] for k in units}
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n):
        pick = rng.choice(units, len(units), replace=True)
        bs.append(np.concatenate([d[idx[k]] for k in pick]).mean())
    return float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), len(d), len(units)


# ---------------- R1 (q02) ----------------
def r1_state_rows(tag):
    S = pd.read_csv(RF / "eval/raw" / tag / "q02_states.csv")
    Z = np.load(RF / "eval/raw" / tag / "q02.npz")
    rows = []
    for r in S.itertuples():
        key = f"{r.tag}_c{int(r.chunk_id):05d}"
        tdir = int(r.tdir)
        typ = QC.typ(r)
        for src in ("U", "G"):
            A = Z[f"{src}_{key}"].astype(float)
            p = A[:, :, 0]
            s0 = float(r.s0)
            row = dict(tag=tag, key=key, ep=r.tag, type=typ, src=src, tdir=tdir, zone=r.zone, wstate=r.wstate, n_seed=len(A),
                       cum30_med=float(np.median(p[:, 29] - s0)), exec_med=float(np.median(p[:, 29] - p[:, 9])))
            if tdir != 0:
                fc = np.where(np.abs(p[:, 0] - s0) < 0.5, "hold", np.where(np.sign(p[:, 0] - s0) == tdir, "toward", "away"))
                for nm, arr in (("first", fc), ("exec", dir3(p[:, 29] - p[:, 9], tdir)), ("cum30", dir3(p[:, 29] - s0, tdir)), ("late", dir3(p[:, 49] - p[:, 29], tdir))):
                    for k in ("toward", "away", "hold"):
                        row[f"{nm}_{k}"] = float((arr == k).mean())
                row["exec_along"] = float(np.median((p[:, 29] - p[:, 9]) * tdir))
                row["cum30_along"] = float(np.median((p[:, 29] - s0) * tdir))
            pm = r.prior_move_0p5s
            if abs(pm) >= THR:
                c = p[:, 29] - s0
                row["continue"] = float(((np.abs(c) >= THR) & (np.sign(c) == np.sign(pm))).mean())
                row["reverse"] = float(((np.abs(c) >= THR) & (np.sign(c) != np.sign(pm))).mean())
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------- R2 · 정상 (vd_b, vd_h) ----------------
def r2_state_rows(tag, which):
    S = pd.read_csv(VD / f"tables/{'b' if which == 'vd_b' else 'h'}_states.csv")
    Z = np.load(RF / "eval/raw" / tag / f"{which}.npz")
    hum = GB.load_parquet(V.D2 / "dataset") if which == "vd_h" else None
    rows = []
    for r in S.itertuples():
        s = Z[f"S_{r.key}"].astype(float)
        for src in (("G", "U") if which == "vd_b" else ("G",)):
            A = Z[f"{src}_{r.key}"].astype(float)
            ci = close_idx(A, s[5])
            row = dict(tag=tag, key=r.key, src=src, group=getattr(r, "group", "human_d2"), role=r.role, ep=getattr(r, "tag", None) or f"H{r.ep:03d}",
                       w_cls=getattr(r, "w_cls", None), w_v=getattr(r, "w_v", np.nan), s_grip=s[5], n_seed=len(A),
                       p_close30=float((ci <= 29).mean()), p_close50=float(np.isfinite(ci).mean()),
                       close_idx_med=float(np.nanmedian(ci)) if np.isfinite(ci).any() else np.nan, grip_a29=float(np.median(A[:, 29, 5])))
            for jj, jn in enumerate(["pan", "lift", "elbow", "wflex", "wroll"]):
                row[f"d{jn}29"] = float(np.median(A[:, 29, jj] - s[jj]))
            if s[5] < 15:
                row["p_open30"] = float((A[:, :30, 5].max(axis=1) >= 15).mean())
                row["p_open50"] = float((A[:, :, 5].max(axis=1) >= 15).mean())
            if hum is not None:
                hs, ha = hum[int(r.ep)]
                ref = ha[int(r.frame):int(r.frame) + 50]
                if len(ref) == 50:
                    hd = ref[29, 0] - s[0]
                    row["h_pan29"] = float(hd)
                    if abs(hd) >= THR:
                        md = A[:, 29, 0] - s[0]
                        row["pan_dir_agree"] = float(((np.abs(md) >= THR) & (np.sign(md) == np.sign(hd))).mean())
                        row["pan_gain"] = float(np.median(md) / hd)
                    row["L1_arm_0_29"] = float(np.median(np.abs(A[:, :30, :5] - ref[None, :30, :5]).mean(axis=(1, 2))))
                    hc = RA.chunk_close_idx(ref[:, 5], s[5])
                    row["h_close30"] = float(hc is not None and hc <= 29)
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------- demo ----------------
def demo_rows(tag):
    S = pd.read_csv(RF / "eval/raw" / tag / "demo_states.csv")
    Z = np.load(RF / "eval/raw" / tag / "demo.npz")
    rows = []
    for r in S.itertuples():
        A = Z[f"G_{r.key}"].astype(float)
        ref = Z[f"REF_{r.key}"].astype(float)
        s = Z[f"S_{r.key}"].astype(float)
        ci = close_idx(A, s[5])
        hc = RA.chunk_close_idx(ref[:, 5], s[5])
        row = dict(tag=tag, key=r.key, group=r.group, scenario=r.scenario, approved=r.approved, role=r.role, ep=f"{r.group}e{r.src_ep}",
                   s_grip=s[5], n_seed=len(A), p_close30=float((ci <= 29).mean()), h_close30=float(hc is not None and hc <= 29),
                   L1_arm_0_49=float(np.median(np.abs(A[:, :, :5] - ref[None, :, :5]).mean(axis=(1, 2)))),
                   pan49_med=float(np.median(A[:, 49, 0] - s[0])), h_pan49=float(ref[49, 0] - s[0]))
        if abs(row["h_pan49"]) >= THR:
            md = A[:, 49, 0] - s[0]
            row["pan_dir_agree"] = float(((np.abs(md) >= THR) & (np.sign(md) == np.sign(row["h_pan49"]))).mean())
            row["pan_dir_opposite"] = float(((np.abs(md) >= THR) & (np.sign(md) != np.sign(row["h_pan49"]))).mean())
            row["pan_gain49"] = float(np.median(md) / row["h_pan49"])
        if s[5] < 15:
            row["p_open30"] = float((A[:, :30, 5].max(axis=1) >= 15).mean())
            row["h_open30"] = float(ref[:30, 5].max() >= 15)
        for jj, jn in enumerate(["lift", "elbow", "wflex"], start=1):
            row[f"d{jn}29"] = float(np.median(A[:, 29, jj] - s[jj]))
            row[f"h_d{jn}29"] = float(ref[29, jj] - s[jj])
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="d2_020000")
    ap.add_argument("--tags", required=True)
    a = ap.parse_args()
    tags = [a.base] + [t for t in a.tags.split(",") if t]
    OUT.mkdir(parents=True, exist_ok=True)
    have = {t: {p.stem for p in (RF / "eval/raw" / t).glob("*.npz")} for t in tags}
    R1 = pd.concat([r1_state_rows(t) for t in tags if "q02" in have[t]], ignore_index=True)
    B = pd.concat([r2_state_rows(t, "vd_b") for t in tags if "vd_b" in have[t]], ignore_index=True)
    H = pd.concat([r2_state_rows(t, "vd_h") for t in tags if "vd_h" in have[t]], ignore_index=True)
    Dm = pd.concat([demo_rows(t) for t in tags if "demo" in have[t]], ignore_index=True)
    for nm, df in (("r1_states", R1), ("r2_real_states", B), ("human_states", H), ("demo_states", Dm)):
        df.to_csv(OUT / f"e02_{nm}.csv", index=False)
    summ = {}
    # R1 유형표 (state 평균 비율 = seed 합 / (상태 × seed), q02c 와 같은 분모)
    t1 = []
    for (typ, src, tag), g in R1.groupby(["type", "src", "tag"]):
        r = dict(type=typ, src=src, tag=tag, n_eps=g.ep.nunique(), n_states=len(g))
        for m in ("first", "exec", "cum30", "late"):
            for k in ("toward", "away", "hold"):
                c = f"{m}_{k}"
                r[c] = 100 * g[c].mean() if c in g and g[c].notna().any() else np.nan
        for k in ("continue", "reverse"):
            r[k] = 100 * g[k].mean() if k in g and g[k].notna().any() else np.nan
        r["exec_along_med"] = g.exec_along.median() if "exec_along" in g else np.nan
        r["cum30_along_med"] = g.cum30_along.median() if "cum30_along" in g else np.nan
        t1.append(r)
    T1 = pd.DataFrame(t1)
    T1.to_csv(OUT / "e02_r1_type_table.csv", index=False)
    # 짝 차이 (각 tag − base)
    pair_rows = []

    def pair(df, keys, metric, unit, label, filt):
        P = df[filt(df)].pivot_table(index=keys, columns="tag", values=metric)
        P = P.reset_index()
        for t in tags[1:]:
            if t in P and a.base in P:
                m, lo, hi, n, nu = boot_diff(P, a.base, t, unit)
                pair_rows.append(dict(label=label, metric=metric, tag=t, base_mean=float(P[a.base].mean()), tag_mean=float(P[t].mean()),
                                      diff=m, ci_lo=lo, ci_hi=hi, n_states=n, n_units=nu))

    for src in ("U", "G"):
        for typ in ("T4_wrist_lost_front_vis", "T3_over_wrist_seen", "T1_first_chunk", "T1_approach", "T5_moving_away"):
            f = (lambda d, s=src, ty=typ: (d.src == s) & (d.type == ty) & (d.tdir != 0))
            for m in ("exec_toward", "exec_away", "cum30_toward", "first_toward"):
                pair(R1, ["key", "ep"], m, "ep", f"R1 {typ} {src}", f)
        f = (lambda d, s=src: (d.src == s) & (d.type == "T2_near_aligned"))
        for m in ("continue", "reverse"):
            pair(R1, ["key", "ep"], m, "ep", f"R1 T2_near_aligned {src}", f)
    for src in ("G", "U"):
        for grp in ("R2_AHEAD", "R2_BELOW", "normal_grasp", "R2_LATERAL"):
            for role_pat in ("R2_T0", "R2_reach", "R2_preT0", "R2_T2"):
                f = (lambda d, s=src, g_=grp, rp=role_pat: (d.src == s) & (d.group == g_) & d.role.str.contains(rp, regex=False))
                for m in ("p_close30", "p_close50", "dlift29", "delbow29", "dwflex29", "p_open30"):
                    pair(B, ["key", "ep"], m, "ep", f"R2 {grp} {role_pat} {src}", f)
        f = (lambda d, s=src: (d.src == s) & d.role.str.startswith("R1_init"))
        for m in ("p_close30", "dpan29"):
            pair(B, ["key", "ep"], m, "ep", f"R1_init(real first chunk) {src}", f)
    for role in ("H_init", "H_reach", "H_preclose"):
        f = (lambda d, r_=role: d.role == r_)
        for m in ("p_close30", "p_close50", "pan_dir_agree", "pan_gain", "L1_arm_0_29", "dpan29", "dlift29", "p_open30"):
            pair(H, ["key", "ep"], m, "ep", f"human {role}", f)
    for appr in (True, False):
        for grp in ("R1", "R2"):
            f = (lambda d, ap_=appr, g_=grp: (d.approved == ap_) & (d.group == g_))
            for m in ("pan_dir_agree", "pan_dir_opposite", "pan_gain49", "p_open30", "p_close30", "L1_arm_0_49"):
                pair(Dm, ["key", "ep"], m, "ep", f"demo {grp} {'approved(in-sample)' if appr else 'excluded(not trained)'}", f)
    PR = pd.DataFrame(pair_rows)
    PR.to_csv(OUT / "e02_paired_diffs.csv", index=False)
    summ["tags"] = tags
    summ["n"] = dict(r1_states=int(R1.key.nunique()), r2_real_states=int(B.key.nunique()), human_states=int(H.key.nunique()), demo_states=int(Dm.key.nunique()))
    (RF / "eval/e02_summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False))
    pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 30)
    print(T1[T1.type.isin(["T4_wrist_lost_front_vis", "T1_first_chunk", "T1_approach", "T3_over_wrist_seen"])][
        ["type", "src", "tag", "n_eps", "n_states", "exec_toward", "exec_away", "exec_hold", "cum30_toward", "first_toward"]].round(1).to_string())
    print(PR.round(3).to_string())


if __name__ == "__main__":
    main()
