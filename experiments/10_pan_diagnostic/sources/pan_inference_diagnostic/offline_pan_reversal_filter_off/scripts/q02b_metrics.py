"""q02b q02 재추론 결과의 Pan 방향 지표 (CPU). 로봇 연결 없음.

입력: tables/q02_states.csv, q02_seed_pan.npz (상태별 U · G pan (N, 50)), q01b_ticks.csv.gz (필터 켬 근사용 직전 out).
조건:
  U  = RTC prefix 없음 (모델 Raw)                                         [재구성 · 이후 chunk 에는 반사실]
  G  = 기록 prefix · inference_delay 로 RTC guided EXP                       [재구성]
  C  = Arm Filter 끔의 실행 예정 명령 = G 의 index 10–29 (실물 applied_delay 10 → 실행 구간) 그대로.
       lerobot max_relative_target 8° clamp (Present 기준) 는 오프라인에서 Present 를 몰라 적용하지 않음.
  Cf = 참고: Arm Filter 켬 근사 = G index 10–29 에 EMA α 0.5 (재설정 10°) + pan 속도 제한 2.4615°/틱 을 직전 기록 out 에서 시작해 적용 (filter 상태 근사).
지표 (pan °, s0 = 관측 state pan, 상태마다 seed N 개):
  first   = a0 − s0, 부호 (|·| < 0.5 → hold)
  cum10/20/30 = a9 / a19 / a29 − s0
  exec    = a29 − a9 (C 는 실행 구간 첫 값 → 끝 값, Cf 는 필터 출력 첫 → 끝)
  late    = a49 − a29 (실행 안 되는 30–49)
방향 (문턱 2°): tdir = 목표대 중앙 쪽 부호 (zone under/over 만, aligned · undetermined 은 n/a)
  toward / away / hold.  prior = 직전 0.5 s 실제 pan 이동 (|·| ≥ 2° 일 때만 부호).
  continue = cum30 부호 = prior 부호 (≥ 2°), reverse = 반대 (≥ 2°), hold = |cum30| < 2°.
  late_only = exec 가 toward 아님 (hold/away) 이고 late 는 toward.
출력: tables/q02b_state_metrics.csv (상태 × 조건, seed 비율), q02b_group.csv (범주 · zone · 손목 상태 · 조건 별 합계, 분모 명시)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q02b_metrics.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off"
TB = OUT / "tables"
THR = 2.0
VMAX = 2.4615383
ALPHA = 0.5


def cls(d, tdir):
    d = np.asarray(d, float)
    if tdir == 0:
        return np.full(d.shape, "n/a", dtype=object)
    out = np.where(np.abs(d) < THR, "hold", np.where(np.sign(d) == tdir, "toward", "away"))
    return out.astype(object)


def filt(seq, e0, y0):
    e, y, out = e0, y0, []
    for x in seq:
        e = x if abs(x - e) > 10 else ALPHA * x + (1 - ALPHA) * e
        y = y + float(np.clip(e - y, -VMAX, VMAX))
        out.append(y)
    return np.array(out)


def main():
    S = pd.read_csv(TB / "q02_states.csv")
    Z = np.load(TB / "q02_seed_pan.npz")
    T = pd.read_csv(TB / "q01b_ticks.csv.gz", usecols=["tag", "i", "pop_chunk", "pan_out"])
    rows = []
    for _, r in S.iterrows():
        tdir = int(r.tdir)
        prior = r.prior_move_0p5s
        psign = int(np.sign(prior)) if abs(prior) >= 2 else 0
        g = T[(T.tag == r.tag) & (T.pop_chunk == r.chunk_id)]
        prev = T[(T.tag == r.tag) & (T.i == (g.i.min() - 1 if len(g) else -5))]
        y0 = float(prev.pan_out.iloc[0]) if len(prev) else np.nan
        for cond in ("U", "G", "C", "Cf"):
            A = Z[f"{'U' if cond == 'U' else 'G'}_{r.key}"].astype(float)
            s0 = r.s0
            first, c10, c20, c30 = A[:, 0] - s0, A[:, 9] - s0, A[:, 19] - s0, A[:, 29] - s0
            late = A[:, 49] - A[:, 29]
            if cond == "U" or cond == "G":
                ex = A[:, 29] - A[:, 9]
            elif cond == "C":
                ex = A[:, 29] - A[:, 10]
            else:
                if not np.isfinite(y0):
                    continue
                F = np.array([filt(a[10:30], y0, y0) for a in A])
                ex = F[:, -1] - F[:, 0]
            if cond in ("C", "Cf") and not r.has_prefix:
                pass
            fc = np.where(np.abs(first) < 0.5, "hold", np.where(np.sign(first) == tdir, "toward", "away")) if tdir else np.full(len(first), "n/a")
            ce, cl, c3 = cls(ex, tdir), cls(late, tdir), cls(c30, tdir)
            if psign:
                rev = np.where(np.abs(c30) < THR, "hold", np.where(np.sign(c30) == psign, "continue", "reverse"))
            else:
                rev = np.full(len(c30), "n/a")
            n = len(A)
            row = dict(key=r.key, tag=r.tag, cond_filter=r.cond, chunk_id=r.chunk_id, t_s=r.t_s, category=r.category, zone=r.zone, wstate=r.wstate,
                       front_vis=r.front_vis, has_prefix=r.has_prefix, first_in_ep=r.first_in_ep, inference_delay=r.inference_delay, tdir=tdir, prior=prior, psign=psign,
                       before_first_close=r.before_first_close, s0=r.s0, err_to_mid=r.err_to_band_mid, cond=cond, n_seeds=n,
                       cum10_med=float(np.median(c10)), cum20_med=float(np.median(c20)), cum30_med=float(np.median(c30)), exec_med=float(np.median(ex)),
                       late_med=float(np.median(late)), cum30_p10=float(np.percentile(c30, 10)), cum30_p90=float(np.percentile(c30, 90)))
            for nm, arr in (("first", fc), ("exec", ce), ("late", cl), ("cum30", c3)):
                for k in ("toward", "away", "hold"):
                    row[f"{nm}_{k}"] = int((arr == k).sum())
            for k in ("continue", "reverse", "hold"):
                row[f"vsprior_{k}"] = int((rev == k).sum())
            row["late_only"] = int(((ce != "toward") & (cl == "toward") & (ce != "n/a")).sum())
            rows.append(row)
    M = pd.DataFrame(rows)
    M.to_csv(TB / "q02b_state_metrics.csv", index=False)
    # 묶음 합계 (분모 = 상태 수 × seed 수)
    M["group"] = np.where(M.category == "dense_A0B1", "dense_" + M.tag, M.category)
    keys = ["group", "zone", "wstate", "has_prefix", "cond"]
    sumcols = [c for c in M.columns if any(c.startswith(p) for p in ("first_", "exec_", "late_", "cum30_", "vsprior_")) and not c.endswith(("_med", "_p10", "_p90"))] + ["late_only", "n_seeds"]
    Gp = M.groupby(keys)[sumcols].sum().reset_index()
    Gp["n_states"] = M.groupby(keys).size().values
    Gp["n_eps"] = M.groupby(keys).tag.nunique().values
    Gp["cum30_med_of_state_meds"] = M.groupby(keys).cum30_med.median().values
    Gp.to_csv(TB / "q02b_group.csv", index=False)
    pd.set_option("display.width", 300, "display.max_columns", 50, "display.max_rows", 300)
    show = Gp[Gp.cond.isin(["U", "G"])][["group", "zone", "wstate", "has_prefix", "cond", "n_eps", "n_states", "n_seeds", "exec_toward", "exec_away", "exec_hold",
                                          "late_toward", "late_only", "vsprior_continue", "vsprior_reverse", "vsprior_hold", "cum30_med_of_state_meds"]]
    print(show.to_string())


if __name__ == "__main__":
    main()
