# 02. R1/R2 데이터셋 구성안

설정 파일: `config/r12_scenarios.yaml` (수량·시나리오 문구·안전 범위 모두 여기). 계획은 이미 만들어 두었다 (녹화 전이라 `plan --force` 로 다시 만들 수 있음):

| 그룹 | 세션 | repo_id | 편수 | seed | 계획 |
|---|---|---|---:|---:|---|
| r1_pilot | `main_k8/r1_realign_pilot` | `oxr/so101_k8_r1_realign_pilot` | 16 | 3101 | `r12_plan.csv`, `r12_sheet.md` |
| r2_pilot | `main_k8/r2_pregrasp_pilot` | `oxr/so101_k8_r2_pregrasp_pilot` | 32 | 3201 | 〃 |

R1 과 R2 는 **별도 세션 = 별도 LeRobot dataset** 이다. d2 (`main_k8/d2/dataset`) 와 d2 를 이룬 세션은 건드리지 않는다 (도구가 그 세션 이름을 거부함).

## 1. 공통 원칙

- **오류 자세는 녹화 전에 만든다.** 판마다 녹화 앞에 '준비' 단계(녹화 안 함)가 있고, 시작 자세 검사를 통과한 뒤 → 를 눌러야 녹화가 시작된다. 오류 자세로 가는 동작은 dataset 에 들어가지 않는다 (가짜 로봇 시험으로 확인, 05 문서).
- 시작할 때 그리퍼는 열림 권장 (그리퍼 < 15 는 WARN 표시만, 11-02 부터).
- 큐브 자리 = d2 와 같은 고정 위치 K1–K8, 각도 = d2 와 같은 0 / ↺30 / ↻30 / 45. 각 그룹 안에서 K·각도가 정확히 고르게 나뉜다 (R1: K마다 2, 각도마다 4 · R2: K마다 4, 각도마다 8).
- 좌우는 **로봇에서 상자를 볼 때** 기준 (K 번호 규칙과 같음). 좌우 시나리오 수는 같다.
- 판 끝 = d2 와 같이 상자에 넣고 쉬는 자세로 돌아온 뒤 →.
- FK 로 시작 상태를 판정하지 않는다. 시작 상태 기록 = 관절값 + 리더 값 + 손목 영상 큐브 위치(픽셀) + front 영상 큐브 좌표(H 보정). 물리적 접근 깊이는 `unknown`.

## 1-1. 처음 어긋남 = 판마다 정한 Pan 목표 (2026-10-30 추가)

판마다 **Pan 목표 = K 기준 + 처음 어긋남** 이 계획에 정해진다 (`r12_plan.csv` 의 `pan_offset_deg`, `pan_target_deg`, 계획표 굵은 글씨). 준비 단계에서 사용자가 먼저 이 pan 으로 옮긴 뒤 → 를 누른다.

- K 기준 = '큐브 가운데 pan'. d2 구성 세션 `redbox_t1_known`·`redbox_t3_known` 125편에서, 판마다 '열린 뒤 명령 그리퍼 <10 인데 팔로워 그리퍼 >6 이 5프레임 이어진 첫 프레임'(= 큐브를 쥔 순간)의 pan 을 잰 K 별 중앙값. FK 가 아니라 관절 기록에서 잰 값.

| K | 기준 pan | n | 단순 기하(−atan2 − 1.4°)와 차이 |
|---|---:|---:|---:|
| K1 | −33.5° | 16 | +2.5 |
| K2 | −1.9° | 15 | +0.7 |
| K3 | +31.2° | 16 | −0.2 |
| K4 | −46.2° | 16 | +3.1 |
| K5 | −2.6° | 16 | +0.9 |
| K6 | +44.6° | 15 | 0.0 |
| K7 | −70.7° | 16 | +1.2 |
| K8 | +69.5° | 16 | +1.7 |

- 로봇 왼쪽 = pan − (K7·K4·K1 열이 음수). 어긋남 (시나리오 판마다 차례로): R1-L −8/−11/−14 · R1-R +8/+11/+14 · R1-OL −16/−20 · R1-OR +16/+20 · R2-LEFT −3/−5 · R2-RIGHT +3/+5 · 나머지 0.
- 기준 + 어긋남이 |pan| 92° 를 넘으면 크기를 줄이도록 만들었다 (현재 계획에서 줄어든 판 없음). 가장 큰 목표: R1 K7 −90.7°, R2 73.7°.
- 화면: 노란·회색 배너에 '▶ Pan 목표 …', 영상 창 왼쪽 아래에 'Pan 지금 … → 목표 … : N° 더 왼쪽(−)/오른쪽(+)' (±6° 안이면 초록 ✓). 목표와 달라도 녹화를 막지 않고 ⚠ 만 띄운다. 실제 시작 어긋남은 `r12_episodes.csv` `start_pan_offset_deg` (= 시작 pan − K 기준) 로 남는다.
- 손목 회전·높이·깊이는 아직 글 안내 (목표 값 없음).
- 시작 위치(오답) `start_xy_cm` 도 계획에 들어간다 (Pan 목표 방향, 큐브 거리 + `start_radial_cm`). 화면 표시는 03 문서 §6-0.
- 시험 연습 그룹: `r1_trial` (practice/r1_trial: R1-L·R1-R·R1-OL 1판씩), `r2_trial` (practice/r2_trial: R2-AHEAD·R2-LEFT·R2-HIGH 1판씩) — `trial_practice.sh`.

