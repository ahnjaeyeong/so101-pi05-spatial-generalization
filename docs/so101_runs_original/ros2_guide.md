# Thor ROS2 트윈(~/Ros2) 사용 설명서

- 작성: 2026-10-07. 문서와 스크립트를 읽고, 조회 명령(`git log`, `docker images/ps`, `dev_cams.sh`, `ls /dev/...`)만 돌려서 정리했다. **이 문서의 명령은 아직 하나도 실행해 보지 않았다.**
- 근거: `~/Ros2`(브랜치 arm-jetson), `CLAUDE.md`, `docs/RUNBOOK.md`, `docs/STATUS.md`, `docs/data_collection_thor.md`, `docs/requests_to_main.md`, `ros2_ws/src/twin_bringup/config/sites/thor/`, `scripts/dev_*.sh`, `scripts/lib/`, 드라이버 소스, Thor 커밋 메시지(2026-10-01), 원격 main(eb90313)의 `dev_up.sh`와 RUNBOOK §13.
- RUNBOOK은 WSL(Windows) 시절에 쓴 문서라 `usbipd attach`, `/mnt/d/ROS2` 같은 내용이 남아 있다. **Thor에서는 해당 없다.** Thor는 USB가 바로 붙어 있고 리포는 `~/Ros2`에 있다.
- 명령은 전부 `cd ~/Ros2`에서 **Thor 데스크톱의 실제 터미널**에 사람이 직접 입력한다. `--real`, `dev_jog`, `dev_home`은 TTY가 없으면 거부된다(§5-3). Claude Code의 `!`나 에이전트가 대신 실행하면 안 된다.

---

## 1. 무엇이 준비돼 있나

### 1-1. 현재 상태 (2026-10-07 조회)

| 항목 | 값 |
|---|---|
| 브랜치 | `arm-jetson` @ `43d25ef` (2026-10-01 17:31, "data_collection_thor.md …"). 작업 트리 깨끗함, origin과 같음 |
| 원격 main | `eb90313` (2026-10-02, "첫 CV 세션 준비 …"). **arm-jetson은 아직 이 main 위로 rebase되지 않았다.** main에만 `--real --cv`, `--real-cv`, 53 mm 큐브, 집게 토크 가드, cv2 카메라 노드가 있다 |
| Docker 이미지 | `twin_ws:lyrical`(2026-10-01 13:46 빌드, 7.42 GB), 베이스 `ros:lyrical-ros-base` |
| 컨테이너 | **없음** (`docker ps -a` 비어 있음) |
| 볼륨 | `twin_ws_build`, `twin_ws_install`, `twin_ws_log` (colcon 산출물, 2026-10-01 생성). **dev_up은 빌드하지 않고 install 볼륨을 그대로 쓴다** (§5-1) |
| docker 런타임 | `nvidia` 있음 → `TWIN_GPU=1`로 RViz에 GPU를 쓸 수 있다 |
| 화면 | `DISPLAY=:1` (데스크톱 터미널). `dev_container.sh`가 기동마다 `xhost +SI:localuser:root`를 해 준다 |
| 호스트 python | `/usr/bin/python3` 3.12.3 + PyYAML 6.0.1 (dev_up의 7/7 검사에 필요, 충족) |
| 서보 버스 | 팔로워 `5B8E116810` → **/dev/ttyACM0**, 리더 `5B79015701` → /dev/ttyACM1 (by-id 기준, 재연결하면 번호가 바뀔 수 있다) |
| 카메라 | 머리(front) USB 2.4 → /dev/video0, 손목(wrist) USB 2.3.2 → /dev/video2 (`dev_cams.sh`: `OK: 카메라 2대`). 지금 두 대 모두 수동 156/4600 |
| Thor 팔 설정 | `ros2_ws/src/twin_bringup/config/sites/thor/` — `calibration_so101_jetson.json`(lerobot `my_arm.json`과 sha256 같음), `.limits.yaml`(q_tol 0.04, 자기 점검 0.03 m, 토크 on 허용 띠 8 tick), `measured.yaml`(집게 표, pan 하드스톱 — 기록용, 아직 코드가 읽지 않음) |
| Unity | `~/Unity/Ros2Twin` 프로젝트와 `/usr/bin/unityhub`는 있지만 설치된 에디터는 찾지 못했다. 프로젝트 문서는 Windows(D:\) 기준이다 |

**Thor 실측 기록(커밋 메시지):**
- `--real-ro`: 헬스체크 6/6, joint_states 29.995 Hz.
- `--real-ro --viz`: RViz에 실물 팔이 보였다.
- `--real`: 자기 점검 READY → `dev_goal 0.20 0.10 --tol 0.028 --deadline 60`이 **DONE (50.8 s)** → `/twin/home` → `dev_down --real`(fold, 토크 off 6/6, 크래시 0).
- 카메라: `--cameras` 두 대 각 30 fps.
- sim에서 `dev_up`을 돌린 기록은 커밋에 없다. colcon 테스트(678건)만 있다.

