# 03 기존 d2 정책 실행 로그 목록 · 사용 가능한 정보 · 빠진 정보

작성 2026-10-29. 대상: `~/so101_runs/main_k8/d2/eval/rollouts/` (d2 020000 실물 실행 전부). 생성 스크립트 `scripts/p01_timeline.py` (틱 시간축), `p02_existing_metrics.py`, `p02b_timing_facts.py`.

## 1. 실행 목록

| 실행 | 판 | 프레임 | 필터 | 파일 |
|---|---|---|---|---|
| 20261026_135128_20k_t1_try3 | 0, 1 | 898, 2085 | 꺼짐 | command.txt, console.log, debug.log, dataset/ (21 MB), analysis.json/npz, ep*_action_state.png, pose_check.txt |
| 20261026_140246_20k_t1_try3_filt | 0, 1, 2 | 607, 1580, 942 | 켬 | 위와 같음 + filter_log.csv (3,332 줄) |

- 이 밖의 d2 실물 정책 실행은 없다. d2 eval_ui 실행 (`*_t1_eval_filt`) 은 기록이 없다.
- 성공/실패 판정은 기록되지 않았다 (`평가_명령.md`: run_rollout 은 판정을 남기지 않음).
- 큐브 위치는 기록되지 않았다. 지금 쓰는 위치는 dataset 첫 front 프레임에서 빨강 검출 → 화면→탁자 변환으로 추정한 값이다 (`diag_grasp_bias/grasp_eval.csv` start_x/y, `data_coverage_audit/tables/a04_eval_positions.csv`). 큐브 각도는 기록·추정 모두 없다.
- 오프라인 프로브 결과 (실물 실행 아님): `diag_grasp_bias/` (첫 chunk 프로브, ep1 재계획, noise 64 개), `action_bottleneck/`, `vision_probe/`, `sampling_ablation/eval/` — 모두 기록된 영상·state 를 넣어 다시 계산한 값이다.

## 2. 항목별 존재 여부

| 항목 | try3 (필터 꺼짐) | try3_filt (필터 켬) | 비고 |
|---|---|---|---|
| 입력 front 프레임 | △ dataset 영상 (AV1 재부호화, 녹화된 틱만) | △ 같음 | 정책이 실제로 받은 원본 (MJPEG 디코드 RGB) 이 아님. 첫 chunk 의 관측 틱 (action 이 나가기 전) 은 dataset 에 없다 |
| 입력 wrist 프레임 | △ 같음 | △ 같음 | |
| 입력 observation.state | ○ dataset (틱마다) | ○ dataset + filter_log state_* | 추론에 쓴 바로 그 틱은 기록되지 않음 → merge 틱 − 적용 delay 로 근사 (±1 틱) |
| 최초 생성 action chunk (50 개 전체) | ✕ | ✕ | 실행된 index 0–29 만 남아 있음 (아래) |
| 시간별 생성 chunk (50 개 전체) | ✕ | ✕ | 실행된 index ≈ 10–29 (chunk 당 19–21 개) 만 |
| 실행된 chunk 부분 (queue 출력 = RTC 안내 뒤, 필터 전) | ○ dataset action (필터 없으므로 같은 값) | ○ filter_log raw_* | `p01_ticks.parquet` raw_* |
| RTC 처리 전 action (안내 없는 chunk) | ✕ | ✕ | 기록 자체가 없다 (guided RTC 는 denoise 안에서 안내하므로 '안내 전' 값은 따로 계산해야만 생김) |
| RTC 처리 후 action | △ 실행된 부분만 | △ 실행된 부분만 | 위와 같음 |
| chunk 경계 (merge 시각, real_delay, 적용 delay) | ○ debug.log (시각 ms, latency, real/clamped delay) | ○ filter_log merge 행 (틱 단위) + debug.log | `p01_merges.csv`. try3 은 시각→프레임 대응을 clamp 기준점 직선으로 함 (잔차 중앙값 0.8 / 1.6 ms, 최대 10 ms) |
| 정책에 넘긴 inference_delay | ✕ | ✕ | 코드로 도출만 가능 (02 문서) |
| RTC prefix (prev_chunk_left_over), noise | ✕ | ✕ | |
| 필터 뒤 명령 | (필터 없음) | ○ filter_log out_* = dataset action (차 ≤ 5.4e-5) | |
| 실제 서보 명령 (clamp 뒤 Goal_Position) | △ clamp 경고 틱만 debug.log 'safe goal_pos', 나머지 틱은 clamp 안 됨 = 필터 뒤 값 | △ 같음 | 경고와 프레임을 값으로 맞춤: 판 안 경고 전부 대응 (try3 369 · filt 250). 대응 안 된 85 개는 판 마지막 프레임 0.08–0.99 s 뒤 (리셋 동작) |
| clamp 에 쓴 Present_Position | ✕ | ✕ | send_action 이 따로 읽는 값. 관측 state 와 시각이 다름 |
| 실제 관절 측정 state | ○ dataset observation.state (틱 시작) | ○ 같음 | |
| 실행 시각 · 처리 지연 | ○ debug.log RTC latency, 제어 루프 cadence 경고 | ○ + filter_log wall (틱마다) | |
| 카메라 프레임 시각 · 나이 | ✕ | ✕ | |
| 큐브 배치 위치 · 각도 | ✕ (영상 추정 위치만) | ✕ (영상 추정 위치만) | 위치 추정 오차: 사람 파지 순간 기준 |pan − 추정 기대 pan| SD 2.31° (data_coverage_audit 07) |
| 시작 자세 | ○ pose_check.txt | ○ pose_check.txt | |

○ 있음 · △ 일부 · ✕ 없음

## 3. 기존 로그로 계산한 것 / 못 한 것

계산함 (실측):
- 판별 pan 명령 (raw) · 실제 위치 (state) 의 onset 뒤 0.5/1/2/3 s 진행률, t50/t90 (`p02_policy_episodes.csv`)
- 첫 chunk 의 실행된 부분 (index 0–29, 1 s) 의 pan
- chunk 경계마다 실행 명령의 끊김 (seam), chunk 실행 구간의 남은 오차 대비 이동 비율 (`p02_chunks.csv`, `p02_closed_loop_gain.csv`)
- 명령 → 실제 위치 지연·추종 오차, 필터 · clamp 가 pan 명령을 바꾼 양 (`p02_tracking.csv`)

재구성으로만 가능 (GPU, 실측 아님 — `p03_offline_replan.py`, 결과는 04/05 문서에 '재구성' 으로 표시):
- 같은 관측에서 RTC 안내 없이 다시 만든 chunk 전체 (noise 8 개). 영상은 AV1 디코드, 관측 틱은 ±1 틱 근사, noise 는 실물과 다름.

기존 로그로 불가능:
- 실물에서 만든 chunk 의 실행 안 된 부분 (index 30–49, 첫 chunk 는 30–49, 이후는 0–9 · 30–49)
- 실물 chunk 의 RTC 안내 전후 차이 (같은 noise 로 다시 계산하려면 noise · prefix · 원본 영상이 필요)
- clamp 에 쓴 Present_Position, 카메라 프레임 나이
- 큐브 실제 좌표·각도, 성공 판정

→ 신규 계측 필요 항목은 `07_evaluation_protocol.md` · `d2/eval/diag_log.py`.