## 2. R1 — 접촉 전 재정렬 (16편)

| ID | 편수 | 시작 상태 | 크기 (눈대중) | 시연 | 손목 화면 큐브 |
|---|---:|---|---|---|---|
| R1-L | 4 | 큐브 높이보다 3–5 cm 위, Pan 이 큐브보다 왼쪽 | TCP 3–6 cm 왼쪽 | Pan 을 되돌려 중심 → 파지 → 상자 → 쉬는 자세 | 보여야 함 |
| R1-R | 4 | 위와 좌우 반대 | 3–6 cm 오른쪽 | 〃 | 보여야 함 |
| R1-OL | 2 | 오른→왼으로 오다 큐브를 지나침 | Pan 10–20° 왼쪽 (절댓값 ≤ 95°) | 반대로 되돌려 재정렬 | 가장자리/안 보여도 됨 |
| R1-OR | 2 | 왼→오른으로 지나침 | Pan 10–20° 오른쪽 | 〃 | 가장자리/안 보여도 됨 |
| R1-TL | 2 | Pan 은 큐브 방향 ±3°, 손목 회전·굽힘 때문에 손가락 사이 중심이 왼쪽 | 1.5–3 cm | 손목·팔 고쳐 중심 → 파지 | 보여야 함 |
| R1-TR | 2 | 위와 좌우 반대 | 1.5–3 cm | 〃 | 보여야 함 |

좌 8 / 우 8. 실물 평가의 Pan −109° 이탈은 재현하지 않는다: |pan| > 95° 이면 녹화 시작 BLOCK (캘리브레이션 한계 ±110.2°).

**R1C-REGRASP (설계만, 수량 0)**: 그리퍼를 큐브 앞에서 닫아 둔 상태(빈 파지 결과)에서 시작 → 열고 1–2 cm 후퇴 → 재접근 → 파지. 접촉 뒤 상태라 R1 과 섞지 않도록 별도 시나리오·별도 세션으로 둔다. 시작 그리퍼가 닫혀 있어 지금 안전 검사(그리퍼 열림)를 통과하지 못하므로, 수집하려면 이 시나리오에만 그리퍼 조건을 빼는 설정이 필요하다 (현재 미구현).

## 3. R2 — 파지 직전 정렬·깊이·닫힘 시점 (32편)

| ID | 편수 | 시작 상태 | 크기 (눈대중) | 시연 |
|---|---:|---|---|---|
| R2-AHEAD | 8 | 좌우 중심 맞음, 파지 높이, 큐브가 아직 손가락 사이에 안 들어옴 | 손가락 끝–큐브 앞면 1.5–3 cm | 다 들어올 때까지 전진 → 닫기 |
| R2-LOW | 4 | 큐브가 손목 화면 아래 가장자리에 걸침 (덜 들어감) | — | 충분히 진입 → 닫기 |
| R2-LEFT | 6 | 깊이·높이 근처, 손가락 사이 중심이 큐브 왼쪽 | 1–2 cm | 옆으로 고쳐 → 닫기 |
| R2-RIGHT | 6 | 위와 좌우 반대 | 1–2 cm | 〃 |
| R2-HIGH | 4 | 큐브 바로 위 가운데, 손가락이 옆면까지 안 내려옴 | 손가락 끝이 윗면보다 1–3 cm 위 | 내려가 감싼 뒤 닫기 |
| R2-READY | 4 | 거의 파지 가능 (대조군) | ≤ 0.5 cm | 필요하면 작게 고친 뒤 닫기 |

배분 근거 (측정 사실): 첫 파지 실패 12건 중 R2 계열 10건 (사용자 실물 평가), 그중 '큐브가 손가락 앞에 있는데 닫음' 이 다수 (pregrasp 검토 기록: 실패 대부분 'close short, cube ahead'). 그래서 AHEAD 를 가장 많이 둠.
파지 직전에 일부러 일정 시간 기다리는 시연은 하지 않는다 (시나리오 문구에 명시). 닫기 전의 실제 접근·정렬 동작이 녹화된다. 첫 닫힘까지 걸린 시간은 QA 가 판마다 잰다.

## 4. 판별 메타데이터

LeRobot v3 표준 판 스키마(`meta/episodes`)에는 임의 필드를 넣을 수 없다 → **sidecar** 로 관리:

