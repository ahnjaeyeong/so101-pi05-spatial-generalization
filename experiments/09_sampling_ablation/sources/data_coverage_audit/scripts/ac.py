"""data_coverage_audit 공통 함수 (읽기만 함: d2 데이터셋 · 세션 QA · 기존 분석 산출물. 로봇 · GPU 안 씀).

좌표계 (config/redbox8_layouts.yaml 'C frame', 단위 cm):
  x = 로봇 → 상자 방향 (+), y = 로봇 왼쪽 (+). 원점 C = 상자 로봇쪽 벽 바깥면의 로봇 오른쪽 끝.
  로봇 베이스: config base_xy_cm = (-31, 11), pan_offset -1.4 (T1-K 48편으로 맞춤). 이 감사는 256편 첫 파지 pan 으로 다시 맞춘 값
  (tables/a00_base_fit.json, 실측 아님) 을 쓴다. bearing b = atan2(y - by, x - bx) [°], + = 로봇 왼쪽.  pan 기대값 = -b + pan_offset.
  반지름 축 u_r = 베이스 → 큐브 단위벡터, 접선 축 u_t = u_r 를 반시계 90° (위에서 볼 때, + = 로봇 왼쪽으로 도는 쪽).
  접선 오차 e_t = (집게 끝 − 큐브) · u_t, 반지름 오차 e_r = (집게 끝 − 큐브) · u_r.
집게 끝 (TCP) = FK(so101_new_calib.urdf, gripper_frame_link, URDF 0 = lerobot 보정 중앙) 를 diag_grasp_bias/fk_fit.json
  (학습 첫 파지에서 큐브 위치에 맞춘 2D 강체 변환) 으로 탁자 좌표에 옮긴 값. 이 변환은 첫 파지 평균 오차가 0 이 되도록 맞춘 것이다.
"""
import csv
import glob
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
K8 = HOME / "so101_runs/main_k8"
D2 = K8 / "d2"
DS = D2 / "dataset"
AUD = D2 / "data_coverage_audit"
TAB = AUD / "tables"
FIG = AUD / "figs"
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
import common as C  # noqa: E402

FPS = 30
JOINTS = C.JOINTS
J5 = JOINTS[:5]
CFG = C.CFG
ROB = CFG["robot"]
BASE_CFG = C.BASE
# 이 감사의 베이스 · pan 오프셋: a00_tcp_model.py 가 256편 첫 파지 pan 으로 다시 맞춘 값 (없으면 config 값)
_BF = Path(__file__).resolve().parent.parent / "tables/a00_base_fit.json"
if _BF.exists():
    _b = json.load(open(_BF))
    BASE = np.array(_b["base_xy_cm"], float)
    PAN_OFF = float(_b["pan_offset_deg"])
else:
    BASE = BASE_CFG.copy()
    PAN_OFF = float(ROB["pan_offset_deg"])
PAN_SIGN = float(ROB["pan_sign"])
ROLL0 = float(ROB.get("wrist_roll_neutral_deg", -1.5))
SOURCES = C.SOURCES   # d2 합친 순서
KNOWN = C.load_known()

_FIT = json.load(open(D2 / "diag_grasp_bias/fk_fit.json"))
FIT_R, FIT_T = np.array(_FIT["R"]), np.array(_FIT["t"])


def wrap90(a):
    return ((np.asarray(a, float) + 45) % 90) - 45


def wrap180(a):
    return ((np.asarray(a, float) + 180) % 360) - 180


def bearing(x, y):
    return np.degrees(np.arctan2(np.asarray(y) - BASE[1], np.asarray(x) - BASE[0]))


def rng(x, y):
    return np.hypot(np.asarray(x) - BASE[0], np.asarray(y) - BASE[1])


def tip(q):
    """q (N,≥5) lerobot ° → 집게 끝 (N,3): x, y 는 탁자 C frame cm (fk_fit 변환), z 는 FK base_link z (cm, 탁자 높이 기준 아님)."""
    p, R = C.fk_xy(np.asarray(q, float)[:, :5])
    xy = (FIT_R @ (p[:, :2] * 100).T).T + FIT_T
    return np.column_stack([xy, p[:, 2] * 100]), R


