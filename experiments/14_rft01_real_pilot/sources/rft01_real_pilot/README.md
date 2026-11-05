# rft01 실물 평가 파일럿 준비 (`main_k8/rft01_real_pilot`)

작성 2026-11-05.
- 표기: [사실] 파일 · 코드 · 측정값 · [가짜 장치] FakeBus · FakeCam 시험 결과 · [재추론] 저장 관측을 다시 넣은 오프라인 출력 · [계획] 설계만.
- 이번 작업 범위: 평가 설정, 스크립트, 안전 점검, 기록 방식 준비. **실물 로봇 연결 · 토크 · 정책 추론 rollout 은 하지 않았다.**
- 사용자 실행 순서: `RUN_REAL_PILOT.md`.

## 0. 구성

| 경로 | 내용 | 새로 / 재사용 |
|---|---|---|
| `eval/rollout_logged.py` | shim. R2 세션 shim (`r2_grasp_diagnostic/eval/rollout_logged.py` → d2 rollout_logged + r2_safety) 을 수정 없이 불러오고, 그 위에 `fault_latch` 를 건다 | 새 (20 줄) |
| `eval/fault_latch.py` | 추론 오류 래치 (§3.3) | 새 |
| `eval/arm_filter.py` · `pose_check.py` · `analyze_rollout.py` · `plot_rollout.py` | d2 `eval/` 로 가는 symlink | 재사용 |
| `config/pilot_plan.csv` | 시행표 8 행. r2_safety 배치 계획 형식 + trial · model · pair · phase 열 | 새 |
| `config/models.env` | 두 체크포인트 경로 · SHA-256 · 과제 문장 · 판 최대 60 s | 새 |
| `scripts/run_trial.sh` | 시행 1 개 실행 (게이트 → SHA 확인 → manifest → eval_ui) | 새 (eval_ui 호출) |
| `scripts/post_trial.sh` | p00b 점검 → p05 재구성 → r2_analyze → trial_auto | 새 (기존 스크립트 호출) |
| `scripts/trial_auto.py` · `record_trial.py` · `gate.sh` | 자동 지표 · 사용자 판정 입력 · 진행 게이트 | 새 |
| `scripts/c01_verify_models.py` · `c02_history.py` | 체크포인트 검증 · 과거 기록표 | 새 |
| `tests/test_fake_pilot_e2e.py` · `test_units.py` · `run_all.sh` | 가짜 장치 · 단위 시험 | 새 |

- 수정하지 않은 파일: `so101_boxpick/scripts/eval_ui.py`, R2 세션 `eval/` · `scripts/` · `tests/`, d2 `eval/`, 체크포인트, 데이터셋.
- `so101_boxpick` git HEAD `490a5da`. `scripts/eval_ui.py` 는 그 저장소에서 추적되지 않는 파일 (`??`) 이다. 그래서 run 마다 manifest 에 코드 파일별 SHA-256 을 남긴다 (§5).

## 1. 실제 사용 가능한 평가 명령 [사실]

`scripts/run_trial.sh <N>` 이 만드는 명령 (`CHECK=1` 로 확인, 2026-11-05 09:41–09:42 시행 1 · 2 `CHECK_OK`):

```bash
cd ~/so101_boxpick
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py --session main_k8/rft01_real_pilot \
  --ckpt <BL 또는 FT 절대 경로>/pretrained_model \
  --task "pick up the red cube and put it in the brown box" \
  --tag t<NN>_<ft|bl>_<자리> --episodes 1 --episode-time 60 \
  --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 \
  --arm_filter=false --rollout_guard=warn --r2_safety=stop \
  --r2_safety.plan=$HOME/so101_runs/main_k8/rft01_real_pilot/config/pilot_plan.csv --r2_safety.plan_start=<N> \
  --fault_latch=stop
```

CHECK_OK 출력 (두 모델 같음):
- `RTCConfig(enabled=True, mode='guided', prefix_attention_schedule=EXP, max_guidance_weight=10.0, execution_horizon=20)`, `queue_threshold=30`
- `max_relative_target=8.0`, `fps=30.0`
- `arm_filter={'arm_filter': False, ... 'guard': 'warn', 'exec_speed': 1.0}`
- eval_ui 기본값 `--policy.num_inference_steps=5` · `--inference.type=rtc`

11-03 R2 실물 평가 (`r2_grasp_diagnostic/eval/rollouts/20261103_111340_20k_r2_diag2/command.txt`) 와의 차이:

| 항목 | 11-03 R2 | 이번 파일럿 |
|---|---|---|
| 세션 | `main_k8/r2_grasp_diagnostic` | `main_k8/rft01_real_pilot` |
| 체크포인트 | d2 020000 | 시행표에 따라 d2 020000 / rft01 001000 |
| 실행당 판 | 4 | 1 (시행마다 모델을 바꾸기 때문) |
| 판 최대 시간 | 3600 s (사람이 → 로 끝냄) | 60 s (두 모델 같은 종료 기준) |
| 배치 계획 | `r2_plan.csv` | `pilot_plan.csv` (`plan_start=N`) |
| 추론 오류 래치 | 없음 | `--fault_latch=stop` |
| 추론 · 필터 · clamp · r2_safety 임계값 | — | 같음 |

