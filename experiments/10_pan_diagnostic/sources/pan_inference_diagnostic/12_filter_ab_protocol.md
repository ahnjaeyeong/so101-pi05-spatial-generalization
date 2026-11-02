# 12 arm_filter 켬 / 끔 실물 대조 — 실행 절차 (사용자 실행, 승인 뒤에만)

작성 2026-10-29. 근거: 11 문서 (오프라인 비교 · 안전 평가). **Claude 는 로봇을 연결 · 구동하지 않는다.** 필터 끔 실물 실행은 사용자가 승인한 뒤에만 한다.

## 1. 고정 조건 (두 묶음 같음)

| 항목 | 값 |
|---|---|
| 체크포인트 | d2 020000 |
| 추론 | RTC guided EXP, h 20, mgw 10, denoise 5, queue_threshold 30, fps 30 |
| clamp | max_relative_target 8 |
| 기록 | `ROLLOUT_DIAG=1`, `--rollout_guard=warn` (감시 경고만 남기고 명령은 바꾸지 않음 — 필터를 끈 쪽에서도 filter_log · diag 를 남기려고 두 묶음 모두 켬) |
| **유일한 변수** | `--arm_filter=true` (A) / `--arm_filter=false` (B) |

- `--rollout_guard=warn` 은 10-29 파일럿 (guard off) 과 다르다. 경고 로그만 추가되며 제어 명령은 같다 (`arm_filter.py` RolloutGuard: warn 은 `logger.warning` 만).
- 2026-10-29 `eval_ui --check` (ROLLOUT_DIAG=1, 하드웨어 연결 전 멈춤) 결과:
  - A: arm_filter True · guard warn
  - B: arm_filter False · guard warn
  - 둘 다 RTC guided EXP mgw 10 h20 · queue 30 · clamp 8 · fps 30.

## 2. 위치 · 큐브 · 시작 자세

- **위치:** 표시된 K 자리 4 곳 K1 (−8.5, 26.5) · K3 (−8.5, −3.5) · K6 (−17.0, −3.5) · K7 (−25.5, 26.5).
  - 표시가 있어 두 묶음에서 같은 자리를 다시 놓을 수 있다.
  - 파일럿에서 K 4 판의 사진 좌표 − 명목은 0.2–0.6 cm 였다.
  - 파일럿 결과: K1 · K3 실패 (덜 다가감), K6 · K7 성공.
- **큐브 각도:** 0 (큐브 면이 로봇 정면과 나란히).
  - 파일럿에서는 K1 +24° · K6 −25° · K7 +19° 로 0 이 아니었다.
  - 판 시작 사진에서 각도를 다시 잰다 (`cube_angle.measure_at`). 차이가 크면 분석에서 따로 본다.
- **시작 자세:** 네 실행 모두 같게 한다.
  - eval_ui 는 실행을 시작할 때의 팔 자세를 '처음 자세' 로 잡고, 판마다 그 자세로 돌아간다. 그래서 실행마다 시작 전에 팔을 같은 자세에 두어야 한다.
  - 파일럿 시작 pan 은 +5.4 … +7.0° (학습 시작 범위 −14.8 … +3.8°, 평균 −4.3°) 였다.
  - 학습 평균 근처 (pan ≈ −4, lift ≈ −103, elbow ≈ 95, wrist_flex ≈ 65, roll ≈ 2.5) 로 맞출지, 파일럿과 같게 둘지는 사용자가 정한다.
  - eval_ui 의 `pose_check.txt` 가 실행마다 기록한다 (자세로 막지 않음).
- 카메라 · 조명 · 상자 자리는 그대로 둔다. 판 시작 때 손 · 다른 빨간 물체가 화면에 없게 한다.

## 3. 순서 (ABBA, 16 판)

| 실행 | 조건 | 판 순서 | 비고 |
|---|---|---|---|
| S1 | A 필터 켬 | K1 · K3 · K6 · K7 | 기준 |
| S2 | **B 필터 끔** | K1 · K3 · K6 · K7 | **안전 확인용.** 첫 2 판을 특히 지켜본다 |
| S3 | B 필터 끔 | K7 · K6 · K3 · K1 | |
| S4 | A 필터 켬 | K7 · K6 · K3 · K1 | |

