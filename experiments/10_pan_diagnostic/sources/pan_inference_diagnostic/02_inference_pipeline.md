# 02 추론 경로 — 정책 입력에서 서보 명령까지 (d2 020000 실물 실행)

작성 2026-10-29. 코드 위치는 설치된 lerobot 0.6.2 (`~/so101-env/lib/python3.12/site-packages/lerobot/`, 이하 `lr/`) 와 `d2/eval/` 기준이다.
시간 값은 세 가지로 나눠 적는다: **[설정]** 설정값으로 계산, **[로그]** 기존 실물 로그에서 측정 (`tables/p01_*`, `p02b_timing.json`), **[코드]** 코드에서 도출 (기록 없음).

## 1. 실행 경로

| 단계 | 스레드 | 내용 | 위치 |
|---|---|---|---|
| 실행기 | — | `run_rollout.sh` → `rollout_logged.py` (lerobot-rollout 를 감쌈) 또는 `eval_ui.py --child` (같은 rollout_logged.install 을 import) | `d2/eval/run_rollout.sh:43-67`, `~/so101_boxpick/scripts/eval_ui.py:143-153` |
| 정책 적재 | main | `PI05Policy.from_pretrained`, RTC 면 `policy.config.rtc_config = cfg.inference.rtc` + `init_rtc_processor()` | `lr/rollout/context.py:289, 348-357` |
| 관측 | control | `robot.get_observation()`: `sync_read("Present_Position")` 후 카메라마다 `read_latest()` (백그라운드 스레드가 받아 둔 최신 프레임, 나이 ≤ 500 ms 만 허용) | `lr/robots/so_follower/so_follower.py:204-226`, `lr/cameras/opencv/camera_opencv.py:585-611` |
| 관측 전달 | control | `robot_observation_processor` → `engine.notify_observation(obs)` (최신 관측 하나만 보관, 덮어씀) | `lr/rollout/strategies/core.py:177-178`, `lr/rollout/inference/rtc.py` notify_observation |
| 추론 시작 조건 | RTC | `queue.qsize() <= queue_threshold` 일 때. 그때 보관된 최신 관측을 씀 | `rtc.py` `_rtc_loop` |
| delay 추정 | RTC | `inference_delay = ceil(LatencyTracker.max() × fps)`. tracker 는 스레드 시작 후 첫 추론 뒤 reset, 이후 세션 전체 최댓값 | `rtc.py` `_estimate_rtc_delay`, `lr/policies/rtc/latency_tracker.py` |
| 정책 호출 | RTC | `predict_action_chunk(preprocessed, inference_delay=d, prev_chunk_left_over=P)`. P = 앞 chunk 의 아직 안 꺼낸 action (정규화 값), 20 개로 자르거나 마지막 값으로 채움 | `rtc.py` (`_normalize_prev_actions_length`) |
| RTC 안내 | RTC | denoise 단계마다 `v − w·correction`, `err = (P − x̂1)·weights`. weights: index < d 는 1, d … h(20) 는 EXP 감소, ≥ h 는 0. w ≤ max_guidance_weight 10 | `lr/policies/rtc/modeling_rtc.py:122-256` |
| 후처리 | RTC | postprocessor (역정규화 → °) | `rtc.py` |
| merge | RTC | `delay = min(real_delay, idx_diff)` (real_delay = ceil(이번 지연 × fps), idx_diff = 추론 중 꺼낸 개수). queue 를 새 chunk 의 `[delay:]` 로 **통째로 교체** (앞 chunk 남은 부분 버림) | `lr/policies/rtc/action_queue.py` `merge`, `_check_and_resolve_delays`, `_replace_actions_queue` |
| action 꺼내기 | control | 틱마다 queue 에서 1 개 (interpolation_multiplier 1) | `action_queue.py` `get_with_task`, `core.py:383-432` |
| 팔 필터 | control | (`--arm_filter=true`) 팔 5관절: EMA α 0.5 (입력과 EMA 차 > 10° 이면 그 관절 EMA 초기화) → 직전 출력 대비 관절별 속도 제한 (pan 2.46°/틱 = 73.8°/s, 사람 리더 p99.5). 그리퍼 제외 | `d2/eval/arm_filter.py:53-96`, `rollout_logged.py:136-176` |
| 녹화 | control | dataset frame = 그 틱 관측 + **필터 뒤** action (clamp 전) | `lr/rollout/strategies/episodic.py:286-290` |
| clamp | control | `send_action`: `sync_read("Present_Position")` 를 **한 번 더** 읽고 `goal ∈ present ± max_relative_target(8°)` 로 자름 → `sync_write("Goal_Position")` | `so_follower.py:229-254`, `lr/robots/utils.py:93-116` |

## 2. 실제 설정 (기존 d2 실물 실행 2 회, `command.txt`·`debug.log` argv 로 확인)

| 항목 | 20261026_135128_20k_t1_try3 | 20261026_140246_20k_t1_try3_filt | 근거 |
|---|---|---|---|
| 체크포인트 | d2 020000 | d2 020000 | debug.log argv |
| inference.type | rtc | rtc | argv |
| rtc.mode | guided (기본) | guided (기본) | `configuration_rtc.py` 기본값 |
| execution_horizon | 20 | 20 | argv |
| prefix_attention_schedule | EXP | EXP | argv |
| max_guidance_weight | 10.0 (기본) | 10.0 (기본) | 기본값 |
| num_inference_steps | 5 | 5 | argv |
| queue_threshold | 30 | 30 | argv |
| chunk_size / n_action_steps | 50 / 50 | 50 / 50 | 체크포인트 config.json |
| fps · interpolation_multiplier | 30 · 1 | 30 · 1 | argv, 기본값 |
| max_relative_target | 8 | 8 | argv |
| arm_filter | **꺼짐** | **켬** (α 0.5, init state) | argv, debug.log 옵션 줄 |
| rollout_guard · exec_speed | off · 1.0 | off · 1.0 | debug.log |
| 카메라 | front · wrist 640×480 30 fps MJPG, warmup 기본 (학습 녹화는 4 s) | 같음 | argv |
| 판 수 | 2 판 저장 | 3 판 저장 | dataset |

