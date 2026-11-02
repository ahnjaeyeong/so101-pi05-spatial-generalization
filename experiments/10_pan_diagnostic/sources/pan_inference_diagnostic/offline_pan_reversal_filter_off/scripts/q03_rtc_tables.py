"""q03 RTC 영향 분리 (CPU, q02 재추론 결과만 읽음). 로봇 연결 없음.

같은 상태 · 같은 noise seed (64) 짝: U (prefix 없음) vs G (기록 prefix · inference_delay, guided EXP).
prefix 가 있는 상태만 (판 첫 chunk 는 G = U 라 제외).
seed 마다:
  exec_U, exec_G = a29 − a9 (실행 구간 index 10–29), cum30 = a29 − s0
  toward_U / toward_G = 실행 구간 Δ 가 목표 쪽 ≥ 2° (zone under/over 만)
  짝 분류: both / U_only (RTC 가 목표 쪽 이동을 없앰) / G_only (RTC 가 만들어 냄) / neither
  first_toward_idx = 처음으로 a_k − s0 가 목표 쪽 ≥ 2° 가 되는 index (없으면 50) — U vs G 지연
  along = 처음 진행 방향 (판의 s_sign) 으로 잰 G − U 실행 구간 차 (+ = RTC 가 원래 진행 방향으로 더 감)
C (Arm Filter 끔) = G 의 index 10–29 그대로 → 방향은 G 와 같다 (clamp 미적용, q02b 참고). Cf (필터 켬 근사) 는 q02b_state_metrics.
출력: tables/q03_pairs.csv (상태별), q03_group.csv (묶음별, 분모 = 상태 × seed)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q03_rtc_tables.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off"
TB = OUT / "tables"
THR = 2.0


def first_idx(A, s0, tdir):
    m = (tdir * (A - s0)) >= THR
    return np.where(m.any(1), m.argmax(1), 50)


def main():
    S = pd.read_csv(TB / "q02_states.csv")
    Z = np.load(TB / "q02_seed_pan.npz")
    M = pd.read_csv(TB / "q02b_state_metrics.csv")
    cf = M[M.cond == "Cf"].set_index("key")
    rows = []
    for _, r in S[S.has_prefix].iterrows():
        U, G = Z[f"U_{r.key}"].astype(float), Z[f"G_{r.key}"].astype(float)
        eu, eg = U[:, 29] - U[:, 9], G[:, 29] - G[:, 9]
        row = dict(key=r.key, tag=r.tag, cond_filter=r.cond, category=r.category, zone=r.zone, wstate=r.wstate, t_s=r.t_s, s0=r.s0, tdir=int(r.tdir),
                   inference_delay=r.inference_delay, n=len(U), along_GminusU_med=float(np.median((eg - eu) * r.s_sign)),
                   absdiff_exec_med=float(np.median(np.abs(eg - eu))), absdiff_a29_med=float(np.median(np.abs(G[:, 29] - U[:, 29]))),
                   absdiff_a9_med=float(np.median(np.abs(G[:, 9] - U[:, 9]))), absdiff_a49_med=float(np.median(np.abs(G[:, 49] - U[:, 49]))))
        if r.tdir:
            tu, tg = r.tdir * eu >= THR, r.tdir * eg >= THR
            row.update(both=int((tu & tg).sum()), U_only=int((tu & ~tg).sum()), G_only=int((~tu & tg).sum()), neither=int((~tu & ~tg).sum()))
            fu, fg = first_idx(U, r.s0, r.tdir), first_idx(G, r.s0, r.tdir)
            ok = (fu < 50) & (fg < 50)
            row.update(first_toward_idx_U_med=float(np.median(fu)), first_toward_idx_G_med=float(np.median(fg)),
                       delay_G_minus_U_med=float(np.median(fg[ok] - fu[ok])) if ok.any() else np.nan,
                       U_toward_by29=int((fu <= 29).sum()), G_toward_by29=int((fg <= 29).sum()),
                       U_toward_by19=int((fu <= 19).sum()), G_toward_by19=int((fg <= 19).sum()))
            if r.key in cf.index:
                row["Cf_exec_toward"] = int(cf.loc[r.key].exec_toward)
        rows.append(row)
    P = pd.DataFrame(rows)
    P.to_csv(TB / "q03_pairs.csv", index=False)
    P["group"] = np.where(P.category == "dense_A0B1", "dense_" + P.tag, P.category)
    keys = ["group", "zone", "wstate"]
    agg = P.groupby(keys).agg(n_states=("key", "size"), n_eps=("tag", "nunique"), n_seed_pairs=("n", "sum"), both=("both", "sum"), U_only=("U_only", "sum"),
                              G_only=("G_only", "sum"), neither=("neither", "sum"), U_by29=("U_toward_by29", "sum"), G_by29=("G_toward_by29", "sum"),
                              U_by19=("U_toward_by19", "sum"), G_by19=("G_toward_by19", "sum"),
                              along_med=("along_GminusU_med", "median"), absdiff_exec_med=("absdiff_exec_med", "median"),
                              absdiff_a9=("absdiff_a9_med", "median"), absdiff_a29=("absdiff_a29_med", "median"), absdiff_a49=("absdiff_a49_med", "median")).reset_index()
    agg.to_csv(TB / "q03_group.csv", index=False)
    # inference_delay 0 vs 12
    d = P.groupby("inference_delay").agg(n_states=("key", "size"), absdiff_a9=("absdiff_a9_med", "median"), absdiff_a29=("absdiff_a29_med", "median"),
                                         absdiff_a49=("absdiff_a49_med", "median")).reset_index()
    d.to_csv(TB / "q03_by_delay.csv", index=False)
    pd.set_option("display.width", 300, "display.max_columns", 40)
    print(agg.round(2).to_string())
    print(d.round(2).to_string())


if __name__ == "__main__":
    main()
