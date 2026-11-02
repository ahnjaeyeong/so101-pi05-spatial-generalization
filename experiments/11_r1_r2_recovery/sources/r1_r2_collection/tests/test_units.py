#!/home/user/so101-env/bin/python
"""단위 시험 (장치·lerobot 안 씀): 계획 균형 · 재현성 · 시작 자세 검사 · 시도 기록 접기 · 보호 세션.
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_units.py
"""

import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import r12_common as rc  # noqa: E402

OK = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}")
    OK.append(bool(cond))


cfg = rc.load_config()
for grp, n, per_k, per_a in (("r1_pilot", 16, 1, 4), ("r2_pilot", 32, 4, 8)):
    rows = rc.make_plan(cfg, grp)
    st = rc.plan_stats(rows)
    check(f"{grp}: {n}편", len(rows) == n)
    check(f"{grp}: 자리마다 {per_k}", set(st["positions"].values()) == {per_k} if grp == "r2_pilot" else
          sorted(st["positions"].items()) == sorted({**{k: 1 for k in cfg["positions"]}, **{f: 2 for f in cfg["free_points"]}}.items()), str(st["positions"]))
    check(f"{grp}: 각도마다 {per_a}", set(st["angles"].values()) == {per_a}, str(st["angles"]))
    check(f"{grp}: 시나리오 수량 = 설정", all(st["scenarios"][s] == c["count"] for s, c in rc.scenarios_of(cfg, rows[0]["type"])))
    check(f"{grp}: 좌우 같음", st["offset_dir"].get("robot_left") == st["offset_dir"].get("robot_right"), str(st["offset_dir"]))
    check(f"{grp}: 같은 seed → 같은 계획", rc.rows_text(rows) == rc.rows_text(rc.make_plan(cfg, grp)))
    first8 = {r["scenario_id"] for r in rows[:8]}
    check(f"{grp}: 앞 8편에 시나리오 4종 이상 (섞임)", len(first8) >= 4, str(sorted(first8)))

for grp in ("r1_pilot", "r2_pilot"):
    rows = rc.make_plan(cfg, grp)
    t = [float(r["pan_target_deg"]) for r in rows]
    check(f"{grp}: 모든 Pan 목표 |pan| ≤ 92°", max(abs(x) for x in t) <= 92, f"최대 {max(abs(x) for x in t):.1f}")
    ok_sign = all((float(r["pan_offset_deg"]) < 0) == (r["offset_dir"] == "robot_left") for r in rows if float(r["pan_offset_deg"]) != 0)
    check(f"{grp}: 왼쪽 시나리오 = pan 어긋남 음수", ok_sign)
    check(f"{grp}: 목표 = 기준 + 어긋남", all(abs(float(r["pan_target_deg"]) - rc.pan_ref(cfg, r["position"]) - float(r["pan_offset_deg"])) < 0.06 for r in rows))
    check(f"{grp}: Pan 목표에서 시작해도 안전 검사 BLOCK 없음 (접근 자세 + 목표 pan)",
          all(not rc.blocking(rc.safety_check({**dict(shoulder_pan=0), "shoulder_pan.pos": x, "shoulder_lift.pos": 17.5, "elbow_flex.pos": 7.1,
                                                "wrist_flex.pos": 73.4, "wrist_roll.pos": 4.4, "gripper.pos": 28.2}, None, cfg)) for x in t))
r = rc.make_plan(cfg, "r1_pilot")[0]
d, txt, ok = rc.pan_guide(cfg, r, float(r["pan_target_deg"]) + 9)
check("pan 안내: 9° 오른쪽에 있으면 '9.0° 더 왼쪽(−)'", "9.0° 더 왼쪽(−)" in txt and not ok, txt)
d, txt, ok = rc.pan_guide(cfg, r, float(r["pan_target_deg"]) - 5)
check("pan 안내: 5° 안이면 ✓ (대략, pan_tol 6)", ok, txt)