### 1-2. 실행 모드 (arm-jetson에서 쓸 수 있는 것)

| 모드 | 명령 | 뜨는 것 | 실물 팔 | 사람 동석 |
|---|---|---|---|---|
| **sim** | `bash scripts/dev_up.sh [--viz]` | sim_arm_node(가상 팔), kinematic_world(가상 큐브), ground_truth_publisher, goal_executor_node, rosbridge :9090, rosapi | 안 씀 (장치 전달 0) | 불필요 |
| **--real-ro** (arm_only) | `… dev_up.sh --real-ro --device /dev/ttyACM0 [--viz] [--cameras]` | soarm_driver_node(읽기 전용) + rosbridge. executor·세계·`/twin/objects` 없음 | **안 움직임.** 토크 off이고 `/robot/joint_cmd` 구독도 없다. 손으로 움직이면 트윈이 따라온다 | 권장(토크 off라 팔이 처지므로 받치거나 접어 둔다) |
| **--real** (real_kinematic) | `… dev_up.sh --real --device /dev/ttyACM0 [--viz] [--cameras]` | 드라이버(쓰기) + kinematic_world + ground_truth_publisher + executor + rosbridge | **움직인다.** 기동 한 줄이 게인 쓰기 → 토크 on → 자기 점검(관절 6개 ±0.1 rad 왕복) → READY까지 한다. 이후 `dev_goal`로 pick-place | **필수.** TTY에서 입력한 것 자체가 "12 V 스위치 옆에 있다"는 선언이다 |
| --real-kinematic --with-human | 같은 프로파일인데 토크·자기 점검을 자동으로 하지 않는다 | 위와 같음 | 토크를 켜면 움직인다(켜는 것은 사람 도구 몫) | 필수. 보통은 `--real`을 쓴다 |
| --arm-jog --with-human | `… dev_up.sh --arm-jog --with-human --device /dev/ttyACM0` | 드라이버(쓰기)만. executor 없음 | `dev_jog.sh --with-human torque on`, `dev_jog.sh --with-human shoulder_pan 0.05`, `--pose home/fold`로 **한 관절씩 조금씩** 움직인다(매번 Enter 확인) | 필수. **박사님과 함께** |
| `--viz` (덧붙임) | 모든 모드에 붙일 수 있다 | robot_state_publisher, tf, `/twin/viz` 마커, **rviz2 창** | — | — |
| `--cameras` (덧붙임) | 실물 모드에서만 | `/wrist_camera/image_raw`, `/head_camera/image_raw` (640x480@30, rgb8). arm-jetson에서는 **발행만 하고 아무 노드도 쓰지 않는다** | — | — |
| ~~--real --cv~~, ~~--real-cv~~ | **arm-jetson에 없다** (main eb90313에만 있음) | 머리 카메라로 큐브를 검출해서 집는다 | 움직인다 | §5 참고 — rebase와 Thor 카메라 캘리브레이션이 먼저다 |

공통으로 알아 둘 것:
- **실물 모드는 Thor 팔 캘리브레이션을 반드시 지정한다.** `TWIN_SERVO_CALIBRATION=src/twin_bringup/config/sites/thor/calibration_so101_jetson.json`. 빼먹으면 1호 팔(Windows) 캘리브레이션으로 뜨고, 서보 EEPROM과 맞지 않아 드라이버가 rc 7로 거부한다(안전하지만 기동 실패).
- **`--device`도 반드시 준다.** 주지 않으면 dev_up이 `/dev/serial/by-id`의 **첫 링크**를 고르는데, 알파벳 순서상 리더(5B79…)가 먼저다. 리더가 꽂혀 있으면 리더 버스(ttyACM1)를 잡는다(캘리브레이션 불일치로 거부된다). `--device`는 `/dev/ttyACM<번호>` 형식만 받고 by-id 경로는 거부한다. 그래서 아래처럼 번호를 구해서 넘긴다.
  ```bash
  export TWIN_SERVO_CALIBRATION=src/twin_bringup/config/sites/thor/calibration_so101_jetson.json
  FOLLOWER=$(readlink -f /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B8E116810-if00); echo $FOLLOWER   # /dev/ttyACM0 이어야 한다
  ```
- 같은 시각에 컨테이너는 하나만 쓴다. 실물 컨테이너가 떠 있으면 dev_up이 `REFUSED: existing real stack`으로 거부한다.

### 1-3. Unity가 필요한가 → 필요 없다

