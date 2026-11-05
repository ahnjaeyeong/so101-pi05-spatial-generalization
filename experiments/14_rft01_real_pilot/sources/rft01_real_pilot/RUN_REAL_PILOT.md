# rft01 실물 파일럿 — 사용자 실행 순서

작성 2026-11-05.
- **아래 2 · 3 단계 명령은 팔에 토크를 걸고 정책이 팔을 움직인다. 사용자가 직접 터미널에서 실행한다.**
- Claude 는 로봇 · 카메라에 연결하지 않았고, 실물 실행을 시작하지 않았다.
- 명령은 기존 d2 / R2 실물 평가 체계 (`scripts/eval_ui.py` + R2 세션 shim + `r2_safety`) 를 그대로 쓴다. 새로 더한 것은 `fault_latch` (추론 오류 래치) 하나뿐이다.
- 근거와 검증 결과는 `README.md`.

## 0. 시행표 (`config/pilot_plan.csv`)

모두 Known 자리 (K 표시). 쌍마다 같은 자리 · 같은 각도로 두 모델을 연속 실행하고, 쌍 안 순서를 바꾼다 (FT·BL / BL·FT / FT·BL / BL·FT).

| 시행 | Phase | 쌍 | 모델 | 자리 | 각도 |
|---|---|---|---|---|---|
| 1 | 2 (첫 안전 확인) | P1 | **FT** rft01 001000 | K3 | 0 |
| 2 | 3 | P1 | BL d2 020000 | K3 | 0 |
| 3 | 3 | P2 | BL | K1 | 0 |
| 4 | 3 | P2 | FT | K1 | 0 |
| 5 | 3 | P3 | FT | K3 | R30 ↻ |
| 6 | 3 | P3 | BL | K3 | R30 ↻ |
| 7 | 3 | P4 | BL | K1 | L30 ↺ |
| 8 | 3 | P4 | FT | K1 | L30 ↺ |

- K1 = (−8.5, 26.5) cm, 큐브 방위 약 −35.5°. K3 = (−8.5, −3.5) cm, 약 +32.9°.
- 각도: 0 = 큐브 면이 로봇 정면과 나란히, R30 = 위에서 볼 때 시계 방향 30°, L30 = 반시계 30° (d2 규칙: 0 = ±15°, L30 = +15…+37.5°, R30 = −15…−37.5°).
- 시행 1 은 K3 이다. 과거 −109° Pan 이탈 (A0 · B1) 은 두 번 모두 K1 에서 나왔다.

## 1. 실행 전 점검 (사용자, 매 실행 전)

1. 다른 프로세스가 팔 · 카메라 · GPU 를 쓰지 않는지 확인한다. 출력이 없어야 한다.

   ```bash
   pgrep -af "lerobot|r12_collect|record_ui|eval_ui|teleop|hil_dagger" ; nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader ; fuser -v /dev/so101_follower /dev/cam_front /dev/cam_wrist
   ```

   eval_ui 도 시작할 때 GPU · lerobot 프로세스 · twin 컨테이너를 보고 막는다.
2. 팔 · 전원:
   - follower 12 V 전원 스위치 (또는 어댑터 플러그) 에 손이 닿는 자리에 선다. **비상시 전원 차단이 최종 정지 수단이다.**
   - 전원을 끊으면 토크가 사라져 팔이 자기 무게로 내려온다. 쉬는 자세 근처에서는 낙하가 작지만, 팔을 뻗은 자세에서는 손으로 받칠 준비를 한다.
   - Leader 는 이 평가에서 쓰지 않는다.
3. 작업공간:
   - 팔 반경 안에 큐브 1 개와 상자만 둔다. 손 · 케이블 · 다른 빨간 물체를 치운다.
   - 상자 · 카메라 위치는 d2 평가 때 그대로 둔다. 분석이 카메라 이동 ≤ 6 px 를 점검한다.
   - K1 쪽 (로봇 기준 왼쪽, pan −) 으로 팔이 크게 돌 수 있다 (과거 −109°). pan 끝 쪽 공간도 비운다.
