# 05. 로봇 미연결 검증 결과

실행일 2026-10-30. 실제 로봇·리더·카메라 연결 0회, 실물 dataset 녹화 0편. 시험 출력 원문: `tests/results/`.

## 1. 시험 목록

| 시험 | 방법 | 결과 |
|---|---|---|
| 단위 (`tests/test_units.py`) | 계획 균형·재현성, Pan 목표 (부호·범위·기준+어긋남·목표에서 안전 검사 통과·안내 문구), 안전 검사 규칙, 시도 기록 접기, d2 세션 보호 | PASS 37/37 |
| 환경 확인 (`r12_collect.py check`) | 파일·장치 경로 존재, 캘리브레이션 한계, lerobot `record_loop` 인자 14개·`record()` 안 구문 4개가 진입점 가정과 같은지 (모듈만 불러옴) | 문제 없음 |
| 오류 처리 (`tests/test_errors.py`) | d2 세션·d2 폴더 거부, 설정에 없는 세션 거부, 계획 없으면 거부, lerobot 옵션 직접 입력 거부, 연결 실패 흉내 → 종료 코드 1·저장 0·파이썬 오류 없음 | PASS 6/6 |
| Preview 흐름 (`tests/test_preview_flow.py`) | 실제 `r12_collect.py preview` 를 pty 에서 실행, 키 바이트 전송 | PASS 13/13 |
| 진입점 + 실제 lerobot `record()` (`tests/test_entry_stub.py`) | lerobot 0.6.2 `record()` 를 가짜 로봇·리더로 실행, dataset 은 임시 폴더 | PASS 13/13 |
| 실제 화면 실행·스크린샷 (`tests/shot_session.py`) | xterm + 영상 창을 디스플레이 :1 에 띄워 R2 3판·R1 1판 Preview | 스크린샷 4장 (§4) |

## 2. Preview 흐름 시험 항목 (실제 터미널 UI 코드)

1. 첫 판 앞 준비 단계 (녹화 안 함) 배너
2. 쉬는 자세(재생 영상 시작)에서 → → 막힘 (lift 한계 1°, elbow 한계, 그리퍼 1 < 15)
3. 검사 통과 순간 → → '시작 자세 OK' → 녹화 ep0
4. → → 결과 입력 단계, 녹화 프레임·Hz 줄 (예: 91 프레임 · 30.03 Hz · 늦은 틱 0 · 카메라 반복 0)
5. 2, 2, m + 메모 "빈 파지 1번 q n r" + Enter → 재시도 2, 메모 저장. 메모 안의 q/n/r 이 lerobot 에 가지 않음 (종료·다음·다시가 일어나지 않음)
6. → → ep0 저장 → ep1 녹화
7. 녹화 중 ← → 버리기 예약, 그 판에는 결과 입력 거부
8. → → 버림 확인 → 같은 번호 ep1 다시 녹화
9. ep1 결과 1 → 저장 → ep2 (마지막 판)
10. 마지막 판 끝 → 결과 질문 (3 입력) → 종료 코드 0
11. 기록: `r12_attempts.jsonl` 저장 3·버림 1, `r12_episodes.csv` 3줄 (ep0: 첫 파지 False · 최종 True · 재시도 2 · 메모, 시작 관절값, 프레임 수), `r12_plan.csv` 상태 recorded ×3
12. Preview 폴더에 dataset 없음 · 로그에 'PREVIEW 모드' · Traceback 없음
13. 시험 동안 `~/so101_runs/main_k8` 폴더 변경 없음

예시 출력: `tests/results/preview_r12_episodes.csv`, `preview_r12_attempts.jsonl`.
첫 실행 중 1회 실패: 시험이 '검사 통과' 를 본 직후 재생 영상의 그리퍼가 15 미만으로 바뀌어 UI 가 → 를 막음 (제품 동작). 시험에 '막히면 다시 →' 를 넣은 뒤 연속 3회 통과.

## 3. 진입점 + 실제 lerobot `record()` (가짜 로봇)

장치 차단: 포트·카메라 경로 `/nonexistent/...`, `MotorsBusBase`·`SerialMotorsBus`·`FeetechMotorsBus`·`OpenCVCamera` 의 `connect` 와 `serial.Serial.open` 을 예외로 교체, `make_robot_from_config`·`make_teleoperator_from_config` 를 가짜만 돌려주게 교체, 연결 전에 가짜 클래스인지 assert. 진짜 SO101 클래스는 만들지 않음. 키 입력은 `events` 를 직접 세움.