- 목표는 **`scripts/dev_goal.sh`**가 ExecuteGoal 액션(`/twin/goal`)으로 보낸다. 예: `dev_goal.sh 0.20 0.10` = 큐브 `red_cube_01`을 (x 0.20, y 0.10) m로 옮겨라.
- 진행 보기는 `dev_status.sh`(-f, --goal), 완료 대기는 `dev_wait.sh`, 화면은 `--viz`(RViz)로 한다.
- rosbridge `ws://localhost:9090`은 Unity(P2)가 붙는 자리다. 지금은 쓰지 않아도 된다. 2026-09-28 첫 실물 pick-place는 Windows의 Unity에서 goal을 보냈지만, Thor 시험(2026-10-01)은 `dev_goal`로 했다.
- 좌표: world = 로봇 base_link (`calibration.yaml`이 항등 변환). +x는 published shoulder_pan = 0인 방향(로봇 정면)이고, +y는 로봇 기준 왼쪽, z = 0은 탁자다. 큐브 z는 registry가 정한다(35 mm 큐브 → 0.0175).

---

## 2. 모드별 사용법

### 2-0. 공통: 시작 전 확인

```bash
cd ~/Ros2
docker ps --format '{{.Names}}'                 # 비어 있어야 한다 (twin_ws_dev 가 있으면 먼저 dev_down)
pgrep -af 'lerobot|record_ui|rollout' || echo "lerobot 없음"   # lerobot 이 버스·카메라를 쓰고 있으면 안 된다
git -C ~/Ros2 status --short                    # 비어 있어야 한다 (누가 편집 중인지)
```
실물 모드라면 추가로 확인한다.
```bash
ls -l /dev/serial/by-id/                        # 5B8E116810(팔로워) → ttyACM? 확인
ls -l /dev/v4l/by-path/ | grep index0           # 2.4(머리) · 2.3.2(손목)  — --cameras 쓸 때만
bash scripts/dev_cams.sh --check                # 카메라 역할 계약 (읽기만 한다)
bash scripts/dev_bus.sh ping --device $FOLLOWER # 서보 6/6 응답 (쓰기 0회, 일회용 컨테이너)
```
- `dev_bus.sh ping`은 이렇게 나와야 정상이다: `link: ids=[1, 2, 3, 4, 5, 6] err=0 (broadcast ping x3)`. 여섯이 안 나오면 12 V 전원과 케이블을 확인한다.
- **12 V 전원**: 실물 모드는 켜져 있어야 하고 스위치는 손 닿는 곳에 둔다. 비상정지는 이 스위치 하나다.
- **팔 자세**: 접힌 자세(탁자에 기댄 자세)에서 시작한다. 토크 on 직전에 관절이 캘리브레이션 범위 ±8 tick 밖이면 거부된다.
- **같이 돌면 안 되는 것**: lerobot(teleoperate/record/rollout, record_ui.py, servo_dump.py), 다른 twin 컨테이너, 카메라를 여는 프로그램(`--cameras`를 쓸 때). 버스와 카메라는 한 번에 한 프로그램만 쓴다.

### 2-A. sim (하드웨어 없음)

```bash
bash scripts/dev_up.sh --viz            # 또는 TWIN_GPU=1 bash scripts/dev_up.sh --viz  (RViz CPU 부담을 GPU 로)
```
- **정상 기동**: 헬스체크 7단계 뒤 마지막 줄이 `E2 ready ws://localhost:9090  (+viz)`이고 RViz 창이 뜬다.
  - `1/7 /twin/goal action server: up` → `2/7 rosbridge` → `3/7 rosapi topics` → `4/7 writer 유일성` → `5/7 /robot/joint_states: ~30 Hz` → `6/7 /twin/objects` → `7/7 초기 상태`.
  - 실패하면 `FAIL at stage N/7: …`(exit 1)이 나온다.
- **상태 한 화면**: `bash scripts/dev_status.sh` (~10 s). 확인할 것은 `writer <topic> 1` ×5, `param failure_rate=0.0`, rviz2 세 단계(노드/창/화면)다.
- **시험 목표**:
  ```bash
  bash scripts/dev_goal.sh 0.20 0.10          # accepted → (~6 s 계획) → APPROACH … RETREAT → result DONE (~15 s)
  bash scripts/dev_goal.sh 0.20 -0.10         # 되돌리기
  bash scripts/dev_fault.sh GRIP_JAM 0        # 결함 주입 → 다음 goal 은 result FAILED_GRASP (cease_grasp), exit 3
  bash scripts/dev_goal.sh 0.20 0.10
  bash scripts/dev_fault.sh none 0            # 해제
  bash scripts/dev_reset.sh                   # 큐브·팔 초기화 (sim 전용, 진행 중 goal 이 있으면 거부)
  bash scripts/dev_ros.sh topic echo /twin/objects --once
  ```
  - 결과는 `dev_goal` 출력의 `result …` 줄이다. 백그라운드로 보내려면 `-d`를 붙이고 `dev_status.sh -f` 또는 `dev_wait.sh`로 확인한다.