lim = rc.calib_limits(cfg)
check("캘리브레이션 pan 한계 ±110°", abs(lim["shoulder_pan"][0] + 110.2) < 0.5 and abs(lim["shoulder_pan"][1] - 110.2) < 0.5, str(lim["shoulder_pan"]))
safe = {"shoulder_pan.pos": -2.2, "shoulder_lift.pos": 17.5, "elbow_flex.pos": 7.1, "wrist_flex.pos": 73.4, "wrist_roll.pos": 4.4, "gripper.pos": 28.2}
check("접근 자세 = BLOCK 없음", not rc.blocking(rc.safety_check(safe, safe, cfg)))
c = rc.safety_check({**safe, "shoulder_pan.pos": -109.0}, None, cfg)
check("pan −109° = BLOCK (3차 지시서: Pan 한계 근처 시작 금지)", {"pan_abs"} <= {x[1] for x in rc.blocking(c)})
c = rc.safety_check({**safe, "shoulder_pan.pos": 96.0}, None, cfg)
check("pan +96° = BLOCK", rc.blocking(c) != [])
c = rc.safety_check({**safe, "shoulder_pan.pos": 90.0}, None, cfg)
check("pan +90° = BLOCK 아님 (계획 최대 92)", not rc.blocking(c))
REST = {"shoulder_pan.pos": -76.7, "shoulder_lift.pos": -102.8, "elbow_flex.pos": 95.5, "wrist_flex.pos": 68.7, "wrist_roll.pos": 1.8, "gripper.pos": 1.1}
c = rc.safety_check(REST, REST, cfg)
check("쉬는 자세 = WARN 만 (11-02 사용자 실행에서 막혔던 값)", not rc.blocking(c) and {"limit_shoulder_lift", "limit_elbow_flex", "gripper_closed"} <= {x[1] for x in c})
c = rc.safety_check({**safe, "gripper.pos": 3}, None, cfg)
check("그리퍼 닫힘 = WARN 만 (11-02)", not rc.blocking(c) and "gripper_closed" in {x[1] for x in c})
c = rc.safety_check(safe, {**safe, "elbow_flex.pos": 7.1 + 30}, cfg)
check("리더−팔로워 30° = BLOCK (4차: 막힘·밀기, 실제 시작 17번 최대 2.9°)", "diff_elbow_flex" in {x[1] for x in rc.blocking(c)})
c = rc.safety_check(safe, {**safe, "elbow_flex.pos": 7.1 + 15}, cfg)
check("리더−팔로워 15° = WARN 만", not rc.blocking(c) and "diff_elbow_flex" in {x[1] for x in c})
c = rc.safety_check({**safe, "wrist_flex.pos": 30}, None, cfg)
check("d2 접근 범위 밖 = WARN 만", not rc.blocking(c) and any(x[1] == "env_wrist_flex" for x in c))
check("관절값 없음 = BLOCK", rc.blocking(rc.safety_check(None, None, cfg)) != [])
check("NaN = BLOCK", rc.blocking(rc.safety_check({**safe, "elbow_flex.pos": float("nan")}, None, cfg)) != [])

