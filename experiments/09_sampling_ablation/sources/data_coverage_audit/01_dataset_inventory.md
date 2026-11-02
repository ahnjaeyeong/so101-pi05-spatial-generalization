# 01 데이터 구조 · 원본 파일 조사 (d2, 256편)

작성 2026-10-29. 읽기 전용 분석 (데이터셋 · 체크포인트 · 학습 run 은 건드리지 않음, 로봇 · GPU 안 씀).
재현: `cd ~/so101_runs/main_k8/d2/data_coverage_audit/scripts && PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python a00_tcp_model.py && ... a01_inventory.py && ... a02_timeline.py && ... a08_facts_0102.py && python3 make_reports.py`

## 측정 사실 (스크립트 생성: `scripts/a01_inventory.py`, `a00_tcp_model.py`, `a08_facts_0102.py`)

### 1.1 파일

- 경로 `~/so101_runs/main_k8/d2/dataset` (LeRobot v3.0, robot_type so_follower), 256 편 · 123,342 프레임 · fps 30.

| kind | files | MB |
|---|---|---|
| data | 1 | 5.5 |
| meta | 4 | 0.5 |
| videos/observation.images.front | 4 | 642.9 |
| videos/observation.images.wrist | 2 | 348.8 |


### 1.2 스키마 (meta/info.json)

| column | dtype | shape | names |
|---|---|---|---|
| action | float32 | [6] | shoulder_pan.pos, shoulder_lift.pos, elbow_flex.pos, wrist_flex.pos, wrist_roll.pos, gripper.pos |
| observation.state | float32 | [6] | shoulder_pan.pos, shoulder_lift.pos, elbow_flex.pos, wrist_flex.pos, wrist_roll.pos, gripper.pos |
| observation.images.front | video | [480, 640, 3] | height, width, channels |
| observation.images.wrist | video | [480, 640, 3] | height, width, channels |
| timestamp | float32 | [1] | None |
| frame_index | int64 | [1] | None |
| episode_index | int64 | [1] | None |
| index | int64 | [1] | None |
| task_index | int64 | [1] | None |


- 영상: av1 yuv420p, g=2, crf=30, 640×480, 30 fps.
- 원본 세션 메타 (d2 에는 없음, 세션 폴더에 있음): `layout.csv` (계획 배치 · 각도 · 상태), `qa/positions.csv` (front 첫 화면 큐브 위치 cm), `qa_report.md` (잰 각도 · 손목 필요/돌림), `qa/servo_data.json` (관절 요약), record_ui sidecar 로그 (`~/.local/state/record_ui/record_*.log|json`).

### 1.3 각 열의 의미 · 단위 (코드 근거)

| 열 | 의미 | 근거 |
|---|---|---|
| observation.state | 팔로워 서보 `Present_Position` (sync_read), 프레임 처음에 읽음 | lerobot `robots/so_follower/so_follower.py:204-207` |
| action | 리더 팔 위치 (teleop.get_action) — 같은 tick 에 팔로워 `Goal_Position` 으로 그대로 보냄 (절대 목표, 상대 변화량 아님) | `scripts/lerobot_record.py:320-368` (데이터셋에는 자르기 전 action_values 를 저장), `so_follower.py:229-253` |
| max_relative_target | 녹화 256편 모두 ['None'] → 보낸 목표 = 저장된 action | sidecar 로그 |
| 위치 PID | P ['16'] · I ['0'] · D ['32'] | sidecar 로그 |
| 단위 | 관절 5개 °(use_degrees=['True']: (raw − (range_min+range_max)/2) × 360/4095), 그리퍼 0–100 (RANGE_0_100) | `so_follower.py:71-80` |
| timestamp | frame_index / 30 (기록 시각이 아니라 계산값) | 데이터: 아래 1.4 |
| 큐브 위치 | 데이터셋에 없음. 세션 QA 가 front 첫 화면 빨강 중심을 config H 로 역산 (C frame cm) | `check_dataset.py`, `qa/positions.csv` |
| 큐브 각도 | 데이터셋에 없음. 계획 = layout.csv angles, 잰 값 = QA cube_angle (front 첫 화면) | `qa_report.md` |
| 속도 · 전류 · 온도 · 전압 · 부하 · 실제 보낸 목표의 서보 측 값 | **기록 없음** (데이터셋 열 · sidecar 로그 모두) | info.json, 로그 |

