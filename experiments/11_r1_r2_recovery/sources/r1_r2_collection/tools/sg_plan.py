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


REGION_RE = r"^K(\d)r(\d+)$"  # 2026-11-06 예비3: K 둘레 영역 무작위 점 이름 (K4r2 = K4 영역 2번) — 좌표는 설정 free_points 에 고정


def pos_info(s, p):
    """설정 positions 정보. K#r# (영역 무작위 점) 는 좌표 고정 · 탁자 표시 없음 → confirmed True, d2_trained 'K 영역 무작위'."""
    import re

    if re.match(REGION_RE, str(p or "")):
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


def gen_region_points(cfg):
    """K 마다 둘레 칸 (x ± half_x, y ± half_y) 안 무작위 점 per_region 개 (조건은 sg50.known_regions). 반환 {이름: (x, y)}."""
    s = sg(cfg)
    kr = s["known_regions"]
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
        for _ in range(20000):
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
            if any(math.hypot(x - a, y - b) < kr["min_between_cm"] for a, b in got + list(out.values())):  # 다른 영역 점과도
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
            out[f"{k}r{i}"] = (x, y)
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
        pairs = [(k, one or "S0") for k in sorted(cfg["_base"]["known_positions"])] + [(p, one or "S0") for p in reg]
        area = lambda p: p[:2]  # noqa: E731  K4 · K4r2 → K4
        for _ in range(5000):
            rng.shuffle(pairs)
            if all(area(a[0]) != area(b[0]) for a, b in zip(pairs, pairs[1:])):
                break
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
                     "cube_position_source": rc.position_source(cfg, p)[0]})
    return rows


def pose_of(cfg, row):
    sc = cfg["scenarios"].get(row.get("scenario_id", ""), {})
    return sc.get("pose", "")


def pose_dev(cfg, pose_id, state):
    """시작 관절값 ↔ 자세 목표: {joint: (실제, 목표, 차, tol 안?)}. state = {'shoulder_pan.pos': ...} 또는 {'shoulder_pan': ...}."""
    p = sg(cfg)["start_poses"].get(pose_id)
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
                     "sticker", "split"]


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
        p = s["start_poses"].get(q, {})
        posd = pos_info(s, r["position"])
        x, y = rc.known_xy(cfg, r["position"])
        ne = min(math.hypot(x - ex, y - ey) for ex, ey in s["eval_reserved"]["points"].values())
        out.append({"episode_index": r["episode_index"], "session": session, "group": group, "scenario_id": r["scenario_id"],
                    "start_pose_id": q, "start_pose_name": p.get("name", ""),
                    "start_pose_target": ";".join(f"{rc.SHORT[j]}={v:g}" for j, v in p.get("joints", {}).items()),
                    "start_pose_status": p.get("status", ""), "cube_position": r["position"], "cube_xy_cm": r["cube_xy_cm"],
                    "position_confirmed": posd.get("confirmed", False),
                    "d2_trained_position": {"K": "d2 Known (K 마다 32편 학습)", "near_random": f"d2 Random 근처 (최근접 {posd.get('d2_nearest_cm')} cm)"}.get(posd.get("d2_trained"), posd.get("d2_trained", "")),
                    "cube_rotation": s["cube_rotation"]["value"], "cube_rotation_def": "로봇 쪽 면 ↔ 로봇 좌우축 (redbox8_layouts angles)",
                    "bearing_deg": round(bearing(cfg, r["position"]), 1), "pan_ref_deg": r.get("pan_target_deg", ""),
                    "need_wrist_turn_deg": need_turn(cfg, r["position"]), "nearest_eval_cm": round(ne, 1), "sticker": sticker_text(cfg),
                    "split": split.get(str(r["episode_index"]), {}).get("split", s.get("split_default", "train_candidate"))})
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
         "| ep | 시작 자세 | 큐브 | 좌표 cm | 확정 | d2 학습 위치 | 방향° | 손목 필요° | 평가 자리까지 cm | split |",
         "|---:|---|---|---|---|---|---:|---:|---:|---|"]
    for r in sh:
        L.append(f"| {r['episode_index']} | {r['start_pose_id']} {r['start_pose_name']} | {r['cube_position']} | {r['cube_xy_cm']} | "
                 f"{'✓' if r['position_confirmed'] else '미확정'} | {r['d2_trained_position']} | {r['bearing_deg']:+.0f} | {r['need_wrist_turn_deg']:+.0f} | "
                 f"{r['nearest_eval_cm']} | {r['split']} |")
    cnt_p, cnt_q = {}, {}
    for r in sh:
        cnt_p[r["cube_position"]] = cnt_p.get(r["cube_position"], 0) + 1
        cnt_q[r["start_pose_id"]] = cnt_q.get(r["start_pose_id"], 0) + 1
    L += ["", "## 분포", "", "- 위치별: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt_p.items())),
          "- 시작 자세별: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt_q.items())), "", "## 시작 자세 후보", ""]
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
        dev = pose_dev(cfg, q, parse_short(e.get("start_joint_state", "")))
        side = run_sidecar(e.get("run_id", "")) if e.get("run_id") else {}
        cv = side.get("sg50_calib") or {}
        src = "녹화 시작 때 기록" if cv else "기록 없음 (이 판 녹화 실행 sidecar 에 보정 해시 없음)"
        fg, fs = e.get("first_grasp_success", ""), e.get("final_success", "")
        outcome = {("True", "True"): "first_grasp", ("False", "True"): "success_after_retry", ("False", "False"): "failed"}.get((fg, fs), "미입력" if cfg.get("result_entry", True) else "")
        a = ann.get(str(i))
        out.append({"episode_id": e.get("episode_id", ""), "episode_index": i, "session": meta["session"], "dataset_group": meta["group"],
                    "scenario_id": pr.get("scenario_id", ""), "start_pose_id": q,
                    "start_pose_target": ";".join(f"{rc.SHORT[j]}={v:g}" for j, v in s["start_poses"].get(q, {}).get("joints", {}).items()),
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
