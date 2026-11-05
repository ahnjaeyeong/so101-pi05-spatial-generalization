# R1/R2 품질 검사 — main_k8/r12_pilot12_r1

- 만든 시각: 2026-11-04 14:39 · dataset `~/so101_runs/main_k8/r12_pilot12_r1/dataset` (읽기만)
- 계획 `r12_plan.csv` 8줄 (유효 4) · 저장 8편 · 제외 표시 4편
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
| dataset 판 번호 | 8개 · 0..7 연속, 중복 없음 |
| info.json total_episodes | 8 |
| 판 길이 = 데이터 줄 수 | 모두 같음 |
| 전역 index | 0..3824 연속 |
| 판 안 frame_index | 모두 0..길이−1 연속 |
| 영상 파일 (front·wrist) | 모두 있음 |
| 영상 구간 프레임 수 = 판 길이 | 모두 같음 (±1) |
| r12_episodes.csv episode_id | 8개 · 중복 없음 |
| 녹화 중 센 프레임 = 저장 줄 수 | 모두 같음 |

## 2. 수량

| 시나리오 | 저장 | 계획 |
|---|---:|---:|
| R1-FOLD-OVER | 4 | 4 |

| K | 편수 |
|---|---:|
| K1 | 1 |
| K3 | 1 |
| K4 | 1 |
| K6 | 1 |

| 각도 | 편수 |
|---|---:|
| 0° | 1 |
| 45° | 1 |
| ↺30° | 1 |
| ↻30° | 1 |

| 어긋남 방향 | 편수 |
|---|---:|
| robot_left | 2 |
| robot_right | 2 |

손목 카메라 첫 화면 큐브 중심 dx (화면 가로, −1 왼쪽 … +1 오른쪽):

| 시나리오 | n | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| R1-FOLD-OVER | 3 | -0.43 | -0.86 | +0.10 |

## 3. 판별