| 항목 | 결과 |
|---|---|
| 쉬는 자세에서 → → 진입점 안 검사 BLOCK | gripper_closed, limit_elbow_flex, limit_shoulder_lift |
| 저장 편수 | 2 |
| 판 길이 = 녹화 단계 프레임 수 (버린 판 제외) | [30, 31] = [30, 31] |
| 준비 단계 쉬는 자세(lift −102.9)가 dataset 에 없음 | dataset lift 최소 17.5 |
| ← 로 버린 뒤 같은 번호 ep0 = 새 시도 (pan 10°) | 같음 |
| ep1 첫 프레임 = 준비 때 자세 (pan −20°) | 같음 |
| action = 리더 값 | 같음 |
| timestamp 간격 1/30 | 같음 |
| `features` 9개 (이름·dtype·shape·영상 코덱 설정) | d2 와 같음, 이름 집합 같음 |
| fps · robot_type · codebase_version | 30 · so_follower · v3.0 = d2 |
| 과제 문장 | d2 와 같음 (1개) |
| 첫 판 준비 중 Esc | 저장 0편, 오류 없음 |

만든 dataset 의 `info.json`: `tests/results/stub_dataset_info.json`. (robot_type 은 가짜 로봇의 이름에서 오므로 실제 팔로워 클래스 이름은 d2 notes 의 같은 클래스로 확인: `so_follower`.)

## 4. 바탕화면 스크린샷 (실제 실행 화면)

| 파일 | 크기 | 장면 |
|---|---|---|
| `~/Desktop/SO101_R1_R2_Collection_UI.png` | 2470×1038 | R2 · ep1 녹화 중 5 s (ep0 저장 결과·시나리오 집계 1/32 표시) |
| `~/Desktop/SO101_R1_R2_Collection_UI_R1.png` | 2470×1038 | R1 · ep0 준비 단계, → 가 시작 자세 검사로 막힌 직후 |
| `~/Desktop/SO101_R1_R2_Collection_UI_R2.png` | 2470×1038 | R2 · ep0 뒤 결과 입력 단계 (재시도 1 + 메모), 다음 판 R2-RIGHT 안내 |
| `~/Desktop/SO101_R1_R2_Collection_UI_Recording.png` | 2470×1038 | R2 · ep0 녹화 중 4 s |

같은 파일이 `screenshots/` 에도 있다. (2026-10-30 Pan 목표·시각 안내(지도·큰 글씨)를 넣은 뒤 다시 찍은 것. 모든 시험도 그 뒤 다시 실행해 위 결과와 같음.)

찍은 방법 (사실):
- 실제 `r12_collect.py preview` 가 디스플레이 :1 에서 실행됐고, Tk 영상 창과 xterm(터미널 UI)이 화면에 떴다. 키는 `tests/shot_session.py` 가 pty 로 자동 전송 (사람이 누르는 바이트와 같음).
- 각 창을 `xwd -id <창>` 으로 따로 찍어 왼쪽(영상 창) · 오른쪽(xterm) 으로 붙인 한 장이다. 두 창의 실제 화면 위치 관계는 아니다. 다른 창·바탕화면은 찍히지 않는다.
  (GNOME 합성 화면에서 `xwd -root` 는 창 내용이 검게 나왔고, 창이 겹치면 xterm 이 검게 나와 창을 겹치지 않게 놓았다. xterm 은 굵은 검정 글자를 회색으로 그려서 `boldColors: false` 로 gnome-terminal 과 같게 했다.)
- 영상·관절값 = `main_k8/redbox_t1_known` episode 5 의 review 영상·state/action 재생. 창 위 PREVIEW 띠와 각 영상 위 'PREVIEW · 기존 녹화 영상 재생 · 녹화 안 함' 표시가 있다. 큐브 위치는 계획 K 와 무관하다 (화면에 표시).
- 스크린샷의 이미지를 직접 열어 글자가 읽히는지 확인했다 (`Read` 로 4장 모두).

## 5. 시험하지 않은 것

- 실제 리더·팔로워·카메라로 녹화 (사용자 승인 필요). 실물 30 Hz 루프에서 탭이 더하는 시간, 실제 카메라 프레임의 검출 결과, 실제 저장 시간 동안 리더 이동.
- 녹화 프로세스가 1시간 넘게 준비 단계에 머무는 경우 (`setup_max_s` 반복 경로는 코드 검토만).
- 접촉 후 시나리오 R1C (수량 0, 미구현 조건 있음).
- QA 도구는 가짜 로봇 dataset 과 d2 구성 세션 `redbox_t1_known` (읽기만, 출력은 임시 폴더) 에서 실행됨. 후자의 형식 비교 결과 `tests/results/qa_format_check_on_redbox_t1_known.md` (features·fps·robot_type·codebase_version·tasks 모두 d2 와 같음). R1/R2 판정 항목은 R1/R2 데이터가 없어 실데이터로 검증되지 않았다.