PAN_AXIS_FK_CM = np.array([3.88, 0.0])   # so101_new_calib.urdf shoulder_pan 관절 원점 (base_link 기준 수평, cm)
_POLAR = AUD / "tables/a00_tcp_model.json"


def armplane(q):
    """pan=0 으로 둔 FK 집게 끝을 pan 축 기준 팔 평면 좌표로: A = 축에서 뻗은 수평 거리, L = 옆 오프셋 (FK +y), Z = FK z (cm)."""
    q0 = np.asarray(q, float)[:, :5].copy()
    q0[:, 0] = 0.0
    p0, _ = C.fk_xy(q0)
    h = p0[:, :2] * 100 - PAN_AXIS_FK_CM
    return h[:, 0], h[:, 1], p0[:, 2] * 100


def tcp(q, dA=None):
    """pan 축 극좌표 TCP (기본 TCP, a00_tcp_model.py 에서 검증): 방향 = pan (config: bearing = -(pan + 1.4)), 반지름 = 베이스 (-31, 11) 에서
    FK 팔 평면 거리 A + dA, 옆 = -L (URDF 옆 부호가 탁자 접선과 반대 — 파지 순간 roll 상관 −0.80 → −0.04 로 확인).
    dA = 학습 첫 파지에서 맞춘 반지름 편향 (a00_tcp_model.json). 반환 (N,3): x, y (C frame cm), z (FK cm)."""
    q = np.asarray(q, float)
    if dA is None:
        dA = json.load(open(_POLAR))["dA_cm"] if _POLAR.exists() else 0.0
    A, L, Z = armplane(q)
    b = np.radians((q[:, 0] - PAN_OFF) / PAN_SIGN)
    ur = np.column_stack([np.cos(b), np.sin(b)])
    ut = np.column_stack([-np.sin(b), np.cos(b)])
    xy = BASE + (A + dA)[:, None] * ur - L[:, None] * ut
    return np.column_stack([xy, Z])


def axes(cx, cy):
    ur = np.array([cx - BASE[0], cy - BASE[1]], float)
    ur /= np.linalg.norm(ur)
    ut = np.array([-ur[1], ur[0]])
    return ut, ur


def tip_jacobian_tr(q, ut, ur, h=0.5):
    """관절 5개 각각을 h° 바꿨을 때 집게 끝 (접선, 반지름, z) 변화 / ° — 수치 미분. 반환 (N,5,3)."""
    q = np.asarray(q, float)[:, :5]
    p0, _ = tip(q)
    J = np.zeros((len(q), 5, 3))
    for j in range(5):
        qq = q.copy()
        qq[:, j] += h
        p1, _ = tip(qq)
        d = (p1 - p0) / h
        J[:, j, 0] = d[:, :2] @ ut
        J[:, j, 1] = d[:, :2] @ ur
        J[:, j, 2] = d[:, 2]
    return J


def load_d2():
    """episode → (state (n,6), action (n,6), timestamp (n,), frame_index (n,))."""
    files = sorted(glob.glob(str(DS / "data/*/*.parquet")))
    df = pd.concat([pd.read_parquet(f) for f in files])
    out = {}
    for e, g in df.groupby("episode_index"):
        g = g.sort_values("frame_index")
        out[int(e)] = (np.stack(g["observation.state"].values).astype(float), np.stack(g["action"].values).astype(float),
                       g["timestamp"].values.astype(float), g["frame_index"].values.astype(int), g["index"].values.astype(int))
    return out


def episodes_meta():
    return pd.read_parquet(glob.glob(str(DS / "meta/episodes/*/*.parquet"))[0])


# ---------------- 큐브 위치 · 각도 (세션 QA) ----------------
ARROW = {"↺": 1.0, "↻": -1.0}


def _angle(tok):
    """'↺31°' → +31, '↻42°' → -42, '45°' → 45, '0°' → 0, 그 밖 → nan. + = 반시계 (위에서)."""
    tok = tok.strip()
    m = re.match(r"^([↺↻]?)(-?\d+(?:\.\d+)?)°", tok)
    if not m:
        return np.nan
    v = float(m.group(2))
    return v * ARROW.get(m.group(1), 1.0)