4. 팔 시작 자세는 기존 d2 평가와 같은 쉬는 자세 (접은 자세) 다. eval_ui 는 연결 순간 자세를 '처음 자세' 로 잡는다. `pose_check` 는 기록만 한다.
5. 카메라 자동 노출 · 자동 WB: eval_ui 점검 줄에 ⚠ 가 없어야 한다.

## 2. Phase 2 — 시행 1 (FT 1 회, 첫 안전 확인)

옵션만 먼저 확인한다 (팔 · 카메라 연결 없음):

```bash
CHECK=1 ~/so101_runs/main_k8/rft01_real_pilot/scripts/run_trial.sh 1
```

- `CHECK_OK ... RTCConfig(... EXP ... execution_horizon=20) ... queue_threshold=30 ... max_relative_target=8.0 ... arm_filter=False ... guard=warn` 가 나와야 한다.

실행:

```bash
~/so101_runs/main_k8/rft01_real_pilot/scripts/run_trial.sh 1
```

- 스크립트가 게이트와 체크포인트 SHA-256 (약 7 s) 을 확인한 뒤 eval_ui 를 띄운다.
- eval_ui 가 `Enter = 시작` 을 묻는다 → Enter.
- 모델 로딩 2–3 분 동안 '큐브 배치' 창이 뜬다. 창에 시행 1 자리 (K3 · 0°) 윤곽이 보인다.
- **⏸ 준비**: 큐브를 놓고 창에 '맞음' 이 뜨면 터미널에서 → (또는 Enter).
- **▶ 실행**: 판 최대 60 s. 아래 종료 기준대로 끝낸다.
- **v2 (11-05): 판이 어떻게 끝나든 (60 s · → · 안전 정지 · 추론 오류 · Ctrl+C) 팔은 자동으로 돌아가지 않는다.**
  - 멈춘 자리에서 토크를 켠 채 유지한다. 팔이 뻗은 자세일 수 있다.
  - 콘솔에 `[end_hold] END_HOLD 종료: 자동 복귀 없음 …` 가 나온다. run 폴더에 `end_state.json` 이 생긴다.
- 이어서 P(성공) / F(실패) 와 메모를 묻는다.

### 판 종료 기준 (8 회 모두 같게)

| 상황 | 하는 일 |
|---|---|
| 큐브를 상자에 넣고 팔이 물러남 | → (판 끝) — 성공 |
| 60 s 경과 | 자동 종료 (lerobot `episode_time_s=60`) — 그때까지 상자에 없으면 실패 |
| r2_safety 정지 · fault_latch | 자동 종료. 콘솔 `R2_SAFETY STOP` 또는 `FAULT_LATCH` 줄 · 배치 창 빨간 줄 |
| 위험 (충돌 · 끼임 · 케이블 당김 · 상자 · 카메라 접촉 우려) | **Ctrl+C**. 더 급하면 전원 차단 |

- 실패해 보인다는 이유만으로 60 s 전에 → 로 끊지 않는다 (두 모델 같은 기준).
- 판을 버리는 ← 는 큐브를 잘못 놓았을 때만 쓴다.
  - v2 에서 ← 는 '이 판 버리고 실행 종료' 다 (복귀 · 재시작 없음).
  - 팔을 쉬는 자세로 돌린 뒤 (아래 safe_home) `RERUN="배치 실수"` 로 run_trial.sh 를 다시 실행한다.

### 시행 직후 — 팔을 쉬는 자세로 (사용자가 직접, 매 시행)

eval_ui 가 끝나면 (프롬프트로 돌아오면) 팔은 멈춘 자리에서 토크 유지 중이다.

```bash
python3 ~/so101_runs/main_k8/rft01_real_pilot/scripts/safe_home.py --run <run 폴더> --check   # 팔 연결 없이 끝 자세 · 목표 확인
python3 ~/so101_runs/main_k8/rft01_real_pilot/scripts/safe_home.py --run <run 폴더>           # ※ 팔이 움직임
```

