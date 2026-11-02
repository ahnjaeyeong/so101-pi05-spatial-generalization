# practice_10 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/practice_10`
- dataset: `$HOME/so101_runs/practice/practice_10/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-02

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라: 이 세션은 수동 156/4600(카메라 기본값, 노랗고 초록빛)으로 녹화됨. 이후 세션은 자동 노출·자동 화이트밸런스.
- 카메라 상태 확인 (2026-10-02, 영상 측정): 10개 에피소드 모두 처음·중간·끝 프레임이 156/4600 화면과 같음 (흰 탁자 B/G front 0.50–0.51, wrist 0.53–0.57; 자동이면 ≈1.0). 세션 중간에 바뀐 판 없음.
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-02 15:57 · 새 녹화 <!-- run:20261002_155718 -->

**녹화 전 점검**
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=1, exposure_time_absolute=156, white_balance_automatic=0, white_balance_temperature=4600 — 수동 고정, 기준값과 같음
- /dev/cam_wrist: auto_exposure=1, exposure_time_absolute=156, white_balance_automatic=0, white_balance_temperature=4600 — 수동 고정, 기준값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/practice_10 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice10 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=30 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice10 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=30 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/practice_10/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261002_155718.log`

**결과** <!-- results:20261002_155718 -->
- 종료: ⚠ 비정상 (코드 1) — 수동 후처리 · 후처리 2026-10-02 16:07
- repo_id: `oxr/so101_cubebox_practice10` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=30 · reset_time_s=120
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-10-02 15:59 · 새 녹화 <!-- run:20261002_155906 -->

**녹화 전 점검**
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=1, exposure_time_absolute=156, white_balance_automatic=0, white_balance_temperature=4600 — 수동 고정, 기준값과 같음
- /dev/cam_wrist: auto_exposure=1, exposure_time_absolute=156, white_balance_automatic=0, white_balance_temperature=4600 — 수동 고정, 기준값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/practice_10 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice10 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=30 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice10 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=30 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/practice_10/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261002_155906.log`

**결과** <!-- results:20261002_155906 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-02 16:07
- repo_id: `oxr/so101_cubebox_practice10` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=30 · reset_time_s=120
- 에피소드: 이번 10개 (episode 0–9) · 전체 10개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 703 | 23.4 | 29.92 | 0/702 |
| 001 | 878 | 29.3 | 29.91 | 0/877 |
| 002 | 763 | 25.4 | 29.92 | 0/762 |
| 003 | 607 | 20.2 | 29.93 | 0/606 |
| 004 | 523 | 17.4 | 29.92 | 0/522 |
| 005 | 562 | 18.7 | 29.91 | 0/561 |
| 006 | 700 | 23.3 | 29.91 | 0/699 |
| 007 | 576 | 19.2 | 29.92 | 0/575 |
| 008 | 632 | 21.1 | 29.92 | 0/631 |
| 009 | 645 | 21.5 | 29.91 | 0/644 |

```
Cadence summary — whole run, 11 episodes · target 30 Hz (33.3 ms budget per tick): 6682 ticks, 6671 judged
  effective cadence: 29.92 Hz over 223.0 s measured
  ticks over the 33.3 ms work budget: 0/6671 (0.0%) — work mean 2.7 ms, worst 18.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 94
  loop-body steps (share of measured work):
    observe      mean   1.22 ms · worst  15.84 ms ·  44.9% of work · 6682 calls
    process_obs  mean   0.03 ms · worst   1.46 ms ·   1.1% of work · 6682 calls
    teleop       mean   1.07 ms · worst   4.91 ms ·  39.5% of work · 6682 calls
    send         mean   0.20 ms · worst   3.25 ms ·   7.3% of work · 6682 calls
    record       mean   0.16 ms · worst   2.28 ms ·   5.7% of work · 6682 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
| 004 | | |
| 005 | | |
| 006 | | |
| 007 | | |
| 008 | | |
| 009 | | |

## 학습 기록

### 2026-10-02 16:51 · π0.5 연습 학습 `train/pi05_2k` (동작 확인용, 성능 목표 아님)

