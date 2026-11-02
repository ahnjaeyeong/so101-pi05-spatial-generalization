# 07 실물 진단 파일럿 — 사용자 실행 절차 (d2 020000, 계측 켬)

작성 2026-10-29. **로봇 실행은 사용자가 직접 한다** (Claude 는 명령을 실행하지 않음). 이 평가는 원인 단계를 가르기 위한 소규모 파일럿이고, 성공률 확정용이 아니다. 기록은 학습에 쓰지 않는다.

## 1. 고정 조건 (기존 d2 평가와 같게)

| 항목 | 값 | 기존 대비 |
|---|---|---|
| 체크포인트 | d2 `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` | 같음 |
| 추론 | RTC guided, EXP, execution_horizon 20, max_guidance_weight 10, num_inference_steps 5, queue_threshold 30, fps 30 | try3 · try3_filt 와 같음 |
| 팔 필터 | `--arm_filter=true` (α 0.5, init state) | try3_filt · `평가_명령.md` 와 같음 |
| max_relative_target | 8 | 같음 |
| 카메라 | front · wrist 640×480 30 fps MJPG, 위치·노출 그대로 | 같음 |
| 과제 문장 | `pick up the red cube and put it in the brown box` | 같음 |
| 시작 자세 | eval_ui 가 판마다 처음 자세로 되돌림. `pose_check.txt` 에 기록만 함 (자세로 막거나 묻지 않음) | 같음 |
| **추가** | 환경변수 `ROLLOUT_DIAG=1` → `d2/eval/diag_log.py` 기록 | 새로 추가 (제어 값은 바꾸지 않음, 4 절) |

코드 변경 기록: `rollout_logged.py` sha256 `cf72afe0…` (원본, `backup/rollout_logged.before_diag_20261029.py`) → `8fcd4b6b…` (ROLLOUT_DIAG 분기 3 곳만 추가). `diag_log.py` 새 파일 (sha256 `b1425bab…`, 6 절의 수정 뒤). lerobot 설치 파일은 바꾸지 않음. 실행마다 `diag/manifest.json` 에 관련 파일 sha256 이 남는다.

## 2. 판 구성 (12 판, 각도 0 만) — 2026-10-29 수정: U 는 지정 좌표 없음

| 순서 | 이름 | 놓는 곳 | 비고 |
|---|---|---|---|
| 1 | U3 | 작업 범위 안 임의 자리 (참고: 가운데 앞, pan 이동 작은 곳) | 기록: `U3 unknown` |
| 2 | K1 | 표시된 K1 자리 (−8.5, 26.5) | 학습 위치 |
| 3 | U2 | 임의 (참고: 로봇 오른쪽 먼 곳) | `U2 unknown` |
| 4 | U5 | 임의 (참고: 로봇 왼쪽, 상자 쪽 줄 바깥) | `U5 unknown` |
| 5 | K3 | 표시된 K3 자리 (−8.5, −3.5) | 학습 위치 |
| 6 | U6 | 임의 (참고: 로봇 오른쪽 가까운 곳) | `U6 unknown` |
| 7 | U7 | 임의 (참고: 가운데 줄 왼쪽) | `U7 unknown` |
| 8 | K6 | 표시된 K6 자리 (−17.0, −3.5) | 학습 위치 |
| 9 | U4 | 임의 (참고: 상자 쪽 줄 오른쪽 바깥) | `U4 unknown` |
| 10 | U1 | 임의 (참고: 로봇 왼쪽 먼 곳) | `U1 unknown` |
| 11 | K7 | 표시된 K7 자리 (−25.5, 26.5) | 학습 위치 |
| 12 | U8 | 임의 (참고: 왼쪽 앞, 상자 벽에서 2.5 cm 이상 떨어지게) | `U8 unknown` |

