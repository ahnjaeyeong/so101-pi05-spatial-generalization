# D단계 (③) 실물 구동 체크리스트 — ③a 잡고 들기 · ③b 놓기 · 살포시 놓기(10절)

- **범위**: ③a만 합니다.
  - 흐름: 학습 시작 자세로 이동 → 정책으로 잡고 3 cm 들기 → 12 s 버티기 → 집은 자리에 내려놓기.
  - 박스·탁자로 옮기기(③b)는 ③a 결과를 본 뒤 따로 준비합니다.
- **속도 천장**: 0.5 rad/s (`constants_e0j0.yaml` `max_joint_vel_rad_s: 0.5`). 1.0은 사용자 지시가 있을 때만 씁니다.
  - IK 이동(시작 자세·내려놓기)은 이보다 낮은 0.3 rad/s입니다.
- **명령 입력**: 모든 명령은 사용자가 Thor 데스크톱 터미널에서 직접 칩니다.
  - 터미널은 T1(정책 서버), T2(트윈), T3(goal), T4(정지)를 씁니다.
- **12 V 스위치 옆에 있어야 합니다.** `/e0j0/stop`은 소프트 정지이고, 비상정지는 12 V입니다.

## P. 먼저 — 카메라 30 Hz 재확인 (② probe, 토크 off)

DDS 공유 메모리 16 MB 설정을 넣었습니다(커밋 cc8627d). 실제 카메라로 30 Hz가 나오는지 봅니다.

**2026-10-08 10:57 통과**: front 30.08 Hz, wrist 30.13 Hz, stale 0 (`shadow_20261008_015719`). 다시 할 필요는 없습니다.

```bash
# T2
cd ~/Ros2_e0j0 && bash scripts/e0j0_up.sh real-ro
#   확인할 줄: "started: twin_ws_dev (… dds=/ws/src/twin_bringup/config/fastdds_shm16mb.xml)"
#   마지막 줄: "E2 ready … [real  /dev/ttyACM0, torque off]"
# T3
cd ~/Ros2_e0j0 && bash scripts/e0j0_shadow.sh probe 20
#   summary 의 "camera_hz": front·wrist 둘 다 ≥ 28  (이전 17–25),  "joint_states_hz" ≈ 30
# T2 — 끝나면
bash scripts/dev_down.sh            # 기대: OK: processes=0 zombies=0 container=removed
```

- 정책 서버는 필요 없습니다.
- `dds=default`가 찍히거나 `camera_hz`가 28보다 낮으면 여기서 멈추고 알려 주세요.

## 0. 시작 전 확인 (T3)

| 확인 | 명령 / 방법 | 기대 |
|---|---|---|
| 학습 안 돎 | `pgrep -a -f "lerobot-trai[n]"` | 아무것도 안 나옴 |
| lerobot·다른 서버 안 돎 | `pgrep -a -f "lerobot-recor[d]\|lerobot-rollou[t]\|lerobot-teleoperat[e]\|record_u[i]\|policy_serve[r]\|fake_polic[y]"` | 아무것도 안 나옴 |
| GPU 비어 있음 | `nvidia-smi --query-compute-apps=pid,used_memory --format=csv` | 머리줄만 |
| 컨테이너 없음 | `docker ps --format '{{.Names}}'` | 아무것도 안 나옴 (박사님 컨테이너가 있으면 **멈춤**) |
| 팔로워 장치 | `ls -l /dev/serial/by-id/` | `…5B8E116810-if00 -> ../../ttyACM?` |
| 카메라 자동 3/1/0 | `for d in /dev/cam_front /dev/cam_wrist; do v4l2-ctl -d $d -C auto_exposure,white_balance_automatic,exposure_dynamic_framerate; done` | 둘 다 3 / 1 / 0 |
| 장면 | 학습 때처럼 놓습니다: 흰 탁자, 갈색 박스 왼쪽, 빨간 큐브(53 mm) 오른쪽 앞. 큐브 위치는 사진이나 메모로 남깁니다 | — |
| 팔 | 접힌 휴식 자세, 토크 off. 자세는 기록만 합니다 | — |
| **③ 전 덤프** | `PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/scripts/servo_dump.py --arm follower` | `저장: …_follower.json` → **BEFORE** 경로로 적어 둡니다 |

## 1. 정책 서버 (T1)

```bash
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/e0_j0/policy_server.py
#   기대: [policy] loaded in ~166 s … → [policy] listening 172.17.0.1:5555 …
```