- 조건마다 위치당 2 판, 8 판씩이다.
- 실행마다 모델을 새로 불러온다 (2–3 분). 실행마다 '세션 두 번째 추론의 inference_delay 0' 이 첫 판 chunk 1 에서 한 번 생긴다 (05 문서). 네 실행이 같은 조건이다.

## 4. 명령

```bash
cd ~/so101_boxpick
# S1 · S4 (A, 필터 켬)
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py --session main_k8/d2 --tag filt_on --episodes 4 \
  --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true --rollout_guard=warn
# S2 · S3 (B, 필터 끔)
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py --session main_k8/d2 --tag filt_off --episodes 4 \
  --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn
```

판 흐름은 파일럿과 같다:
1. 큐브를 놓고 → 로 시작한다.
2. 끝나면 → 를 누른다.
3. 복귀 중 P/F 를 누른다.
4. 마지막 판은 초기화 없이 저장된다.

메모 (판 번호 0–3):

`<번호> <K> first=<Y|N> lift=<Y|N> drop=<Y|N> final=<Y|N> side=<C|L|R|?> depth=<D|S|E|?> <특이사항>`

| 기호 | 뜻 |
|---|---|
| first | 첫 닫힘에서 큐브를 쥐었나 |
| lift | 들어 올렸나 |
| drop | 들어 올린 뒤 놓쳤나 |
| final | 상자에 넣었나 |
| side | 손가락 사이 큐브 위치 (C 중앙 · L 로봇 왼쪽 손가락 쪽 · R 오른쪽 · ? 모름) |
| depth | D 깊게 · S 얕게 (손가락 끝) · E 헛잡기 · ? 모름 |

사람 눈 관찰로 기록하고, 자동 분류 (11 문서 1 절) 와 따로 둔다.

## 5. 안전 중단

- S2 첫 2 판 중 다음이 보이면 즉시 `Esc` (저장 후 종료) 또는 `Ctrl+C` 를 누르고, 그 묶음을 멈춘다:
  - 탁자 · 상자에 부딪힘
  - 큰 떨림 · 튐
  - 같은 자리에서 관절이 버티며 소리 냄
- 그래도 위험하면 팔로워 12 V 를 끈다.
- 멈춘 경우 Claude 가 기록을 읽어 원인을 보고하고, 더 안전한 대안을 낸다. 예: 필터 α 만 1.0 으로 (EMA 끔 · 속도 제한 유지), 또는 속도 제한만 끔.
- guard warn 경고 (stall 등) 는 `debug.log` 에 남는다.

## 6. 실행 뒤 점검 · 분석 (Claude, 읽기만)

```bash
cd ~/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts
for R in <S1> <S2> <S3> <S4>; do
  nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p05_replay_check.py $R/diag
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p00b_verify_run.py $R --expect_filter <true|false>
  PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python p07_new_eval_analysis.py $R
done
# 조건별 묶음: P09_OUT · PILOT_DIR 를 같은 폴더로 (예: ../filter_ab/A, ../filter_ab/B)
P09_OUT=../filter_ab/A PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p09_pilot_summary.py --runs <S1> <S4> --labels K1,K3,K6,K7,K7,K6,K3,K1
PILOT_DIR=../filter_ab/A PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p14_grasp_analysis.py
# B 도 같게 (S2 S3, --labels K1,K3,K6,K7,K7,K6,K3,K1)
```

비교 지표 (우선순위 순):
1. 첫 파지 손목 화면 위치: 중앙 · 앞쪽 (덜 다가감) · 아래쪽 · 가려짐 · 판단 불가. 좌우 편향은 판단 가능할 때만.
2. 깊이: 깊은 · 얕은 · 헛잡기 · 판단 불가.
3. 첫 파지 성공.
4. 들어 올린 뒤 놓침.
5. 최종 상자 투입.
6. 닫힘 시작 때 TCP z · 관절의 이웃 사람 대비 차.
7. Pan t90 (참고).

판 8 개씩이라 차이를 확정할 수 없다. 결과는 판별 표와 개수로만 낸다.
