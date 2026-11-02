"""R1/R2 추가 시연 수집 — 공용 부분 (설정 · 계획 · 시작 자세 안전 검사 · 색 검출 · 실시간 공유 파일 · 메타데이터).

녹화 프로세스(r12_record_entry.py, lerobot 안)에서도 불리므로 모듈 맨 위에서는 표준 라이브러리 + numpy + yaml 만 쓴다.
cv2 는 검출 함수 안에서만 불러온다. 로봇·카메라 장치는 이 모듈에서 절대 열지 않는다.
"""

import csv
import datetime
import hashlib
import json
import math
import os
import random
import re
import tempfile

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # ~/so101_runs/main_k8/r1_r2_collection
DEFAULT_CONFIG = os.path.join(ROOT, "config", "r12_scenarios.yaml")
HOME = os.path.expanduser("~")
RUNS_ROOT = os.path.abspath(os.path.expanduser(os.environ.get("RECORD_UI_RUNS", "~/so101_runs")))

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")
ARM_JOINTS = JOINTS[:5]
SHORT = {"shoulder_pan": "pan", "shoulder_lift": "lift", "elbow_flex": "elbow", "wrist_flex": "wflex",
         "wrist_roll": "wroll", "gripper": "grip"}
CAMS = ("front", "wrist")
FRAME_SHAPE = (480, 640, 3)

PLAN_CSV = "r12_plan.csv"
PLAN_META = "r12_plan_meta.json"
ATTEMPTS = "r12_attempts.jsonl"
EPISODES_CSV = "r12_episodes.csv"
PLAN_FIELDS = ["episode_index", "scenario_id", "type", "position", "cube_xy_cm", "angle", "offset_dir",
               "pan_offset_deg", "pan_target_deg", "start_xy_cm", "status", "retake_of", "frames", "note",
               # R1 = Pan 방향 오차 (방향 left/right·명목 크기)·시작 자세 종류·손목 가시성 목표, R2 = 국소 정렬 종류·명목 크기. 해당 없는 쪽은 빈칸.
               "error_kind", "pan_error_direction", "nominal_pan_error_deg", "local_alignment_type", "nominal_local_error_cm",
               "start_pose_type", "wrist_visibility_target",
               # 4차: R1 접근 단계 기대 (early / mid / mid|late), 큐브 자리 출처 (K 격자 / 자유 점 / front 검출)
               "approach_stage_expected", "cube_position_source"]
PLANNED, RECORDED, EXCLUDED = "planned", "recorded", "excluded"

# 기존 d2 를 이루는 세션·폴더 — R1/R2 세션 이름으로 쓰면 거부한다 (d2 원본 보호).
PROTECTED_SESSIONS = {f"main_k8/redbox_t{t}_{m}" for t in (1, 2, 3) for m in ("known", "random")} | \
    {f"main_k8/d{i}" for i in range(1, 10)} | {"main_k8/r1_r2_collection"}

ANGLE_KO = {"0": "0°", "45": "45°"}


class PlanError(Exception):
    pass


# ---------------------------------------------------------------- 설정

def _expand(p):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def load_config(path=None):
    path = _expand(path or DEFAULT_CONFIG)
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["_path"] = path
    with open(path, "rb") as f:
        cfg["_sha256"] = hashlib.sha256(f.read()).hexdigest()
    with open(_expand(cfg["base_config"])) as f:
        cfg["_base"] = yaml.safe_load(f)
    return cfg


def angle_label(a):
    a = str(a)
    if a in ANGLE_KO:
        return ANGLE_KO[a]
    if a[:1] == "L":
        return f"↺{a[1:]}°"
    if a[:1] == "R":
        return f"↻{a[1:]}°"
    return a


def pan_ref(cfg, pos):
    """큐브 자리의 '큐브 가운데 pan' 기준값. K = 설정 pan_reference_deg (d2 파지 순간 중앙값, 판마다 ±9°).
    자유 점 F# · 검출 자리 X(x,y) = 기하 −atan2 − 1.4° (K 에서 d2 중앙값과 −0.2…+3.1° 차이)."""
    if pos in cfg["pan_reference_deg"]:
        return float(cfg["pan_reference_deg"][pos])
    (x, y), (bx, by) = known_xy(cfg, pos), base_xy(cfg)
    return -math.degrees(math.atan2(y - by, x - bx)) - 1.4


def pan_ref_source(cfg, pos):
    return "d2_K_median" if pos in cfg["pan_reference_deg"] else "geometry"


def position_source(cfg, pos):
    """큐브 자리 출처와 신뢰도 (메타데이터 cube_position_source / confidence)."""
    if pos in cfg["_base"]["known_positions"]:
        return "K_grid", "K 격자 (탁자 표시, ±0.5 cm)"
    if pos in (cfg.get("free_points") or {}):
        return "free_point", "자유 점 (탁자 표시 없음, 사람이 대략 놓음 — front 검출로 확인)"
    return "front_detected", "front H 검출 (큐브 중심 평면 rms 2 px ≈ ±0.5 cm, 로봇에 가려지면 치우침)"


def detected_pos(xy):
    """front 검출 위치 → 계획 자리 이름 X(x,y)."""
    return f"X({xy[0]:.1f},{xy[1]:.1f})"


def pan_guide(cfg, row, pan_now):
    """준비 때 안내: (차이 = 목표 − 지금, 글, 맞음 여부). row 는 계획 줄 또는 describe_row 결과."""
    if row is None or row.get("pan_target_deg") in (None, "") or pan_now is None:
        return None, "", False
    tgt = float(row["pan_target_deg"])
    d = tgt - pan_now
    ok = abs(d) <= float(cfg.get("pan_tol_deg", 2.5))
    side = "왼쪽(−)" if d < 0 else "오른쪽(+)"
    return d, (f"Pan 지금 {pan_now:+.1f}° → 목표 {tgt:+.1f}° : " + ("✓ 맞음" if ok else f"{abs(d):.1f}° 더 {side}")), ok


def pan_target_text(row):
    off = float(row.get("pan_offset_deg") or 0)
    side = "왼쪽(−)" if off < 0 else "오른쪽(+)"
    return (f"Pan 목표 {float(row['pan_target_deg']):+.1f}° = {row['position']} 기준 {float(row['pan_target_deg']) - off:+.1f}°"
            + (f" + {side} {abs(off):g}°" if off else " (어긋남 0)"))


# ---- 손목 영상 '닫기 영역' (d2 사람 시연에서 닫기 시작한 순간의 큐브 위치, tools/r12_wrist_zone.py)
WRIST_ZONE = os.path.join(ROOT, "config", "r12_wrist_zone.json")


def wrist_zone():
    z = read_json(WRIST_ZONE)
    return z.get("close_zone") if z else None


def zone_status(w, zone):
    """손목 검출 w (vision()['wrist']) → (닫아도 됨?, 안내 글). 화면 좌표 기준 (u 오른쪽 +, v 아래 +)."""
    if not zone:
        return False, ""
    if not w or not w.get("detected"):
        return False, "큐브 안 보임"
    u, v = (w["dx"] + 1) / 2, (w["dy"] + 1) / 2
    area = w["area_px"] / (640 * 480)
    msgs = []
    if area < zone["area_min"] or v < zone["v"][0]:
        msgs.append("더 진입")
    elif v > zone["v"][1]:
        msgs.append("너무 들어감")
    if u < zone["u"][0]:
        msgs.append("영역 왼쪽")
    elif u > zone["u"][1]:
        msgs.append("영역 오른쪽")
    return (not msgs), ("✓ 닫기 OK" if not msgs else " · ".join(msgs))


# ---- 큐브 각도 (d2 와 같은 규칙·측정: ~/so101_boxpick/scripts/cube_angle.py — 읽기만 해서 씀)
def _cube_angle():
    import sys as _s

    p = os.path.join(HOME, "so101_boxpick", "scripts")
    if p not in _s.path:
        _s.path.insert(0, p)
    import cube_angle

    return cube_angle


def cube_corners(cfg, pos, angle, half=None):
    """K 자리에 계획 각도로 놓은 큐브 윗면 네 꼭짓점 (탁자 cm). 각도 L = 위에서 반시계 +."""
    ca = _cube_angle()
    half = half or float(cfg["_base"]["objects"]["red_cube"]["size_cm"]) / 2
    x, y = known_xy(cfg, pos)
    t = math.radians(ca.target_deg(angle))
    out = []
    for dx, dy in ((half, half), (half, -half), (-half, -half), (-half, half)):
        out.append((x + dx * math.cos(t) - dy * math.sin(t), y + dx * math.sin(t) + dy * math.cos(t)))
    return out