## 2. 체크포인트 · normalizer 검증 [사실] (`logs/c01_verify_models.json`, 2026-11-05)

| 검사 | 결과 | 값 |
|---|---|---|
| M1 SHA-256 재계산 | PASS | BL `6c46dee79b167c48ad24b6af739157dc22636505c4c838815a4bf3656a364886` · FT `620c45988a35b77e76b5c0869c560697d9d095143aceee33b98946a7db712af9` (= recovery_ft 기록) |
| M2 000500 보존 | PASS | `c0e3c88b135eb43354909eea3d0b30415d16106e108c0ad55744c62614c0cbbd` (이번 파일럿에서 실행하지 않음) |
| M3 config.json 차이 | PASS | `pretrained_path`, `optimizer_lr` 2.5e-5 → 1e-5, `scheduler_warmup_steps` 1000 → 50, `scheduler_decay_steps` 30000 → 1000 만 다름. chunk_size 50 · n_action_steps 50 · QUANTILES (state · action) · image 224² · tokenizer_max_length 200 · dtype bfloat16 같음 |
| M4 processor json | PASS | `policy_preprocessor.json` · `policy_postprocessor.json` byte 동일 |
| M5 normalizer 값 | PASS | normalizer · unnormalizer 90 텐서 모두 `np.array_equal`. action q01 `[−108.84, −104.47, −81.68, 0.65, −57.36, 0.32]` · q99 `[103.64, 62.81, 97.64, 100.26, 55.68, 49.95]` |
| M6 tokenizer | PASS | `tokenizer.json` byte 동일. `tokenizer_config.json` 은 저장 기본값 7 키만 다름 (`max_length` 200 · `padding_side` right 등 = 전처리 호출 인자와 같은 값). 과제 문장 · pi05 형식 예시 문자열 토큰 id · mask 동일 |
| M7 Action 범위 [재추론] | **FAIL** (미리 정한 규칙) | 아래 |

M7 방법:
- recovery_ft 오프라인 재추론 배열 (`d2/recovery_ft/eval/raw/{d2_020000,rft01_001000}/{q02,vd_b,vd_h}.npz`, 같은 상태 · 같은 noise) 에서 관절별 예측 범위를 비교했다. G 11,360 chunk · U 9,824 chunk.
- 규칙 v2: FT 의 min / max 가 BL 의 min − 5° … max + 5° 안, chunk 안 step 간 최대 변화 ≤ BL 의 1.25 배, |pan| > 104 비율 ≤ BL + 1 %p.
  - 규칙 v1 (학습 action 범위 ± 5°) 은 BL 자체도 pan −132° 를 예측해 비교 기준이 안 되어 v2 로 바꿨다. v1 기록: `logs/c01_verify_models_rule_v1.json`.

| G (RTC) | BL 020000 | FT 001000 |
|---|---|---|
| pan min / max | −132.1 / 100.8 | −128.7 / 98.2 |
| wrist_flex min / max | **38.25** / 105.5 | **30.01** / 103.1 |
| step 간 최대 변화 (pan, lift, elbow, flex, roll, grip) | 7.1, 8.3, 6.4, 4.1, 5.2, 10.6 | 6.8, 9.1, 7.2, 4.2, 5.2, 10.3 |
| \|pan\| > 104 비율 | 8.1 % | 7.1 % |
| U \|pan\| > 104 비율 | 9.3 % | 8.0 % |

- FAIL 원인: FT wrist_flex 최솟값이 BL 최솟값 − 5° (33.25°) 보다 낮다.
- 그 상태: q02 `U8_c00436` (G 30.0°, U 30.5°) · `K7_c00409` (U 32.6°). 비율 G 2e-5 · U 5e-5. vd_b · vd_h 에는 없다.
- 학습 action wrist_flex 범위는 0.6 … 100.6° 다.
- 파일럿 자리 K1 · K3 의 상태는 아니다.
- |pan| > 104 예측은 두 모델 모두 7–9 % 다. 이 상태들은 주로 A0 · B1 지나침 상태 (q02) 이고, r2_safety `pan_cmd_abs_max=104` 가 이 명령을 막는 대상이다.

## 3. RTC · 필터 · 안전 설정

### 3.1 추론 · 필터 [사실]

| 항목 | d2 표준 실물 (11-03 R2) | 파일럿 BL | 파일럿 FT |
|---|---|---|---|
| inference | RTC guided, EXP, h20, mgw 10 | 같음 | 같음 |
| num_inference_steps | 5 | 5 | 5 |
| queue_threshold | 30 | 30 | 30 |
| chunk / n_action_steps | 50 / 50 | 50 / 50 | 50 / 50 |
| Arm Filter | 꺼짐 (`--arm_filter=false`, `--rollout_guard=warn`) | 같음 | 같음 |
| max_relative_target | 8° | 8° | 8° |
| 카메라 | front · wrist 640×480 MJPG 30 fps (`/dev/cam_front` · `/dev/cam_wrist`) | 같음 (eval_ui ROBOT_ARGS) | 같음 |
| 캘리브레이션 | `--robot.id=my_arm` | 같음 | 같음 |
| normalizer | — | 020000 | 020000 과 값 동일 (M5) |

### 3.2 안전 점검 (§5 작업 지시 항목) [사실]

