#!/home/user/so101-env/bin/python
"""SG50 계획 · 판 기록 (r12 수집 도구 위에 얹음 — 녹화 경로 · dataset 형식은 r12 그대로).

  r12_common.make_plan 이 그룹 planner: sg50 이면 make_rows() 를 부른다 (r12_plan.csv 와 같은 칸).
  r12_collect.py sync/record 뒤 write_episodes() 가 <세션>/sg_episodes.csv 를 만든다 (r12_episodes.csv + 계획 + 설정 + 보정 해시).

  sg_plan.py sheet    --session S [--config C]       # <세션>/sg_plan.csv · sg_plan.md (배치표)
  sg_plan.py episodes --session S [--config C]       # <세션>/sg_episodes.csv 다시 만들기 (dataset · 기록은 읽기만)
  sg_plan.py split    --session S --episodes 3,7 --to eval_holdout --reason "..." [--config C]   # 학습 전 평가용 분리 표시
"""

import csv
import datetime
import hashlib
import json
import collections
import math
import os
import random
import time
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

POSES = ("P0", "P1", "P2", "P3")
SG_PLAN_CSV = "sg_plan.csv"
SG_EPISODES_CSV = "sg_episodes.csv"
SPLIT_JSON = "sg_split.json"
HOME = os.path.expanduser("~")
CALIB = {"follower": "~/.cache/huggingface/lerobot/calibration/robots/so_follower/my_arm.json",
         "leader": "~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_leader.json"}


def sg(cfg):
    s = cfg.get("sg50")
    if not s:
        raise rc.PlanError("설정에 sg50 블록이 없어요 (config/sg50.yaml 을 --config 로)")
    return s


def bearing(cfg, pos):
    (x, y), (bx, by) = rc.known_xy(cfg, pos), rc.base_xy(cfg)
    return math.degrees(math.atan2(y - by, x - bx))


def check_eval_distance(cfg, positions):
    s = sg(cfg)
    ev = s["eval_reserved"]
    bad = []
    for p in positions:
        if s["positions"].get(p, {}).get("d2_trained") == "K":  # K 는 이미 d2 학습 위치 (H 는 학습 위치에서 ≥ 2 cm 로 정의됨) — 새 위치만 검사
            continue
        x, y = rc.known_xy(cfg, p)
        for name, (ex, ey) in ev["points"].items():
            d = math.hypot(x - ex, y - ey)
            if d < float(ev["min_dist_cm"]):
                bad.append(f"{p} ({x},{y}) ↔ 평가 자리 {name} ({ex},{ey}) {d:.1f} cm < {ev['min_dist_cm']}")
    if bad:
        raise rc.PlanError("평가 전용 자리와 너무 가까운 수집 위치:\n  " + "\n  ".join(bad))


PIN_REGION_RE = r"^K(\d)p(\d+)$"  # 2026-11-12 sg_pin: 영역 무작위 점 둘째 묶음 (K4p3 = K4 영역 3번, 영역마다 8) — K#r# (예비3) 과 따로, 기존 계획은 안 바뀜
REGION_RE = r"^K(\d)r(\d+)$"  # 2026-11-06 예비3: K 둘레 영역 무작위 점 이름 (K4r2 = K4 영역 2번) — 좌표는 설정 free_points 에 고정


def pos_info(s, p):
    """설정 positions 정보. K#r# (영역 무작위 점) 는 좌표 고정 · 탁자 표시 없음 → confirmed True, d2_trained 'K 영역 무작위'."""
    import re

    if re.match(REGION_RE, str(p or "")) or re.match(PIN_REGION_RE, str(p or "")):
        return {"confirmed": True, "d2_trained": f"K{p[1]} 영역 무작위 (탁자 표시 없음, front 빨간 원)"}
    return s["positions"].get(p, {})


def _in_poly(x, y, poly):
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _poly_dist(x, y, poly):
    best = 1e9
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return best


def reach_fk(reach, x, y):
    """탁자 (x, y) cm → (로봇 기준 거리 cm, pan 쪽 각 °) — reach.table_to_fk 2D 변환 (FK 좌표, pan ≈ −방향각)."""
    R = reach["table_to_fk_R"]
    t = reach["table_to_fk_t"]
    qx, qy = R[0][0] * x + R[0][1] * y + t[0], R[1][0] * x + R[1][1] * y + t[1]
    return math.hypot(qx, qy), -math.degrees(math.atan2(qy, qx))


def reach_ok(reach, x, y):
    r, pan = reach_fk(reach, x, y)
    return r <= float(reach["max_r_cm"]) + float(reach.get("side_cm", 0.0)) * math.sin(math.radians(pan))


FALLBACK_USED = []   # gen_region_points 가 좁은 간격 (min_between_fallback_cm) 을 쓴 (영역, 그 전까지 찾은 수)


def gen_region_points(cfg, over=None, letter="r"):
    """K 마다 둘레 칸 (x ± half_x, y ± half_y) 안 무작위 점 per_region 개 (조건은 sg50.known_regions). 반환 {이름: (x, y)}.
    over (2026-11-12 sg_pin) = known_regions 값 일부를 바꿈 (per_region · min_between_cm · seed), letter = 이름 글자 (K4r2 / K4p2)."""
    s = sg(cfg)
    kr = dict(s["known_regions"], **(over or {}))
    rng = random.Random(int(kr["seed"]))
    K = cfg["_base"]["known_positions"]
    hz = [z["polygon"] for z in ((cfg["_base"].get("workspace") or {}).get("hard_zones_cm") or [])]
    ev = list(s["eval_reserved"]["points"].values())
    H = rc.front_H(cfg)
    q = float(kr.get("quantize_cm", 0.5))
    bx, by = rc.base_xy(cfg)
    out = {}
    for k in sorted(K):
        kx, ky = K[k]["xy_cm"]
        got = []
        mb = float(kr["min_between_cm"])
        for _n in range(40000 if kr.get("min_between_fallback_cm") else 20000):
            if _n == 20000:  # 2026-11-12 좁은 영역 (수직 거리 한계 · 어려운 영역 · 평가 자리): 남은 점은 더 좁은 간격으로
                mb = float(kr["min_between_fallback_cm"])
                FALLBACK_USED.append((k, len(got)))
            x = round((kx + rng.uniform(-kr["half_x_cm"], kr["half_x_cm"])) / q) * q
            y = round((ky + rng.uniform(-kr["half_y_cm"], kr["half_y_cm"])) / q) * q
            if abs(x - kx) > kr["half_x_cm"] or abs(y - ky) > kr["half_y_cm"]:
                continue
            if any(_in_poly(x, y, z) or _poly_dist(x, y, z) < kr["hard_zone_margin_cm"] for z in hz):
                continue
            if any(math.hypot(x - ex, y - ey) < float(s["eval_reserved"]["min_dist_cm"]) for ex, ey in ev):
                continue
            if any(math.hypot(x - v["xy_cm"][0], y - v["xy_cm"][1]) < kr["min_from_k_cm"] for v in K.values()):
                continue
            if kr.get("max_base_dist_cm") and math.hypot(x - bx, y - by) > float(kr["max_base_dist_cm"]):  # 사용자 최대거리 (sg_reach.py)
                continue
            if kr.get("reach") and not reach_ok(kr["reach"], x, y):  # 실제 수직이 가능한 거리 안 (sg50.known_regions.reach)
                continue
            if any(math.hypot(x - a, y - b) < mb for a, b in got + list(out.values())):  # 다른 영역 점과도
                continue
            u, v = rc.cm_to_px(H, (x, y))
            if not (10 <= u <= 630 and (kr.get("front_min_y_px_by_region") or {}).get(k, kr.get("front_min_y_px", 105)) <= v <= 470):
                continue
            got.append((x, y))
            if len(got) == kr["per_region"]:
                break
        if len(got) < kr["per_region"]:
            raise rc.PlanError(f"{k} 영역에 조건 맞는 점을 {kr['per_region']} 개 못 찾음 ({len(got)})")
        for i, (x, y) in enumerate(got, 1):
            out[f"{k}{letter}{i}"] = (x, y)
    return out