| 파일 | 내용 |
|---|---|
| `<세션>/r12_plan.csv` | 계획 (줄 i = episode i): scenario_id, type, position(K), cube_xy_cm, angle, offset_dir, status(planned/recorded/excluded), retake_of, frames |
| `<세션>/r12_plan_meta.json` | 계획 만든 설정 사본·sha256, 통계 |
| `<세션>/r12_attempts.jsonl` | 시도마다 사건 기록 (추가만): armed(시작 관절·리더·검사), vision, rec_start(준비 자세→첫 프레임 이동), rec_end(프레임·Hz·늦은 틱·카메라 반복), label, discarded, saved, blocked, excluded |
| `<세션>/r12_episodes.csv` | 저장된 판마다 한 줄 (dataset total_episodes 기준으로 다시 만듦) |

`r12_episodes.csv` 열 ↔ 요청 필드:

| 요청 | 열 |
|---|---|
| recovery_type | `recovery_type` (R1/R2) |
| scenario_id | `scenario_id` |
| cube_position · 신뢰도 | `position`, `cube_xy_planned_cm`, `front_cube_xy_cm` (첫 화면 검출), `cube_position_confidence` |
| cube_rotation | `cube_rotation` |
| start_joint_state | `start_joint_state` (팔로워), `start_leader_action` |
| start_gripper_state | `start_gripper_state` |
| intended_offset_direction / magnitude | `intended_offset_direction`, `intended_offset_magnitude`, `planned_pan_offset_deg`, `start_pan_offset_deg`, `pan_reference_deg` |
| first_grasp_success · final_success · retry_count · operator_notes | 같은 이름 (터미널에서 1/2/3/m 입력) |
| (추가) | `wrist_cube_at_start` (dx, dy, 넓이, 가장자리), `physical_depth`=unknown, `frames`, `loop_hz_mean`, `late_ticks`, `camera_stall_ticks`, `start_shift_deg`, `attempt_id`, `run_id`, `retake_of` |

## 5. 과제 문장 · 학습 호환

- 과제 문장 = d2 와 같은 `pick up the red cube and put it in the brown box` (도구가 설정에서 넣음, 손으로 바꿀 수 없음). R1/R2 구분은 문장이 아니라 dataset·sidecar 로 한다. → 섞어 학습할 때 π₀.₅ 프롬프트가 d2 와 같다.
- 형식 호환 조건은 `analysis_handoff.md` §3.
- R1/R2 는 중간 자세에서 시작하는 판이다. 기본 자세에서 시작하는 전체 작업은 d2 에만 있다 → R1/R2 만으로 학습하지 않고 d2 와 섞는 실험을 전제로 한다. 섞는 비율은 정하지 않았다 (Ablation 대상).
- 판 끝은 d2 와 같이 쉬는 자세 (QA 가 확인).

## 6. 조정 방법

수량·문구를 바꾸려면 `config/r12_scenarios.yaml` 의 `count`/`start`/`demo` 를 고친 뒤 **녹화 전에** `plan --group <그룹> --force`. 녹화가 시작된 세션은 계획을 다시 만들 수 없다 (도구가 거부). 녹화 뒤 버릴 판은 `exclude` (dataset 은 그대로, 같은 시나리오 재촬영 줄이 계획 끝에 붙음).

## 7. 2026-10-30 변경 (사용자 결정)

- R2-LEFT/RIGHT 처음 어긋남: ±3·5° → **큐브 쪽 좌우 1.5 / 2.5 / 3.5 cm** (`lateral_offsets_cm`), K 거리 r 로 pan = atan(cm / r) 환산 → 현재 계획 3.1–12.0°. 근거(기록): d2 평가 빈 닫기 때 pan 오차 +5…+12°, 사람 시연에서 1 cm 넘는 좌우 수정 37/256판 (왼쪽 6).
- R1 수량: L 3 · R 3 · OL 3 · OR 3 · TL 2 · TR 2 (지나침 4 → 6). 지나침 크기 16·20° → **25·30°** (큐브가 손목 화면에서 사라질 만큼). |pan| ≤ 92° 를 넘는 판은 다른 판과 K 를 바꿔 배치 (현재 계획에서 줄어든 판 없음). 근거(기록): −109° 이탈은 큐브가 손목 화면에서 사라진 뒤 같은 방향으로 계속 돈 경우.
- 둘러보기(탐색) 시연은 넣지 않음: front 영상에 큐브가 보이고, 방향 없는 탐색은 같은 장면에 다른 정답을 만든다. 대신 '안 보이면 바로 큐브 쪽으로 되돌아오기' = R1-OL/OR.
- 시연 속도 안내 (`pace_text`): 고칠 때 1–2초에 걸쳐 손목 화면을 보며 (크게 → 작게), 큐브가 손목 '닫기 영역'에 들어오면 닫기, 일부러 멈추지 않기. 근거(기록): d2 사람 시연은 98% 가 pan 을 한 번에, 시작 뒤 0.8 s 에 90% 완료.

## 11. 2026-11-02 R1 을 '녹화 중 어긋남' 방식으로 바꿈

사용자 연습 (practice/r1_trial 3편, 옛 방식 — `practice/r1_trial_old_20261102/` 로 옮김) 뒤 의견: "처음 위치는 고정하고, 정렬할 때 지나치거나 덜 가서 다시 재정렬해야 하지 않나", "2번째는 그은 선으로는 다른 정렬값인데 현실에서는 그냥 바로 앞".

