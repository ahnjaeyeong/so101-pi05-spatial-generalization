# 가짜 장치 e2e 측정값 (make_facts.py 자동 생성)

각 시나리오 = 설치된 lerobot 0.6.2 `lerobot_rollout.main()` 를 `--strategy.type=dagger --inference.type=rtc` 로 실행, 가짜 follower/leader, stub 정책 (지연 0.3 s, chunk 50).

## 1. 불변식 검사

| 시나리오 | 내용 | 통과 | 실패 항목 |
|---|---|---|---|
| S1_normal | 공식 · 정상: 정책 → Space → (리더 이동) → Tab → 손 교정 3.3 s → Tab 저장 → Space 재개 → 정지 → 교정 1 s → ESC | 7/7 | - |
| S2_key_race | 공식 · AUTONOMOUS 에서 Tab, 정지 직후 리더 이동 중 Space 한 번 더 | 7/7 | - |
| S3_esc_in_correction | 공식 · 교정 도중 ESC | 7/7 | - |
| S4_leader_fault | 공식 · 교정 도중 리더 읽기 오류 주입 | 7/7 | - |
| S5_rtc_fault | 공식 · 정책 실행 중 추론 오류 주입 (계속 실패) | 7/7 | - |
| S9_follower_write_fault | 공식 · 교정 도중 follower 쓰기 오류 주입 | 7/7 | - |
| S6a_enable_stale | 공식 · 리더 Goal 레지스터 '유지' 모델 (S1 과 같은 조작) | 7/7 | - |
| S6b_enable_present | 공식 · 리더 Goal 레지스터 '토크 켤 때 현재값' 모델 | 7/7 | - |
| S7_adapter_normal | adapter 기본 (팔 필터 OFF · guard warn 기록 · debounce · goal sync · clamp 8 · 종료 hold) · S1 + 표시 키 + 리더 이동 중 Space | 13/13 | - |
| S8_adapter_esc_in_correction | adapter · 교정 도중 ESC | 13/13 | - |
| S11_adapter_fast_correction | adapter · 교정 중 손 20 °/틱 (clamp 8°) → 저장 action vs 보낸 명령 | 15/15 | - |
| S12_adapter_rtc_fault | adapter A10 · 정책 실행 중 추론 오류 주입 → 차단 · 큐 무효화 · 강제 정지 → Space 재개 시도 → 교정 → Esc | 16/16 | - |
| S13_adapter_leader_fault | adapter · 교정 도중 리더 읽기 오류 주입 | 13/13 | - |
| S14_adapter_follower_fault | adapter · 교정 도중 follower 쓰기 오류 주입 | 13/13 | - |
| S15_adapter_normal_end_home | adapter A11 · 정상 교정 → Esc → 사용자 선택 home (HIL_TEST_END_CHOICE) | 12/12 | - |
| S16_adapter_pty_keys | adapter · pty(가짜 터미널) 에 실제 키 바이트 (Space·Tab·1·m·g·b·Esc) → 종료 메뉴에 'release' 입력 | 13/13 | - |
| S17_adapter_viewer_killed | adapter + 화면 · S7 조작 중 9 s 에 화면 프로세스 강제 종료 (SIGKILL) | 13/13 | - |
| S18_adapter_tap_fault | adapter + 화면 · tap 20 번째 기록부터 오류 주입 → tap 만 멈춤 | 13/13 | - |
| S10_adapter_start_paused_reset | adapter A9 · PAUSED 로 시작 (리더 15°·10° 어긋난 채 연결) → 원위치 교정(r) → 정책 → 교정(R1) → 원위치(r) → ESC | 15/15 | - |

