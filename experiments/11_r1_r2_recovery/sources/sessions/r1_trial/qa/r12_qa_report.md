# R1/R2 품질 검사 — practice/r1_trial

- 만든 시각: 2026-11-02 11:17 · dataset `~/so101_runs/practice/r1_trial/dataset` (읽기만)
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
| R1-UNDER | 1 | 1 |
| R1-OVER | 1 | 1 |
| R1-TL | 1 | 1 |

| K | 편수 |
|---|---:|
| K2 | 1 |
| K3 | 1 |
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
| R1-TL | 1 | -0.82 | -0.82 | -0.82 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 재정렬 표시 | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 | R1-UNDER | K3 | 19.4 | 10.67 | Space 없음 | 더 진입 @ 10.3s | 3.2 | 0.0 | 안 보임 | 0.77 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입); 재정렬 표시(Space) 없음 — 어긋남 구간을 나중에 자를 수 없음; 첫 화면 큐브 각도 범위 밖 (각도 지금 ↻35° → 목표 ↺30° (↺15°…↺38° 안으로)); 결과 미입력; camera_stall_ticks 30 |
| 1 | R1-OVER | K8 | 21.03 | 17.3 | Space 없음 | 더 진입 · 영역 오른쪽 @ 17.1s | 1.1 | 0.0 | 안 보임 | 0.35 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 재정렬 표시(Space) 없음 — 어긋남 구간을 나중에 자를 수 없음; 결과 미입력; camera_stall_ticks 25 |
| 2 | R1-TL | K2 | 18.83 | 10.63 | Space 없음 | 영역 안 @ 10.4s | 1.1 | 0.0 | dx=-0.82 dy=-0.34 area=12606 edge | 0.28 |  |  |  | 재정렬 표시(Space) 없음 — 어긋남 구간을 나중에 자를 수 없음; 결과 미입력; camera_stall_ticks 28 |

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
