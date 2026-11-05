# 07 · 교정 시연 파일럿 12편 (R1 4 · R2-P 4 · R2-O 4) — 기존 UI 재사용

작업 지시: "SO-101 R1/R2 교정 시연 파일럿 — 기존 UI 재사용" (2026-11-03).
- HIL 이 아니다. 사람이 준비 단계 (녹화 안 함) 에서 안전한 시작 상태를 만들고, 텔레오퍼레이션으로 복구 행동만 녹화한다.
- Claude 는 준비와 검증만 했다. 실물 로봇 연결 · 구동 · 녹화는 하지 않았다.

명령은 `08_pilot12_usage.md` 에 있다.

## 1. 재사용 범위 (새 UI 없음)

| 필요 기능 | 쓰는 것 | 이번에 바꾼 것 |
|---|---|---|
| Front/Wrist 실시간 화면 · 관절 상태 · 리더−팔로워 차이 | `r12_viewer.py` (Tk) + `record_ui.py` 터미널 배너 (d2 녹화와 같은 흐름) | 파일럿 시작 조건 칸 · 녹화 상태 줄 · 명령 보호 표시 |
| 현재 시나리오 (큰 글씨) | 시나리오 `label` → 영상 창 맨 위 | 파일럿 시나리오 3 개 추가 (설정) |
| 녹화 시작 · 중지 · 저장 · 버리기 · 결과 (1/2/3) · 메모 · 종료 | 기존 키 (→ ← 1 2 3 m Esc) · lerobot 0.6.2 `record()` 그대로 | 없음 |
| 준비 단계 (녹화 안 함) · 시작 자세 안전 검사 (BLOCK) | `r12_record_entry.py` | 없음 (완화 없음) |
| 실행 로그 · 영상 저장 · 후처리 · QA | record_ui 후처리 · `r12_qa.py` | 파일럿 QA 절 (§9) |
| 터미널 실행 | `r12_collect.py` | 모든 명령에 `--config config/r12_pilot12.yaml` |

실물 추론 UI (`eval_ui.py` + `r2_place_viewer.py`) 는 정책을 돌리는 화면이라 텔레오퍼레이션 녹화에 쓸 수 없다.
- 그 화면의 주요 요소는 r12 영상 창에 이미 같은 형태로 있다: 계획 위치 윤곽 · 실시간 큐브 검출 · 단계 · 계획 목록.
- 그래서 r12 도구를 그대로 쓴다.

## 2. 파일럿 구성 (`config/r12_pilot12.yaml`)

- 기존 `r12_scenarios.yaml` 을 고치지 않고 `extends` 로 덧씌운다.
  - 기준 커밋과 sha256 이 같음을 시험으로 확인했다.
  - 덧씌운 파일의 sha 는 계획 · 실행 기록에 남는다.
- 기존 `r2_pilot` (40 편 잠정, draft) 과 `r1_pilot` 계획 · 세션은 건드리지 않았다.

| 그룹 | 세션 · repo_id | 시나리오 | 편수 | 시작 상태 (준비 단계, 녹화 안 함) | 녹화하는 행동 |
|---|---|---|---|---|---|
| pilot12_r1 | `main_k8/r12_pilot12_r1` · `oxr/so101_k8_r12_pilot12_r1` | R1-FOLD-OVER | 4 (K1 · K4 왼쪽, K3 · K6 오른쪽 → 복구 방향 좌우 2/2) | 팔 접힘 · 쉬는 자세 pan 에서 큐브 쪽으로 돌려 큐브 방향을 20 · 25° 지나쳐 멈춤 · 그리퍼 닫힘 그대로 · 손목 큐브 가장자리/안 보여도 됨 · front 보임 | Pan 을 되돌려 재정렬 → 팔 펴며 접근 → 파지 → 상자 → 쉬는 자세 |
| pilot12_r2p | `main_k8/r12_pilot12_r2p` · `oxr/so101_k8_r12_pilot12_r2p` | R2-P-AHEAD 2 · R2-P-DEPTH 2 (기존 AHEAD · DEPTH 복사 + 그리퍼 열림 조건) | 4 | 그리퍼 열림 · 파지 높이 근처 팔 정지 · 큐브가 손가락 앞 / 일부 진입 | 연 채 접근 깊이 · 높이 · 정렬 보정 → 한 번 닫기 → 작업 완료 |
| pilot12_r2o | `main_k8/r12_pilot12_r2o` · `oxr/so101_k8_r12_pilot12_r2o` | R2-O-REOPEN | 4 | 그리퍼 닫힘 (쉬는 자세 그대로 접근, 빈 파지 동작 없음) · 큐브 앞 파지 높이 근처 팔 정지 · 큐브에 닿지 않음 | 먼저 충분히 열기 (약 30) → 연 채 추가 접근 · 정렬 → 한 번 닫기 → 작업 완료 |