- **U1–U8 은 지정 좌표에 맞추지 않는다.** 이름은 기록용이고, '참고' 는 자리가 한쪽에 몰리지 않게 하려는 대략적 방향일 뿐이다. 실제 좌표는 판마다 시작 front 사진에서 잰다 (09 문서, `scripts/cube_coords.py`).
- 작업 범위 (이 안에 놓으면 좌표 역산이 '검증 범위' 안이다):
  - H 적용 범위 x −35 … −5, y −15 … +37 cm 안 (d2 학습 큐브가 있던 범위 + 1 cm). K 에서 멀어도 된다. K 에서 3 cm 넘게 떨어진 자리는 valid_off_K 로 따로 분석한다 (좌표 정확도 미검증).
  - 상자 앞 벽 바로 앞 띠 (x > −5) 는 피한다. config 상 보정이 덜 정확한 곳이라 invalid_calibration 이 된다.
  - 로봇 바로 앞 '집기 어려운 영역' (config hard_zones: x −34 … −18, y −1.5 … +24.7) 은 피하기를 권한다. 금지는 아니다.
- K1 · K3 · K6 · K7 은 표시된 자리에 놓는다. 이 4 판의 '사진 좌표 − K 명목' (`photo_minus_K_cm`) 이 이 실행 안의 좌표 역산 점검이 된다. 학습 K 판 128 편에서 이 값은 중앙 0.48 · p90 0.98 · 최대 2.3 cm 였다.
- 판 시작 사진은 eval_ui 가 → 를 누른 순간 (팔이 움직이기 전) 찍는다. 이때 **손 · 다른 빨간 물체가 화면에 없어야** 좌표가 나온다 (빨강 덩어리가 둘이거나 크기가 맞지 않으면 invalid_detection).
- 각도는 모두 0 (큐브 면이 로봇 정면과 나란히).
- 정답 pan (pe) 은 사진 좌표로만 계산한다. 로봇이 잡은 자리 · 정책 pan 은 정답에 쓰지 않는다.
- 좌표 상태 (09 문서 5 절): valid_near_K · valid_off_K (pe 저장, off-K 는 좌표 정확도 미검증 · 별도 그룹) · invalid_detection · invalid_calibration (이 둘만 pe 지표에서 빠짐).
- 메모의 `unknown` 은 '놓을 때 좌표를 정하지 않았음' 이라는 뜻이다. 좌표 상태와는 별개다.

## 3. 실행 — 2 단계 (U3 1 판 → 기록 점검 통과 → 나머지 11 판)

로봇 명령은 모두 **사용자가 직접** 터미널에서 실행한다. Claude 는 아래 점검 · 분석 (읽기만, 로봇 연결 없음) 만 한다.

### 3.0 직전 점검 (읽기만, 로봇 · 카메라 장치를 열지 않음)

```bash
cd ~/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00_preflight.py      # 마지막 줄 ALL_OK 여야 함 (약 1 분)
```

- 무엇을 보는가:
  - d2 020000 파일 sha256 (10-27 기록과 같음).
  - 평가 코드 sha256 (rollout_logged `8fcd4b6b`, diag_log `b1425bab`, arm_filter `a5307329`).
  - lerobot 설치 파일 = pip RECORD.
  - eval_ui `--check` 의 RTC · queue · filter · fps · clamp.
  - 학습 정지 (QUEUE_STOPPED, 학습 프로세스 없음).
  - GPU · 다른 lerobot · twin · 장치 경로 · 디스크.
- 2026-10-29 15:04 결과: ALL_OK (`preflight/preflight_20261029_150452.json`).

### 3.1 1 단계: U3 1 판 (`--episodes 1`)

```bash
cd ~/so101_boxpick
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py --session main_k8/d2 --tag pan_diag --episodes 1 \
  --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true
```

1. 점검 화면 (장치 · docker · GPU 없음 · 카메라 자동 노출) 을 확인하고 Enter 를 누른다. 모델을 불러오는 데 2–3 분 걸린다.
2. '준비' 화면에서 큐브를 **작업 범위 안 임의 자리 (참고: 가운데 앞), 각도 0** 에 놓는다. 손이 화면에서 빠진 뒤 → 를 누르면 시작 사진이 찍히고 실행된다.
3. 끝나면 (상자에 넣었거나, 멈췄거나, 1 분 넘게 헤맴) → 를 누른다.
   - `--episodes 1` 이라 초기화 단계 없이 저장된다.
   - 팔은 처음 자세로 돌아간 뒤 연결을 끊는다.