## 2. 실물 구동 기동 (T2, TTY, 12 V 옆)

```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_up.sh real
```

- 기대 순서:
  1. `started: twin_ws_dev (… dds=…fastdds_shm16mb.xml)`
  2. 헬스체크
  3. `== 토크 on …` → `success`
  4. `== 자기 점검 …`: 팔이 **학습 시작 자세** `[70.9, 15.8, 34.1, 74.3, 6.8, 0.6]`로 갑니다.
     - 휴식 자세에서 약 1.7 s 걸리고, TCP는 휴식 자세보다 내려가지 않습니다(관절별 램프 0.5 rad/s, 오프라인 계산).
     - 관절마다 0.1 rad 왕복한 뒤 다시 시작 자세로 갑니다.
     - 왕복 방향은 **탁자에서 멀어지는 쪽**입니다.
       - shoulder_lift: −0.1 (TCP +5.9 mm)
       - elbow_flex: +0.1 (+1.6 mm)
       - wrist_flex: +0.1 (+10.2 mm)
       - pan·roll·집게: +0.1 (높이 변화 없음)
     - 표 각 줄에 `방향 ±1 (z …)`이 찍히고, 6줄 모두 `OK`가 기대값입니다.
     - 단일 관절 이동의 도달 기준 q_tol은 실험 프로파일에서 **0.06 rad**입니다(커밋 700097f; 원본 0.04는 P32 기준이라 14:47에 wrist_flex 0.043으로 보류됨). `== demo.launch.py …` 줄에 `arm_limits_file:=/ws/src/twin_e0j0/config/arm_limits_thor_e0j0.yaml`이 보여야 합니다.
  5. 마지막 줄 `E2 ready … [real real_kinematic /dev/ttyACM0, torque on — READY]`
  6. 그다음 줄 `기동 로그 → ~/Ros2_e0j0/ros2_ws/e0j0_runs/up_logs/up_<시각>_real.log`
     - 자기 점검 표, 토크·게인 줄, `E0J0 중력 모형: comp=False P=16 …` 줄이 이 파일에 남습니다. `dev_down` 뒤에도 남아요.
- 바뀐 점 (2026-10-08 오후, 커밋 f5cec74):
  - 자기 점검과 `/twin/home`(= `dev_home.sh`) 자세는 이 실험 프로파일에서 URDF 영점(ㄱ자)이 아니라 학습 시작 자세입니다.
    - 이유: P16에서 ㄱ자 자세의 처짐(37 mm)이 도달 벽(22.5 mm)을 넘습니다. 시작 자세의 처짐은 9 mm입니다.
  - ③a는 중력 보상을 **끄고** 돕니다(`gravity_comp.enabled: false`). 버티는 동안 실제 처짐과 모형 예측을 나란히 재서 모형을 검증합니다.
- 실패하면:
  - `FAIL at 토크 on`이면 팔을 벽 안 자세로 손으로 옮긴 뒤 다시 칩니다.
  - 자기 점검이 보류되면 `bash scripts/dev_down.sh --real`로 끝내고, 위 기동 로그 파일 경로를 알려 주세요.

## 3. ③a-0 — `/e0j0/stop` 시험 (첫 goal)

자기 점검이 팔을 이미 학습 시작 자세에 두므로, goal의 시작 자세 이동은 거의 0입니다. 그래서 **정책이 팔을 움직이기 시작한 직후**에 정지합니다. 큐브에 닿기 전이에요.

```bash
# T3
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --hold-only table1
# T4 — 팔이 정책으로 움직이기 시작하는 것을 보고 바로 (rollout 기준 정책 연결 뒤 1–1.4 s)
cd ~/Ros2_e0j0 && bash scripts/e0j0_stop.sh
```

| 보이는 것 | 뜻 / 할 것 |
|---|---|
| T4 `OK: 정지 요청 전달 (busy=True)` | 정상입니다. 팔은 다음 틱(≤ 33 ms) 안에 정책 명령을 멈추고 그 자리에 섭니다(토크 on) |
| T3 `result FAILED_HW (exception)` | 정상입니다. 기록 `detail`: `/e0j0/stop 요청으로 멈췄다`, `failed_stage`: `grasp_policy` |
| T4 `WARN: 진행 중인 goal 이 없었다` (rc 2) | goal이 아직 시작 전이었습니다. 아무것도 멈추지 않았으니 팔이 움직이면 **다시** 칩니다 |
| T4 `FAIL: /e0j0/stop 을 부르지 못했다` | **12 V를 끕니다** |
| 팔이 계속 움직임 | **12 V를 끕니다** |