def make_rows(cfg, group_name):
    g = rc.group_of(cfg, group_name)
    s = sg(cfg)
    rng = random.Random(int(g["seed"]))
    sid_of = {sc["pose"]: sid for sid, sc in cfg["scenarios"].items() if sc.get("type") == "SG" and sc.get("pose")}
    mode = s.get("start_pose_mode")
    # free (2026-11-05): 시작 자세는 매번 직접 정함 → 계획은 위치만. fixed (2026-11-06): 매 판 같은 자세 fixed_pose
    one = "FREE" if mode == "free" else (s["fixed_pose"] if mode == "fixed" else None)
    if one and one != "FREE" and one not in s["start_poses"]:
        raise SystemExit(f"sg50.fixed_pose {one} 가 start_poses 에 없어요")
    if g.get("plan") == "known_regions":  # K 8 곳 한 번씩 + 설정 free_points 의 K#r# (영역 무작위) — 같은 영역 연달아 안 옴
        import re

        reg = sorted(p for p in (cfg.get("free_points") or {}) if re.match(REGION_RE, p))
        if not reg:
            raise rc.PlanError("free_points 에 K#r# 점이 없어요 — sg_plan.py regions --write 먼저")
        if g.get("start_pose") == "planned":
            one = "PLAN"
        base_pairs = [(k, one or "S0") for k in sorted(cfg["_base"]["known_positions"])] + [(p, one or "S0") for p in reg]
        area = lambda p: p[:2]  # noqa: E731  K4 · K4r2 → K4
        pairs = []
        for _r in range(int(g.get("rounds", 1))):  # 2026-11-09 rounds: 같은 자리 묶음을 여러 번 (회차마다 따로 섞음)
            blk = list(base_pairs)
            for _ in range(5000):
                rng.shuffle(blk)
                if all(area(a[0]) != area(b[0]) for a, b in zip(blk, blk[1:])) and (not pairs or area(pairs[-1][0]) != area(blk[0][0])):
                    break
            pairs += blk
    elif g.get("plan") == "k_angles_regions":  # 2026-11-12 sg_pin: K 8 곳 × 각도 4 (32) + 영역 무작위 K#p# (영역마다 per_region, 각도 고르게)
        import re

        angs = [str(a) for a in g.get("k_angles", ["0", "L30", "R30", "45"])]
        per = int(g.get("per_region", 8))
        if g.get("start_pose") == "planned":
            one = "PLAN"
        items = [(k, a) for k in sorted(cfg["_base"]["known_positions"]) for a in angs]
        for k in sorted(cfg["_base"]["known_positions"]):
            pts = sorted((p for p in (cfg.get("free_points") or {}) if re.match(PIN_REGION_RE, p) and p[:2] == k), key=lambda p: int(p[3:]))
            if len(pts) < per:
                raise rc.PlanError(f"free_points 에 {k}p# 점이 {len(pts)} 개 (필요 {per}) — sg_plan.py regions --pin --write 먼저")
            al = [angs[i % len(angs)] for i in range(per)]
            rng.shuffle(al)
            items += list(zip(pts[:per], al))
        area = lambda p: p[:2]  # noqa: E731
        best, bsc = None, None
        for _ in range(400):  # 같은 영역 연달아 없음 · 같은 각도 3 연속 없음: 조건에 맞는 것 중 남은 수가 많은 영역부터 차례로 (안 되면 가장 적은 것)
            left, seq = list(items), []
            rng.shuffle(left)
            while left:
                cand = [it for it in left if (not seq or area(it[0]) != area(seq[-1][0])) and not (len(seq) >= 2 and seq[-1][1] == seq[-2][1] == it[1])] or left
                cnt = collections.Counter(area(it[0]) for it in left)
                m = max(cnt[area(it[0])] for it in cand)
                it = rng.choice([it for it in cand if cnt[area(it[0])] >= m - 1])
                left.remove(it)
                seq.append(it)
            sc = (sum(area(a[0]) == area(b[0]) for a, b in zip(seq, seq[1:])), sum(a[1] == b[1] == c[1] for a, b, c in zip(seq, seq[1:], seq[2:])))
            if bsc is None or sc < bsc:
                best, bsc = seq, sc
            if sc == (0, 0):
                break
        pairs = [(p, one or "S0") for p, _a in best]
        preset_angles = [a for _p, a in best]
    elif g.get("plan") == "regions_distractors":  # 2026-11-13 방해물 조건: sg_pin 의 영역 무작위 자리 K#p# 64 곳을 다시 씀 · 각도는 깨끗한 판과 다르게
        import re

        if g.get("start_pose") == "planned":
            one = "PLAN"
        clean = {r["position"]: r["angle"] for r in make_rows(cfg, g.get("angle_from", "sg_pin"))}   # 같은 자리의 깨끗한 판 각도
        nxt = {"0": "L30", "L30": "R30", "R30": "45", "45": "0"}                                     # 한 칸 밀기 → 영역 · 전체 각도 수는 그대로
        items = [(p, nxt[clean[p]]) for p in sorted(cfg.get("free_points") or {}) if re.match(PIN_REGION_RE, p) and p in clean]
        area = lambda p: p[:2]  # noqa: E731
        best, bsc = None, None
        for _ in range(400):
            left, seq = list(items), []
            rng.shuffle(left)
            while left:
                cand = [it for it in left if (not seq or area(it[0]) != area(seq[-1][0])) and not (len(seq) >= 2 and seq[-1][1] == seq[-2][1] == it[1])] or left
                cnt = collections.Counter(area(it[0]) for it in left)
                m = max(cnt[area(it[0])] for it in cand)
                it = rng.choice([it for it in cand if cnt[area(it[0])] >= m - 1])
                left.remove(it)
                seq.append(it)
            sc = (sum(area(a[0]) == area(b[0]) for a, b in zip(seq, seq[1:])), sum(a[1] == b[1] == c[1] for a, b, c in zip(seq, seq[1:], seq[2:])))
            if bsc is None or sc < bsc:
                best, bsc = seq, sc
            if sc == (0, 0):
                break
        pairs = [(p, one or "S0") for p, _a in best]
        preset_angles = [a for _p, a in best]
    elif g.get("plan") == "pilot":
        pairs = [(p[0], one) if one else tuple(p) for p in s["pilot_rows"]]
    elif one:
        pairs = [(p, one) for p in s["positions"] for _ in range(3)]
        for _ in range(2000):  # 같은 위치가 연달아 오지 않게
            rng.shuffle(pairs)
            if all(a[0] != b[0] for a, b in zip(pairs, pairs[1:])):
                break
    else:
        pos = sorted(s["positions"], key=lambda p: bearing(cfg, p))  # 로봇 오른쪽 → 왼쪽 순으로 빠지는 자세를 돌려가며
        pairs = []
        for i, p in enumerate(pos):
            skip = POSES[i % len(POSES)]
            pairs += [(p, q) for q in POSES if q != skip]
        for _ in range(2000):  # 같은 위치가 연달아 오지 않게 섞음
            rng.shuffle(pairs)
            if all(a[0] != b[0] for a, b in zip(pairs, pairs[1:])) and all(not (a[1] == b[1] == c[1]) for a, b, c in zip(pairs, pairs[1:], pairs[2:])):
                break
    check_eval_distance(cfg, {p for p, _ in pairs})
    rows = []
    for i, (p, q) in enumerate(pairs):
        x, y = rc.known_xy(cfg, p)
        conf = pos_info(s, p).get("confirmed", False)
        rows.append({"episode_index": i, "scenario_id": sid_of[q], "type": "SG", "position": p, "cube_xy_cm": f"{x:.1f},{y:.1f}",
                     "angle": str(s["cube_rotation"]["value"]), "offset_dir": "", "pan_offset_deg": "0",
                     "pan_target_deg": f"{rc.pan_ref(cfg, p):.1f}", "start_xy_cm": f"{x:.1f},{y:.1f}", "status": rc.PLANNED,
                     "retake_of": "", "frames": "", "note": "" if conf else "위치 미확정 (계산 좌표) — front 확인 후 confirmed",
                     "error_kind": "", "pan_error_direction": "", "nominal_pan_error_deg": "", "local_alignment_type": "",
                     "nominal_local_error_cm": "", "start_pose_type": "", "wrist_visibility_target": "", "approach_stage_expected": "",
                     "cube_position_source": rc.position_source(cfg, p)[0], "approach_type": "", "start_fold": "", "start_joints": "",
                     "need_turn_deg": "", "wp_dir": "", "wp_u": "", "wp_v": "", "wp_size": "", "distractors": ""})
    if g.get("plan") in ("k_angles_regions", "regions_distractors"):
        for r, a in zip(rows, preset_angles):
            r["angle"] = a
            r["need_turn_deg"] = f"{need_turn(cfg, r['position'], ANG_DEG[a]):+.1f}"
    if g.get("approach_mix"):
        assign_approach(rows, g["approach_mix"], s.get("approach") or {}, rng)
    if g.get("angle_mix"):
        assign_angles(cfg, rows, g["angle_mix"], rng)
    if g.get("start_pose") == "planned":
        assign_start(cfg, rows, g.get("fold_mix") or {k: 1 for k in s["start_folds"]}, rng)
    if g.get("waypoint"):
        assign_waypoints(cfg, rows, rng)
    if g.get("pin"):
        assign_pin_entry(cfg, rows, rng)
    if g.get("distractors"):
        assign_distractors(cfg, rows, rng)
    if g.get("pick"):
        rows = pick_diverse(rows, int(g["pick"]), rng)
    return rows