def measure_angle(front_rgb, cfg, pos, angle):
    """front 한 장에서 K 근처 빨강 큐브 각도를 재서 계획과 비교. 반환 dict (meas, conf, ok, text, range) 또는 이유."""
    import cv2

    ca = _cube_angle()
    hsv = cv2.cvtColor(front_rgb, cv2.COLOR_RGB2HSV)
    m = np.zeros(hsv.shape[:2], np.uint8)
    for r in red_ranges(cfg):
        m |= cv2.inRange(hsv, (r["h"][0], r["s"][0], r["v"][0]), (r["h"][1], r["s"][1], r["v"][1]))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    cam = cfg["_base"]["camera"]["front_640x480"]["camera_xy_cm"]
    meas, conf = ca.measure_at(m, front_H(cfg), cam, known_xy(cfg, pos), img=cv2.cvtColor(front_rgb, cv2.COLOR_RGB2BGR))
    choices = cfg.get("angles") or ca.CHOICES
    rng = ca.range_text(angle, choices)
    if meas is None:
        return {"meas": None, "why": conf, "ok": False, "range": rng,
                "text": f"각도 못 잼 ({conf}) → 목표 {angle_label(angle)}"}
    ok, d, _ = ca.judge(meas, angle, choices)
    return {"meas": round(meas, 1), "conf": round(conf, 2), "ok": bool(ok), "diff": round(d, 1), "range": rng,
            "text": f"각도 지금 {ca.label(meas)} → 목표 {angle_label(angle)} " + ("✓" if ok else f"({rng} 안으로)")}


# ---- 위에서 본 위치 (탁자 C 좌표 cm: x = 상자 쪽, y = 로봇 왼쪽). Pan 방향만 쓴다 — FK(손목 위치) 는 쓰지 않는다.
def base_xy(cfg):
    return tuple(cfg["_base"]["robot"]["base_xy_cm"])


def k_radius(cfg, pos):
    (x, y), (bx, by) = known_xy(cfg, pos), base_xy(cfg)
    return math.hypot(x - bx, y - by)


def pan_phi(cfg, pos, pan):
    """pan 값 → 로봇 밑동에서 본 탁자 위 방향 (°, atan2(y, x)). K 의 기준 pan 에서 정확히 그 K 를 향하게 맞춘다.
    pan 이 커지면 오른쪽(y 감소) — d2 기록과 같은 부호 (K7·K4·K1 열 = pan 음수)."""
    (x, y), (bx, by) = known_xy(cfg, pos), base_xy(cfg)
    return math.degrees(math.atan2(y - by, x - bx)) - (pan - pan_ref(cfg, pos))


def polar_xy(cfg, phi, r):
    bx, by = base_xy(cfg)
    return bx + r * math.cos(math.radians(phi)), by + r * math.sin(math.radians(phi))


def start_xy(cfg, row):
    """시작 위치(오답) = 밑동에서 Pan 목표 방향, 거리 = 큐브 거리 + start_radial_cm."""
    s = cfg["scenarios"][row["scenario_id"]]
    r = k_radius(cfg, row["position"]) + float(s.get("start_radial_cm", 0) or 0)
    return polar_xy(cfg, pan_phi(cfg, row["position"], float(row["pan_target_deg"])), r)


def known_xy(cfg, pos):
    """K# = 격자, F# = 설정 free_points, X(x,y) = front 검출 자리."""
    if pos in cfg["_base"]["known_positions"]:
        return tuple(cfg["_base"]["known_positions"][pos]["xy_cm"])
    if pos in (cfg.get("free_points") or {}):
        return tuple(float(v) for v in cfg["free_points"][pos])
    m = re.match(r"^X\(([-0-9.]+),([-0-9.]+)\)$", str(pos))
    if m:
        return float(m.group(1)), float(m.group(2))
    raise KeyError(f"큐브 자리 {pos!r} 를 몰라요")


def scenarios_of(cfg, typ):
    return [(sid, s) for sid, s in cfg["scenarios"].items() if s["type"] == typ and int(s.get("count", 0)) > 0]


def group_of(cfg, name):
    if name not in cfg["groups"]:
        raise PlanError(f"그룹 {name} 이 설정에 없어요 ({', '.join(cfg['groups'])})")
    return cfg["groups"][name]


def group_for_session(cfg, session):
    for name, g in cfg["groups"].items():
        if g["session"] == session:
            return name, g
    return None, None


# ---------------------------------------------------------------- 관절 한계 · 시작 자세 안전 검사

def calib_limits(cfg):
    """follower 캘리브레이션 range_min/max → lerobot DEGREES 정규화와 같은 식 ((raw − mid)·360/4095) 의 ± 한계."""
    path = _expand(cfg["safety"]["calibration"])
    with open(path) as f:
        cal = json.load(f)
    out = {}
    for j in ARM_JOINTS:
        lo, hi = cal[j]["range_min"], cal[j]["range_max"]
        mid = (lo + hi) / 2
        out[j] = ((lo - mid) * 360 / 4095, (hi - mid) * 360 / 4095)
    return out


def _joint_dict(d):
    if d is None:
        return None
    out = {}
    for j in JOINTS:
        for k in (f"{j}.pos", j):
            if k in d:
                out[j] = float(d[k])
                break
    return out


def safety_check(state, action, cfg, limits=None):
    """시작 자세 검사. state/action: {'shoulder_pan.pos': °, ...} (팔로워 관측 / 리더 명령).
    반환 [(level, code, 메시지)] — level 'BLOCK' 이면 녹화를 시작하지 않는다, 'WARN' 은 표시만.
    BLOCK (안전, 녹화 막음): 관절값 없음·NaN · |pan| > 95° 또는 Pan 한계 10° 안 · 팔 관절 리더−팔로워 > 25° (막힘·밀기).
    WARN (막지 않음): lift·elbow 등 한계 근처 (쉬는 자세가 원래 lift −103 = 한계 1° 안, d2 시작 자세) · d2 범위 밖 · 그리퍼 닫힘.
    시나리오 조건 (단계·가시성·Pan 오차) 은 여기서 보지 않는다 — scenario_checks.
    FK·TCP 위치는 쓰지 않는다 (K1 에서 절대 위치 4–5 cm 오차, 2026-10 확인)."""
    sf = cfg["safety"]
    limits = limits or calib_limits(cfg)
    s, a = _joint_dict(state), _joint_dict(action)
    out = []
    if not s or any(j not in s for j in JOINTS):
        return [("BLOCK", "no_state", "관절값을 아직 못 읽었어요")]
    for j in ARM_JOINTS:
        v = s[j]
        if not math.isfinite(v):
            out.append(("BLOCK", f"nan_{j}", f"{SHORT[j]} 값이 숫자가 아님"))
            continue
        lo, hi = limits[j]
        room = min(v - lo, hi - v)
        if room < sf["limit_margin_block_deg"]:
            out.append(("WARN", f"limit_{j}", f"{SHORT[j]} {v:+.1f}° — 한계({lo:+.0f}/{hi:+.0f}°)까지 {room:.0f}° (쉬는 자세?)"))
        elif room < sf["limit_margin_warn_deg"]:
            out.append(("WARN", f"limit_{j}", f"{SHORT[j]} {v:+.1f}° — 한계까지 {room:.0f}°"))
        env = sf.get("d2_approach_envelope", {}).get(j)
        if env and not env[0] <= v <= env[1]:
            out.append(("WARN", f"env_{j}", f"{SHORT[j]} {v:+.1f}° — d2 접근 구간 범위 [{env[0]:+.0f}, {env[1]:+.0f}] 밖"))
    # Pan 만은 BLOCK (3차 지시서: Pan 기계적 한계 근처 시작 금지, 실물 평가 −109° 이탈 재현 금지). 쉬는 자세 pan −4 와 무관.
    pv = s["shoulder_pan"]
    if math.isfinite(pv):
        plo, phi_ = limits["shoulder_pan"]
        if abs(pv) > sf["pan_abs_block_deg"]:
            out.append(("BLOCK", "pan_abs", f"|pan| {abs(pv):.1f}° > {sf['pan_abs_block_deg']}° — Pan 을 안쪽으로"))
        elif min(pv - plo, phi_ - pv) < sf.get("pan_limit_margin_block_deg", 10):
            out.append(("BLOCK", "pan_limit", f"pan {pv:+.1f}° — 한계({plo:+.0f}/{phi_:+.0f}°)까지 {min(pv - plo, phi_ - pv):.0f}°"))
    g = s["gripper"]
    if g < sf["gripper_open_min"]:
        out.append(("WARN", "gripper_closed", f"그리퍼 {g:.0f} < {sf['gripper_open_min']} — 녹화 시작 뒤 열어도 됨"))
    if a:
        for j in ARM_JOINTS:
            if j in a:
                d = abs(a[j] - s[j])
                if d > sf["leader_follower_diff_block_deg"]:  # 4차: 다시 BLOCK — 팔로워가 못 따라감 = 막힘·밀기 (실제 시작 17번 최대 2.9°)
                    out.append(("BLOCK", f"diff_{j}", f"{SHORT[j]} 리더−팔로워 {d:.0f}° > {sf['leader_follower_diff_block_deg']}° — "
                                                      "팔로워가 막혀 밀고 있거나 아직 움직이는 중 (팔을 멈추고 다시 →)"))
                elif d > sf["leader_follower_diff_warn_deg"]:
                    out.append(("WARN", f"diff_{j}", f"{SHORT[j]} 리더−팔로워 {d:.0f}°"))
    return out


