"""SO101 forward kinematics from so101_new_calib.urdf (URDF zero = lerobot calibrated mid, rad = deg*pi/180)."""
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


if __name__ == "__main__":
    print([j["name"] for j in CHAIN])
    for d in ([0, 0, 0, 0, 0], [30, 0, 0, 0, 0], [0, -100, 95, 70, 0]):
        print(d, fk(np.array([d], float))[0].round(3))