def _plan_angle(code):
    """layout.csv 각도 코드 L30/R30/0/45 → +30 / -30 / 0 / 45 (L = 반시계 ↺)."""
    if not code:
        return np.nan
    code = code.strip()
    if code.startswith("L"):
        return float(code[1:])
    if code.startswith("R"):
        return -float(code[1:])
    return float(code)


def qa_rows(sess):
    """qa_report.md 의 배치 표 (각도 · 손목 칸 있는 표) → {세션 ep: (각도 칸, 손목 칸)}."""
    txt = (K8 / sess / "qa_report.md").read_text().splitlines()
    out, hdr = {}, None
    for ln in txt:
        if ln.startswith("| ep |") and "각도 계획" in ln:
            hdr = [c.strip() for c in ln.strip("|").split("|")]
            continue
        if hdr and ln.startswith("| ") and re.match(r"^\| \d{3}", ln):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if len(cells) != len(hdr):
                continue
            ep = int(cells[0][:3])
            out[ep] = (cells[hdr.index("각도 계획→잰 값")], cells[hdr.index("손목 필요→돌림 (오차)")])
        elif hdr and not ln.startswith("|"):
            if out:
                hdr = None
    return out


def cube_table():
    """d2 episode 256 행: 그룹 · 원본 · 빨강 위치 (front 첫 화면 + H 역산, cm) · 계획 K · K 좌표 · 계획/잰 각도 · 손목 필요/돌림."""
    rows = []
    d2e = 0
    for grp, sess in SOURCES:
        lay = [r for r in csv.DictReader(open(K8 / sess / "layout.csv")) if r["status"] == "recorded"]
        lay.sort(key=lambda r: int(r["episode_index"]))
        pos = {}
        for r in csv.DictReader(open(K8 / sess / "qa/positions.csv")):
            if r["color"] == "red":
                pos.setdefault(int(r["episode_index"]), []).append((float(r["x_cm"]), float(r["y_cm"]), r["nearest_known"], float(r["dist_known_cm"])))
        qa = qa_rows(sess)
        for r in lay:
            e = int(r["episode_index"])
            p = pos.get(e, [])
            lid = r["layout_id"]
            mode = "K" if grp.endswith("K") else "R"
            planK = ""
            if mode == "K":
                m = re.match(r"^T\dK(\d)", lid)
                planK = f"K{m.group(1)}" if m else ""
            # 계획 각도 (빨강)
            ang_code = ""
            for it in (r.get("angles") or "").split(";"):
                if not it:
                    continue
                k, v = it.split(":")
                if (mode == "K" and k == planK) or (mode == "R" and k.startswith("red")):
                    ang_code = v
            # 잰 각도 (빨강) · 손목
            meas, need, turned = np.nan, np.nan, np.nan
            if e in qa:
                acell, wcell = qa[e]
                for it in acell.split(" · "):
                    it = it.strip()
                    key = it.split(" ")[0]
                    if (mode == "K" and key == planK) or (mode == "R" and key.startswith("red")):
                        if "→" in it:
                            meas = _angle(it.split("→")[1])
                m = re.match(r"^([↺↻]?\d+(?:\.\d+)?°)→([↺↻]?\d+(?:\.\d+)?°)", wcell)
                if m:
                    need, turned = _angle(m.group(1)), _angle(m.group(2))
            x, y = (p[0][0], p[0][1]) if len(p) == 1 else (np.nan, np.nan)
            kx, ky = KNOWN.get(planK, (np.nan, np.nan))
            rows.append(dict(ep=d2e, group=grp, task=grp[:2], mode=mode, session=sess, src_ep=e, layout_id=lid, n_red_found=len(p),
                             cube_x=x, cube_y=y, nearest_K=p[0][2] if p else "", dist_nearest_K_cm=p[0][3] if p else np.nan,
                             plan_K=planK, plan_x=kx, plan_y=ky, yaw_plan=_plan_angle(ang_code), yaw_plan_code=ang_code,
                             yaw_meas=meas, wrist_need_qa=need, wrist_turned_qa=turned, frames_plan=int(r["frames"] or 0)))
            d2e += 1
    T = pd.DataFrame(rows)
    T["bearing"] = bearing(T.cube_x, T.cube_y)
    T["range_cm"] = rng(T.cube_x, T.cube_y)
    T["pan_expected"] = PAN_SIGN * T.bearing + PAN_OFF
    yaw = T.yaw_meas.where(T.yaw_meas.notna(), T.yaw_plan)
    T["yaw_used"] = yaw
    T["yaw_src"] = np.where(T.yaw_meas.notna(), "measured", np.where(T.yaw_plan.notna(), "plan", ""))
    T["roll_need_rel"] = wrap90(yaw - T.bearing)   # 손목이 돌아야 하는 각 (90° 주기, 반지름 기준) — QA roll_check 와 같은 정의
    return T