with tempfile.TemporaryDirectory() as d:
    rc.append_event(d, {"ev": "armed", "attempt_id": "a", "ep": 0, "state": safe, "checks": []})
    rc.append_event(d, {"ev": "rec_end", "attempt_id": "a", "ep": 0, "frames": 90})
    rc.append_event(d, {"ev": "discarded", "attempt_id": "a", "ep": 0})
    rc.append_event(d, {"ev": "armed", "attempt_id": "b", "ep": 0, "state": safe, "checks": []})
    rc.append_event(d, {"ev": "rec_end", "attempt_id": "b", "ep": 0, "frames": 120})
    rc.append_event(d, {"ev": "label", "attempt_id": "b", "first_grasp_success": True, "final_success": True, "retry_count": 0, "operator_notes": "x"})
    rc.append_event(d, {"ev": "saved", "attempt_id": "b", "ep": 0})
    rows = rc.make_plan(cfg, "r2_pilot")
    eps, probs = rc.build_episode_rows(d, cfg, rows, 1)
    check("버린 시도 빼고 저장 시도만 판 메타데이터로", eps[0]["attempt_id"] == "b" and eps[0]["frames"] == 120 and not probs, str(probs))
    eps, probs = rc.build_episode_rows(d, cfg, rows, 2)
    check("저장 기록 없는 판 = 문제로 보고", any("episode 1" in p for p in probs))
    check("R2 판 메타데이터: 첫 닫힘·깊이 범주·episode_id", eps[0]["first_close_result"] == "grasped" and eps[0]["approach_depth_category"]
          and eps[0]["episode_id"].endswith(":0000") and eps[0]["dataset_group"] == "R2" and not eps[0]["start_pose_type"], str(eps[0]))
with tempfile.TemporaryDirectory() as d:
    r1rows = rc.make_plan(cfg, "r1_pilot")
    pr = next(x for x in r1rows if x["scenario_id"] == "R1-A")
    r1rows = [pr] + [x for x in r1rows if x is not pr]
    st = {**REST, "shoulder_pan.pos": float(pr["pan_target_deg"]) + 3.0}
    rc.append_event(d, {"ev": "armed", "attempt_id": "a", "ep": 0, "state": st, "checks": [], "pan_calib": 3.0, "safety_confirmed": True})
    rc.append_event(d, {"ev": "vision", "attempt_id": "a", "ep": 0, "vision": {"wrist": {"detected": False}, "front": {"detected": True, "xy_cm": [0, 0], "dist_planned_cm": 1.0}}})
    rc.append_event(d, {"ev": "label", "attempt_id": "a", "first_grasp_success": False, "final_success": False, "retry_count": 0,
                        "operator_notes": "", "recovery_completed": True})
    rc.append_event(d, {"ev": "recovery", "attempt_id": "a", "ep": 0, "first_pan_move_dir": "toward", "pan_reversal": True, "pan_reversal_t_s": 0.03,
                        "pan_reversal_kind": "away→toward", "cube_reacquired_in_wrist": True, "cube_reacquire_t_s": 1.3})
    rc.append_event(d, {"ev": "override", "ep": 0, "key": "k"})
    rc.append_event(d, {"ev": "saved", "attempt_id": "a", "ep": 0})
    e = rc.build_episode_rows(d, cfg, r1rows, 1)[0][0]
    check("R1 판 메타데이터: 측정 Pan 오차 = 시작 pan − K 기준 − 보정",
          abs(float(e["measured_start_pan_error_deg"]) - float(pr["pan_offset_deg"])) < 0.06, e["measured_start_pan_error_deg"])
    check("R1 판 메타데이터: 복구 측정·자리 출처·재분류 기록",
          e["first_pan_move_dir"] == "toward" and e["pan_reversal"] is True and e["pan_reversal_kind"] == "away→toward"
          and e["cube_reacquired_in_wrist"] is True and e["scenario_override"] == "k" and e["cube_position_source"] == pr["cube_position_source"]
          and e["start_pan_deg"] and e["pan_reference_source"], str({k: e[k] for k in ("first_pan_move_dir", "pan_reversal", "scenario_override")}))
    check("R1 판 메타데이터: 단계·가시성·신뢰도·안전 확인·재정렬",
          e["approach_stage_at_start"] == "early" and e["wrist_cube_visibility"] == "absent" and e["front_cube_visibility"] == "visible"
          and e["pan_error_estimate_confidence"] == "medium" and e["start_safety_confirmed"] == "yes" and e["recovery_completed"] == "yes"
          and e["dataset_group"] == "R1" and not e["first_close_result"], str({k: e[k] for k in ("approach_stage_at_start", "wrist_cube_visibility",
                                                                                                 "front_cube_visibility", "recovery_completed")}))

