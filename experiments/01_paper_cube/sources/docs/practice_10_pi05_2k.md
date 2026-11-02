# practice_10 · π0.5 연습 학습과 실물 평가 정리

- 기간: 2026-10-02 (학습) ~ 2026-10-06 (오프라인 확인·실물 평가)
- 세션: `practice/practice_10` · 데이터 `oxr/so101_cubebox_practice10` · 체크포인트 `train/pi05_2k/checkpoints/002000`
- 목적: 성능이 아니라 **학습 → 실물 실행까지 끝까지 도는지** 확인
- 자세한 기록(명령 원문, 시각별 로그): [`practice/practice_10/notes.md`](../practice/practice_10/notes.md)

## 요약
- **학습은 끝까지 돌았다.** 2000스텝, 1시간 25분, loss 0.139 → 0.020. 체크포인트(설정·가중치·정규화 파일)도 모두 저장됐다.
- **오프라인에서는 녹화된 동작을 꽤 따라 한다.** 팔 5관절 평균 오차 2.3–2.4°. 다만 두 판 모두 학습에 쓴 데이터라 일반화 성능은 아니다.
- **실물에서는 7번 실행해 큐브를 상자에 넣은 건 1번이다.** `rtc_fast` 설정(flow 5단계 + RTC 재계획 기준 40, 시간 제한 없음)으로 107초 만에 넣었다.
- **흔들림은 동작 묶음(chunk) 전환 주기와 겹친다.** 추론을 빠르게 하고 자주 재계획한 `rtc_fast`에서 팔 흔들림이 사람 조작 수준으로 줄었다. 단, 1판뿐이라 확정은 아니다.
- **카메라 경로는 정상이고, 정책은 화면을 보고 방향을 정한다.** 반응이 느린 건 구조적인 지연 때문이다. 팔이 실행하는 동작은 0.5–1.5초 전 화면으로 만든 것이다.
- **잡기가 약하다.** 큐브가 손가락 사이에 있어도 팔이 덜 내려가 그리퍼만 여닫는 경우가 많다. 종이 큐브가 밀리면 다시 잡지 못한다. 데이터가 10판뿐인 게 가장 큰 원인으로 보인다.

## 사용자 평가 (2026-10-06, 실물 실행을 직접 보고)

### 평가
- 빨간색 박스라는 것을 인지하고 있음.
- 빨간색 박스를 잡으면 갈색 박스에 넣는 것은 잘함.

### 제한사항
- 빨간색 박스가 너무 가벼워서 위치를 벗어나는 바람에 잡는 데 어려움이 있음.
- 빨간색 박스를 집는 데까지 시간이 걸리기 때문에 시간 제한을 두면 안 됨.
- 학습할 때 잡는 세기를 잘 조절해야 할 것 같음.

관련 기록:
- 화면을 보고 방향을 정하는지 확인한 결과는 3장의 "화면을 보는지"에 있다.
- 잡기 실패 장면과 반응 지연은 4장의 "카메라·반응 속도"에 있다.
- 판·리셋 시간은 이 평가에 따라 기본 3600초(사실상 제한 없음)로 바꿨다.

## 1. 데이터
- 10판, 판당 17–29초(평균 22초), 30 fps. 카메라 front·wrist 640x480.
- 카메라는 수동 156/4600(노랗고 초록빛)으로 녹화됐다. 이 정책을 평가할 때도 같은 값으로 맞췄다.
- 큐브 시작 위치·각도는 판마다 다르고, 상자 위치는 같다 (`practice_10/qa/overview_front_first.jpg`).
- 사람이 큐브를 놓기까지 14–24초 걸렸다.

## 2. 학습
```bash
PYTHONDONTWRITEBYTECODE=1 $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubebox_practice10 \
  --dataset.root=$HOME/so101_runs/practice/practice_10/dataset \
  --policy.type=pi05 --policy.pretrained_path=lerobot/pi05_base --policy.push_to_hub=false \
  --policy.dtype=bfloat16 --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/practice/practice_10/train/pi05_2k --job_name=pi05_2k \
  --batch_size=4 --steps=2000 --log_freq=50 --save_freq=2000 --num_workers=4 --wandb.enable=false
```