| 항목 | 기존 평가 경로에서 확인한 것 | 출처 |
|---|---|---|
| Pan 기계 · 캘리브레이션 한계 | 캘리브레이션 pan ±110.2°. A0 · B1 은 present −108.9 / −109.0° 에서 멈춤 (명령 −126.5 / −119.3°) | r1_r2_collection 문서 · 13_k1_pregrasp_analysis.md |
| Pan 소프트웨어 정지 | r2_safety: 보내려는 pan \|·\| > 104 · 현재 pan \|·\| > 100 · 시작 사진 큐브 방위 pe 를 처음 진행 방향으로 30° 넘게 지나침 · 팔 관절 추종 정지 20 틱. 걸리면 그 명령 차단 → 현재 위치 유지 1 회 → engine.pause · reset (queue 비움) → 판 남은 정책 명령 차단 → 판 종료 | `r2_grasp_diagnostic/eval/r2_safety.py` |
| 　K1 에서의 over_target 위치 | K1 pe −35.5° → present < 약 −65.5° 에서 정지. 과거 K1 사용자 P 판의 pan 최소 −26.2 … −33.2° (c02) | config · `logs/c02_history.md` |
| 　검증 | 기록 20 판 오프라인 재적용: A0 · B1 을 −105° 도달 약 8 s 전에 잡음, 나머지 18 판 첫 닫힘 전 오경보 0 · 가짜 장치 e2e PASS. 실물 11-03 8 판에서 설치 · 동작 (정지 0 회). **실물에서 규칙이 걸린 적은 없다** | R2 README §3 · §5 |
| 정지 요청 후 잔여 RTC action | r2_safety 정지: queue 30 → 0, 이후 정책 명령 0 ([가짜 장치] R2 T9 · 이 세션 S1–S3). → 키: 정책 루프가 다음 틱에 끝나고 이후 정책 명령 없음 (episodic `_policy_loop`). 이미 보낸 Goal (현재 위치에서 ≤ 8°) 은 서보가 계속 따라간다 (취소 불가, 덮어쓰기만 가능) | lerobot `rollout/strategies/episodic.py` |
| 추론 오류 | **공식 동작: 오류 뒤에도 queue 의 action 을 계속 보내고 0.5 s × 10 회 재시도 뒤 종료.** 기존 평가 경로 (r2_safety) 는 이를 막지 않는다. HIL A10 래치는 dagger 전략 전용이라 이 경로에 없다 → 이번에 `fault_latch` 를 더함 (§3.3) | lerobot `rollout/inference/rtc.py` 50–60, 600–630 행 |
| 통신 오류 (서보 bus · 카메라) | 예외 → 정책 루프 종료 → 이후 정책 명령 없음 → lerobot 종료 처리 (판 저장 · 복귀 시도 · disconnect). bus 가 죽으면 복귀 · 토크 끄기도 실패할 수 있고, 서보는 마지막 Goal 을 토크로 유지한다 → 전원 차단 | episodic `run()` finally · core `_teardown_hardware` · eval_ui `make_return_home` (예외 시 경고 후 계속) |
| 충돌 · 끼임 | 접촉 센서 없음. r2_safety stall 규칙 (명령 − 현재 > 8° 이고 틱당 이동 < 0.3° 가 20 틱 = 0.67 s) 이 유일한 소프트웨어 감지. 서보 토크 · 전류 제한 설정은 이번에 확인하지 않음 | r2_safety |
| 전원 차단 | follower 12 V 스위치 / 플러그 (물리). 차단 시 토크가 사라져 팔이 자기 무게로 내려온다 | — |
| 사용자 수동 정지 | → (판 끝) · Ctrl+C (KeyboardInterrupt → 판 저장 → 종료 처리) · 전원 차단. **v2: 어느 경우든 자동 복귀 없이 그 자리 유지 (§3.4)** | eval_ui · end_hold |
| 정지 · 오류 뒤 자동 이동 | v1 (기존 경로): 판 종료 · r2_safety 정지 · fault_latch · Ctrl+C 모두 lerobot 종료 처리에서 처음 자세로 자동 복귀 (eval_ui 보강 30°/s) → 토크 끔. **v2: 차단 — 자동 복귀 명령 0, 토크 유지 (§3.4)** | eval_ui `make_return_home` · core `_teardown_hardware` · `eval/end_hold.py` |
| 작업공간 | K1 은 로봇 기준 왼쪽 (pan −). 과거 K1 9 판 중 2 판 (A0 · B1) 이 pan −109° 까지 감 (c02). 이번 시행표는 지나침을 일부러 만드는 시작 자세를 쓰지 않는다 (기존 쉬는 자세) | `logs/c02_history.md` |
| R1/R2 수집 도구 안전 게이트 (pan > 95 BLOCK 등) | 텔레오퍼레이션 녹화 경로 (`r12_record_entry.py`) 에만 있다. 정책 평가 경로에는 없다 | r1_r2_collection 문서 |

### 3.3 fault_latch (새로 더함)

동작:
1. RTC 로거의 ERROR 줄 `RTC inference error` / `Fatal error in RTC thread` 가 처음 나오는 순간 (RTC 스레드 안) 래치를 건다.
   - 동시에 `engine.pause()` 로 재시도를 멈춘다.
   - 주 루프 틱마다 `engine.failed` 도 본다.