check("d2 세션 이름 보호", "main_k8/redbox_t1_known" in rc.PROTECTED_SESSIONS and "main_k8/d2" in rc.PROTECTED_SESSIONS)
check("계획 세션은 보호 목록 밖", all(g["session"] not in rc.PROTECTED_SESSIONS for g in cfg["groups"].values()))
# 4차 지시서: R1 = A 초기 방향 4 · B1 접근 중 반전 4 · B2 지나침 4 · B3 손목 놓침 4, 오차 상태는 준비 단계
rows = rc.make_plan(cfg, "r1_pilot")
by = {}
for r in rows:
    by.setdefault(r["scenario_id"], []).append(r)
check("R1 = A·B1·B2·B3 각 4", sorted((k, len(v)) for k, v in by.items()) == [("R1-A", 4), ("R1-B1", 4), ("R1-B2", 4), ("R1-B3", 4)], str({k: len(v) for k, v in by.items()}))
check("R1 시나리오마다 왼쪽 2 · 오른쪽 2", all(sorted(r["pan_error_direction"] for r in v) == ["left", "left", "right", "right"] for v in by.values()))
check("R1 왼쪽 = pan 어긋남 음수", all((float(r["pan_offset_deg"]) < 0) == (r["pan_error_direction"] == "left") for r in rows))
check("R1 접근 단계 기대: A early · B1 mid · B2/B3 mid|late (B 는 팔 일부 폄)",
      {r["scenario_id"]: r["approach_stage_expected"] for r in rows} == {"R1-A": "early", "R1-B1": "mid", "R1-B2": "mid|late", "R1-B3": "mid|late"})
check("R1-B3 = 손목 안 보임, 나머지 상관없음", all((r["wrist_visibility_target"] == "absent") == (r["scenario_id"] == "R1-B3") for r in rows))
check("R1 명목 오차 15–30° (후보)", all(15 <= float(r["nominal_pan_error_deg"]) <= 30 for r in rows))
check("R1 줄어든 오차 없음", not any(r["note"] for r in rows))
check("R1 큐브 자리 = K 8 + 자유 점 8 (F1–F4 각 2)", sorted(r["position"] for r in rows) == sorted(cfg["r1_positions"])
      and sum(r["cube_position_source"] == "free_point" for r in rows) == 8)
check("R1 은 녹화 중 오차 아님 (Space 없음) · r1_setup", all(not rc.describe_row(cfg, r)["error_in_rec"] and rc.describe_row(cfg, r)["r1_setup"] for r in rows))
check("자유 점·검출 자리 Pan 기준 = 기하 (K 는 d2 중앙값)", rc.pan_ref_source(cfg, "F1") == "geometry" and rc.pan_ref_source(cfg, "K1") == "d2_K_median"
      and abs(rc.pan_ref(cfg, "X(-8.5,11.5)") - (-2.7)) < 0.2 and rc.known_xy(cfg, "X(-8.5,11.5)") == (-8.5, 11.5))
check("자리 출처", [rc.position_source(cfg, p)[0] for p in ("K3", "F2", "X(1.0,2.0)")] == ["K_grid", "free_point", "front_detected"])
check("접근 단계: 쉬는 자세 = early, d2 파지 lift = late, 중간 = mid",
      rc.approach_stage(cfg, REST, "K6")[0] == "early" and rc.approach_stage(cfg, {**REST, "shoulder_lift.pos": 16.5}, "K6")[0] == "late"
      and rc.approach_stage(cfg, {**REST, "shoulder_lift.pos": -40.0}, "K6")[0] == "mid", str(rc.approach_stage(cfg, {**REST, "shoulder_lift.pos": -40.0}, "K6")))
d0 = rc.describe_row(cfg, by["R1-B1"][0])
sc = rc.scenario_checks(cfg, d0, REST, {"wrist": {"detected": False}, "front": {"detected": False}})
check("시나리오 조건은 경고 목록 (단계 다름·front 안 보임 = False), 안전 검사와 별개",
      {k for ok_, k, _ in sc if ok_ is False} >= {"stage", "front"} and not rc.blocking(rc.safety_check(REST, REST, cfg)))