검사 정의: C1 follower 쓰기 스레드가 모두 MainThread · C2 정책 명령은 AUTONOMOUS 에서만 · C3 사람 명령은 CORRECTING 에서만 + 그때 리더 토크 꺼짐 · C3b 출처 미분류 쓰기 없음 · C4 정책 구간 리더 토크 꺼짐 · C5 재개 뒤 정책 명령은 재개 reset 뒤 시작한 chunk 에서만 (공식 시나리오) · C6 정지~재개 사이 정책 명령 0 · A1 dagger 의 send_next_action = 필터 버전 · A1b 정책 쓰기 수 = filter_log cmd 행 수 · A7 교정 끝 리더 토크 켤 때 Goal−Present < 0.5° · A8 clamp 8 (교정·정책·복귀) · A9 Space 전 정책 명령 0 · A10a 오류 뒤 정책 명령 (첫 오류 뒤 ≤1, 처리 뒤 0) · A10b 큐 0 + epoch+1 · A10c 오류 뒤 재개 없음 · A11 자동 복귀 없음 / home 은 선택 뒤에만 / hold 는 토크 유지 · A12 팔 필터 OFF (out = raw) · A13 저장 action = 리더 읽기 (clamp 전) · A13b 보낸 명령은 직전 present 에서 8° 안

## 2. 측정값