2. 래치 뒤 정책 루프의 `send_action` 은 모두 차단한다.
3. 래치 뒤 첫 `get_observation` (매 틱 불림 — queue 가 비어 send 가 없어도 처리됨) 에서 한 번 처리한다.
   - `engine.reset()` 으로 queue 를 비운다.
   - 팔 5 관절 Goal 을 현재 위치로, 그리퍼는 마지막 정책 명령 (쥔 큐브를 놓지 않게) 으로 한 번 보낸다. 이 명령은 r2_safety 를 거친다.
   - r2_safety 를 stopped 로 두고 `exit_early` 로 판을 끝낸다.
4. 기록: `fault_latch.csv` 와 `r2_safety.csv` (event=FAULT), 콘솔 `FAULT_LATCH`.

정책 루프 밖 (처음 자세 복귀 · 종료 처리) 의 명령은 건드리지 않는다. HIL A10 과 같은 원칙이지만 코드는 hil_dagger 에서 가져오지 않았다 (dagger 전략 전용 상태를 쓰기 때문).

### 3.4 종료 처리 v2 — 자동 복귀 없음 · 제자리 유지 · 토크 유지 (2026-11-05 사용자 요청)

기존 경로에서 팔을 자동으로 움직이던 곳 [사실, lerobot 0.6.2 · eval_ui]:

| 호출 위치 | 언제 | v1 동작 | v2 |
|---|---|---|---|
| `core._teardown_hardware` → `return_to_initial_position` | 모든 종료 (정상 · 예외 · Ctrl+C · fault Fatal) | eval_ui 보강으로 30°/s 보간 + 4 s 추종 → `robot.disconnect()` 가 토크 끔 | 교체 (E4): 엔진 정지 → 제자리 유지 → `bus.disconnect(disable_torque=False)` · 카메라 끊기. 토크 유지 |
| `episodic.run` reset 단계 | 다음 판 전 (판 2 개 이상 · 다시 찍기) | 복귀 1 s (eval_ui 보강) | 차단 (E1) + 공식 `--strategy.reset_to_initial_position=false` |
| `episodic.run` 다시 찍기 (←) | ← | 버리고 복귀 → 같은 프로세스에서 정책 재시작 | E3: 버리고 실행 종료 (복귀 · 재시작 없음). 다시 하려면 `RERUN=…` |
| lerobot `cfg.return_to_initial_position` | 종료 | True | 공식 `--return_to_initial_position=false` 도 줌 (E4 가 어차피 대체) |
| `robot.disconnect()` | 종료 | `disable_torque_on_disconnect=True` → 토크 끔 → 팔이 자기 무게로 내려옴 | 쓰지 않음 (E4) |

`eval/end_hold.py` (shim 이 항상 설치, 끄는 옵션 없음):
- E1: `EpisodicStrategy.return_to_initial_position` 을 차단한다. 명령 0 개로 False 를 돌려주고 `end_hold.csv` 에 기록한다.
  - eval_ui 의 보강 함수는 기반 클래스 `RolloutStrategy` 에 들어간다. 하위 클래스 속성이 먼저 잡히므로 보강 함수도 불리지 않는다.
- E2: 정책 루프가 어떤 이유로 끝나든 finally 에서 한 번, 팔 5 관절 Goal 을 지금 Present 로 쓴다. 이미 보낸 ≤ 8° 의 남은 이동을 덮어쓴다. 그리퍼는 쓰지 않는다.
- E4 끝에 `end_state.json` 을 쓴다: 끝난 이유 · 시작 자세 · 끝 자세 · 차이 · `torque_left_on` · 차단한 복귀 호출 수.

복귀가 필요할 때 — `scripts/safe_home.py` (사용자가 eval_ui 가 끝난 뒤 따로 실행):
- lerobot `SOFollower.connect()` 를 쓰지 않는다 (configure() 가 토크를 잠깐 끄므로). `bus.connect()` (포트 + ping · 펌웨어 읽기) 만 한다.
- 캘리브레이션이 불일치하면 쓰지 않고 멈춘다.
- 이동 전 점검 H1–H7 (하나라도 실패하면 이동 안 함, 토크 그대로):
  - H1 다른 lerobot · eval_ui 프로세스 없음
  - H2 6 관절 토크 켜짐
  - H3 |Goal − Present| ≤ 4°
  - H4 |pan| ≤ 100 · 캘리브레이션 범위 안
  - H5 목표 = end_state 의 시작 자세이고 접은 자세 (lift ≤ −85 · elbow ≥ 80)
  - H6 지금 자세 = end_state 끝 자세 ± 5°
  - H7 관절별 이동 ≤ 140°
- 계획 표 (지금 · 목표 · 차이, 예상 시간) 를 보여 준 뒤 **`home` 을 정확히 입력해야** 움직인다.
- 이동:
  - 팔 5 관절 직선 보간, 최대 관절 15°/s (틱당 ≤ 0.5°), 30 Hz. 그리퍼는 쓰지 않는다.
  - 추종 오차 > 12° 가 10 틱 연속 · |pan| > 105 · 읽기 오류 · Ctrl+C 가 나오면 즉시 Goal 을 Present 로 쓰고 멈춘다.
