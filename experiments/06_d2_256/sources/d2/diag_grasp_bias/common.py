"""main_k8 d2 파지 편향 진단 공통 함수 (읽기만 함 — 데이터셋·학습·로봇 코드는 건드리지 않는다).

좌표계 (config/redbox8_layouts.yaml, C frame, 단위 cm):
  x = 로봇 → 상자 방향(+), y = 로봇 왼쪽(+).  base_xy_cm = (-31, 11) (pan 으로 맞춘 추정값, 실측 아님).
  bearing b = atan2(y - 11, x + 31) [°], + = 로봇 왼쪽.  pan 기대값 = -b - 1.4  (pan + = 로봇 오른쪽).
  front 영상: 왼쪽 = 로봇 오른쪽.
"""
import csv
import glob
import math
import sys
from pathlib import Path

import numpy as np

HOME = Path.home()
K8 = HOME / "so101_runs/main_k8"
D2 = K8 / "d2"
OUT = D2 / "diag_grasp_bias"
sys.path.insert(0, str(HOME / "so101_boxpick/scripts"))
sys.path.insert(0, str(HOME / "so101_runs/reference/range_compare_20261021"))

import yaml  # noqa: E402

CFG = yaml.safe_load(open(HOME / "so101_boxpick/config/redbox8_layouts.yaml"))
ROB = CFG["robot"]
BASE = np.array(ROB["base_xy_cm"], float)
PAN_SIGN, PAN_OFF = float(ROB["pan_sign"]), float(ROB["pan_offset_deg"])
H = np.array(CFG["camera"]["front_640x480"]["H_cm_to_px"], float)
HINV = np.linalg.inv(H)
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
GRIP = 5

# d2 합친 순서 (description.md 3.2): 0–63 T1-K · 64–127 T1-R · 128–191 T3-K · 192–255 T3-R
SOURCES = [("T1K", "redbox_t1_known"), ("T1R", "redbox_t1_random"), ("T3K", "redbox_t3_known"), ("T3R", "redbox_t3_random")]


def load_known():
    """config 의 K1–K8 (C frame cm)."""
    ks = {}
    for k, v in CFG.get("known_positions", {}).items():
        xy = v.get("xy_cm") if isinstance(v, dict) else v
        if xy is not None:
            ks[k] = (float(xy[0]), float(xy[1]))
    return ks


def bearing(x, y):
    return math.degrees(math.atan2(y - BASE[1], x - BASE[0]))


def rng(x, y):
    return math.hypot(x - BASE[0], y - BASE[1])


def pan_expected(x, y):
    return PAN_SIGN * bearing(x, y) + PAN_OFF


def px_to_cm(u, v):
    p = HINV @ np.array([u, v, 1.0])
    return float(p[0] / p[2]), float(p[1] / p[2])


def cm_to_px(x, y):
    p = H @ np.array([x, y, 1.0])
    return float(p[0] / p[2]), float(p[1] / p[2])


def load_parquet(ds):
    import pandas as pd
    files = sorted(glob.glob(str(Path(ds) / "data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(f, columns=["episode_index", "frame_index", "action", "observation.state"]) for f in files])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float))
    return out


def d2_positions():
    """d2 episode_index → (그룹, 원본 세션, 원본 episode_index, 빨강 (x, y) cm, layout_id, 각도)."""
    out = []
    for grp, sess in SOURCES:
        lay = [r for r in csv.DictReader(open(K8 / sess / "layout.csv")) if r["status"] == "recorded"]
        pos = {}
        for r in csv.DictReader(open(K8 / sess / "qa/positions.csv")):
            if r["color"] == "red" and r["excluded"] != "yes":
                pos.setdefault(int(r["episode_index"]), []).append((float(r["x_cm"]), float(r["y_cm"])))
        for r in lay:
            e = int(r["episode_index"])
            p = pos.get(e)
            out.append(dict(group=grp, session=sess, src_ep=e, layout_id=r["layout_id"], frames_plan=int(r["frames"] or 0),
                            angles=r.get("angles", ""), red=p[0] if p and len(p) == 1 else None, n_red=len(p) if p else 0))
    return out


def first_grasp(g):
    """check_dataset.first_grasp 와 같은 규칙 (그리퍼 state 1D)."""
    import check_dataset as cd
    s = np.zeros((len(g), 6))
    s[:, GRIP] = g
    return cd.first_grasp(s)


def close_events(g, min_drop=8.0, reopen=8.0):
    """그리퍼가 열린 정점에서 크게 닫힌 곳을 모두 (재시도 포함). 각 이벤트 = 닫힘이 거의 끝난 프레임.
    규칙: 지금까지 연 정점에서 max(min_drop, 열린 폭 35%) 넘게 닫히면 이벤트 시작 → 계속 줄어드는 동안 따라가 바닥+2 에 처음 닿은 프레임.
    그 뒤 바닥에서 reopen 이상 다시 열리면 다음 이벤트를 찾는다."""
    g = np.asarray(g, float)
    span = max(1.0, float(np.percentile(g, 99) - g.min()))
    thr = max(min_drop, 0.35 * span)
    ev, i, peak, n = [], 0, g[0], len(g)
    while i < n:
        peak = max(peak, g[i])
        if peak - g[i] >= thr:
            m = i
            while m + 1 < n and g[m + 1] <= g[m] + 0.3:
                m += 1
            bottom = g[m]
            p = int(np.argmax(g[max(0, i - 60): i + 1])) + max(0, i - 60)
            j = p + int(np.argmax(g[p: m + 1] <= bottom + 2))
            ev.append(j)
            k = m
            while k < n and g[k] < bottom + reopen:
                k += 1
            i, peak = k, g[k] if k < n else 0
            continue
        i += 1
    return ev


def red_mask(rgb):
    import pregrasp_angles as PA
    return PA.red_mask_rgb(rgb)


def blobs(mask, min_area=60):
    import cv2
    n, lab, st, cen = cv2.connectedComponentsWithStats(mask)
    return [(int(st[i, cv2.CC_STAT_AREA]), (float(cen[i][0]), float(cen[i][1])), i, lab) for i in range(1, n)
            if st[i, cv2.CC_STAT_AREA] >= min_area]


def frames(ds, ep, cam_key, f0, f1, cache):
    """[f0, f1] 프레임 RGB 목록."""
    import record_ui
    ds = str(ds)
    if ds not in cache:
        cache[ds] = record_ui.load_meta(ds)
    info, eps, cams = cache[ds]
    cam = next(c for c in cams if c.endswith(cam_key))
    row = eps[eps.episode_index == ep].iloc[0]
    t0, fps = float(row[f"videos/{cam}/from_timestamp"]), info["fps"]
    return list(record_ui.iter_frames(record_ui.video_path(ds, info, cam, row), t0 + max(0, f0) / fps, t0 + (f1 + 1) / fps, fps))


def fk_xy(deg5):
    import fk
    p, R = fk.fk(np.atleast_2d(deg5)[:, :5])
    return p, R


def fit_rigid2d(A, B):
    """B ≈ R A + t (2D, 회전+평행이동, 크기 고정). 반환 R, t."""
    ca, cb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    return R, cb - R @ ca