# 다음 판 바꾸기 (s/d/k)
r = dict(by["R1-A"][0])
rc.set_scenario(cfg, r, "R1-B3")
rc.refresh_row(cfg, r)
check("s: 시나리오 바꾸기 — 방향 유지, 크기·단계·손목 목표는 새 시나리오", r["scenario_id"] == "R1-B3" and r["approach_stage_expected"] == "mid|late"
      and r["wrist_visibility_target"] == "absent" and r["pan_error_direction"] == by["R1-A"][0]["pan_error_direction"], str({k: r[k] for k in ("pan_offset_deg", "pan_error_direction")}))
r["pan_offset_deg"] = f"{-float(r['pan_offset_deg']):g}"
rc.refresh_row(cfg, r)
check("d: 방향 바꾸기 — 목표 = 기준 + 어긋남", abs(float(r["pan_target_deg"]) - rc.pan_ref(cfg, r["position"]) - float(r["pan_offset_deg"])) < 0.06)
r["position"] = "K7"
r["pan_offset_deg"] = "-30"
rc.refresh_row(cfg, r)
check("k: K7 에서 왼쪽 30° = |pan| 92 로 줄임 + 표시", abs(float(r["pan_target_deg"])) <= 92.01 and r["note"], r["pan_target_deg"])
# 복구 측정
import numpy as np  # noqa: E402

pre = np.linspace(40, 55, 30)
rec = np.concatenate([np.full(10, 55), np.linspace(55, 44, 40), np.full(30, 44)])
m = rc.pan_recovery(rec, 30, 44.6, pre)
check("복구: 준비 때 멀어짐 → 녹화 첫 이동 큐브 쪽 = 반전 (시각 ≈ 0)", m["setup_pan_motion"].startswith("away") and m["first_pan_move_dir"] == "toward"
      and m["pan_reversal"] and abs(m["pan_reversal_t_s"]) < 0.2 and m["pan_reversal_kind"] == "away→toward", str(m))
pre = np.concatenate([np.linspace(40, 58, 20), np.linspace(58, 55, 10)])
m = rc.pan_recovery(np.linspace(55, 44, 40), 30, 44.6, pre)
check("복구: 준비 때 이미 되돌리기 시작 → 반전 시각 음수", m["pan_reversal"] and m["pan_reversal_t_s"] < 0, str(m))
grip = np.concatenate([np.full(40, 1.0), np.full(30, 30.0), np.linspace(30, 12, 20), np.full(40, 12.0)])
pan = np.concatenate([np.linspace(68, 33, 40), np.linspace(33, 43, 30), np.full(20, 43.0), np.linspace(43, 3, 40)])
m = rc.pan_recovery(pan, 30, 44.6, None, grip)
check("복구: 파지 시작(리더 그리퍼 <10 안 닫아도) 뒤 상자 쪽 Pan 은 뺌 · 지나침 뒤 되돌아옴 = toward→toward 반전",
      m["grasp_start_t_s"] and abs(m["pan_error_at_grasp_deg"]) < 3 and m["pan_reversal_kind"] == "toward→toward", str(m))
check("손목 재획득", rc.wrist_reacquire([False, False, True, True], 0.33) == (False, True, 0.7) and rc.wrist_reacquire([True], 0.33)[0] is True
      and rc.wrist_reacquire([False, True, False], 0.33) == (False, False, ""))