- 도착 뒤 `release` 를 입력해야만 토크를 끈다. 그 밖에는 토크를 유지한다.
- `--mode release`: 이동 없이 지금 자리에서 토크만 끈다. 접은 자세가 아니면 `받쳤음` 을 한 번 더 입력해야 한다.
- 기록: `results/home_logs/<run>_<시각>.json`.

다음 시행 게이트: `run_trial.sh` 가 마지막으로 팔에 연결한 run 의 `end_state.json` 을 본다.
- 막는 경우: 시작 자세와 > 5° 이고 safe_home 도착 기록도 `gate.sh rest` 기록도 없을 때, 또는 end_state 가 없을 때.
- 이유 (코드로 해결 안 됨): 다음 lerobot connect 는 `configure()` 에서 토크를 잠깐 끈다. 그래서 팔이 접은 자세가 아니면 내려온다.

## 4. 평가 시행표 [계획] (`config/pilot_plan.csv`)

| 시행 | Phase | 쌍 | 모델 | 자리 · 각도 |
|---|---|---|---|---|
| 1 | 2 | P1 | FT | K3 · 0 |
| 2 | 3 | P1 | BL | K3 · 0 |
| 3 | 3 | P2 | BL | K1 · 0 |
| 4 | 3 | P2 | FT | K1 · 0 |
| 5 | 3 | P3 | FT | K3 · R30 |
| 6 | 3 | P3 | BL | K3 · R30 |
| 7 | 3 | P4 | BL | K1 · L30 |
| 8 | 3 | P4 | FT | K1 · L30 |

- 모델 순서: FT BL · BL FT · FT BL · BL FT (쌍마다 먼저 하는 모델을 바꿈). 모델별 4 회.
- 같게 두는 것: 큐브 자리 · 각도 (쌍 안), 시작 자세 (기존 쉬는 자세, eval_ui 가 연결 순간 자세를 처음 자세로 잡음), 카메라 · 캘리브레이션, 과제 문장, 종료 기준 (판 최대 60 s, 상자에 넣으면 →, 자동 정지, 위험 시 Ctrl+C).
- 시행 1 = FT 1 회 (Phase 2). 결과를 기록하고 `gate.sh go` 를 해야 시행 2 가 열린다.

과거 기록 (d2 020000, 시작 사진 판정 Known, `logs/c02_history.md`) [기록]:

| 조건 | arm_filter false (현재 표준) | arm_filter true |
|---|---|---|
| K1 · 0 | 4 판: 첫 닫힘 grasp 2 · no_close 1 (B1, pan −109.0) · undetermined 1 · 사용자 P 2 | 0 판 |
| K1 · L30 | 1 판: grasp · P | 4 판: grasp 1 · empty 2 · no_close 1 (A0, −108.9) · P 1 |
| K3 · 0 | **0 판** | 1 판: empty · F |
| K3 · R30 | 1 판: empty · F (11-03, BELOW 쪽) | 0 판 |

- 현재 표준 설정 (filter 끔) 에서 K3 · 0 은 기록이 없다. K1 · L30 과 K3 · R30 은 1 판씩이다. 이 조건들은 과거 기록과 직접 비교하지 않는다. 파일럿 안의 BL · FT 쌍끼리만 비교한다.
- 다른 날 · 다른 실행이라 큐브 배치 · 조명 · 카메라 위치 차이가 통제되지 않는다.
- 위치 선택 근거 [사실]:
  - K1 은 R1 (Pan 지나침) 이 나온 자리다 (A0 · B1).
  - K1 · L30 과 K3 · 0 의 빈 닫힘은 손목 영상 'ahead' (AHEAD) 였다.
  - K3 · R30 빈 닫힘은 'edge_below' (BELOW) 였다 (R2 reports).

## 5. 기록 경로와 결과 입력 방식

시행마다 (모두 새 파일 — 기존 결과를 덮어쓰지 않음):