| ep | 시나리오 | K | 길이 s | 처음 닫힘 s | 시작 조건 (R1 자세·Pan 오차·가시성 · R2 손목 시작 영역) | 닫기 시작 때 손목 큐브 | 시작 그리퍼 | 시작 이동° | 손목 첫 화면 | front↔계획 cm | 첫 파지 | 최종 | 재시도 | 문제 |
|---:|---|---|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---|
| 0 (제외) | R1-FOLD-OVER | K4 | 16.47 | 13.17 | 접근 초반 (-0.0) · Pan -1.5° = 기준 -46.2° +44.7° (계획 left 20°) · 손목 안 보임 · front visible / 준비 때 toward -0.0° · 녹화 첫 이동 toward -62.3° · 반전 toward→toward @+2.60s (-62.3° → +16.8°) · 손목 다시 찾음 @1.3s · 파지 시작 9.97s Pan 오차 -5.0° | 큐브 안 보임 @ 13.0s | 1.1 | 0.0 | 안 보임 | 0.17 | True | True | 0 | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (큐브 안 보임); 시나리오 조건: 첫 화면 손목 큐브 안 보임 (계획 None); camera_stall_ticks 24 |
| 1 (제외) | R1-FOLD-OVER | K6 | 15.67 | 9.93 | 접근 초반 (-0.0) · Pan -3.5° = 기준 +44.6° -48.1° (계획 right 25°) · 손목 안 보임 · front visible / 준비 때 toward +0.0° · 녹화 첫 이동 toward +73.6° · 반전 toward→toward @+3.77s (+73.6° → -28.9°) · 손목 다시 찾음 @1.7s · 파지 시작 9.8s Pan 오차 -1.3° | 영역 안 @ 9.6s | 2.1 | 0.0 | 안 보임 | 0.13 | True | True | 0 | 시나리오 조건: 첫 화면 손목 큐브 안 보임 (계획 None); camera_stall_ticks 21 |
| 2 (제외) | R1-FOLD-OVER | K1 | 17.47 | 11.93 | 접근 초반 (-0.0) · Pan -4.2° = 기준 -33.5° +29.3° (계획 left 20°) · 손목 가장자리 · front visible / 준비 때 away +0.0° · 녹화 첫 이동 away -61.3° · 반전 away→toward @+2.37s (-61.3° → +29.5°) · 손목 처음부터 보임 · 파지 시작 11.87s Pan 오차 -4.1° | 영역 안 @ 11.7s | 1.1 | 0.0 | dx=-0.73 dy=+0.94 area=1711 edge | 0.23 | True | True | 0 | 시나리오 조건: 첫 화면 손목 큐브 가장자리 (계획 None); 녹화 첫 Pan 이동이 큐브에서 멀어짐 (-61.3°) — 틀린 방향 이동이 녹화됨?; camera_stall_ticks 14 |
| 3 (제외) | R1-FOLD-OVER | K3 | 19.23 | 13.13 | 접근 초반 (-0.0) · Pan -4.0° = 기준 +31.2° -35.2° (계획 right 25°) · 손목 안 보임 · front visible / 준비 때 toward -0.0° · 녹화 첫 이동 toward +60.4° · 반전 toward→toward @+2.17s (+60.4° → -30.7°) · 손목 다시 찾음 @1.3s · 파지 시작 12.83s Pan 오차 -5.0° | 영역 안 @ 12.7s | 1.2 | 0.0 | 안 보임 | 0.74 | True | True | 0 | 시나리오 조건: 첫 화면 손목 큐브 안 보임 (계획 None); camera_stall_ticks 25 |
| 4 | R1-FOLD-OVER | K4 | 14.27 | 11.53 | 접근 초반 (-0.0) · Pan -65.5° = 기준 -46.2° -19.3° (계획 left 20°) · 손목 가장자리 · front visible / 준비 때 away -8.1° · 녹화 첫 이동 toward +22.7° · 반전 toward→away @-2.67s (+6.2° → -9.1°) · 손목 처음부터 보임 · 파지 시작 8.97s Pan 오차 -3.9° | 더 진입 · 영역 오른쪽 @ 11.3s | 1.1 | 0.0 | dx=-0.86 dy=-0.98 area=516 edge | 0.33 | True | True | 0 | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 첫 화면 큐브 각도 범위 밖 (각도 지금 ↻14° → 목표 ↻30° (↻15°…↻38° 안으로)); 시나리오 조건: 첫 화면 손목 큐브 가장자리 (계획 None); camera_stall_ticks 22 |
| 5 | R1-FOLD-OVER | K6 | 12.87 | 9.43 | 접근 초반 (0.0) · Pan +67.7° = 기준 +44.6° +23.1° (계획 right 25°) · 손목 가장자리 · front visible / 준비 때 toward +0.0° · 녹화 첫 이동 toward -28.1° · 반전 없음 · 손목 처음부터 보임 · 파지 시작 7.0s Pan 오차 -3.5° | 더 진입 · 영역 오른쪽 @ 9.2s | 3.2 | 0.0 | dx=+0.10 dy=+0.90 area=4604 edge | 0.38 |  |  |  | 닫기 시작 때 손목 큐브가 닫기 영역 밖 (더 진입 · 영역 오른쪽); 첫 화면 큐브 각도 범위 밖 (각도 지금 ↺37° → 목표 45° (37.5°…45° (좌우 무관) 안으로)); 시나리오 조건: 첫 화면 손목 큐브 가장자리 (계획 None); 결과 미입력; camera_stall_ticks 18 |
| 6 | R1-FOLD-OVER | K1 | 15.67 | 9.7 | 접근 초반 (0.0) · Pan -53.5° = 기준 -33.5° -20.0° (계획 left 20°) · 손목 안 보임 · front visible / 준비 때 toward -0.0° · 녹화 첫 이동 toward +20.6° · 반전 toward→away @+3.83s (+20.6° → -3.8°) · 손목 다시 찾음 @2.0s · 파지 시작 9.63s Pan 오차 -3.2° | 영역 안 @ 9.5s | 1.9 | 0.0 | 안 보임 | 0.33 | True | True | 0 | 시나리오 조건: 첫 화면 손목 큐브 안 보임 (계획 None); camera_stall_ticks 21 |
| 7 | R1-FOLD-OVER | K3 | 15.87 | 10.2 | 접근 초반 (0.0) · Pan +56.5° = 기준 +31.2° +25.3° (계획 right 25°) · 손목 보임 · front visible / 준비 때 toward -0.0° · 녹화 첫 이동 toward -30.3° · 반전 없음 · 손목 처음부터 보임 · 파지 시작 9.97s Pan 오차 -4.3° | 영역 안 @ 9.8s | 1.1 | 0.0 | dx=-0.54 dy=+0.82 area=498 | 0.44 | True | True | 0 | 시나리오 조건: 첫 화면 손목 큐브 보임 (계획 None); camera_stall_ticks 18 |

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
| 0 (제외) | R1-FOLD-OVER | exclude | check | ok | na | na | ok | ok | ok | ok |
| 1 (제외) | R1-FOLD-OVER | exclude | check | ok | na | na | ok | ok | ok | ok |
| 2 (제외) | R1-FOLD-OVER | exclude | check | ok | na | na | ok | ok | ok | ok |
| 3 (제외) | R1-FOLD-OVER | exclude | check | ok | na | na | ok | check | ok | ok |
| 4 | R1-FOLD-OVER | candidate_needs_review | ok | ok | na | na | ok | ok | ok | ok |
| 5 | R1-FOLD-OVER | review | ok | ok | na | na | check | ok | ok | ok |
| 6 | R1-FOLD-OVER | candidate_needs_review | ok | ok | na | na | ok | ok | ok | ok |
| 7 | R1-FOLD-OVER | review | check | ok | na | na | ok | ok | ok | ok |

