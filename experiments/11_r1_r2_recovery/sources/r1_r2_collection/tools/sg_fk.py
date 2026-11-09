"""SG50 수평계용 FK — ~/so101_runs/reference/range_compare_20261021/fk.py 를 그대로 옮김 (2026-11-06) + 그리퍼 기울기 함수.
URDF: ~/Ros2/ros2_ws/src/twin_description/urdf/so101_new_calib.urdf (URDF 0 = lerobot 보정 가운데, deg→rad). 절대값에는 치우침이 있을 수 있음 (config sg50.tilt_zero_deg 로 0 점 보정)."""
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

URDF = Path.home() / "Ros2/ros2_ws/src/twin_description/urdf/so101_new_calib.urdf"
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def rpy_mat(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def axis_rot(ax, q):
    """Rotation matrices (N,3,3) about unit axis ax by angles q (N,)."""
    ax = np.asarray(ax, float) / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    q = np.asarray(q)[:, None, None]
    return np.eye(3) + np.sin(q) * K + (1 - np.cos(q)) * (K @ K)


def load_chain(tip="gripper_frame_link"):
    root = ET.parse(URDF).getroot()
    by_child = {j.find("child").get("link"): j for j in root.findall("joint")}
    chain, link = [], tip
    while link in by_child:
        j = by_child[link]
        o = j.find("origin")
        xyz = np.array([float(v) for v in o.get("xyz").split()])
        rpy = [float(v) for v in o.get("rpy").split()]
        ax = j.find("axis")
        chain.append(dict(name=j.get("name"), type=j.get("type"), xyz=xyz, R=rpy_mat(*rpy),
                          axis=None if ax is None else [float(v) for v in ax.get("xyz").split()]))
        link = j.find("parent").get("link")
    return chain[::-1]


CHAIN = load_chain()


def fk(deg):
    """deg: (N,>=5) lerobot degrees [pan, lift, elbow, wflex, wroll]. Returns tip xyz (N,3) m in base_link frame and R (N,3,3)."""
    deg = np.atleast_2d(deg)
    n = len(deg)
    R = np.repeat(np.eye(3)[None], n, 0)
    p = np.zeros((n, 3))
    for j in CHAIN:
        p = p + R @ j["xyz"]
        R = R @ j["R"]
        if j["type"] == "revolute":
            q = np.deg2rad(deg[:, JOINTS.index(j["name"])])
            R = R @ axis_rot(j["axis"], q)
    return p, R


J5 = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def tool_tilt(state):
    """팔로워 관절값 (dict '<joint>.pos' 또는 '<joint>', 또는 [pan, lift, elbow, wflex, wroll] °) → 그리퍼 축 기울기 °.
    반환 (앞뒤, 옆, 전체): 앞뒤 + = 손끝이 로봇에서 먼 쪽 (바깥) 으로, − = 로봇 쪽으로. 옆은 5 축 팔이라 거의 0. 수직 = 0."""
    if isinstance(state, dict):
        try:
            deg = [float(state.get(f"{j}.pos", state.get(j))) for j in J5]
        except (TypeError, ValueError):
            return None
    else:
        deg = [float(v) for v in list(state)[:5]]
    p, R = fk(np.array([deg], float))
    a = R[0][:, 2]  # 끝 좌표계 z 축 = 손끝 방향 (수직이면 (0, 0, −1))
    xy = p[0][:2]
    r = xy / (np.linalg.norm(xy) or 1.0)
    t = np.array([-r[1], r[0]])
    fwd = float(np.degrees(np.arcsin(np.clip(a[:2] @ r, -1, 1))))
    side = float(np.degrees(np.arcsin(np.clip(a[:2] @ t, -1, 1))))
    tot = float(np.degrees(np.arccos(np.clip(-a[2], -1, 1))))
    return fwd, side, tot