| 시나리오 | 쓰기 수 (출처별) | 정지 시 RTC 큐 길이 | 정지 시 진행 중 추론 | 쓰기 공백 >0.2 s (시각, 길이 s) | 교정 끝 리더 Goal−Present (°, 0 아닌 관절) | 종료 시 복귀 쓰기 | 데이터셋 (판 · 판별 frame · intervention 모두 True · d2 대비 추가 열) | 예외 |
|---|---|---|---|---|---|---|---|---|
| S1_normal | {'policy': 144, 'hold': 77, 'teleop': 130, 'home': 150} | [31, 25, 45] | [0, 1, 0] | [[7.07, 2.08], [12.79, 0.4], [14.33, 0.37], [16.84, 2.08], [20.3, 0.31]] | [{'shoulder_pan': 25.02, 'shoulder_lift': -6.0, 'gripper': -4.0}, {}, {'shoulder_pan': -10.01}] | 150 | 2 · [99, 31] · True · ['intervention'] | - |
| S2_key_race | {'policy': 130, 'hold': 1, 'home': 150} | [37, 33] | [0, 0] | [[7.03, 2.1], [9.13, 0.31]] | [] | 150 | - | - |
| S3_esc_in_correction | {'policy': 65, 'hold': 12, 'teleop': 30, 'home': 150} | [25, 45] | [1, 0] | [[6.7, 2.09], [10.12, 0.35]] | [] | 150 | 1 · [30] · True · ['intervention'] | - |
| S4_leader_fault | {'policy': 65, 'hold': 12, 'teleop': 21, 'home': 150} | [25, 45] | [1, 0] | [[6.79, 2.08], [9.91, 0.32]] | [] | 150 | 1 · [21] · True · ['intervention'] | ['ConnectionError: fake leader: injected read failure'] |
| S5_rtc_fault | {'policy': 110, 'home': 150} | [0] | [0] | [[8.45, 3.51]] | [] | 150 | - | - |
| S9_follower_write_fault | {'policy': 65, 'hold': 12, 'teleop': 21} | [25, 45] | [1, 0] | [[6.74, 2.09]] | [] | 0 | 1 · [21] · True · ['intervention'] | ['ConnectionError: fake follower: injected write failure'] |
| S6a_enable_stale | {'policy': 144, 'hold': 77, 'teleop': 130, 'home': 150} | [31, 25, 45] | [0, 1, 0] | [[7.06, 2.07], [12.77, 0.4], [14.31, 0.37], [16.82, 2.07], [20.26, 0.31]] | [{'shoulder_pan': 25.02, 'shoulder_lift': -6.0, 'gripper': -4.0}, {}, {'shoulder_pan': -10.01}] | 150 | 2 · [99, 31] · True · ['intervention'] | - |
| S6b_enable_present | {'policy': 144, 'hold': 78, 'teleop': 130, 'home': 150} | [31, 25, 45] | [0, 1, 0] | [[7.04, 2.07], [12.79, 0.4], [14.33, 0.37], [16.84, 2.07], [20.28, 0.3]] | [{}, {}, {}] | 150 | 2 · [99, 31] · True · ['intervention'] | - |
| S7_adapter_normal | {'policy': 101, 'hold': 91, 'teleop': 131} | [30, 29, 49] | [1, 1, 0] | [[7.21, 2.08], [12.97, 0.42], [14.49, 0.37], [15.53, 2.08], [19.48, 0.32]] | [{}, {}, {}] | 0 | 2 · [100, 31] · True · ['intervention'] | - |
| S8_adapter_esc_in_correction | {'policy': 64, 'hold': 12, 'teleop': 30} | [26, 46] | [1, 0] | [[6.84, 2.08]] | [] | 0 | 1 · [30] · True · ['intervention'] | - |
| S11_adapter_fast_correction | {'policy': 65, 'hold': 18, 'teleop': 48} | [25, 45] | [1, 0] | [[6.93, 2.09], [10.96, 0.38]] | [{}] | 0 | 1 · [48] · True · ['intervention'] | - |
| S12_adapter_rtc_fault | {'policy': 80, 'fault_hold': 1, 'hold': 42, 'teleop': 51} | [30, 0, 0] | [0, 0, 0] | [[7.53, 2.09], [12.47, 0.38]] | [{}] | 0 | 1 · [51] · True · ['intervention'] | - |
| S13_adapter_leader_fault | {'policy': 64, 'hold': 12, 'teleop': 21} | [26, 46] | [1, 0] | [[6.93, 2.09]] | [] | 0 | 1 · [21] · True · ['intervention'] | ['ConnectionError: fake leader: injected read failure'] |
| S14_adapter_follower_fault | {'policy': 65, 'hold': 12, 'teleop': 21} | [25, 45] | [1, 0] | [[6.71, 2.08]] | [] | 0 | 1 · [21] · True · ['intervention'] | ['ConnectionError: fake follower: injected write failure'] |
| S15_adapter_normal_end_home | {'policy': 64, 'hold': 19, 'teleop': 34, 'home': 150} | [26, 46] | [1, 0] | [[6.88, 2.11], [10.44, 0.33]] | [{}] | 150 | 1 · [34] · True · ['intervention'] | - |
| S16_adapter_pty_keys | {'policy': 65, 'hold': 44, 'teleop': 69} | [25, 45] | [1, 0] | [[9.64, 2.08], [14.83, 0.38]] | [{}] | 0 | 1 · [69] · True · ['intervention'] | - |
| S17_adapter_viewer_killed | {'policy': 101, 'hold': 91, 'teleop': 130} | [30, 29, 49] | [1, 1, 0] | [[7.15, 2.08], [12.88, 0.42], [14.4, 0.37], [15.44, 2.08], [19.39, 0.32]] | [{}, {}, {}] | 0 | 2 · [99, 31] · True · ['intervention'] | - |
| S18_adapter_tap_fault | {'policy': 98, 'hold': 90, 'teleop': 129} | [32, 30, 50] | [0, 1, 0] | [[7.33, 2.12], [13.09, 0.43], [14.62, 0.37], [15.62, 2.08], [19.57, 0.32]] | [{}, {}, {}] | 0 | 2 · [98, 31] · True · ['intervention'] | - |
| S10_adapter_start_paused_reset | {'teleop': 116, 'hold': 50, 'policy': 64} | [26, 46] | [1, 0] | [[8.95, 0.31], [9.97, 0.37], [12.44, 2.08], [16.9, 0.36], [18.43, 0.31]] | [{}, {}, {}, {}] | 0 | 3 · [25, 61, 30] · True · ['intervention'] | - |

## 3. 시나리오별 추가 측정

- **S1_normal**
  - correction_frames_vs_teleop_writes = [130, 130]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -23.28, 'shoulder_lift': -6.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.07, 'gripper': -4.0}