### 1.4 시간 · 동기화

- timestamp 간격 0.033333–0.033335 s; |timestamp − frame_index/30| 최대 8.90e-07; frame_index 불연속 0; NaN state 0 · action 0.
- 영상 구간 길이 (to − from) × 30 − 데이터 프레임 수: 최대 1.2e-11 프레임.
- 실제 루프 주기 (record_ui 로그 'Cadence' 줄, 판별): 256/256 편 연결, tick 수 = 프레임 수 256/256. 29.88–29.94 Hz (중앙값 29.92); 33.3 ms 예산 넘긴 tick 0/123,086; 작업 시간 평균 중앙값 2.7 ms, 최악 29.4 ms. 프레임별 실제 시각은 기록되지 않음.
- 영상 해독 표본 16편 × 2 카메라: 해독 프레임 수 = 데이터 프레임 수 32/32. 팔이 움직이는 프레임 (관절 속도 > 20°/s) 중 앞 프레임과 거의 같은 (평균 차 < 0.05/255, 1/8 축소) 프레임: front 61, wrist 51 / 카메라당 3488 (중복 · 멈춘 프레임 후보).
- 카메라 영상은 `read_latest()` (비동기 최신 프레임) 이라 state 읽기와 같은 tick 에 묶이지만 촬영 시각은 기록되지 않는다 → 영상-관절 사이 지연은 측정 불가.

### 1.5 값 해상도 · 범위 (전 프레임)

| joint | state_min_step | n_unique_state | state_min | state_max | action_min | action_max |
|---|---|---|---|---|---|---|
| shoulder_pan | 0.0879 | 2337 | -108.48 | 103.30 | -108.84 | 103.74 |
| shoulder_lift | 0.0879 | 1860 | -103.25 | 63.25 | -105.27 | 62.81 |
| elbow_flex | 0.0879 | 1958 | -82.07 | 96.31 | -84.22 | 97.85 |
| wrist_flex | 0.0879 | 1009 | 1.58 | 99.96 | 0.57 | 100.62 |
| wrist_roll | 0.0879 | 1208 | -57.01 | 55.16 | -57.36 | 55.69 |
| gripper | 0.0691 | 647 | 0.83 | 49.62 | 0.00 | 50.04 |


### 1.6 캘리브레이션

- `/home/user/.cache/huggingface/lerobot/calibration/robots/so_follower/my_arm.json` (수정 2026-09-29T08:13:26): shoulder_pan homing -1509 range 830–3338; shoulder_lift homing -1575 range 856–3215; elbow_flex homing -846 range 872–3071; wrist_flex homing 1982 range 808–3130; wrist_roll homing -1758 range 0–4095; gripper homing 1413 range 2045–3492
- `/home/user/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_leader.json` (수정 2026-09-29T08:13:26): shoulder_pan homing -1418 range 760–3366; shoulder_lift homing 1956 range 888–3267; elbow_flex homing -1721 range 817–3031; wrist_flex homing -1458 range 904–3153; wrist_roll homing -1440 range 0–4095; gripper homing 1617 range 2027–3258

### 1.7 좌표계 · TCP (a00_tcp_model)

- C frame (config redbox8_layouts.yaml): x = 로봇 → 상자 (+), y = 로봇 왼쪽 (+), cm. 원점 = 상자 로봇쪽 벽 바깥면 로봇 오른쪽 끝 (C 의 y 는 ±0.5 cm 추정).
- 베이스: config (-31.0, 11.0), pan 오프셋 -1.4° (T1-K 48편 맞춤) → 첫 파지 pan 잔차 SD 2.31°, 평균 +1.01°, bearing 과 상관 -0.44. 이 감사는 256편으로 다시 맞춘 (-30.55, 11.18), 오프셋 -0.75° 사용 (5-fold CV 잔차 SD 2.15°, bearing 상관 -0.07). 실측 베이스 위치는 없다.
- TCP 모델 비교 (파지 순간, 큐브 중심 대비 cm):