- safe_home 은 점검 H1–H7 을 보여 준다. 모두 PASS 일 때만 계획 표를 보여 주고 묻는다.
  - 경로 (상자 · 카메라 · 손 · 케이블) 를 보고 **`home` 을 정확히 입력**해야 움직인다 (15°/s, 그리퍼 그대로).
  - 멈추려면 Ctrl+C (그 자리 유지). 급하면 전원 차단.
- 도착 뒤 토크를 끄려면 `release` 를 입력한다. Enter 는 토크를 켠 채 둔다 (다음 시행 연결 때 lerobot 이 어차피 잠깐 끔).
- 점검 실패 · 도중 멈춤이면 팔은 그 자리에서 토크 유지다. 이때 둘 중 하나를 한다:
  - 팔을 손으로 받치고 `--mode release` (접은 자세가 아니면 `받쳤음` 까지 입력) 로 토크를 끈 뒤 손으로 쉬는 자세에 둔다. 그다음 `gate.sh rest "손으로 둠"`.
  - 전원을 차단한다 (팔을 받친 뒤).
- 다음 run_trial.sh 는 직전 run 이 시작 자세에서 > 5° 떨어져 끝났는데 safe_home 도착 기록도 `gate.sh rest` 도 없으면 막는다.
  - 이유: 다음 연결 때 토크가 잠깐 꺼져 팔이 내려오기 때문.
- 토크를 켠 채 오래 두지 않는다 (서보 과부하 보호가 작동하면 토크가 꺼질 수 있음).

### 시행 1 뒤 (로봇 연결 없음)

```bash
~/so101_runs/main_k8/rft01_real_pilot/scripts/post_trial.sh <run 폴더>     # run_trial.sh 가 끝에 경로를 보여 줌. GPU 2–5 분
python3 ~/so101_runs/main_k8/rft01_real_pilot/scripts/record_trial.py <run 폴더>
```

- record_trial.py 는 [기록] · [자동 후보] 값을 보여 준 뒤 기본값 없이 묻는다: 첫 파지 · 빈 파지 · Pan 반전 · Wrist 재획득 · 최종 성공 · 중단 · 개입 · 이유 · 메모.
- 시행 1 에서 비정상 Pan (목표를 크게 지나쳐 계속 회전), 그리퍼 이상 행동, 종료 기능 (→ · 자동 종료 · 복귀) 이상이 **없으면**:

  ```bash
  ~/so101_runs/main_k8/rft01_real_pilot/scripts/gate.sh go "시행 1 확인: <본 것>"
  ```

- **문제가 있으면**:

  ```bash
  ~/so101_runs/main_k8/rft01_real_pilot/scripts/gate.sh stop "<이유>"
  ```

  run_trial.sh 는 `results/STOP` 이 있으면 실행하지 않는다.

## 3. Phase 3 — 시행 2–8

한 번에 이어서 하려면 (11-05 v3.1): `~/so101_runs/main_k8/rft01_real_pilot/scripts/run_series.sh`
- 남은 시행을 모델별 세션으로 (모델당 로딩 1 회). 판마다 P/F → (→) → 팔 (5 관절) 시작 자세 복귀 15°/s → 그리퍼 시작 값 → 다음 판.
- 시행 9–16 (11-05 추가): Unknown U2 L30 · U7 45 · U8 0 · U1 R30 (R2 진단과 같은 좌표 · 각도) × FT (9–12) · BL (13–16).
  지금 상태에서 순서: FT 세션 (8 · 9 · 10 · 11 · 12) → BL 세션 (13 · 14 · 15 · 16). 모델 교대 아님.
- 키는 터미널 또는 배치 창 (창을 한 번 클릭) 에서: → 시작 · 다음 · P 성공 · F 실패 · ← 버리기 · Esc 끝 · Ctrl+C 비상 정지. 한글 입력 상태 (ㅔ · ㄹ) 도 됨.
  배치 창 위쪽 = 이번 (초기화 땐 다음) 판 자리 · 각도, 오른쪽 = 이번 판 판정 (eval_ui 기록) · 계획 목록 (판정 표시).