- 다음 goal은 지금 선 자리에서 시작 자세로 돌아갑니다(0.3 rad/s). 움직이기 전에 경로의 바닥·벽을 전부 검사하고, 막히면 한 번도 보내지 않고 FAILED_HW로 끝냅니다.
- 정책이 10 s 안에 출발하지 않으면 정지를 칠 틈 없이 `policy_no_start`로 끝납니다(5번). 그때는 같은 goal로 다시 시도합니다.

## 4. ③a-1 — 잡고 들기 (12 s 버티기 → 내려놓기)

```bash
# T3
bash scripts/e0j0_goal.sh --hold-only table1
```

1. **시작 자세** (0.3 rad/s). 자기 점검이 이미 이 자세에 두므로 보통 거의 안 움직입니다. ③a-0 정지 뒤라면 그 자리에서 돌아옵니다.
   - 목표: practice_50 29번 편 첫 자세 `[70.9, 15.8, 34.1, 74.3, 6.8, 0.6]`. 50편 첫 자세 중앙값에 가장 가까운 실제 편입니다.
   - TCP는 휴식 자세와 거의 같은 자리이고 1 cm 위입니다. 큐브와는 13.9 cm 떨어져 있습니다.
2. **정책** (30 Hz)
   - lerobot rollout 기준으로, 출발은 1–1.4 s, 집게 열기는 5–6.5 s쯤입니다. 클립은 측정값 기준 8°입니다.
   - 몸통 관절은 드라이버 천장 0.5 rad/s를 넘지 못합니다. 학습·rollout(천장 없음)보다 느려 정책 명령보다 팔이 뒤처질 수 있습니다(기록 항목).
3. **넘겨주기**: 쥔 뒤 3 cm 들리면 정책을 끊고 집게를 `쥔 값 − 6`으로 조입니다.
4. **버티기 12 s**: 처짐(명령 FK z − 측정 FK z), 집게 측정값, 1 s마다 집게 Present_Load를 기록합니다.
   - 놓침 감지: 집게가 `쥔 값 − 4` 이하로 3틱 연속이면 FAILED_GRASP이고, 팔은 그 자리에 섭니다.
5. **내려놓기**: 집은 자세로 내려가 집게를 연 뒤 넘겨줄 때 자세로 물러납니다 → `result DONE`.

**바로 멈출 때**: T4 `bash scripts/e0j0_stop.sh`, 위험하면 12 V.
- 팔이 탁자·박스를 세게 누르거나 그쪽으로 빠르게 갈 때.
- 집게가 큐브를 쥔 채 소리·떨림이 계속될 때.
  - 참고: 집게 서보 과부하 보호는 Overload_Torque 25 %, 2 s입니다. 이게 걸리면 집게 힘이 빠져 큐브가 떨어지고, 놓침 감지가 FAILED_GRASP로 멈춥니다.

## 5. 정책이 출발하지 않을 때 (요청 3)

- **기다리는 시간**: 정책 연결(시작 자세 도착) 뒤 **10 s**입니다(`grasp.no_start_s`).
  - 출발 판정: 정책 action이 몸통 관절 하나라도 시작 자세에서 **3° 이상**(`no_start_deg`) 움직이라고 하면 출발로 봅니다. 기록에는 `policy_started` 사건으로 남습니다.
  - 근거: 10-07 rollout 3회는 1.0–1.4 s에 3°를 넘었습니다(가장 느린 편은 10°까지 3.4 s). 오늘 그림자 프레임을 고정해서 넣었을 때 늦은 출발이 7 s까지 있었습니다.
- **10 s가 지나면 실행기가 스스로 멈춥니다**:
  - 결과: `result FAILED_GRASP (grasp_not_held)`, 기록 `failed_stage: policy_no_start`.
  - 정책 연결을 끊고 명령을 더 보내지 않습니다. 드라이버는 마지막 명령(≈ 학습 시작 자세)을 토크 on으로 잡고 섭니다.
  - 정책이 거의 안 움직였으니 팔은 큐브에서 떨어진 시작 자세에 있습니다.
- **사람이 할 것** (둘 중 하나):
  - 다시 시도: `bash scripts/e0j0_goal.sh --hold-only table1`. 정책 상태(RTC 큐)는 goal마다 reset됩니다.
  - 끝내기: 아래 6번 정리.