**사전 점검**
- 녹화 프로세스·twin_ws 컨테이너 없음 (녹화와 겹치지 않음)
- `~/so101-env`: lerobot 0.6.2, torch 2.11.0 (CUDA 13.0), transformers 5.5.4, scipy 1.18.1 — `lerobot.policies.pi05` import OK, 설치·업데이트 안 함
- HF 로그인 `ahnjaeyeong`. `lerobot/pi05_base` (공개, 14.5 GB) 접근 OK. 토크나이저 `google/paligemma-3b-pt-224` (gated·manual) 접근 OK → 라이선스 승인돼 있음
- GPU: NVIDIA Thor, 통합 메모리 122 GiB (시작 때 여유 113 GiB), bf16 지원
- dataset stats.json 에 q01/q99 있음 (pi05 QUANTILES 정규화에 필요)

**명령** (`train/run_pi05_2k.sh`, 로그 `train/pi05_2k.log`, 메모리 기록 `train/pi05_2k.mem.log`)
```bash
PYTHONDONTWRITEBYTECODE=1 $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubebox_practice10 \
  --dataset.root=$HOME/so101_runs/practice/practice_10/dataset \
  --policy.type=pi05 --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/practice/practice_10/train/pi05_2k --job_name=pi05_2k \
  --batch_size=4 --steps=2000 --log_freq=50 --save_freq=2000 --num_workers=4 \
  --wandb.enable=false
```
- 학습 파라미터 4.14B (전부 학습). lr 스케줄 자동 축소: warmup 1000→66, decay 30000→2000 (peak 2.5e-5 → 2.5e-6)
- 2000 스텝 × 배치 4 = 8000 샘플 ≈ 1.21 epoch (6589 프레임)

**결과**
- 종료: 정상 ("End of training"), Traceback 없음. 경고: vision patch_embedding 키 2개 "might need handling" (키는 모두 로드됨, "All keys loaded successfully")
- loss: step 50 0.139 → 100 0.076 → 250 0.053 → 500 0.040 → 1000 0.034 → 2000 0.020 (처음 5회 평균 0.080, 마지막 5회 평균 0.020) — 줄어듦
- 시간: 전체 16:51:31–18:16:34 (1시간 25분) = 모델 생성·pi05_base 내려받기 약 4분 20초 + 학습 1시간 20분 36초 (≈2.36 s/step) + 저장 약 45초
- 메모리: lerobot 표시 mem_gb 36.99, nvidia-smi 프로세스 최대 39.3 GB. 시스템 전체 사용량(통합 메모리) 학습 중 약 53 GB, 체크포인트 저장 때 최대 66 GB (시작 전 약 6 GB)
- 출력 `train/pi05_2k/checkpoints/002000/` (`last` → 002000), 전체 23 GB
  - `pretrained_model/`: config.json (type pi05, bfloat16, 입력 state·front·wrist, 출력 action), model.safetensors (9.4 GB, 텐서 813개), policy_preprocessor.json + normalizer safetensors, policy_postprocessor.json + unnormalizer safetensors (action·state q01/q99 포함), train_config.json, tokenizer/
  - `training_state/`: optimizer_state 15 GB, scheduler·rng·step (재개용)
- 허브 업로드 없음 (push_to_hub=false). 내려받은 모델은 `~/.cache/huggingface/hub` (14 GB)

### 2026-10-06 · pi05_2k 오프라인 확인 (팔 연결 없음, 데이터셋 읽기만)

- 스크립트: `eval/offline_eval_pi05_2k.py` (`~/so101-env`, PYTHONDONTWRITEBYTECODE=1), 그래프 `eval/plot_pi05_2k.py` (시스템 python3 — venv 에 matplotlib 없음, 설치 안 함)
- 추론 경로는 `lerobot-rollout --inference.type=sync` 와 같음: prepare_observation_for_inference → preprocessor → predict_action_chunk → postprocessor. bf16, seed 0
- 방식: 에피소드마다 50프레임 간격으로 그 시점 녹화 관측을 넣어 chunk(50)를 받고 이어 붙여 녹화 action 과 비교 (open-loop). **두 판 모두 학습에 쓴 에피소드라 일반화 성능이 아님**
- 결과 파일: `eval/pi05_2k_offline.json`, `.npz`, `pi05_2k_ep001_actions.png`, `pi05_2k_ep004_actions.png`, `pi05_2k_error_vs_horizon.png`, 로그 `offline_eval_pi05_2k.log`