- Ctrl+C · Esc · 예외로 끝나면 움직이지 않고 멈춘다. 복귀 점검 실패 · 저장 0 판 · STOP · 모델 검증 FAIL 도 멈춘다. 다시 같은 명령이면 이어진다.
- 시험: tests/test_series.sh (17) · tests/test_ui_keys.py (8) · test_fake_pilot_e2e.py series_home · series_ctrl_c.

아래는 하나씩 하는 방법 (같은 규칙).

같은 명령을 번호만 바꿔 순서대로 실행한다. 매 시행 뒤 `safe_home.py` (팔 쉬는 자세) → `post_trial.sh` → `record_trial.py`.

```bash
~/so101_runs/main_k8/rft01_real_pilot/scripts/run_trial.sh 2
# … post_trial.sh · record_trial.py
~/so101_runs/main_k8/rft01_real_pilot/scripts/run_trial.sh 3
# …
```

run_trial.sh 가 막는 경우 (그때 실행하지 않음):
- 앞 시행 결과가 `results/trials.csv` 에 없음.
- 시행 2 이후인데 `results/phase2_go.txt` 가 없음.
- `results/STOP` 이 있음.
- 앞 시행에 안전 개입 기록이 있는데 확인 파일이 없음. 확인 후 계속하려면 `gate.sh ack <N> "메모"`.
- 같은 시행을 다시 하려는데 `RERUN="이유"` 가 없음. 다시 하면 새 run ID 가 생기고 이전 결과는 남는다.
- (v2) 직전 run 이 시작 자세에서 > 5° 떨어져 끝났는데 safe_home 도착 · `gate.sh rest` 기록이 없음. end_state.json 이 없는 경우도 막는다.
- 체크포인트 SHA-256 이 다름.

## 4. 기록 위치

| 무엇 | 어디 |
|---|---|
| run 폴더 (시행마다 새로, 시각 + tag) | `eval/rollouts/<YYYYMMDD_HHMMSS>_<1k\|20k>_t<NN>_<ft\|bl>_<자리>/` |
| ├ 영상 · state · action | `dataset/` (front · wrist 영상, observation.state, action) |
| ├ 필터 전·후 action (필터 꺼짐 → 같음) | `filter_log.csv` |
| ├ chunk · 관측 · 타이밍 | `diag/` (ROLLOUT_DIAG) |
| ├ 시작 사진 · 자세 | `start_images/` · `pose_check.txt` |
| ├ 안전 정지 · 배치 확인 | `r2_safety.csv` |
| ├ 추론 오류 래치 | `fault_latch.csv` |
| ├ eval_ui P/F · 메모 | `results.csv` · `results.md` |
| ├ 모델 · SHA · 코드 SHA · 조건 | `trial_manifest.json` |
| ├ 종료 처리 (v2) | `end_state.json` · `end_hold.csv` |
| 복귀 기록 (safe_home) | `results/home_logs/<run>_<시각>.json` · 손으로 둔 확인 `results/rest_<run>.txt` |
| 실행 장부 (실행마다 1 줄) | `results/run_ledger.csv` |
| 실행 manifest 원본 | `results/manifests/trialNN_<시각>.json` |
| 자동 지표 · R2 분석 | `reports/<run>/` (trial_auto.md · report.md · events.csv …) |
| **시행 결과표** | `results/trials.csv` (record_trial.py, 추가만) |
| 진행 게이트 | `results/phase2_go.txt` · `ack_trialNN.txt` · `STOP` |
| eval_ui 누적 | `eval/index.md` · `eval/results_all.csv` |

## 5. 이 파일럿에서 하지 않는 것

- 000500 체크포인트 실행.
- Arm Filter 켜기.
- r2_safety 임계값 바꾸기.
- R1 상황 (큐브를 지나치게 하는 시작 자세) 을 일부러 만들기.
- Leader · HIL.