| 항목 | 값 |
|---|---|
| 학습 파라미터 | 4.14B (전부 학습) · 2000스텝 × 배치 4 ≈ 1.2 epoch |
| loss | 0.139(50) → 0.053(250) → 0.040(500) → 0.034(1000) → 0.020(2000) |
| 시간 | 1시간 25분 (모델 준비·내려받기 4분 + 학습 1시간 20분 36초, 2.36 s/step) |
| 메모리 | GPU 37–39 GB, 시스템 전체 최대 66 GB (Thor 통합 메모리 122 GB) |
| 결과 크기 | 23 GB (그중 15 GB는 이어 학습용 `training_state/optimizer_state.safetensors`) |

- 사전 점검: pi05 import 정상. HF 로그인돼 있고 `google/paligemma-3b-pt-224` 라이선스도 승인돼 있었다. `~/so101-env`에는 아무것도 설치하지 않았다.
- 메모리가 부족할 때 쓸 수 있는 옵션: `--policy.train_expert_only=true`, `--policy.freeze_vision_encoder=true`, 작은 배치 + `--accelerator.gradient_accumulation.steps`.

## 3. 오프라인 확인 (팔 연결 없음)

### 녹화 동작과 비교
에피소드 1·4에서 50프레임마다 chunk를 받아 이어 붙이고 녹화된 action과 비교했다.

| 관절 평균 오차 | pan | lift | elbow | w_flex | w_roll | gripper |
|---|---|---|---|---|---|---|
| ep 1 | 2.6° | 2.6° | 2.9° | 0.4° | 3.5° | 1.7 |
| ep 4 | 2.3° | 2.1° | 2.3° | 0.7° | 4.0° | 2.3 |

- chunk 첫 스텝 오차는 0.9°이고, 50번째에서 3–4°까지 커진다.
- chunk 경계에서 값이 한 번에 크게 튄다(최대 25–43°). 녹화 동작은 한 프레임에 최대 3–4°만 바뀐다.
- 그래프: [ep1](../practice/practice_10/eval/pi05_2k_ep001_actions.png) · [ep4](../practice/practice_10/eval/pi05_2k_ep004_actions.png) · [chunk 안 위치별 오차](../practice/practice_10/eval/pi05_2k_error_vs_horizon.png)

### 추론 시간 (Thor, chunk 50 = 1.67초분)

| 방식 | flow 10단계 | flow 5단계 |
|---|---|---|
| sync (오프라인) | 213–225 ms | 161 ms |
| guided RTC (오프라인) | 308–324 ms | 208 ms |
| guided RTC (실물, 녹화와 함께) | 494–497 ms (최대 570) | 318 ms (최대 370) |
| 팔 5관절 오차 | 2.61° | 2.39° |

- 5단계로 줄여도 정확도 손해가 없다.
- 첫 호출(워밍업)은 약 0.7초 걸린다.

### 화면을 보는지
움직임이 시작되는 순간에는 팔 자세가 판마다 거의 같아서, 큐브 위치는 화면으로만 알 수 있다. 이때 화면만 바꿔서 예측을 비교했다 (`eval/vision_check.json`).
- 회색 화면을 넣으면 shoulder_pan 예측이 30° 바뀐다.
- 다른 판의 화면을 넣으면 21° 바뀌고, 63%는 그 판 쪽으로 따라간다.
- 따라서 화면을 보고 방향을 정한다. 단, 학습에 쓴 위치에서만 확인한 결과다.

## 4. 실물 평가

### 실행 방법
`practice/practice_10/eval/run_rollout.sh <tag> <추론 옵션>` 하나로 아래를 모두 한다.
- `lerobot-rollout --strategy.type=episodic`으로 실행하면서 관측·정책 action을 dataset으로 녹화한다.
- RTC 지연과 제한 경고를 DEBUG 로그로 남긴다 (`rollout_logged.py`).
- 끝나면 흔들림 지표와 그래프를 자동으로 만든다.

공통 설정은 `max_relative_target=8`, 30 Hz, 카메라 수동 156/4600이다. 판·리셋 시간은 기본 3600초라 사실상 제한이 없다.

키는 실행한 터미널에서 누른다:
- `n` / →: 판 또는 리셋을 끝내고 다음으로 넘어간다.
- `r` / ←: 이번 판을 다시 한다.
- `q` / `Esc`: 이번 판을 저장하고 종료한다.