4. 판정 질문에 P/F, 메모에 `0 U3 unknown first=<Y|N> final=<Y|N> <특이사항>` 을 입력한다 (U 판은 좌표를 모르므로 `unknown`).
5. 다시 하기: 실행 중 ← 를 누르면 그 시도를 버리고 같은 번호로 다시 한다. 버린 시도도 diag 에 남고, 분석에서 discarded 로 표시된다.

### 3.2 1 단계 기록 점검 (GPU 를 쓰므로 eval_ui 가 끝난 뒤. 로봇 연결 없음)

```bash
cd ~/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts
RUN1=$(ls -dt ~/so101_runs/main_k8/d2/eval/rollouts/*_pan_diag | head -1); echo $RUN1
nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p05_replay_check.py $RUN1/diag   # GPU 1–2 분: 기록 입력으로 다시 계산 + RTC 끔 반사실
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00b_verify_run.py $RUN1                       # CPU 수 초: 마지막 줄 VERIFY_OK
```

`p00b_verify_run.py` 가 보는 것 (`$RUN1/diag/verify.json`):

| # | 확인 | 통과 기준 |
|---|---|---|
| F1 | results.csv · start_images/ep000_{front,wrist}.png · dataset · filter_log.csv · debug.log · console.log | 모두 있음 |
| F2 | diag/manifest.json · summary.json · chunks.jsonl · ticks.csv · chunks/ · obs/ | 모두 있음 (summary 는 정상 종료 때 씀) |
| F3 | 버린 기록 · 감싸기 오류 | 0 · 0 |
| F4 | manifest 코드 sha256 · 실행 설정 | 위 sha · steps 5 · guided · EXP · mgw 10 · h 20 · queue 30 · 020000 · clamp 8 · arm_filter |
| F5 | chunk 마다 original (RTC 처리 뒤 정규화 chunk 50×6) · processed (° 50×6) · noise (50×32) · prefix · 관측 PNG front/wrist 480×640 | 모두 있음, 값 유한 |
| F6 | 판 첫 chunk | prefix 없음 (= RTC 안내 없는 Action Expert 출력) |
| F7 | ticks.csv: Goal 입력 · 보낸 Goal · Present (6 관절) | 빈칸 0, 행 수 = filter_log cmd 행 ≈ dataset 프레임 |
| F8 | chunk 값 = queue 출력 (filter_log raw) · Present ≈ 틱 시작 state | 차 < 1e-3° · 중앙 < 1° |
| F9 | 추론 시간 · 카메라 프레임 나이 | predict p50 200–600 ms · front 나이 p50 < 100 ms |
| F10 | 기록 입력으로 다시 계산한 chunk = 기록 chunk | 모든 chunk \|차\| ≤ 0.01° |
| F11 | 시작 front 사진: 카메라 이동 (상자 사각형 좌우 변) · 큐브 좌표 역산 | 이동 ≤ 6 px (FAIL 이면 좌표 전체를 쓸 수 없음). 좌표 결과는 INFO (invalid_* 이어도 기록 점검은 통과, 그 판만 pe 지표에서 빠짐) |

**VERIFY_OK (F1–F10 FAIL 0) 일 때만 2 단계로 간다.** FAIL 이 있으면 진행하지 말고 `verify.json` 을 Claude 에게 보여 준다.

### 3.3 2 단계: 나머지 11 판 (`--episodes 11`)

```bash
cd ~/so101_boxpick
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py --session main_k8/d2 --tag pan_diag --episodes 11 \
  --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true
```

- 순서: K1 → U2 → U5 → K3 → U6 → U7 → K6 → U4 → U1 → K7 → U8. K 는 표시된 자리, U 는 작업 범위 안 임의 자리 (2 절). 각도는 모두 0.
- 판 흐름:
  1. 큐브를 놓고 → 로 시작한다.
  2. 끝나면 → 를 누른다.
  3. 처음 자세로 복귀하는 동안 **P/F** 를 누르고 → 로 다음 판으로 간다.
  4. 11 번째 판은 초기화 없이 저장되고 끝난다.