def blocking(checks):
    return [c for c in checks if c[0] == "BLOCK"]


# ---------------------------------------------------------------- 계획 (r12_plan.csv)

def _spread(entries, rng):
    """[(scenario, i, count)] → 시나리오가 고르게 섞인 순서 (각 시나리오의 (i+0.5)/count 위상 + 작은 흔들림)."""
    keyed = [((i + 0.5) / c + rng.uniform(-0.15, 0.15) / c, rng.random(), sid) for sid, i, c in entries]
    return [sid for *_, sid in sorted(keyed)]


def make_plan(cfg, group_name):
    g = group_of(cfg, group_name)
    scen = scenarios_of(cfg, g["type"])
    if g.get("scenario_counts"):  # 그룹이 시나리오별 편수를 따로 정함 (시험 연습 등)
        scen = [(sid, {**cfg["scenarios"][sid], "count": int(n)}) for sid, n in g["scenario_counts"].items() if int(n) > 0]
    if not scen:
        raise PlanError(f"{g['type']} 시나리오 수량이 모두 0 이에요")
    rng = random.Random(int(g["seed"]))
    pos, angs = list(cfg["positions"]), list(cfg["angles"])
    rows_by_sid = {}
    total = sum(int(s["count"]) for _, s in scen)
    # K 가 정해진 시나리오 (positions) 먼저: 그 K 들을 섞어 돌려 씀
    fixed_k = {}
    for sid, s in scen:
        if s.get("positions"):
            ks = []
            if s.get("travel"):  # 지나침: 진행 방향 왼쪽/오른쪽 K 를 번갈아 (어긋남 방향이 반반)
                rest = float(cfg.get("rest_pan_deg", -4.0))
                sides = [[k for k in s["positions"] if pan_ref(cfg, k) < rest], [k for k in s["positions"] if pan_ref(cfg, k) >= rest]]
                while len(ks) < int(s["count"]):
                    for side in sides:
                        rng.shuffle(side)
                    ks += [k for pair in zip(*sides) for k in pair]
            while len(ks) < int(s["count"]):
                p_ = list(s["positions"])
                rng.shuffle(p_)
                ks += p_
            fixed_k[sid] = ks[:int(s["count"])]
    # 나머지 판의 K: 전체가 K 마다 고르게 되도록 남은 몫을 채운 뒤 섞음 (정해진 K 가 없으면 섞은 순열을 이어 붙인 것과 같음)
    used = {k: 0 for k in pos}
    for ks in fixed_k.values():
        for k in ks:
            used[k] += 1
    n_free = total - sum(used.values())
    kseq = []
    if g["type"] == "R1" and cfg.get("r1_positions") and not fixed_k:  # 4차: K 8 + 자유 점 8
        pool = list(cfg["r1_positions"])
        rng.shuffle(pool)
        kseq = (pool * (n_free // len(pool) + 1))[:n_free]
    while len(kseq) < n_free:
        p = [k for k in pos if used[k] <= min(used.values())]
        rng.shuffle(p)
        for k in p:
            if len(kseq) < n_free:
                kseq.append(k)
                used[k] += 1
    aseq = []  # 각도도 전체에서 고르게 (16편 = 4가지 × 4, 32편 = × 8)
    while len(aseq) < total:
        a = angs[:]
        rng.shuffle(a)
        aseq += a
    k_iter, a_iter = iter(kseq), iter(aseq)
    lim = float(cfg["safety"]["pan_abs_block_deg"]) - 3.0

    def resolve(spec, pos):  # 요청 어긋남 → (pan 어긋남 °, 줄었는지)
        if spec[0] in ("over", "under", "over_deg", "under_deg"):  # 진행 방향(쉬는 자세 pan → K 기준 pan) 기준 지나침(+)/덜 감(−)
            t = math.copysign(1.0, pan_ref(cfg, pos) - float(cfg.get("rest_pan_deg", -4.0)))
            spec = ("deg" if spec[0].endswith("_deg") else "cm", t * spec[1] * (1 if spec[0].startswith("over") else -1))
        if spec[0] == "cm":
            off = math.copysign(math.degrees(math.atan(abs(spec[1]) / k_radius(cfg, pos))), spec[1])
        else:
            off = float(spec[1])
        ref = pan_ref(cfg, pos)
        if abs(ref + off) > lim:  # |pan| 한계(95 − 3) 를 넘으면 크기를 줄인다
            return math.copysign(max(0.0, lim - abs(ref)), off), True
        return off, False

    flat = []
    allowed = {sid: s.get("positions") or pos for sid, s in scen}
    for si, (sid, s) in enumerate(scen):
        offs = [(s["travel"] + "_deg", float(v)) for v in s["travel_offsets_deg"]] if s.get("travel_offsets_deg") else \
            [(s["travel"], float(v)) for v in s["travel_offsets_cm"]] if s.get("travel_offsets_cm") else \
            [("cm", float(v)) for v in s["lateral_offsets_cm"]] if s.get("lateral_offsets_cm") else \
            [("deg", float(v)) for v in s.get("pan_offsets_deg", [0])]
        if s.get("positions"):
            kit = iter(fixed_k[sid])
        for i in range(int(s["count"])):
            loc = s.get("local_offsets_cm") or [""]
            flat.append({"scenario_id": sid, "type": s["type"], "position": next(kit) if s.get("positions") else next(k_iter),
                         # 시나리오마다 시작 칸을 하나씩 밀어 씀: 편수 = 목록 길이면 같고, 1편씩인 시험 연습에서는 왼쪽/오른쪽이 섞임
                         "angle": next(a_iter), "offset_dir": s.get("offset_dir", ""), "_spec": offs[(i + si) % len(offs)],
                         "error_kind": s.get("error_kind", ""),
                         "local_alignment_type": s.get("local_dir", "") if s["type"] == "R2" else "",
                         "start_pose_type": s.get("start_pose_type", "") if s["type"] == "R1" else "",
                         "wrist_visibility_target": s.get("wrist_visibility", "") if s["type"] == "R1" else "",
                         "approach_stage_expected": "|".join(s.get("stages", [])) if s["type"] == "R1" else "",
                         "nominal_local_error_cm": f"{loc[i % len(loc)]:g}" if s["type"] == "R2" and loc[0] != "" else ""})
    # 줄어드는 판은 다른 판과 K 를 바꿔 본다 (K 별 편수 그대로)
    for r in flat:
        if not resolve(r["_spec"], r["position"])[1]:
            continue
        for o in flat:
            if o is r or o["position"] == r["position"] or o["position"] not in allowed[r["scenario_id"]] \
                    or r["position"] not in allowed[o["scenario_id"]]:
                continue
            if not resolve(r["_spec"], o["position"])[1] and not resolve(o["_spec"], r["position"])[1]:
                r["position"], o["position"] = o["position"], r["position"]
                break
    for r in flat:
        off, capped = resolve(r.pop("_spec"), r["position"])
        if r["offset_dir"] in ("travel", "per_episode"):
            r["offset_dir"] = "robot_right" if off > 0 else "robot_left"
        if r["type"] == "R1":
            r["pan_error_direction"] = "right" if off > 0 else "left" if off < 0 else "none"  # 로봇에서 상자를 볼 때
            r["nominal_pan_error_deg"] = f"{round(abs(off), 1):g}"
        else:
            r["pan_error_direction"] = r["nominal_pan_error_deg"] = ""
        r.update(pan_offset_deg=f"{round(off, 1):g}",
                 pan_target_deg=f"{pan_ref(cfg, r['position']) + off:.1f}", note="pan 어긋남이 한계로 줄어듦" if capped else "")
        rows_by_sid.setdefault(r["scenario_id"], []).append(r)
    order = _spread([(sid, i, int(s["count"])) for sid, s in scen for i in range(int(s["count"]))], rng)
    used = {sid: 0 for sid, _ in scen}
    rows = []
    for idx, sid in enumerate(order):
        r = dict(rows_by_sid[sid][used[sid]])
        used[sid] += 1
        x, y = known_xy(cfg, r["position"])
        r.update(episode_index=idx, cube_xy_cm=f"{x:.1f},{y:.1f}", status=PLANNED, retake_of="", frames="", note=r.get("note", ""),
                 cube_position_source=position_source(cfg, r["position"])[0])
        sx, sy = start_xy(cfg, r)
        r["start_xy_cm"] = f"{sx:.1f},{sy:.1f}"
        rows.append(r)
    return rows


# R1 다음 판 바꾸기 (s 키) 때 줄 사이에서 맞바꾸는 시나리오 칸
SCENARIO_FIELDS = ["scenario_id", "error_kind", "offset_dir", "pan_offset_deg", "pan_error_direction", "nominal_pan_error_deg",
                   "wrist_visibility_target", "approach_stage_expected", "start_pose_type"]


def refresh_row(cfg, r):
    """계획 줄의 pan_offset_deg · position 에서 파생 칸을 다시 계산 (Pan 목표 |pan| ≤ 한계 − 3 으로 줄임)."""
    lim = float(cfg["safety"]["pan_abs_block_deg"]) - 3.0
    off = float(r.get("pan_offset_deg") or 0)
    ref = pan_ref(cfg, r["position"])
    note = ""
    if abs(ref + off) > lim:
        off = math.copysign(max(0.0, lim - abs(ref)), off)
        note = "pan 어긋남이 한계로 줄어듦"
    x, y = known_xy(cfg, r["position"])
    r.update(pan_offset_deg=f"{round(off, 1):g}", pan_target_deg=f"{ref + off:.1f}", cube_xy_cm=f"{x:.1f},{y:.1f}",
             cube_position_source=position_source(cfg, r["position"])[0], note=note)
    if r.get("type") == "R1":
        r["pan_error_direction"] = "right" if off > 0 else "left" if off < 0 else "none"
        r["nominal_pan_error_deg"] = f"{round(abs(off), 1):g}"
        r["offset_dir"] = "robot_right" if off > 0 else "robot_left" if off < 0 else "none"
    sx, sy = start_xy(cfg, r)
    r["start_xy_cm"] = f"{sx:.1f},{sy:.1f}"
    return r


def set_scenario(cfg, r, sid):
    """줄을 다른 R1 시나리오로 (오차 방향은 그대로, 크기 = 그 시나리오 후보 중 같은 방향 첫 값)."""
    s = cfg["scenarios"][sid]
    sign = -1.0 if float(r.get("pan_offset_deg") or 0) < 0 else 1.0
    cand = [float(v) for v in s.get("pan_offsets_deg", [0])]
    mag = next((abs(v) for v in cand if v * sign > 0), abs(cand[0]))
    r.update(scenario_id=sid, error_kind=s.get("error_kind", ""), pan_offset_deg=f"{sign * mag:g}",
             wrist_visibility_target=s.get("wrist_visibility", ""), approach_stage_expected="|".join(s.get("stages", [])),
             start_pose_type=s.get("start_pose_type", ""))
    return r


def plan_stats(rows):
    st = {"scenarios": {}, "positions": {}, "angles": {}, "offset_dir": {}}
    for r in rows:
        if r["status"] == EXCLUDED:
            continue
        for k, col in (("scenarios", "scenario_id"), ("positions", "position"), ("angles", "angle"), ("offset_dir", "offset_dir")):
            st[k][r[col]] = st[k].get(r[col], 0) + 1
    return st


def rows_text(rows):
    buf = [",".join(PLAN_FIELDS)]
    for r in rows:
        buf.append(",".join(str(r.get(k, "")) for k in PLAN_FIELDS))
    return "\n".join(buf) + "\n"


def write_plan(sess_dir, rows):
    _atomic_write(os.path.join(sess_dir, PLAN_CSV), lambda f: _write_rows(f, rows))


def _write_rows(f, rows):
    w = csv.DictWriter(f, fieldnames=PLAN_FIELDS)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in PLAN_FIELDS})