옛 방식 연습 기록에서 잰 값:

| ep | 시나리오 | K | 계획 Pan 목표 | 시작 자세 | 손목 첫 화면 큐브 | 파지 때 pan (대략) |
|---|---|---|---:|---|---|---:|
| 0 | R1-L | K7 | −78.7 | 쉬는 자세 (lift −102.5) + pan −78.2 | dx +0.54 dy −0.69 (가장자리) | −62 |
| 1 | R1-R | K8 | +77.5 | 쉬는 자세 + pan +76.9 | dx −0.23 dy +0.06 (거의 가운데, 손가락 바로 앞) | +73…+75 |
| 2 | R1-OL | K3 | +6.2 | 쉬는 자세 + pan +6.0 | 안 보임 | +38 |

- 세 판 모두 쉬는 자세에서 pan 만 돌려 시작함 (설계의 '큐브 위 3–5 cm' 자세가 아님).
- K7·K8 은 로봇 밑동에서 약 16 cm 로 가까워, pan 8° ≈ 탁자 위 2.2 cm. ep1 손목 첫 화면은 큐브가 손가락 바로 앞.
- 파지 때 pan 이 K 기준 pan (d2 중앙값) 과 4–8° 다름 (K7 −62 vs −70.7, K8 ≈ +74 vs +69.5, K3 +38 vs +31.2; 각 1편). 기준 pan 으로 그린 '지금 Pan' 방향선은 실제 방향과 달랐음.

바꾼 것:
- R1-OVER (지나쳤다 되돌아오기) 6 · R1-UNDER (덜 갔다 더 가기) 6 · R1-TL/TR (손가락 사이 2.5 cm 어긋남) 2+2 = 16. 옛 R1-L/R/OL/OR 은 수량 0 (정의는 옛 기록을 읽으려고 남김).
- 시작 = 쉬는 자세 (고정, d2 와 같음). 준비 단계는 큐브 각도만. 어긋남은 녹화 중에 만든다.
- 주황 ✕ = 큐브를 로봇 밑동 둘레로 5·7·9 cm 돌린 탁자 위 점 (지나침 = 진행 방향 너머, 덜 감 = 진행 방향 앞). 진행 방향 = 쉬는 자세 pan (−4°) → K 기준 pan. 지나침/덜 감은 진행 방향이 분명한 K1·K3·K4·K6·K7·K8, TL/TR 은 K2·K5 → K 마다 2편.
- ✕ 에 닿으면 Space = 재정렬 시작 표시 (프레임·pan 을 r12_attempts.jsonl `mark` 사건 → r12_episodes.csv `realign_mark_frames`·`realign_mark_pan`). QA 에 '재정렬 표시' 열 (Space pan → 닫기 시작 pan), error_in_rec 시나리오에 Space 가 없으면 ⚠.
- Space 앞 구간의 행동은 큐브에서 멀어지거나 멈추는 행동이다. 학습에 그대로 쓸지, Space 프레임부터 잘라 쓸지는 정하지 않았다 (dataset 은 전체 저장).
- 영상 창: '지금 Pan' 방향선(앞의 K 기준 pan 으로 그린 선) 삭제. 녹화 중 어긋남 시나리오는 ✕ · 큐브 목표 윤곽 · ✕→큐브 화살표만.
- (11-02) 멈출 곳 표시: 로봇 밑동 → 멈출 곳(✕) 주황 방향선 (옛 시작선과 같은 방식) + 밑동 → 큐브 초록선. 짧은 가로 선은 사용자 요청으로 되돌림.
- (11-02) 로봇선 (하늘색): 지금 pan 을 K 기준 pan 매핑으로 그린 선 + 세션 보정. 준비 때 그리퍼를 큐브 바로 위에 두고 c → 보정 = 지금 pan − K 기준 pan (|보정| > 15° 면 거부), `<세션>/r12_pan_calib.json` 에 저장·다음 실행에도 씀, `pan_calib` 사건. 보정 없으면 11-02 연습 기준 실제와 4–9° 다를 수 있음.

## 12. 2026-11-02 R1/R2 정의 수정 (사용자 지시) — R2 는 현재 기준, R1 은 §13 으로 바뀜

이 절이 앞 절(§11 포함)보다 우선한다. 손가락·TCP 의 미세 어긋남은 R1 이 아니라 R2.

### R1 = Shoulder Pan 중심의 접근 방향 재정렬 (16) — 세션 `main_k8/r1_realign_pilot`