- 메모는 2 단계 판 번호 (0–10) 기준이다: K 판 `<번호> <K이름> first=<Y|N> final=<Y|N> <특이사항>`, U 판 `<번호> <U이름> unknown first=… final=… <특이사항>`. 예: `2 U5 unknown first=N final=Y 덜 돌아 두 번째 시도에 잡음`.
- 판 시간: 30 s 를 넘겨도 끊지 않아도 된다. 같은 자리에서 1 분 넘게 헤매면 → 로 끝내고 메모에 `timeout` 을 남긴다.
- 실행이 두 개로 나뉘므로 '세션 두 번째 추론의 inference_delay 0' (05 문서 1 절) 은 U3 판 chunk 1 과 K1 판 chunk 1 에서 한 번씩 생긴다. 분석 표의 inference_delay 열로 구분한다.
- 2 단계가 끝나면 `p00b_verify_run.py $RUN2` 로 같은 점검을 한다 (판 수만 다름).

## 4. 기록되는 것 (`eval/rollouts/<시각>_32_20000_20k_pan_diag/`)

eval_ui 기본: results.md/csv · start_images/ · dataset/ · console.log · debug.log · filter_log.csv · pose_check.txt.
`diag/` (ROLLOUT_DIAG=1):

| 파일 | 내용 | 진단 항목 |
|---|---|---|
| chunks.jsonl | chunk 마다 관측 틱·시각, 카메라 프레임 시각, 추론 시작·끝, merge 시각, 정책에 넘긴 inference_delay, real_delay, 적용 delay, 관측 state | 관측 → 추론 → 실행 지연 |
| chunks/c#####.npz | original (정규화) · processed (°) 50×6 **전체**, noise 50×32, prefix (prev_chunk_left_over), merge 직전 queue 에 남은 앞 chunk action | 최초 chunk 전체, chunk 간 차이, RTC 안내 반사실 재현 |
| obs/c#####_{front,wrist}.png | 그 추론이 실제로 받은 영상 (무손실) | 정확한 오프라인 재현 |
| ticks.csv | 틱마다 꺼낸 action 의 chunk·index, clamp 전 명령, clamp 뒤 Goal_Position, clamp 에 쓴 Present_Position, send 시간, 관측 카메라 프레임 나이 | RTC 뒤 → 필터 → clamp → 서보 추종 |
| manifest.json · summary.json | 인자·환경·설정·코드 sha256 / 기록 개수·버린 수·감싸기 비용 | 재현성·로깅 영향 점검 |

필터 전 queue 출력은 기존대로 filter_log.csv raw_*, 실제 위치는 dataset observation.state 에 남는다.

## 5. 로깅이 제어에 주는 영향 (오프라인 점검)

`scripts/p04_harness.py` 로 같은 RTC 엔진 · 정책 (d2 020000, RTC guided EXP h20 mgw 10, steps 5, queue_threshold 30, fps 30) · `SOFollower.send_action` (clamp 8° 포함) 을 가짜 팔 (FakeBus · FakeCam, `FeetechMotorsBus.connect` · `OpenCVCamera.connect` 차단, Fake assert) 에 붙여 diag 끔 3 회 · 켬 2 회를 같은 조건 (기록 판 filt/ep1 영상 · state, 450 틱 = 15 s) 으로 돌렸다 (2026-10-29 14:2x–14:3x). 모음: `scripts/p04b_harness_summary.py` → `tables/p04_harness_summary.csv`.
기록된 chunk 재현: `scripts/p05_replay_check.py harness/on_1/diag` → `harness/on_1/diag/replay/replay.csv`.

## 6. 점검 결과

