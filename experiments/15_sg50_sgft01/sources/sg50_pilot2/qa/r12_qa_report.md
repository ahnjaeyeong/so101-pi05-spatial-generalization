# R1/R2 품질 검사 — practice/sg50_pilot2

- 만든 시각: 2026-11-06 10:28 · dataset `~/so101_runs/practice/sg50_pilot2/dataset` (읽기만)
- 계획 `r12_plan.csv` 4줄 (유효 4) · 저장 4편 · 제외 표시 0편
- 문제 없음 0/4 (제외 판 빼고)

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
| dataset 판 번호 | 4개 · 0..3 연속, 중복 없음 |
| info.json total_episodes | 4 |
| 판 길이 = 데이터 줄 수 | 모두 같음 |
| 전역 index | 0..3565 연속 |
| 판 안 frame_index | 모두 0..길이−1 연속 |
| 영상 파일 (front·wrist) | 모두 있음 |
| 영상 구간 프레임 수 = 판 길이 | 모두 같음 (±1) |
| r12_episodes.csv episode_id | 4개 · 중복 없음 |
| 녹화 중 센 프레임 = 저장 줄 수 | 모두 같음 |

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| SG-S0 | 4 | 4 |

| K | 편수 |
|---|---:|
| K2 | 1 |
| K5 | 1 |
| K7 | 1 |
| K8 | 1 |

| 각도 | 편수 |
|---|---:|
| 0° | 4 |

| 어긋남 방향 | 편수 |
|---|---:|
|  | 4 |

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| SG-S0 | 1 | -0.18 | -0.18 | -0.18 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 | SG-S0 | K2 | 21.5 | 13.77 | — | 영역 안 @ 13.4s | 1.5 | 0.0 | 안 보임 | 0.66 |  |  |  | camera_stall_ticks 32 |
| 1 | SG-S0 | K7 | 35.1 | 31.83 | — | 더 진입 · 영역 왼쪽 @ 31.7s | 1.4 | 0.0 | 안 보임 | 0.37 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 왼쪽); camera_stall_ticks 42 |
| 2 | SG-S0 | K8 | 44.8 | 40.77 | — | 영역 오른쪽 @ 40.7s | 1.4 | 0.0 | 안 보임 | 0.1 |  |  |  | 끝 프레임이 쉬는 자세 아님 (lift 16, elbow -8); 닫기 시작 때 손목 큐브가 닫기 영역 밖 (영역 오른쪽); camera_stall_ticks 56 |
| 3 | SG-S0 | K5 | 17.47 | 11.63 | — | 영역 안 @ 11.1s | 1.5 | 0.0 | dx=-0.18 dy=-0.19 area=20168 | 0.38 |  |  |  | camera_stall_ticks 22 |

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