def _wp_band(d):
    """노란 프레임 방향 → 위 (225–315) · 아래 (45–135) · 옆 (0 · 180)."""
    d = float(d) % 360
    return "up" if 225 <= d <= 315 else ("down" if 45 <= d <= 135 else "side")


def pick_diverse(rows, n, rng):
    """시험용 (2026-11-10 사용자 "시험계획 3편"): 전체 계획에서 n 줄을 고름 — 각도 · 노란 프레임 위/옆/아래 · 시작 팬 쪽 (±) · 영역이 서로 다르게.
    점수 = 서로 다른 각도 수 (0° 는 반만) + 노랑 띠 수 + 팬 오프셋 부호 수 + 영역 수, 같으면 무작위. 고른 줄은 episode_index 0.. 으로 다시 매김."""
    import itertools

    best, score = None, None
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    for combo in itertools.combinations(idx, n):
        rs = [rows[i] for i in combo]
        a = {r["angle"] for r in rs}
        sc = (len(a - {"0"}) + 0.5 * ("0" in a), len({_wp_band(r["wp_dir"]) for r in rs if r.get("wp_dir")}),
              len({r.get("pan_offset_deg", "")[:1] for r in rs}), len({r["position"][:2] for r in rs}))
        if score is None or sc > score:
            best, score = rs, sc
    out = []
    for k, r in enumerate(best):
        r = dict(r)
        r["episode_index"] = k
        out.append(r)
    return out


def clip_poly(pts, lo=0.0, hi=1.0):
    """다각형 [(u, v)] 을 화면 [lo, hi]² 로 자름 (Sutherland–Hodgman)."""
    def clip(poly, inside, cross):
        out = []
        for i, p in enumerate(poly):
            q = poly[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(cross(q, p))
                out.append(p)
            elif inside(q):
                out.append(cross(q, p))
        return out

    def cx(a, b, x):
        t = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + t * (b[1] - a[1]))

    def cy(a, b, y):
        t = (y - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y)
    poly = list(pts)
    for inside, cross in ((lambda p: p[0] >= lo, lambda a, b: cx(a, b, lo)), (lambda p: p[0] <= hi, lambda a, b: cx(a, b, hi)),
                          (lambda p: p[1] >= lo, lambda a, b: cy(a, b, lo)), (lambda p: p[1] <= hi, lambda a, b: cy(a, b, hi))):
        if not poly:
            break
        poly = clip(poly, inside, cross)
    return poly


def poly_area_centroid(pts, sx=640.0, sy=480.0):
    """다각형 넓이 (px², 화면 sx × sy) · 무게중심 (u, v)."""
    if len(pts) < 3:
        return 0.0, None
    a = cxs = cys = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        cr = (x0 * sx) * (y1 * sy) - (x1 * sx) * (y0 * sy)
        a += cr
        cxs += (x0 + x1) * cr
        cys += (y0 + y1) * cr
    a *= 0.5
    if abs(a) < 1e-9:
        return 0.0, None
    return abs(a), (cxs / (6 * a), cys / (6 * a))


def waypoint_fit(ref, wp, u, v, size):
    """노란 프레임 (ref 윤곽을 (u, v) 로 옮기고 size 배) 이 화면 안 (margin) 에 다 들어오나.
    2026-11-10 allow_bottom_clip: 아래로는 잘려도 됨 (왼쪽 · 오른쪽 · 위는 margin 안, 보이는 넓이 ≥ bottom_visible_min)."""
    m = float(wp.get("margin", 0.02))
    hull = [(u + (x - ref["u"]) * size, v + (y - ref["v"]) * size) for x, y in ref["hull"]]
    if all(m <= x <= 1 - m and m <= y <= 1 - m for x, y in hull):
        return True
    if not wp.get("allow_bottom_clip"):
        return False
    if not all(m <= x <= 1 - m and y >= m for x, y in hull):
        return False
    full, _ = poly_area_centroid(hull)
    vis, _ = poly_area_centroid(clip_poly(hull))
    return full > 0 and vis / full >= float(wp.get("bottom_visible_min", 0.55))


def assign_waypoints(cfg, rows, rng):
    """판마다 노란 프레임 (2026-11-09): 8 방향 고르게 · 같은 방향 연달아 없음. 거리 · 크기 = 범위 안 무작위, 화면 밖이면 거리 ↓ · 크기 ↓."""
    import sg_sticker as sgs

    wp = sg(cfg)["waypoint"]
    ref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    if ref is None:
        raise rc.PlanError("닫기 자리 목표 (kind target) 가 없어 노란 프레임을 만들 수 없어요")
    dirs = [float(x) for x in wp["dirs"]]
    mix = wp.get("dir_mix") or {str(int(d)): 1 for d in dirs}   # 2026-11-10 dir_mix (내려오는 축 위 3 : 아래 1)
    cnt = approach_counts({str(int(float(k))): v for k, v in mix.items()}, len(rows))
    if not wp.get("dir_mix"):
        best = []
        for _ in range(len(rows)):  # 남은 수가 많은 방향 중 바로 앞과 다른 것 (같으면 무작위)
            cand = [k for k in cnt if cnt[k] > 0 and (not best or k != best[-1])] or [k for k in cnt if cnt[k] > 0]
            m = max(cnt[k] for k in cand)
            k = rng.choice([k for k in cand if cnt[k] == m])
            cnt[k] -= 1
            best.append(k)
    else:  # 2026-11-10 dir_mix: 순서를 짬 — 로봇 쪽 (위) 을 칸막이로, 그 사이에 카메라 쪽 (아래 띠) 을 1–3 개씩 · 같은 방향 연달아 없음 · 앞/뒤 절반 고르게
        downs = {k: c for k, c in cnt.items() if _wp_band(k) == "down"}
        ups = {k: c for k, c in cnt.items() if _wp_band(k) != "down"}
        nd, nu = sum(downs.values()), sum(ups.values())
        half = len(rows) // 2
        best, score = None, None
        for _ in range(3000):
            gaps = [0] + [1] * max(0, nu - 1) + [0]                       # 위 사이 칸은 1 개 이상
            left = nd - sum(gaps)
            while left > 0:
                i = rng.randrange(len(gaps))
                if gaps[i] < 3:
                    gaps[i] += 1
                    left -= 1
            dl = dict(downs)
            ul = dict(ups)
            seq, prev = [], None
            for gi, g in enumerate(gaps):
                for _k in range(g):
                    cand = [k for k in dl if dl[k] > 0 and k != prev] or [k for k in dl if dl[k] > 0]
                    k = rng.choices(cand, weights=[dl[c] for c in cand])[0]   # 남은 수에 비례 (많은 방향이 앞에 몰리지 않게)
                    dl[k] -= 1
                    seq.append(k)
                    prev = k
                if gi < len(gaps) - 1:
                    cand = [k for k in ul if ul[k] > 0]
                    k = rng.choice(cand)
                    ul[k] -= 1
                    seq.append(k)
                    prev = k
            dmax = max(abs(seq[:half].count(k) - seq[half:].count(k)) for k in cnt)
            sc = (sum(x == y for x, y in zip(seq, seq[1:])), max(0, dmax - 2), dmax)
            if score is None or sc < score:
                best, score = seq, sc
            if sc[0] == 0 and dmax <= 1:
                break
    for r, dd in zip(rows, best):
        d0, d1 = [float(x) for x in (wp.get("dist_by_dir") or {}).get(str(dd), wp["dist"])]
        s0, s1 = [float(x) for x in (wp.get("size_by_dir") or {}).get(str(dd), wp["size"])]
        th = math.radians(float(dd))
        dist, size = rng.uniform(d0, d1), rng.uniform(s0, s1)
        ok = False
        while True:
            u = round(ref["u"] + dist * math.cos(th), 3)
            v = round(ref["v"] + dist * math.sin(th) * 640.0 / 480.0, 3)
            size = round(size, 2)
            if waypoint_fit(ref, wp, u, v, size):
                ok = True
                break
            if dist > float(wp.get("min_dist", 0.07)) + 1e-9:
                dist = max(float(wp.get("min_dist", 0.07)), dist - 0.01)
            elif size > s0 - 1e-9 - 0.10:
                size -= 0.02
            else:
                break
        if not ok:
            raise rc.PlanError(f"노란 프레임 자리를 못 찾음 (방향 {dd}°)")
        r.update(wp_dir=f"{float(dd):.0f}", wp_u=f"{u:.3f}", wp_v=f"{v:.3f}", wp_size=f"{size:.2f}")


