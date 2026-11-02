"""q02c 지시서 상태 유형별 보고 표 (CPU, q02b_state_metrics 만 읽음).
유형 (chunk 관측 시각 기준):
  T1 정상 접근      : zone under, 첫 닫힘 전, 손목 보임 · 테두리 · 본 적 없음 (S1 · S2 · dense under)
  T2 거의 정렬      : zone aligned (S3 · dense)
  T3 지나침 · 손목 봄 : zone over, 손목 보임 · 테두리 (dense A0, 첫 닫힘 전)
  T4 손목 놓침 · front 보임 : 손목 본 뒤 안 보임 + front 보임, zone over · undetermined (dense A0 · B1)
  T5 보정 방향 충돌  : 직전 0.5 s 실제 이동이 목표 반대 ≥ 2° (S6, zone under · over)
  T6 첫 닫힘 뒤 over (참고, U3)
각 유형 × 조건 (U · G · C · Cf): 판 · 상태 · seed 수 (분모), 비율 (%), 중앙값의 중앙.
첫 chunk (prefix 없음) 는 따로 (T1_first).
출력: tables/q02c_type_table.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q02c_report_table.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

TB = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off/tables"


def typ(r):
    if r.category == "S7_post_close_over" or (r.zone == "over" and not r.before_first_close):
        return "T6_post_close_over"
    if r.category == "S6_moving_away":
        return "T5_moving_away"
    if r.wstate == "wrist_lost_after_seen" and r.front_vis and r.zone in ("over", "undetermined"):
        return "T4_wrist_lost_front_vis"
    if r.zone == "over":
        return "T3_over_wrist_seen"
    if r.zone == "aligned":
        return "T2_near_aligned"
    if r.zone == "under" and r.before_first_close:
        return "T1_first_chunk" if not r.has_prefix else "T1_approach"
    return "other"


def main():
    M = pd.read_csv(TB / "q02b_state_metrics.csv")
    M["type"] = M.apply(typ, axis=1)
    rows = []
    for (t, c), g in M.groupby(["type", "cond"]):
        n = g.n_seeds.sum()
        r = dict(type=t, cond=c, n_eps=g.tag.nunique(), eps=",".join(sorted(g.tag.unique())), n_states=len(g), n_seeds_total=int(n))
        for k in ("first", "exec", "late", "cum30"):
            tot = g[[f"{k}_toward", f"{k}_away", f"{k}_hold"]].sum().sum()
            for d in ("toward", "away", "hold"):
                r[f"{k}_{d}_pct"] = 100 * g[f"{k}_{d}"].sum() / tot if tot else np.nan
        pv = g[["vsprior_continue", "vsprior_reverse", "vsprior_hold"]].sum().sum()
        for d in ("continue", "reverse", "hold"):
            r[f"vsprior_{d}_pct"] = 100 * g[f"vsprior_{d}"].sum() / pv if pv else np.nan
        r["vsprior_denominator"] = int(pv)
        r["late_only_pct"] = 100 * g.late_only.sum() / n if g.tdir.abs().sum() else np.nan
        for k in ("cum10_med", "cum20_med", "cum30_med", "exec_med", "late_med"):
            r[k + "_along_target"] = float(np.median(g[k] * np.where(g.tdir == 0, np.nan, g.tdir))) if g.tdir.abs().sum() else np.nan
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(TB / "q02c_type_table.csv", index=False)
    pd.set_option("display.width", 320, "display.max_columns", 50)
    print(D[D.cond.isin(["U", "G", "C", "Cf"])].round(1).drop(columns=["eps"]).to_string())


if __name__ == "__main__":
    main()