| scenario_id | 편수 | 오차 종류 (error_kind) | 시작 조건 | 오차 (주황 선) | 목표 동작 |
|---|---:|---|---|---|---|
| R1-PAN-L | 4 | wrong_target | 쉬는 자세 (고정), 큐브 각도만 맞춤 | Pan 목표가 큐브보다 왼쪽(−) 12·14·16·20° | 틀린 목표 쪽으로 접근 → Space → 큐브 방향으로 고쳐 접근 → 파지 → 상자 → 쉬는 자세 |
| R1-PAN-R | 4 | wrong_target | 〃 | 오른쪽(+) 12·14·16·20° | 〃 |
| R1-OVER | 4 | overshoot | 〃 | 진행 방향(쉬는 자세 pan −4° → K) 으로 큐브 방향을 15·18·20·25° 지나침. K1·K3·K4·K6·K7·K8, 왼쪽/오른쪽 2·2 | 지나친 뒤 Space → 되돌아와 큐브 방향 → 파지 |
| R1-DRIFT | 4 | drift | 〃 | 큐브 방향으로 맞춘 뒤 팔을 펴며 접근하는 중 Pan 이 왼쪽/오른쪽 12·16° 흐름 (판마다 방향) | 흐른 뒤 Space → 큐브 방향으로 고쳐 접근 → 파지 |

- 어긋남은 녹화 중에 만든다 (Lift·Elbow 동시 움직임 허용). 손가락 끝단 미세 파지 오차는 시작 조건으로 쓰지 않는다.
- 크기 ≥ 12°: 11-02 연습 6판에서 사람 파지 pan 이 K 기준과 +8.7, +4.5, +7.0, −3.9, ≈−1, −6.3° 달랐음 (±9° 안팎).
- 안전: 계획 |Pan 목표| ≤ 92° (넘으면 크기를 줄이거나 K 교환; 현재 계획 최대 86.7°). 실물 평가의 −109° 이탈 재현 안 함. 녹화 시작 → 를 막는 것은 관절값 없음/NaN 뿐 (11-02), 나머지 안전 항목은 경고로 표시·기록.
- K 마다 2편, 각도마다 4편, 왼쪽/오른쪽 8/8.

### R2 = 파지 직전 국소 정렬·접근 깊이·닫힘 타이밍 (32) — 세션 `main_k8/r2_pregrasp_pilot`

| scenario_id | 편수 | 오차 종류 | 국소 오차 방향 (r2_local_error_dir) | 시작 조건 (준비 단계, 녹화 안 함) | 손목 화면 시작 영역 (u, v) | 목표 동작 |
|---|---:|---|---|---|---|---|
| R2-DEPTH | 8 | depth | shallow (0.5·1.0·1.5 cm) | 그리퍼 열림, 좌우 중심, 파지 높이. 큐브가 손가락 끝 사이에 일부만 | u 0.22–0.50, v 0.48–0.62 (닫기 영역 바로 위) | 더 밀어 넣어 닫기 영역에서 한 번 닫기 → 상자 → 쉬는 자세 |
| R2-AHEAD | 8 | ahead | ahead (1.5·2.0·3.0 cm) | 큐브가 손가락 끝보다 1.5–3 cm 앞 | u 0.22–0.50, v 0.25–0.47 | 전진해 닫기 영역에서 한 번 닫기 |
| R2-LEFT | 4 | lateral | robot_left (1.5·2.5·3.5 cm) | 손가락 사이 중심이 큐브 왼쪽 | u 0.45–0.72, v 0.55–0.85 (큐브가 화면 오른쪽) | 옆으로 고쳐 닫기 영역에서 닫기 |
| R2-RIGHT | 4 | lateral | robot_right (1.5·2.5·3.5 cm) | 손가락 사이 중심이 큐브 오른쪽 | u 0.03–0.26, v 0.55–0.85 (큐브가 화면 왼쪽) | 〃 |
| R2-READY | 8 | none | none | 큐브가 손가락 사이 거의 가운데 | 닫기 영역 (u 0.255–0.432, v 0.633–0.78) | 필요하면 아주 작게 고친 뒤 한 번 닫기 |

- Pan 목표 없음 (pan_offset 0). 작은 Pan 수정은 허용. K 기준 pan 의 판마다 ±9° 흔들림 때문에 cm 단위 좌우 오차를 Pan 값으로 정할 수 없어 손목 화면 영역으로 정함.
- 시작 영역 근거: d2 닫기 시작 순간 큐브 v 중앙값 0.71·넓이 0.11, 1 s 전 v 0.60·넓이 0.089 (덜 들어갈수록 위쪽·작게). 좌우 부호 (그리퍼가 큐브 왼쪽 → 큐브가 화면 오른쪽) 는 연습 2판 근거, 첫 수집 뒤 QA 로 확인.
- K 마다 4편, 각도마다 8편.
- 구 정의 R1-L/R/OL/OR/UNDER/TL/TR, R2-LOW/HIGH 는 수량 0 (옛 연습 세션 기록을 읽으려고 정의만 남김).

### 저장 구조 (LeRobot dataset 은 d2 와 같은 형식 — 바꾸지 않음)