- eval_ui 의 기본값은 `queue_threshold=40`, schedule 기본 LINEAR 이다 (`eval_ui.py:77-82`). d2 평가 명령 (`평가_명령.md`) 은 EXP · queue 30 · `--arm_filter=true` 를 덮어쓴다. 2026-10-29 `--check` 로 확인한 값: RTC guided, EXP, max_guidance_weight 10.0, execution_horizon 20, queue_threshold 30, max_relative_target 8.0, fps 30, arm_filter α 0.5.
- d2 eval_ui 실행 기록은 없다 (`eval/rollouts/` 에 위 2 회뿐).

## 3. 시간

| 항목 | 값 | 종류 |
|---|---|---|
| 제어 주기 | 33.3 ms (30 Hz) | [설정] |
| 실제 프레임 간격 (try3, clamp 기준점 직선 맞춤) | 33.48 / 33.47 ms (판 0 / 1), 잔차 중앙값 0.8 / 1.6 ms | [로그] |
| 첫 chunk 추론 지연 (판 첫 추론) | 0.73 s (세션 첫 판), 0.32 s (이후 판) | [로그] |
| 이후 추론 지연 | p5 0.33 · p50 0.34 · p95 0.36 · 최대 0.39 s (n 304) | [로그] |
| merge 간격 (= 새 관측 반영 주기) | p5 0.649 · p50 0.669 · p95 0.694 · 최대 1.03 s | [로그] |
| 적용 delay (merge 때 버린 chunk 앞부분) | 10 틱 266 회, 9 틱 21 회, 11 틱 12 회, 그 밖 5 회 | [로그] |
| chunk 당 실행된 action 수 | 첫 chunk 30 (index 0–29), 이후 19–21 (index 10–29 중앙값) | [로그] |
| 정책에 넘긴 inference_delay | 세션 두 번째 추론 0 (첫 추론 뒤 tracker reset → 지연 0 으로 추정), 이후 ceil(세션 최대 지연 × 30) ≈ 11–12 | [코드], 기록 없음 |
| 관측 → 그 관측으로 만든 첫 실행 action | ≈ 적용 delay 10 틱 ≈ 0.33 s (+ 관측 나이) | [로그]+[설정] |
| 관측 → 그 chunk 마지막 실행 action | ≈ 29 틱 ≈ 0.97 s | [로그] |
| 카메라 프레임 나이 (관측 시점) | 기록 없음. 코드상 상한 500 ms (`read_latest(max_age_ms=500)`) | [코드] |
| 명령 → 실제 위치 지연 (pan, sent 와 state 의 평균 절대차가 가장 작은 틱 차) | 5 판 모두 4 틱 (≈ 133 ms) | [로그] (`p02_tracking.csv`) |

## 4. 핵심 질문별 답

1. **정책은 몇 초 간격으로 새 관측을 쓰는가** — merge 간격 p50 0.669 s [로그]. 그 사이 20 틱은 이미 만든 chunk 를 실행한다.
2. **front/wrist 영상은 어느 시점 영상인가** — 추론 시작 틱의 `get_observation()` 이 읽은 최신 프레임 (카메라 백그라운드 스레드 보관본). 프레임 나이는 기록되지 않았다 [코드]. 기존 dataset 영상은 같은 프레임을 AV1 로 다시 저장한 것이다.
3. **영상 촬영 → Action Expert 출력 지연** — 추론 지연 p50 0.34 s [로그] + 관측 나이 (미기록). 그 chunk 의 action 이 실제로 나가기 시작하는 시각은 관측 뒤 ≈ 0.33 s, 마지막은 ≈ 0.97 s [로그].
4. **새 chunk 가 오면 이전 chunk 는** — queue 를 새 chunk `[delay:]` 로 통째로 바꾼다. 앞 chunk 의 남은 action (꺼내지 않은 ~30 개) 은 버린다. 이어짐은 RTC 안내 (prefix) 로만 맞춘다 [코드].
5. **RTC 가 새 행동을 얼마나 늦게 반영하는가** — 실행 구간 index 10–29 중 index < inference_delay (≈ 11–12) 는 앞 chunk 값으로 강하게 끌리고 (weight 1), 그 뒤 EXP 감소 [코드, `get_prefix_weights` 로 계산]:
   - d = 11: index 10 1.0 · 11 0.765 · 12 0.571 · 14 0.287 · 16 0.114 · 18 0.026 · ≥ 20 0
   - d = 0 (세션 두 번째 추론): index 0 0.882 · 5 0.433 · 10 0.169 · 15 0.037 · ≥ 20 0 — 실행이 시작되는 index 10 의 weight 가 0.17 이다.
   실제 안내 전후 차이는 기존 로그에 없다 (안내 없는 chunk 를 기록하지 않음).
6. **관절 목표가 서보 명령으로 바뀌며 변형되는가** — 두 단계에서 바뀔 수 있다: (a) arm_filter (켠 실행만), (b) clamp ±8°. 기존 로그 측정값은 `06_servo_tracking.md`.