| 요구 (작업 지시 §6) | 어디 | 종류 |
|---|---|---|
| run ID | eval_ui run 폴더 이름 `<YYYYMMDD_HHMMSS>_<1k\|20k>_t<NN>_<ft\|bl>_<자리>` (시각이 들어가 고유) | [기록] |
| 모델 · checkpoint SHA | `<run>/trial_manifest.json` (실행 직전 재계산한 SHA-256) · `results/run_ledger.csv` | [기록] |
| 코드 commit SHA | manifest `so101_boxpick_git.head` + `code_sha256` (eval_ui.py · 두 shim · fault_latch · r2_safety · r2_live · r2_place_viewer · d2 rollout_logged · arm_filter · diag_log · cube_coords · 계획 · models.env · run_trial.sh 각 SHA-256). trials.csv 에는 묶음 digest | [기록] |
| 큐브 위치 · 각도 | `r2_safety.csv` plan_check (시작 front 사진 측정, 계획과 2 cm 넘거나 각도 코드가 다르면 ⚠) · `reports/<run>/episodes.csv` | [기록] |
| 로봇 시작 관절값 | dataset 첫 frame `observation.state` · `pose_check.txt` | [기록] |
| Front · Wrist 영상 | `<run>/dataset/videos/` · `diag/obs/` (모델 입력 PNG) | [기록] |
| 실제 state · action | `<run>/dataset/data/*.parquet` · `filter_log.csv` · `diag/ticks.csv` (sent · present · goal) | [기록] |
| 첫 파지 성공 | 사용자 입력 `first_grasp` + 자동 후보 `auto_first_close` (r2_analyze T4) | 사용자 / [자동 후보] |
| 빈 파지 발생 | `empty_grasp` + `auto_empty_before_grasp` | 사용자 / [자동 후보] |
| Pan 방향 반전 | `pan_reversal` + `auto_pan_rev_pre_close` · `auto_pan_rev_whole` (present pan 을 목표 방향으로 투영, 최대 진행에서 5° 이상 되돌아감; 진행 5° 전은 세지 않음) · `auto_pan_max_past_target` | 사용자 / [자동 후보] |
| Wrist 큐브 재획득 | `wrist_reacquire` + `auto_wrist_lost_segments` · `auto_wrist_reacquired` (3 frame 마다 빨강 검출, 보임 ≥ 0.3 s 뒤 안 보임 ≥ 1 s = 놓침, 다시 보임 ≥ 0.3 s = 재획득, 첫 파지 전까지) | 사용자 / [자동 후보] |
| 최종 작업 성공 | `final_success` + eval_ui P/F (`eval_ui_verdict`) | 사용자 |
| 중단 · 안전 개입 · 이유 | `intervention` (none · r2_safety_stop · fault_latch · user_key_end_early · ctrl_c · power_off · hand_contact · other) · `intervention_reason` + 기록 `safety_stops` · `fault_events` · `console_ctrl_c` | 사용자 / [기록] |

- 결과 입력: `record_trial.py <run>`. [기록] · [자동 후보] 를 먼저 보여 준다. 사용자 판정 칸은 기본값 없이 묻는다 (y · n · u · na).
- `results/trials.csv` 에는 추가만 한다. 같은 run 을 다시 입력하면 거부한다. `--amend "이유"` 는 revision 을 올린 새 줄을 더한다.
- 자동 후보 규칙 자체 시험: B1 (`20261029_170818` ds_ep 1) 에서 반전 1 회 (−47.6 → −31.6°, 16.0°), 목표 지나침 최대 73.6°, pan 최소 −109.0°, 손목 놓침 1 구간 (i 120) · 재획득 없음. 13_k1_pregrasp_analysis.md · offline_pan_reversal 문서의 B1 기술과 같다.

## 6. 가짜 장치 시험 결과

### 6.0 v2 (종료 처리) — `tests/run_all.sh` 2026-11-05 10:33–10:58 → **TESTS_ALL_PASS** (`logs/tests/run_20261105_103355/`)

모든 시나리오 공통 검사 [가짜 장치]:
- R1 자동 원위치 복귀 명령 0: 정책 루프 마지막 쓰기 뒤 FakeBus Goal 이 모두 Present ± 0.5° 이고, 시작 자세 쪽으로 간 관절 0, eval_ui HOMING 표시 0.
- R2 `end_state.json`: torque_left_on = True · bus 정상 · lerobot return flag = False.
- R3 `bus.disconnect(disable_torque=False)` 만 불림.
- R4 정책 루프 끝 제자리 유지 명령이 있음.

| 시나리오 | 끝난 이유 (end_state) | 정책 뒤 쓰기 | 자동 복귀 명령 | 토크 | 시작 자세와 최대 차 | 시나리오 검사 |
|---|---|---|---|---|---|---|
| normal_timeout (판 6 s) | episode_end_or_user_next | 2 (유지 2) | 0 | 유지 | 31.0° | 판 시간 끝까지 실행 5.99 s · SAVED 1 |
| user_next (→, 5 s) | episode_end_or_user_next | 2 | 0 | 유지 | 35.1° | SAVED 1 |
| r2stop (pan 한계 15°) | r2_safety_stop | 2 | 0 | 유지 | 19.7° | STOP tick 63 · queue 27 → 0 · 정지 뒤 정책 명령 0 · 오경보 0 |
| fault (추론 오류 주입) | fault_latch | 2 | 0 | 유지 | 7.1° | 처리 0.024 s · queue 30 → 0 · 오류 뒤 정책 명령 0 · 재시도 1 |
| ctrl_c (SIGINT 1 회) | shutdown_signal | 2 | 0 | 유지 | 41.7° | SAVED 1 |
| ctrl_c2 (SIGINT 2 회, 0.05 s) | shutdown_signal (뒤이어 lerobot `Force shutdown` → SystemExit) | 2 | 0 | 유지 | 23.6° | SAVED 0 (강제 종료라 판 저장 안 됨) |
| rerecord (←) | user_rerecord | 2 | 0 | 유지 | 5.9° | DISCARD 1 · 실행 종료 · 정책 재시작 0 |
| fault_off (대조, latch 끔) | engine_failed_shutdown | 2 | 0 | 유지 | 29.2° | [공식 동작] 첫 오류 뒤 정책 명령 30 개 · 0.99 s · 실패 호출 10 회 |