**관절별 평균 오차 (°, 그리퍼는 0–100) — 괄호는 "chunk 시작 자세 유지" 기준**

| ep | shoulder_pan | shoulder_lift | elbow_flex | wrist_flex | wrist_roll | gripper | 팔 5관절 |
|---|---|---|---|---|---|---|---|
| 001 (878프레임, 18 chunk) | 2.59 (7.77) | 2.63 (5.91) | 2.87 (6.28) | 0.42 (0.69) | 3.48 (6.72) | 1.73 (4.99) | 2.40 |
| 004 (523프레임, 11 chunk) | 2.29 (11.77) | 2.05 (11.81) | 2.31 (6.59) | 0.73 (1.34) | 4.01 (5.62) | 2.26 (8.13) | 2.28 |

- chunk 안 위치별: 첫 스텝 오차 ≈0.9° → 50번째 3–4° (`pi05_2k_error_vs_horizon.png`)
- 최대 오차: wrist_roll 46°(ep1)·40°(ep4), shoulder_lift 22–32° — 동작 시작 시점이 늦거나 이른 구간
- chunk 경계 점프(한 프레임 사이 최대 관절 변화): ep1 최대 24.8°, ep4 36.4°·42.7°. chunk 안 프레임 간 변화 p99 3–6°, 녹화 action p99 2.6–3.8°

**추론 시간 (Thor, warm, 58회)**
- chunk 길이 50 (chunk_size=50, n_action_steps=50 → 30 Hz 에서 1.67초분), num_inference_steps=10
- 1회 전체: 평균 212.8 ms, p95 220.4 ms, 최대 229.9 ms (모델 210.8 / 전처리 1.7 / 후처리 0.3)
- 첫 호출(워밍업): 698 ms. GPU 최대 할당 9.5 GB

**30 Hz 판단**
- 루프 예산 33.3 ms 대비 추론 ≈213 ms (6.4배). sync 모드는 chunk 가 비는 틱에서 추론이 루프를 막음 → 1.67초마다 약 0.21초(≈6–7틱) 명령 정지 = 멈칫거림 생김. 첫 chunk 는 약 0.7초.
- 거기에 chunk 경계 점프(오프라인에서 최대 25–43°)가 겹치면 정지 뒤 큰 한 번 이동이 생길 수 있음. 녹화는 max_relative_target=None.
- 대안: `--inference.type=rtc` (pi05 supports_rtc=True; 추론을 별도 스레드에서 돌리고 이전 chunk 와 이어 붙임, 0.21초 ≈ 7틱 지연이 execution_horizon 기본 10 안에 들어감) + 첫 실물은 `--robot.max_relative_target` 로 한 틱 이동량 제한 권장
- guided RTC 추론 시간 (`eval/rtc_timing_pi05_2k.py`, `eval/pi05_2k_rtc_timing.json`): 평균 308.5 ms, 최대 329.1 ms (23회, 첫 호출 717 ms) → 지연 10틱 = 기본 execution_horizon 10 과 같음 → 실물은 `--inference.rtc.execution_horizon=20` 로. queue_threshold 30(1초분) > 지연 10틱이라 큐가 비지 않음.
- 실물 명령 옵션은 lerobot 파서로 오프라인 확인함 (팔 연결 없음). 카메라는 학습 데이터와 같은 수동 156/4600 으로 맞춰서 평가.

### 2026-10-06 09:27 · 첫 실물 rollout (RTC guided, horizon 20, max_relative_target 8, interactive, 1회 20초)
- 로그: `eval/rollout_pi05_2k_20261006_092753.log`. 사용자 관찰: 팔이 약간 흔들흔들
- 루프: 599틱 / 20.0초, 29.92 Hz, 33.3 ms 넘은 틱 0 (작업 평균 2.6 ms, 최악 5.0 ms), 페이싱 밀림 2틱
- 행동 없음(추론 대기) 26틱 ≈ 0.87초 — "no warmup needed" 라 첫 추론(콜드 ≈0.72초)이 /start 뒤에 돌아서 시작 직후로 추정 (로그로 위치 확인 불가)
- RTC 추론 지연·실행 중 경고는 로그에 없음: 지연은 DEBUG 로만 찍히고, interactive 모드는 실행 중 WARNING 이하를 끔
- 경고: 종료 후 처음 자세로 돌아가는 중 shoulder_pan 제한 경고 4번 (명령과 실제 위치 차이 > 8°)
- 오프라인 비교(흔들림 지표, `eval/analyze_rollout.py`): 사람 조작 데이터 hf_rms 약 0.2°, 방향 바뀜 0.1–0.3회/초.
  정책 open-loop 출력은 shoulder_pan 0.55–0.79°·1.7–2.3회/초, wrist_roll 0.89–1.82°·2.6–2.8회/초.
  chunk 안만 보면 진폭은 0.16–0.21°(pan)로 줄지만 방향 바뀜은 pan 1.1–1.7, wrist_roll 2.1회/초로 남음
  → 흔들림 크기는 chunk 전환에서, 잔떨림은 정책 출력 자체(pan·wrist_roll)에서 온다는 가설