- sim 확인(2026-10-08): 출발 안 하는 가짜 정책(`--still`)으로 시험했습니다. 정책 연결 10.0 s 뒤 `policy_no_start`로 멈췄고, 팔은 시작 자세에 섰습니다.
- **다른 멈춤** (모두 팔은 그 자리에 섭니다):

| 상황 | 결과 |
|---|---|
| 출발은 했는데 40 s 안에 넘겨주기 없음 | FAILED_GRASP, `grasp_policy` |
| 관측·정책 응답이 1 s 끊김 | FAILED_HW |
| TCP가 바닥(z −0.025 m) 아래 | FAILED_HW |
| 놓침 | FAILED_GRASP |

  - 팔이 큐브·박스 가까이 낮게 서 있으면, 6번의 `dev_down --real`(접기) 전에 접는 길에 큐브·박스가 없는지 봅니다. 걸리면 손으로 치웁니다(토크 on 팔 근처 주의).

## 6. 끝낼 때 — 정리 순서

1. T3 goal이 끝났는지 확인합니다(`result …` 줄).
2. **T1 정책 서버 Ctrl-C** → `[policy] RTC 추론 지연 (이번 세션): {…}` 줄을 남겨 둡니다.
3. **T2: `cd ~/Ros2_e0j0 && bash scripts/dev_down.sh --real`** → 접기(fold) → 토크 off.
   - 기대: `OK: processes=0 zombies=0 container=removed`.
4. `docker ps --format '{{.Names}}'` → 아무것도 안 나와야 합니다.
5. **12 V를 끄고** 5 s 뒤 **다시 켭니다**(트윈이 쓴 Goal_Velocity 등 RAM 값을 지웁니다).
6. **재투입 뒤 덤프**: `PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/scripts/servo_dump.py --arm follower` → **AFTER** 경로.
7. **레지스터 확인**: `/usr/bin/python3 ~/so101_boxpick/e0_j0/check_restored.py <BEFORE> <AFTER>`
   - 기대: 6개 모두 `OK  Goal_Velocity=0 Torque_Enable=0`, 마지막 줄 `결과: PASS`.
   - `Goal_Velocity`(레지스터 46)가 0이 아니면 12 V를 다시 끄고 켭니다. 그래도 FAIL이면 lerobot을 쓰기 전에 알려 주세요.
8. 기록 모으기: `/usr/bin/python3 ~/so101_boxpick/e0_j0/collect_runs.py`. 시험 기록은 `~/so101_runs/e0_j0/runs/trial_<시각>.jsonl`에 남습니다.

## 8. ③a 반복 — 큐브 위치를 바꿔 가며 (2026-10-08 오후 추가)

**먼저 알아 둘 것**: 첫 ③a 두 번은 넘겨준 지 0.4 s 만에 **놓침 오판**으로 실행기가 멈췄습니다. 종이 큐브가 조임(쥔 값 − 6)에 눌려, 측정값이 놓침 문턱(쥔 값 − 4) 아래로 내려갔기 때문이에요. 그래서 12 s 버티기 기록이 없습니다. 이번 반복은 **`--slip-log`**(놓침을 기록만 하고 계속)로 돌려 버티기·처짐·집게·부하 자료를 모읍니다. 사람이 큐브를 눈으로 지켜봅니다.

**세션** — 한 번 띄우고 여러 번 돌립니다.
```bash
# T1 정책 서버 (떠 있으면 그대로)
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/e0_j0/policy_server.py
# T2 실물 기동 (TTY, 12 V 옆) → 자기 점검 6줄 OK → READY
cd ~/Ros2_e0j0 && bash scripts/e0j0_up.sh real
```

**한 번 시도** (T3) — 큐브를 손으로 놓은 뒤:
```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --hold-only --slip-log --cube "<위치 메모>" table1
```
- 기대 흐름: 시작 자세 → 정책이 잡고 3 cm 들기 → 12 s 버티기 → 집은 자리에 내려놓기·열기·물러나기 → `result DONE`.
- 결과는 자동으로 `runs/index.md`의 **"실물 (실제 π0.5)"** 표에 쌓입니다. 칸: 큐브 메모, 출발, 쥠, 넘겨주기 높이, 버티기(처짐·집게·부하), 놓침, 결과.
- 끝나면 팔은 큐브 위 공중에 섭니다. 다음 큐브를 놓을 때 토크가 켜진 팔에 손이 닿지 않게 합니다.

**큐브 위치** (학습 때 쥔 곳: 중앙값 (0.188, −0.044), p10–p90 x 0.149–0.229 · y −0.072–+0.009)
- 트윈 x = 로봇에서 멀어지는 쪽(앞 카메라 위쪽), y+ = 박스 쪽(앞 카메라 왼쪽)입니다.