- **멈추기**: ^C는 **클라이언트만** 끝낸다. goal은 취소되지 않고 끝까지 간다(취소 미지원). 끝나기를 기다린다(`dev_wait.sh`).
- **끄기**: `bash scripts/dev_down.sh` → `OK: processes=0 zombies=0 container=removed`.
  - RViz 창을 먼저 닫지 않는다. rviz2만 단독 종료하면 segfault하는 상류 결함이 있다. 이 경우 dev_down에 `WARN: 관측자 크래시`가 찍히는데, 동작에는 영향이 없다.

### 2-B. --real-ro (읽기 전용, 팔이 안 움직임)

```bash
export TWIN_SERVO_CALIBRATION=src/twin_bringup/config/sites/thor/calibration_so101_jetson.json
FOLLOWER=$(readlink -f /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B8E116810-if00)
bash scripts/dev_up.sh --real-ro --viz --device $FOLLOWER            # 카메라도 볼 거면 --cameras 추가
```
- **정상 기동**: `== 실물 사전 점검 ==`(안전 문구, 장치, `리더: 없음`) → 헬스체크 **6단계** → `E2 ready … [real  /dev/ttyACM0, torque off]`.
  - `1/6 실물 링크·토크: torque disabled: 6/6 (verified) · link: ids=[1, 2, 3, 4, 5, 6] err=0`
  - `5/6 /robot/joint_states: ~30 Hz`
  - `6/6 읽기 전용 계약: read-only contract: joint_cmd subscriptions=0 read_only=True joints=6`
- **확인**:
  ```bash
  bash scripts/dev_ros.sh topic echo /robot/joint_states      # Ctrl-C 로 끝낸다. --qos 옵션은 주지 않는다
  bash scripts/dev_ros.sh topic hz /robot/joint_states
  bash scripts/dev_status.sh                                  # 컨테이너 줄 끝 "장치 /dev/ttyACM0" = 지금 버스를 쥔 쪽
  ```
  - 관절을 손으로 하나씩 움직이면 RViz 팔이 같은 방향으로 따라온다(RUNBOOK §12 표).
  - **pan = 0 방향 찾기**: shoulder_pan을 손으로 돌려 position[0]이 0에 가까워지는 방향이 트윈의 +x(정면)다. 실물 시험 때 큐브를 놓을 기준이다.
  - 카메라를 켰다면 `bash scripts/dev_ros.sh topic hz /head_camera/image_raw`를 본다(~30). 화면으로 보려면 RViz에 Image 디스플레이를 추가하거나 rqt_image_view를 쓴다. 이미지에 들어 있는지는 확인하지 않았다(§5).
- **정상인데 결함처럼 보이는 것**:
  - `/twin/objects` 없음, 마커 빈칸
  - `dev_goal`·`dev_reset`·`dev_fault` 거부
  - wrist_roll ±180°, wrist_flex가 URDF를 약 4° 넘음
  - 이유는 RUNBOOK §11e·§11f에 있다.
- **멈추기·끄기**: `bash scripts/dev_down.sh`. 토크가 꺼진 채라 팔은 그대로 자유 상태다.
- **이상 상황**:
  - `TORQUE_ON … exit 6`: 다른 프로그램(lerobot)이 토크를 켜 둔 상태다. lerobot을 끄고, 팔을 받치고 `dev_down` → 12 V를 껐다 켠다 → `dev_bus.sh ping`.
  - `REASON:PORT_BUSY`: lerobot 등이 포트를 쓰고 있다.
  - rc 7: 캘리브레이션을 빼먹었거나 리더 포트를 골랐다.

### 2-C. --real (실물 구동)

**처음에는 박사님과 함께 한다.** 12 V 스위치 옆에 서서 입력한다.
```bash
export TWIN_SERVO_CALIBRATION=src/twin_bringup/config/sites/thor/calibration_so101_jetson.json
FOLLOWER=$(readlink -f /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B8E116810-if00)
bash scripts/dev_up.sh --real --viz --device $FOLLOWER
```
- **기동 순서(자동)**:
  1. 사전 점검과 헬스체크 6단계. 6/6은 `write contract: real_kinematic pub=1 sub=1; torque remains off`.
  2. `== 토크 on (선결 순서: Present 재독 → 창 확인 → 게인 → Goal:=Present → Enable) ==`
  3. `== 자기 점검 (관절 6개 ±0.1 rad 왕복 — 팔이 움직인다) ==`
  4. `E2 ready … [real real_kinematic /dev/ttyACM0, torque on — READY]`
