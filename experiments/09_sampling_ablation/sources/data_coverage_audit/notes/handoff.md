# analysis_handoff — d2 데이터 커버리지 감사 (ChatGPT 전달용)

작성 2026-10-29 · Claude Code · 읽기 전용 CPU 분석. 폴더 `~/so101_runs/main_k8/d2/data_coverage_audit/`.

## 0. 범위와 제한

- 대상: d2 = SO-101 + LeRobot 0.6.2, π0.5 expert-only (vision frozen) 학습 데이터 256편 (T1-K 64 · T1-R 64 · T3-K 64 · T3-R 64; 123,342 프레임, 30 fps). 체크포인트 `d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000`.
- 하지 않은 것: 학습 · 파인튜닝 · 데이터 수정 · 로봇 구동 · GPU 사용. 실행 중이던 sampling_ablation 큐 (A2_s2001 학습) 에는 손대지 않았다. 모든 계산은 `nice -n 19`.
- 출처 표시: [자체 실험] d2 데이터 · d2 실물 실행. [SO-101 외부 실험] aswinkumar99 공개 데이터. [논문] 08 문서에 제목 · 링크.

## 1. 데이터 정의 (확인된 사실)

| 항목 | 정의 | 근거 |
|---|---|---|
| action | 리더 팔 절대 관절 위치 = 같은 tick 의 팔로워 Goal_Position. max_relative_target=None → 자르기 없음 | lerobot `lerobot_record.py:320-368`, `so_follower.py:229-253`, record_ui 로그 |
| observation.state | 팔로워 Present_Position (프레임 처음) | `so_follower.py:204-207` |
| 단위 | 관절 ° (보정 범위 중앙 = 0), 그리퍼 0–100 | use_degrees=True |
| 시간 | timestamp = frame_index/30. 실제 주기 29.88–29.94 Hz, 예산 초과 tick 0/123,086 | record_ui Cadence 로그 |
| 없는 것 | 서보 속도 · 전류 · 토크 · 온도 · 전압, 프레임별 실제 시각, 영상 촬영 시각, 큐브 실측 좌표 | info.json · 로그 |
| 큐브 위치 | 세션 QA: front 첫 화면 빨강 중심 → H 역산 (C frame cm). Known 의 잰−계획 중앙값 0.50 cm | `redbox_*/qa/positions.csv` |
| 큐브 각도 | 계획 (layout.csv) + QA cube_angle 측정 (228/256) | `qa_report.md` |
| 명령→측정 지연 | 3 프레임 (lift 4), 움직일 때 \|action−state\| 3–7° | `tables/a02_lag.csv` |

## 2. 좌표계 · TCP

- C frame: x = 로봇→상자 (+), y = 로봇 왼쪽 (+), cm. 접선 축 = 베이스→큐브 반지름을 반시계 90° (+ = 로봇 왼쪽으로 도는 쪽).
- 베이스: config (−31, 11), pan 오프셋 −1.4 → 이 감사는 256편 첫 파지 pan 으로 다시 맞춘 (−30.55, 11.18), −0.75° 사용 (CV 잔차 2.15°). `tables/a00_base_fit.json`
- TCP = pan 축 극좌표 모델 (`scripts/ac.py: tcp()`): 방향 = pan, 반지름 = FK (so101_new_calib.urdf) 팔 평면 거리 + 4.20 cm (맞춘 편향), 옆 = −(URDF 옆 오프셋). 사람 파지 순간 바닥: 접선 SD 0.59 cm, 반지름 0.79 cm (5-fold CV). 기존 diag fk_fit 는 접선 SD 2.1 cm (bearing 상관 −0.88).
- r_t, r_r = TCP(t) − TCP(첫 파지) 의 접선/반지름 성분 (최종 파지 위치까지 남은 거리, 판별 고정 편향 제거). e_t, e_r = TCP − 큐브 중심.
- 엄격 구분: measured_position (state), commanded_position (action), FK TCP (계산값), 큐브 위치 (영상 추정, 실측 없음).

## 3. 핵심 수치

| 주제 | 수치 | 파일 |
|---|---|---|
| 시작 자세 SD | pan 2.5°, lift 0.1°, elbow 1.5°, wrist_flex 6.1°, roll 2.6° (첫 파지 pan SD 49°) | 03 |
| 첫 pan 움직임 | 총회전의 98% 를 한 번에 (r 0.98), 방향 일치 206/212, ±2° 진입 onset+0.97 s (접근의 11%), ±2° 머묾 파지 4.13 s 전 | 03, 05 |
| pan t90 | 사람 0.8 s (95% 2.6, 최대 4.3) · 외부 단일 1.3–2.6 s · 정책 2.2 / 2.8 / 6.1 / 14.6 s | 07, 10 |
| 위치 공백 | hull (hard zone 제외) 최대 3.44 cm, 반경 3 cm 안 중앙값 4편, K 2 cm 안 129/256 | 04 |
| 늦은 접선 거리 | \|r_t\| ≥ 1 cm: −3 s 27편, −2 s 15편, −1 s 2편; ≥ 1.5 cm: −3 s 3편, −2 s 0편 | 05 |
| 큰 보정 방향 | 닫힘 3 s 안 1 cm 넘는 보정 37편: 오른쪽 31 / 왼쪽 6 | 06 |
| 보정 관절 | 파지 전 3 s 접선 이동 pan 75.7%, roll 5.0%; 보정 창 278/278 이 pan 주도 | 05 |
| roll | 파지 순간 ±55°, 접근 중 \|변화\| 22°; pan 보다 늦게 자리잡음 (2.4 vs 4.1 s 전) | 05 |
| 라벨 편향 | labels_v2 tan @ 사람 파지 순간 ~ roll: r −0.82, −0.011 cm/°; 닫힘 기준 L′ 0.03; 관절 F −0.16 | 06 |
| 칸 재현 | c5 (1.5 s) · s1 (3 s) 칸 표가 칸마다 같음. 빈 칸 25 (3 s), 채워진 칸 사이 빈 칸 0 | 06 |
| 정책 이탈 | 5판 중 4판 이탈 (pan 오차 3판, 시작 높이 1판); 새 위치 판 e_t −5.9 cm, pan +10.2° | 07 |
| 외부 | 시작 고정 (pan SD 2.5–3.7°), T2 연속 파지 시작 pan SD 35°, roll 변화 5–8° (우리 20–23°) | 10 |

