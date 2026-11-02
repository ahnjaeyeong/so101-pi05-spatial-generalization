"""q04 d2 사람 시연 256 편의 Pan 방향 반전 · 복구 커버리지 (읽기만, CPU). 로봇 연결 없음, dataset 변경 없음.

입력: data_coverage_audit/02_servo_timeline.parquet (프레임별 pan state = measured_position, action = commanded_position),
      tables/a02_events.csv (close_start = 첫 닫힘 시작 프레임, pan_c = 첫 파지 프레임 pan state, pan0),
      tables/a04_cube_positions.csv (큐브 좌표 · 가까운 K · 묶음).
창: 판 시작 … close_start (그리퍼 닫기 시작 전 접근 구간).
각 판의 목표 = 그 판 자신의 첫 파지 pan (pan_c, 256/256 첫 파지 성공). s = sign(pan_c − pan0).
반전 검출: pan state 의 hysteresis 전환점 (h = 1, 2, 3, 5, 10°). h 보다 작은 왕복 (서보 잡음 · 미세 진동 · 멈췄다 다시 감) 은 전환점이 되지 않는다.
  전환점 분류 (전환점 pan x_tp, 전환 전 진행 부호 d):
    overshoot_return : d = s (목표 쪽으로 가다) 이고 s·(x_tp − pan_c) > 0 (목표를 지나친 뒤) 되돌아옴
    early_backoff    : d = s 이고 아직 목표 전 (s·(x_tp − pan_c) ≤ 0) 에서 되돌아감 (목표에서 멀어지는 쪽으로 바뀜)
    wrong_way_fix    : d = −s (목표 반대로 가다) 에서 목표 쪽으로 바뀜 (처음 반대 방향 출발 · 되돌아감 뒤 재접근 포함)
  지나침 크기 ovs = max_t s·(pan_t − pan_c) (창 안, + 면 목표를 지나친 최대 각).
멈춤 뒤 같은 방향 계속 (반전 아님): 목표 전 (s·(pan_c − x) ≥ 5°) 에서 |속도| < 0.1°/프레임 이 ≥ 9 프레임 뒤 같은 방향으로 ≥ 3° 더 감.
'지나친 상태' 프레임 커버리지: s·(pan − pan_c) > 3 / 5 / 8 / 15 / 30° 인 창 안 프레임 수 · 판 수, 그 프레임의 action − state 부호 (목표 쪽 = 복귀 명령).
손목 영상 (h = 3° overshoot_return · wrong_way_fix 전환점만): 전환점 프레임 손목 큐브 보임 여부 (p14 wrist_measure, dataset 영상).
출력: tables/q04_human_episodes.csv, q04_human_turnpoints.csv, q04_over_frames.csv, q04_summary.json, q04_by_position.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q04_human_recovery_coverage.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
PD = D2 / "pan_inference_diagnostic"
OUT = PD / "offline_pan_reversal_filter_off"
AUD = D2 / "data_coverage_audit"
sys.path.insert(0, str(PD / "scripts"))
sys.path.insert(0, str(OUT / "scripts"))
from q01_timeline import zigzag  # noqa: E402

HS = (1.0, 2.0, 3.0, 5.0, 10.0)
OVER_T = (3, 5, 8, 15, 30)


def main():
    L = pd.read_parquet(AUD / "02_servo_timeline.parquet", columns=["episode_id", "frame_index", "servo_name", "measured_position", "commanded_position"])
    pan = L[L.servo_name == "shoulder_pan"].sort_values(["episode_id", "frame_index"])
    lift = L[L.servo_name == "shoulder_lift"].sort_values(["episode_id", "frame_index"])
    ev = pd.read_csv(AUD / "tables/a02_events.csv").set_index("ep")
    cp = pd.read_csv(AUD / "tables/a04_cube_positions.csv").set_index("ep")
    ep_rows, tp_rows, over_rows = [], [], []
    for ep, g in pan.groupby("episode_id"):
        e = ev.loc[ep]
        cs = int(e.close_start)
        x = g.measured_position.values[:cs + 1]
        act = g.commanded_position.values[:cs + 1]
        lf = lift[lift.episode_id == ep].measured_position.values[:cs + 1]
        pc, p0 = float(e.pan_c), float(x[0])
        s = float(np.sign(pc - p0)) if abs(pc - p0) >= 1 else 0.0
        r = dict(ep=ep, group=cp.loc[ep].group, nearest_K=cp.loc[ep].nearest_K, dist_K=cp.loc[ep].dist_nearest_K_cm, cube_x=cp.loc[ep].cube_x,
                 cube_y=cp.loc[ep].cube_y, pan0=p0, pan_c=pc, need=pc - p0, s=s, close_start=cs, n_frames=len(x))
        r["ovs"] = float(np.max(s * (x - pc))) if s else np.nan
        r["ovs_frame"] = int(np.argmax(s * (x - pc))) if s else None
        for h in HS:
            tps = zigzag(x, h)
            cls = []
            for (i, val, d) in tps:
                if not s:
                    c = "small_need"
                elif d == s and s * (val - pc) > 0:
                    c = "overshoot_return"
                elif d == s:
                    c = "early_backoff"
                else:
                    c = "wrong_way_fix"
                cls.append(c)
                if h in (2.0, 3.0, 5.0):
                    # 전환 뒤 반대로 간 양 (다음 전환점 또는 창 끝까지의 극값)
                    nxt = [t for t in tps if t[0] > i]
                    j_end = nxt[0][0] if nxt else len(x) - 1
                    seg = x[i:j_end + 1]
                    amp = float(np.max(np.abs(seg - val)))
                    tp_rows.append(dict(ep=ep, h=h, i=i, t_s=i / 30, pan=val, dir_before=d, cls=c, past_target_deg=float(s * (val - pc)) if s else np.nan,
                                        amp_after=amp, lift=float(lf[i]), frames_to_close=cs - i, group=r["group"], nearest_K=r["nearest_K"]))
            r[f"n_tp_h{int(h)}"] = len(tps)
            for c in ("overshoot_return", "early_backoff", "wrong_way_fix"):
                r[f"n_{c}_h{int(h)}"] = cls.count(c)
        # 멈춤 뒤 같은 방향 계속
        v = np.gradient(x)
        n_pause_cont = 0
        if s:
            k = 0
            while k < len(x):
                if abs(v[k]) < 0.1 and s * (pc - x[k]) >= 5:
                    j = k
                    while j < len(x) and abs(v[j]) < 0.1:
                        j += 1
                    if j - k >= 9 and j < len(x):
                        after = x[j:min(len(x), j + 60)]
                        if len(after) and np.max(s * (after - x[k])) >= 3:
                            n_pause_cont += 1
                    k = j + 1
                else:
                    k += 1
        r["n_pause_then_continue"] = n_pause_cont
        # 지나친 상태 프레임
        if s:
            past = s * (x - pc)
            for T in OVER_T:
                m = past > T
                r[f"frames_past_{T}"] = int(m.sum())
                if m.any():
                    da = s * (act[m] - x[m])
                    over_rows.append(dict(ep=ep, thr=T, n_frames=int(m.sum()), act_toward_target_frac=float((da < -0.5).mean()),
                                          act_away_frac=float((da > 0.5).mean()), lift_med=float(np.median(lf[m]))))
        ep_rows.append(r)
    EP = pd.DataFrame(ep_rows)
    TP = pd.DataFrame(tp_rows)
    OV = pd.DataFrame(over_rows)
    # 손목 영상: h = 3 overshoot_return · wrong_way_fix 전환점
    import p14_grasp_analysis as P14
    sys.path.insert(0, str(D2 / "diag_grasp_bias"))
    import common as Cm
    cache = {}
    ds = D2 / "dataset"
    wv = []
    for k, t in TP[(TP.h == 3.0) & TP.cls.isin(["overshoot_return", "wrong_way_fix", "early_backoff"])].iterrows():
        fr = Cm.frames(ds, int(t.ep), "wrist", int(t.i), int(t.i), cache)
        w = P14.wrist_measure(fr[0]) if fr else {}
        wv.append(dict(idx=k, wrist_vis=w.get("w_vis", False), wrist_u=w.get("w_u", np.nan), wrist_v=w.get("w_v", np.nan)))
    if wv:
        W = pd.DataFrame(wv).set_index("idx")
        TP = TP.join(W)
    EP.to_csv(OUT / "tables/q04_human_episodes.csv", index=False)
    TP.to_csv(OUT / "tables/q04_human_turnpoints.csv", index=False)
    OV.to_csv(OUT / "tables/q04_over_frames.csv", index=False)
    # 위치별
    EP["first_dir_ok"] = np.sign(ev.loc[EP.ep].pan_first_dir.values) == np.sign(EP.need.values)
    BP = EP.groupby("nearest_K").agg(n=("ep", "size"), need_med=("need", "median"), ovs_med=("ovs", "median"), ovs_max=("ovs", "max"),
                                      ovs_ge3=("ovs", lambda v: int((v >= 3).sum())), ovs_ge5=("ovs", lambda v: int((v >= 5).sum())),
                                      n_tp3_any=("n_tp_h3", lambda v: int((v > 0).sum())), first_dir_ok=("first_dir_ok", "sum")).reset_index()
    BP.to_csv(OUT / "tables/q04_by_position.csv", index=False)
    summ = {"n_eps": int(len(EP)), "n_small_need": int((EP.s == 0).sum())}
    for h in HS:
        hh = int(h)
        summ[f"h{hh}"] = {"eps_with_any_tp": int((EP[f"n_tp_h{hh}"] > 0).sum()), "n_tp": int(EP[f"n_tp_h{hh}"].sum()),
                          **{c: {"n_tp": int(EP[f"n_{c}_h{hh}"].sum()), "n_eps": int((EP[f"n_{c}_h{hh}"] > 0).sum())}
                             for c in ("overshoot_return", "early_backoff", "wrong_way_fix")}}
    summ["ovs_quantiles"] = {q: float(EP.ovs.quantile(q / 100)) for q in (50, 75, 90, 95, 99, 100)}
    summ["eps_ovs_ge"] = {T: int((EP.ovs >= T).sum()) for T in OVER_T}
    summ["frames_past"] = {T: int(EP[f"frames_past_{T}"].sum()) for T in OVER_T}
    summ["pause_then_continue"] = {"n_events": int(EP.n_pause_then_continue.sum()), "n_eps": int((EP.n_pause_then_continue > 0).sum())}
    summ["first_dir_ok"] = int(EP.first_dir_ok.sum())
    if "wrist_vis" in TP:
        t3 = TP[TP.h == 3.0]
        summ["h3_wrist_vis_at_tp"] = {c: {"n": int((t3.cls == c).sum()), "wrist_vis": int(t3[t3.cls == c].wrist_vis.fillna(False).astype(bool).sum())}
                                      for c in ("overshoot_return", "early_backoff", "wrong_way_fix")}
    (OUT / "tables/q04_summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False))
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print(BP.round(1).to_string())


if __name__ == "__main__":
    main()