- R1 의 지나침 크기는 20 · 25° 이다. 계획 |pan| 최대 69.6° 이고, 실패 때의 −109° 는 재현하지 않는다. K7 · K8 은 지나치면 92° 를 넘어 쓰지 않는다.
- 주황 선 · 손목 시작 영역은 안내일 뿐 녹화를 막지 않는다. 막는 것은 안전 조건뿐이다.
- 세 그룹은 세션 · dataset · repo_id 가 각각 따로다. R2-P 와 R2-O 를 나눠 학습할 수 있다.
- 과제 문장 · 카메라 · fps · features 는 d2 와 같다 (가짜 장치 시험에서 info.json 비교).

계획 (`~/so101_runs/main_k8/r12_pilot12_*/r12_plan.csv`, `r12_sheet.md`):

| 그룹 | ep0 | ep1 | ep2 | ep3 |
|---|---|---|---|---|
| R1 | K4 ↻30° 왼쪽 20° (pan −66.2) | K6 45° 오른쪽 25° (69.6) | K1 0° 왼쪽 20° (−53.5) | K3 ↺30° 오른쪽 25° (56.2) |
| R2-P | AHEAD K3 45° | DEPTH K4 ↻30° | AHEAD K8 0° | DEPTH K7 ↺30° |
| R2-O | K5 45° | K8 ↺30° | K6 0° | K7 ↻30° |

## 3. 녹화 전 시작 상태 기록 (§7)

녹화 시작 (→) 순간 `r12_attempts.jsonl` 에 남는 것:
- `armed`: 관절 · 리더 값, 안전 검사, code_version
- `vision`: front · wrist 검출
- `pilot_start`: 아래 값

| R1 | R2 (P · O) |
|---|---|
| Shoulder Pan · Lift (+ Elbow · Wflex) · 접근 단계 | Lift · Elbow · Wflex · 그리퍼 값 · 열림/닫힘 (시나리오 조건과 비교) |
| 손목 큐브 가시성 (보임 / 가장자리 / 안 보임) · front 큐브 가시성 | 손목 큐브 u · v · 시작 영역 안 여부 |
| Pan 기준 대비 오차 · 지나침/덜 감 · **필요한 복구 방향** | 손가락 사이와의 2D 관계 (닫기 영역 위 = 앞쪽 · 안 · 아래 · 좌우) = 접근/정렬 부족 쪽 |
| 실물 실패 상태와 비슷함 (팔 접힘 lift ≤ −85 · 지나침 ≥ 10° · 손목 가장자리/안 보임 · front 보임) | 실물 실패 상태와 비슷함 (R2-O: 그리퍼 < 15 · 손목 v 0.25–0.633 · front 보임) |

- 녹화 첫 프레임 front · wrist 를 PNG 로 저장한다: `<세션>/r12_start_frames/ep###_<attempt>_{front,wrist}.png` (녹화 프로세스의 별도 스레드).
- 기준 Pan (판마다 ±9°) · 손목 v 영역은 검증된 물리 정답이 아니다. 화면 · 기록에는 '근사 · 참고' 로만 표시하고, 녹화를 막지 않는다.

## 4. 판 메타데이터 (§8) — `<세션>/r12_pilot_episodes.csv`

`sync` · 녹화 끝 · `status` 때 다시 만든다. 열:

| 묶음 | 열 |
|---|---|
| 판 · 시나리오 | run_id, episode_index, episode_id, scenario_id, pilot_variant, failure_type, correction_action |
| 시작 관절 | start_joint_state, start_pan · lift · elbow · wflex_deg, start_stage(_progress) |
| 시작 그리퍼 | start_gripper_value · state, gripper_start_expected |
| R1 시작 | start_pan_error_deg, start_pan_side, needed_recovery_dir |
| 시작 손목 · front | start_wrist_u · v · relation · visibility, start_front_visibility, start_in_wrist_region, failure_similarity(_items) |
| 큐브 | cube_position, cube_xy_planned_cm, cube_rotation, front_cube_xy_cm |
| 시작 프레임 | start_frame_front · wrist |
| 데이터 위치 | dataset_root, dataset_repo_id, video_front · wrist (`videos/…/file-###.mp4@시작–끝 s`) |
| 결과 · 유효성 | first_grasp_success, final_success, valid, invalid_reason, operator_notes, guard_events, frames, loop_hz_mean |
| 재현 정보 | code_version (git HEAD), config_sha256, config_extends_sha256, recorded_at, attempt_id |

- 관절 state/action 은 dataset parquet 에 있다 (LeRobot v3.0, d2 와 같은 features).
- 기존 `r12_episodes.csv` 도 그대로 만든다.

## 5. 파일럿 QA (§9) — `r12_collect.py qa --config …` → `qa/r12_qa_report.md` §5 · `qa/r12_pilot_qa.csv`