| 항목 | diag 끔 (off_1 / off_2 / off_3) | diag 켬 (on_1 / on_2) |
|---|---|---|
| 추론 수 · starved 틱 | 22 · 21 / 22 · 22 / 22 · 22 | 22 · 22 / 22 · 22 |
| 첫 추론 지연 (s) | 0.68 / 0.71 / 0.69 | 0.72 / 0.69 |
| 이후 추론 지연 p50 · 최대 (s) | 0.30 · 0.33 / 0.32 · 0.34 / 0.31 · 0.32 | 0.33 · 0.33 / 0.31 · 0.34 |
| 제어 루프 본체 p50 / p99 / 최대 (ms) | 0.26 / 0.59 / 0.78 · 0.26 / 0.58 / 0.74 · 0.27 / 0.80 / 1.03 | 0.38 / 0.71 / 1.71 · 0.34 / 0.75 / 1.01 |
| 감싸기 비용 (제어 스레드) p50 / p99 (µs) | — | 6.9 / 87.8 · 6.2 / 82.6 |
| 감싸기 비용 (RTC 스레드) p50 (µs) | — | 39.5 · 35.9 |
| writer chunk 하나 쓰기 p50 (ms, 별도 스레드) | — | 71.7 · 72.4 |
| 기록 / 버림 | — | chunk 22 / 0, tick 428 / 0 (두 번 모두) · wrapper 오류 0 |
| 재현 (기록 입력 PNG · state · noise · prefix · inference_delay → 다시 계산) | — | 22 chunk 모두 기록된 original 과 차 0.0 (정규화 · ° 모두) |

- 틱 주기는 33.3 ms. 켬 때 늘어난 루프 본체 시간 p50 은 0.08–0.12 ms.
- starved 21–22 틱은 끔 · 켬 모두 첫 추론 (모델 첫 호출) 동안이다.
- 첫 시도 (on, 14:2x) 는 `diag_log.py` 끝내기 (`close`) 에서 `TypeError: 'Event' object is not callable` 로 실패했다 (writer 스레드의 `self._stop` 이 `threading.Thread._stop` 을 가림). 이름을 `_stop_ev` 로 바꿨다 (sha256 `08662d05…` → `b1425bab…`, 이전 판 `backup/diag_log.v1_08662d05.py`, 실패 기록 `harness/failed_v1/`). 제어 경로 코드는 바뀌지 않았다.
- 이 점검이 덮지 않는 것: eval_ui + `rollout_logged` 의 필터 · 로그 감싸기와 diag 감싸기가 함께 걸린 실제 경로 (harness 는 rollout_logged 를 설치하지 않음), 실제 카메라 · 직렬 통신 시간. → 3 절 실행에서 **첫 판이 끝난 뒤** 아래를 확인하고 계속한다 (Claude 가 읽기만으로 확인 가능):
  `RUN/diag/summary.json` 은 끝날 때 쓰이므로 첫 판 뒤에는 `chunks.jsonl` 줄 수 > 0, `ticks.csv` 줄 수 ≈ 판 틱 수, `debug.log` 의 추론 지연이 기존 (p50 0.34 s) 과 같은 범위인지 본다.

## 7. 예상 자원

| 항목 | 값 |
|---|---|
| GPU | d2 정책 추론 1 개 (학습 없음). A 실험 학습은 멈춰 있음 (01 문서 5 절) |
| 디스크 | harness 측정 chunk 당 ≈ 0.30 MB (PNG 2 장이 대부분). 판 30 s ≈ 45 chunk ≈ 13 MB → 12 판 ≈ 0.2–0.3 GB (+ 기존 dataset · 영상) |
| 사용자 시간 | 로딩 3 분 + 판당 (배치 ~30 s + 실행 15–40 s + 복귀) ≈ 12 판 25–35 분 |

## 8. 안전 중단

- 정상 종료: `Esc` (진행 중 판 저장 후 종료, 팔은 처음 자세로 돌아간 뒤 토크 꺼짐).
- 그 판만 버리기: `←` (다시 하기).
- 비상: `Ctrl+C` (진행 중 판은 저장 안 됨) → 그래도 위험하면 팔로워 12 V 전원을 끈다.
- diag 기록은 종료 때 (`atexit`) 마저 쓴다. Ctrl+C 로 끝나도 그때까지의 chunk 는 남는다. 프로세스를 강제 종료 (kill -9) 하면 writer 큐에 남은 기록은 잃는다.

