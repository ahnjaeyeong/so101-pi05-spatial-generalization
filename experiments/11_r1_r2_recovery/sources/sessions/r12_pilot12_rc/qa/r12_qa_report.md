# R1/R2 품질 검사 — main_k8/r12_pilot12_rc

- 만든 시각: 2026-11-04 14:39 · dataset `~/so101_runs/main_k8/r12_pilot12_rc/dataset` (읽기만)
- 계획 `r12_plan.csv` 13줄 (유효 12) · 저장 13편 · 제외 표시 1편
- 문제 없음 0/12 (제외 판 빼고)

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
| dataset 판 번호 | 13개 · 0..12 연속, 중복 없음 |
| info.json total_episodes | 13 |
| 판 길이 = 데이터 줄 수 | 모두 같음 |
| 전역 index | 0..4627 연속 |
| 판 안 frame_index | 모두 0..길이−1 연속 |
| 영상 파일 (front·wrist) | 모두 있음 |
| 영상 구간 프레임 수 = 판 길이 | 모두 같음 (±1) |
| r12_episodes.csv episode_id | 13개 · 중복 없음 |
| 녹화 중 센 프레임 = 저장 줄 수 | 모두 같음 |

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| RC-F2 | 4 | 4 |
| RC-F1 | 4 | 4 |
| RC-F3-L | 2 | 2 |
| RC-F3-R | 2 | 2 |

| K | 편수 |
|---|---:|
| K1 | 2 |
| K2 | 1 |
| K3 | 2 |
| K4 | 1 |
| K5 | 2 |
| K6 | 1 |
| K7 | 2 |
| K8 | 1 |

| 각도 | 편수 |
|---|---:|
| 0° | 3 |
| 45° | 3 |
| ↺30° | 3 |
| ↻30° | 3 |