dataset 을 읽기만 해서 다시 잰다.

| 질문 | 규칙 (설정 `pilot_qa`) |
|---|---|
| Q1 시작 상태가 실패 상태와 비슷 | 녹화 첫 프레임 state + 첫 영상으로 §3 기준 다시 계산, 모두 맞으면 ok · 시작 그리퍼가 조건과 다르면 check |
| Q2 R1 Pan 수정 기록 | 첫 Pan 이동 (≥ 2°) 이 필요한 방향 · 그 방향으로 ≥ 5° · 닫기 시작 때 기준 대비 오차가 처음보다 작음 |
| Q3 R2-P 열린 채 접근 | 첫 닫힘 전 리더 그리퍼 ≥ 15 비율 ≥ 0.95 · 시작 열림 |
| Q4 R2-O 충분히 다시 엶 | 시작 < 15 · 닫기 전 최대 ≥ 25 (reopen_min) · 처음 열기 전 Lift/Elbow 이동 ≤ 5° (= 먼저 엶) |
| Q5 한 번의 닫힘으로 파지 | 닫힘 사건 1 번 (열린 정점에서 max(8, 35 %) 하강 3 프레임) · 첫 파지 입력 성공 |
| Q6 불필요한 동작 | 닫기 전 팔 관절 경로/순 변위 ≤ 2.5 · R1 Pan 방향 바뀜 ≤ 2 |
| Q7 시간 일치 | 무결성 표 (영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속) + 판 timestamp 간격 |
| Q8 d2 와 독립 보존 | dataset 이 d2 · d2 구성 세션 밖 · repo_id 다름 |

- 분류: `exclude` (제외 · 녹화 중 보호 사건) / `review` / `candidate_needs_review`.
- 성공 판도 바로 '학습 적합' 으로 분류하지 않는다. candidate 도 사람 검토가 필요하다.

## 6. 안전 (§10) — 점검 결과

| 항목 | 상태 | 근거 |
|---|---|---|
| 실제 명령 차단형 관절 안전 정지 | **추가** (파일럿 설정에서만 켬): `TeleopGuard` 가 `robot.send_action` 으로 보내는 값만 제한. Pan 명령 \|·\| > 95 → ±95 까지만 | 시험 B: 리더 Pan 100° → 보낸 값 최대 95.0 |
| 지속 Goal/Present 추종 오차 감지 | **추가**: 팔 관절 리더−팔로워 > 25° → 팔로워를 그 순간 자세에 고정 (막힘 밀기 중단). 15° 이상이 1 s 넘게 이어지면 알림 | 시험 B: 막힌 팔로워 → 고정, elbow 명령 ≤ 팔로워 + 25° |
| 남은 명령 큐 무효화 | 해당 없음: 녹화 경로에는 정책 · action 큐가 없다 (매 틱 리더 값 1 개). 보호가 걸리면 고정 자세만 보냄 | lerobot record_loop 소스 |
| 안전 정지 때 자동 홈 복귀 방지 | 보호는 홈으로 보내지 않는다 (고정 = 그 자리). lerobot record() 에도 홈 동작 없음 | 시험 B: 고정 중 pan 95.0 유지 |
| 리더/팔로워 자세 차이 점프 방지 | 기존: 녹화 시작 → BLOCK (25°). **추가**: 준비 단계 시작 · 연결 직후에도 25° 넘으면 팔로워 고정 → 리더를 팔로워 자세 ±10° 로 맞추면 풀림 | 시험 B: 리더−팔로워 97° → 고정 (점프 없음) → 맞춘 뒤 풀림 |
| 정책 추론과 텔레오퍼레이션 동시 명령 | **추가**: `record` 시작 전 다른 lerobot-record/teleoperate/rollout · eval_ui · rollout_logged · r12 녹화 프로세스나 로봇 · 카메라 장치를 연 프로세스가 있으면 시작 거부 | 시험 A: 가짜 lerobot-record 프로세스 찾음 |
| 녹화 중 보호가 걸린 판 | 무효 시연: 사유를 알리고 그 판을 저장하지 않음 (← 와 같은 lerobot 다시 찍기 경로). 기록되는 action 은 보호와 무관하게 리더 값 | 시험 B: 무효 판 0 저장, 정상 판 action = 리더 값 |
| 기존 안전 조건 | 완화 없음 (pan 95 · 한계 10 · 리더−팔로워 25 · NaN BLOCK 그대로) | 시험 A: 설정 값 비교 |

- 명령 보호는 기본 설정 (기존 r1/r2 세션) 에서는 꺼져 있다. 기존 녹화 동작은 그대로다 (시험 B, 회귀 시험).
- 동시 프로세스 검사 (녹화 시작 전) 는 모든 세션에 적용된다 (기존 세션 포함 — 막는 쪽으로만 바뀜). 편집기 · grep 등은 이름이 같아도 제외한다.

