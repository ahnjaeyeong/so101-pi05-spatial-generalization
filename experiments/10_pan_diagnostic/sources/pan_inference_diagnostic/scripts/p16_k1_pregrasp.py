"""p16 K1 필터 켬/끔 8 판의 파지 직전 정밀 분석 (읽기만, CPU). 로봇 연결 없음.

기준 시각:
  닫힘 판: 그리퍼 '명령' 닫힘 시작 tc = 보낸 Goal gripper 가 직전 1 s 최대에서 3 넘게 줄어든 첫 틱 (state 닫힘 시작 on 보다 서보 지연만큼 앞섬).
           모든 닫힘 이벤트 (재시도 포함) 를 따로 본다.
  안 닫힌 판 (A0 · B1): 손목 영상에서 큐브가 마지막으로 보인 틱 t_lost.
1. 동기화 표 (tc − 30 … tc + 15 틱, 관절 6 개):
   raw_chunk = RTC 안내 없는 반사실 (p05, 같은 관측 · noise) 의 그 틱 index 값 [반사실]
   rtc       = RTC 처리 뒤 queue 출력 (filter_log raw) [실측]
   out       = 필터 뒤 (켬: EMA + 속도 제한, 끔: = rtc) [실측]
   goal      = 보낸 Goal_Position (clamp 뒤) [실측],  present = clamp 때 읽은 Present_Position [실측]
   FK (ac.tcp) 는 '명령 vs 현재 자세' 의 상대 차 (같은 자세 근처 Jacobian) 로만 쓴다 — 절대 위치 · 큐브 대비 오차의 정답으로 쓰지 않음.
2. 필터 영향 (tc 앞 1 s): 관절별 out − rtc 부호 평균 · |차|, tc 때 rtc − present (명령 의도 대비 팔 위치) · out − present,
   FK 상대: tc 때 z(rtc 명령) − z(present), z(out) − z(present) (cm, 음수 = 명령이 더 낮음 = 아직 내려가는 중)
   tc 뒤 0.5 s 동안 present z 가 더 내려간 양 (닫히는 동안 하강 계속?).
3. 계획 (tc 를 내보낸 chunk): 그 chunk 의 index i_c (tc 에 꺼낸 index) 에서 계획된 FK z 와 그 뒤 index 의 최저 z,
   최저 z 위치 index, 계획 그리퍼 닫힘 index, RTC 끔 반사실 chunk 의 같은 값.
4. 손목 영상 (dataset 영상, tc − 30 … tc + 15, 3 프레임마다): 큐브 중심 u · v · 넓이 · 보임 — 사람 5–95 % 범위 대비 (p14 와 같은 측정).
5. 안 닫힌 판: t_lost 전후 pan state · 명령 · 계획 (chunk idx 49 pan − 현재) 방향.
출력: filter_ab/p16_sync_<A|B><판>_<이벤트>.csv, p16_events.csv, p16_wrist.csv, p16_sweep.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p16_k1_pregrasp.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402
import p14_grasp_analysis as P14  # noqa: E402

ac, C = CC.ac, CC.C
D2 = CC.D2
AB = D2 / "pan_inference_diagnostic/filter_ab"
ROLL = D2 / "eval/rollouts"
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
RUNS = {"A": "20261029_170219_32_20000_20k_filt_on", "B": "20261029_170818_32_20000_20k_filt_off"}


def load(run, ep):
    FL = pd.read_csv(ROLL / run / "filter_log.csv", dtype={"vclip_mask": str, "ema_reset_mask": str})
    f = FL[(FL.event == "cmd") & (FL.episode == ep)].sort_values("tick").reset_index(drop=True)
    TK = pd.read_csv(ROLL / run / "diag/ticks.csv")
    t = TK[(TK.episode == ep) & (TK.pop_chunk >= 0)].sort_values("tick").reset_index(drop=True)
    assert len(f) == len(t)
    RZ = np.load(ROLL / run / "diag/replay/replay.npz")
    proc = {}
    for c in t.pop_chunk.unique():
        proc[int(c)] = np.load(ROLL / run / "diag/chunks" / f"c{int(c):05d}.npz")["processed"]
    return f, t, RZ, proc


def fkz(q5):
    return ac.tcp(np.atleast_2d(q5))[:, 2]


def main():
    H = json.load(open(D2 / "pan_inference_diagnostic/pilot/p14_summary.json"))["human_ref_5_95"]
    cache = {}
    ev_rows, wr_rows, sw_rows = [], [], []
    for G, run in RUNS.items():
        for ep_i, ep in enumerate(sorted(pd.read_csv(ROLL / run / "filter_log.csv", usecols=["episode"]).episode.unique())):
            f, t, RZ, proc = load(run, ep)
            n = len(f)
            rtc = f[[f"raw_{j}" for j in J]].values.astype(float)
            out = f[[f"out_{j}" for j in J]].values.astype(float)
            goal = t[[f"sent_{j}" for j in J]].values.astype(float)
            pres = t[[f"present_{j}" for j in J]].values.astype(float)
            off = np.array([RZ[f"rtc_off_c{int(c):05d}"][int(i)] if f"rtc_off_c{int(c):05d}" in RZ else np.full(6, np.nan)
                            for c, i in zip(t.pop_chunk, t.pop_idx)])
            g_state = pres[:, 5]
            cl = C.close_events(g_state)
            tag = f"{G}{ep_i}"
            ds = ROLL / run / "dataset"
            # 손목: 판 전체 3 프레임마다 (보임 여부 · 위치)
            wv = []
            for fr in range(0, n, 3):
                w = P14.wrist_measure(C.frames(ds, ep_i, "wrist", fr, fr, cache)[0])
                wv.append(dict(frame=fr, **w))
            WV = pd.DataFrame(wv)
            events = []
            for k, c in enumerate(cl):
                on, _ = P14.onset_of(g_state, c)
                lo = max(0, on - 45)
                gm = np.maximum.accumulate(goal[lo:on + 1, 5])
                drop = np.where(goal[lo:on + 1, 5] < gm - 3)[0]
                tc = lo + int(drop[0]) if len(drop) else on
                events.append((k, c, on, tc))
            # 파지 성공 (그리퍼 ≥ 9 로 1 s 유지) 뒤의 닫힘은 상자에 놓은 뒤 닫힘이라 뺀다
            keep, held = [], False
            for ev in events:
                if held:
                    break
                keep.append(ev)
                held = bool(g_state[ev[1]:ev[1] + 30].min() >= 9)
            events = keep
            if not cl:
                # 큐브가 손목 화면에서 처음으로 1 s (3 프레임 간격 10 칸) 넘게 연속 사라진 시작 프레임
                vis = WV.w_vis.fillna(False).astype(bool).values
                t_lost = 0
                for q in range(len(vis) - 10):
                    if vis[q] and not vis[q + 1:q + 11].any():
                        t_lost = int(WV.frame.values[q + 1])
                        break
                events.append(("lost", None, None, t_lost))
            for k, c, on, tc in events:
                lo, hi = max(0, tc - 30), min(n, tc + 16)
                rows = []
                for i in range(lo, hi):
                    r = {"tick_rel": i - tc, "t_rel_s": (i - tc) / 30, "pop_chunk": int(t.pop_chunk[i]), "pop_idx": int(t.pop_idx[i])}
                    for jj, j in enumerate(J):
                        r.update({f"{j}_raw_chunk": off[i, jj], f"{j}_rtc": rtc[i, jj], f"{j}_out": out[i, jj], f"{j}_goal": goal[i, jj], f"{j}_present": pres[i, jj]})
                    r.update(fkz_rtc=float(fkz(rtc[i, :5])[0]), fkz_out=float(fkz(out[i, :5])[0]), fkz_present=float(fkz(pres[i, :5])[0]))
                    rows.append(r)
                S = pd.DataFrame(rows)
                S.to_csv(AB / f"p16_sync_{tag}_{k}.csv", index=False)
                pre = slice(max(0, tc - 30), tc)
                e = {"tag": tag, "cond": "ON" if G == "A" else "OFF", "event": k, "c": c, "on": on, "tc": tc, "on_minus_tc": None if on is None else on - tc,
                     "bottom": None if c is None else float(g_state[c:c + 30].min())}
                for jj, j in enumerate(J[:5]):
                    e[f"{j}_out_minus_rtc_mean"] = float(np.mean(out[pre, jj] - rtc[pre, jj]))
                    e[f"{j}_out_minus_rtc_absmed"] = float(np.median(np.abs(out[pre, jj] - rtc[pre, jj])))
                    e[f"{j}_rtc_minus_present_tc"] = float(rtc[tc, jj] - pres[tc, jj])
                    e[f"{j}_out_minus_present_tc"] = float(out[tc, jj] - pres[tc, jj])
                    e[f"{j}_rtc_minus_rawchunk_absmed"] = float(np.nanmedian(np.abs(rtc[pre, jj] - off[pre, jj])))
                zp = fkz(pres[:, :5])
                e.update(fk_dz_rtc_vs_present_tc=float(fkz(rtc[tc, :5])[0] - zp[tc]), fk_dz_out_vs_present_tc=float(fkz(out[tc, :5])[0] - zp[tc]),
                         fk_present_z_drop_after_tc=float(zp[tc] - zp[tc:min(n, tc + 16)].min()),
                         fk_present_vz_tc_cm_s=float((zp[tc] - zp[max(0, tc - 6)]) / (min(6, tc) / 30)) if tc else np.nan)
                # 계획: tc 의 chunk
                kc, ic = int(t.pop_chunk[tc]), int(t.pop_idx[tc])
                P = proc[kc]
                zpl = fkz(P[:, :5])
                rem = np.arange(ic, 50)
                e.update(plan_chunk=kc, plan_idx_at_tc=ic, plan_z_at_tc=float(zpl[ic]), plan_z_min_after=float(zpl[rem].min()),
                         plan_z_min_idx=int(rem[np.argmin(zpl[rem])]), plan_descent_left_cm=float(zpl[ic] - zpl[rem].min()),
                         plan_descent_left_beyond29_cm=float(zpl[min(max(ic, 29), 49)] - zpl[rem].min()) if ic <= 49 else np.nan)
                gp = P[:, 5]
                gc = np.where(gp < np.maximum.accumulate(gp) - 3)[0]  # chunk 전체에서 계획된 그리퍼 닫힘 시작 index
                e["plan_grip_close_idx"] = int(gc[0]) if len(gc) else None
                if f"rtc_off_c{kc:05d}" in RZ:
                    O = RZ[f"rtc_off_c{kc:05d}"]
                    zo = fkz(O[:, :5])
                    go = np.where(O[:, 5] < np.maximum.accumulate(O[:, 5]) - 3)[0]
                    e.update(off_plan_z_at_tc=float(zo[ic]), off_plan_descent_left_cm=float(zo[ic] - zo[rem].min()),
                             off_plan_grip_close_idx=int(go[0]) if len(go) else None)
                # 손목 (tc − 30 … tc + 15)
                ww = WV[(WV.frame >= tc - 30) & (WV.frame <= tc + 15)].copy()
                ww["tag"], ww["event"], ww["frame_rel"] = tag, k, ww.frame - tc
                wr_rows.append(ww)
                w0 = ww.iloc[(ww.frame_rel.abs()).argsort()[:1]]
                if len(w0) and bool(w0.w_vis.iloc[0]):
                    e.update(wrist_u_tc=float(w0.w_u.iloc[0]), wrist_v_tc=float(w0.w_v.iloc[0]), wrist_area_tc=float(w0.w_area.iloc[0]),
                             wrist_edge_tc=bool(w0.w_edge.iloc[0]))
                    v = float(w0.w_v.iloc[0])
                    e["wrist_depth_tc"] = "앞쪽 (덜 다가감)" if v < H["w_v"][0] - 0.02 else ("아래쪽 가장자리" if v > H["w_v"][1] + 0.02 else "사람 범위 안")
                    u = float(w0.w_u.iloc[0])
                    e["wrist_lr_tc"] = "판단 불가 (테두리)" if bool(w0.w_edge.iloc[0]) else ("중앙" if H["w_u"][0] - 0.02 <= u <= H["w_u"][1] + 0.02 else ("화면 왼쪽" if u < H["w_u"][0] else "화면 오른쪽"))
                else:
                    e["wrist_depth_tc"] = e["wrist_lr_tc"] = "판단 불가 (큐브 안 보임)"
                if k == "lost":
                    for dt in (-30, -15, 0, 15, 30, 60, 90, 150):
                        i = min(max(0, tc + dt), n - 1)
                        kc2, ic2 = int(t.pop_chunk[i]), int(t.pop_idx[i])
                        sw_rows.append(dict(tag=tag, t_rel_s=dt / 30, pan_state=pres[i, 0], pan_rtc=rtc[i, 0], pan_raw_chunk=off[i, 0],
                                            plan_pan_idx49_minus_state=float(proc[kc2][49, 0] - pres[i, 0]), grip_state=pres[i, 5]))
                    e["pan_state_end"] = float(pres[-1, 0])
                    e["pan_state_at_lost"] = float(pres[tc, 0])
                    hit = np.where(pres[:, 0] <= -105)[0]
                    e["t_reach_minus105_s"] = float((hit[0] - tc) / 30) if len(hit) else None
                    e["pan_cmd_min"] = float(rtc[:, 0].min())
                ev_rows.append(e)
    E = pd.DataFrame(ev_rows)
    E.to_csv(AB / "p16_events.csv", index=False)
    pd.concat(wr_rows).to_csv(AB / "p16_wrist.csv", index=False)
    SW = pd.DataFrame(sw_rows)
    SW.to_csv(AB / "p16_sweep.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 60)
    print(E.round(2).T.to_string())
    print(SW.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