def read_plan(sess_dir):
    path = os.path.join(sess_dir, PLAN_CSV)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for i, r in enumerate(rows):
        if int(r["episode_index"]) != i:
            raise PlanError(f"{path}: {i}번째 줄 episode_index={r['episode_index']}")
    return rows


def read_meta(sess_dir):
    with open(os.path.join(sess_dir, PLAN_META)) as f:
        return json.load(f)


def write_meta(sess_dir, meta):
    _atomic_write(os.path.join(sess_dir, PLAN_META), lambda f: json.dump(meta, f, ensure_ascii=False, indent=1))


def describe_row(cfg, r):
    s = cfg["scenarios"][r["scenario_id"]]
    return {"scenario_id": r["scenario_id"], "title": s["title"], "position": r["position"],
            "cube_xy_cm": r["cube_xy_cm"], "angle": angle_label(r["angle"]), "offset_dir": r["offset_dir"],
            "offset_mag": s.get("offset_mag", ""), "start": s.get("start", ""), "demo": s.get("demo", ""),
            "wrist_expect": s.get("wrist_expect", "visible"),
            "pan_offset_deg": r.get("pan_offset_deg", ""), "pan_target_deg": r.get("pan_target_deg", ""),
            "pan_text": pan_target_text(r) if r.get("pan_target_deg") not in (None, "") and not s.get("wrist_start_region")
            and not s.get("error_in_rec") else "",
            "label": s.get("label", r["scenario_id"]), "pace": cfg.get("pace_text", ""), "angle_raw": r.get("angle", ""), "start_height": s.get("start_height", ""), "via": s.get("via", ""),
            "start_xy_cm": r.get("start_xy_cm", ""), "error_in_rec": bool(s.get("error_in_rec")),
            "x_label": s.get("x_label", "시작(오답)"),
            "type": s["type"], "error_kind": r.get("error_kind") or s.get("error_kind", ""),
            "pan_error_direction": r.get("pan_error_direction", ""), "nominal_pan_error_deg": r.get("nominal_pan_error_deg", ""),
            "local_alignment_type": r.get("local_alignment_type", ""), "nominal_local_error_cm": r.get("nominal_local_error_cm", ""),
            "start_pose_type": r.get("start_pose_type", ""), "wrist_visibility_target": r.get("wrist_visibility_target", ""),
            "approach_stage_expected": r.get("approach_stage_expected", ""),
            "setup_from": s.get("setup_from", ""),
            # 준비 단계에서 R1 오차 상태를 만드는 줄 (3차 start_pose_type · 4차 approach_stage_expected)
            "r1_setup": bool(r.get("start_pose_type") or r.get("approach_stage_expected")),
            "cube_position_source": r.get("cube_position_source") or position_source(cfg, r["position"])[0],
            "pan_ref_deg": round(pan_ref(cfg, r["position"]), 1), "pan_ref_source": pan_ref_source(cfg, r["position"]),
            "approach_depth_category": s.get("approach_depth_category", ""),
            "wrist_start_region": start_region(s),
            "retake_of": r.get("retake_of", "")}


def start_region(s):
    """R2 시작 영역 (손목 영상, u·v 0–1) — 'close_zone' 이면 닫기 영역. 없으면 None."""
    reg = s.get("wrist_start_region")
    if reg == "close_zone":
        z = wrist_zone()
        return {"u": z["u"], "v": z["v"]} if z else None
    return reg or None