| # | `--cube` 메모 예 | 놓는 곳 |
|---|---|---|
| 1 | `"기본 0.19,-0.04"` | 학습 사진(ep000) 자리 |
| 2 | `"로봇쪽 3cm"` | 1에서 로봇 쪽으로 3 cm (x ≈ 0.16) |
| 3 | `"멀리 3cm"` | 1에서 멀리 3 cm (x ≈ 0.22) |
| 4 | `"박스쪽 2.5cm"` | 1에서 박스 쪽(왼쪽)으로 2.5 cm (y ≈ −0.015) |
| 5 | `"오른쪽 2.5cm"` | 1에서 오른쪽으로 2.5 cm (y ≈ −0.07) |

- 위치마다 1–2번 돌립니다. 큐브를 돌려 놓는 등 다른 조건은 메모에 적습니다.

**실패했을 때**
- **큐브를 쥔 채 실패**(예: `FAILED_*` 뒤 팔이 큐브를 들고 서 있음)하면 **1분 안에** 집게를 엽니다(T4):
  ```bash
  cd ~/Ros2_e0j0 && bash scripts/dev_ros.sh service call /twin/release std_srvs/srv/Trigger '{}'
  ```
  - 이유: 14:54 시도 뒤 4.2분 쥐고 있다가 드라이버가 `LINK` stale로 관측을 멈췄습니다(집게 과부하 보호로 추정).
- `policy_no_start`(10 s 출발 없음)이면 같은 명령을 다시 냅니다.
- 기동 로그(`up_logs/up_<시각>_real.log`)에 `LINK:`가 보이면 그 세션은 끝냅니다: `dev_down --real` → 12 V 재투입.

**끝낼 때**: 6번 정리 순서 그대로입니다(`dev_down --real` → 12 V 재투입 → 덤프 → `check_restored.py`).

## 9. ③b 완주 시도 (2026-10-08 오후)

세션은 8절과 같습니다(T1 정책 서버, T2 `e0j0_up.sh real` → READY). 큐브를 기본 자리에 놓고 T3에서:
```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --slip-log --cube "기본 0.19,-0.04" table1   # 먼저 탁자 (벽 없음)
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --slip-log --cube "기본 0.19,-0.04" box      # 그다음 박스
```
- 흐름:
  1. 시작 자세 → 정책이 잡고 3 cm 들기 → 넘겨주기(조임)
  2. 들기(위로) → 탁자면 놓을 자리 위, 박스면 벽 위 경로(넘겨준 뒤 계획 ≤ 3 s)
  3. 내려가 놓기 → 집게 열기 → 물러나기 → 접기(fold) → `result DONE`
- 중력 보상이 켜져 있어 명령이 계획보다 조금 위입니다(1–2 cm). 박스는 큐브 중심이 안쪽 범위 안이고 놓을 높이 + 3 cm 아래로 정착하면 엽니다. 탁자는 도달 못 해도 접촉으로 보고 엽니다.
- **바로 멈출 때**(T4 `bash scripts/e0j0_stop.sh`, 위험하면 12 V): 큐브가 박스 벽에 걸릴 것 같을 때, 팔이 탁자·박스를 세게 누를 때.
- 계획이 안 되면(박스 벽 여유 경로 없음) 실행기가 스스로 집은 자리에 되돌려 놓고 열고 `FAILED_HW (ik_infeasible)`로 끝냅니다.
- 큐브를 쥔 채 실패하면 1분 안에 `/twin/release`(8절)를 칩니다.
- 결과는 `runs/index.md` 실물 표에 쌓입니다(단계 칸 `③b 놓침기록`).

## 10. 살포시 놓기로 잡고 놓기 (2026-10-12, 커밋 035ab3a)

**바뀐 점**: 놓을 때 이제 "그 높이로 가서 연다"가 아니라 **"천천히 내려가다 닿으면 그 자리에 서서 연다"**입니다.
- 이유: ③b 실물 3회에서 큐브 바닥이 탁자 위 약 2 cm일 때 열었습니다(기록 추정). 목표가 쥘 때보다 1 cm 위였고, 중력 보상이 명령을 14 mm 더 올렸는데 팔은 처지지 않았기 때문입니다.
- 적용되는 곳: ③b 놓기(탁자·박스), ③a 내려놓기, 계획 실패 때 되돌려 놓기. 끄려면 `e0j0.yaml` `touchdown.enabled: false`.