- **움직이는 동안 팔은 느리다**(관절 최대 0.16 rad/s ≈ 9°/s). 한 번의 pick-place가 50 s쯤 걸린다.
- **실패하는 경우**:
  - 토크 on 실패: `FAIL at 토크 on — 팔을 창 안으로 옮긴 뒤 다시 친다`. 토크는 꺼진 상태다.
  - 자기 점검 보류: `보류: 자기 점검이 벽을 넘은 관절을 보고했다 — READY 를 내지 않는다`. **토크가 켜진 채로 팔이 서 있다.** 판단한 뒤 `bash scripts/dev_home.sh --with-human`(접기)이나 `bash scripts/dev_down.sh --real`(끝내기)을 고른다.
- **시험 목표 (real_kinematic = 추측 항법)**:
  - 트윈은 카메라로 큐브를 보지 않는다. registry의 초기 위치 **(0.20, −0.10)**에 큐브가 있다고 **가정**하고 움직인다.
  - 그래서 사람이 실물 큐브(registry는 **35 mm**)를 그 자리에 놓는다. 위치는 로봇 정면 20 cm, 오른쪽 10 cm, 탁자 위다.
  ```bash
  bash scripts/dev_goal.sh 0.20 0.10 --tol 0.028 --deadline 60     # Thor 실측값: 기본 tol 0.02·deadline 30 으로는 실패할 수 있다
  bash scripts/dev_goal.sh 0.20 -0.10 --tol 0.028 --deadline 60    # 되돌리기 (dev_reset 은 실물에서 쓰지 않는다)
  ```
  - 결과: `result DONE (… final (0.200, 0.099, 0.018) …)`가 나오고, 실물 큐브가 옮겨졌는지 **눈으로** 본다.
  - `final` 값은 트윈이 계산한 값이다. 실물 위치를 잰 것이 아니다.
- **goal이 끝난 뒤 팔 접기**: `bash scripts/dev_home.sh --with-human` (Enter 확인 → `/twin/home`). `--release`를 붙이면 집게만 연다.
- **진단(토크 on 상태에서 읽기만)**: `bash scripts/dev_diag.sh` → 부하·전압·온도.
- **멈추기**:
  - ^C로는 팔이 서지 않는다. goal은 끝까지 간다.
  - 위험하면 **12 V 스위치**를 끈다. 토크가 풀려 팔이 떨어지므로 손을 가까이 둔다.
  - 12 V를 끈 뒤에는 드라이버가 발행을 멈춘다. 이때는 `bash scripts/dev_down.sh`(토크 off 단계가 실패해도 이미 꺼진 상태다) → 12 V를 다시 켠다 → `dev_bus.sh ping`으로 6/6을 확인한 뒤 다시 기동한다.
- **안전하게 끄기**:
  ```bash
  bash scripts/dev_down.sh --real      # ① fold(느리게, 팔이 움직인다) ② 토크 off 6/6 ③ 그래프·컨테이너 정리
  ```
  - 토크 off 순간 팔을 받친다.
  - `FAIL: 토크 off 가 6/6 을 보고하지 않았다`가 나오면 12 V로 끈다.
  - **실물 구동 모드를 `--real` 없이 `dev_down`으로 내리면 토크를 끄지 않는다.** 서보가 마지막 목표에서 힘을 준 채로 남는다. 반드시 `--real`을 붙인다.

### 2-D. --arm-jog (관절을 손으로 조금씩, 고급)

```bash
bash scripts/dev_up.sh --arm-jog --with-human --device $FOLLOWER      # TWIN_SERVO_CALIBRATION export 된 상태
bash scripts/dev_jog.sh --with-human torque on                        # Enter 확인 뒤 토크 on (현재 자세 유지)
bash scripts/dev_jog.sh --with-human observe 5                        # 5 s 동안 저절로 움직이는지(0.01 rad 이상이면 STOP)
bash scripts/dev_jog.sh --with-human shoulder_pan 0.05                # 한 관절 +0.05 rad (매번 Enter)
bash scripts/dev_jog.sh --with-human --pose fold                      # 접기
bash scripts/dev_jog.sh --with-human torque off                       # 팔 받치고
bash scripts/dev_down.sh
```
- `--pose`는 다른 `/robot/joint_cmd` 발행자가 있으면 거부된다.
- fold 목표는 1호 팔 캘리브레이션으로 rad 환산한 값이다(requests_to_main 1번, 임시 처리).
- **박사님과 함께**만 한다.

### 2-E. 화면으로 보기