- 정책 뒤 쓰기 2 개 = 정책 루프 끝 유지 1 + teardown 유지 1. 둘 다 Present 그대로다.
- 차단한 `return_to_initial_position` 호출: 모든 시나리오 0 회. 공식 플래그 `--return_to_initial_position=false` · `--strategy.reset_to_initial_position=false` 로 호출 자체가 생기지 않았다. 차단 함수는 예비로 남겨 둔다.
- 단위 시험 (CPU): test_units 31/31 (게이트 U5 6 개 추가), test_safe_home 17/17.
  - safe_home 이 막는 경우: `home` 미입력 · 토크 꺼짐 · Goal 차 6° · 끝 자세에서 8° 옮겨짐 · pan 102 · 목표가 쉬는 자세 아님 · 다른 프로세스 있음. 모두 쓰기 0 회.
  - 이동: 틱당 최대 0.500° (15°/s), 그리퍼 쓰기 0 회, `release` 입력 시에만 토크 끔.
  - 걸림: elbow 걸림 → 39 틱에 멈추고 제자리 유지. Ctrl+C → 10 틱에 멈추고 유지.
  - 연결: 소스에서 `bus.connect(` 만 있고 robot connect · configure 는 없다.
- eval_ui `--check` 8 시행 모두 CHECK_OK (`logs/check_all_trials_v2.txt`).
  - FT = 1 · 4 · 5 · 8, BL = 2 · 3 · 6 · 7.
  - h20 · queue 30 · clamp 8.0 · arm_filter False 이고, 새 플래그 2 개를 lerobot 이 받아들였다.
- R2 세션 기존 시험 · c01 재실행: §6.0b.

### 6.0b 기존 시험 재실행 (2026-11-05 10:58–11:1x)

| 시험 | 결과 | 로그 |
|---|---|---|
| R2 세션 `tests/run_all_tests.sh` (offline 1–8 · 안전 규칙 재적용 · 가짜 eval_ui e2e T9–T13, 코드 수정 없음) | TESTS_ALL_PASS (PASS 33) | `logs/tests/r2_session_tests_20261105.log` · `r2_grasp_diagnostic/logs/tests_20261105_105850/` |
| c01 체크포인트 검증 | M1–M6 PASS · M7 FAIL (§2 와 같은 값) | `logs/c01_verify_models_rerun_20261105.log` |

- R2 세션 (`main_k8/r2_grasp_diagnostic`) 의 평가 경로는 바꾸지 않았다. 그 세션으로 평가하면 지금도 v1 처럼 자동 복귀한다.
- v2 는 이 파일럿 세션 (`--session main_k8/rft01_real_pilot`) 에만 적용된다.

### 6.1 v1 기록 — `tests/run_all.sh` 2026-11-05 09:48–10:0x → TESTS_ALL_PASS (로그 `logs/tests/run_20261105_094837/`). v1 은 종료 때 자동 복귀했다 (아래 HOMING 표시).

방법 [가짜 장치]:
- `eval_ui.child_main` (실물과 같은 자식 경로) → 이 세션 shim → lerobot-rollout episodic · RTC · **rft01 001000** (GPU).
- 장치: R2 세션 `tests/fake_robot.py` 를 그대로 쓴다. 3 중 차단 · `/nonexistent` 경로 · MOCK_OK assert.
- 가짜 카메라 = B1 기록 영상 (K1).
- 옵션 = run_trial.sh 와 같다. 다른 점은 viewer · live off, 판 20 s 뿐이다.

| 시나리오 | 확인 | 결과 |
|---|---|---|
| fault (오류 주입, latch stop) | 7 번째 predict_action_chunk 부터 RuntimeError | — |
| | F1 래치 · 처리 | PASS: inference_error, tick 120, 오류 → 처리 0.029 s |
| | F2 오류 뒤 정책 명령 | PASS: 정책 루프 쓰기 1 개 (= 유지 명령), 유지 명령과 다른 Goal 0 |
| | F3 queue | PASS: 30 → 0 |
| | F4 판 종료 | PASS: 처리 틱에 종료 (dataset 120 frame / 600) |
| | F5 재시도 | PASS: 실패 호출 1 회 (재시도 멈춤), Fatal 없음 |
| | F6 eval_ui 경로 · 기록 | PASS: 예외 없음, SAVED 1, fault_latch.csv FAULT · FAULT_HANDLED, r2_safety.csv FAULT 1 행, 종료 뒤 HOMING 16° → HOMED 0.5° |
| fault_off (대조, latch off = 공식 동작) | 같은 주입 | INFO: 첫 오류 뒤 **정책 명령 30 개 · 0.99 s** (그중 28 개가 서로 다른 Goal), 실패 호출 10 회 뒤 Fatal → 종료, HOMING 50° → HOMED 1.6° |
| r2stop (pan 현재 한계 15° 로 낮춤, 주입 없음) | S1 정지 | PASS: tick 185 pan_present_limit |
| | S2 queue | PASS: 25 → 0 |
| | S3 정지 뒤 정책 명령 | PASS: 0 |
| | S4 fault_latch 오경보 | PASS: 없음 |
| | S5 eval_ui 경로 | PASS: SAVED 1, HOMED 0.6° |
| 공통 | T10a 진짜 bus · 카메라 connect 차단 · T10b FakeBus/FakeCam | 3 시나리오 모두 PASS |
| test_units (CPU) | Pan 반전 규칙 6 · Wrist 재획득 4 · record_trial 추가 전용 · 중복 거부 · amend 4 · run_trial 게이트 11 | 25/25 PASS |
| eval_ui `--check` | 시행 1 (FT) · 2 (BL) | CHECK_OK (§1) |
| trial_auto 실물 기록 자체 시험 | B1 · 같은 run ep 0 | §5 끝 문단 |