## 4. 해석 · 가설 · 제안 (요약, 상세 08 · 09)

- [해석] 가장 부족한 상태는 '큰 접선 오차 (≥ 1 cm) 와 그 보정, 특히 왼쪽 방향' 이다. roll × 작은 오차는 충분하다.
- [해석] 초기 자세 고정과 새 위치 실패의 인과는 데이터로 검정할 수 없다 (변이 없음).
- [가설] 정책의 느린 pan 회전 → 사람에 없는 중간 상태 → 보정 시연 부재가 이어질 수 있다.
- [제안] P0 정책 기준선 평가 16–24판 (새 위치, 라벨) → P1 정렬 오차 회복 시연 64–80편 (hover-offset 으로 시작, 좌우 · 크기 · roll 균형) → P3 시작 pan 다양화 32편 (검증) → P4 위치 밀도 32편. sampling_ablation A2/A2r 결과도 먼저 본다.

## 5. 누락 · 한계

- 속도 · 전류 · 온도 미기록. 큐브 실측 좌표 · 베이스 실측 없음.
- d2 정책 실물 실행은 2 실행 5판뿐이고, 성공 판정이 없다. 새 위치 판은 1판이다.
- URDF 옆 오프셋 부호는 데이터 적합으로 정했다 (물리 실측 확인 안 됨).
- 외부 연구는 관절만 비교했다. 물체 위치 · 영상은 쓰지 않았다.

## 6. 재현

```bash
cd ~/so101_runs/main_k8/d2/data_coverage_audit/scripts
R="env PYTHONDONTWRITEBYTECODE=1 nice -n 19 $HOME/so101-env/bin/python"
$R a00_tcp_model.py      # 베이스 재적합 + TCP 모델 (a00_*.json) — 다른 스크립트보다 먼저
$R a01_inventory.py      # 스키마 · 주기 · 영상 표본 · 큐브 표
$R a02_timeline.py       # 02_servo_timeline.parquet, a02_frames.parquet, 이벤트, 지연
$R a03_initial_state.py; $R a04_cube_coverage.py; $R a05_action_timeline.py
$R a06_roll_error.py; $R a07_policy_vs_demo.py; $R a09_reference_compare.py; $R a08_facts_0102.py
nice -n 19 /usr/bin/python3 p_figures.py    # 그림 (시스템 python3 + matplotlib)
python3 make_reports.py                      # notes/*.md + _facts/*.md → 최종 보고서
```

입력 (읽기만): `d2/dataset`, `main_k8/redbox_*/{layout.csv,qa/positions.csv,qa_report.md}`, `~/.local/state/record_ui/record_2026102[23]_*`, `d2/vision_probe/labels_v2.csv`,
`d2/diag_grasp_bias/{common.py,fk_fit.json,grasp_train.csv,grasp_eval.csv}`, `d2/action_bottleneck/c5_*`, `d2/sampling_ablation/s1_cells.csv`, `d2/eval/rollouts/*`,
`~/so101_runs/reference/aswinkumar99_so101_pick_place`, `~/so101_boxpick/config/redbox8_layouts.yaml`, URDF `~/Ros2/ros2_ws/src/twin_description/urdf/so101_new_calib.urdf`.

## 7. 파일

| 파일 | 내용 |
|---|---|
| 01_dataset_inventory.md | 스키마 · 단위 · 주기 · 누락 · 좌표계 · TCP 모델 |
| 02_servo_timeline.parquet (+ 02_servo_timeline_readme.md) | 256편 × 프레임 × 서보 6, 측정/명령 분리 |
| 03_initial_state_analysis.md | 시작 자세 · 첫 pan 움직임 |
| 04_cube_position_coverage.md | 위치 · 각도 · 공백 |
| 05_action_timeline_analysis.md | 구간별 행동, Q1–Q5 |
| 06_roll_error_coverage.md | roll × 오차 재검증 · 라벨 편향 |
| 07_policy_vs_demonstration.md | 정책 5판 vs 사람 |
| 08_additional_data_recommendation.md | 판단 표 · 고정/변수 · P0–P4 |
| 09_analysis_summary.md | 발견 9개 · 연구 질문 10개 답 |
| 10_reference_so101_compare.md | 외부 SO-101 관절 비교 |
| figs/fig01–07 | 위치 · 시작 자세 · pan 시점 · 남은 거리 · roll×tan 칸 · 정책 vs 사람 · 외부 비교 |
| tables/ | 모든 수치 원본 (csv/json/parquet) |