- **S2_key_race**
  - phase_after_tab_in_auto = autonomous
  - phase_after_double_space = autonomous
  - 리더 토크 on 단계 ['paused'] · off 단계 ['autonomous'] · 리더 disconnect [('autonomous', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -33.7, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.07, 'gripper': 0.0}
- **S3_esc_in_correction**
  - correction_frames_vs_teleop_writes = [30, 30]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.32
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -2.52, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.03, 'gripper': 0.0}
- **S4_leader_fault**
  - inject {'what': 'leader_read_fail', 'policy_writes_after_inject': 0, 'last_policy_write_after_inject_s': None, 'teleop_writes_after_inject': 0, 'home_writes_after_inject': 150}
  - correction_frames_vs_teleop_writes = [21, 21]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.54
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -2.53, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.03, 'gripper': 0.0}
- **S5_rtc_fault**
  - inject {'what': 'policy_fail', 'policy_writes_after_inject': 47, 'last_policy_write_after_inject_s': 1.6, 'teleop_writes_after_inject': 0, 'home_writes_after_inject': 150}
  - first_inference_error_t = 7.436
  - policy_writes_after_first_error = 30
  - policy_write_span_after_first_error_s = 1.013
  - follower_arm_motion_after_error_1s_deg = 8.54
  - 리더 토크 on 단계 [] · off 단계 [] · 리더 disconnect [('autonomous', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -30.21, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.04, 'gripper': 0.0}
- **S9_follower_write_fault**
  - inject {'what': 'follower_write_fail', 'policy_writes_after_inject': 0, 'last_policy_write_after_inject_s': None, 'teleop_writes_after_inject': 0, 'home_writes_after_inject': 0}
  - correction_frames_vs_teleop_writes = [21, 21]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.32
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', True)]
- **S6a_enable_stale**
  - correction_frames_vs_teleop_writes = [130, 130]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -23.28, 'shoulder_lift': -6.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.07, 'gripper': -4.0}
- **S6b_enable_present**
  - correction_frames_vs_teleop_writes = [130, 130]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': -23.27, 'shoulder_lift': -6.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.07, 'gripper': -4.0}
