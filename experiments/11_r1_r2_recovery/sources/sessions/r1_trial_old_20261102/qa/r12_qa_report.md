# R1/R2 품질 검사 — practice/r1_trial

- 만든 시각: 2026-11-02 10:43 · dataset `~/so101_runs/practice/r1_trial/dataset` (읽기만)
- 계획 `r12_plan.csv` 3줄 (유효 3) · 저장 3편 · 제외 표시 0편
- 문제 없음 0/3 (제외 판 빼고)

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

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| R1-L | 1 | 1 |
| R1-R | 1 | 1 |
| R1-OL | 1 | 1 |

| K | 편수 |
|---|---:|
| K3 | 1 |
| K7 | 1 |
| K8 | 1 |

| 각도 | 편수 |
|---|---:|
| 0° | 1 |
| ↺30° | 1 |
| ↻30° | 1 |

| 어긋남 방향 | 편수 |
|---|---:|
| robot_left | 2 |
| robot_right | 1 |

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| R1-L | 1 | +0.54 | +0.54 | +0.54 |
| R1-R | 1 | -0.23 | -0.23 | -0.23 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---:|---:|---|---:|---|---|---:|---|
| 0 | R1-L | K7 | 23.63 | 14.93 | 영역 안 @ 14.1s | 1.1 | 0.0 | dx=+0.54 dy=-0.69 area=23918 edge | 0.71 |  |  |  | 결과 미입력; camera_stall_ticks 29 |
| 1 | R1-R | K8 | 15.43 | 10.97 | 더 진입 · 영역 오른쪽 @ 10.8s | 0.8 | 0.0 | dx=-0.23 dy=+0.06 area=20103 | 0.48 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 결과 미입력; camera_stall_ticks 17 |
| 2 | R1-OL | K3 | 21.43 | 9.77 | 영역 안 @ 9.4s | 1.1 | 0.0 | 안 보임 | 0.63 |  |  |  | 결과 미입력; camera_stall_ticks 31 |

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