ANG_DEG = {"0": 0.0, "L30": 30.0, "R30": -30.0, "45": 45.0}
DIS_KO = {"yellow": "노랑", "orange": "주황", "blue": "파랑", "green": "초록"}
DIS_DIRS = ("robot", "box", "left", "right")   # 큐브 기준 가장 가까운 방해물의 방향: 로봇 쪽 · 상자 쪽 (로봇 반대) · 로봇 왼쪽 · 로봇 오른쪽


def parse_distractors(txt):
    """'색:x,y;색:x,y' → [(색, x, y), ...]"""
    out = []
    for part in str(txt or "").split(";"):
        if ":" in part:
            c, xy = part.split(":", 1)
            x, y = (float(v) for v in xy.split(","))
            out.append((c, x, y))
    return out


def distractor_ok(cfg, x, y, dc):
    """방해물을 놓을 수 있는 자리인가: 정한 범위 안 · front 화면 안 · 집기 어려운 영역 (쉬는 팔 아래) 밖 · 로봇 밑동 둘레 밖."""
    ar = dc["area_cm"]
    if not (ar["x"][0] <= x <= ar["x"][1] and ar["y"][0] <= y <= ar["y"][1]):
        return False
    u, v = rc.cm_to_px(rc.front_H(cfg), (x, y))
    if not (15 <= u <= 625 and 40 <= v <= 465):
        return False
    hz = [z["polygon"] for z in ((cfg["_base"].get("workspace") or {}).get("hard_zones_cm") or [])]
    if any(_in_poly(x, y, z) for z in hz):
        return False
    bx, by = rc.base_xy(cfg)
    return math.hypot(x - bx, y - by) >= float(dc.get("base_keepout_cm", 9))


def assign_distractors(cfg, rows, rng):
    """2026-11-13 방해물 (다른 색 큐브, d2 T3 와 같은 색) 자리 — 판마다 계획표가 정함 (sg50.distractors).
    개수 counts 비율 · '가장 가까운 방해물' 의 거리 (near / far 절반씩) × 방향 (로봇 쪽 · 상자 쪽 · 왼쪽 · 오른쪽 고르게) · 색은 전체에서 고르게 (한 판에 같은 색 max_per_color 개까지).
    가장 가까운 것은 큐브에서 그 방향 (± jitter°) 으로 정한 거리, 나머지는 그보다 gap_cm 넘게 먼 무작위 자리. 서로 min_between_cm 이상. 계획 칸 distractors · note."""
    dc = sg(cfg)["distractors"]
    n = len(rows)
    bx, by = rc.base_xy(cfg)
    combos = [(c, d) for c in ("near", "far") for d in DIS_DIRS]
    cd = [combos[i % len(combos)] for i in range(n)]
    cnts = _balanced({str(k): v for k, v in dc["counts"].items()}, n, rng)
    best, bsc = None, None
    for _ in range(2000):   # 같은 거리 · 방향 조합이 연달아 안 오게, 개수가 거리 구분 안에서 고르게
        rng.shuffle(cd)
        rng.shuffle(cnts)
        per = collections.defaultdict(list)
        for (c, _d), k in zip(cd, cnts):
            per[c].append(int(k))
        sc = (sum(a == b for a, b in zip(cd, cd[1:])), round(abs(sum(per["near"]) / max(len(per["near"]), 1) - sum(per["far"]) / max(len(per["far"]), 1)), 1),
              sum(a == b == c for a, b, c in zip(cnts, cnts[1:], cnts[2:])))
        if bsc is None or sc < bsc:
            best, bsc = (list(cd), list(cnts)), sc
        if sc == (0, 0.0, 0):
            break
    cd, cnts = best
    used = collections.Counter()
    colors = list(dc["colors"])
    for r, (cls, dr), k in zip(rows, cd, cnts):
        k = int(k)
        cx, cy = (float(v) for v in r["cube_xy_cm"].split(","))
        rad = (cx - bx, cy - by)
        L = math.hypot(*rad) or 1.0
        er = (rad[0] / L, rad[1] / L)                      # 로봇 → 큐브 (상자 쪽 = 로봇 반대)
        el = (-er[1], er[0])                               # 로봇에서 볼 때 왼쪽 (y + 가 로봇 왼쪽)
        base = {"box": er, "robot": (-er[0], -er[1]), "left": el, "right": (-el[0], -el[1])}
        lo, hi = dc["near_cm"] if cls == "near" else dc["far_cm"]
        pts = None
        for dtry in [dr] + [d for d in DIS_DIRS if d != dr]:   # 그 방향이 안 되면 (탁자 끝 등) 다른 방향
            for _t in range(300):
                d0 = rng.uniform(lo, hi)
                th = math.radians(rng.uniform(-float(dc.get("jitter_deg", 25)), float(dc.get("jitter_deg", 25))))
                e = base[dtry]
                v = (e[0] * math.cos(th) - e[1] * math.sin(th), e[0] * math.sin(th) + e[1] * math.cos(th))
                q = dc.get("quantize_cm", 0.5)
                px, py = round((cx + v[0] * d0) / q) * q, round((cy + v[1] * d0) / q) * q
                dd = math.hypot(px - cx, py - cy)
                if lo <= dd <= hi + 0.3 and distractor_ok(cfg, px, py, dc):
                    pts = [(px, py)]
                    break
            if pts:
                dr_used = dtry
                break
        if not pts:
            raise rc.PlanError(f"{r['position']}: 가장 가까운 방해물 자리를 못 찾음 ({cls})")
        d1 = math.hypot(pts[0][0] - cx, pts[0][1] - cy)
        ar = dc["area_cm"]
        for _t in range(20000):
            if len(pts) == k:
                break
            px = round(rng.uniform(*ar["x"]) / 0.5) * 0.5
            py = round(rng.uniform(*ar["y"]) / 0.5) * 0.5
            if math.hypot(px - cx, py - cy) < d1 + float(dc.get("gap_cm", 1.5)) or not distractor_ok(cfg, px, py, dc):
                continue
            if any(math.hypot(px - a, py - b) < float(dc["min_between_cm"]) for a, b in pts):
                continue
            pts.append((px, py))
        if len(pts) < k:
            raise rc.PlanError(f"{r['position']}: 방해물 {k} 개 자리를 못 찾음 ({len(pts)})")
        cols, per = [], collections.Counter()
        for _i in range(k):   # 색: 전체에서 가장 적게 쓴 색부터, 한 판에 max_per_color 까지
            cand = [c for c in colors if per[c] < int(dc.get("max_per_color", 2))]
            m = min(used[c] for c in cand)
            c = rng.choice([c for c in cand if used[c] == m])
            cols.append(c)
            per[c] += 1
            used[c] += 1
        r["distractors"] = ";".join(f"{c}:{x:g},{y:g}" for c, (x, y) in zip(cols, pts))
        r["offset_dir"] = ""
        r["note"] = (r.get("note") + " · " if r.get("note") else "") + \
            f"방해물 {k}개 ({' '.join(DIS_KO.get(c, c) for c in cols)}) · 가장 가까운 것 {DIS_KO.get(cols[0], cols[0])} {d1:.1f} cm {dict(robot='로봇 쪽', box='상자 쪽', left='로봇 왼쪽', right='로봇 오른쪽')[dr_used]} ({cls})"
        r["_dis"] = dict(cls=cls, dir=dr_used, want_dir=dr, n=k, d1=d1)