## 6. 2026-11-02 (3차 지시서) 다시 실행한 결과

| 시험 | 결과 | 확인한 것 |
|---|---|---|
| `tests/test_units.py` | PASS 65/65 | R1 셀 4×4 · 셀마다 좌우 2/2 · 명목 오차 15–30° · 25–30° 는 안 보임 셀만 · 줄어든 오차 0 · K 왼쪽/가운데/오른쪽 · Pan −109°/+96° BLOCK, +90° 통과 · 시작 자세·가시성 분류 · R1/R2 판 메타데이터 (측정 Pan 오차 = 시작 pan − 기준 − 보정, 신뢰도, 안전 확인, 재정렬, 첫 닫힘 결과, episode_id) · 48편 진행률 |
| `tests/test_errors.py` | PASS 6/6 | 장치 없음 · 계획 없음 · 옵션 거부 · 연결 실패 처리 |
| `tests/test_preview_flow.py` (R2) | PASS 13 | 준비 → 녹화 → 결과 · 버리기 → 다시 · 영상 창 키 · 기록 파일 · dataset 없음 · ~/so101_runs/main_k8 변화 없음 |
| `tests/test_preview_r1.py` (R1, 새로) | PASS 8 | → 한 번으로는 녹화 안 함, 두 번째 → 로 녹화 (준비·결과 단계 모두) · p 이전 판 다시 보기 (축소 영상 파일·ui.replay) · 결과 4 · r12_episodes.csv R1 메타데이터 · dataset 없음 · Traceback 없음 · ~/so101_runs/main_k8 변화 없음 |
| `tests/test_entry_stub.py` (실제 lerobot record() + 가짜 장치) | PASS 13/13 | features·fps·robot_type·codebase_version·과제 문장 d2 와 같음 · 준비 단계 미녹화 · action = 리더 값 · NaN BLOCK · 다시 보기 파일 (`last_episode.npy` 3장, 29.97 Hz) |
| `r12_collect.py check` | 문제 없음 | lerobot 0.6.2 record_loop 인자·record() 구조 |
| QA 저장 무결성 (새 항목) | 실데이터 `practice/r1_trial` 3편 (출력은 임시 폴더) | 판 번호 연속·중복 없음 · total_episodes · 판 길이 = 데이터 줄 수 · 전역 index 연속 · frame_index 연속 · 영상 파일 · 영상 구간 프레임 수 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 — 모두 이상 없음 |

결과 원문: `tests/results/test_*.txt`, `check.txt`, `menu.txt`. d2 확인: `main_k8/d2/dataset`, `main_k8/d2/train`, `redbox_t1_known/dataset`, `redbox_t3_known/dataset` 에 2026-10-30 이후 바뀐 파일 0개.

### 스크린샷 (13:44, Preview 실제 실행, §4 와 같은 방법)

| 파일 | 크기 | 화면 |
|---|---|---|
| `~/Desktop/SO101_R1_R2_Collection_UI.png` | 2074×1038 | R1 · ep0 결과 입력 (4 = 재정렬 O·파지 실패 + 메모), 다음 판 R1-HOME-OUT 안내, 48편 진행률, 조작 키 |
| `~/Desktop/SO101_R1_R2_Collection_UI_R1.png` | 2074×1038 | R1-MID-VIS · ep0 준비 단계에서 첫 → 뒤 '안전 확인' 문구, 주황 선(시작 Pan)·하늘색 로봇 선·초록 큐브 선 |
| `~/Desktop/SO101_R1_R2_Collection_UI_R2.png` | 2074×1038 | R2-DEPTH · ep0 준비 단계 (손목 화면 주황 시작 영역) |
| `~/Desktop/SO101_R1_R2_Collection_UI_Recording.png` | 2074×1038 | R1 · ep0 녹화 중 4 s |
| `screenshots/SO101_R1_R2_Collection_UI_R1_review.png` | 2074×1038 | R1 · p 이전 판 다시 보기 (축소 영상) |

영상·관절값은 기존 녹화 재생이라 화면의 Pan·큐브 위치는 계획과 맞지 않는다 (예: Pan 지금 −1.7° → 목표 +54.5°, 각도 못 잼). 5장 모두 `Read` 로 열어 글자를 확인했다.

### 시험하지 않은 것 (추가)
- 실물에서 R1 시작 자세 (특히 mid_approach 에서 25° Pan) 의 충돌·케이블 여유, 손목 가시성 목표가 그 자세에서 실제로 만들어지는지.
- 시작 자세 분류 기준 (lift ≤ −80 & elbow ≥ 70) 이 실제 '접근 중간' 자세들과 맞는지 — 기준값은 쉬는 자세 값에서 정한 대략값.
- 45 s 판 끝 다시 보기 저장 (약 15 MB) 이 실물 저장 직전에 주는 지연.