| 파일 | 내용 |
|---|---|
| `<세션>/dataset/` | LeRobot v3.0, d2 와 같은 features·fps·robot_type·task 문장. R1/R2 구분 정보는 넣지 않음 |
| `<세션>/r12_plan.csv` | 판별 계획: scenario_id, type(R1/R2), K, 각도, **error_kind, r1_pan_error_dir, r1_pan_error_deg, r2_local_error_dir, r2_local_error_cm**, pan_offset/target, 상태 |
| `<세션>/r12_attempts.jsonl` | 사건: armed · rec_start · rec_end · **mark (Space: frame, pan)** · **pan_calib (c)** · label · saved · discarded |
| `<세션>/r12_episodes.csv` | 저장된 판마다: recovery_type(R1/R2), scenario_id, error_kind, r1_pan_error_dir/deg, r2_local_error_dir/cm, **r2_wrist_start_in_region**, 시작 관절·리더 값, start_pan_offset_deg, **realign_mark_frames/pan**, 결과(첫 파지·최종·재시도·메모), 프레임·Hz |
| `<세션>/r12_pan_calib.json` | 로봇선 보정 (c 키) |
| `<세션>/qa/r12_qa_report.md`·`r12_qa.csv` | 품질 검사 (R1 Space 없음 ⚠, R2 첫 화면 손목 큐브가 시작 영역 밖 ⚠ 포함) |

## 13. 2026-11-02 작업 지시서 (3차) — R1 (§14 로 바뀜)

지시서 3.5: 잘못된 시작 자세를 만드는 과정은 정답 행동으로 녹화하지 않는다. 따라서 §11·§12 의 '녹화 중 오차 + Space' R1 (R1-PAN-L/R · OVER · DRIFT) 은 수량 0 으로 두고, 시작 자세를 준비 단계(녹화 안 함)에서 만드는 R1 으로 바꿨다.

### R1 16편 = 시작 자세 2 × 손목 가시성 2 (각 4, 셀 안 왼쪽 2 · 오른쪽 2)

| scenario_id | 시작 자세 (`start_pose_type`) | 손목 가시성 목표 (`wrist_visibility_target`) | 명목 Pan 오차 (°) | 편수 |
|---|---|---|---|---:|
| R1-HOME-VIS | home_near (쉬는 자세 근처, 팔 접힘) | visible_or_edge | ±15, ±20 | 4 |
| R1-HOME-OUT | home_near | absent (front 에는 보임) | ±25, ±30 | 4 |
| R1-MID-VIS | mid_approach (팔 일부 폄, 그리퍼 탁자 위 8 cm 이상) | visible_or_edge | ±15 | 4 |
| R1-MID-OUT | mid_approach | absent (front 에는 보임) | ±20, ±25 | 4 |

- Pan 오차 = K 기준 pan (`pan_reference_deg`, d2 파지 순간 pan 의 K 별 중앙값) 대비. 계획의 Pan 목표 = 기준 + 명목 오차, |Pan 목표| ≤ 92°. 계획 최대 |pan| 85.7°, 줄어든 판 0.
- ±25–30° 는 접힌 팔(home_near)에 두고, 편 팔(mid_approach)은 최대 25°. 편 팔로 돌리기 위험하면 20° 로 줄이고 메모 (실제 시작 pan 은 기록됨).
- 큐브 위치: K1–K8 각 2편 (로봇 왼쪽 K1·K4·K7 / 가운데 K2·K5 / 오른쪽 K3·K6·K8 모두). 새 위치는 추가하지 않았다 (좌표 확인된 K 만 사용).
- 각도 4가지 각 4편. 그리퍼: d2 와 같이 열림 시작, 별도 오프셋·시나리오 변수 없음.
- 계획 파일: `main_k8/r1_realign_pilot/r12_plan.csv` (seed 3101), 시험 연습 4편 `practice/r1_try2` (셀마다 1편, 좌우 2/2, K4·K5·K6·K8).
- 시작 자세 만드는 순서 (안내): 팔을 접은 채 Pan 을 주황 선으로 → (mid_approach 만) 그다음 팔을 편다. 편 팔로 크게 돌리지 않는다.
- 측정 한계: K 기준 pan 은 판마다 사람 파지 pan 과 ±9° 다르다 (11-02 연습 6판: +8.7, +4.5, +7.0, −3.9, ≈−1, −6.3). 그래서 오차 값은 '명목' 이고, 실제 시작 상태는 시작 관절값·손목/front 가시성으로 기록한다.

### 저장 구조 (dataset 은 d2 와 같은 형식, 아래는 sidecar)

`r12_plan.csv` 새 열: `pan_error_direction` (left/right) · `nominal_pan_error_deg` · `start_pose_type` · `wrist_visibility_target` · `local_alignment_type` · `nominal_local_error_cm` (R1/R2 해당 없는 쪽은 빈칸).

`r12_episodes.csv` (판마다, 지시서 §5 이름):