```bash
cd $HOME/so101_runs/practice/practice_10/eval
./run_rollout.sh rtc_fast --policy.num_inference_steps=5 --inference.type=rtc \
  --inference.rtc.execution_horizon=20 --inference.queue_threshold=40
```

### 실행 기록 (2026-10-06)

| 시각 | tag | 설정 | 판 길이 | 저장 | 결과 |
|---|---|---|---|---|---|
| 09:27 | (대화식) | RTC, horizon 20 | 20초 | 녹화 안 함 | 약간 흔들흔들 |
| 09:42–09:51 | — | — | — | 0 | 녹화 이름 규칙(`rollout_` 접두어)으로 시작 실패 |
| 09:56 | rtc_h20 | RTC, horizon 20, q30 | 20초 | 0 | 리셋 중 Ctrl+C로 그 판이 지워짐 |
| 10:00 | sync | sync | 20초 ×2 | 2 | 못 넣음 |
| 10:04 | rtc_h20_q20 | RTC, horizon 20, q20 | 20초 ×2 | 2 | 못 넣음 (큐브 위에서 그리퍼만 여닫음) |
| 10:16 | rtc_h20 | RTC, horizon 20, q30 | 45초 ×2 | 2 | 못 넣음 (2판째 시작 때 상자 위치 바뀜) |
| 10:39 | rtc_fast | 5단계, horizon 20, q40 | 45초 | 0 | 리셋 중 종료로 지워짐 |
| 10:49 | rtc_fast | 5단계, horizon 20, q40 | 제한 없음 | 1 | **107초에 큐브가 상자 안**. 2판째는 → 두 번 눌림으로 0프레임 에러 |

판마다 처음과 끝 front 화면은 각 실행 폴더의 `start_end_front.jpg`에 있다.

### 흔들림 지표 (판 평균)
- `방향 바뀜`: 1초에 움직임 방향이 바뀐 횟수(작은 떨림은 제외).
- `고주파`: 0.3초 이동평균에서 벗어난 정도의 RMS.
- 둘 다 실제 팔(state) 기준이다.

| 실행 | 방향 바뀜 pan / w_roll (회/초) | 고주파 pan / gripper | RTC 지연 평균/최대 | 8° 제한 경고 |
|---|---|---|---|---|
| 사람 조작 (학습 데이터) | 0.16 / 0.12 | 0.20 / 0.33 | — | — |
| sync (20초×2) | 0.27 / 0.36 | 0.20 / 0.20 | (추론 틱 최악 353 ms, 실효 25 Hz) | 41 |
| rtc_h20_q20 (20초×2) | 0.42 / 0.50 | 0.28 / 0.44 | 494 / 520 ms | 97 |
| rtc_h20 (45초×2) | 0.85 / 0.82 | 0.50 / 0.65 | 497 / 570 ms | 426 |
| **rtc_fast (107초×1)** | **0.23 / 0.54** | **0.16 / 0.37** | **318 / 370 ms** | 107 |

- 흔들림 주기가 chunk 전환 주기와 겹친다. sync는 50프레임, q20은 30프레임 간격이다.
- 정책이 내는 명령(action) 자체도 pan·wrist_roll에서 1초에 2–4번 방향을 바꾼다. 사람 조작은 0.1–0.3번이다.
- 주의: 판 길이와 판 수가 달라서 엄밀한 비교는 아니다. `rtc_fast`는 1판뿐이다.

### 카메라·반응 속도
- 카메라 경로는 정상이다. 설정이 학습 때와 같고 front·wrist가 바뀌지 않았다. 움직이는 중 wrist 프레임 반복도 판당 0–8회로 학습 데이터(14–18회)보다 적다.
- 반응 지연은 계산상 이렇다. 실행되는 동작은 아래 시간만큼 전의 화면으로 만든 것이다.
  - RTC q30: 0.5–1.2초
  - RTC q20: 0.5–1.5초
  - sync: 0–1.7초, 추론하는 동안 0.2–0.35초 정지
  - rtc_fast(지연 약 10틱, 계속 재계획): 약 0.3–0.7초