- 다음부터 `eval/run_rollout.sh <tag> <추론 옵션>` 로 실행: episodic 녹화(관측·정책 action) + DEBUG 로그(`rollout_logged.py`) + 자동 분석. 결과 `eval/rollouts/<시각>_<tag>/`. 기준값은 `eval/reference_teleop/analysis.json`
- 2026-10-06 09:42·09:47·09:51 run_rollout.sh 3회 실패 (팔 연결 직후, 움직이기 전): lerobot-rollout 은 녹화 repo 이름이 `rollout_` 로 시작해야 함 → `oxr/rollout_practice10_pi05_2k_<tag>` 로 고침. 실패 폴더 `eval/rollouts/20261006_0942*·0947*·0951*` 에는 로그만 있음

### 2026-10-06 09:56–10:09 · 비교 실행 3개 (episodic, 판 20초 × 2, 리셋 20초, max_relative_target 8)
- `rollouts/20261006_095635_rtc_h20`: 1판 녹화 후 리셋 12초째(10:00:00)에 종료 → **0판 저장**. episodic 은 리셋이 끝난 뒤에 판을 저장하는데, Ctrl+C 로 끊겨 그 판이 지워짐 (q/Esc 는 저장하고 끝남)
- `rollouts/20261006_100015_sync`, `rollouts/20261006_100443_rtc_h20_q20`: 2판씩 저장
- **시작 자세가 학습 데이터와 다름**: 연결 때 자세 ≈ [pan 80–83, lift −7…−5, elbow 49–51, wrist_flex 63–64, roll 25, gripper 2–3] vs 학습 시작 평균 [75, 43, 6, 98, 1.5, 0.8] → 정책이 본 적 없는 자세에서 출발. lerobot-rollout 은 연결 순간 자세를 "처음 자세"로 잡고 리셋도 거기로 돌아감 (2번째 판 시작 자세가 1번째와 1° 이내). 10:20 읽기 전용 확인에서도 같은 자세 (lift 40°, elbow 38°, wrist_flex 27°, roll 12° 벗어남). 보정 파일은 9/29 이후 안 바뀜
- 판 길이: 20초 끝 시점에 그리퍼가 열린 채(49–62) 작업 중간. 학습 데이터는 놓기까지 14–24초, 판 17–29초
- RTC 실측 지연: 평균 494 ms, 최대 520 ms (오프라인 308 ms보다 느림; 녹화·카메라와 동시) → 지연 16틱, horizon 20 안
- 흔들림 지표 (판 평균, pan/lift/elbow/w_flex/w_roll/gripper):
  - 사람 조작: action 방향 바뀜 0.18/0.21/0.30/0.14/0.12/0.19 회/초, 팔로워(state) 0.16/0.22/0.23/0.13/0.12/0.14
  - sync: action 1.87/0.97/1.38/0.39/2.82/1.20, state 0.27/0.27/0.30/0.45/0.36/0.60. 주기 50프레임(자기상관 0.51·0.35) = chunk 길이. 추론 틱 최악 353 ms, 실효 25 Hz
  - RTC q20: action 1.48/0.96/1.40/0.42/1.94/1.14, state 0.42/0.52/0.34/0.29/0.50/0.52. 주기 30프레임(0.27·0.33) = chunk 전환 간격. 추론 대기 38틱(판마다 첫 추론), 제한 경고 97건
  → 흔들림 주기가 chunk 전환 주기와 겹침 + 정책 출력 자체의 잦은 방향 바뀜(pan·wrist_roll ~2회/초). 팔로워는 사람 조작 때보다 2–3배 자주 방향을 바꿈