**놓기 흐름** (넘겨주기 → 들기 → 이송은 9절과 같습니다)
1. `place above`: 예상 바닥(= 쥘 때 TCP 높이, 큐브 바닥이 탁자에 닿는 높이)보다 2 cm 위로 갑니다. 보상 때문에 실제로는 1–1.5 cm 더 위에 섭니다.
2. `touchdown`: 중력 보상 없이 **1.2 cm/s로 수직 하강**합니다(약 3–5 s). 명령은 예상 바닥보다 1.5 cm 아래까지 내려갑니다.
3. **닿으면 섭니다**: 명령은 계속 내려가는데 측정 높이가 0.2 s 동안 1.5 mm 이하로만 내려가고, 측정이 명령보다 5 mm 이상 위에 있으면 접촉으로 봅니다. 그 순간 **측정 자세 그대로** 섭니다(더 누르지 않음).
   - 감지가 안 되면 명령 최저점까지 간 뒤 1 s 더 보고 그 자리에서 엽니다(기록 `bottom`). P16이라 이때 누르는 힘은 1–2 N 정도로 추정합니다.
4. 0.3 s 서 있다가 집게를 **0.8 s에 걸쳐 천천히** 엽니다.
5. **수직으로 3 cm** 든 뒤 물러나고 접습니다(큐브를 옆으로 끌지 않게).

**세션**: 8절과 같습니다. **T2는 새로 띄워야 합니다** — 새 코드는 실행기가 뜰 때 읽습니다. 빌드는 이미 되어 있습니다.
```bash
# T1 정책 서버 (떠 있으면 그대로 둡니다)
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/e0_j0/policy_server.py
# T2 실물 기동 (TTY, 12 V 옆) → 자기 점검 6줄 OK → READY
cd ~/Ros2_e0j0 && bash scripts/e0j0_up.sh real
```

**잡고 놓기** (T3) — 큐브를 기본 자리(0.19, −0.04)에 놓고:
```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --slip-log --cube "기본 0.19,-0.04 살포시" table1   # 먼저 탁자
cd ~/Ros2_e0j0 && bash scripts/e0j0_goal.sh --slip-log --cube "기본 0.19,-0.04 살포시" box      # 그다음 박스
```
- **`--slip-log`를 꼭 붙입니다.** 없으면 넘겨준 직후 놓침 오판(종이 큐브가 조임에 눌림, 오늘 15:46 시도와 같은 것)으로 멈춥니다.
- 기대: `result DONE`. 전체 시간은 예전보다 3–5 s 늘어납니다(하강).
- 끝나면 `runs/index.md` 실물 표의 **살포시** 칸을 봅니다. 예: `접촉 +3mm (지연 6mm, 3.4s)`.
  - `접촉`이면 감지로 섰다는 뜻이고, `bottom`이면 감지 없이 명령 최저점까지 갔다는 뜻입니다.
  - `±Nmm`는 닿은 높이와 예상 바닥의 차이입니다(− = 예상보다 아래). 박스는 바닥 두께만큼 + 쪽이 정상입니다.

**눈으로 볼 것** (보고에 적어 주세요)
- 하강할 때 큐브가 탁자·박스 바닥에 닿기 **전에** 멈췄는지(공중에서 섰는지), 닿고 섰는지, 눌렀는지.
- 열 때 큐브가 떨어졌는지(높이 대략), 튀거나 쓰러졌는지.
- 수직으로 들 때 큐브가 끌리지 않았는지.

**바로 멈출 때** (T4 `bash scripts/e0j0_stop.sh`, 위험하면 12 V)
- 큐브가 닿았는데도 팔이 계속 내려가며 세게 누를 때. 예: 큐브가 찌그러지거나 팔·집게가 휘는 소리.
- 박스 벽에 큐브가 걸릴 때.
- 큐브를 쥔 채 실패하면 1분 안에 `/twin/release`(8절).

**끝낼 때**: 6절 정리 순서 그대로입니다(`dev_down --real` → 12 V 재투입 → 덤프 → `check_restored.py`).

## 7. 보고에 담을 것

- T3 `result …` 줄(시도마다).
- T1 마지막 `RTC 추론 지연` 줄.
- `check_restored.py` 결과.
- 눈으로 본 것: 출발 시각, 쥐는 모습, 버티는 동안 큐브·집게 상태, 내려놓기.
- 나머지(처짐·집게·Present_Load·정책 통계)는 기록 파일에서 제가 정리합니다.
