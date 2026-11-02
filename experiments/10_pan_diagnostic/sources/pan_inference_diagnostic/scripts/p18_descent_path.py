"""p18 K1 필터 켬/끔: 첫 닫힘 전 하강 경로 비교 (읽기만, CPU). 로봇 연결 없음.

창: 그리퍼 명령 닫힘 시작 tc (p16) 앞 2 s. 하강 시작 s0 = 그 창에서 present FK z 가 가장 높은 틱. 구간 [s0, tc].
신호 (관절 5 개 + FK):
  raw_chunk (RTC 끔 반사실, p05) · rtc (queue 출력, 실측) · out (필터 뒤, 실측) · goal (보낸 Goal, 실측) · present (실측)
  cf_out = 반사실 필터: 켬 실행은 필터를 뺀 명령 = rtc, 끔 실행은 같은 rtc 열을 arm_filter.ArmFilter (α 0.5, 판 시작 state 로 초기화) 에 통과시킨 값.
          명령 열만의 반사실이다 — 팔이 그 명령을 따라 실제로 움직였을 경로 · 결과가 아니다.
FK 경로 지표 (ac.tcp, 짧은 구간 상대 이동만. K1 에서 절대 위치가 손목 영상과 4–5 cm 어긋나므로 절대값은 쓰지 않음):
  H = 수평 순이동 (cm), V = 수직 순하강 (cm), H/V, 수직에서 기운 각 atan(H/V), 반지름 · 접선 성분 (s0 의 TCP 방향 기준),
  경로 길이, 직선성 = 순이동 / 경로 길이, 수평 경로 길이 / 수직 경로 길이
관절 타이밍: 구간 안 관절별 총변화, 50 % 도달 시각 (s0 기준 s), present 가 rtc 를 따라가는 최적 지연 (틱), 필터 속도 제한 작동 틱, clamp 작동 틱
영상 (dataset 영상, 프레임마다):
  손목: 큐브 중심 u · v (화면 비율) · 넓이 — 하강 동안의 변화 (화면 이동량일 뿐 실제 거리 아님)
  front: 큐브 둘레 반지름 90 px 안 어두운 픽셀 (로봇 · 그리퍼) 의 중심 − 큐브 중심 (px, 화면 평면, 높이 차 · 원근 보정 없음)
출력: filter_ab/p18_paths.csv (이벤트 × 신호), p18_joints.csv, p18_video.csv (프레임별), p18_video_summary.csv
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p18_descent_path.py
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cube_coords as CC  # noqa: E402
import p14_grasp_analysis as P14  # noqa: E402
import p16_k1_pregrasp as P16  # noqa: E402

sys.path.insert(0, str(CC.D2 / "eval"))
from arm_filter import ArmFilter  # noqa: E402

ac, C = CC.ac, CC.C
AB = CC.D2 / "pan_inference_diagnostic/filter_ab"
ROLL = CC.D2 / "eval/rollouts"
J = P16.J
J5 = J[:5]


def path_metrics(Q):
    P = ac.tcp(Q[:, :5])
    d = np.diff(P, axis=0)
    H = float(np.linalg.norm(P[-1, :2] - P[0, :2]))
    V = float(P[0, 2] - P[-1, 2])
    ur = (P[0, :2] - ac.BASE) / np.linalg.norm(P[0, :2] - ac.BASE)
    ut = np.array([-ur[1], ur[0]])
    dxy = P[-1, :2] - P[0, :2]
    L = float(np.linalg.norm(d, axis=1).sum())
    return dict(H_cm=H, V_cm=V, H_over_V=H / V if V > 0.2 else np.nan, tilt_deg=math.degrees(math.atan2(H, V)) if V > 0.2 else np.nan,
                radial_cm=float(dxy @ ur), tangential_cm=float(dxy @ ut), path_len_cm=L,
                straightness=float(np.linalg.norm(P[-1] - P[0]) / L) if L > 0 else np.nan,
                horiz_path_cm=float(np.linalg.norm(d[:, :2], axis=1).sum()), vert_path_cm=float(np.abs(d[:, 2]).sum()))


def best_lag(cmd, pres):
    best, be = 0, 1e9
    for L in range(0, 11):
        e = np.mean(np.abs(pres[L:] - cmd[: len(cmd) - L])) if len(cmd) - L > 5 else 1e9
        if e < be:
            best, be = L, e
    return best


def front_offsets(img, u0, v0, r=90):
    import cv2
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    dark = (hsv[..., 2] < 90) & (hsv[..., 1] < 90)
    h, w = dark.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m = dark & ((xx - u0) ** 2 + (yy - v0) ** 2 <= r * r)
    if m.sum() < 30:
        return None
    return float(xx[m].mean() - u0), float(yy[m].mean() - v0), int(m.sum())


def main():
    E = pd.read_csv(AB / "p16_events.csv")
    E = E[E.event.astype(str) != "lost"]
    keys = [f"{j}.pos" for j in J]
    cache, prow, jrow, vrow, vsum = {}, [], [], [], []
    for _, e in E.iterrows():
        G, epi, k, tc = e.tag[0], int(e.tag[1]), str(e.event), int(e.tc)
        run = P16.RUNS[G]
        ep = sorted(pd.read_csv(ROLL / run / "filter_log.csv", usecols=["episode"]).episode.unique())[epi]
        f, t, RZ, proc = P16.load(run, ep)
        rtc = f[[f"raw_{j}" for j in J]].values.astype(float)
        out = f[[f"out_{j}" for j in J]].values.astype(float)
        goal = t[[f"sent_{j}" for j in J]].values.astype(float)
        pres = t[[f"present_{j}" for j in J]].values.astype(float)
        off = np.array([RZ[f"rtc_off_c{int(c):05d}"][int(i)] if f"rtc_off_c{int(c):05d}" in RZ else np.full(6, np.nan)
                        for c, i in zip(t.pop_chunk, t.pop_idx)])
        # 반사실 필터
        if G == "A":
            cf = rtc.copy()
            chk = ArmFilter(keys, enabled=True)
            rep = np.array([chk.step(rtc[i], pres[i] if i == 0 else None)[0] for i in range(len(rtc))])
            refilter_err = float(np.abs(rep[:, :5] - out[:, :5]).max())
        else:
            af = ArmFilter(keys, enabled=True)
            cf = np.array([af.step(rtc[i], pres[i] if i == 0 else None)[0] for i in range(len(rtc))])
            refilter_err = None
        lo = max(0, tc - 60)
        zp = ac.tcp(pres[lo:tc + 1, :5])[:, 2]
        s0 = lo + int(np.argmax(zp))
        seg = slice(s0, tc + 1)
        base = dict(tag=e.tag, event=k, cond="ON" if G == "A" else "OFF", bottom=e.bottom, s0=s0, tc=tc, descent_s=(tc - s0) / 30,
                    refilter_reproduce_maxerr=refilter_err)
        for nm, Q in (("raw_chunk", off), ("rtc", rtc), ("out", out), ("goal", goal), ("present", pres), ("cf_out", cf)):
            if np.isnan(Q[seg, :5]).any():
                continue
            prow.append(dict(base, signal=nm, **path_metrics(Q[seg])))
        fl = f.iloc[s0:tc + 1]
        for jj, j in enumerate(J5):
            r = dict(base, joint=j)
            for nm, Q in (("rtc", rtc), ("out", out), ("present", pres), ("cf_out", cf)):
                x = Q[seg, jj]
                tot = x[-1] - x[0]
                r[f"{nm}_delta"] = float(tot)
                if abs(tot) > 1.0:
                    prog = (x - x[0]) / tot
                    k50 = np.where(prog >= 0.5)[0]
                    r[f"{nm}_t50_s"] = float(k50[0] / 30) if len(k50) else np.nan
            r["lag_present_vs_rtc"] = best_lag(rtc[lo:tc + 1, jj], pres[lo:tc + 1, jj])
            r["lag_present_vs_out"] = best_lag(out[lo:tc + 1, jj], pres[lo:tc + 1, jj])
            r["vclip_ticks"] = int(fl.vclip_mask.fillna("").map(lambda s, jj=jj: len(s) > jj and s[jj] == "1").sum()) if G == "A" else 0
            r["clamp_ticks"] = int((np.abs(goal[seg, jj] - out[seg, jj]) > 1e-4).sum())
            r["cf_vclip_like_ticks"] = int((np.abs(np.diff(cf[lo:tc + 1, jj])) >= ArmFilter(keys).vmax[jj] - 1e-6).sum())
            jrow.append(r)
        # 영상
        ds = ROLL / run / "dataset"
        f0 = C.frames(ds, epi, "front", 0, 0, cache)[0]
        d0 = CC.detect(f0)
        u0, v0 = d0["u"], d0["v"]
        rows = []
        for fr in range(s0, min(tc + 4, len(pres))):
            w = P14.wrist_measure(C.frames(ds, epi, "wrist", fr, fr, cache)[0])
            fo = front_offsets(C.frames(ds, epi, "front", fr, fr, cache)[0], u0, v0)
            rows.append(dict(base, frame=fr, t_rel_s=(fr - tc) / 30, w_vis=w.get("w_vis"), w_edge=w.get("w_edge"), w_u=w.get("w_u"), w_v=w.get("w_v"),
                             w_area=w.get("w_area"), front_du=fo[0] if fo else None, front_dv=fo[1] if fo else None, front_dark_px=fo[2] if fo else None))
        V = pd.DataFrame(rows)
        vrow.append(V)
        vv = V[(V.w_vis == True) & (V.w_edge == False)]  # noqa: E712
        fv = V.dropna(subset=["front_du"])
        s = dict(base)
        if len(vv) >= 2:
            s.update(w_u_start=vv.w_u.iloc[0], w_u_end=vv.w_u.iloc[-1], w_du=vv.w_u.iloc[-1] - vv.w_u.iloc[0], w_dv=vv.w_v.iloc[-1] - vv.w_v.iloc[0],
                     w_u_path=float(np.abs(np.diff(vv.w_u)).sum()), w_v_path=float(np.abs(np.diff(vv.w_v)).sum()),
                     w_area_ratio=vv.w_area.iloc[-1] / vv.w_area.iloc[0], w_n=len(vv))
            dd = np.hypot(np.diff(vv.w_u), np.diff(vv.w_v))
            s["w_straightness"] = float(math.hypot(s["w_du"], s["w_dv"]) / dd.sum()) if dd.sum() > 0 else np.nan
        if len(fv) >= 2:
            s.update(front_du_start=fv.front_du.iloc[0], front_dv_start=fv.front_dv.iloc[0], front_du_end=fv.front_du.iloc[-1], front_dv_end=fv.front_dv.iloc[-1],
                     front_lateral_change_px=fv.front_du.iloc[-1] - fv.front_du.iloc[0], front_depth_change_px=fv.front_dv.iloc[-1] - fv.front_dv.iloc[0],
                     front_path_px=float(np.hypot(np.diff(fv.front_du), np.diff(fv.front_dv)).sum()))
            s["front_straightness"] = float(math.hypot(s["front_lateral_change_px"], s["front_depth_change_px"]) / s["front_path_px"]) if s["front_path_px"] > 0 else np.nan
        vsum.append(s)
    P = pd.DataFrame(prow)
    P.to_csv(AB / "p18_paths.csv", index=False)
    JR = pd.DataFrame(jrow)
    JR.to_csv(AB / "p18_joints.csv", index=False)
    pd.concat(vrow).to_csv(AB / "p18_video.csv", index=False)
    VS = pd.DataFrame(vsum)
    VS.to_csv(AB / "p18_video_summary.csv", index=False)
    pd.set_option("display.width", 260, "display.max_columns", 40)
    print(P[["tag", "event", "cond", "bottom", "descent_s", "signal", "H_cm", "V_cm", "H_over_V", "tilt_deg", "radial_cm", "tangential_cm", "straightness",
             "horiz_path_cm", "vert_path_cm", "refilter_reproduce_maxerr"]].round(2).to_string(index=False))
    print(JR.round(2).to_string(index=False))
    print(VS.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