| 구분 | 열 |
|---|---|
| 공통 | episode_id (`<repo_id>:<번호 4자리>`) · episode_index · dataset_group (R1/R2) · scenario_id · error_kind · cube_position · cube_rotation · start_joint_state · start_gripper_state · recording_fps (30) · loop_hz_mean · first_grasp_success · final_success · retry_count · operator_notes |
| R1 | start_pose_type (계획) · start_pose_measured (시작 관절값: lift ≤ −80 & elbow ≥ 70 → home_near) · pan_error_direction · nominal_pan_error_deg · measured_start_pan_error_deg (= 시작 pan − K 기준 − 세션 보정 c) · pan_error_estimate_confidence (low = 보정 없음, medium = c 보정 있음; high 는 쓰지 않음) · wrist_visibility_target · wrist_cube_visibility (visible/edge/absent) · front_cube_visibility (visible/offset/not_detected) · recovery_completed (결과 1·2·4 = yes, 3 = no) · start_safety_confirmed |
| R2 | local_alignment_type (depth_short/cube_ahead/fingers_left/fingers_right/near_aligned) · nominal_local_error_cm · cube_relative_position_in_wrist (u, v, 넓이 비율) · approach_depth_category (partial/not_entered/lateral_offset/sufficient) · first_close_result (grasped/missed_then_retry/failed, 결과 1/2/3 에서) · retry_count · r2_wrist_start_in_region |

- `r12_attempts.jsonl` 새 사건: `safety_confirmed` (R1 시작 자세 확인), `armed` 에 `pan_calib`·`safety_confirmed`.
- 값 이름 변경: §12 의 r1_pan_error_dir/deg → pan_error_direction/nominal_pan_error_deg, r2_local_error_dir/cm → local_alignment_type/nominal_local_error_cm, recovery_type → dataset_group, position → cube_position. 이미 녹화된 practice 세션(`r1_trial`, `r1_try`)의 r12_episodes.csv 는 바꾸지 않았다.
- d2+R1, d2+R2, d2+R1+R2 구성: 세 dataset 모두 features·fps·과제 문장이 d2 와 같아 그대로 합칠 수 있다. 혼합 비율·가중치는 정하지 않았다.

## 14. 2026-11-02 작업 지시서 (4차) — R1 현재 기준

### 왜 바꿨나 (사용자 기록에서 확인한 사실)
- 11-02 R1 실행 기록 (`practice/*/r12_attempts.jsonl`, `~/.local/state/record_ui/record_20261102_*.log`):
  - 10:03·10:27·10:30·10:56·11:00 실행은 준비 단계에서 Esc 로 끝남 (녹화 0). 그때 BLOCK 은 쉬는 자세의 lift −102.9° (캘리브레이션 한계 −104° 까지 1°) 와 닫힌 그리퍼였다 (11-02 오전 완화 전 규칙). 11:06 이후 실행에는 blocked 사건이 없다.
  - 13:20 `r1_try` 4편, 13:52 `r1_try2` 2편 (+1 버림) 은 녹화됐다. `r1_try2` 의 두 시작 자세는 모두 lift −103·elbow 96 (팔 접힘) 이었고 그리퍼는 닫힘(1–3) 이었다 — 계획한 '접근 중간' 이 만들어지지 않았다. ep1 은 front 큐브가 계획 K4 에서 23 cm 떨어진 곳 (상자 안 좌표) 에서 검출됐고, 그리퍼를 열지 않고 끝났다.
  - `r1_try2` ep1 첫 프레임: 리더 pan −26.5°, 팔로워 −60.7° (차이 34°), 팔로워가 0.3 s 에 28° 움직임. 원인: 결과 단계 → 뒤 저장(약 6 s) 이 끝나자마자 녹화가 시작되는 흐름에서 저장 중 리더가 움직였다. 다른 11편의 첫 프레임 리더−팔로워 차이는 ≤ 2.9°.
- 3차 정의의 시작 조건 (HOME/MID 관절 기준·손목 가시성·명목 Pan) 은 경고였고 녹화를 막지 않았다. 다만 K 기준 pan 이 판마다 ±9° 흔들려 Pan 안내 (±6° ✓) 가 실제 큐브 방향과 어긋날 수 있었다. MID 는 큐브 거리 −4 cm 를 시작점으로 그려, 큐브와 가까운 시작을 안내했다.

### R1 16편
| scenario_id | 상태 (준비 단계에서 만듦, 녹화 안 함) | 접근 단계 (기대) | 손목 | 명목 Pan 오차 (후보) | 편수 |
|---|---|---|---|---|---:|
| R1-A | 접근 초반, Pan 이 큐브와 다른 방향 | early | 상관없음 | ±15, 20, 25, 30 | 4 |
| R1-B1 | 팔을 펴며 다가가다 Pan 이 큐브에서 멀어지는 쪽으로 감 | mid | 상관없음 | ±15, 20 | 4 |
| R1-B2 | 반대쪽에서 와서 큐브 방향을 지나쳐 멈춤 | mid/late | 상관없음 | ±15, 20, 25 | 4 |
| R1-B3 | 접근 중 Pan 이 벗어나 손목 화면에서 큐브가 사라짐, front 에는 보임 | mid/late | 안 보임 | ±20, 25 | 4 |