def assign_pin_entry(cfg, rows, rng):
    """2026-11-12 sg_pin 첫 맞춤 자리 (노란 프레임): 상단 프레임 (sg50.hover.frame) 에서 화면 dir 방향으로 dist 만큼 옮긴 자리 · 같은 크기.
    방향 (sg50.pin.entry.dirs: 0 오른쪽 · 90 아래 = 카메라 쪽 · 180 왼쪽 · 270 위 = 로봇 쪽) 은 전체 · 각도마다 고르게, 같은 방향 3 연속 없음.
    계획 칸 wp_dir · wp_u · wp_v · wp_size 에 씀 (화면은 waypoint_ref 그대로). 화면 밖이면 거리를 줄임."""
    import sg_sticker as sgs

    s = sg(cfg)
    en = (s.get("pin") or {}).get("entry") or {}
    fr = (s.get("hover") or {}).get("frame")
    ref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    if ref is None or not fr:
        raise rc.PlanError("닫기 자리 목표 (kind target) · sg50.hover.frame 이 없어 첫 맞춤 자리를 만들 수 없어요")
    dirs = [str(int(float(d))) for d in en.get("dirs", [0, 90, 180, 270])]
    by_ang = {}
    for i, r in enumerate(rows):
        by_ang.setdefault(r.get("angle") or "0", []).append(i)
    best, bsc = None, None
    for _ in range(3000):
        got = [None] * len(rows)
        off = rng.randrange(len(dirs))
        for a, idx in sorted(by_ang.items()):
            dl = [dirs[(j + off) % len(dirs)] for j in range(len(idx))]   # 각도마다 고르게 (나머지는 돌려 가며)
            off += len(idx)
            rng.shuffle(dl)
            for i, d in zip(idx, dl):
                got[i] = d
        sc = sum(a == b == c for a, b, c in zip(got, got[1:], got[2:]))
        if bsc is None or sc < bsc:
            best, bsc = got, sc
        if sc == 0:
            break
    hu, hv, size = ref["u"] + float(fr["du"]), ref["v"] + float(fr["dv"]), float(fr["size"])
    lo, hi = (float(x) for x in en.get("dist", [0.08, 0.13]))
    mind = float(en.get("min_dist", 0.05))
    fit = {"margin": float(en.get("margin", 0.02))}
    for r, dd in zip(rows, best):
        th = math.radians(float(dd))
        dist = rng.uniform(lo, hi)
        while True:
            u = round(hu + dist * math.cos(th), 3)
            v = round(hv + dist * math.sin(th) * 640.0 / 480.0, 3)
            if waypoint_fit(ref, fit, u, v, size):
                break
            if dist <= mind + 1e-9:
                raise rc.PlanError(f"첫 맞춤 자리가 화면 밖 (방향 {dd}°)")
            dist = max(mind, dist - 0.01)
        r.update(wp_dir=f"{float(dd):.0f}", wp_u=f"{u:.3f}", wp_v=f"{v:.3f}", wp_size=f"{size:.2f}")


def _balanced(mix, n, rng):
    cnt = approach_counts({str(k): v for k, v in mix.items()}, n)
    out = [k for k, c in cnt.items() for _ in range(c)]
    rng.shuffle(out)
    return out


def assign_angles(cfg, rows, mix, rng):
    """큐브 각도 (d2 표기 0 · L30 · R30 · 45) 고르게 · 같은 자리 두 판은 다른 각도 · 같은 각도 3 연속 없음 (2026-11-09).
    need_turn_deg = 0° 큐브 정의 기준 필요한 손목 회전 참고값 (wrap90(각도 − 방향), + 반시계 — 회전량이 적은 쪽)."""
    sgn = ANG_DEG
    keys = [str(k) for k in mix]
    target = approach_counts({k: mix[k] for k in mix}, len(rows))
    best, score = None, None
    for _ in range(4000):  # 차례로: 남은 수가 많은 각도 중 그 자리에 아직 없는 것 (같으면 무작위) → 자리 중복 0 · 3 연속 최소
        left = dict(target)
        used = {}
        ang = []
        for r in rows:
            u = used.setdefault(r["position"], set())
            cand = [k for k in keys if left[k] > 0 and k not in u and not (len(ang) >= 2 and ang[-1] == ang[-2] == k)] \
                or [k for k in keys if left[k] > 0 and k not in u] or [k for k in keys if left[k] > 0]
            m = max(left[k] for k in cand)
            k = rng.choice([k for k in cand if left[k] == m] if rng.random() < 0.7 else cand)
            left[k] -= 1
            u.add(k)
            ang.append(k)
        per = {}
        for r, a in zip(rows, ang):
            per.setdefault(r["position"], []).append(a)
        sc = (sum(len(v) - len(set(v)) for v in per.values()), sum(a == b == c for a, b, c in zip(ang, ang[1:], ang[2:])))
        if score is None or sc < score:
            best, score = ang, sc
        if sc == (0, 0):
            break
    for r, a in zip(rows, best):
        r["angle"] = a
        r["need_turn_deg"] = f"{need_turn(cfg, r['position'], sgn[a]):+.1f}"


def start_pan(cfg, pos, off):
    """큐브 방향 (pan_ref) + 오프셋, |팬| ≤ abs_max — 넘으면 반대쪽, 그래도 넘으면 30° 로."""
    sp = sg(cfg)["start_pan"]
    ref = rc.pan_ref(cfg, pos)
    lim = float(sp.get("abs_max", 85))
    for o in (off, -off, math.copysign(30.0, off), -math.copysign(30.0, off)):
        if abs(ref + o) <= lim:
            return ref + o, o
    return max(-lim, min(lim, ref)), 0.0


def assign_start(cfg, rows, fold_mix, rng):
    """판마다 시작 자세 = 팔 접힘 (start_folds, 실제 녹화값) + 팬 (큐브 방향 + 크게 벌린 오프셋). 고르게 섞고 같은 접힘 3 연속 없음."""
    s = sg(cfg)
    offs = [float(o) for o in s["start_pan"]["offsets"]]
    best, score = None, None
    for _ in range(3000):
        folds = _balanced(fold_mix, len(rows), rng)
        oo = _balanced({str(o): 1 for o in offs}, len(rows), rng)
        sc = sum(a == b == c for a, b, c in zip(folds, folds[1:], folds[2:])) + sum(a == b == c for a, b, c in zip(oo, oo[1:], oo[2:]))
        if score is None or sc < score:
            best, score = (folds, oo), sc
        if sc == 0:
            break
    for r, f, o in zip(rows, *best):
        pan, used = start_pan(cfg, r["position"], float(o))
        j = dict(s["start_folds"][f]["joints"])
        j = {"shoulder_pan": round(pan, 1), **j}
        r["start_fold"] = f
        r["pan_offset_deg"] = f"{used:+.0f}"
        r["start_joints"] = ";".join(f"{k}={v:g}" for k, v in j.items())


def row_pose(cfg, row):
    """줄의 시작 자세 → {name, joints, tol, status} (계획 시작 자세면 줄의 start_joints, 아니면 시나리오 자세)."""
    s = sg(cfg)
    if row and row.get("start_joints"):
        j = {k: float(v) for k, v in (x.split("=") for x in row["start_joints"].split(";") if "=" in x)}
        f = s.get("start_folds", {}).get(row.get("start_fold", ""), {})
        return {"name": f"{row.get('start_fold', '')} {f.get('name', '')} · 팬 {j.get('shoulder_pan', 0):+.0f}° (큐브 방향 {row.get('pan_offset_deg', '')}°)",
                "joints": j, "tol": s.get("start_tol", {}), "status": "planned", "source": f.get("source", "")}
    return s["start_poses"].get(pose_of(cfg, row or {}))


