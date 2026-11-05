"""_out/*/result.json → _out/FACTS.md (측정값 표, 손으로 옮기지 않음)."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "_out")
DESC = {
    "S1_normal": "공식 · 정상: 정책 → Space → (리더 이동) → Tab → 손 교정 3.3 s → Tab 저장 → Space 재개 → 정지 → 교정 1 s → ESC",
    "S2_key_race": "공식 · AUTONOMOUS 에서 Tab, 정지 직후 리더 이동 중 Space 한 번 더",
    "S3_esc_in_correction": "공식 · 교정 도중 ESC",
    "S4_leader_fault": "공식 · 교정 도중 리더 읽기 오류 주입",
    "S5_rtc_fault": "공식 · 정책 실행 중 추론 오류 주입 (계속 실패)",
    "S9_follower_write_fault": "공식 · 교정 도중 follower 쓰기 오류 주입",
    "S6a_enable_stale": "공식 · 리더 Goal 레지스터 '유지' 모델 (S1 과 같은 조작)",
    "S6b_enable_present": "공식 · 리더 Goal 레지스터 '토크 켤 때 현재값' 모델",
    "S7_adapter_normal": "adapter 기본 (팔 필터 OFF · guard warn 기록 · debounce · goal sync · clamp 8 · 종료 hold) · S1 + 표시 키 + 리더 이동 중 Space",
    "S8_adapter_esc_in_correction": "adapter · 교정 도중 ESC",
    "S11_adapter_fast_correction": "adapter · 교정 중 손 20 °/틱 (clamp 8°) → 저장 action vs 보낸 명령",
    "S12_adapter_rtc_fault": "adapter A10 · 정책 실행 중 추론 오류 주입 → 차단 · 큐 무효화 · 강제 정지 → Space 재개 시도 → 교정 → Esc",
    "S13_adapter_leader_fault": "adapter · 교정 도중 리더 읽기 오류 주입",
    "S14_adapter_follower_fault": "adapter · 교정 도중 follower 쓰기 오류 주입",
    "S15_adapter_normal_end_home": "adapter A11 · 정상 교정 → Esc → 사용자 선택 home (HIL_TEST_END_CHOICE)",
    "S16_adapter_pty_keys": "adapter · pty(가짜 터미널) 에 실제 키 바이트 (Space·Tab·1·m·g·b·Esc) → 종료 메뉴에 'release' 입력",
    "S17_adapter_viewer_killed": "adapter + 화면 · S7 조작 중 9 s 에 화면 프로세스 강제 종료 (SIGKILL)",
    "S18_adapter_tap_fault": "adapter + 화면 · tap 20 번째 기록부터 오류 주입 → tap 만 멈춤",
    "S10_adapter_start_paused_reset": "adapter A9 · PAUSED 로 시작 (리더 15°·10° 어긋난 채 연결) → 원위치 교정(r) → 정책 → 교정(R1) → 원위치(r) → ESC",
}
L = ["# 가짜 장치 e2e 측정값 (make_facts.py 자동 생성)", "",
     "각 시나리오 = 설치된 lerobot 0.6.2 `lerobot_rollout.main()` 를 `--strategy.type=dagger --inference.type=rtc` 로 실행, 가짜 follower/leader, stub 정책 (지연 0.3 s, chunk 50).", ""]
L += ["## 1. 불변식 검사", "", "| 시나리오 | 내용 | 통과 | 실패 항목 |", "|---|---|---|---|"]
R = {}
for s in DESC:
    p = root / s / "result.json"
    if not p.exists():
        continue
    r = json.loads(p.read_text()); R[s] = r
    fails = [k for k, c in r["checks"].items() if not c["pass"]]
    L.append(f"| {s} | {DESC[s]} | {len(r['checks']) - len(fails)}/{len(r['checks'])} | {', '.join(fails) or '-'} |")
L += ["", "검사 정의: C1 follower 쓰기 스레드가 모두 MainThread · C2 정책 명령은 AUTONOMOUS 에서만 · C3 사람 명령은 CORRECTING 에서만 + 그때 리더 토크 꺼짐 · "
      "C3b 출처 미분류 쓰기 없음 · C4 정책 구간 리더 토크 꺼짐 · C5 재개 뒤 정책 명령은 재개 reset 뒤 시작한 chunk 에서만 (공식 시나리오) · "
      "C6 정지~재개 사이 정책 명령 0 · A1 dagger 의 send_next_action = 필터 버전 · A1b 정책 쓰기 수 = filter_log cmd 행 수 · "
      "A7 교정 끝 리더 토크 켤 때 Goal−Present < 0.5° · A8 clamp 8 (교정·정책·복귀) · A9 Space 전 정책 명령 0 · A10a 오류 뒤 정책 명령 (첫 오류 뒤 ≤1, 처리 뒤 0) · "
      "A10b 큐 0 + epoch+1 · A10c 오류 뒤 재개 없음 · A11 자동 복귀 없음 / home 은 선택 뒤에만 / hold 는 토크 유지 · A12 팔 필터 OFF (out = raw) · "
      "A13 저장 action = 리더 읽기 (clamp 전) · A13b 보낸 명령은 직전 present 에서 8° 안", ""]
L += ["## 2. 측정값", "", "| 시나리오 | 쓰기 수 (출처별) | 정지 시 RTC 큐 길이 | 정지 시 진행 중 추론 | 쓰기 공백 >0.2 s (시각, 길이 s) | 교정 끝 리더 Goal−Present (°, 0 아닌 관절) | 종료 시 복귀 쓰기 | 데이터셋 (판 · 판별 frame · intervention 모두 True · d2 대비 추가 열) | 예외 |", "|---|---|---|---|---|---|---|---|---|"]
for s, r in R.items():
    m = r["measures"]; d = m["dataset"]
    snaps = [{k: v for k, v in x.items() if abs(v) > 0.05} for x in m["leader_goal_minus_present_at_torque_on_after_correction"]]
    ds = "-" if d is None else f"{d['episodes']} · {d['frames_per_ep']} · {d['intervention_all_true']} · {d['vs_d2']['extra']}"
    L.append(f"| {s} | {m['n_writes_by_origin']} | {m['rtc_qsize_at_pause']} | {m['inflight_chunks_at_pause']} | {m['follower_write_gaps_over_0.2s']} | {snaps} | {m['home_writes']} | {ds} | {m['main_exception'] or '-'} |")
L += ["", "## 3. 시나리오별 추가 측정", ""]
for s, r in R.items():
    m = r["measures"]
    extra = []
    for o in r["ops"]:
        if o["kind"] in ("phase_after_tab_in_auto", "phase_after_double_space"):
            extra.append(f"{o['kind']} = {o['phase']}")
    if m.get("inject"):
        extra.append(f"inject {m['inject']}")
    if m.get("hil_transitions"):
        extra.append("전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = " + str(m["hil_transitions"]))
    if m.get("hil_marks"):
        extra.append(f"표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = {m['hil_marks']}")
    if "hil_key_dropped" in m:
        extra.append(f"버린 키 = {m['hil_key_dropped']}")
    if m.get("hil_session_end"):
        extra.append(f"세션 끝 = {m['hil_session_end']}")
    if m.get("hil_snapshots"):
        extra.append(f"정지 직전 기록 = {m['hil_snapshots']}")
    for k in ("first_inference_error_t", "policy_writes_after_first_error", "policy_write_span_after_first_error_s", "latch_after_first_error_s",
              "policy_writes_after_latch", "fault_handled_after_latch_s", "policy_writes_after_handled", "fault_handled", "fault_hold_writes",
              "follower_arm_motion_after_error_1s_deg", "correction_frames_vs_teleop_writes", "action_minus_leader_read_max",
              "action_minus_sent_goal_max", "frames_action_ne_sent_goal(>0.5deg)", "sent_goal_minus_prev_present_max"):
        if m.get(k) is not None:
            extra.append(f"{k} = {m[k]}")
    if m.get("end_choice"):
        extra.append(f"종료 선택 = {m['end_choice'].get('choice')} ({m['end_choice'].get('source')}) · follower disconnect torque_off {[d['torque_off'] for d in m['follower_disconnect']]}")
    if m.get("max_relative_target_by_origin"):
        extra.append(f"출처별 max_relative_target = {m['max_relative_target_by_origin']}")
    if m.get("filter_log_cmd_rows") is not None:
        extra.append(f"filter_log cmd 행 {m['filter_log_cmd_rows']}, |out−raw| 최대 {m['filter_log_raw_vs_out_max_abs_diff']:.3f}")
    extra.append(f"리더 토크 on 단계 {m['leader_torque_on_phases']} · off 단계 {m['leader_torque_off_phases']} · 리더 disconnect {[(x['phase'], x['torque_off']) for x in m['leader_disconnect']]}")
    if m.get("home_move_deg"):
        extra.append(f"종료 복귀 이동량 (°) {m['home_move_deg']}")
    L.append(f"- **{s}**")
    L += [f"  - {e}" for e in extra]
(root / "FACTS.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