b2 = rc.describe_row(cfg, by["R1-B2"][0])
sp = rc.setup_path(cfg, b2)
f_from, f_stop = rc.pan_phi(cfg, b2["position"], sp["from_pan"]), rc.pan_phi(cfg, b2["position"], float(b2["pan_target_deg"]))
f_cube = rc.pan_phi(cfg, b2["position"], rc.pan_ref(cfg, b2["position"]))
check("B2 출발선 = 큐브 반대쪽 (출발·멈출 곳이 큐브 방향을 사이에 둠), 경로 끝 = 멈출 곳",
      (f_from - f_cube) * (f_stop - f_cube) < 0 and abs(sp["path"][-1][0] - rc.start_xy(cfg, b2)[0]) < 0.01, f"{f_from:.1f} {f_cube:.1f} {f_stop:.1f}")
b1 = rc.describe_row(cfg, by["R1-B1"][0])
b3, a1 = rc.describe_row(cfg, by["R1-B3"][0]), rc.describe_row(cfg, by["R1-A"][0])
check("출발선: B1·B3 = 큐브 방향 · A = 쉬는 자세 pan · 네 시나리오 모두 있음",
      abs(rc.setup_path(cfg, b1)["from_pan"] - rc.pan_ref(cfg, b1["position"])) < 0.01 and abs(rc.setup_path(cfg, b3)["from_pan"] - rc.pan_ref(cfg, b3["position"])) < 0.06
      and abs(rc.setup_path(cfg, a1)["from_pan"] - cfg["rest_pan_deg"]) < 0.01)
tr = rc.make_plan(cfg, "r1_try3")
check("r1_try3 (시험 4편): A·B1·B2·B3 각 1 · 좌우 2/2 · 서로 다른 자리 (K 2 · 자유 점 2)",
      sorted(r["scenario_id"] for r in tr) == ["R1-A", "R1-B1", "R1-B2", "R1-B3"] and sorted(r["pan_error_direction"] for r in tr) == ["left", "left", "right", "right"]
      and len({r["position"] for r in tr}) == 4 and sum(r["position"].startswith("F") for r in tr) == 2)
check("R1 계획 |pan 목표| ≤ 92", all(abs(float(r["pan_target_deg"])) <= 92.01 for r in rows))
r2rows = rc.make_plan(cfg, "r2_pilot")
check("R2 = Pan 오차 없음 (pan_offset 0)", all(float(r["pan_offset_deg"]) == 0 for r in r2rows))
check("R2 metadata: local_alignment_type 채움, R1 필드 빈칸", all(r["local_alignment_type"] and not r["pan_error_direction"] and not r["start_pose_type"] for r in r2rows))
check("R2 접근 깊이 범주: 시나리오마다", all(rc.describe_row(cfg, r)["approach_depth_category"] for r in r2rows))
check("R2 시작 영역: 모든 시나리오", all(rc.describe_row(cfg, r)["wrist_start_region"] for r in r2rows))
check("R2 손목 영역 판정", rc.in_region({"detected": True, "dx": 0.0, "dy": -0.1}, {"u": [0.4, 0.6], "v": [0.4, 0.5]}) is True
      and rc.in_region({"detected": True, "dx": 0.9, "dy": 0.9}, {"u": [0.4, 0.6], "v": [0.4, 0.5]}) is False)
prog = rc.program_progress(cfg)
check("48편 진행률 = R1 16 + R2 32", sum(x[3] for x in prog) == 48 and sum(x[3] for x in prog if x[0] == "R1") == 16, str(prog))
check("R2 첫 닫힘 결과 (1/2/3 → grasped/missed_then_retry/failed)",
      [rc.first_close_result(x) for x in ({"first_grasp_success": True, "final_success": True}, {"first_grasp_success": False, "final_success": True},
                                          {"first_grasp_success": False, "final_success": False}, {})] == ["grasped", "missed_then_retry", "failed", ""])
att = rc.fold_attempts([{"ev": "armed", "attempt_id": "a", "ep": 0}, {"ev": "mark", "attempt_id": "a", "frame": 120, "pan": -40.0},
                        {"ev": "saved", "attempt_id": "a"}])
check("Space 표시가 시도에 모임", att["a"]["marks"][0]["frame"] == 120)
print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)}")
sys.exit(0 if all(OK) else 1)