def approach_counts(mix, n):
    """비율 {유형: 무게} → 합이 n 인 판 수 (큰 나머지 방식)."""
    tot = float(sum(mix.values()))
    raw = {k: v * n / tot for k, v in mix.items()}
    cnt = {k: int(math.floor(x)) for k, x in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - cnt[k], reverse=True)[: n - sum(cnt.values())]:
        cnt[k] += 1
    return cnt


def assign_approach(rows, mix, defs, rng):
    """판마다 접근 유형 배정 (2026-11-09). 같은 유형 3 번 연달아 안 오게, 같은 영역 (K4 · K4r2) 에 같은 유형이 몰리지 않게 섞음."""
    bad = [k for k in mix if k not in defs]
    if bad:
        raise rc.PlanError(f"approach_mix 의 {bad} 가 sg50.approach 에 없어요")
    cnt = approach_counts(mix, len(rows))
    types = [k for k, c in cnt.items() for _ in range(c)]
    best, score = None, None
    for _ in range(3000):
        rng.shuffle(types)
        run3 = sum(a == b == c for a, b, c in zip(types, types[1:], types[2:]))
        per = {}
        for r, t in zip(rows, types):
            per.setdefault(r["position"][:2], []).append(t)
        rep = sum(len(v) - len(set(v)) for v in per.values())
        sc = (run3, rep)
        if score is None or sc < score:
            best, score = list(types), sc
        if sc == (0, 0):
            break
    for r, t in zip(rows, best):
        r["approach_type"] = t


def pose_of(cfg, row):
    sc = cfg["scenarios"].get(row.get("scenario_id", ""), {})
    return sc.get("pose", "")


def pose_dev(cfg, pose_id, state):
    """시작 관절값 ↔ 자세 목표: {joint: (실제, 목표, 차, tol 안?)}. state = {'shoulder_pan.pos': ...} 또는 {'shoulder_pan': ...}.
    pose_id = start_poses 키, 또는 row_pose() 가 돌려준 자세 dict (계획 시작 자세)."""
    p = pose_id if isinstance(pose_id, dict) else sg(cfg)["start_poses"].get(pose_id)
    if not p or not state:
        return {}
    st = rc._joint_dict(state) or {}
    out = {}
    for j, t in p["joints"].items():
        if j in st:
            d = st[j] - t
            out[j] = (round(st[j], 1), t, round(d, 1), abs(d) <= p["tol"].get(j, 10))
    return out


def sha_file(p):
    p = os.path.expanduser(p)
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        return "없음"


def calib_versions(cfg):
    """카메라 · 서보 보정 버전 (파일 sha256 앞 16자리). front H = base 설정의 camera.front_640x480 블록."""
    cam = json.dumps(cfg["_base"]["camera"]["front_640x480"], sort_keys=True).encode()
    return {"front_H_sha": hashlib.sha256(cam).hexdigest()[:16], "base_config_sha": sha_file(cfg["base_config"].replace("$HOME", HOME)),
            "follower_calib_sha": sha_file(CALIB["follower"]), "leader_calib_sha": sha_file(CALIB["leader"]),
            "wrist_camera_calib": "없음 (손목 카메라 보정 파일 없음)"}


def sticker_text(cfg):
    st = sg(cfg).get("sticker") or {}
    if not st.get("id"):
        return "미정 (예비 시연 확인 전)"
    return f"{st['id']} · {st.get('face') or '면 미정'} · {st.get('size_mm') or '크기 미정'} mm"


PLAN_SHEET_FIELDS = ["episode_index", "session", "group", "scenario_id", "start_pose_id", "start_pose_name", "start_pose_target",
                     "start_pose_status", "cube_position", "cube_xy_cm", "position_confirmed", "d2_trained_position",
                     "cube_rotation", "cube_rotation_def", "bearing_deg", "pan_ref_deg", "need_wrist_turn_deg", "nearest_eval_cm",
                     "sticker", "split", "approach_type", "approach_name"]


TURN_FIT = (0.86, -5.1)   # 실제 손목 회전량 ≈ 0.86 × need_turn_deg − 5.1 (sg_pin 76 편, |need| < 35, 상관 0.75, 잔차 중앙 7°) — 11-13 연습 3 판에서 계획 값 그대로는 10–17° 어긋남
TURN_SMALL, TURN_AMBIG = 10.0, 35.0   # 2026-11-13 손목 회전 권장 (사용자: "규칙을 명확하게 ui 로") — sg_pin 96 편 전수조사 기준


def turn_advice(need_deg):
    """손목 회전 권장 (need_turn_deg, + = 위에서 볼 때 반시계 = wrist_roll 값이 커지는 쪽).
    |각| < 10 → none (거의 그대로) · 10–35 → ccw / cw (가까운 쪽) · ≥ 35 → either (어느 쪽이든 되는 애매한 각 — 사용자가 그때그때 정함).
    근거 (sg_pin 96 편): 10–35° 에서 돌린 51 편 중 49 편이 가까운 쪽, ≥ 35° 20 편은 + 12 · − 8 로 갈림."""
    try:
        v = float(need_deg)
    except (TypeError, ValueError):
        return None
    a = abs(v)
    if a >= TURN_AMBIG:   # 애매한 각은 계획 값 (기하) 으로 판단, 양은 대략
        return {"kind": "either", "deg": v, "pred": None, "text": f"손목 약 {int(round(a / 5.0) * 5)}° — 어느 쪽이든", "sub": "애매한 각 · 편한 쪽으로"}
    v = TURN_FIT[0] * v + TURN_FIT[1]   # 시연에서 실제로 돌린 양으로 보정
    a = abs(v)
    amt = int(round(a / 5.0) * 5)
    if a < TURN_SMALL:
        return {"kind": "none", "deg": v, "text": "손목 거의 그대로", "sub": "10° 안쪽 미세 조정"}
    if v > 0:
        return {"kind": "ccw", "deg": v, "text": f"손목 반시계 약 {amt}°", "sub": "위에서 볼 때 (L30 쪽)"}
    return {"kind": "cw", "deg": v, "text": f"손목 시계 약 {amt}°", "sub": "위에서 볼 때 (R30 쪽)"}


def need_turn(cfg, pos, yaw=0.0):
    """0° 큐브에 필요한 손목 회전 (check_dataset roll_check 정의: wrap90(yaw − bearing), + = 반시계). 참고값."""
    v = (yaw - bearing(cfg, pos) + 45) % 90 - 45
    return round(v, 1)


def plan_sheet_rows(cfg, session, group, rows, split=None):
    s = sg(cfg)
    split = split or {}
    out = []
    for r in rows:
        q = pose_of(cfg, r)
        p = row_pose(cfg, r) or {}
        posd = pos_info(s, r["position"])
        x, y = rc.known_xy(cfg, r["position"])
        ne = min(math.hypot(x - ex, y - ey) for ex, ey in s["eval_reserved"]["points"].values())
        out.append({"episode_index": r["episode_index"], "session": session, "group": group, "scenario_id": r["scenario_id"],
                    "start_pose_id": q, "start_pose_name": p.get("name", ""),
                    "start_pose_target": ";".join(f"{rc.SHORT[j]}={v:g}" for j, v in p.get("joints", {}).items()),
                    "start_pose_status": p.get("status", ""), "cube_position": r["position"], "cube_xy_cm": r["cube_xy_cm"],
                    "position_confirmed": posd.get("confirmed", False),
                    "d2_trained_position": {"K": "d2 Known (K 마다 32편 학습)", "near_random": f"d2 Random 근처 (최근접 {posd.get('d2_nearest_cm')} cm)"}.get(posd.get("d2_trained"), posd.get("d2_trained", "")),
                    "cube_rotation": r.get("angle") or s["cube_rotation"]["value"], "cube_rotation_def": "로봇 쪽 면 ↔ 로봇 좌우축 (redbox8_layouts angles)",
                    "bearing_deg": round(bearing(cfg, r["position"]), 1), "pan_ref_deg": r.get("pan_target_deg", ""),
                    "need_wrist_turn_deg": float(r["need_turn_deg"]) if r.get("need_turn_deg") else need_turn(cfg, r["position"]), "nearest_eval_cm": round(ne, 1), "sticker": sticker_text(cfg),
                    "split": split.get(str(r["episode_index"]), {}).get("split", s.get("split_default", "train_candidate")),
                    "approach_type": r.get("approach_type") or "",
                    "approach_name": ((s.get("approach") or {}).get(r.get("approach_type") or "", {}) or {}).get("name", "")})
    return out