## 9. 실행 뒤 분석 (Claude, 읽기만 · 로봇 연결 없음)

```bash
cd ~/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts
RUN1=<1 단계 폴더>; RUN2=<2 단계 폴더>
for R in $RUN1 $RUN2; do
  nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p05_replay_check.py $R/diag    # GPU: 재현 + RTC 끔 반사실 (같은 관측 · noise)
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00b_verify_run.py $R
  PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p07_new_eval_analysis.py $R      # CPU: 실행별 chunk · 틱 · 판 표
done
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p09_pilot_summary.py --runs $RUN1 $RUN2 \
  --labels U3,K1,U2,U5,K3,U6,U7,K6,U4,U1,K7,U8                                                  # → pilot/pilot_episodes.csv · pilot_summary.json (좌표는 사진 측정값만)
```

| 분석 항목 | 열 (p07 `analysis_pan/` · p09 `pilot/`) | 값 종류 |
|---|---|---|
| 최초 Raw chunk 의 Pan 목표 · 이동 비율 | first_chunk_idx29 · idx49 · gain29 · gain49 · idx49_minus_pe | 실측 (판 첫 chunk = 안내 없는 출력) |
| Raw vs RTC 뒤 chunk 차 | chunks: rtc_minus_off_exec_first/last/absmax, off_gain_idx29/49 · 판: rtc_minus_off_exec_last_abs_med | 실측 vs 반사실 (p05) |
| chunk index 30–49 에 계획된 이동 | plan_30_49_sg · plan_30_49_frac (first_chunk_ · pre_close_ 중앙) | 실측 (기록 chunk 전체) |
| 실제 실행된 index (≈ 10–29) 이동 | exec_idx_first/last · exec_move_sg · exec_move_frac | 실측 (ticks 의 꺼낸 index) |
| Pan 목표각 오차 · 방향 역전 | first_dir_ok · seam_sg/back_sg (판: seam_min · back_max · n_…) · off_seam/off_back (RTC 끔) · pan_err_at_close_sg | 실측 · 반사실 · est (pe) |
| 명령 → 서보 추종 | ticks_chain: goal_in → sent → present · 판: servo_lag_ticks · sent_minus_present_moving_p50/p95 · pan_clamp_ticks · filter_change_pan_p95 | 실측 |
| K / U 위치별 첫 접근 정확도 | pilot_episodes: group · pan_abs_err_at_close · state_t90_s · verdict · memo, pilot_summary.json (K/U 중앙) | 실측 · est |

- 판 대응: diag 의 판 번호를 console.log 의 `[eval_ui] START/SAVED/DISCARD` 순서에 맞춘다. 버린 시도는 discarded 로 표시하고 p09 에서 뺀다.
- 큐브 위치 · pe 는 start_images front 사진에서만 잰다 (`cube_coords.py`, 09 문서). U 의 '참고' 자리는 쓰지 않는다. K 판은 photo_minus_K_cm 로 이 실행의 역산을 점검하고, 2 cm 넘게 벗어난 K 판은 group K_off 로 따로 둔다.
- invalid_detection · invalid_calibration 판: pe · need · 방향 맞음 · gain · 목표 오차 열이 비고, raw chunk 이동 (first_chunk_move29/49) · RTC · 서보 열은 남는다. p09 요약은 coord_status 별로 따로 내고, n_pe_ok 가 pe 지표에 들어간 판 수다.
- valid_off_K 판의 pe 오차는 좌표 정확도가 검증되지 않은 값이다. 좌표 불확실성 (pe_sigma_coord_deg, 참고치) 과 사람 파지 산포 (pe_sigma_grasp_deg 2.15°) 를 따로 적는다.
- 학습 위치와의 거리 (dist_nearest_train_cm, n_train_within_3cm) · 최근접 K (nearest_K, dist_K_cm) 도 사진 좌표로 계산한다.
- 스크립트는 harness 기록 · 가짜 실행 폴더로 코드 경로만 시험했다 (2026-10-29). 실제 값 검증은 3.2 의 U3 판에서 처음 한다.
