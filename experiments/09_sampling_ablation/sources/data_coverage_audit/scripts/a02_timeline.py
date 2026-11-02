"""02 시간별 서보 타임라인 + 판별 이벤트 (읽기만 함, CPU).

출력
  02_servo_timeline.parquet  (긴 형식: episode × frame × servo)  — 요청 표의 열
  tables/a02_frames.parquet  (넓은 형식: episode × frame) — 관절 · FK 집게 끝 · 큐브 상대 오차 · 구간 이름
  tables/a02_events.csv      판별 이벤트 프레임 · pan/집게 끝 정렬 지표
  tables/a02_lag.csv         관절별 명령(action) → 측정(state) 지연 · 추종 오차
TCP = ac.tcp (pan 축 극좌표 모델, 반지름 편향 dA 와 베이스는 a00_tcp_model.py 결과). 파지 순간 측정 바닥: 접선 SD ≈ 0.59 cm, 반지름 SD ≈ 0.79 cm (CV).
정의
  measured_position = observation.state (팔로워 Present_Position, 프레임 처음에 읽음)
  commanded_position = action (리더 위치 = 같은 tick 에 팔로워 Goal_Position 으로 보낸 값; 녹화 때 max_relative_target=None 이라 자르지 않음)
  estimated_velocity = 측정 위치 중앙 차분 / (1/30 s)  ← 추정값 (실제 주기 29.88–29.94 Hz, a01)
이벤트 (프레임)
  onset      리더(action) 관절 5개 중 하나가 처음 값에서 2° 넘게 벗어난 첫 프레임 (policy_probe.move_start 와 같다)
  grasp (c)  check_dataset.first_grasp (팔로워 그리퍼 처음 큰 닫힘)
  close_start c 직전 그리퍼가 가장 열린 프레임 (c 에서 거꾸로 그리퍼가 줄지 않는 동안)
  pan_reach2 / pan_settle2   pan 이 pan(c) ±2° 에 처음 들어온 / 계속 머물기 시작한 프레임 (±1, ±3 도 같이)
  pan_sub1_end  pan 첫 하위 움직임 끝 (속도 봉우리 뒤 max(5°/s, 10%) 아래)
  reach2     집게 끝 수평 위치가 집게 끝(c) 2 cm 안에 계속 머물기 시작한 프레임 (접근 끝)
  lift       c 뒤 집게 끝 z 가 z(c) + 3 cm 를 처음 넘은 프레임
  release    lift 뒤 그리퍼가 c..lift 중앙값 + 5 넘게 처음 열린 프레임 (상자에 놓을 때 +6–10 만 열림)
구간 (프레임별 phase): idle < onset ≤ approach < reach2 ≤ fine_align < close_start ≤ closing ≤ c < lift_phase ≤ lift < transport ≤ release < retreat
사용: PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a02_timeline.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import ac

sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))


def lag_stats(s, a, j, maxlag=15):
    vs = np.gradient(s[:, j])
    va = np.gradient(a[:, j])
    if np.std(va) < 1e-6 or np.std(vs) < 1e-6:
        return np.nan, np.nan
    cc = [np.corrcoef(va[: len(va) - L], vs[L:])[0, 1] for L in range(maxlag + 1)]
    L = int(np.nanargmax(cc))
    return L, float(cc[L])


def main():
    data = ac.load_d2()
    T = ac.cube_table()
    meta = ac.episodes_meta()
    G0 = pd.read_csv(ac.D2 / "diag_grasp_bias/grasp_train.csv")
    import check_dataset as cd
    long_rows, wide, ev, lagrows = [], [], [], []
    for e in range(256):
        s, a, ts, fi, ix = data[e]
        n = len(s)
        r = T.loc[e]
        cx, cy = r.cube_x, r.cube_y
        ut, ur = ac.axes(cx, cy)
        P = ac.tcp(s)            # pan 축 극좌표 TCP (a00_tcp_model)
        _, Rm = ac.tip(s)        # 방향 (집게 축) 만 FK 회전에서
        Pa = ac.tcp(a)
        rel = P[:, :2] - [cx, cy]
        e_t, e_r = rel @ ut, rel @ ur
        rel_a = Pa[:, :2] - [cx, cy]
        tip_bear = ac.bearing(P[:, 0], P[:, 1])
        dbear = ac.wrap180(tip_bear - r.bearing)
        vel = np.gradient(s, axis=0) * ac.FPS
        c = cd.first_grasp(s)
        on = ac.onset(a[:, :5], 2.0)
        on_s = ac.onset(s[:, :5], 2.0)
        g = s[:, 5]
        cs = c
        while cs > 0 and g[cs - 1] >= g[cs] - 0.3:
            cs -= 1
        # 닫힘 이벤트 (재시도 포함)
        cev = C_close = ac.C.close_events(g)
        # lift / release
        z = P[:, 2]
        up = np.where(z[c:] >= z[c] + 3.0)[0]
        lift = int(c + up[0]) if len(up) else None
        rel_f = None
        if lift is not None:
            base_g = np.median(g[c:lift + 1])
            op = np.where(g[lift:] >= base_g + 5)[0]
            rel_f = int(lift + op[0]) if len(op) else None
        # 첫 파지 성공 (그리퍼가 큐브에 막혔는가): c+5..c+20 그리퍼 state 중앙값, action 과 차이
        w = slice(c + 5, min(n, c + 21))
        g_hold = float(np.median(g[w]))
        g_gap = float(np.median(g[w] - a[w, 5]))
        n_close_before_lift = sum(1 for k in cev if lift is None or k <= lift)
        pan = s[:, 0]
        ev_row = dict(ep=e, group=r.group, task=r.task, mode=r["mode"], n=n, len_s=n / ac.FPS, onset=on, onset_state=on_s, grasp=c,
                      grasp_prev=int(G0.loc[e, "grasp_f"]), close_start=cs, n_close_events=len(cev), n_close_before_lift=n_close_before_lift,
                      lift=lift, release=rel_f, g_hold=g_hold, g_gap=g_gap, g_open_max_pre=float(g[on:c + 1].max()) if on is not None else np.nan)
        for tol in (1, 2, 3):
            ev_row[f"pan_reach{tol}"] = ac.first_reach_index(pan, c, tol, on)
            ev_row[f"pan_settle{tol}"] = ac.settle_index(pan, c, tol, on)
        d_h = np.hypot(*(P[:, :2] - P[c, :2]).T)
        for tol in (1, 2, 3):
            ev_row[f"reach{tol}"] = ac.settle_index(d_h, c, tol, on) if True else None
        # settle_index 는 x[c] 기준 차이 — d_h[c]=0 이라 그대로 쓴다
        # pan 첫 움직임
        pm = np.where(np.abs(pan[on:c + 1] - pan[on]) > 1.0)[0]
        f_pm = int(on + pm[0]) if len(pm) else None
        sub1 = ac.first_submovement(pan, f_pm if f_pm is not None else on, c)
        ev_row.update(pan0=float(pan[0]), pan_on=float(pan[on]), pan_c=float(pan[c]), pan_exp=float(r.pan_expected),
                      pan_first_move=f_pm, pan_first_dir=float(np.sign(pan[f_pm] - pan[on])) if f_pm is not None else 0.0,
                      pan_target_dir=float(np.sign(pan[c] - pan[on])), pan_sub1_end=sub1, pan_sub1_amount=float(pan[sub1] - pan[on]),
                      pan_total=float(pan[c] - pan[on]))
        # 파지 순간 FK 오차 · 시간 전 상태
        ev_row.update(e_t_c=float(e_t[c]), e_r_c=float(e_r[c]), dbear_c=float(dbear[c]), tip_z_c=float(z[c]), roll_c=float(s[c, 4]),
                      tip_x_c=float(P[c, 0]), tip_y_c=float(P[c, 1]))
        for sec in (5, 3, 2, 1):
            f = c - sec * ac.FPS
            if f >= 0:
                ev_row[f"e_t_m{sec}"] = float(e_t[f])
                ev_row[f"e_r_m{sec}"] = float(e_r[f])
                ev_row[f"dpan_m{sec}"] = float(pan[f] - pan[c])
                ev_row[f"roll_m{sec}"] = float(s[f, 4])
                ev_row[f"dist_m{sec}"] = float(d_h[f])
                ev_row[f"dz_m{sec}"] = float(z[f] - z[c])
            else:
                for k in ("e_t", "e_r", "dpan", "roll", "dist", "dz"):
                    ev_row[f"{k}_m{sec}"] = np.nan
        ev.append(ev_row)
        # 구간 이름
        ph = np.full(n, "retreat", dtype=object)
        reach = ev_row["reach2"]
        b = [0, on, reach, max(reach, cs), c + 1, (lift + 1) if lift is not None else n, (rel_f + 1) if rel_f is not None else n]
        names = ["idle", "approach", "fine_align", "closing", "lift", "transport"]
        for k, nm in enumerate(names):
            lo, hi = b[k], b[k + 1]
            if hi > lo:
                ph[lo:hi] = nm
        # 넓은 표
        W = pd.DataFrame({"ep": e, "frame": fi, "index": ix, "timestamp": ts, "t_rel": ts - ts[0], "t_to_grasp": (c - fi) / ac.FPS, "phase": ph})
        for j, nm in enumerate(ac.JOINTS):
            W[f"s_{nm}"] = s[:, j]
            W[f"a_{nm}"] = a[:, j]
            W[f"v_{nm}"] = vel[:, j]
        W["tip_x"], W["tip_y"], W["tip_z"] = P.T
        W["tip_x_a"], W["tip_y_a"] = Pa[:, 0], Pa[:, 1]
        W["e_t"], W["e_r"] = e_t, e_r
        W["e_t_a"], W["e_r_a"] = rel_a @ ut, rel_a @ ur
        W["dbear"] = dbear
        W["dist_to_grasp_tip"] = d_h
        W["approach_dir_deg"] = np.degrees(np.arctan2(*(np.gradient(P[:, :2], axis=0) @ np.column_stack([ut, ur])).T[::-1]))  # 수평 이동 방향: 0 = +반지름, +90 = +접선
        W["gripper_axis_yaw"] = np.degrees(np.arctan2(Rm[:, 1, 0], Rm[:, 0, 0]))
        wide.append(W)
        # 긴 표
        row0 = meta[meta.episode_index == e].iloc[0]
        for j, nm in enumerate(ac.JOINTS):
            pd_ = np.r_[np.nan, np.diff(s[:, j])]
            long_rows.append(pd.DataFrame({
                "episode_id": e, "task_type": f"{r.task}-{r['mode']}", "frame_index": fi, "timestamp": ts, "relative_time": ts - ts[0],
                "servo_name": nm, "unit": "deg" if j < 5 else "gripper_0_100",
                "measured_position": s[:, j], "commanded_position": a[:, j], "action_value": a[:, j],
                "position_delta": pd_, "estimated_velocity": vel[:, j], "velocity_is_estimate": True,
                "tracking_error_cmd_minus_meas": a[:, j] - s[:, j], "phase": ph,
                "front_video": f"videos/observation.images.front/chunk-{int(row0['videos/observation.images.front/chunk_index']):03d}/file-{int(row0['videos/observation.images.front/file_index']):03d}.mp4",
                "front_video_ts": float(row0["videos/observation.images.front/from_timestamp"]) + fi / ac.FPS,
                "wrist_video": f"videos/observation.images.wrist/chunk-{int(row0['videos/observation.images.wrist/chunk_index']):03d}/file-{int(row0['videos/observation.images.wrist/file_index']):03d}.mp4",
                "wrist_video_ts": float(row0["videos/observation.images.wrist/from_timestamp"]) + fi / ac.FPS}))
            mv = np.abs(vel[:, j]) > (10 if j < 5 else 20)
            L, cc = lag_stats(s, a, j)
            err = a[:, j] - s[:, j]
            lagrows.append(dict(ep=e, group=r.group, joint=nm, lag_frames=L, lag_corr=cc, err_mean=float(err.mean()), err_abs_mean=float(np.abs(err).mean()),
                                err_abs_p95=float(np.percentile(np.abs(err), 95)), err_abs_mean_moving=float(np.abs(err[mv]).mean()) if mv.any() else np.nan,
                                err_mean_static=float(err[~mv].mean()) if (~mv).any() else np.nan))
        if e % 32 == 0:
            print(e, flush=True)
    L = pd.concat(long_rows, ignore_index=True)
    L["task_type"] = L.task_type.astype("category")
    L["servo_name"] = L.servo_name.astype("category")
    L["phase"] = L.phase.astype("category")
    L.sort_values(["episode_id", "frame_index", "servo_name"]).to_parquet(ac.AUD / "02_servo_timeline.parquet", index=False)
    Wd = pd.concat(wide, ignore_index=True)
    Wd = Wd.merge(T[["ep", "group", "task", "mode", "cube_x", "cube_y", "bearing", "range_cm", "plan_K", "yaw_used", "roll_need_rel"]], on="ep")
    Wd.to_parquet(ac.TAB / "a02_frames.parquet", index=False)
    E = pd.DataFrame(ev)
    E.to_csv(ac.TAB / "a02_events.csv", index=False)
    pd.DataFrame(lagrows).to_csv(ac.TAB / "a02_lag.csv", index=False)
    print("long", L.shape, "wide", Wd.shape)
    print("grasp == prev", int((E.grasp == E.grasp_prev).sum()))
    print(E.describe().T.to_string())


if __name__ == "__main__":
    main()