- 실물 SO-101 · 카메라 연결 0 회다. `eval/rollouts/` · `results/` 는 비어 있다.
- 시험 출력은 `tests/_out/` 에 있다.

## 7. 실물 평가 전 남은 위험 [사실 — 확인되지 않은 것]

1. **fault_latch 는 실물에서 돈 적이 없다.** 가짜 장치에서 주입한 예외 (predict_action_chunk 의 RuntimeError) 로만 확인했다. CUDA OOM · 장치 오류 같은 다른 예외 경로에서 같은 로그 줄이 나오는지는 확인하지 않았다 (코드상 모든 Exception 이 같은 줄로 로그됨).
2. r2_safety 규칙이 실물에서 실제로 걸린 적은 없다. 실물 서보에서 '현재 위치 유지' 뒤 정지 거리 · 시간은 재지 않았다.
3. (v2 로 바뀜) 자동 복귀는 없다. 대신 **종료 뒤 팔이 멈춘 자리에서 토크를 켠 채 남는다** (뻗은 자세일 수 있음).
   - 서보가 오래 무게를 버티면 과부하 보호가 작동할 수 있다. 그러면 토크가 꺼지고 팔이 내려올 수 있다 (STS3215 보호 설정은 확인하지 않음).
   - 시행 뒤 곧바로 safe_home 또는 손으로 받친 release 를 한다.
4. 서보 bus 가 끊기면 제자리 유지 · 끊기 기록이 실패할 수 있다. `end_state.json` 에 `torque_left_on: "unknown"` 이 남는다. 마지막 Goal 을 유지하므로 전원 차단이 필요하다 (팔을 받친 뒤).
4b. safe_home.py 는 실물에서 돈 적이 없다 (가짜 bus 시험만).
   - 관절 공간 직선 경로라 상자 · 카메라와의 거리를 계산하지 않는다. 사용자가 경로를 보고 `home` 을 입력한다.
   - 그리퍼는 쓰지 않아 큐브를 쥔 채면 그대로 쥐고 간다.
4c. 다음 시행 연결 (lerobot `configure()`) 은 토크를 잠깐 끈다. 팔이 접은 자세가 아니면 그 순간 내려온다. 게이트로 막지만, 게이트는 기록 (end_state · home_logs · rest) 만 본다.
4d. eval_ui 가 아닌 프로세스 종료 (kill -9 · 정전 · 파이썬 충돌로 finally 가 안 돌 때) 는 end_hold 가 돌지 못한다. 서보는 마지막 Goal 을 유지한다 (토크를 끄는 코드도 안 돌므로).
5. 충돌 · 끼임 감지는 stall 규칙 (0.67 s) 뿐이다. 서보 토크 · 과전류 설정은 확인하지 않았다.
6. K1 시행 (3 · 4 · 7 · 8) 은 과거 같은 자리에서 pan −109° 사례가 있었다. over_target 은 약 −65.5° 에서 걸리게 되어 있다.
7. over_target 은 판 시작 front 사진에서 큐브를 찾을 때만 켜진다. 손 · 다른 빨간 물체가 사진에 있으면 그 판만 꺼진다 (`r2_safety.csv` episode_start 에 이유가 남음). pan 절대 한계 규칙은 그대로다.
8. 판당 프로세스 1 개라 모델 로딩이 8 번 (각 2–3 분) 이다. 시행 사이 조명 · 큐브 · 상자 위치가 바뀔 수 있다 (시작 사진 · 분석 F11 카메라 이동 점검으로 기록만 됨).
9. M7: FT 가 일부 상태 (U8 · K7) 에서 BL 보다 wrist_flex 를 약 8° 낮게 예측했다 [재추론]. 파일럿 자리는 아니다.
10. `--episodes 1` 이라 eval_ui 의 '초기화 중 P/F' 단계 대신 판 종료 뒤 판정 질문이 나온다. r2_safety 의 '다음 판 자리' 안내 줄은 다음 시행 행을 보여 주지만, 다음 시행은 새 프로세스다.

11. (11-05 시행 1 에서 확인) `post_trial.sh` 1 단계 `p00b_verify_run.py` (d2 스크립트, 수정하지 않음) 는 실행 설정 점검에 `checkpoints/020000` 문자열을 요구한다 (79 행). FT 시행 (1 · 4 · 5 · 8) 에서는 `F4 실행 설정 … checkpoint 020000 ✗ → VERIFY_FAIL 1` 이 항상 나온다. 나머지 F1–F11 은 따로 본다. 체크포인트 확인은 trial_manifest 의 SHA-256 이 맡는다.

## 8. 사용자 실행 순서

`RUN_REAL_PILOT.md`:
- 1 절: 점검
- 2 절: 시행 1 (Phase 2) → post_trial → record_trial → `gate.sh go` / `stop`
- 3 절: 시행 2–8
- 4 절: 기록 위치

8 회 결과는 파일럿이다. 성공률로 일반화하지 않는다 (조건당 모델별 1 판).