# ---------------- 이벤트 ----------------
def onset(x, thr):
    """x (n,k): 처음 값에서 thr 넘게 벗어난 첫 프레임 (없으면 None)."""
    d = np.abs(x - x[0]).max(1) if x.ndim == 2 else np.abs(x - x[0])
    i = np.where(d > thr)[0]
    return int(i[0]) if len(i) else None


def settle_index(x, c, tol, start=0):
    """x[c] 기준 ±tol 안에 c 까지 계속 머물기 시작한 프레임 (start 이상)."""
    out = np.abs(x[start:c + 1] - x[c]) > tol
    idx = np.where(out)[0]
    return int(start + idx[-1] + 1) if len(idx) else int(start)


def first_reach_index(x, c, tol, start=0):
    idx = np.where(np.abs(x[start:c + 1] - x[c]) <= tol)[0]
    return int(start + idx[0]) if len(idx) else int(c)


def smooth(x, k=5):
    if len(x) < k:
        return x
    w = np.ones(k) / k
    pad = k // 2
    xp = np.pad(x, (pad, pad), mode="edge")
    return np.convolve(xp, w, mode="valid")


def first_submovement(x, i0, c, vmin=5.0):
    """x (°), i0 = 움직임 시작. 속도(5프레임 평균, °/s) 가 최고점 뒤 처음으로 max(vmin, 최고점 10%) 아래로 떨어진 프레임."""
    v = np.gradient(smooth(x, 5)) * FPS
    seg = np.abs(v[i0:c + 1])
    if len(seg) < 3:
        return c
    # 첫 봉우리: 처음으로 속도가 줄기 시작한 극대
    k = 0
    while k + 1 < len(seg) and seg[k + 1] >= seg[k]:
        k += 1
    pk = seg[k]
    thr = max(vmin, 0.1 * pk)
    j = k
    while j < len(seg) and seg[j] > thr:
        j += 1
    return int(i0 + min(j, len(seg) - 1))


# ---------------- 보고서 도우미 ----------------
FACTS = AUD / "_facts"


def md_table(df, fmt=None, index=False):
    """DataFrame → markdown 표 (tabulate 없음). fmt: {열: 형식} 또는 전체 기본 '{:.2f}'."""
    d = df.reset_index() if index else df
    cols = list(d.columns)

    def f(c, v):
        if isinstance(v, (float, np.floating)):
            if np.isnan(v):
                return "–"
            spec = (fmt or {}).get(c, "{:.2f}") if isinstance(fmt, dict) else (fmt or "{:.2f}")
            return spec.format(v)
        return str(v)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in d.iterrows():
        lines.append("| " + " | ".join(f(c, r[c]) for c in cols) + " |")
    return "\n".join(lines)


def write_facts(name, text):
    FACTS.mkdir(exist_ok=True)
    (FACTS / name).write_text(text)


def q(x, p):
    return float(np.nanpercentile(x, p))


def boot_ci(x, fn=np.mean, n=2000, seed=0):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 3:
        return (np.nan, np.nan)
    r = np.random.default_rng(seed)
    v = [fn(x[r.integers(0, len(x), len(x))]) for _ in range(n)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