| 어긋남 방향 | 편수 |
|---|---:|
| forward | 4 |
| none | 4 |
| robot_left | 2 |
| robot_right | 2 |

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| RC-F2 | 4 | +0.05 | -0.09 | +0.13 |
| RC-F1 | 4 | -0.27 | -0.34 | -0.17 |
| RC-F3-L | 2 | +0.09 | +0.07 | +0.12 |
| RC-F3-R | 2 | +0.06 | +0.04 | +0.07 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 | RC-F2 | K7 | 12.07 | 6.47 | — | 영역 안 @ 6.1s | 1.1 | 0.0 | dx=+0.04 dy=-0.06 area=20039 | 0.81 |  |  |  | 첫 화면 큐브 각도 범위 밖 (각도 지금 ↺38° → 목표 ↻30° (↻15°…↻38° 안으로)); 결과 미입력; camera_stall_ticks 18 |
| 1 | RC-F1 | K6 | 12.03 | 7.27 | 영역 밖 | 영역 안 @ 6.9s | 27.4 | 0.0 | dx=-0.28 dy=+0.74 area=18208 edge | 0.31 |  |  |  | 첫 화면 손목 큐브가 R2 시작 영역(cube_ahead) 밖/안 보임; 결과 미입력; camera_stall_ticks 10 |
| 2 | RC-F3-L | K5 | 11.43 | 6.87 | 영역 안 | 더 진입 @ 6.4s | 1.1 | 0.0 | dx=+0.12 dy=-0.38 area=20852 | 0.09 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입); 결과 미입력; camera_stall_ticks 10 |
| 3 | RC-F3-R | K1 | 12.43 | 7.7 | 영역 안 | 영역 안 @ 7.4s | 1.1 | 0.0 | dx=+0.07 dy=+0.70 area=5059 |  |  |  |  | 결과 미입력; camera_stall_ticks 14 |
| 4 | RC-F2 | K8 | 15.03 | 7.9 | — | 영역 안 @ 7.7s | 1.0 | 0.0 | dx=+0.10 dy=-0.02 area=14583 | 0.05 | True | True | 0 | camera_stall_ticks 22 |
| 5 | RC-F1 | K3 | 11.27 | 6.23 | 영역 밖 | 영역 안 @ 6.0s | 21.2 | 0.0 | dx=-0.17 dy=+0.72 area=19699 edge | 0.52 | True | True | 0 | 첫 화면 손목 큐브가 R2 시작 영역(cube_ahead) 밖/안 보임; camera_stall_ticks 17 |
| 6 | RC-F1 | K1 | 12.07 | 6.6 | 영역 밖 | 영역 안 @ 6.1s | 29.4 | 0.0 | dx=-0.34 dy=-0.22 area=41927 | 0.63 | True | True | 0 | 첫 화면 손목 큐브가 R2 시작 영역(cube_ahead) 밖/안 보임; camera_stall_ticks 18 |
| 7 | RC-F2 | K5 | 12.23 | 7.57 | — | 영역 안 @ 7.1s | 1.1 | 0.0 | dx=+0.13 dy=-0.03 area=15252 | 0.47 | True | True | 0 | 첫 화면 큐브 각도 범위 밖 (각도 지금 ↻32° → 목표 45° (37.5°…45° (좌우 무관) 안으로)); camera_stall_ticks 14 |
| 8 | RC-F3-R | K3 | 13.27 | 6.43 | 영역 안 | 영역 안 @ 6.2s | 1.1 | 0.0 | dx=+0.04 dy=+0.79 area=7601 edge | 0.52 | True | True | 0 | 첫 화면 큐브 각도 범위 밖 (각도 지금 ↺33° → 목표 45° (37.5°…45° (좌우 무관) 안으로)); camera_stall_ticks 16 |
| 9 | RC-F3-L | K7 | 12.47 | 6.87 | 영역 밖 | 영역 안 @ 6.6s | 1.1 | 0.09 | dx=+0.07 dy=-0.55 area=26447 | 0.33 | True | True | 0 | 첫 화면 손목 큐브가 R2 시작 영역(fingers_left) 밖/안 보임; camera_stall_ticks 12 |
| 10 | RC-F1 | K4 | 11.07 | 8.5 | 영역 밖 | 더 진입 · 영역 오른쪽 @ 8.3s | 28.1 | 0.0 | dx=-0.31 dy=+0.84 area=10779 edge | 1.25 | True | True | 0 | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 첫 화면 손목 큐브가 R2 시작 영역(cube_ahead) 밖/안 보임; camera_stall_ticks 16 |
| 11 (제외) | RC-F2 | K2 | 8.67 | 4.87 | — | 영역 안 @ 4.6s | 1.2 | 0.0 | dx=-0.12 dy=-0.04 area=20909 | 1.64 |  |  |  | 끝 프레임이 쉬는 자세 아님 (lift 19, elbow -41); 결과 미입력; camera_stall_ticks 15 |
| 12 | RC-F2 | K2 | 10.23 | 4.43 | — | 영역 안 @ 4.0s | 0.8 | 0.0 | dx=-0.09 dy=-0.05 area=21854 | 0.85 |  |  |  | 결과 미입력; camera_stall_ticks 10 |

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
| 0 | RC-F2 | review | check | na | na | ok | check | ok | ok | ok |
| 1 | RC-F1 | review | check | na | ok | na | check | check | ok | ok |
| 2 | RC-F3-L | review | ok | na | na | ok | check | ok | ok | ok |
| 3 | RC-F3-R | review | check | na | na | ok | check | check | ok | ok |
| 4 | RC-F2 | review | check | na | na | check | ok | ok | ok | ok |
| 5 | RC-F1 | review | check | na | ok | na | ok | check | ok | ok |
| 6 | RC-F1 | review | check | na | ok | na | ok | check | ok | ok |
| 7 | RC-F2 | review | check | na | na | ok | ok | ok | ok | ok |
| 8 | RC-F3-R | review | ok | na | na | check | ok | check | ok | ok |
| 9 | RC-F3-L | review | check | na | na | ok | ok | ok | ok | ok |
| 10 | RC-F1 | review | check | na | ok | na | ok | check | ok | ok |
| 11 (제외) | RC-F2 | exclude | check | na | na | check | check | check | ok | ok |
| 12 | RC-F2 | review | check | na | na | check | check | ok | ok | ok |

### 판별 값