- 고친 것: `run_rollout.sh` 기본 판 45초·리셋 60초(N_EP/EP_S/RESET_S 로 변경), Ctrl+C 에도 로그 유지·분석 실행. 시작 자세는 사용자 판단으로 평가에 상관없음 → `pose_check.py --yes` 로 `pose_check.txt` 에 기록만 하고 묻지 않음

### 2026-10-06 · 카메라·반응 속도 확인 (오프라인, 읽기만)
사용자 관찰: 빨간 큐브(종이)를 인지는 하는데 반응이 느림. 건드려서 자리를 벗어나도 원래 자리를 보고 허우적댐.
- 카메라 경로 (`eval/camera_check.py`, `cam_ep*_sheet.jpg`): 설정은 지금도 학습 때와 같은 수동 156/4600. front·wrist 키 바뀜 없음.
  팔이 움직이는 중 wrist 같은 프레임 반복 0–8회/판 (학습 데이터 14–18회) → 프레임이 멈추거나 늦게 오는 문제는 안 보임.
  wrist 평균 색이 학습보다 밝고 파람 — 설정은 같아서 보이는 내용(가까운 흰 탁자·큐브) 차이로 판단
- 화면 사용 여부 (`eval/vision_check.py`, `vision_check.json`): 움직임 시작 순간(팔 자세 거의 같음)에 화면만 바꿔 50프레임 뒤 예측 비교.
  회색 화면 → shoulder_pan 예측 30° 바뀜, 다른 판 화면 → 21° 바뀜 (판 사이 실제 차이 19°). 다른 판 화면을 넣으면 pan 예측이 그 판 쪽에 더 가까운 경우 63%.
  → 화면을 보고 방향을 정함 (단, 학습에 쓴 판이라 처음 보는 위치에 대한 일반화는 아님)
- rollout q20 ep0 화면: 2.5초부터 wrist 화면에 큐브가 손가락 사이에 있는데, 그리퍼가 24–55 사이를 여닫기만 하고 잡지 못함.
  팔이 덜 내려감 (lift 15–27·elbow −12~−22, 학습 때 잡는 순간 lift 38–46·elbow −36~−42)
- 반응 지연(계산): 실행되는 action 은 몇 틱 전 화면으로 만든 것. 실측 RTC 지연 15틱(494 ms) 기준
  RTC q30(기본): 0.5–1.2초 전 화면 / q20: 0.5–1.5초 / sync: 0–1.7초(+추론 동안 0.2–0.35초 정지). 카메라 자체 지연은 별도(측정 안 함)
- flow 단계 수 (`eval/steps_timing.py`, `steps_timing.json`, 오프라인): 10단계 sync 225 ms·RTC 324 ms, 팔 5관절 오차 2.61° /
  5단계 sync 161 ms·RTC 208 ms, 오차 2.39° → 5단계로 줄여도 정확도 손해 없음. `--policy.num_inference_steps=5` 파서 확인
- 2026-10-06: `run_rollout.sh` 판·리셋 기본 3600초(사실상 제한 없음) — 끝나면 n/→ 로 넘김, q/Esc 로 저장 후 종료

### 2026-10-06 10:16–10:55 · 추가 실행 3개 (정리 문서: `~/so101_runs/docs/practice_10_pi05_2k.md`)
- `rollouts/20261006_101657_rtc_h20` (45초×2, 2판 저장): 못 넣음. RTC 지연 497/570 ms, 팔 방향 바뀜 pan 0.85·w_roll 0.82회/초, 제한 경고 426
- `rollouts/20261006_103946_rtc_fast` (5단계·q40, 45초): 리셋 중 종료 → 0판
- `rollouts/20261006_104919_rtc_fast` (5단계·q40, 제한 없음): 1판 107초, **큐브 상자 안**. RTC 지연 318/370 ms, 팔 방향 바뀜 pan 0.23·w_roll 0.54회/초, 고주파 pan 0.16°(사람 조작 수준). 2판째는 리셋 중 → 두 번 눌림 → 0프레임 판 저장 에러로 종료
