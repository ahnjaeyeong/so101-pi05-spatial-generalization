"""q01b 최종 목표대 · zone · 실제 방향 반응 (분석 A) (읽기만, CPU). 로봇 연결 없음.

입력: q01 의 tables/q01_{episodes,ticks,chunks,turnpoints}.

최종 목표대 (q01 의 사람 목표대만으로는 K1 정책 성공 파지 pan −22.9 … −28.6° 이 'under' 로 나와 쓰지 않음):
  band = [min(사람 목표대 lo, 같은 자리 (3 cm) 정책 성공 파지 pan), max(사람 목표대 hi, 그 pan)]
  정책 성공 파지 pan = 판정 P 인 판의 첫 '쥔' 닫힘 (그리퍼 바닥 ≥ 9) 의 present pan (q01 success_close_pan).
zone_f (여유: under 쪽 3°, over 쪽 8°):
  under        : s·pan < s·가까운끝 − 3
  aligned      : 목표대 안
  over         : s·pan > s·먼끝 + 8
  undetermined : 그 사이 (목표대 끝에서 under 쪽 3° · over 쪽 8° 안)
방향 분류 (chunk, 문턱 2°):  toward = 목표대 중앙 쪽으로 ≥ 2°, away = 반대로 ≥ 2°, hold = |Δ| < 2°.
  zone aligned · undetermined 은 목표 방향이 정해지지 않아 toward/away 를 매기지 않음 (dir = 'n/a').
chunk 별 Δ (모두 pan °):
  rtc_exec = 기록 chunk (RTC 뒤) a29 − a9  (실행 구간 index 10–29)      [실측 chunk]
  raw_exec = 같은 관측 · 기록 noise · RTC 안내 없음 a29 − a9             [재구성]
  rtc_late / raw_late = a49 − a29 (실행 안 되는 30–49)
  out_exec = 그 chunk 에서 실제 꺼낸 틱의 필터 뒤 명령 마지막 − 처음       [실측]
  present_exec = 같은 틱 구간 present 마지막 − 처음                       [실측]
손목 상태 (chunk 관측 PNG): wrist_in_view = 큐브 보임 · 중심이 테두리 5 % (u) / 8 % (v) 밖, wrist_edge = 보이지만 중심이 테두리 근처,
  wrist_lost_after_seen = 안 보임 (그 판에서 전에 본 적 있음), wrist_never_seen = 안 보임 (그 전에 본 적 없음).
실제 반전: q01 전환점 (present pan, hysteresis 3°) 중 dir_before 가 '목표에서 멀어지는' 쪽이고 그 자리 zone_f = over 인 첫 점.
출력: tables/q01b_episodes.csv, q01b_chunks.csv, q01b_ticks.csv.gz, q01b_phase_dir.csv, q01b_turnpoints.csv, q01b_events_A0_B1.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q01b_zones_reversal.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path.home() / "so101_runs/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off"
TB = OUT / "tables"
M_UNDER, M_OVER, THR = 3.0, 8.0, 2.0


def zone_f(pan, s, lo, hi):
    pan = np.asarray(pan, float)
    near, far = (lo, hi) if s > 0 else (hi, lo)
    sp = s * pan
    z = np.full(pan.shape, "undetermined", dtype=object)
    z[sp < s * near - M_UNDER] = "under"
    z[(pan >= lo) & (pan <= hi)] = "aligned"
    z[sp > s * far + M_OVER] = "over"
    return z


def dclass(delta, tdir):
    if not np.isfinite(delta):
        return "nan"
    if tdir == 0:
        return "n/a"
    if abs(delta) < THR:
        return "hold"
    return "toward" if np.sign(delta) == tdir else "away"


def main():
    E = pd.read_csv(TB / "q01_episodes.csv")
    T = pd.read_csv(TB / "q01_ticks.csv.gz")
    Ch = pd.read_csv(TB / "q01_chunks.csv")
    TP = pd.read_csv(TB / "q01_turnpoints.csv")
    P = E[E.verdict == "P"]
    lo_f, hi_f, srcs = [], [], []
    for _, e in E.iterrows():
        d = np.hypot(P.cube_x - e.cube_x, P.cube_y - e.cube_y)
        pp = P[(d <= 3.0)].success_close_pan.dropna().values
        lo_f.append(min([e.band_lo, *pp]))
        hi_f.append(max([e.band_hi, *pp]))
        srcs.append(f"{e.band_src}+policy{len(pp)}")
    E["bandf_lo"], E["bandf_hi"], E["bandf_src"] = lo_f, hi_f, srcs
    E["bandf_mid"] = (E.bandf_lo + E.bandf_hi) / 2
    E["s_sign"] = np.sign(E.bandf_mid - E.start_pan)
    eb = E.set_index("tag")
    # 틱
    zt = []
    for tag, g in T.groupby("tag", sort=False):
        e = eb.loc[tag]
        zt.append(pd.Series(zone_f(g.pan_present.values, e.s_sign, e.bandf_lo, e.bandf_hi), index=g.index))
    T["zone"] = pd.concat(zt)
    # 손목에서 1 s 넘게 연속 사라짐 (본 뒤) 표시
    T["wrist_lost"] = False
    for tag, g in T.groupby("tag", sort=False):
        v = g.wrist_vis.values.astype(bool)
        seen = g.wrist_seen_before.values.astype(bool)
        lost = np.zeros(len(v), bool)
        run = 0
        for i in range(len(v)):
            run = run + 1 if (not v[i] and seen[i]) else 0
            if run >= 30:
                lost[i - 29:i + 1] = True
        T.loc[g.index, "wrist_lost"] = lost
    # chunk
    Ch["zone"] = [zone_f([r.s0], eb.loc[r.tag].s_sign, eb.loc[r.tag].bandf_lo, eb.loc[r.tag].bandf_hi)[0] for r in Ch.itertuples()]
    Ch["tdir"] = [(np.sign(eb.loc[r.tag].bandf_mid - r.s0) if r.zone in ("under", "over") else 0) for r in Ch.itertuples()]
    Ch["wrist_lost"] = [bool(T[(T.tag == r.tag) & (T.i == r.obs_i)].wrist_lost.iloc[0]) for r in Ch.itertuples()]
    for nm in ("rtc", "raw"):
        Ch[f"{nm}_first"] = Ch[f"{nm}_a0"] - Ch.s0
        Ch[f"{nm}_cum10"] = Ch[f"{nm}_a9"] - Ch.s0
        Ch[f"{nm}_cum20"] = Ch[f"{nm}_a19"] - Ch.s0
        Ch[f"{nm}_cum30"] = Ch[f"{nm}_a29"] - Ch.s0
        Ch[f"{nm}_exec"] = Ch[f"{nm}_a29"] - Ch[f"{nm}_a9"]
        Ch[f"{nm}_late"] = Ch[f"{nm}_a49"] - Ch[f"{nm}_a29"]
    for col in ("rtc_exec", "raw_exec", "rtc_late", "raw_late", "out_exec_delta", "present_exec_delta", "rtc_cum30", "raw_cum30"):
        Ch[f"dir_{col}"] = [dclass(d, td) for d, td in zip(Ch[col], Ch.tdir)]
    Ch["prior_dir"] = [dclass(d, td) for d, td in zip(Ch.prior_move_0p5s, Ch.tdir)]
    # zone × 손목 상태 별 방향 비율 (첫 닫힘 전)
    edge = (Ch.wrist_u < 0.05) | (Ch.wrist_u > 0.95) | (Ch.wrist_v < 0.08) | (Ch.wrist_v > 0.92)
    Ch["wstate"] = np.where(Ch.wrist_vis & ~edge, "wrist_in_view", np.where(Ch.wrist_vis, "wrist_edge",
                            np.where(Ch.wrist_seen_before, "wrist_lost_after_seen", "wrist_never_seen")))
    rows = []
    pre = Ch[Ch.before_first_close]
    for (cond, zn, ws), g in pre.groupby(["cond", "zone", "wstate"]):
        r = dict(cond=cond, zone=zn, wstate=ws, n_chunks=len(g), n_eps=g.tag.nunique(), front_vis_frac=g.front_vis.mean())
        for col in ("rtc_exec", "raw_exec", "out_exec_delta", "present_exec_delta", "rtc_late", "raw_late"):
            vc = g[f"dir_{col}"].value_counts()
            for k in ("toward", "away", "hold"):
                r[f"{col}_{k}"] = int(vc.get(k, 0))
        rows.append(r)
    PH = pd.DataFrame(rows)
    # 판 사건 · 반전
    ep_extra, tp_rows = [], []
    for _, e in E.iterrows():
        g = T[T.tag == e.tag].reset_index(drop=True)
        z = g.zone.values
        tp = TP[TP.tag == e.tag].copy()
        tp["zone"] = zone_f(tp.pan.values, e.s_sign, e.bandf_lo, e.bandf_hi) if len(tp) else []
        # 전환 전 진행이 목표대 중앙에서 멀어지는 쪽이었나
        tp["away_before"] = [bool(np.sign(db) == -np.sign(e.bandf_mid - p)) for db, p in zip(tp.dir_before, tp.pan)]
        tp_rows.append(tp)
        fc = int(e.first_close_i) if np.isfinite(e.first_close_i) else len(g)
        over_i = np.where((z == "over") & (np.arange(len(g)) < fc))[0]
        lost_i = np.where(g.wrist_lost.values & (np.arange(len(g)) < fc))[0]
        first_over = int(over_i[0]) if len(over_i) else None
        rev = tp[(tp.zone == "over") & tp.away_before & (tp.i >= (first_over or 0))] if first_over is not None else tp.iloc[0:0]
        rev = rev[rev.i < fc] if len(rev) else rev
        ep_extra.append(dict(tag=e.tag, first_over_i=first_over, first_wrist_lost_i=int(lost_i[0]) if len(lost_i) else None,
                             n_over_ticks_preclose=int(len(over_i)), first_reversal_in_over_i=int(rev.i.iloc[0]) if len(rev) else None,
                             reversal_delay_s=float((rev.i.iloc[0] - first_over) / 30) if len(rev) else None,
                             pan_at_first_over=float(g.pan_present[first_over]) if first_over is not None else None,
                             max_past_far_edge=float(np.max(e.s_sign * g.pan_present.values[:fc] - e.s_sign * (e.bandf_hi if e.s_sign > 0 else e.bandf_lo))),
                             n_turnpoints_preclose=int((tp.i < fc).sum()), n_turn_away_before_preclose=int(((tp.i < fc) & tp.away_before).sum())))
    E = E.rename(columns={"first_over_i": "first_over_i_humanband", "max_over_deg": "max_over_deg_humanband"}).merge(pd.DataFrame(ep_extra), on="tag")
    # A0 · B1 사건표
    evrows = []
    for tag in ("A0", "B1"):
        e = E.set_index("tag").loc[tag]
        g = T[T.tag == tag].reset_index(drop=True)
        z = g.zone.values
        def first(mask):
            k = np.where(mask)[0]
            return int(k[0]) if len(k) else None
        evs = {"start": 0, "first_aligned": first(z == "aligned"), "first_past_far_edge": first(e.s_sign * g.pan_present.values > e.s_sign * (e.bandf_hi if e.s_sign > 0 else e.bandf_lo)),
               "first_over": first(z == "over"), "wrist_last_seen": (first(g.wrist_lost.values) - 1) if first(g.wrist_lost.values) else None,
               "first_wrist_lost_1s": first(g.wrist_lost.values), "reach_-90": first(g.pan_present.values <= -90), "reach_-105": first(g.pan_present.values <= -105), "end": len(g) - 1}
        for k, i in evs.items():
            if i is None:
                evrows.append(dict(tag=tag, event=k))
                continue
            evrows.append(dict(tag=tag, event=k, i=i, t_s=i / 30, pan_present=g.pan_present[i], pan_rtc=g.pan_rtc[i], pan_raw=g.pan_raw[i], pan_out=g.pan_out[i],
                               pan_sent=g.pan_sent[i], zone=z[i], wrist_vis=g.wrist_vis[i], front_vis=g.front_vis[i], lift=g.lift_present[i]))
    T.to_csv(TB / "q01b_ticks.csv.gz", index=False)
    Ch.to_csv(TB / "q01b_chunks.csv", index=False)
    E.to_csv(TB / "q01b_episodes.csv", index=False)
    PH.to_csv(TB / "q01b_phase_dir.csv", index=False)
    pd.concat(tp_rows).to_csv(TB / "q01b_turnpoints.csv", index=False)
    pd.DataFrame(evrows).to_csv(TB / "q01b_events_A0_B1.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(E[["tag", "cond", "verdict", "bandf_lo", "bandf_hi", "bandf_src", "first_over_i", "first_wrist_lost_i", "first_reversal_in_over_i", "reversal_delay_s", "max_past_far_edge",
             "n_turnpoints_preclose", "n_turn_away_before_preclose"]].round(1).to_string())
    print(PH.to_string())
    print(pd.DataFrame(evrows).round(1).to_string())


if __name__ == "__main__":
    main()