- **RViz**: `--viz`. 데스크톱 터미널에서 띄워야 창이 보인다(ssh에는 DISPLAY가 없다). `TWIN_GPU=1`을 붙이면 소프트웨어 렌더링(CPU ~218%)을 GPU로 돌린다.
- 창이 안 보이면 `dev_status.sh`의 rviz2 세 단계(노드/창/화면)에서 어느 층이 문제인지 본다.
- **토픽**: `bash scripts/dev_ros.sh topic list`, `… topic echo …`, `… topic hz …`. 사람은 `docker exec`로 컨테이너에 들어가지 않는다.
- **로그**: launch 로그는 컨테이너 안 `/tmp/dev_demo.log`에 있고 컨테이너를 내리면 사라진다. `-d` goal 로그는 `/ws/log/goals/dev/`(볼륨이라 남는다).

---

## 3. 추천 순서

| 단계 | 할 것 | 통과 기준 |
|---|---|---|
| 0. sim (혼자 가능) | §2-A 전체: `dev_up --viz` → `dev_status` → `dev_goal 0.20 0.10` → GRIP_JAM → `dev_fault none` → `dev_reset` → `dev_down` | `E2 ready` 7/7, RViz에서 팔과 큐브가 움직임, `result DONE`(~15 s), GRIP_JAM 뒤 `FAILED_GRASP`, dev_down `OK: … container=removed` |
| 1. 읽기 전용 (혼자 가능, 팔은 접어 두거나 받침) | 12 V on, lerobot 꺼짐 확인, `dev_bus.sh ping` 6/6 → `--real-ro --viz [--cameras]` → 관절을 손으로 하나씩 움직임 → pan = 0 방향 확인 → (카메라) hz 30 → `dev_down` | 1/6 `torque disabled: 6/6`, 6/6 읽기 전용 계약, joint_states 25–35 Hz, RViz가 손 움직임을 같은 방향으로 따라옴, 카메라 두 대 ~30 Hz, dev_down 뒤 `docker ps` 비어 있음 |
| 2. 실물 구동 (**처음은 박사님과**) | 큐브(35 mm)를 (0.20, −0.10)에 놓고 작업 공간을 비움 → `--real --viz` → READY → `dev_goal 0.20 0.10 --tol 0.028 --deadline 60` → 역방향 → `dev_home` → `dev_down --real` → **12 V 재투입**(§4) | 토크 on·자기 점검 READY, DONE 두 번, 실물 큐브가 실제로 옮겨짐(눈으로 확인), 끌거나 부딪힘 없음, `dev_down --real`의 fold·토크 off 6/6·`crashes=0` |
| 3. 나중 | `--arm-jog`, `--real --cv` | §5에서 박사님 확인 뒤 |

---

## 4. lerobot과 번갈아 쓸 때

### 4-1. 트윈이 서보에 쓰는 값

토크를 켤 때(`--real`, `dev_jog torque on`) 드라이버가 쓰는 값과, 그 뒤 lerobot 연결 시 어떻게 되는지다.

| 레지스터 | 트윈이 쓰는 값 | 저장 위치 | lerobot이 연결할 때 | 결과 |
|---|---|---|---|---|
| P/D/I 게인 (21/22/23) | **P 32**, D 32, I 0 (다를 때만 씀) | **EEPROM**(전원을 껐다 켜도 남음) | P 16, I 0, D 32를 매번 다시 씀 | lerobot 연결 시 자동 복구 |
| Acceleration (41) | 13 (집게 16) ≈ 2 rad/s² | SRAM | 254를 씀 | 자동 복구 |
| **Goal_Velocity (46)** | **104 (집게 132) ≈ 0.16 rad/s** | SRAM | **쓰지 않음** | **12 V 재투입 전까지 남는다.** 그대로 lerobot을 쓰면 팔로워가 약 9°/s로 제한돼 리더를 늦게 따라간다(2026-10-02 실제 발생) |
| Torque_Enable (40) | `dev_down --real`이 0 | SRAM | lerobot이 연결 시 켬 | — |
| 집게 Max_Torque_Limit 등 | arm-jetson 트윈은 쓰지 않음 (main은 파지 중 Torque_Limit을 낮췄다 복원) | — | 500/250/25를 씀 | — |

- `data_collection_thor.md` §5의 "각자 연결 시 자기 서보 설정 적용"은 **Goal_Velocity에는 해당하지 않는다.** lerobot이 이 값을 되돌리지 않는다.
- **카메라**: 트윈(`uvc_camera_node`)은 해상도·MJPG·fps만 맞추고 **노출과 화이트밸런스는 건드리지 않는다.** 그 값은 v4l2에 남아 있던 값 그대로이고, USB를 다시 꽂거나 재부팅하면 기본값으로 돌아간다.
- `--cameras`로 띄운 동안 lerobot은 카메라를 열 수 없다.