def in_region(w, reg):
    """손목 검출 w (vision()['wrist']) 의 큐브 중심이 영역 안인가. 반환 True/False/None(검출 없음)."""
    if not reg or not w or not w.get("detected"):
        return None
    u, v = (w["dx"] + 1) / 2, (w["dy"] + 1) / 2
    return reg["u"][0] <= u <= reg["u"][1] and reg["v"][0] <= v <= reg["v"][1]


LOCAL_KO = {"depth_short": "덜 들어감", "cube_ahead": "큐브가 앞", "fingers_left": "손가락이 왼쪽", "fingers_right": "손가락이 오른쪽",
            "near_aligned": "정렬됨"}
KIND_KO = {"wrong_target": "Pan 목표 오차", "overshoot": "목표 지나침", "drift": "접근 중 Pan 흐름", "pan_misaligned": "Pan 방향 오차",
           "depth": "접근 깊이 부족", "ahead": "큐브가 손가락 앞", "lateral": "좌우 어긋남", "none": "정상 파지 준비"}
POSE_KO = {"home_near": "쉬는 자세 근처", "mid_approach": "접근 중간"}
STAGE_KO = {"early": "접근 초반", "mid": "접근 중간", "late": "접근 후반 (큐브 가까이)"}
STAGE_SHORT = {"early": "초반", "mid": "중간", "late": "후반"}
KIND_KO.update({"initial_direction": "초기 방향 오류", "drift_away": "접근 중 멀어짐 → 반전", "lost_in_wrist": "손목에서 놓침"})
VIS_KO = {"visible": "보임", "edge": "가장자리", "absent": "안 보임", "visible_or_edge": "보임/가장자리", "unknown": "모름"}
DEPTH_KO = {"partial": "일부 진입", "not_entered": "진입 전", "lateral_offset": "깊이 근처·좌우 어긋남", "sufficient": "충분"}


def wrist_visibility(w):
    """손목 검출 → visible / edge (상자 테두리에 닿음) / absent. 검출 정보 없으면 unknown."""
    if not w:
        return "unknown"
    if not w.get("detected"):
        return "absent"
    return "edge" if w.get("touches_edge") else "visible"


def visibility_matches(target, now):
    if target in ("", None) or now == "unknown":
        return None
    return now in ("visible", "edge") if target == "visible_or_edge" else now == target


def front_visibility(f, max_cm=4.0):
    """front 검출 → visible (계획 K 와 max_cm 안) / offset (멀리 검출) / not_detected."""
    if not f:
        return "unknown"
    if not f.get("detected"):
        return "not_detected"
    return "visible" if f.get("dist_planned_cm", 0) <= max_cm else "offset"


def pose_class(cfg, state):
    """시작 관절값 → home_near / mid_approach (설정 start_pose_types 기준, 대략). 관절값 없으면 ''."""
    s = _joint_dict(state)
    if not s:
        return ""
    h = (cfg.get("start_pose_types") or {}).get("home_near", {})
    return "home_near" if s["shoulder_lift"] <= h.get("lift_max", -80) and s["elbow_flex"] >= h.get("elbow_min", 70) else "mid_approach"


def approach_stage(cfg, state, pos):
    """시작 관절값 → (early|mid|late, 진행률). 진행률 = (lift − 쉬는 자세 lift) / (이 큐브 거리의 d2 파지 lift − 쉬는 자세 lift).
    큐브 거리 = 밑동 ~ 큐브 자리 (K·자유 점·검출). 관절값 없으면 ('', None). 대략값 (설정 start_stages)."""
    s = _joint_dict(state)
    if not s or not math.isfinite(s.get("shoulder_lift", float("nan"))):
        return "", None
    c = cfg.get("start_stages") or {}
    rest = c.get("rest_lift", -103.0)
    try:
        r = k_radius(cfg, pos)
    except KeyError:
        r = 20.0
    g = c.get("grasp_lift_a", -65.2) + c.get("grasp_lift_b", 4.04) * r
    p = (s["shoulder_lift"] - rest) / max(g - rest, 1.0)
    st = "early" if p < c.get("early_max", 0.4) else "mid" if p < c.get("mid_max", 0.85) else "late"
    return st, round(p, 2)


def scenario_checks(cfg, row, state, vis, calib=0.0):
    """R1 시나리오 조건 (막지 않음). 반환 [(ok: True/False/None, 항목, 글)] — None = 판단 못 함.
    단계 · 손목 가시성 · front 가시성 · Pan 오차 (방향·크기, 후보는 참고)."""
    out = []
    if not row or not row.get("r1_setup"):
        return out
    st, prog = approach_stage(cfg, state, row["position"])
    exp = [x for x in (row.get("approach_stage_expected") or "").split("|") if x]
    if st:
        out.append((st in exp if exp else None, "stage", f"접근 단계 지금 {STAGE_SHORT.get(st)} ({prog:.2f}) · 계획 "
                    + "/".join(STAGE_SHORT.get(x, x) for x in exp)))
    if vis:
        wv = wrist_visibility(vis.get("wrist"))
        tgt = row.get("wrist_visibility_target")
        if tgt not in ("", None, "any"):
            out.append((visibility_matches(tgt, wv), "wrist", f"손목 큐브 지금 {VIS_KO.get(wv)} · 계획 {VIS_KO.get(tgt)}"))
        fv = front_visibility(vis.get("front"))
        out.append((fv == "visible" if fv != "unknown" else None, "front",
                    f"front 큐브 {'보임' if fv == 'visible' else '계획 자리에서 멀리 검출' if fv == 'offset' else '안 보임'}"))
    s = _joint_dict(state)
    if s:
        err = s["shoulder_pan"] - pan_ref(cfg, row["position"]) - float(calib or 0)
        want = {"left": -1, "right": 1}.get(row.get("pan_error_direction"))
        side = "왼쪽(−)" if err < 0 else "오른쪽(+)"
        ok = (abs(err) >= 8 and (want is None or err * want > 0))
        out.append((ok, "pan", f"Pan 오차 지금 {side} {abs(err):.0f}° · 계획 "
                    + {"left": "왼쪽", "right": "오른쪽"}.get(row.get("pan_error_direction"), "") + f" {row.get('nominal_pan_error_deg', '')}° (후보)"))
    return out


def _zigzag(x, th):
    """1차원 열 → 꺾인 점 [(i, 값)] (th 이상 되돌아가야 방향이 바뀐 것으로 봄). 첫 점·마지막 극점 포함."""
    pts = [(0, x[0])]
    d, ei, ev = 0, 0, x[0]
    for i in range(1, len(x)):
        v = x[i]
        if d == 0:
            if abs(v - x[0]) >= th:
                d, ei, ev = (1 if v > x[0] else -1), i, v
        elif (v - ev) * d > 0:
            ei, ev = i, v
        elif abs(v - ev) >= th:
            pts.append((ei, ev))
            d, ei, ev = -d, i, v
    if d != 0:
        pts.append((ei, ev))
    return pts


def grasp_start(grip_cmd, open_min=15.0, drop=10.0):
    """명령 그리퍼 열 → 파지 시작 프레임: 처음 열린(>open_min) 뒤 그때까지의 최대 열림에서 drop 이상 줄어든 첫 프레임. 없으면 None.
    (d2 의 '<10' 규칙은 리더를 끝까지 닫지 않는 시연에서 못 찾음 — 11-02 r1_try2 ep0 은 12.8 까지만 닫음.)"""
    import numpy as _np

    g = _np.asarray(grip_cmd, float)
    op = _np.where(g > open_min)[0]
    if not len(op):
        return None
    mx = g[op[0]]
    for i in range(op[0], len(g)):
        mx = max(mx, g[i])
        if g[i] < mx - drop:
            return i
    return None


