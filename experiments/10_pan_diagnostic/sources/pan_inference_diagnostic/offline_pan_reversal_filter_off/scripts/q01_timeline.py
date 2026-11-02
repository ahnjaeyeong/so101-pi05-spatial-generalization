"""q01 실물 diag 20 판의 틱 · chunk 시간축 + Pan 목표대 (읽기만, CPU). 로봇 연결 없음.

대상: ROLLOUT_DIAG=1 로 기록된 저장 시도 20 판
  파일럿 12 (필터 켬, 20261029_155513 · 160831), K1 필터 켬 4 (A0–A3, 170219), K1 필터 끔 4 (B0–B3, 170818).
판 목록 · 큐브 좌표 · pe: pan_inference_diagnostic/{pilot,filter_ab/A,filter_ab/B}/pilot_episodes.csv (기존 산출물, 판 시작 사진 기준).

Pan 목표대 (사람 성공 시연 기반, 공식 pe 를 정답으로 쓰지 않음):
  d2 사람 256 편 중 큐브 (a04_cube_positions) 가 이 판 큐브에서 3 cm 안인 편의 첫 닫힘 pan (a02_events.pan_c, 256/256 첫 파지 성공).
  n ≥ 5  → 목표대 = 그 pan 의 [p5, p95]                                  (band_src = human_knn)
  2–4    → [min − 2.63, max + 2.63]  (2.63° = off-K 사람 잔차 SD, p10b)     (band_src = human_knn_few)
  ≤ 1    → pe ± 2·2.63                                                     (band_src = pe_only)
  진행 부호 s = sign(목표대 중앙 − 시작 pan).
  zone (여유 m = 3°):  s·pan < s·가까운끝 − m → under (아직 덜 감)
                       목표대 안 → aligned
                       s·pan > s·먼끝 + m → over (지나침)
                       나머지 (목표대 끝에서 m 안) → undetermined
  정책 자체 성공 파지 pan 은 검산 열로만 둔다 (정답으로 쓰지 않음).

틱 표 (tables/q01_ticks.csv.gz): 판 · 정책 틱 (pop_chunk ≥ 0) 마다
  present  = clamp 때 읽은 Present_Position (ticks.csv)                   [실측]
  sent     = 보낸 Goal_Position (clamp 뒤)                                 [실측]
  out      = 필터 뒤 명령 (filter_log out_; 필터 끔 판은 = rtc)             [실측]
  rtc      = RTC 처리 뒤 queue 출력 (filter_log raw_)                      [실측]
  raw      = 같은 관측 · 같은 기록 noise · RTC 안내 없음 chunk 의 같은 index (diag/replay rtc_off_c*) [재구성]
  wrist_* / front_* = dataset 영상 2 프레임마다 측정 (사이 프레임은 직전 값)
chunk 표 (tables/q01_chunks.csv): chunk 마다 관측 PNG (모델이 실제 받은 입력) 에서 잰 손목 · front 큐브,
  obs state pan, 목표대 zone, 직전 0.5 s 실제 이동, 기록 chunk (RTC) · RTC 끔 재구성 chunk 의 pan 값 (idx 0 9 19 29 49).
판 표 (tables/q01_episodes.csv)
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python q01_timeline.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D2 = Path.home() / "so101_runs/main_k8/d2"
PD = D2 / "pan_inference_diagnostic"
sys.path.insert(0, str(PD / "scripts"))
import cube_coords as CC  # noqa: E402
import p14_grasp_analysis as P14  # noqa: E402

C = CC.C
OUT = PD / "offline_pan_reversal_filter_off"
ROLL = D2 / "eval/rollouts"
AUD = D2 / "data_coverage_audit/tables"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
SD_OFFK = 2.63
MARGIN = 3.0
KNN_CM = 3.0


def episodes():
    rows = []
    for src, cond in ((PD / "pilot/pilot_episodes.csv", "ON"), (PD / "filter_ab/A/pilot_episodes.csv", "ON"),
                      (PD / "filter_ab/B/pilot_episodes.csv", "OFF")):
        d = pd.read_csv(src)
        for i, r in d.iterrows():
            tag = r.label if "pilot/" in str(src) else (("A" if cond == "ON" else "B") + str(i))
            rows.append(dict(tag=tag, label=r.label, set="pilot" if "pilot/" in str(src) else "K1_AB", cond=cond, run=r.run,
                             diag_ep=int(r.episode), ds_ep=int(r.ds_ep), cube_x=r.cube_x, cube_y=r.cube_y, cube_yaw=r.cube_yaw_deg,
                             coord_status=r.coord_status, pe=r.pe, verdict=r.verdict, pan_at_close_logged=r.get("pan_at_close", np.nan)))
    return pd.DataFrame(rows)


def human_band(x, y, pe):
    cp = pd.read_csv(AUD / "a04_cube_positions.csv")[["ep", "cube_x", "cube_y"]]
    ev = pd.read_csv(AUD / "a02_events.csv")[["ep", "pan_c"]]
    h = cp.merge(ev, on="ep")
    d = np.hypot(h.cube_x - x, h.cube_y - y)
    nb = h[d <= KNN_CM]
    n = len(nb)
    if n >= 5:
        lo, hi, src = np.percentile(nb.pan_c, 5), np.percentile(nb.pan_c, 95), "human_knn"
    elif n >= 2:
        lo, hi, src = nb.pan_c.min() - SD_OFFK, nb.pan_c.max() + SD_OFFK, "human_knn_few"
    else:
        lo, hi, src = pe - 2 * SD_OFFK, pe + 2 * SD_OFFK, "pe_only"
    return dict(band_lo=float(lo), band_hi=float(hi), band_mid=float((lo + hi) / 2), band_src=src, band_n=n,
                human_pan_med=float(nb.pan_c.median()) if n else np.nan)


def zone(pan, s, lo, hi):
    near, far = (lo, hi) if s > 0 else (hi, lo)
    sp = s * np.asarray(pan, float)
    z = np.full(sp.shape, "undetermined", dtype=object)
    z[sp < s * near - MARGIN] = "under"
    z[(np.asarray(pan) >= lo) & (np.asarray(pan) <= hi)] = "aligned"
    z[sp > s * far + MARGIN] = "over"
    return z


def zigzag(x, h):
    """hysteresis h 의 전환점 목록 [(index, value, dir_before)] (dir_before = 전환 전 진행 부호)."""
    tp, d, ext_i, hi, lo = [], 0, 0, 0, 0
    for i in range(1, len(x)):
        if d == 0:
            hi = i if x[i] > x[hi] else hi
            lo = i if x[i] < x[lo] else lo
            if x[i] - x[lo] >= h:
                d, ext_i = 1, i
            elif x[hi] - x[i] >= h:
                d, ext_i = -1, i
            continue
        if (d > 0 and x[i] > x[ext_i]) or (d < 0 and x[i] < x[ext_i]):
            ext_i = i
        elif abs(x[i] - x[ext_i]) >= h:
            tp.append((ext_i, float(x[ext_i]), d))
            d, ext_i = -d, i
    return tp


def main():
    import cv2
    E = episodes()
    cache = {}
    tick_rows, chunk_rows, ep_rows, tp_rows = [], [], [], []
    for _, e in E.iterrows():
        run = ROLL / e.run
        FL = pd.read_csv(run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
        f = FL[(FL.event == "cmd") & (FL.episode == e.diag_ep)].sort_values("tick").reset_index(drop=True)
        TK = pd.read_csv(run / "diag/ticks.csv")
        t = TK[(TK.episode == e.diag_ep) & (TK.pop_chunk >= 0)].sort_values("tick").reset_index(drop=True)
        assert len(f) == len(t), (e.tag, len(f), len(t))
        assert (f.tick.values == t.tick.values).all()
        RZ = np.load(run / "diag/replay/replay.npz")
        n = len(t)
        ds = run / "dataset"
        # dataset 프레임 수 = 정책 틱 수 확인
        info, eps, cams = __import__("record_ui").load_meta(str(ds))
        n_ds = int(eps[eps.episode_index == e.ds_ep].iloc[0]["length"])
        # 영상 측정 (2 프레임마다)
        W, F = {}, {}
        for cam, store in (("wrist", W), ("front", F)):
            fr = C.frames(ds, e.ds_ep, cam, 0, n_ds - 1, cache)
            for i in range(0, len(fr), 2):
                if cam == "wrist":
                    store[i] = P14.wrist_measure(fr[i])
                else:
                    store[i] = CC.detect(fr[i])
        band = human_band(e.cube_x, e.cube_y, e.pe)
        pres = t[[f"present_{j}" for j in J]].values.astype(float)
        s0 = pres[0, 0]
        s = float(np.sign(band["band_mid"] - s0))
        z = zone(pres[:, 0], s, band["band_lo"], band["band_hi"])
        g_state = pres[:, 5]
        cl = C.close_events(g_state)
        first_close = int(cl[0]) if cl else None
        raw = np.array([RZ[f"rtc_off_c{int(c):05d}"][int(i)] if f"rtc_off_c{int(c):05d}" in RZ else np.full(6, np.nan)
                        for c, i in zip(t.pop_chunk, t.pop_idx)])
        wv_last, fv_last = {}, {}
        seen = False
        for i in range(n):
            if i in W:
                wv_last = W[i]
            if i in F:
                fv_last = F[i]
            seen = seen or bool(wv_last.get("w_vis", False))
            fvis = bool(fv_last.get("n_blobs", 0) > 0 and fv_last.get("area_ratio", 0) >= 0.3)
            tick_rows.append(dict(tag=e.tag, cond=e["cond"], i=i, tick=int(t.tick[i]), t_s=i / 30, pop_chunk=int(t.pop_chunk[i]), pop_idx=int(t.pop_idx[i]),
                                  pan_present=pres[i, 0], pan_sent=float(t.sent_shoulder_pan[i]), pan_out=float(f.out_shoulder_pan[i]),
                                  pan_rtc=float(f.raw_shoulder_pan[i]), pan_raw=raw[i, 0], lift_present=pres[i, 1], grip_present=pres[i, 5],
                                  zone_h=z[i], wrist_vis=bool(wv_last.get("w_vis", False)), wrist_u=wv_last.get("w_u", np.nan), wrist_v=wv_last.get("w_v", np.nan),
                                  wrist_seen_before=seen, front_vis=fvis, front_x=fv_last.get("x", np.nan), front_y=fv_last.get("y", np.nan),
                                  before_first_close=(first_close is None or i < first_close)))
        T = pd.DataFrame(tick_rows[-n:])
        # 실제 pan 전환점 (hysteresis 3°)
        for (ti, val, dbefore) in zigzag(pres[:, 0], 3.0):
            tp_rows.append(dict(tag=e.tag, cond=e["cond"], i=ti, t_s=ti / 30, pan=val, dir_before=dbefore, zone_h=z[ti],
                                                                wrist_vis=bool(T.wrist_vis[ti]), front_vis=bool(T.front_vis[ti]),
                                before_first_close=(first_close is None or ti < first_close)))
        # chunk 표
        meta = [json.loads(x) for x in (run / "diag/chunks.jsonl").read_text().splitlines()]
        meta = [m for m in meta if m["episode"] == e.diag_ep]
        tick_to_i = {int(k): i for i, k in enumerate(t.tick)}
        for m in meta:
            cid = int(m["chunk_id"])
            zc = np.load(run / "diag/chunks" / f"c{cid:05d}.npz")
            P = zc["processed"][:, 0].astype(float)
            O = RZ[f"rtc_off_c{cid:05d}"][:, 0].astype(float) if f"rtc_off_c{cid:05d}" in RZ else np.full(50, np.nan)
            ot = int(m["obs_tick"])
            oi = tick_to_i.get(ot, 0 if ot < int(t.tick[0]) else None)
            if oi is None:
                oi = int(np.searchsorted(t.tick.values, ot))
            oi = min(oi, n - 1)
            sp = float(m["obs_state"][0])
            wimg = cv2.cvtColor(cv2.imread(str(run / "diag/obs" / f"c{cid:05d}_wrist.png")), cv2.COLOR_BGR2RGB)
            fimg = cv2.cvtColor(cv2.imread(str(run / "diag/obs" / f"c{cid:05d}_front.png")), cv2.COLOR_BGR2RGB)
            wm, fm = P14.wrist_measure(wimg), CC.detect(fimg)
            prev = pres[max(0, oi - 15):oi + 1, 0]
            popped = T[T.pop_chunk == cid]
            r = dict(tag=e.tag, cond=e["cond"], chunk_id=cid, obs_tick=ot, obs_i=oi, t_s=oi / 30, first_in_ep=(m["qsize_before"] == 0),
                     has_prefix=bool(m["has_prefix"]), inference_delay=m.get("inference_delay"), applied_delay=m.get("applied_delay"),
                     s0=sp, zone_h=zone([sp], s, band["band_lo"], band["band_hi"])[0], s_sign=s, band_mid=band["band_mid"],
                     err_to_band_mid=band["band_mid"] - sp, prior_move_0p5s=float(prev[-1] - prev[0]) if len(prev) > 1 else 0.0,
                     wrist_vis=bool(wm.get("w_vis", False)), wrist_u=wm.get("w_u", np.nan), wrist_v=wm.get("w_v", np.nan), wrist_area=wm.get("w_area", np.nan),
                     front_vis=bool(fm.get("n_blobs", 0) > 0 and fm.get("area_ratio", 0) >= 0.3), front_area_ratio=fm.get("area_ratio", np.nan),
                     front_x=fm.get("x", np.nan), front_y=fm.get("y", np.nan),
                     wrist_seen_before=bool(T.wrist_seen_before[oi]), before_first_close=(first_close is None or oi < first_close),
                     lift=float(m["obs_state"][1]), n_popped=len(popped),
                     exec_first_idx=int(popped.pop_idx.min()) if len(popped) else None, exec_last_idx=int(popped.pop_idx.max()) if len(popped) else None,
                     out_exec_delta=float(popped.pan_out.iloc[-1] - popped.pan_out.iloc[0]) if len(popped) > 1 else np.nan,
                     present_exec_delta=float(popped.pan_present.iloc[-1] - popped.pan_present.iloc[0]) if len(popped) > 1 else np.nan)
            for nm, A in (("rtc", P), ("raw", O)):
                for k in (0, 9, 19, 29, 49):
                    r[f"{nm}_a{k}"] = float(A[k])
            chunk_rows.append(r)
        hit = np.where(pres[:, 0] <= -105)[0]
        succ = [float(pres[c, 0]) for c in cl if g_state[c:c + 30].min() >= 9]
        ep_rows.append(dict(**e.to_dict(), **band, start_pan=s0, s_sign=s, n_ticks=n, n_ds_frames=n_ds, first_close_i=first_close,
                            pan_min=float(pres[:, 0].min()), pan_max=float(pres[:, 0].max()),
                            first_over_i=int(np.argmax(z == "over")) if (z == "over").any() else None,
                            max_over_deg=float(np.max(s * pres[:, 0] - s * (band["band_hi"] if s > 0 else band["band_lo"]))),
                            reach_m105_i=int(hit[0]) if len(hit) else None,
                            success_close_pan=succ[0] if succ else np.nan, n_close=len(cl)))
        print(e.tag, e["cond"], band["band_src"], band["band_n"], round(band["band_lo"], 1), round(band["band_hi"], 1), "n", n, "ds", n_ds,
              "zones", dict(pd.Series(z).value_counts()), flush=True)
    pd.DataFrame(tick_rows).to_csv(OUT / "tables/q01_ticks.csv.gz", index=False)
    pd.DataFrame(chunk_rows).to_csv(OUT / "tables/q01_chunks.csv", index=False)
    pd.DataFrame(ep_rows).to_csv(OUT / "tables/q01_episodes.csv", index=False)
    pd.DataFrame(tp_rows).to_csv(OUT / "tables/q01_turnpoints.csv", index=False)


if __name__ == "__main__":
    main()