### 4-2. 트윈 → lerobot으로 돌아올 때

```bash
bash scripts/dev_down.sh --real          # 실물 구동 모드였다면 반드시 --real (fold → 토크 off). 읽기 전용이었다면 그냥 dev_down
docker ps --format '{{.Names}}'          # 비어 있어야 한다 (record_ui.py 도 이것을 점검한다)
# 12 V 전원을 껐다가 켠다 (Goal_Velocity·Acceleration SRAM 초기화) — 팔을 받친다
ls -l /dev/serial/by-id/                 # 팔로워·리더 번호 다시 확인
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/scripts/servo_dump.py --arm follower
#   → 여섯 서보 Goal_Velocity(46) = 0 인지 본다. (읽기 전용 덤프. 결과 JSON 이 ~/so101_boxpick/docs/servo_dumps/ 에 생긴다)
```
- **카메라**: 다음 lerobot 작업 조건에 맞춘다.
  - 수집·테스트 기본(`~/so101_runs/camera_settings.md` 결정)은 자동이다.
    ```bash
    for d in /dev/cam_front /dev/cam_wrist; do
      v4l2-ctl -d $d -c auto_exposure=3 -c white_balance_automatic=1 -c exposure_dynamic_framerate=0
      v4l2-ctl -d $d -C auto_exposure,white_balance_automatic,exposure_dynamic_framerate
    done
    ```
  - practice_10 정책을 평가할 때는 학습 조건인 수동 156/4600을 쓴다. 모드를 먼저 수동으로 바꾼 다음 값을 넣는다.
- **P 게인**: lerobot이 연결하면서 16으로 되돌린다. 따로 할 일은 없다. 확인하려면 위 덤프의 P_Coefficient를 본다.

### 4-3. lerobot → 트윈으로 갈 때

- lerobot 세션(teleoperate/record/rollout)을 **정상 종료**한다. 연결을 끊을 때 토크를 끈다. 비정상 종료로 토크가 남아 있으면 트윈 드라이버가 rc 6으로 거부한다 → 팔을 받치고 12 V를 재투입한다.
- 팔을 접힌 자세로 둔다(토크 on 범위 확인 때문이다).
- 카메라를 쓰는 프로그램을 끈다(`--cameras`를 쓸 때).
- lerobot이 P=16으로 바꿔 놨어도 트윈이 토크를 켤 때 다시 32로 쓴다. 신경 쓸 필요 없다.

---

## 5. 박사님께 확인할 것

### 5-1. 문서만으로는 불확실한 것

1. **브랜치**: arm-jetson(10-01)과 main(10-02, `--real --cv`, 53 mm 큐브, 집게 가드, cv2 카메라 노드)이 갈라져 있다. requests_to_main의 규칙상 main이 갱신됐으니 rebase할 차례로 보인다. 언제 하는지, 그 전까지 arm-jetson으로 써도 되는지 확인한다.
2. **빌드 상태**: dev_up은 colcon 빌드를 하지 않고 `twin_ws_install` 볼륨(10-01 11:01 생성)을 쓴다. 이 볼륨이 지금 HEAD(43d25ef)로 빌드된 것인지, 소스가 바뀌면 사람이 칠 빌드 명령이 무엇인지 확인한다. RUNBOOK은 "colcon은 에이전트 몫"이라고만 적어 두었다.
3. **큐브**: arm-jetson registry는 35 mm, main은 "운영 큐브 = 실물 53 mm"다. 지금 책상에 어떤 큐브를 쓰는지, Thor 시험 때 tol 0.028을 쓴 것이 기준인지 확인한다.
4. **pan 영점**: 코드는 1호 팔 값(+0.1381 rad)을 쓴다. Thor 팔의 실측 중앙(`measured.yaml` zero_offset −0.2194, "확정")은 아직 코드에 반영되지 않았다(requests_to_main 7번). 그래서 트윈의 +x(정면)가 Thor 팔의 하드스톱 중앙과 약 20° 다를 수 있다. 큐브를 놓을 기준 방향을 확인한다.
5. **카메라 노출**: 트윈은 건드리지 않는다. 문서는 세 가지가 있다. data_collection_thor.md는 수동 250, camera_settings.md는 자동, practice_10은 156/4600이다. `--cv`를 쓸 때 어느 값을 쓸지 확인한다.
6. **`--real --cv`를 Thor에서 쓰려면**: rebase 뒤에도 main의 머리 카메라 외부 파라미터(`calibration.yaml`, 2026-09-30)는 1호 환경에서 잰 값이다. Thor 카메라는 intrinsics도 없다(`measured.yaml` camera_intrinsics: null). Thor에서 캘리브레이션을 다시 하는 절차를 확인한다.
7. **Goal_Velocity 잔류**: `dev_down --real`이 46번을 되돌리지 않아서 lerobot 전에 12 V 재투입이 필요하다. 이 절차를 문서(data_collection_thor.md §5)에 넣을지, 드라이버가 끌 때 되돌리게 할지 확인한다.
8. **기본 장치 선택**: `--device`를 생략하면 리더 포트를 고른다(§1-2). 리더를 뽑아 두는 것이 원칙인지, 기본값을 팔로워 by-id로 바꿀지 확인한다.
9. **udev 이름**: data_collection_thor.md는 `/dev/so101_follower`와 `/dev/so101_leader`가 "서로 바뀌어 있다"고 적었다. 지금 규칙은 팔로워 → 5B8E116810으로 맞게 고쳐져 있다. 문서를 갱신할지 확인한다.
10. **RViz 카메라 보기**: 이미지에 rqt_image_view나 image_view가 들어 있는지 확인하지 않았다. `dev_cams.sh`는 `ros2 run image_view image_view`를 안내한다.
11. **P=32 EEPROM 쓰기**: lerobot과 번갈아 쓰면 토크를 켤 때마다 EEPROM에 16 ↔ 32를 다시 쓴다. 쓰기 수명 면에서 괜찮은지 확인한다.