- **S7_adapter_normal**
  - phase_after_double_space = paused
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.04, 0, 0, 30, True], ['paused', 'correcting', 0.0, 0, 0, 50, False], ['correcting', 'paused', 0.0, 100, 0, 50, False], ['paused', 'autonomous', 0.001, 0, 1, 50, False], ['autonomous', 'paused', 2.04, 0, 1, 29, True], ['paused', 'correcting', 0.0, 0, 1, 49, False], ['correcting', 'paused', 0.0, 31, 1, 49, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R2', 'correcting', 1, 0], ['recovery_done', 'correcting', 58, 0], ['first_grasp_ok', 'correcting', 100, 0]]
  - 버린 키 = [['pause_resume', 'paused', True, 1.344, None]]
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 2, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 30, 'span_s': 2.91, 'front': [30, 12, 16, 3]}, {'file': 'pause_002.npz', 'n': 10, 'span_s': 0.9, 'front': [10, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [131, 131]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 4.3
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 101, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', False)]
- **S8_adapter_esc_in_correction**
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.043, 0, 0, 26, True], ['paused', 'correcting', 0.0, 0, 0, 46, False]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'correcting', 'ended_during_correction': True, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 24, 'span_s': 2.31, 'front': [24, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [30, 30]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.32
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 64, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', False)]
- **S11_adapter_fast_correction**
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.055, 0, 0, 25, True], ['paused', 'correcting', 0.0, 0, 0, 45, False], ['correcting', 'paused', 0.0, 48, 0, 45, False]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 25, 'span_s': 2.42, 'front': [25, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [48, 48]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 29.61
  - frames_action_ne_sent_goal(>0.5deg) = 28
  - sent_goal_minus_prev_present_max = 8.0
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 65, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused'] · off 단계 ['correcting'] · 리더 disconnect [('paused', False)]
- **S12_adapter_rtc_fault**
  - inject {'what': 'policy_fail', 'policy_writes_after_inject': 15, 'last_policy_write_after_inject_s': 0.5, 'teleop_writes_after_inject': 51, 'home_writes_after_inject': 0}
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.047, 0, 0, 0, True], ['paused', 'correcting', 0.0, 0, 0, 0, False], ['correcting', 'paused', 0.0, 51, 0, 0, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R2', 'correcting', 1, 0], ['recovery_done', 'correcting', 25, 0], ['first_grasp_ok', 'correcting', 42, 0], ['final_success', 'correcting', 51, 0]]
  - 버린 키 = [['pause_resume', 'paused', None, None, 'policy_fault_latched']]
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 30, 'span_s': 2.92, 'front': [30, 12, 16, 3]}]
  - first_inference_error_t = 7.504
  - policy_writes_after_first_error = 0
  - policy_write_span_after_first_error_s = 0.0
  - latch_after_first_error_s = 0.0002
  - policy_writes_after_latch = 0
  - fault_handled_after_latch_s = 0.029
  - policy_writes_after_handled = 0
  - fault_handled = {'rtc_qsize_before': 30, 'rtc_qsize_after': 0, 'epoch_before': 2, 'epoch_after': 3}
  - fault_hold_writes = 1
  - follower_arm_motion_after_error_1s_deg = 0.25
  - correction_frames_vs_teleop_writes = [51, 51]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 4.42
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'fault_hold': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 80, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused'] · off 단계 ['correcting'] · 리더 disconnect [('paused', False)]
- **S13_adapter_leader_fault**
  - inject {'what': 'leader_read_fail', 'policy_writes_after_inject': 0, 'last_policy_write_after_inject_s': None, 'teleop_writes_after_inject': 0, 'home_writes_after_inject': 0}
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.057, 0, 0, 26, True], ['paused', 'correcting', 0.0, 0, 0, 46, False]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'correcting', 'ended_during_correction': True, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 24, 'span_s': 2.33, 'front': [24, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [21, 21]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.32
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 64, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', False)]
- **S14_adapter_follower_fault**
  - inject {'what': 'follower_write_fail', 'policy_writes_after_inject': 0, 'last_policy_write_after_inject_s': None, 'teleop_writes_after_inject': 0, 'home_writes_after_inject': 0}
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.045, 0, 0, 25, True], ['paused', 'correcting', 0.0, 0, 0, 45, False]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'correcting', 'ended_during_correction': True, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 25, 'span_s': 2.43, 'front': [25, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [21, 21]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.32
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 65, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused'] · off 단계 ['correcting'] · 리더 disconnect [('correcting', False)]
- **S15_adapter_normal_end_home**
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.077, 0, 0, 26, True], ['paused', 'correcting', 0.0, 0, 0, 46, False], ['correcting', 'paused', 0.0, 34, 0, 46, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R1', 'correcting', 1, 0], ['recovery_done', 'correcting', 25, 0], ['first_grasp_ok', 'correcting', 34, 0], ['final_success', 'correcting', 34, 0]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 24, 'span_s': 2.32, 'front': [24, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [34, 34]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 종료 선택 = home (env) · follower disconnect torque_off [True]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0], 'home': [8.0]}
  - filter_log cmd 행 64, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused'] · off 단계 ['correcting'] · 리더 disconnect [('paused', True)]
  - 종료 복귀 이동량 (°) {'shoulder_pan': 2.79, 'shoulder_lift': 0.0, 'elbow_flex': 0.0, 'wrist_flex': 0.0, 'wrist_roll': -0.03, 'gripper': 0.0}
- **S16_adapter_pty_keys**
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['paused', 'autonomous', 0.0, 0, 0, 0, False], ['autonomous', 'paused', 2.04, 0, 0, 25, True], ['paused', 'correcting', 0.0, 0, 0, 45, False], ['correcting', 'paused', 0.0, 69, 0, 45, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R1', 'correcting', 9, 0], ['recovery_done', 'correcting', 42, 0], ['first_grasp_ok', 'correcting', 51, 0], ['final_success', 'correcting', 60, 0]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 1, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 25, 'span_s': 2.41, 'front': [25, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [69, 69]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 종료 선택 = release (tty) · follower disconnect torque_off [True]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 65, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['autonomous', 'paused', 'paused'] · off 단계 ['autonomous', 'correcting'] · 리더 disconnect [('paused', True)]
- **S17_adapter_viewer_killed**
  - phase_after_double_space = paused
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.043, 0, 0, 30, True], ['paused', 'correcting', 0.0, 0, 0, 50, False], ['correcting', 'paused', 0.0, 99, 0, 50, False], ['paused', 'autonomous', 0.001, 0, 1, 50, False], ['autonomous', 'paused', 2.042, 0, 1, 29, True], ['paused', 'correcting', 0.0, 0, 1, 49, False], ['correcting', 'paused', 0.0, 31, 1, 49, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R2', 'correcting', 0, 0], ['recovery_done', 'correcting', 57, 0], ['first_grasp_ok', 'correcting', 99, 0]]
  - 버린 키 = [['pause_resume', 'paused', True, 1.349, None]]
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 2, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 30, 'span_s': 2.91, 'front': [30, 12, 16, 3]}, {'file': 'pause_002.npz', 'n': 10, 'span_s': 0.9, 'front': [10, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [130, 130]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.33
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 101, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', False)]
- **S18_adapter_tap_fault**
  - phase_after_double_space = paused
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['autonomous', 'paused', 2.082, 0, 0, 32, True], ['paused', 'correcting', 0.0, 0, 0, 32, False], ['correcting', 'paused', 0.0, 98, 0, 32, False], ['paused', 'autonomous', 0.001, 0, 1, 32, False], ['autonomous', 'paused', 2.041, 0, 1, 30, True], ['paused', 'correcting', 0.0, 0, 1, 50, False], ['correcting', 'paused', 0.0, 31, 1, 50, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['type_R2', 'correcting', 1, 0], ['recovery_done', 'correcting', 56, 0], ['first_grasp_ok', 'correcting', 98, 0]]
  - 버린 키 = [['pause_resume', 'paused', True, 1.31, None]]
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 2, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 29, 'span_s': 2.87, 'front': [29, 12, 16, 3]}, {'file': 'pause_002.npz', 'n': 10, 'span_s': 0.9, 'front': [10, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [129, 129]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 3.83
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'policy': [8.0], 'hold': [8.0], 'teleop': [8.0]}
  - filter_log cmd 행 98, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting'] · 리더 disconnect [('paused', False)]
- **S10_adapter_start_paused_reset**
  - 전환 (old, new, blocking_s, 진행 중 교정 frame 수, 저장된 판 수, RTC 큐, 정지 직전 기록) = [['paused', 'correcting', 0.0, 0, 0, 0, False], ['correcting', 'paused', 0.0, 25, 0, 0, False], ['paused', 'autonomous', 0.001, 0, 1, 0, False], ['autonomous', 'paused', 2.043, 0, 1, 26, True], ['paused', 'correcting', 0.0, 0, 1, 46, False], ['correcting', 'paused', 0.0, 61, 1, 46, False], ['paused', 'correcting', 0.0, 0, 2, 46, False], ['correcting', 'paused', 0.0, 30, 2, 46, False]]
  - 표시 (표시, 단계, 교정 frame 위치, 저장된 판 수) = [['reset_segment', 'correcting', 1, 0], ['type_R1', 'correcting', 1, 1], ['recovery_done', 'correcting', 31, 1], ['first_grasp_ok', 'correcting', 60, 1], ['reset_segment', 'correcting', 1, 2]]
  - 버린 키 = []
  - 세션 끝 = {'phase_at_end': 'paused', 'ended_during_correction': False, 'episodes_saved': 3, 'frames_in_current': 0}
  - 정지 직전 기록 = [{'file': 'pause_001.npz', 'n': 24, 'span_s': 2.31, 'front': [24, 12, 16, 3]}]
  - correction_frames_vs_teleop_writes = [116, 116]
  - action_minus_leader_read_max = 0.0
  - action_minus_sent_goal_max = 0.0
  - frames_action_ne_sent_goal(>0.5deg) = 0
  - sent_goal_minus_prev_present_max = 4.44
  - 종료 선택 = hold (non_tty_default) · follower disconnect torque_off [False]
  - 출처별 max_relative_target = {'teleop': [8.0], 'hold': [8.0], 'policy': [8.0]}
  - filter_log cmd 행 64, |out−raw| 최대 0.000
  - 리더 토크 on 단계 ['autonomous', 'paused', 'paused', 'paused', 'paused'] · off 단계 ['correcting', 'autonomous', 'correcting', 'correcting'] · 리더 disconnect [('paused', False)]
