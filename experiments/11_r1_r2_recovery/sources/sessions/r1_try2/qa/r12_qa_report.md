# R1/R2 품질 검사 — practice/r1_try2

- 만든 시각: 2026-11-02 14:08 · dataset `~/so101_runs/practice/r1_try2/dataset` (읽기만)
- 계획 `r12_plan.csv` 4줄 (유효 4) · 저장 2편 · 제외 표시 0편
- 문제 없음 0/2 (제외 판 빼고)

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
| 전역 index | 0..793 연속 |
| 판 안 frame_index | 모두 0..길이−1 연속 |
| 영상 파일 (front·wrist) | 모두 있음 |
| 영상 구간 프레임 수 = 판 길이 | 모두 같음 (±1) |
| r12_episodes.csv episode_id | 2개 · 중복 없음 |
| 녹화 중 센 프레임 = 저장 줄 수 | 모두 같음 |

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| R1-MID-OUT | 1 | 1 |
| R1-MID-VIS | 1 | 1 |
| R1-HOME-VIS | 0 | 1 |
| R1-HOME-OUT | 0 | 1 |

| K | 편수 |
|---|---:|
| K4 | 1 |
| K6 | 1 |

| 각도 | 편수 |
|---|---:|
| ↺30° | 1 |
| ↻30° | 1 |

| 어긋남 방향 | 편수 |
|---|---:|
| robot_left | 1 |
| robot_right | 1 |

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| R1-MID-OUT | 1 | +0.09 | +0.09 | +0.09 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 | R1-MID-OUT | K6 | 16.03 | 13.53 | 접근 초반 (0.0) · Pan +68.7° = 기준 +44.6° +24.1° (계획 right 25°) · 손목 가장자리 · front visible / 준비 때 unknown · 녹화 첫 이동 toward -37.2° · 반전 @+12.93s (-40.5° → +12.0°) · 손목 처음부터 보임 · 닫기 시작 Pan 오차 -41.6° | 더 진입 · 영역 오른쪽 @ 13.3s | 3.0 | 0.0 | dx=+0.09 dy=+0.87 area=5702 edge | 0.35 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 첫 화면 큐브 각도 범위 밖 (각도 지금 ↺36° → 목표 ↻30° (↻15°…↻38° 안으로)); 시나리오 조건: 첫 화면 손목 큐브 가장자리 (계획 안 보임); 결과 미입력; camera_stall_ticks 23 |
| 1 | R1-MID-VIS | K4 | 10.43 |  | 접근 초반 (0.0) · Pan -60.7° = 기준 -46.2° -14.5° (계획 left 15°) · 손목 안 보임 · front offset / 준비 때 unknown · 녹화 첫 이동 toward +26.4° · 반전 @+2.83s (+51.3° → -67.3°) · 손목 못 찾음 |  | 1.2 | 0.0 | 안 보임 | 23.11 |  |  |  | 첫 프레임 시작 자세 검사 BLOCK: pan 리더−팔로워 34° > 25° — 팔로워가 막혀 밀고 있거나 아직 움직이는 중 (팔을 멈추고 다시 →); 그리퍼 닫힘(명령 >15 → <10) 없음; 시나리오 조건: 첫 화면 손목 큐브 안 보임 (계획 보임/가장자리); 손목 화면에서 큐브를 다시 찾지 못함 (10 프레임마다 검사); front 큐브 ↔ 계획 K4 23.1 cm; 결과 미입력; camera_stall_ticks 17 |

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