### 판별 값

- ep0 R1-FOLD-OVER
  - Q1 check: 3/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✗ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 +44.7° → 필요한 방향 왼쪽(−) · 첫 Pan 이동 toward · 최대 수정 62.3° · 닫기 시작 때 기준 대비 -5.0°
  - Q5 ok: 첫 닫힘 9.80s 팔로워 바닥 14.1 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.21 · Pan 방향 바뀜 2번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep1 R1-FOLD-OVER
  - Q1 check: 3/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✗ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 -48.1° → 필요한 방향 오른쪽(+) · 첫 Pan 이동 toward · 최대 수정 73.6° · 닫기 시작 때 기준 대비 -1.3°
  - Q5 ok: 첫 닫힘 9.63s 팔로워 바닥 11.9 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.29 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep2 R1-FOLD-OVER
  - Q1 check: 3/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✗ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 +29.3° → 필요한 방향 왼쪽(−) · 첫 Pan 이동 toward · 최대 수정 61.3° · 닫기 시작 때 기준 대비 -4.1°
  - Q5 ok: 첫 닫힘 11.73s 팔로워 바닥 11.8 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.24 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep3 R1-FOLD-OVER
  - Q1 check: 3/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✗ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 -35.2° → 필요한 방향 오른쪽(+) · 첫 Pan 이동 toward · 최대 수정 60.4° · 닫기 시작 때 기준 대비 -6.8°
  - Q5 ok: 첫 닫힘 10.20s 팔로워 바닥 28.0 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 check: 닫기 전 팔 관절 경로/순 변위 1.36 · Pan 방향 바뀜 3번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep4 R1-FOLD-OVER
  - Q1 ok: 4/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✓ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 -19.3° → 필요한 방향 오른쪽(+) · 첫 Pan 이동 toward · 최대 수정 21.6° · 닫기 시작 때 기준 대비 -3.8°
  - Q5 ok: 첫 닫힘 8.80s 팔로워 바닥 13.1 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.13 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep5 R1-FOLD-OVER
  - Q1 ok: 4/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✓ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 +23.1° → 필요한 방향 왼쪽(−) · 첫 Pan 이동 toward · 최대 수정 28.1° · 닫기 시작 때 기준 대비 -4.2°
  - Q5 check: 첫 닫힘 6.83s 팔로워 바닥 13.5 · 첫 닫힘에 쥠 · 첫 파지 입력 미입력
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.17 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep6 R1-FOLD-OVER
  - Q1 ok: 4/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✓ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✓ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 -20.0° → 필요한 방향 오른쪽(+) · 첫 Pan 이동 toward · 최대 수정 20.6° · 닫기 시작 때 기준 대비 -3.2°
  - Q5 ok: 첫 닫힘 9.47s 팔로워 바닥 11.3 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.16 · Pan 방향 바뀜 1번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖
- ep7 R1-FOLD-OVER
  - Q1 check: 3/4: ✓ 팔 접힘 lift ≤ -85 (실패 A0·B1: −102 … −92) · ✓ 목표를 지나친 쪽 ≥ 10° (실패: 수십 °, 재현 안 함) · ✗ 손목 큐브 가장자리 · 안 보임 (실패: 보임 0.27, 보일 때 v 0.96) · ✓ front 큐브 보임 (실패: 1.00)
  - Q2 ok: 시작 기준 대비 +25.3° → 필요한 방향 왼쪽(−) · 첫 Pan 이동 toward · 최대 수정 30.3° · 닫기 시작 때 기준 대비 -4.3°
  - Q5 ok: 첫 닫힘 9.83s 팔로워 바닥 12.8 · 첫 닫힘에 쥠 · 첫 파지 입력 True
  - Q6 ok: 닫기 전 팔 관절 경로/순 변위 1.14 · Pan 방향 바뀜 0번 (3° 문턱)
  - Q7 ok: 무결성 표: 영상 구간 = 판 길이 · 녹화 중 센 프레임 = 저장 줄 수 · frame_index 연속
  - Q8 ok: dataset ~/so101_runs/main_k8/r12_pilot12_r1/dataset · repo_id oxr/so101_k8_r12_pilot12_r1 · d2 dataset 밖

규칙 (config pilot_qa · pilot_reference): {"pan_correction_min_deg": 5, "gripper_open_min": 15, "close_drop_min": 8, "pan_reversals_max": 2, "path_ratio_max": 2.5, "time_align_tol_s": 0.002, "reference": {"R1": {"lift_max": -85, "over_min_deg": 10}, "R2-O": {"wrist_v": [0.25, 0.633]}, "R2-P": {"wrist_v": [0.25, 0.633]}}}