| model | tan_mean | tan_sd | tan_abs_p50 | tan_abs_p90 | rad_mean | rad_sd | corr_tan_roll | corr_tan_bearing |
|---|---|---|---|---|---|---|---|---|
| M0_fkfit_rigid | 0.05 | 2.07 | 1.83 | 3.08 | -2.32 | 1.26 | -0.35 | -0.88 |
| M1_polar_lat_plus | -0.06 | 0.85 | 0.62 | 1.33 | -4.22 | 0.78 | -0.84 | 0.04 |
| M2_polar_lat_minus | 0.01 | 0.46 | 0.24 | 0.71 | -4.20 | 0.78 | -0.05 | 0.08 |
| M2b_polar_lat0 | -0.02 | 0.59 | 0.37 | 0.94 | -4.21 | 0.78 | -0.62 | 0.06 |
| M2_dA_cv | 0.01 | 0.59 | 0.34 | 0.94 | -0.00 | 0.79 | -0.22 | 0.08 |


- 채택 = M2 + 반지름 편향 dA 4.20 cm (CV). URDF (so101_new_calib) 의 pan 축은 base_link 원점에서 3.88 cm 떨어져 있어, 기존 fk_fit (base_link 를 강체 변환) 은 bearing 에 비례하는 접선 오차 (상관 −0.88) 를 만든다. URDF 옆 오프셋 부호를 뒤집은 M2 가 roll 상관을 없앤다 (M1 −0.84 → M2 −0.05) — URDF wrist_roll 방향과 lerobot 보정 방향의 차이로 보이나 확인 안 됨.
- 측정 바닥 (사람 파지 순간): 접선 SD 0.59 cm (|.| 중앙값 0.34, 90% 0.94), 반지름 SD 0.79 cm. 큐브 위치 추정 오차 (Known 잰 − 계획) 중앙값 0.50, 90% 0.99 cm 가 이 안에 포함된다.
- 판 안 상대 이동 (TCP(t) − TCP(c)) 은 판별 고정 편향이 빠지므로 바닥보다 작은 변화도 비교할 수 있다 (a05: wrist 영상 라벨과 상관 −0.73, 기울기 −0.92 @ 닫힘 2–3 s 전).


## [해석] (자체 실험)

- `action` 은 **리더 팔의 절대 관절 위치 = 같은 tick 에 팔로워로 보낸 Goal_Position** 이다. 상대 변화량이 아니고, 실제 측정 관절값도 아니다. 녹화 때 max_relative_target 이 None 이라 저장된 action 과 서보에 보낸 목표가 같다.
- `observation.state` 는 팔로워 측정값이다. 명령보다 3–4 프레임 (≈ 100–130 ms) 늦게 따라가고, 움직이는 동안 평균 3–7° 차이가 난다 (02 문서 2.2). 정책 학습 목표 (action) 는 '측정 상태보다 약 0.1 s 앞선 목표'다.
- 시간축은 frame_index/30 으로 만든 값이지만, 녹화 로그상 실제 주기가 29.88–29.94 Hz 이고 예산을 넘긴 tick 이 0 개라 프레임 간격 오차는 0.3% 이내다. 영상 프레임 수도 데이터와 정확히 같다. 영상과 관절 사이의 촬영 시각 차는 기록이 없어 측정할 수 없다.
- 서보 속도 · 전류 · 토크 · 온도 · 전압은 **기록되지 않았다**. 이 감사의 속도는 모두 위치 차분 추정값이다.
- 큐브 좌표와 각도는 데이터셋 밖 (세션 QA) 에 있고, 모두 **front 첫 화면 영상 추정값**이다. 실측 좌표는 없다.

## [가설]

- URDF 옆 오프셋 부호가 탁자와 반대로 나오는 것은 URDF wrist_roll 축 방향과 lerobot 보정 방향의 차이 때문일 수 있다. 확인하려면 roll 만 ±45° 돌린 정지 자세에서 집게 끝 위치를 자로 재야 한다 (토크 필요 → 사용자 작업).

## 한계

- TCP 는 FK + 맞춘 베이스 · 반지름 편향이다. 큐브 중심 기준 절대 접선 오차는 SD 0.59 cm 아래를 판별로 해석할 수 없다. 판 안 상대 이동 (최종 파지 기준) 은 이 편향이 빠진다.
- 베이스 위치는 pan 으로 맞춘 추정값이고 실측이 아니다.
