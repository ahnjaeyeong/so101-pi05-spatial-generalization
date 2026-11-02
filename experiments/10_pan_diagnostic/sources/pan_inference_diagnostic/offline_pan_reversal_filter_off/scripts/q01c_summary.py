"""q01c 분석 A 요약 표 (CPU, q01b 표만 읽음).
출력: tables/q01c_episode_summary.csv (판별 구간 · 반전), q01c_A0B1_phase_chunks.csv (A0 · B1 구간별 chunk 방향 수), q01c_A0B1_chunks.csv (A0 · B1 chunk 목록)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q01c_summary.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off"
TB = OUT / "tables"


def main():
    E = pd.read_csv(TB / "q01b_episodes.csv")
    T = pd.read_csv(TB / "q01b_ticks.csv.gz")
    Ch = pd.read_csv(TB / "q01b_chunks.csv")
    TP = pd.read_csv(TB / "q01b_turnpoints.csv")
    rows = []
    for _, e in E.iterrows():
        g = T[T.tag == e.tag]
        fc = int(e.first_close_i) if np.isfinite(e.first_close_i) else len(g)
        pre = g[g.i < fc]
        zc = pre.zone.value_counts()
        tp = TP[(TP.tag == e.tag) & (TP.i < fc)]
        # 의미 있는 되돌림: 전환 뒤 목표 쪽으로 간 양 (다음 전환점 또는 첫 닫힘까지)
        amps = []
        for _, t in tp.iterrows():
            nxt = tp[tp.i > t.i]
            j = int(nxt.i.iloc[0]) if len(nxt) else fc - 1
            seg = g[(g.i >= t.i) & (g.i <= j)].pan_present.values
            amps.append(float(np.max(np.abs(seg - t.pan))) if len(seg) else np.nan)
        rows.append(dict(tag=e.tag, cond=e["cond"], label=e.label, verdict=e.verdict, band=f"{e.bandf_lo:.1f} … {e.bandf_hi:.1f}", bandf_src=e.bandf_src,
                         start_pan=e.start_pan, first_close_s=fc / 30 if fc < len(g) else np.nan, pre_ticks=len(pre),
                         under_s=zc.get("under", 0) / 30, aligned_s=zc.get("aligned", 0) / 30, undet_s=zc.get("undetermined", 0) / 30, over_s=zc.get("over", 0) / 30,
                         max_past_far_edge=e.max_past_far_edge, first_over_s=e.first_over_i / 30 if np.isfinite(e.first_over_i) else np.nan,
                         wrist_lost_s=e.first_wrist_lost_i / 30 if np.isfinite(e.first_wrist_lost_i) else np.nan,
                         n_turn=len(tp), n_turn_in_over=int((tp.zone == "over").sum()),
                         turn_list="; ".join(f"{t.t_s:.1f}s {t.pan:.1f}° {t.zone} {'away→' if t.away_before else 'toward→'} {a:.1f}°" for (_, t), a in zip(tp.iterrows(), amps))))
    S = pd.DataFrame(rows)
    S.to_csv(TB / "q01c_episode_summary.csv", index=False)
    # A0 · B1 구간
    C = Ch[Ch.tag.isin(["A0", "B1"])].copy()
    Eb = E.set_index("tag")

    def phase(r):
        e = Eb.loc[r.tag]
        fa = T[(T.tag == r.tag) & (T.zone == "aligned")].i.min() / 30
        lim = T[(T.tag == r.tag) & (T.pan_present <= -105)].i.min() / 30
        if r.t_s < fa:
            return "1_approach"
        if r.t_s < e.first_over_i / 30:
            return "2_near_target"
        if r.t_s < e.first_wrist_lost_i / 30:
            return "3_over_wrist_seen"
        if r.t_s < lim:
            return "4_wrist_lost_to_-105"
        return "5_at_limit"
    C["phase"] = C.apply(phase, axis=1)
    C.to_csv(TB / "q01c_A0B1_chunks.csv", index=False)
    pr = []
    for (tag, ph), g in C.groupby(["tag", "phase"]):
        r = dict(tag=tag, phase=ph, n_chunks=len(g), t_from=g.t_s.min(), t_to=g.t_s.max(), pan_from=g.s0.iloc[0], pan_to=g.s0.iloc[-1],
                 wrist_states=",".join(f"{k}:{v}" for k, v in g.wstate.value_counts().items()), front_vis=int(g.front_vis.sum()))
        for col in ("raw_exec", "rtc_exec", "out_exec_delta", "present_exec_delta", "raw_late", "rtc_late"):
            vc = g[f"dir_{col}"].value_counts()
            r[col] = f"{vc.get('toward', 0)}/{vc.get('hold', 0)}/{vc.get('away', 0)}/n.a.{vc.get('n/a', 0)}"
        # 진행 방향 (처음 목표 쪽 = s_sign) 으로 잰 실행 구간 Δ: + = 처음 진행 방향 (왼쪽) 계속
        r["rtc_exec_med_along_travel"] = float(np.median(g.rtc_exec * g.s_sign))
        r["raw_exec_med_along_travel"] = float(np.median(g.raw_exec * g.s_sign))
        r["present_exec_med_along_travel"] = float(np.median(g.present_exec_delta * g.s_sign))
        pr.append(r)
    P = pd.DataFrame(pr)
    P.to_csv(TB / "q01c_A0B1_phase_chunks.csv", index=False)
    pd.set_option("display.width", 300, "display.max_colwidth", 200)
    print(S.round(1).to_string())
    print(P.round(1).to_string())


if __name__ == "__main__":
    main()