## 7. 시험 (로봇 · 카메라 연결 0 회)

| 시험 | 결과 | 내용 |
|---|---|---|
| `tests/test_pilot12.py` (새) | PASS 39/39 | A 단위 24: 설정 · 계획 · 시작 조건 · 동시 프로세스 · 닫힘 세기 · QA 규칙. B 실제 lerobot `record()` + 가짜 팔로워 (명령을 따라감) · 리더 15: 시작 프레임 PNG · Pan 제한 · 무효 자동 버림 · 고정 · 풀림 · 막힘 · d2 형식 · 기본 설정 보호 꺼짐 |
| `tests/test_preview_pilot12.py` (새) | PASS 15 | 실제 `r12_collect.py preview --config` 를 pty 로 R1 · R2-P · R2-O 각 2판: 체크리스트 · 흐름 · pilot_start · r12_pilot_episodes.csv · R2-O 닫힘 경고 없음 · 실행 기록 + 파일럿 QA (가짜 장치 dataset) |
| 기존 `test_units.py` | 72/76 (변경 전과 같음) | 실패 4 건은 11-03 r2_pilot 40 편 설정 변경 뒤부터 있던 옛 기대값 (32 편 · K 마다 4 · 각도마다 8 · 깊이 범주) — 이번 변경과 무관, 시험 파일 그대로 |
| 기존 `test_errors.py` · `test_entry_stub.py` · `test_preview_flow.py` · `test_preview_r1.py` | 6/6 · 19/19 · 13 · 11 | 변경 전과 같음 |
| `r2_grasp_diagnostic/tests/test_r12_r2_config.py` | ALL_PASS | 기존 설정 그대로 (이 시험이 자기 출력 `tests/_out/r12_r2_config.json` 을 다시 씀) |
| 영상 창 실행 (디스플레이 :1, preview) | 화면 확인 | `screenshots/pilot12_*.png` — R2-O 준비 · R1 녹화 등 |

결과 원문: `tests/results/pilot12_*.txt`.

## 8. 실물 실행 때 남은 위험

1. **추종 오차 25° 고정의 실제 빈도.** 실물에서 빠르게 움직이면 리더−팔로워 차이가 25° 를 넘을 수 있다.
   - 넘으면 팔로워가 멈추고, 녹화 중이면 그 판은 무효가 된다.
   - 첫 1–2 판에서 화면의 '리더−팔로워' 값을 보고, 너무 자주 걸리면 `hold_gap_deg` 를 조정한다 (안전 쪽으로만).
2. **보호 · 탭의 30 Hz 루프 영향은 실물에서 미측정.** 가짜 장치에서는 29.9–30.0 Hz, 작업 시간 평균 1.3 ms 였다.
3. **종료 (Esc) 때 토크가 꺼진다** (lerobot `disable_torque_on_disconnect`, d2 녹화와 같음). 팔을 쉬는 자세에 둔 뒤 끝낸다 (체크리스트에 있음).
4. **동시 명령 검사는 녹화 시작 때 한 번이다.** 녹화 중 다른 터미널에서 eval_ui 등을 띄우면 막지 못한다 (포트 충돌로 실패할 가능성이 높음). 녹화 중에는 다른 로봇 프로그램을 실행하지 않는다.
5. **R2-O 준비 자세.** 닫힌 그리퍼로 큐브 앞까지 가는 동안 손가락 · 큐브 접촉은 관절값으로 판정하지 않는다. 눈으로 확인한다.
   - 접촉 · 밀림이 있으면 그 판은 ← 로 버린다.
6. **R1 지나침 준비.** 팔을 접은 채 Pan 을 크게 돌린다. 케이블 · 상자 간섭은 눈으로 확인한다. 녹화 시작 \|pan\| > 95 는 BLOCK, 녹화 중 Pan 명령은 ±95 에서 멈춘다.
7. **시작 상태 비슷함 · QA 판정은 근사다** (2D 손목 영상, 판마다 ±9° 흔들리는 Pan 기준). 학습 적합 여부는 영상을 보고 사람이 정한다.
8. 실물 Hz · 늦은 틱 · 카메라 반복은 녹화마다 화면과 `r12_episodes.csv` 에 남는다. 첫 실행은 `--num 2` 정도로 짧게 한다.

## 9. 준비 상태

- 로봇 없이 확인할 수 있는 것은 모두 통과했다: 설정 · 계획 · UI 흐름 · 기록 · 명령 보호 · QA.
- 실물 연결 · 녹화는 사용자가 직접 결정해 실행한다.
- 실물 첫 실행 전 사용자 확인이 필요한 것: 위 §8 의 1 · 3 · 5 · 6, 그리고 `preview` 를 한 번 직접 실행.