def write_csv(path, fields, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    os.replace(tmp, path)


def read_split(sess_dir):
    return rc.read_json(os.path.join(sess_dir, SPLIT_JSON), {}) or {}


def write_sheet(sess_dir, cfg):
    meta = rc.read_meta(sess_dir)
    rows = rc.read_plan(sess_dir)
    sh = plan_sheet_rows(cfg, meta["session"], meta["group"], rows, read_split(sess_dir))
    write_csv(os.path.join(sess_dir, SG_PLAN_CSV), PLAN_SHEET_FIELDS, sh)
    s = sg(cfg)
    cv = calib_versions(cfg)
    L = [f"# {meta['session']} — SG50 배치표 ({len(rows)}편)", "",
         f"- 만든 때 {meta['created']} · 설정 `{meta['config_path']}` (sha256 {meta['config_sha256'][:12]}) · 계획 sha256 {meta['plan_sha256'][:12]}",
         f"- 큐브 회전각 **0°** = {s['cube_rotation']['definition']}",
         f"- 큐브 {s['cube_size_cm']} cm · 스티커 {sticker_text(cfg)} · front H {cv['front_H_sha']} · follower 보정 {cv['follower_calib_sha']} · leader 보정 {cv['leader_calib_sha']}",
         "- 손목 필요 회전 = 0° 큐브를 잡을 때 필요한 손목 회전 참고값 (wrap90(0 − 방향), + 반시계). wrist_roll 목표가 아님.",
         "- N 위치 = 계산 좌표 (미확정). front 화면 흰 점선에 놓아 확인한 뒤 설정 confirmed: true.", "",
         "| ep | 시작 자세 | 큐브 | 각도 | 좌표 cm | 확정 | d2 학습 위치 | 방향° | 손목 필요° | 평가 자리까지 cm | split | 접근 |",
         "|---:|---|---|---|---|---|---|---:|---:|---:|---|---|"]
    for r in sh:
        L.append(f"| {r['episode_index']} | {r['start_pose_id']} {r['start_pose_name']} | {r['cube_position']} | {rc.angle_label(r['cube_rotation'])} | {r['cube_xy_cm']} | "
                 f"{'✓' if r['position_confirmed'] else '미확정'} | {r['d2_trained_position']} | {r['bearing_deg']:+.0f} | {r['need_wrist_turn_deg']:+.0f} | "
                 f"{r['nearest_eval_cm']} | {r['split']} | {(r['approach_type'] + ' ' + r['approach_name']) if r['approach_type'] else ''} |")
    cnt_p, cnt_q = {}, {}
    for r in sh:
        cnt_p[r["cube_position"]] = cnt_p.get(r["cube_position"], 0) + 1
        cnt_q[r["start_pose_id"]] = cnt_q.get(r["start_pose_id"], 0) + 1
    L += ["", "## 분포", "", "- 위치별: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt_p.items())),
          "- 시작 자세별: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt_q.items()))]
    cnt_a = {}
    for r in sh:
        if r["approach_type"]:
            cnt_a[r["approach_type"]] = cnt_a.get(r["approach_type"], 0) + 1
    if cnt_a:
        L.append("- 접근 유형별: " + ", ".join(f"{k} {(s.get('approach') or {}).get(k, {}).get('name', '')} {v}" for k, v in sorted(cnt_a.items())))
        L += ["", "## 접근 유형", ""] + [f"- **{k} {d['name']}**: {d.get('text', '')}" for k, d in (s.get("approach") or {}).items()]
    L += ["", "## 시작 자세 후보", ""]
    for k, p in s["start_poses"].items():
        L.append(f"- **{k} {p['name']}** ({p['status']}): " + ", ".join(f"{rc.SHORT[j]} {v:g}±{p['tol'][j]}" for j, v in p["joints"].items())
                 + f" — 출처: {p['source']}")
    with open(os.path.join(sess_dir, "sg_plan.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return sh


EPISODE_OUT = ["episode_id", "episode_index", "session", "dataset_group", "scenario_id", "start_pose_id", "start_pose_target",
               "start_joint_state", "start_pose_max_abs_dev_deg", "start_pose_in_tol", "start_pose_out_joints",
               "cube_position", "cube_xy_planned_cm", "position_confirmed", "d2_trained_position", "front_cube_xy_cm",
               "cube_rotation_planned", "cube_rotation_def", "sticker", "front_H_sha", "base_config_sha", "follower_calib_sha",
               "leader_calib_sha", "calib_source", "first_grasp_success", "final_success", "grasp_outcome", "retry_count",
               "regrasp_or_realign", "operator_notes", "plan_status", "excluded_reason", "split", "sticker_annot",
               "frames", "loop_hz_mean", "camera_stall_ticks", "config_sha256", "code_version", "run_id", "attempt_id",
               "recorded_at", "retake_of"]


def parse_short(txt):
    """'pan=-1.5;lift=-103.3;…' (r12_episodes start_joint_state) → {'shoulder_pan': -1.5, …}. 비어 있으면 None."""
    if not txt:
        return None
    long = {v: k for k, v in rc.SHORT.items()}
    out = {}
    for kv in txt.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            if k in long:
                out[long[k]] = float(v)
    return out or None


def run_sidecar(run_id):
    p = os.path.join(os.path.expanduser(os.environ.get("RECORD_UI_LOG_DIR", "~/.local/state/record_ui")), f"record_{run_id}.json")
    return rc.read_json(p, {}) or {}


def write_episodes(sess_dir, cfg):
    """r12_episodes.csv (r12 sync 가 만든 것) + 계획 + 설정 → sg_episodes.csv. 실패 · 제외 판도 지우지 않고 표시."""
    s = sg(cfg)
    plan = {int(r["episode_index"]): r for r in rc.read_plan(sess_dir)}
    path = os.path.join(sess_dir, rc.EPISODES_CSV)
    eps = []
    if os.path.exists(path):
        with open(path, newline="") as f:
            eps = list(csv.DictReader(f))
    split = read_split(sess_dir)
    ann = (rc.read_json(os.path.join(sess_dir, "sg_sticker", "summary.json"), {}) or {}).get("episodes", {})
    meta = rc.read_meta(sess_dir)
    out = []
    for e in eps:
        i = int(e["episode_index"])
        pr = plan.get(i, {})
        q = pose_of(cfg, pr)
        dev = pose_dev(cfg, row_pose(cfg, pr) or q, parse_short(e.get("start_joint_state", "")))
        side = run_sidecar(e.get("run_id", "")) if e.get("run_id") else {}
        cv = side.get("sg50_calib") or {}
        src = "녹화 시작 때 기록" if cv else "기록 없음 (이 판 녹화 실행 sidecar 에 보정 해시 없음)"
        fg, fs = e.get("first_grasp_success", ""), e.get("final_success", "")
        outcome = {("True", "True"): "first_grasp", ("False", "True"): "success_after_retry", ("False", "False"): "failed"}.get((fg, fs), "미입력" if cfg.get("result_entry", True) else "")
        a = ann.get(str(i))
        out.append({"episode_id": e.get("episode_id", ""), "episode_index": i, "session": meta["session"], "dataset_group": meta["group"],
                    "scenario_id": pr.get("scenario_id", ""), "start_pose_id": q,
                    "start_pose_target": ";".join(f"{rc.SHORT[j]}={v:g}" for j, v in (row_pose(cfg, pr) or {}).get("joints", {}).items()),
                    "start_joint_state": e.get("start_joint_state", ""),
                    "start_pose_max_abs_dev_deg": max((abs(v[2]) for j, v in dev.items() if j != "gripper"), default=""),
                    "start_pose_in_tol": all(v[3] for v in dev.values()) if dev else "",
                    "start_pose_out_joints": ";".join(f"{rc.SHORT[j]}{v[2]:+g}" for j, v in dev.items() if not v[3]),
                    "cube_position": pr.get("position", ""), "cube_xy_planned_cm": pr.get("cube_xy_cm", ""),
                    "position_confirmed": pos_info(s, pr.get("position")).get("confirmed", ""),
                    "d2_trained_position": pos_info(s, pr.get("position")).get("d2_trained", ""),
                    "front_cube_xy_cm": e.get("front_cube_xy_cm", ""), "cube_rotation_planned": pr.get("angle", ""),
                    "cube_rotation_def": "redbox8_layouts angles (로봇 쪽 면 ↔ 로봇 좌우축), wrist_roll 아님", "sticker": sticker_text(cfg),
                    "front_H_sha": cv.get("front_H_sha", ""), "base_config_sha": cv.get("base_config_sha", ""),
                    "follower_calib_sha": cv.get("follower_calib_sha", ""), "leader_calib_sha": cv.get("leader_calib_sha", ""), "calib_source": src,
                    "first_grasp_success": fg, "final_success": fs, "grasp_outcome": outcome, "retry_count": e.get("retry_count", ""),
                    "regrasp_or_realign": "예" if outcome == "success_after_retry" or (e.get("retry_count") not in ("", "0", None)) else ("" if outcome in ("미입력", "") else "아니오"),
                    "operator_notes": e.get("operator_notes", ""), "plan_status": pr.get("status", ""),
                    "excluded_reason": pr.get("note", "") if pr.get("status") == rc.EXCLUDED else "",
                    "split": split.get(str(i), {}).get("split", "excluded" if pr.get("status") == rc.EXCLUDED else s.get("split_default", "train_candidate")),
                    "sticker_annot": (f"{a.get('detected', 0)}/{a.get('frames', 0)} 검출 · 불확실 {a.get('uncertain', 0)}" if a else "미실행"),
                    "frames": e.get("frames", ""), "loop_hz_mean": e.get("loop_hz_mean", ""), "camera_stall_ticks": e.get("camera_stall_ticks", ""),
                    "config_sha256": side.get("config_sha256", ""), "code_version": side.get("code_version", ""),
                    "run_id": e.get("run_id", ""), "attempt_id": e.get("attempt_id", ""), "recorded_at": e.get("recorded_at", ""),
                    "retake_of": e.get("retake_of", "")})
    write_csv(os.path.join(sess_dir, SG_EPISODES_CSV), EPISODE_OUT, out)
    return out


def _arg(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    cfg = rc.load_config(_arg(argv, "--config", os.path.join(rc.ROOT, "config", "sg50.yaml")))
    sess_dir = rc.session_dir(_arg(argv, "--session")) if cmd != "regions" else None
    if cmd == "sheet":
        sh = write_sheet(sess_dir, cfg)
        print(f"{len(sh)}줄 → {os.path.join(sess_dir, SG_PLAN_CSV)} · sg_plan.md")
        return 0
    if cmd == "episodes":
        out = write_episodes(sess_dir, cfg)
        print(f"{len(out)}편 → {os.path.join(sess_dir, SG_EPISODES_CSV)}")
        return 0
    if cmd == "regions" and "--pin" in argv:  # 2026-11-12 sg_pin 영역 점 K#p# (sg50.pin_regions) — K#r# 은 그대로 둠
        import re

        pts = gen_region_points(cfg, over=sg(cfg)["pin_regions"], letter="p")
        for k, (x, y) in pts.items():
            u, v = rc.cm_to_px(rc.front_H(cfg), (x, y))
            print(f"  {k}: ({x:.1f}, {y:.1f}) cm · front ({u:.0f}, {v:.0f}) px")
        for k, n in FALLBACK_USED:
            print(f"  ※ {k}: {n} 점까지 간격 ≥{sg(cfg)['pin_regions']['min_between_cm']} cm, 나머지는 ≥{sg(cfg)['pin_regions']['min_between_fallback_cm']} cm")
        if "--write" in argv:
            path = cfg["_path"]
            txt = open(path).read()
            if re.search(r"^  K\dp\d+:", txt, re.M):
                print("이미 K#p# 점이 설정에 있어요 — 덮어쓰지 않음")
                return 1
            pr = sg(cfg)["pin_regions"]
            lines = [f"  # sg_pin 영역 무작위 점 (sg_plan.py regions --pin, seed {pr['seed']}, {time.strftime('%Y-%m-%d')}): 영역마다 {pr['per_region']} · 서로 ≥{pr['min_between_cm']} cm · 나머지 조건 = known_regions"]
            lines += [f"  {k}: [{x}, {y}]" for k, (x, y) in pts.items()]
            anchor = re.search(r"^free_points:\n((?:  .*\n)*)", txt, re.M)
            txt = txt[: anchor.end()] + "\n".join(lines) + "\n" + txt[anchor.end():]
            open(path + ".tmp", "w").write(txt)
            os.replace(path + ".tmp", path)
            print(f"→ {path} free_points 에 {len(pts)} 점")
        return 0
    if cmd == "regions":  # K 둘레 영역 무작위 점 만들기 (--write 면 설정 free_points 에 덧붙임 — 이미 있으면 거부)
        pts = gen_region_points(cfg)
        for k, (x, y) in pts.items():
            u, v = rc.cm_to_px(rc.front_H(cfg), (x, y))
            print(f"  {k}: ({x:.1f}, {y:.1f}) cm · front ({u:.0f}, {v:.0f}) px")
        if "--write" in argv:
            import re

            path = cfg["_path"]
            txt = open(path).read()
            if re.search(r"^  K\dr\d+:", txt, re.M):
                if "--replace" not in argv:
                    print("이미 K#r# 점이 설정에 있어요 — 덮어쓰지 않음 (녹화 전 계획만 바꿀 때 --replace)")
                    return 1
                txt = re.sub(r"^  # K 둘레 영역 무작위 점 \(sg_plan.py regions.*\n", "", txt, flags=re.M)
                txt = re.sub(r"^  K\dr\d+: .*\n", "", txt, flags=re.M)
            kr = sg(cfg)["known_regions"]
            lines = [f"  # K 둘레 영역 무작위 점 (sg_plan.py regions, seed {kr['seed']}, {time.strftime('%Y-%m-%d')}): 칸 x±{kr['half_x_cm']} · y±{kr['half_y_cm']} cm,"
                     + (f" 밑동 ≤{kr['max_base_dist_cm']} cm," if kr.get("max_base_dist_cm") else "")
                     + f" 어려운 영역 +{kr['hard_zone_margin_cm']} cm 밖 · 평가 자리 ≥{sg(cfg)['eval_reserved']['min_dist_cm']} · K ≥{kr['min_from_k_cm']} · 서로 ≥{kr['min_between_cm']} cm · front y ≥{kr.get('front_min_y_px', 105)} px"]
            lines += [f"  {k}: [{x}, {y}]" for k, (x, y) in pts.items()]
            anchor = re.search(r"^free_points:\n((?:  .*\n)*)", txt, re.M)
            txt = txt[: anchor.end()] + "\n".join(lines) + "\n" + txt[anchor.end():]
            open(path + ".tmp", "w").write(txt)
            os.replace(path + ".tmp", path)
            print(f"→ {path} free_points 에 {len(pts)} 점")
        return 0
    if cmd == "split":
        eps = [int(x) for x in _arg(argv, "--episodes").split(",")]
        to = _arg(argv, "--to")
        if to not in ("train_candidate", "eval_holdout", "excluded"):
            print("--to 는 train_candidate | eval_holdout | excluded")
            return 1
        d = read_split(sess_dir)
        for e in eps:
            d[str(e)] = {"split": to, "reason": _arg(argv, "--reason", ""), "at": datetime.datetime.now().isoformat(timespec="seconds")}
        rc.write_json(os.path.join(sess_dir, SPLIT_JSON), d)
        write_sheet(sess_dir, cfg)
        print(f"split → {to}: {eps}")
        return 0
    print(f"모르는 명령: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