- ep0 RC-F2
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.22–0.5 · v 0.55–0.9, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 ok: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 3.73s · 닫기 전 최대 32.4 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 0.2° (≤ 5 = 먼저 엶)
  - Q5 check: 첫 닫힘 6.10s 팔로워 바닥 11.6 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.91 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep1 RC-F1
  - Q1 check: 2/3: ✓ 그리퍼 열림 ≥ 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.2–0.5 · v 0.5–0.85, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 27 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 27.2
  - Q5 check: 첫 닫힘 6.87s 팔로워 바닥 12.4 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 4.36 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep2 RC-F3-L
  - Q1 ok: 3/3: ✓ 그리퍼 닫힘 < 15 · ✓ 손목 큐브가 시작 영역 안 (u 0.1–0.65 · v 0.3–0.66, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 ok: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 4.47s · 닫기 전 최대 37.8 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 2.5° (≤ 5 = 먼저 엶)
  - Q5 check: 첫 닫힘 6.37s 팔로워 바닥 12.2 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.13 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep3 RC-F3-R
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✓ 손목 큐브가 시작 영역 안 (u 0.15–0.7 · v 0.72–1.0, 대략) · ✗ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 ok: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 4.03s · 닫기 전 최대 29.0 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 2.0° (≤ 5 = 먼저 엶)
  - Q5 check: 첫 닫힘 7.43s 팔로워 바닥 12.2 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 2.91 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep4 RC-F2
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.22–0.5 · v 0.55–0.9, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 check: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 4.23s · 닫기 전 최대 33.8 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 7.8° (≤ 5 = 먼저 엶)
  - Q5 ok: 첫 닫힘 6.80s 팔로워 바닥 12.9 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.55 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep5 RC-F1
  - Q1 check: 2/3: ✓ 그리퍼 열림 ≥ 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.2–0.5 · v 0.5–0.85, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 21 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 21.2
  - Q5 ok: 첫 닫힘 6.03s 팔로워 바닥 11.5 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 3.56 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep6 RC-F1
  - Q1 check: 2/3: ✓ 그리퍼 열림 ≥ 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.2–0.5 · v 0.5–0.85, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 29 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 29.6
  - Q5 ok: 첫 닫힘 6.10s 팔로워 바닥 12.4 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 3.95 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep7 RC-F2
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.22–0.5 · v 0.55–0.9, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 ok: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 2.23s · 닫기 전 최대 42.2 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 0.0° (≤ 5 = 먼저 엶)
  - Q5 ok: 첫 닫힘 7.17s 팔로워 바닥 11.9 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.76 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep8 RC-F3-R
  - Q1 ok: 3/3: ✓ 그리퍼 닫힘 < 15 · ✓ 손목 큐브가 시작 영역 안 (u 0.15–0.7 · v 0.72–1.0, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 check: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 3.67s · 닫기 전 최대 23.6 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 17.0° (≤ 5 = 먼저 엶)
  - Q5 ok: 첫 닫힘 6.23s 팔로워 바닥 11.5 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 3.02 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep9 RC-F3-L
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.1–0.65 · v 0.3–0.66, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 ok: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 4.20s · 닫기 전 최대 31.9 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 3.2° (≤ 5 = 먼저 엶)
  - Q5 ok: 첫 닫힘 6.57s 팔로워 바닥 12.6 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.72 · Pan 방향 바뀜 2번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep10 RC-F1
  - Q1 check: 2/3: ✓ 그리퍼 열림 ≥ 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.2–0.5 · v 0.5–0.85, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 28 (open, 조건 open)
  - Q3 ok: 닫기 전 리더 그리퍼 ≥ 15 비율 1.00 · 최소 28.4
  - Q5 ok: 첫 닫힘 5.83s 팔로워 바닥 13.2 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 3.22 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep11 RC-F2
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.22–0.5 · v 0.55–0.9, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 check: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 1.37s · 닫기 전 최대 24.7 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 4.1° (≤ 5 = 먼저 엶)
  - Q5 check: 첫 닫힘 4.63s 팔로워 바닥 11.3 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 2.82 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖
- ep12 RC-F2
  - Q1 check: 2/3: ✓ 그리퍼 닫힘 < 15 · ✗ 손목 큐브가 시작 영역 안 (u 0.22–0.5 · v 0.55–0.9, 대략) · ✓ front 큐브 보임 · 시작 그리퍼 1 (closed, 조건 closed)
  - Q4 check: 시작 리더 그리퍼 1 · 처음 ≥ 15 @ 2.47s · 닫기 전 최대 37.9 (목표 ≥ 25) · 열기 전 Lift/Elbow 이동 6.1° (≤ 5 = 먼저 엶)
  - Q5 check: 첫 닫힘 4.07s 팔로워 바닥 12.2 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.26 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_rc/dataset · repo_id oxr/so101_k8_r12_pilot12_rc · d2 dataset 밖

규칙 (config pilot_qa · pilot_reference): {"pan_correction_min_deg": 5, "gripper_open_min": 15, "close_drop_min": 8, "pan_reversals_max": 2, "path_ratio_max": 2.5, "time_align_tol_s": 0.002, "reference": null}
