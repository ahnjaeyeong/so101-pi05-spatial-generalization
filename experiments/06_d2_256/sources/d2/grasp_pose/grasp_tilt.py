"""파지 자세(그리퍼 기울기) — 관절 데이터 + URDF FK, CPU 만 (영상·GPU 안 씀).

FK: ~/Ros2/ros2_ws/src/twin_description/urdf/so101_new_calib.urdf (range_compare_20261021/fk.py 의 CHAIN).
관절값 → URDF 각: 규약 A = lerobot 도 그대로 (0° = 캘리브레이션 범위 중앙. twin_backend/servo_map.py 와 같은 규약)
                 규약 B = A + (범위중앙 − homing 자세) 관절별 (range_compare_20261021/calibration_compare.csv, 팔마다 다름)
기울기 정의 (wrist_roll 과 무관하게):
  접근축 a = wrist_roll 관절 바로 뒤 프레임의 −z (roll 회전축, 손가락 끝 쪽). gripper_frame_link 는 이 축에서 4.6° 벗어나 있어 쓰지 않는다.
  tilt   = a 와 수직 아래(−z_base) 사이 각. 0° = 수직으로 내려 잡음 (인형뽑기), 90° = 수평
  pitch_r = a 를 (반지름, 수직) 평면에 투영한 기울기, + = 손가락 끝이 로봇에서 먼 쪽을 향함 (밖으로 기울임)
  lean_t  = a 를 (접선, 수직) 평면에 투영한 기울기, + = 로봇 왼쪽(반시계)으로 기울임
  wrist_roll 은 a 둘레 회전이라 tilt/pitch_r/lean_t 를 바꾸지 않는다 (아래 roll_invariance 로 확인).
검증 (규약 고르기): 파지 순간 손가락 끝(gripper_frame_link) 높이가 물체 높이로 일정해야 한다 → 높이 SD 와 거리와의 상관.
이벤트: ~/so101_runs/reference/aswin_task2_compare/demo_kinematics_events.csv (닫힘 프레임 c; 우리 첫 파지, 레퍼런스 T2 는 모든 닫힘)
출력: tilt_events.csv, tilt_summary.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
sys.path.insert(0, str(HOME / "so101_runs/reference/range_compare_20261021"))
sys.path.insert(0, str(HOME / "so101_runs/reference/aswin_task2_compare"))
import fk  # noqa: E402
import demo_kinematics as DK  # noqa: E402

OUT = Path(__file__).resolve().parent
J5 = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
CAL = pd.read_csv(HOME / "so101_runs/reference/range_compare_20261021/calibration_compare.csv").set_index("joint")
SHIFT = {"ours_d2": np.array([CAL.loc[j, "our_mid_minus_home_deg"] for j in J5]),
         "ref": np.array([CAL.loc[j, "ref_mid_minus_home_deg"] for j in J5])}


def frames(deg):
    """deg (N,5) → 접근축 a (N,3), 손가락 끝 p_tip (N,3) m, wrist_roll 관절 위치 (N,3)."""
    deg = np.atleast_2d(deg)
    n = len(deg)
    R = np.repeat(np.eye(3)[None], n, 0)
    p = np.zeros((n, 3))
    a = pw = None
    for j in fk.CHAIN:
        p = p + R @ j["xyz"]
        R = R @ j["R"]
        if j["type"] == "revolute":
            if j["name"] == "wrist_roll":
                pw = p.copy()
            R = R @ fk.axis_rot(j["axis"], np.deg2rad(deg[:, J5.index(j["name"])]))
            if j["name"] == "wrist_roll":
                a = -R[:, :, 2]
    return a, p, pw


def tilt_terms(a, tip):
    down = np.array([0, 0, -1.0])
    tilt = np.degrees(np.arccos(np.clip(a @ down, -1, 1)))
    ur = tip[:, :2] / np.linalg.norm(tip[:, :2], axis=1, keepdims=True)
    ut = np.stack([-ur[:, 1], ur[:, 0]], 1)
    ah = a[:, :2]
    v = -a[:, 2]
    pitch_r = np.degrees(np.arctan2((ah * ur).sum(1), v))
    lean_t = np.degrees(np.arctan2((ah * ut).sum(1), v))
    return tilt, pitch_r, lean_t


def main():
    E = pd.read_csv(HOME / "so101_runs/reference/aswin_task2_compare/demo_kinematics_events.csv")
    E = E[E.seg_len_s > 0.5].reset_index(drop=True)
    d2 = DK.load(DK.C.D2 / "dataset")
    ref = {}
    for task in ("task1-single-sponge-no-distractors", "task2-multiple-sponges-no-distractors", "task3-single-sponge-with-distractors"):
        for split, tag in (("fixed-locations", "K"), ("random-locations", "R")):
            ref[f"T{task[4]}{tag}"] = DK.load(DK.REF / task / split)
    rows = []
    for _, r in E.iterrows():
        s, _ = d2[r.ep] if r.src == "ours_d2" else ref[r.group][r.ep]
        c = int(r.frame)
        seg0 = c - int(round(r.seg_len_s * 30))
        for conv in ("A", "B"):
            for lag in (0, 30, 60, 90):
                f = c - lag
                if f < seg0:
                    continue
                q = s[[f], :5] + (SHIFT[r.src] if conv == "B" else 0)
                a, tip, _ = frames(q)
                t, pr, lt = tilt_terms(a, tip)
                rows.append(dict(src=r.src, group=r.group, ep=r.ep, event=r.event, frame=f, lag=lag, conv=conv,
                                 tilt=t[0], pitch_r=pr[0], lean_t=lt[0], tip_z_cm=tip[0, 2] * 100,
                                 tip_r_cm=float(np.hypot(*tip[0, :2])) * 100, roll=s[f, 4], wrist_flex=s[f, 3],
                                 lift=s[f, 1], elbow=s[f, 2], roll_change=abs(s[c, 4] - s[seg0, 4])))
    T = pd.DataFrame(rows)
    T.to_csv(OUT / "tilt_events.csv", index=False)
    S = {}
    # roll 무관성: 같은 자세에서 roll 만 −60…+60 바꿔 tilt 변화
    q0 = np.array([[0, -20, 40, 70, 0]], float)
    tt = [tilt_terms(*[frames(q0 + [0, 0, 0, 0, rr])[i] for i in (0, 1)])[0][0] for rr in (-60, -30, 0, 30, 60)]
    S["roll_invariance_tilt_range_deg"] = float(np.ptp(tt))
    for conv in ("A", "B"):
        for src, g in T[(T.conv == conv) & (T.lag == 0)].groupby("src"):
            S[f"{src}|{conv}|tip_z"] = dict(n=len(g), sd_cm=float(g.tip_z_cm.std()), median_cm=float(g.tip_z_cm.median()),
                                            corr_range=float(np.corrcoef(g.tip_r_cm, g.tip_z_cm)[0, 1]))
    for conv in ("A", "B"):
        for (src, grp), g in T[(T.conv == conv) & (T.lag == 0)].groupby(["src", "group"]):
            S[f"{src}|{grp}|{conv}|at_close"] = dict(n=len(g), tilt_med=float(g.tilt.median()), tilt_p10=float(g.tilt.quantile(.1)),
                                                     tilt_p90=float(g.tilt.quantile(.9)), pitch_r_med=float(g.pitch_r.median()),
                                                     lean_t_med=float(g.lean_t.median()), lean_t_absmed=float(g.lean_t.abs().median()),
                                                     roll_change_med=float(g.roll_change.median()),
                                                     corr_tilt_rollchange=float(np.corrcoef(g.tilt, g.roll_change)[0, 1]),
                                                     corr_tilt_range=float(np.corrcoef(g.tilt, g.tip_r_cm)[0, 1]))
    json.dump(S, open(OUT / "tilt_summary.json", "w"), indent=1)
    print(json.dumps(S, indent=1))


if __name__ == "__main__":
    main()