def pan_recovery(pan, fps, ref, pre=None, grip_cmd=None, th=3.0):
    """R1 복구 측정 (녹화 pan 열 · 큐브 기준 pan · 준비 단계 마지막 pan 열 · 명령 그리퍼 열). 값만 돌려준다.
    구간 = 녹화 시작 ~ 파지 시작 (grasp_start; 없으면 끝까지) — 상자로 옮기는 Pan 은 뺌.
    이동 = th° 이상 이어진 움직임. 'toward' = 큐브 기준까지 거리 |pan − ref| 를 줄임, 'away' = 늘림.
    반전 = 이동 방향(부호)이 바뀐 첫 꺾임 (그 꺾임이 준비 단계면 시각 음수 = 준비 때 이미 되돌리기 시작)."""
    import numpy as _np

    pan = _np.asarray(pan, float)
    if len(pan) < 2:
        return {}
    kg = grasp_start(grip_cmd) if grip_cmd is not None and len(grip_cmd) == len(pan) else None
    upto = kg if kg else len(pan)
    pre = _np.asarray(pre if pre is not None and len(pre) else [], float)
    k = 5
    seq = _np.concatenate([pre, pan[:max(upto, 2)]])
    if len(seq) >= k:
        seq = _np.convolve(_np.pad(seq, (k // 2, k // 2), mode="edge"), _np.ones(k) / k, mode="valid")
    n0 = len(pre)
    pts = _zigzag(seq, th)
    segs = []
    for (i0, v0), (i1, v1) in zip(pts, pts[1:]):
        segs.append({"i0": i0, "i1": i1, "d": round(float(v1 - v0), 1), "dir": "toward" if abs(v1 - ref) < abs(v0 - ref) else "away"})
    # 녹화 안 부분이 th° 이상인 이동만 '녹화 중 이동' (준비 단계에서 이어진 움직임의 꼬리는 뺌)
    rec = [{**g, "d": round(float(seq[g["i1"]] - seq[max(g["i0"], n0)]), 1)} for g in segs
           if g["i1"] > n0 and abs(seq[g["i1"]] - seq[max(g["i0"], n0)]) >= th]
    pre_seg = [{**g, "d": round(float(seq[min(g["i1"], n0 - 1)] - seq[g["i0"]]), 1)} for g in segs if g["i0"] < n0 - 1]
    first = rec[0] if rec else None
    out = {"start_pan_deg": round(float(pan[0]), 1), "start_error_deg": round(float(pan[0] - ref), 1),
           "setup_pan_motion": (pre_seg[-1]["dir"] + f" {pre_seg[-1]['d']:+.1f}°") if pre_seg else ("still" if n0 else "unknown"),
           "first_pan_move_dir": first["dir"] if first else "none", "first_pan_move_deg": first["d"] if first else 0.0,
           "pan_reversal": False, "pan_reversal_t_s": "", "pan_reversal_kind": "", "pan_change_before_reversal_deg": "",
           "pan_change_after_reversal_deg": "", "pan_reversals_in_rec": sum(1 for a, b in zip(segs, segs[1:]) if a["i1"] >= n0),
           "grasp_start_t_s": round(kg / fps, 2) if kg else "", "pan_error_at_grasp_deg": round(float(pan[kg] - ref), 1) if kg else ""}
    for a, b in zip(segs, segs[1:]):
        if b["i1"] > n0:
            out.update(pan_reversal=True, pan_reversal_t_s=round((a["i1"] - n0) / fps, 2), pan_reversal_kind=f"{a['dir']}→{b['dir']}",
                       pan_change_before_reversal_deg=a["d"], pan_change_after_reversal_deg=b["d"])
            break
    return out


def setup_path(cfg, row, n=16):
    """준비 단계 (녹화 안 함) 에서 오차 상태를 만들 때의 출발 쪽과 경로 (탁자 cm). 없으면 None.
    setup_from: cube = 큐브 방향에서 출발 (B1 멀어짐 · B3 놓침), mirror = 큐브 반대쪽 같은 각도에서 출발 (B2 지나침),
    rest = 쉬는 자세 pan 에서 출발 (A 초기 방향).
    반환 {"from": (x, y), "path": [(x, y)…] 출발 → 멈출 곳(주황 선 끝), "from_pan": °}."""
    kind = row.get("setup_from")
    if kind not in ("cube", "mirror", "rest") or row.get("pan_target_deg") in (None, ""):
        return None
    s = cfg["scenarios"][row["scenario_id"]]
    pos = row["position"]
    off = float(row.get("pan_offset_deg") or 0)
    ref = pan_ref(cfg, pos)
    lim = float(cfg["safety"]["pan_abs_block_deg"]) - 3.0
    p_from = ref if kind == "cube" else float(cfg.get("rest_pan_deg", -4.0)) if kind == "rest" else max(-lim, min(lim, ref - off))
    r = k_radius(cfg, pos) + float(s.get("start_radial_cm", 0) or 0)
    f0, f1 = pan_phi(cfg, pos, p_from), pan_phi(cfg, pos, ref + off)
    path = [polar_xy(cfg, f0 + (f1 - f0) * i / (n - 1), r) for i in range(n)]
    return {"from": path[0], "path": path, "from_pan": round(p_from, 1)}


def wrist_reacquire(seen, dt):
    """손목 검출 열 (True/False, dt 초 간격) → (처음 보임 여부, 다시 찾음 여부, 처음 보인 시각 s). 두 번 이어 보이면 찾음."""
    if not seen:
        return None, None, ""
    if seen[0]:
        return True, "", ""
    for i in range(len(seen) - 1):
        if seen[i] and seen[i + 1]:
            return False, True, round(i * dt, 1)
    return False, False, ""


def pan_error_confidence(calib_deg):
    """명목 Pan 오차 추정의 신뢰도 (말로): K 기준 pan 은 d2 중앙값이라 판마다 ±9° (11-02 연습 6판).
    low = 세션 보정(c) 없음 · medium = c 보정으로 세션 치우침을 뺌 (판마다 흔들림은 남음). high 는 쓰지 않음."""
    return "medium" if calib_deg not in (None, "", 0, 0.0) else "low"


# ---------------------------------------------------------------- 색 검출 (설정의 HSV — check_dataset 과 같은 범위)

def red_ranges(cfg):
    return cfg["_base"]["detection"]["colors"]["red"]


def find_red(img_rgb, cfg, min_area=None, open_px=3):
    """RGB 이미지에서 빨강 덩어리 [(넓이, cx, cy, (x, y, w, h))] 큰 것부터."""
    import cv2

    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    m = np.zeros(hsv.shape[:2], np.uint8)
    for r in red_ranges(cfg):
        lo = np.array([r["h"][0], r["s"][0], r["v"][0]], np.uint8)
        hi = np.array([r["h"][1], r["s"][1], r["v"][1]], np.uint8)
        m |= cv2.inRange(hsv, lo, hi)
    if open_px:
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((open_px, open_px), np.uint8))
    n, _, stats, cents = cv2.connectedComponentsWithStats(m)
    min_area = cfg["_base"]["detection"].get("min_blob_area_px", 100) if min_area is None else min_area
    out = [(int(stats[i, 4]), float(cents[i][0]), float(cents[i][1]), tuple(int(v) for v in stats[i, :4]))
           for i in range(1, n) if stats[i, 4] >= min_area]
    return sorted(out, reverse=True)


def front_H(cfg):
    return np.array(cfg["_base"]["camera"]["front_640x480"]["H_cm_to_px"], float)


def px_to_cm(H, px):
    v = np.linalg.inv(H) @ np.array([px[0], px[1], 1.0])
    return float(v[0] / v[2]), float(v[1] / v[2])


def cm_to_px(H, xy):
    v = H @ np.array([xy[0], xy[1], 1.0])
    return float(v[0] / v[2]), float(v[1] / v[2])


def vision(front, wrist, cfg, planned_pos=None):
    """front·wrist RGB 한 장씩 → 큐브 검출 요약 (FK 안 씀). 좌표 신뢰도는 근거와 함께 적는다."""
    out = {"wrist": {"detected": False}, "front": {"detected": False}}
    if wrist is not None:
        b = find_red(wrist, cfg, min_area=150)
        if b:
            a, cx, cy, bb = b[0]
            h, w = wrist.shape[:2]
            out["wrist"] = {"detected": True, "area_px": a, "cx": round(cx, 1), "cy": round(cy, 1),
                            "dx": round((cx - w / 2) / (w / 2), 3), "dy": round((cy - h / 2) / (h / 2), 3),
                            "bbox": bb, "touches_edge": bool(bb[0] <= 2 or bb[1] <= 2 or bb[0] + bb[2] >= w - 2 or bb[1] + bb[3] >= h - 2)}
    if front is not None:
        b = find_red(front, cfg)
        if b:
            a, cx, cy, bb = b[0]
            H = front_H(cfg)
            x, y = px_to_cm(H, (cx, cy))
            f = {"detected": True, "area_px": a, "px": [round(cx, 1), round(cy, 1)], "xy_cm": [round(x, 1), round(y, 1)],
                 "xy_conf": "front H (큐브 중심 평면, rms 2 px ≈ ±0.5 cm) — 로봇·그리퍼에 일부 가려지면 중심이 치우침",
                 "n_blobs": len(b)}
            if planned_pos:
                px, py = known_xy(cfg, planned_pos)
                f["dist_planned_cm"] = round(math.hypot(x - px, y - py), 2)
            out["front"] = f
    return out


# ---------------------------------------------------------------- 실시간 공유 파일 (/dev/shm) — 녹화 프로세스 → 화면

def _atomic_write(path, writer, mode="w"):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_")
    try:
        with os.fdopen(fd, mode) as f:
            writer(f)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json(path, obj):
    _atomic_write(path, lambda f: json.dump(obj, f, ensure_ascii=False))


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class LiveFrames:
    """front·wrist 마지막 프레임 (2×480×640×3 uint8 memmap) + 쓴 순번 (seq.json 대신 헤더 8바이트)."""

    def __init__(self, live_dir, create):
        self.path = os.path.join(live_dir, "frames.u8")
        size = 8 + 2 * int(np.prod(FRAME_SHAPE))
        if create:
            with open(self.path, "wb") as f:
                f.truncate(size)
        self.mm = np.memmap(self.path, np.uint8, "r+" if create else "r", shape=(size,))
        self.seq = self.mm[:8].view(np.uint64)
        self.img = self.mm[8:].reshape((2,) + FRAME_SHAPE)

    def put(self, i, frame):
        if frame is None or frame.shape != FRAME_SHAPE:
            return False
        self.img[i] = frame
        return True

    def bump(self):
        self.seq[0] = self.seq[0] + 1

    def get(self):
        return int(self.seq[0]), np.array(self.img[0]), np.array(self.img[1])


def live_dir_for(tag):
    base = "/dev/shm" if os.path.isdir("/dev/shm") else tempfile.gettempdir()
    d = os.path.join(base, f"r12_live_{tag}")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- 시도 기록 (r12_attempts.jsonl) → 판 메타데이터 (r12_episodes.csv)

EPISODE_FIELDS = ["episode_id", "episode_index", "dataset_group", "scenario_id", "error_kind", "cube_position", "cube_xy_planned_cm", "cube_rotation",
                  "intended_offset_direction", "intended_offset_magnitude",
                  # R1 (4차 지시서): 시작 상태 · 오차 · 가시성 · 복구 측정 (녹화 프로세스 pan 열·축소 손목 영상, 대략 — QA 가 dataset 으로 다시 잼)
                  "approach_stage_expected", "approach_stage_at_start", "approach_progress", "start_pose_type", "start_pan_deg",
                  "pan_error_direction", "nominal_pan_error_deg", "measured_start_pan_error_deg", "pan_reference_source",
                  "pan_error_estimate_confidence", "wrist_visibility_target", "wrist_cube_visibility", "front_cube_visibility",
                  "cube_xy_cm_used", "cube_position_source",
                  "setup_pan_motion", "first_pan_move_dir", "first_pan_move_deg", "pan_reversal", "pan_reversal_t_s", "pan_reversal_kind",
                  "pan_change_before_reversal_deg", "pan_change_after_reversal_deg", "pan_reversals_in_rec", "cube_reacquired_in_wrist",
                  "cube_reacquire_t_s", "grasp_start_t_s", "pan_error_at_grasp_deg",
                  "recovery_completed", "start_safety_confirmed", "scenario_override",
                  # R2
                  "local_alignment_type", "nominal_local_error_cm", "cube_relative_position_in_wrist", "approach_depth_category",
                  "first_close_result", "r2_wrist_start_in_region",
                  "pan_reference_deg", "pan_calib_deg", "planned_pan_offset_deg",
                  "start_pan_offset_deg", "start_joint_state", "start_gripper_state",
                  "start_leader_action", "start_safety_warn", "wrist_cube_at_start", "front_cube_xy_cm", "cube_position_confidence",
                  "physical_depth", "first_grasp_success", "final_success", "retry_count", "operator_notes",
                  "realign_mark_frames", "realign_mark_pan",
                  "frames", "recording_fps", "loop_hz_mean", "late_ticks", "camera_stall_ticks", "start_shift_deg", "attempt_id", "run_id",
                  "recorded_at", "retake_of"]


def append_event(sess_dir, ev):
    ev = dict(ev)
    ev.setdefault("t", datetime.datetime.now().isoformat(timespec="seconds"))
    with open(os.path.join(sess_dir, ATTEMPTS), "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def read_events(sess_dir):
    out = []
    try:
        with open(os.path.join(sess_dir, ATTEMPTS)) as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def fold_attempts(events):
    """attempt_id 별로 사건을 모은다. 반환 {attempt_id: dict}."""
    att = {}
    for ev in events:
        aid = ev.get("attempt_id")
        if not aid:
            continue
        a = att.setdefault(aid, {"attempt_id": aid, "status": "open"})
        k = ev.get("ev")
        if k == "armed":
            a.update(ep=ev["ep"], run_id=ev.get("run_id"), armed=ev)
        elif k == "rec_start":
            a["rec_start"] = ev
        elif k == "rec_end":
            a["rec_end"] = ev
        elif k == "vision":
            a["vision"] = ev.get("vision")
        elif k == "recovery":
            a["recovery"] = ev
        elif k == "mark":
            a.setdefault("marks", []).append(ev)
        elif k == "label":
            a["label"] = {x: ev.get(x) for x in ("first_grasp_success", "final_success", "retry_count", "operator_notes", "recovery_completed")}
        elif k == "discarded":
            a["status"] = "discarded"
        elif k == "saved":
            a["status"] = "saved"
            a["saved_t"] = ev.get("t")
    return att


def _fmt_joints(d):
    d = _joint_dict(d) or {}
    return ";".join(f"{SHORT[j]}={d[j]:.1f}" for j in JOINTS if j in d)


def first_close_result(lab):
    """R2 첫 닫힘 결과 (사람 입력 1/2/3 에서): grasped · missed_then_retry · failed. 입력 없으면 ''."""
    if not lab or lab.get("final_success") is None:
        return ""
    return "grasped" if lab.get("first_grasp_success") else ("missed_then_retry" if lab.get("final_success") else "failed")


def build_episode_rows(sess_dir, cfg, plan_rows, total_episodes):
    """저장된 판 (dataset total_episodes 기준) 마다 가장 마지막 'saved' 시도 → r12_episodes.csv 줄. 문제 목록도 돌려준다."""
    att = fold_attempts(read_events(sess_dir))
    by_ep = {}
    for a in att.values():
        if a["status"] == "saved" and "ep" in a:
            by_ep[a["ep"]] = a  # 같은 번호가 다시 저장된 적은 없다 (lerobot 은 버린 번호를 다시 씀 → 마지막 saved 가 남음)
    rows, problems = [], []
    meta = read_json(os.path.join(sess_dir, PLAN_META), {}) or {}
    overrides = {}
    for e in read_events(sess_dir):
        if e.get("ev") == "override":
            overrides.setdefault(e.get("ep"), []).append(e)
    for ep in range(total_episodes):
        pr = plan_rows[ep] if ep < len(plan_rows) else None
        a = by_ep.get(ep)
        if pr is None:
            problems.append(f"episode {ep}: 계획 줄 없음")
        if a is None:
            problems.append(f"episode {ep}: 저장 기록(r12_attempts.jsonl 'saved') 없음")
        s = cfg["scenarios"].get(pr["scenario_id"], {}) if pr else {}
        arm = (a or {}).get("armed", {})
        rs, re_ = (a or {}).get("rec_start", {}), (a or {}).get("rec_end", {})
        vis = (a or {}).get("vision") or {}
        lab = (a or {}).get("label") or {}
        fr = vis.get("front", {})
        warn = [c[2] for c in arm.get("checks", []) if c[0] == "WARN"]
        st0 = _joint_dict(arm.get("state"))
        calib = arm.get("pan_calib")
        r1 = bool(pr) and pr.get("type") == "R1"
        rec_ = (a or {}).get("recovery") or {}
        r2 = bool(pr) and pr.get("type") == "R2"
        wv = wrist_visibility(vis.get("wrist")) if vis else "unknown"
        ww = vis.get("wrist") or {}
        rows.append({
            "episode_id": f"{meta.get('repo_id', os.path.basename(sess_dir))}:{ep:04d}",  # dataset 마다 고유 (d2+R1+R2 를 섞어도 안 겹침)
            "episode_index": ep,
            "dataset_group": pr["type"] if pr else "",
            "scenario_id": pr["scenario_id"] if pr else "",
            "cube_position": pr["position"] if pr else "",
            "start_pose_type": pr.get("start_pose_type", "") if pr else "",
            "approach_stage_expected": pr.get("approach_stage_expected", "") if pr else "",
            "approach_stage_at_start": approach_stage(cfg, arm.get("state"), pr["position"])[0] if r1 else "",
            "approach_progress": (approach_stage(cfg, arm.get("state"), pr["position"])[1] or "") if r1 else "",
            "start_pan_deg": f"{st0['shoulder_pan']:.1f}" if r1 and st0 else "",
            "pan_reference_source": pan_ref_source(cfg, pr["position"]) if r1 else "",
            "cube_xy_cm_used": pr.get("cube_xy_cm", "") if pr else "",
            "cube_position_source": (pr.get("cube_position_source") or position_source(cfg, pr["position"])[0]) if pr else "",
            **({k_: ("" if rec_.get(k_) is None else rec_.get(k_)) for k_ in (
                "setup_pan_motion", "first_pan_move_dir", "first_pan_move_deg", "pan_reversal", "pan_reversal_t_s", "pan_reversal_kind",
                "pan_change_before_reversal_deg", "pan_change_after_reversal_deg", "pan_reversals_in_rec", "cube_reacquired_in_wrist",
                "cube_reacquire_t_s", "grasp_start_t_s", "pan_error_at_grasp_deg")}
               if r1 else {}),
            "scenario_override": ";".join(f"{o.get('key')}" for o in overrides.get(ep, [])) if r1 else "",
            "measured_start_pan_error_deg": (f"{st0['shoulder_pan'] - pan_ref(cfg, pr['position']) - float(calib or 0):+.1f}"
                                             if r1 and st0 else ""),
            "pan_error_estimate_confidence": pan_error_confidence(calib) if r1 else "",
            "wrist_visibility_target": pr.get("wrist_visibility_target", "") if pr else "",
            "wrist_cube_visibility": wv if pr else "",
            "front_cube_visibility": front_visibility(vis.get("front")) if vis else "unknown",
            "recovery_completed": ({True: "yes", False: "no"}.get(lab.get("recovery_completed"), "") if r1 else ""),
            "start_safety_confirmed": {True: "yes", False: "no"}.get(arm.get("safety_confirmed"), "") if r1 else "",
            "cube_relative_position_in_wrist": (f"u={(ww['dx'] + 1) / 2:.2f};v={(ww['dy'] + 1) / 2:.2f};area={ww['area_px'] / (640 * 480):.3f}"
                                                + (";edge" if ww.get("touches_edge") else "") if ww.get("detected") else wv) if r2 else "",
            "approach_depth_category": s.get("approach_depth_category", "") if r2 else "",
            "first_close_result": first_close_result(lab) if r2 else "",
            "pan_calib_deg": "" if calib is None else calib,
            "recording_fps": cfg.get("fps", 30),
            "cube_xy_planned_cm": pr["cube_xy_cm"] if pr else "",
            "cube_rotation": pr["angle"] if pr else "",
            "intended_offset_direction": pr["offset_dir"] if pr else "",
            "error_kind": (pr.get("error_kind") or s.get("error_kind", "")) if pr else "",
            "pan_error_direction": pr.get("pan_error_direction", "") if pr else "",
            "nominal_pan_error_deg": pr.get("nominal_pan_error_deg", "") if pr else "",
            "local_alignment_type": pr.get("local_alignment_type", "") if pr else "",
            "nominal_local_error_cm": pr.get("nominal_local_error_cm", "") if pr else "",
            "r2_wrist_start_in_region": ({True: "yes", False: "no", None: "not_detected"}[in_region(vis.get("wrist"), start_region(s))]
                                         if pr and start_region(s) and vis else ""),
            "intended_offset_magnitude": s.get("offset_mag", ""),
            "pan_reference_deg": pan_ref(cfg, pr["position"]) if pr else "",
            "planned_pan_offset_deg": pr.get("pan_offset_deg", "") if pr else "",
            "start_pan_offset_deg": (f"{st0['shoulder_pan'] - pan_ref(cfg, pr['position']):+.1f}"
                                     if arm.get("state") and pr else ""),
            "start_joint_state": _fmt_joints(arm.get("state")),
            "start_gripper_state": f"{st0['gripper']:.1f}" if st0 else "",
            "start_leader_action": _fmt_joints(arm.get("action")),
            "start_safety_warn": " | ".join(warn),
            "wrist_cube_at_start": (f"dx={vis['wrist']['dx']:+.2f};dy={vis['wrist']['dy']:+.2f};area={vis['wrist']['area_px']}"
                                    + (";edge" if vis["wrist"].get("touches_edge") else "")) if vis.get("wrist", {}).get("detected")
                                   else ("not_detected" if vis else "unknown"),
            "front_cube_xy_cm": ",".join(str(v) for v in fr["xy_cm"]) if fr.get("detected") else ("not_detected" if vis else "unknown"),
            "cube_position_confidence": (position_source(cfg, pr["position"])[1] + ("; front H 검출 일치 ≤2 cm" if fr.get("dist_planned_cm", 99) <= 2 else
                                         "; front 검출 없음/불일치 — 확인 필요")) if pr else "",
            "physical_depth": "unknown",
            "first_grasp_success": lab.get("first_grasp_success", ""),
            "final_success": lab.get("final_success", ""),
            "retry_count": lab.get("retry_count", ""),
            "operator_notes": lab.get("operator_notes", ""),
            "realign_mark_frames": ";".join(str(m.get("frame")) for m in (a or {}).get("marks", [])),
            "realign_mark_pan": ";".join(f"{m['pan']:.1f}" for m in (a or {}).get("marks", []) if m.get("pan") is not None),
            "frames": re_.get("frames", ""),
            "loop_hz_mean": re_.get("loop_hz_mean", ""),
            "late_ticks": re_.get("late_ticks", ""),
            "camera_stall_ticks": re_.get("stall_ticks", ""),
            "start_shift_deg": rs.get("shift_from_armed_deg", ""),
            "attempt_id": (a or {}).get("attempt_id", ""),
            "run_id": (a or {}).get("run_id", ""),
            "recorded_at": (a or {}).get("saved_t", ""),
            "retake_of": pr.get("retake_of", "") if pr else "",
        })
    return rows, problems


def write_episode_rows(sess_dir, rows):
    def w(f):
        wr = csv.DictWriter(f, fieldnames=EPISODE_FIELDS)
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    _atomic_write(os.path.join(sess_dir, EPISODES_CSV), w)


def session_dir(session):
    m = re.match(r"^(practice|main|main_k8)/([a-z0-9_]+)$", session.strip("/"))
    if not m:
        raise PlanError(f"세션 이름 형식: <practice|main|main_k8>/<영어 소문자·숫자·밑줄> (받은 값 {session})")
    return os.path.join(RUNS_ROOT, m.group(1), m.group(2))


PILOT_GROUPS = ("r1_pilot", "r2_pilot")  # 11-02 정의: R1 16 + R2 32 = 48편


def program_progress(cfg, override=None):
    """48편 파일럿 시나리오별 [(type, scenario_id, 저장, 목표)]. 세션 계획 r12_plan.csv 상태로 센다 (계획이 없으면 설정 수량, 저장 0).
    override = {세션: {scenario_id: (저장, 목표)}} — 지금 녹화 중인 세션은 실행 중 값으로."""
    out = []
    for gname in PILOT_GROUPS:
        g = group_of(cfg, gname)
        per = (override or {}).get(g["session"])
        if per is None:
            per = {}
            try:
                rows = read_plan(session_dir(g["session"]))
            except (OSError, PlanError):
                rows = None
            if rows is None:
                per = {sid: (0, int(s["count"])) for sid, s in scenarios_of(cfg, g["type"])}
            else:
                for r in rows:
                    if r["status"] == EXCLUDED:
                        continue
                    d, t = per.get(r["scenario_id"], (0, 0))
                    per[r["scenario_id"]] = (d + int(r["status"] == RECORDED), t + 1)
        out += [(g["type"], sid, d, t) for sid, (d, t) in per.items()]
    return out


def dataset_total(sess_dir):
    info = read_json(os.path.join(sess_dir, "dataset", "meta", "info.json"))
    return None if info is None else int(info.get("total_episodes", 0))