- 시나리오마다 왼쪽 2 · 오른쪽 2. 녹화는 올바른 방향으로 되돌리는 행동부터 (틀린 쪽 이동을 일부러 녹화하지 않음). 자연스럽게 생긴 오차를 고치는 연속 시연은 허용 — 이때도 복구 측정이 남는다.
- 접근 단계 = 시작 lift 의 진행률 (쉬는 자세 lift −103 → 그 큐브 거리의 d2 파지 lift). d2 파지 lift (redbox_t1/t3_known 128편, 파지 순간 K 별 중앙값) 를 거리 r 로 직선 맞춤: lift_g = −65.2 + 4.04·r (K 8점 최대 잔차 2.7°). early < 0.4 ≤ mid < 0.85 ≤ late. HOME/MID 고정 관절값은 쓰지 않는다.
- 큐브 자리: K1–K8 각 1 + 자유 점 F1 (−12.75, 19) · F2 (−12.75, 4) · F3 (−21.25, 26.5) · F4 (−21.25, −3.5) 각 2. 자유 점은 K 사이, 밑동 거리 17.5–19.9 cm (d2 파지 거리 14–27 cm 안), front 화면 안. 탁자 표시가 없어 사람이 대략 놓고 front H 검출로 기록. 준비 단계에서 `x` 로 지금 검출된 자리 X(x,y) 를 쓸 수 있다.
- Pan 기준: K = d2 중앙값 (`pan_reference_source = d2_K_median`), F·X = 기하 −atan2 − 1.4° (`geometry`, K 에서 d2 중앙값과 −0.2…+3.1° 차이). 계획 최대 |pan| 84.2°, 줄어든 판 0.
- 시험 연습: `practice/r1_try3` (A·B1·B2·B3 각 1, F2·F1·K1·K2, 좌우 2/2).

### 메타데이터 (r12_episodes.csv, R1 추가 열)
| 지시서 항목 | 열 |
|---|---|
| 시작 Pan 실제 관절값 | start_pan_deg (+ start_joint_state) |
| 큐브 위치와 Front/Wrist 가시성 | cube_position (K#/F#/X(x,y)) · cube_xy_cm_used · cube_position_source (K_grid/free_point/front_detected) · cube_position_confidence · front_cube_xy_cm · front_cube_visibility · wrist_cube_visibility |
| 복구 시작 시 접근 단계 | approach_stage_at_start (early/mid/late) · approach_progress · approach_stage_expected |
| 최초 Pan 이동 방향 | setup_pan_motion (준비 단계 마지막 3 s) · first_pan_move_dir (toward/away) · first_pan_move_deg |
| Pan 방향 반전 여부·시각 | pan_reversal · pan_reversal_t_s (녹화 시작 기준, 음수 = 준비 단계에서 이미 반전) · pan_reversal_kind (away→toward 등) · pan_reversals_in_rec |
| 반전 전후 Pan 변화량 | pan_change_before_reversal_deg · pan_change_after_reversal_deg |
| 큐브 재획득 | cube_reacquired_in_wrist · cube_reacquire_t_s (손목 화면 10 틱마다 빨강 검출, 두 번 이어 보이면 찾음) |
| 정상 접근·파지 | first_grasp_success · final_success · recovery_completed · grasp_start_t_s · pan_error_at_grasp_deg |
| 그 밖 | measured_start_pan_error_deg · pan_reference_source · pan_error_estimate_confidence · start_safety_confirmed · scenario_override (s/d/k/x 사용 기록) |

- 측정 구간 = 녹화 시작 ~ 파지 시작 (명령 그리퍼가 열린 뒤 최대 열림에서 10 줄어든 첫 프레임). 상자로 옮기는 Pan 은 뺀다. 리더를 끝까지 닫지 않는 시연(r1_try2 ep0, 12.8 까지) 도 찾는다.
- 이동 = 5 프레임 평균 pan 이 3° 이상 이어진 움직임. 'toward' = 큐브 기준 pan 까지 거리가 줄어듦. 기준 pan 자체의 ±9° 오차는 남는다.
- 녹화 중 값은 녹화 프로세스의 pan 열 (기록 값과 같은 관측) 로 대략 재고, QA 가 dataset state·영상으로 다시 잰다.
- 사용자 기록 r1_try2 를 QA 로 잰 값 (출력은 임시 폴더): ep0 시작 Pan +68.7° (K6 기준 +24.1°), 녹화 첫 이동 큐브 쪽 −37.2°, 큐브를 지나친 뒤 되돌아옴 (toward→toward 반전 @2.77 s, +12.0°), 파지 시작 9.97 s Pan 오차 −1.8°. ep1 은 파지 시작 없음.

### 값 이름 (3차 → 4차)
- 계획 새 칸: approach_stage_expected, cube_position_source. start_pose_type 은 3차 줄에만 남음.
- 판 칸에서 start_pose_measured 를 approach_stage_at_start / approach_progress 로 바꿈.
- 3차 시나리오 R1-HOME-VIS/OUT, R1-MID-VIS/OUT 는 수량 0 (r1_try2 기록을 읽으려고 남김).