## 7. 2026-11-02 (4차) 다시 실행한 결과

| 시험 | 결과 | 확인한 것 |
|---|---|---|
| `tests/test_units.py` | PASS 74/74 | R1 = A·B1·B2·B3 각 4 · 시나리오마다 좌우 2/2 · 단계 기대값 · B3 손목 안 보임 · K 8 + 자유 점 8 · 자유 점/검출 자리 Pan 기준·출처 · 접근 단계 분류 · 시나리오 조건은 경고 목록 (안전 검사와 별개) · s/d/k (set_scenario·refresh_row, \|pan\| 92 로 줄임) · 복구 측정 (준비 때 멀어짐→녹화 반전, 준비 때 이미 반전 = 음수 시각, 파지 시작 뒤 제외, 지나침 뒤 되돌아옴) · 손목 재획득 · 리더−팔로워 30° = BLOCK · R1/R2 판 메타데이터 |
| `tests/test_errors.py` | PASS 6/6 | |
| `tests/test_preview_flow.py` (R2) | PASS 13 | 결과 단계 → = 저장 → 준비 단계 → → = 녹화 (새 흐름) 포함 |
| `tests/test_preview_r1.py` (R1) | PASS 11 | A·B1·B2·B3 를 한 판씩 녹화 시작 → 저장 · → 한 번은 녹화 안 함 · 결과 단계 → 뒤 바로 녹화 안 함 · s×4 (수량 그대로) · d · k · x (front 검출) · p · 결과 4·1·3·2 · 판마다 recovery 사건 · r12_episodes.csv R1 열 · dataset 없음 · ~/so101_runs 변화 없음 |
| `tests/test_entry_stub.py` (실제 lerobot record() + 가짜 장치) | PASS 19/19 | NaN·\|pan\| 96° BLOCK · 결과 단계 → = reset_end → 준비 (녹화 안 함) · 저장 중 리더 30° 이동 → 준비 시작 알림 + 녹화 시작 BLOCK (diff_shoulder_pan) · 팔 편 접근 자세 + Pan −20° 는 통과 · ep1 첫 프레임 리더−팔로워 0 · armed 에 준비 단계 pan 열 · 판 끝 pan·그리퍼 열 = 프레임 수 · features·fps·robot_type·codebase_version·과제 문장 d2 와 같음 |
| `check` | 문제 없음 | |

d2 dataset·train, redbox_t1/t3_known dataset: 2026-10-30 이후 바뀐 파일 0개.

### 스크린샷 (14:18, Preview 실제 실행)
| 파일 | 화면 |
|---|---|
| `~/Desktop/SO101_R1_R2_Collection_UI_R1B.png` | R1-B2 준비 단계 (F4, 지나친 Pan 주황 선, 안전 조건 ✓ / 시나리오 조건 ◇ 나눠 표시) |
| `~/Desktop/SO101_R1_R2_Collection_UI_R1A.png` | R1-A 준비 단계 (K8, 저장 뒤 준비 단계로 온 화면, 최근 저장 2편) |
| `~/Desktop/SO101_R1_R2_Collection_UI_R1.png` | R1-A 준비 단계에서 첫 → 뒤 안전 확인 문구 |
| `~/Desktop/SO101_R1_R2_Collection_UI_Recording.png` | R1-B2 녹화 중 (되돌리는 동작 안내) |
| `~/Desktop/SO101_R1_R2_Collection_UI.png` | R1 결과 단계 (결과 4 + 메모, R1 복구 측정 줄, 다음 판 R1-B1 안내, 48편 진행률) |
| `~/Desktop/SO101_R1_R2_Collection_UI_R2.png` | R2-DEPTH 준비 단계 |

영상·관절값은 d2 구성 세션 재생이라 화면의 Pan·큐브 위치·복구 측정 값은 계획과 무관하다. 6장 모두 열어 확인했다.

### 시험하지 않은 것 (추가)
- 실물에서 B 시나리오 시작 자세 (팔 편 상태 + Pan 15–25°) 의 탁자·상자 여유. 지금 안전 조건은 관절값만 보며 충돌을 직접 재지 않는다 — 사람의 안전 확인 (→ 두 번) 이 그 몫.
- 자유 점 F1–F4 에서 front 검출·각도 측정이 K 와 같은 정확도인지.
- 접근 단계 진행률 기준이 실제 B 시작 자세들과 맞는지.