- 종이 큐브가 밀려도 이 시간 동안은 원래 자리로 가는 계획을 계속 실행한다.
- 잡기 실패 장면(rtc_h20_q20 ep0)에서는 큐브가 손가락 사이에 있는데 팔이 덜 내려갔다. lift 15–27·elbow −12~−22였고, 학습 때 잡는 순간은 lift 38–46·elbow −36~−42였다. 그 상태로 그리퍼만 여닫았다.

## 5. lerobot-rollout 사용 시 주의 (0.6.2)
- 녹화 repo 이름은 `rollout_`로 시작해야 한다. 이 검사는 팔을 연결한 뒤에 돌아서, 파서 검사로는 미리 못 잡는다.
- `--interactive=true`는 실행 중 WARNING 이하 로그를 모두 끈다. RTC 지연은 DEBUG 로그로만 찍힌다. 그래서 `rollout_logged.py`로 DEBUG 파일을 따로 남긴다.
- episodic은 **리셋이 끝난 뒤에** 판을 저장한다. 리셋 중 `Ctrl+C`를 누르면 그 판이 지워지니, 끝낼 때는 `q`/`Esc`를 누른다.
- 리셋 중 → 를 두 번 누르면, 두 번째 입력이 다음 판을 바로 끝낸다. 그 판은 0프레임이 되고 저장 단계에서 에러가 난다. 한 번만 누른다.
- RTC는 워밍업 없이 시작한다. 그래서 판마다 첫 추론 동안 약 0.8초(23–38틱) 명령이 없다.
- `max_relative_target`은 현재 위치 기준으로 목표를 자른다. 팔이 명령보다 8° 넘게 뒤처지면 경고가 나온다.
- 처음 자세는 연결 순간의 자세다. 판 사이 리셋도 그 자세로 1초 동안 돌아간다.

## 6. 다음 할 일
1. `rtc_fast` 설정으로 여러 판을 더 돌려 성공률과 흔들림을 확인한다. 큐브를 일부러 밀었을 때 다시 따라가는지도 본다.
2. 데이터를 늘린다.
   - 큐브 위치를 더 다양하게 둔다.
   - 밀린 큐브를 다시 잡는 장면을 넣는다.
   - 잡을 때 끝까지 내려가는 장면을 충분히 넣는다.
   - 수십 판 단위로 모아서 다시 학습한다.
3. 카메라 설정을 정한다. 이후 세션은 자동 노출·자동 화이트밸런스로 녹화하기로 했다 (`camera_settings.md`). 그 데이터로 학습한 정책은 자동 설정에서 평가한다.
4. 필요 없으면 지운다 (지금은 남겨 둠).
   - 저장된 판이 없는 실행 폴더 5개(09:42, 09:47, 09:51, 09:56, 10:39)
   - 이어 학습용 optimizer 상태 15 GB

## 7. 파일 위치 (`practice/practice_10/` 기준)

| 파일 | 내용 |
|---|---|
| `notes.md` | 세션 전체 기록 (학습 명령, 점검, 각 실행 분석) |
| `train/pi05_2k/` | 학습 결과 · `train/pi05_2k.log` 학습 로그 · `train/run_pi05_2k.sh` 학습 명령 |
| `eval/run_rollout.sh` | 실물 평가 + 녹화 + 분석 실행 |
| `eval/rollout_logged.py` | lerobot-rollout 래퍼 (DEBUG 로그 파일) |
| `eval/analyze_rollout.py`, `eval/plot_rollout.py` | 흔들림 지표 계산·그래프 |
| `eval/pose_check.py` | 팔 자세 읽기만 해서 기록 |
| `eval/offline_eval_pi05_2k.py`, `eval/plot_pi05_2k.py` | 오프라인 action 비교 |
| `eval/rtc_timing_pi05_2k.py`, `eval/steps_timing.py` | 추론 시간 측정 |
| `eval/camera_check.py`, `eval/vision_check.py` | 카메라 프레임 점검, 화면 사용 여부 |
| `eval/rollouts/<시각>_<tag>/` | 실행별 console.log, debug.log, dataset/, analysis.json, 그래프, start_end_front.jpg |
| `eval/reference_teleop/` | 사람 조작(학습 데이터) 기준 지표 |
