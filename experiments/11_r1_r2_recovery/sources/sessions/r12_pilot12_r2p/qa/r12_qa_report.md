# R1/R2 품질 검사 — main_k8/r12_pilot12_r2p

- 만든 시각: 2026-11-03 16:36 · dataset `~/so101_runs/main_k8/r12_pilot12_r2p/dataset` (읽기만)
- 계획 `r12_plan.csv` 6줄 (유효 4) · 저장 2편 · 제외 표시 2편
- 문제 없음 0/0 (제외 판 빼고)

## 1. d2 와 형식 비교

| 항목 | 결과 |
|---|---|
| features.action | 같음 |
| features.observation.state | 같음 |
| features.observation.images.front | 같음 |
| features.observation.images.wrist | 같음 |
| features.timestamp | 같음 |
| features.frame_index | 같음 |
| features.episode_index | 같음 |
| features.index | 같음 |
| features.task_index | 같음 |
| features 이름 집합 | 같음 |
| fps | 30 (d2 30) 같음 |
| robot_type | so_follower (d2 so_follower) 같음 |
| codebase_version | v3.0 (d2 v3.0) 같음 |
| tasks | ['pick up the red cube and put it in the brown box'] = d2 |

### 저장 무결성

| 항목 | 결과 |
|---|---|
| dataset 판 번호 | 2개 · 0..1 연속, 중복 없음 |
| info.json total_episodes | 2 |
| 판 길이 = 데이터 줄 수 | 모두 같음 |
| 전역 index | 0..980 연속 |
| 판 안 frame_index | 모두 0..길이−1 연속 |
| 영상 파일 (front·wrist) | 모두 있음 |
| 영상 구간 프레임 수 = 판 길이 | 모두 같음 (±1) |
| r12_episodes.csv episode_id | 2개 · 중복 없음 |
| 녹화 중 센 프레임 = 저장 줄 수 | 모두 같음 |

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| R2-P-AHEAD | 0 | 2 |
| R2-P-DEPTH | 0 | 2 |

| K | 편수 |
|---|---:|

| 각도 | 편수 |
|---|---:|

| 어긋남 방향 | 편수 |
|---|---:|

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 (제외) | R2-P-AHEAD | K3 | 19.23 | 6.83 | 영역 안 | 큐브가 손목 화면 경계에서 잘림 (위치 판정 불확실) @ 6.5s | 25.6 | 0.0 | dx=-0.15 dy=-0.06 area=17009 | 0.38 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (큐브가 손목 화면 경계에서 잘림 (위치 판정 불확실)); 결과 미입력; camera_stall_ticks 27 |
| 1 (제외) | R2-P-DEPTH | K4 | 13.47 | 2.8 | 영역 안 | 더 진입 · 영역 왼쪽 @ 2.7s | 26.7 | 0.0 | dx=-0.25 dy=-0.03 area=14700 | 0.78 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 왼쪽); 결과 미입력; camera_stall_ticks 14 |

## 4. 판정 규칙

- `len_min_s` = 3.0
- `jump_deg` = 20.0
- `dt_tol_s` = 0.001
- `start_shift_deg` = 5.0
- `front_dist_cm` = 2.5
- `end_lift_max` = -90.0
- `end_elbow_min` = 85.0
- `grip_open` = 15.0
- `grip_closed` = 10.0
- 닫기 영역 = config/r12_wrist_zone.json close_zone (d2 256편 닫기 시작 순간 손목 큐브 중심, 주 덩어리 p10–p90 · 넓이 최소). 닫기 시작 = 명령 그리퍼가 열린 뒤 처음 <10 이 되기 전 계속 줄어들기 시작한 프레임.
- 시작 자세 검사 = r12_common.safety_check (설정 safety 절; 관절 캘리브레이션 한계, |pan|, 그리퍼 열림, 리더−팔로워 차이). FK·TCP 위치는 쓰지 않음.
- 큐브 검출 = redbox8_layouts.yaml detection.colors.red HSV. front 좌표 = 같은 설정의 H (큐브 중심 평면). 물리적 접근 깊이는 측정하지 않음.

## 5. 파일럿 12편 QA (작업 지시 §9) — dataset 으로 다시 잼

판정: ok = 규칙 통과 · check = 사람이 영상으로 확인 · na = 해당 없음. 'candidate_needs_review' 도 학습 적합 확정이 아님 (사람 검토 필요).

- Q1 시작 상태가 의도한 실패 상태와 비슷한가 (근사)
- Q2 R1: 필요한 방향으로 Pan 수정이 기록됐나
- Q3 R2-P: 그리퍼를 연 채 접근했나 (닫기 전까지 열림)
- Q4 R2-O: 그리퍼를 충분히 다시 열었나 (먼저 열고 접근)
- Q5 정렬 뒤 한 번의 닫힘으로 파지했나
- Q6 불필요한 동작 (Pan 왕복 · 경로 길이)
- Q7 영상 · state · action 시간 일치
- Q8 d2 와 독립 보존

| ep | 시나리오 | 적합 분류 | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 0 (제외) | R2-P-AHEAD | exclude | ok | na | ok | na | check | ok | ok | ok |
| 1 (제외) | R2-P-DEPTH | exclude | ok | na | ok | na | check | ok | ok | ok |

### 판별 값

- ep0 R2-P-AHEAD
  - Q1 ok: 3/3: ✓ 그리퍼 열림 ≥ 15 · ✓ 손목 큐브 v 0.25–0.633 (실패 AHEAD 닫는 순간 v 0.39–0.61) · ✓ front 큐브 보임 (실패 AHEAD: 가림 없음) · 시작 그리퍼 26 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 25.8
  - Q5 check: 첫 닫힘 6.50s 팔로워 바닥 3.5 · 첫 닫힘 빈 파지 의심 @ 6.5s (팔로워 그리퍼 바닥 3.5 ≤ 5) · 파지 전에 실패한 닫힘 1번 · 첫 파지 입력 미입력 · 첫 닫힘 때 큐브가 손목 화면 경계에서 잘림
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.20 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r2p/dataset · repo_id oxr/so101_k8_r12_pilot12_r2p · d2 dataset 밖
- ep1 R2-P-DEPTH
  - Q1 ok: 3/3: ✓ 그리퍼 열림 ≥ 15 · ✓ 손목 큐브 v 0.25–0.633 (실패 AHEAD 닫는 순간 v 0.39–0.61) · ✓ front 큐브 보임 (실패 AHEAD: 가림 없음) · 시작 그리퍼 27 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 26.2
  - Q5 check: 첫 닫힘 2.67s 팔로워 바닥 1.1 · 첫 닫힘 빈 파지 의심 @ 2.7s (팔로워 그리퍼 바닥 1.1 ≤ 5) · 파지 전에 실패한 닫힘 1번 · 첫 파지 입력 미입력
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.37 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r2p/dataset · repo_id oxr/so101_k8_r12_pilot12_r2p · d2 dataset 밖

규칙 (config pilot_qa · pilot_reference): {"pan_correction_min_deg": 5, "gripper_open_min": 15, "close_drop_min": 8, "pan_reversals_max": 2, "path_ratio_max": 2.5, "time_align_tol_s": 0.002, "reference": {"R1": {"lift_max": -85, "over_min_deg": 10}, "R2-O": {"wrist_v": [0.25, 0.633]}, "R2-P": {"wrist_v": [0.25, 0.633]}}}