### 5-2. 박사님이 같이 있어야 하는 단계

- 이 기계에서 사용자가 처음 하는 `--real` 세션(자기 점검, 첫 pick-place, `dev_down --real`).
- `--arm-jog` / `dev_jog.sh`, `dev_home.sh`를 처음 쓸 때.
- `--real --cv`(rebase, 카메라 캘리브레이션 포함).
- 이미지 재빌드, colcon 빌드, rebase, 캘리브레이션 파일 교체 등 리포·환경을 바꾸는 일.
- `judge_*.sh --with-human` 같은 판정.

### 5-3. 스크립트가 실행을 거부하는 조건

| 조건 | 결과 |
|---|---|
| `--real`을 TTY가 아닌 곳에서 실행(stdin과 stdout이 모두 터미널이어야 함) | `REFUSED: --real 은 대화형 TTY 에서만` (rc 2) |
| `--arm-jog`/`--real-kinematic`에 `--with-human`이 없음 | `REFUSED: write profile requires --with-human` |
| `dev_jog.sh`/`dev_home.sh`: `--with-human`이 없거나 TTY가 아니거나 **120 s 안에 빈 Enter**가 오지 않음 | `REFUSED …` (rc 2) |
| 실물 컨테이너가 이미 떠 있음 | `REFUSED: existing real stack; human fold/off and dev_down first` |
| 진행 중 goal이 있을 때 `dev_up`/`dev_reset`/`dev_goal -d` | `REFUSED: 진행 중 goal …` (`dev_wait` 뒤 다시, dev_up은 `--force`) |
| 장치 없음 / 다른 프로그램이 포트 사용 / 여섯 서보 중 일부 무응답 | rc 4 + `REASON:NO_DEVICE` / `PORT_BUSY` / `LINK_INCOMPLETE` |
| `--device`가 `/dev/ttyACM*`·`/dev/ttyUSB*`가 아님(by-id 경로, /dev/video 등) | `REFUSED: 서보 버스가 될 수 없는 경로다` |
| 기동 시 토크가 이미 켜져 있음(lerobot이 남김) | 드라이버 rc 6 (12 V 재투입) |
| 캘리브레이션 JSON과 서보 EEPROM 불일치(TWIN_SERVO_CALIBRATION 누락, 리더 포트 선택) | 드라이버 rc 7 → `FAIL at stage 1/6` |
| 토크 on 때 관절이 범위 ±8 tick 밖 | `FAIL at 토크 on — 팔을 창 안으로` |
| 자기 점검에서 벽을 넘음 | `보류 …` exit 1 (토크는 켜진 채) |
| 실물 + `--diag`, sim + `--device`, 실물 + `--registry`, sim + `TWIN_SERVO_CALIBRATION`, sim + `--camera` | rc 2 / FAIL |
| `--cameras`인데 카메라 역할 계약 불일치 | `dev_cams.sh --check` 실패로 rc 2 |
| 실물 모드에서 `dev_reset`·`dev_fault GRIP_JAM` | `REFUSED: sim 전용` / `FAIL: /sim_arm_node 가 없다` |
| `TWIN_GPU=1`인데 nvidia 런타임 없음 | REFUSED (Thor에는 있음) |
| 호스트 python3에 PyYAML 없음 | 컨테이너를 올리기 전에 FAIL (Thor에는 있음) |
