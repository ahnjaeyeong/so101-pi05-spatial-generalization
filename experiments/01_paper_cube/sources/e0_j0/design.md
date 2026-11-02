# E0_J_0 — π0.5 잡기 + E0-lite IK 놓기 시제품 설계 (1단계)

- 작성: 2026-10-07. 읽기와 오프라인 분석만 했다. ~/Ros2, 컨테이너, 팔, 카메라는 건드리지 않았고 설치한 것도 없다.
- 이름: 문서와 사람이 부를 때는 **E0_J_0**. ROS 패키지·노드·실행 파일 이름은 소문자 규칙에 따라 **`e0_j0`**(패키지 `twin_e0j0`, 노드 `e0_j0_executor`).
- 근거:
  - `~/Ros2` arm-jetson `43d25ef`: `twin_executor/goal_executor_node.py`, `branch.py`, `twin_backend/soarm_driver_node.py`, `servo_map.py`, `twin_world/kinematic_world_node.py`, `twin_bringup/launch/demo.launch.py`, `config/constants.yaml`, `sites/thor/*`, `docs/design_notes_scene_execution_review_D1_D7.md`
  - lerobot 0.6.2 (`~/so101-env`)
  - practice_50 데이터셋(50 에피소드, 30 fps)과 학습·평가 스크립트
- 오프라인 분석 스크립트(URDF FK를 numpy로 다시 짠 것)는 scratchpad에만 있다. 구현 단계에서 `~/so101_boxpick/e0_j0/tools/`로 옮긴다.

## 0. 한눈에

```
dev_goal.sh 0.21 0.11 --deadline 90
        │  ExecuteGoal (/twin/goal)
        ▼
┌─ 컨테이너 (ROS2 Lyrical) ───────────────────────────────────────────────────┐
│ e0_j0_executor  = GoalExecutorNode 를 상속한 노드 (/robot/joint_cmd 유일 writer) │
│   GRASP(정책)  : joint_states·카메라 2대 → [변환 rad→도] → 정책 클라이언트       │
│                  ← action chunk(도) → RTC 큐 → 30 Hz /robot/joint_cmd            │
│   HANDOFF 판정 : 집게가 멈춰 쥠 + TCP 3 cm 상승 → 정책 정지·집게 조임 유지        │
│   PLACE(IK)    : E0-lite BranchSelector/TcpInverseKinematics 로 들기→이송→내리기  │
│                  →열기→물러나기→원위치 (부모 클래스 _command_and_wait 재사용)       │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │ TCP 172.17.0.1:<port> (docker0) — 표준 라이브러리 소켓, 길이-접두 프레임
┌──────────────▼──────────────────────────────┐
│ 호스트 ~/so101-env : e0j0_policy_server.py   │  pi05 15000 체크포인트, RTC(실물 평가와 같은 값)
│ (~/so101_boxpick/e0_j0/, 설치 없음)           │
└─────────────────────────────────────────────┘
```

- **체크포인트**: `~/so101_runs/practice/practice_50/train/pi05_15k/checkpoints/015000/pretrained_model`.
  2026-10-07 실물 평가 3회가 이 15000 스텝을 썼다. 평가 조건: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40 --robot.max_relative_target=8`, fps 30.
- **과제 문장**: `"pick up the red cube and put it in the brown box"` (데이터셋 meta와 같음).

### 바로 알아야 할 걸림돌 (지금 그대로면 실패)

1. **명령 상한**: 드라이버의 wrist_flex 상한이 arm #1 표 때문에 **89.7°**다. practice_50 행동의 **61.8%가 거부**된다. Thor EEPROM 창으로 바꾸면 0%다(§3-3).
2. **넘겨받는 자세에서 IK 해가 없을 수 있다**: 3 cm 들렸을 때 wrist_flex 중앙값이 95°다. E0-lite IK는 URDF 한계 ±95°에서 이송 여유 0.1 rad를 요구한다. 그래서 E0-lite의 "현재 자세 그대로 수직 들기"(C27)가 대부분 `ik_infeasible`이다. **들기는 top-down 자세로 다시 풀어야 한다**(§2-4).
3. **실물 모드의 가상 세계는 큐브가 registry 자리에 있다고 가정한다**. π0.5가 다른 자리에서 잡으면 `attach_state`가 IN_GRIPPER가 되지 않는다. 그래서 E0-lite의 "물고 있으면 재개"(C26) 경로를 **그대로는 탈 수 없다**. 넘겨주기 판정은 E0_J_0이 직접 한다.
4. **이송 중 조임이 풀린다(arm-jetson)**: 이름을 주지 않은 관절은 드라이버와 실행기 keepalive가 **측정값**으로 채운다. 그러면 큐브를 쥔 집게의 목표가 현재 위치가 돼서 쥐는 힘이 0이 된다. main은 "이송 중 조임 유지"로 고쳤다. E0_J_0은 넘겨준 뒤 모든 명령에 집게 조임 목표를 넣는다.
5. **속도 상한 9.2°/s (0.16 rad/s)**: 학습 데이터의 관절 속도는 p95 32–63°/s, p99 53–115°/s다. 정책이 내는 목표를 팔이 못 따라가 관측이 학습 분포를 벗어난다(§3-4).
6. **정책 서버 통신**: lerobot 서버는 gRPC다. so101-env에 grpcio가 없고, 컨테이너에는 torch와 lerobot이 없다. 그래서 표준 라이브러리 소켓 서버를 새로 쓴다(§3-1).

---

## 1. 트윈 실행기(E0-lite) 구조

### 1-1. 단계가 코드에서 나뉘는 방식

`GoalExecutorNode` (`twin_executor/goal_executor_node.py`, 1778줄)의 흐름은 다음과 같다.

- `_on_goal_request`: 진행 중이면 REJECT(busy), 아니면 ACCEPT. cancel은 항상 거부한다(`supports_cancel=false`).
- `_execute` → `_prepare(goal)` → `_run(...)` → `_attempt(...)`. 예외는 FAILED_HW, `GoalRejected`는 FAILED_REJECTED + reason으로 끝난다.
- `_prepare`: target_type(POSE만) → frame_id=`world` → registry 오브젝트 → **물고 있는지(`_held_object_id`)** → `/twin/objects` 관측 대기(`_await_observation`, 나이 ≤ 1.0 s) → URDF·IK 대기 → confidence → reach 구 → **가지 선택**.
  - 가지 선택은 `BranchSelector.select(pick, place, …)`, 물고 있으면 `select_place_only(…, lift=…)`.
- `_attempt`: 고정된 9단계 표(`steps`)를 차례로 `_command_and_wait`.

| feedback phase | label | 목표 |
|---|---|---|
| APPROACH | gripper open | 집게만 (opening 0.60) |
| APPROACH | pick standoff | 팔 5관절 (IK) |
| GRASP | pick grasp | 팔 (정밀 단계) |
| GRASP | gripper close | 집게 (실물: 완전 폐합 0) → 직후 `_is_held` 검사, 아니면 FAILED_GRASP |
| TRANSFER | lift to pick standoff | 팔 |
| TRANSFER | place standoff | 팔 |
| PLACE | place grasp | 팔 (정밀) |
| PLACE | gripper open | 집게 |
| RETREAT | retreat to place standoff | 팔 |

- **재개 경로(C26·C27)**: 수락 시점에 `/twin/objects`의 그 오브젝트가 IN_GRIPPER이면 APPROACH·GRASP를 건너뛴다. 첫 동작은 "현재 TCP 자세(FK) + world +Z로 `transfer_z_m`(0.065)까지"의 IK이고, 그다음 place standoff → place → open → retreat이다.
- **`_command_and_wait(targets, budget, criterion, phase, label)`**:
  - 지명 관절만 담은 `JointTrajectory`를 1점 발행한다(`_publish_cmd`). 실물에서는 `command_keepalive_s=0.1`로 다시 보낸다.
  - 도달은 "정착(0.3 s 창 이동량 ≤ v_eps×settle) + 단계 기준"이다. 팔은 TCP 거리 < tolerance×scale, 집게는 |q−target| ≤ q_tol(Thor 0.04).
  - 결과는 'reached' / 'ceased' / 'timeout'.
- **IK**: `twin_kinematics.TcpInverseKinematics`(KDL, DLS 6-잔차, URDF 한계 클램프). `BranchSelector.solve_tcp(frame, seeds, min_margin)`이 **한 자세**를 푸는 공개 메서드다. 여유 문턱은 파지 0.2 rad, 이송 0.1 rad.
- **서비스**: `/twin/home`(실물, fold 자세), `/twin/fold`, `/twin/selfcheck`, `/twin/release`.

### 1-2. IK 이동 부분을 따로 불러 쓸 수 있나 → 예 (상속으로)

- **그대로 재사용**: `BranchSelector.solve_tcp`, `select_place_only`, `object_to_tcp_frame`, `sweep_seeds`, `TcpForwardKinematics`, `GoalExecutorNode._command_and_wait`, `_stage_criterion`, `_publish_cmd`, `_publish_feedback`, `_make_result`, `_timeout/_ceased`, `_seeds`, `_await_ik`, `_await_sample`.
- **바꿔야 할 것**: `_prepare`(pick 관측을 요구하지 않음), `_attempt`(GRASP를 정책으로, 단계 표를 E0_J_0용으로).
- 따라서 **`class E0J0Executor(GoalExecutorNode)`**를 별도 패키지에 두고 두 메서드만 덮어쓴다. 박사님 파일은 고치지 않는다. 내부 메서드(밑줄 이름)에 의존하므로 rebase 때 시그니처가 바뀌면 같이 맞춘다(§4-4 질문).

### 1-3. 실행기를 바꿔 끼우는 방법

- **writer 규칙**: `/robot/joint_cmd`의 writer는 실행기 하나다(§3C, CLAUDE.md 규칙 6).
  - `dev_up`의 6/6 단계가 real_kinematic에서 publisher 1, arm_jog에서 0을 확인한다.
  - `jog_client`는 다른 writer가 있으면 동작을 거부한다.
  - 설계 리뷰도 "E0/E1을 동시에 joint writer로 띄우지 않고, 초기에는 **executor 내부 policy slot**을 권장"한다(`design_notes_scene_execution_review_D1_D7.md:197`).
  - → **E0_J_0이 goal_executor_node의 자리를 대신한다.** 같은 action 서버(`/twin/goal`), 같은 writer 한 개.
- **launch**: `demo.launch.py`가 프로파일별 노드를 하드코딩한다(`Node(package='twin_executor', executable='goal_executor_node')`). `PROFILE_NODES` 표와 대조하므로 바꿀 길이 없다.
  - 우리 브랜치에서 **`executor:=e0_j0` 인자**(기본 `goal_executor_node`)를 추가하고, `PROFILE_NODES` 표를 그에 맞춘다. `dev_up.sh`에는 `--executor e0_j0`(또는 환경변수 `TWIN_EXECUTOR`)를 추가한다.
  - real_kinematic의 executor 파라미터(`latency_budget_s`, `q_tol_rad`, `command_keepalive_s`, `fold_pose_rad`, `grasp_close_opening`, registry 등)는 그대로 상속 노드에 넘어간다.
  - kinematic_world와 ground_truth_publisher는 그대로 둔다(`/twin/objects` writer 1 → dev_up 4/6 통과). E0_J_0은 그 값을 판정에 쓰지 않는다.
- **카메라**: `dev_up --cameras`(실물 프로파일)가 `/head_camera/image_raw`와 `/wrist_camera/image_raw`를 띄운다. E0_J_0이 구독한다.
- **dev_goal이 보내는 것**:
  - `ExecuteGoal.Goal{object_id='red_cube_01', target_type=TARGET_POSE, target_pose(frame world, x, y, z=registry half-extent, yaw), tolerance_m(기본 0.02), deadline(기본 30 s)}`
  - 피드백은 phase(APPROACH…RETREAT)와 progress, 결과는 outcome·reason·final_pose(`/twin/objects`).
  - world = base_link(`calibration.yaml` 항등). E0_J_0도 같은 action을 받는다. Unity가 와도 바뀔 것이 없다.

---

## 2. E0_J_0 동작 설계

### 2-1. 상태 기계

```
ACCEPT(goal) → VALIDATE(frame·object·reach·IK place 가지 사전 확인)
  → GRASP_POLICY (feedback APPROACH→GRASP, 30 Hz 스트리밍)
       ├─ handoff 판정 OK → HANDOFF_HOLD
       ├─ 정책 시간 초과(기본 40 s) / 서버 끊김 1 s / 관측 stale → FAILED_GRASP 또는 FAILED_HW (팔 정지)
       └─ 안전 위반(TCP z < 바닥, 벽 밖) → FAILED_HW
  → HANDOFF_HOLD (집게 조임 목표 고정, 팔 현재 위치, 0.3 s 정착)
  → LIFT_TOPDOWN (TRANSFER) → PLACE_STANDOFF (TRANSFER) → PLACE (PLACE)
  → OPEN (PLACE) → RETREAT (RETREAT) → RETURN(원위치, RETREAT) → DONE
```

- **VALIDATE를 앞에 둔 이유**: 정책으로 큐브를 들었는데 놓을 곳의 IK가 없으면 공중에서 멈춘다. 그래서 goal을 받자마자 place standoff·place 자세의 IK를 미리 풀어 본다. 실패하면 정책을 시작하지 않고 `FAILED_REJECTED(ik_infeasible)`로 끝낸다.

### 2-2. 잡기 (GRASP_POLICY)

- **관측(매 틱 30 Hz, 최신값)**:
  - `/robot/joint_states`(position, rad) → lerobot 단위로 변환(§3-2) → `observation.state` 6개(순서: pan, lift, elbow, wrist_flex, wrist_roll, gripper)
  - `/head_camera/image_raw` → `front`, `/wrist_camera/image_raw` → `wrist`. rgb8, 480×640×3 uint8 그대로.
  - 신선도: 관절 ≤ 0.1 s, 이미지 ≤ 0.2 s. 아니면 그 틱은 명령을 보내지 않는다. 0.5 s 넘게 이어지면 중단.
- **정책 호출**: §3-1 서버에 chunk 요청.
  - RTC는 평가 조건 그대로다: chunk 50, `execution_horizon=20`, `queue_threshold=40`. 큐가 40 미만이면 새 chunk를 요청하고, `inference_delay`는 실측 지연 틱 수, `num_inference_steps=5`.
  - 큐 관리는 클라이언트(컨테이너)에서 하고, 서버는 직전 chunk를 보관해 RTC prefix를 만든다.
- **명령(30 Hz 타이머)**: 큐에서 한 action(도/0~100)을 꺼낸다.
  - **max_relative_target 8 클립**(lerobot 평가와 같음): 측정값 기준 관절별 ±8.
  - rad로 변환(§3-2) → 벽 사전 검사 → 6관절 전체를 `/robot/joint_cmd`로 보낸다.
  - 큐가 비면 보내지 않는다. 같은 값을 반복하지 않으므로 드라이버 워치독 0.5 s 뒤 서보가 제자리를 잡는다.
- **안전 감시(매 틱)**: FK TCP z ≥ −0.03 m(탁자 아래로 파고들지 않기), 벽 안, 관측 신선도. 어기면 즉시 정책을 멈추고 FAILED_HW(팔 정지).
  - 정책 단계에서는 **사람이 12 V 옆에 있다**는 전제다. ^C는 goal을 취소하지 않으므로 `/e0j0/stop`(Trigger) 서비스를 둬서 정책을 즉시 멈추고 정지 상태로 FAILED_HW를 낸다.

### 2-3. 넘겨주기 판정 (데이터로 정한 값)

practice_50 50 에피소드를 오프라인으로 분석했다. URDF FK, 트윈과 같은 변환을 썼다.

| 항목 | 값 |
|---|---|
| 쥔 집게 값 (0~100) | 중앙값 **32.4**, p5 25.4 (Thor 집게 표에서 53 mm ≈ 31.4 → **큐브는 약 53 mm**) |
| 그때 명령 값 | 중앙값 31.3 (조작자가 큐브 폭까지만 닫았다 — 꽉 쥐지 않음) |
| 빈손 완전 폐합 | 0.5–1.4 |
| 쥔 시각 (시작 후) | 중앙값 9.3 s, p95 13.9 s |
| 쥔 뒤 TCP 3 cm 상승까지 | 중앙값 **0.65 s**, p5 0.33, p95 2.2 s |
| 그동안 수평 이동 | 중앙값 1.4 cm, p95 4.0 cm |
| 쥔 순간 TCP 기울기 | top-down에서 중앙값 22°(p5 15°, p95 27°) |
| 3 cm 상승 때 wrist_flex | 중앙값 95.0°, p5 82.1°, p95 98.9° |
| 쥔 위치 (트윈 좌표) | 중앙값 (0.188, −0.044) m, x 0.13–0.23, y −0.08–0.03 |
| 놓은 위치 (트윈 좌표, 박스) | 중앙값 **(0.208, 0.110)**, TCP z ≈ −0.005 (박스 바닥 ≈ 탁자) |
| 이송 중 TCP 최고 높이 | 중앙값 0.085 m, p5 0.071 (박스 벽을 넘는 높이) |

**판정 규칙(초안)**:
1. **쥠**: 집게가 한 번 35 이상 열린 뒤, 측정값이 최근 10틱(0.33 s) 동안 변동 < 1.0이고, 값이 **12 ≤ g ≤ 55**(완전 폐합 < 5와 구분), 정책의 집게 명령 ≤ g + 3(여는 중이 아님). 만족한 첫 틱을 `t_hold`, 그때 TCP z를 `z_hold`, 집게 값을 `g_hold`로 기록한다.
2. **들림**: `t_hold` 이후 TCP z − z_hold ≥ **0.03 m** → 넘겨주기.
3. 쥠 뒤 2.5 s 안에 들림이 없거나 집게가 다시 35 이상 열리면 쥠 판정을 취소하고 정책을 계속한다(정책의 재시도 허용).
4. 실물에서는 쥔 큐브가 막아 서보가 멈춘 값이 g다. sim에서는 명령값에 도달해 멈춘다(같은 규칙으로 잡힌다).

**넘겨줄 때 할 일**:
- 정책 큐를 비우고 서버 세션을 닫는다.
- 집게 목표를 `g_hold − 6`(≈ 10 mm 조임, 집게 표 기울기 ≈ 0.58/mm)으로 고정한다. **이후 모든 팔 명령에 이 집게 목표를 함께 넣는다**(§0 걸림돌 4).
- 팔은 측정 위치로 한 번 명령하고 정착 0.3 s를 기다린다.

### 2-4. 이동·놓기·물러나기·원위치 (E0-lite IK 재사용)

TCP 높이 기준을 registry 대신 **넘겨줄 때 기록한 실측**으로 둔다. π0.5가 쥔 위치·기울기가 registry의 공칭 grasp offset과 다르기 때문이다.

| 단계 | feedback | 목표 | 방법 |
|---|---|---|---|
| LIFT_TOPDOWN | TRANSFER | 현재 TCP의 (x, y), z = **z_carry**(기본 0.10 m, 데이터 최고 높이 0.085 + 여유), 자세 = **top-down**, yaw = 현재 TCP 방위 | `solve_tcp(frame, [현재 관절 seed], transit 0.1)`. 실패하면 cube 대칭 90° 가지 → 그래도 실패하면 FAILED(ik_infeasible)로 **들고 정지**(사람이 /twin/release) |
| PLACE_STANDOFF | TRANSFER | (goal x, y, z_carry), top-down, place yaw | `solve_tcp` (E0 seeds) |
| PLACE | PLACE | (goal x, y, **z_hold + 0.01**) | `solve_tcp`, 정밀 단계 기준 |
| OPEN | PLACE | 집게 opening 0.60 (≈ 56, 데이터의 놓을 때 50–63) | 집게만 |
| RETREAT | RETREAT | PLACE_STANDOFF 자세 | 관절 목표 |
| RETURN | RETREAT | fold 자세(`fold_pose_rad`) 또는 설정한 시작 자세 | 관절 목표 |

- 각 단계는 부모의 `_command_and_wait`에 넣는다. 도달 기준은 그대로(TCP 거리·정착)이고, 팔 단계 목표에는 **집게 조임 목표를 포함**한다.
- **속도**: 드라이버 상한을 정책용으로 높이면(§3-4) IK 단계가 너무 빠르다. 그래서 E0_J_0이 IK 단계에서 관절 공간 보간 경유점을 **최대 0.3 rad/s**(≈ 17°/s)로 30 Hz 발행한다. 기존 E0 값 0.16의 약 2배이고 박사님과 정한다.
- **놓기 결과**: `/twin/objects`(추측 항법)는 실제 큐브를 모른다. 그래서 E0-lite의 place 잔차 검사와 재시도(`retry_on_miss`)는 **쓰지 않는다**.
  - 성공 = 모든 단계 도달 + 집게 열림 확인. `final_pose`는 의미 없음을 로그에 적는다.
  - 실제 성공은 사람이 보고 판정하거나, 머리 카메라 프레임을 저장해 사후 판정한다.
- **dev_goal 목표**: 데이터의 박스 위치는 (0.21, 0.11)이다. 시험 명령은 `dev_goal.sh 0.21 0.11 --deadline 90 --tol 0.03`이다.
  - 정책 잡기 ~10 s, IK 단계 ~25 s(0.3 rad/s), 기본 deadline 30 s로는 부족하다.
- **장면**: 학습 때와 같게 둔다. 큐브는 오른쪽 앞 (0.13–0.23, −0.08–0.03) 범위, 갈색 박스는 왼쪽 (0.21, 0.11) 근처, 카메라 자동 노출·WB. `setup_photos/ep000_front_first.png`를 기준 사진으로 쓴다.

---

## 3. 걸림돌과 해결안

### 3-1. 정책 서버 통신 (설치 없이)

조사한 사실:
- lerobot `async_inference.policy_server`는 **gRPC + pickle**이다(`import grpc`). so101-env에 `grpc` 없음.
- so101-env에 있는 것: `zmq`(pyzmq), `cv2`, `numpy`, `requests`, `aiohttp`. 없는 것: `websockets`, `msgpack`.
- 컨테이너 이미지에 있는 것: python3, numpy·cv2(ROS desktop·카메라 노드가 씀), `python3-websockets`. torch·lerobot·zmq는 Dockerfile에 없다.
- 컨테이너는 bridge 네트워크다. 호스트는 컨테이너에서 **172.17.0.1**(docker0)로 보인다.

| 방법 | 설치 | 장점 | 단점 |
|---|---|---|---|
| **A. 표준 라이브러리 TCP 소켓 (권장)** — 서버 so101-env, 클라이언트 컨테이너 노드 | 없음 | 양쪽 다 이미 있는 것만 쓴다. 이미지 원본(무손실)을 그대로 보낸다. 지연이 작다 | 프레이밍·재연결을 직접 짠다(~150줄). 서버를 docker0 IP에만 바인드해야 한다 |
| B. 표준 라이브러리 HTTP (`http.server` / `urllib`) | 없음 | 디버깅 쉬움(curl) | 요청마다 연결 오버헤드. 기능은 A와 같음 |
| C. Unix 소켓 (바인드 마운트 경로 `/ws/run/e0j0.sock`) | 없음 | 네트워크 노출 0 | 소켓 파일이 리포 작업 트리(우리 클론의 ros2_ws) 안에 생긴다. `.gitignore` 필요 |
| D. pyzmq | 컨테이너에 python3-zmq 설치(이미지 변경) | 메시지 큐 편함 | 이미지 재빌드 = 박사님 레인 |
| E. lerobot gRPC 그대로 | so101-env에 grpcio, 컨테이너에 lerobot+torch | 서버 코드 0줄 | 금지 조건 위반. 컨테이너 torch는 예전에 776 MB로 기각됐다 |
| F. 컨테이너 안에서 정책 실행 | torch·lerobot·GPU 런타임 | 통신 없음 | 같은 이유로 제외 |

**권장 A**의 세부 사항.
- **프레임**: `[4바이트 길이][JSON 헤더][원시 바이트들]`.
- **요청**: `{"v":1, "type":"infer", "seq":n, "t_obs":…, "state":[6, lerobot 단위], "task":"…", "images":{"front":[480,640,3], "wrist":[480,640,3]}, "executed_since_last":k, "inference_delay":d}` + RGB 바이트 2개(1.84 MB).
- **응답**: `{"seq":n, "chunk":[[6]×50], "infer_ms":…, "model":"pi05_15k@015000"}`.
- `type:"hello"`로 체크포인트·과제·버전을 확인하고, `type:"reset"`으로 RTC 상태를 비운다.
- **요청 빈도**: 큐 40 미만일 때 → 약 3 Hz. 이미지 1.84 MB × 3 Hz는 bridge 네트워크에 부담이 없다.
- **서버**(`~/so101_boxpick/e0_j0/e0j0_policy_server.py`, so101-env로 실행):
  - 체크포인트에서 `make_pre_post_processors`, policy 로드(bf16, cuda), `num_inference_steps=5`.
  - 요청마다 `preprocessor → predict_action_chunk(batch, inference_delay=d, prev_chunk_left_over=직전 chunk[k:], execution_horizon=20) → postprocessor`.
  - RTC prefix를 만드는 규칙은 lerobot `rollout/inference/rtc.py`의 `_rtc_loop`를 그대로 옮긴다(정규화 공간 여부 포함, 구현 때 대조).
  - 한 번에 한 클라이언트만 받는다.
  - **바인드는 `172.17.0.1`만**이다. pickle을 쓰지 않으므로(JSON + 원시 바이트) 신뢰 문제도 줄어든다.
- **가짜 정책 서버**(sim용): 같은 프로토콜로, practice_50 에피소드 n의 행동을 틱 번호로 잘라 chunk로 돌려준다. GPU를 쓰지 않는다.

### 3-2. 관절 변환 (트윈 ↔ lerobot)

- **공통**: STS3215 해상도 4096, `max_res = 4095`, `mid = (range_min + range_max) / 2`(캘리브레이션 json, Thor = `sites/thor/calibration_so101_jetson.json` = lerobot `my_arm.json`, sha256 같음).
- **몸통 5관절(DEGREES)**:
  - lerobot: `deg = (tick − mid) × 360 / 4095`
  - 트윈: `q = (tick − mid) × 2π / 4095 + Z[j]`, `Z = {shoulder_pan: +0.1381, 나머지 0}`(arm #1 값, `servo_map.ZERO_OFFSET_RAD`)
  - ⇒ **`q = radians(deg) + Z[j]`**, **`deg = degrees(q − Z[j])`**
- **gripper(RANGE_0_100)**:
  - lerobot: `v = clamp((tick − min)/(max − min) × 100, 0, 100)`
  - 트윈: `q = radians(v)`(발행 범위 0…1.7453)
  - ⇒ **`v = degrees(q)`**, **`q = radians(v)`**
- **명령 쪽**: 트윈 `to_ticks`가 lerobot `_unnormalize`와 같은 산술이다(`int(deg × 4095/360 + mid)`, 집게는 `int(v/100 × (max−min) + min)`, 절단). 같은 action이면 **같은 tick**이 서보에 간다. 골든 벡터 `fixtures/p3a/lerobot_norm_golden.json`이 1e−6으로 단정한다.
- **변환식은 E0_J_0 안에 다시 적지 않는다.** `twin_backend.servo_map.ZERO_OFFSET_RAD`와 `RANGE_0_100_JOINTS`를 import한다. 박사님이 Thor pan 영점(−0.2194)을 반영하면 자동으로 따라간다.
  - 단, 그러면 트윈 좌표의 박스 위치가 회전한다. dev_goal 목표를 다시 계산해야 한다(§4-4 질문).

**같은 자세에서 확인하는 방법**:
1. **오프라인(장치 없음)**: Thor 캘리브레이션으로 tick 0…4095 전 구간에 두 식을 계산해 `|q − (radians(deg)+Z)| < 1e−9`, 집게 `|degrees(q) − v| < 1e−9`를 단위 테스트로 단정한다.
2. **실물 읽기 전용**(팔을 접어 두고 손대지 않는다, 토크 off):
   - ① `~/so101-env/bin/python ~/so101_boxpick/scripts/servo_dump.py --arm follower`로 Present_Position tick 6개를 읽는다(쓰기 0회).
   - ② `dev_down` 상태에서 `dev_up --real-ro` → `dev_ros.sh topic echo /robot/joint_states --once`.
   - 같은 자세에서 ①을 lerobot 식으로 바꾼 값과 ②를 `degrees(q−Z)`로 바꾼 값이 관절마다 **1 tick(0.088°) 이내**인지 본다.
   - 버스는 한 번에 하나만 쓰므로 ①과 ②를 차례로 한다.
3. **그림자 모드**(`--real-ro --cameras`, §4-3 ②): E0_J_0 노드가 보낸 state(도)를 로그로 남긴다. 팔을 데이터 시작 자세 근처에 두고 데이터 첫 프레임 state와 비교한다(대략 일치하는지만).

### 3-3. 드라이버 명령 상한 (데이터로 확인)

- **벽의 원천**(`servo_map.build_walls`):
  - 몸통 4관절 = **arm #1 하드스톱 표 `PHYSICAL_LIMIT_RAD` ∩ 서보 EEPROM 창**
  - wrist_roll = URDF(−157.2°…+162.8°)
  - 집게 = [0, 100]
  - 벽 밖 값이 하나라도 있으면 **메시지 전체 거부**이고, 팔은 직전 목표를 유지한다.
- **practice_50 행동(30,884 프레임)과 대조**한 결과(lerobot 도):

| 관절 | 트윈 벽 (arm #1 ∩ EEPROM) | Thor EEPROM 창 | 데이터 행동 범위 | 벽 밖 |
|---|---|---|---|---|
| shoulder_pan | −96.9 … 98.4 | −110.2 … 110.2 | −47.3 … 83.0 | 0 % |
| shoulder_lift | −101.8 … 91.4 | −103.7 … 103.7 | −57.3 … 63.9 | 0 % |
| elbow_flex | −96.7 … 93.1 | −96.7 … 96.7 | −60.5 … 80.6 | 0 % |
| **wrist_flex** | −97.1 … **89.7** | −102.1 … 102.1 | 47.3 … **99.8** | **61.8 %** |
| wrist_roll | −157.2 … 162.8 (URDF) | (full-turn) | −55.3 … 56.6 | 0 % |
| gripper | 0 … 100 | — | 0.0 … 89.7 | 0 % |

  - → 지금 그대로면 **프레임의 61.8 %가 거부**된다. 시작 자세(wrist_flex ≈ 94–99°)부터 거부된다. **EEPROM 창만 벽으로 쓰면 0 %**다.
- **Thor 기준으로 바꾸는 방법**(우리 브랜치에서, 박사님 확인 뒤):
  1. 드라이버에 `physical_limits_file` 파라미터를 추가하고, `sites/thor/measured.yaml`에서 읽는다(requests_to_main 7번 제안과 같은 방향).
  2. Thor 값:
     - pan = 실측 하드스톱(published −1.278 … +1.993 rad, arm #1 영점 좌표)
     - lift·elbow·wrist_flex = **EEPROM 창**. measured.yaml이 "나머지 몸통 관절은 EEPROM 창이 벽이라 생략"이라고 적은 결정과 같다.
  3. `dev_up.sh`가 `TWIN_SERVO_CALIBRATION`의 site 폴더에서 `measured.yaml`을 함께 넘긴다(`.limits.yaml`과 같은 관용구).
  4. E0_J_0은 보내기 전에 같은 벽 함수로 사전 검사하고, 밖이면 그 틱을 보내지 않고 로그를 남긴다. 클램프는 하지 않는다(정책 행동을 몰래 바꾸지 않는다).
- IK 단계는 URDF 한계(wrist_flex ±95°)를 쓴다. 정책 단계와 벽이 다른 것은 의도다. 넘겨받는 자세 문제는 §2-4의 top-down 재해석으로 푼다.

### 3-4. 속도 제한·P 게인의 영향과 권장 설정

| 항목 | 학습·평가 조건 | 트윈(arm-jetson) | 영향 |
|---|---|---|---|
| 관절 속도 | 제한 없음 (서보 Goal_Velocity 0). 데이터 p95 32–63°/s, p99 53–115°/s | **0.16 rad/s ≈ 9.2°/s** (`speed_scale_real 0.2 × max_joint_vel 0.8`, 드라이버 램프 + 서보 46번 이중) | 팔이 정책 목표를 못 따라간다 → 관측이 학습 분포를 벗어난다 → 같은 자리를 반복하거나 재시도. 10-02 lerobot이 이 값에 묶였을 때 리더를 늦게 따라간 것과 같은 부류 |
| 가속 | lerobot Acceleration 254 (최대) | 2.0 rad/s² | 짧은 chunk 전환마다 출발이 늦다 |
| P 게인 | **P16** (lerobot이 연결마다 씀) | **P32** (토크 on 때 EEPROM에 씀) | 같은 목표에서 처짐과 응답이 다르다(작은 분포 이동). 2호 팔 처짐 때문에 E0-lite가 P32를 골랐다 |
| 상대 목표 제한 | 평가 때 `max_relative_target=8` | 없음 | E0_J_0이 직접 8 클립을 한다 |

**시제품 권장 설정** (우리 브랜치 전용 constants 파일. `demo.launch.py`의 `constants_file` 인자는 이미 있고, dev_up에서 넘기는 줄만 추가):
- `real.speed_scale_real: 1.0`, `real.max_joint_vel_rad_s: 2.0`(≈ 115°/s, 데이터 p99 이상), `real.max_joint_acc_rad_s2: 20.0`(레지스터 상한 39 rad/s² 안).
  - 드라이버 상한은 "안전 천장"으로만 쓰고, 실제 속도 모양은 정책(정책 단계)과 E0_J_0 보간 0.3 rad/s(IK 단계)가 정한다.
- `real.servo_gains: {p: 16, i: 0, d: 32}` — 학습과 같게. 대가로 E0 IK 단계의 처짐이 커질 수 있어 `q_tol`/tolerance를 0.03–0.04로 둔다.
  - P를 단계마다 바꾸는 것은 EEPROM 쓰기라 하지 않는다.
- 안전 장치: 사람 동석과 12 V, 정책 단계의 8 클립·TCP 바닥 감시·벽 사전 검사, `/e0j0/stop`.
  - 첫 실물 시험은 `max_joint_vel 1.0`(57°/s, 데이터 p95 수준)으로 시작해서 박사님과 올린다.
- 세션 뒤에는 **12 V 재투입**이 필요하다. Goal_Velocity가 SRAM에 남기 때문이다. 높인 값이라도 0(무제한)과는 다르다.

### 3-5. 카메라

| 항목 | 학습 (practice_50) | 트윈 토픽 | 판정 |
|---|---|---|---|
| 장치 | front = USB 2.4 (/dev/cam_front = video0), wrist = 2.3.2 (video2) | `/head_camera` = 2.4 (video0), `/wrist_camera` = 2.3.2 (video2) — `dev_cams.sh` OK | 같음. **키 매핑 head → front** |
| 해상도·코덱·fps | 640×480, MJPG, 30 fps (lerobot OpenCVCamera) | 640×480, MJPG, 30 fps. `uvc_camera_node`가 lerobot `OpenCVCamera`의 연결·설정 순서를 그대로 옮겼다(V4L2, 되읽어 다르면 기동 실패) | 같음 |
| 색 순서 | OpenCV BGR → **RGB** | `cv2.cvtColor(BGR2RGB)`, `encoding: rgb8` | 같음 (메시지 encoding을 확인하고, 다르면 거부) |
| 노출·WB | **자동** (auto_exposure=3, WB 자동, dynamic_framerate 0 — 녹화 전 점검 기록) | 트윈은 **건드리지 않는다**. 지금 두 대 모두 자동(2026-10-07 조회) | 같음. 재연결·재부팅 뒤 기본값으로 돌아가므로 세션마다 `v4l2-ctl -C`로 확인 |
| 학습 때 이미지 경로 | 녹화 프레임 → AV1 영상 → 디코드(압축 흔적 포함) | 원본 MJPEG 디코드 | lerobot 실물 평가와 같은 조건(평가도 원본 프레임) |
| QoS·나이 | — | sensor_data(best effort), header stamp | E0_J_0은 나이 ≤ 0.2 s만 쓴다 |

- 그림자 모드(②)에서 확인할 것: 두 토픽 각 ~30 Hz, 프레임 저장 → 학습 첫 프레임(`setup_photos/ep000_*`)과 흰 탁자 밝기·색 치우침 비교(`camera_settings.md` 방법).

### 3-6. 큐브 크기·놓기 높이·쥠 판정

- **실제 큐브 ≈ 53 mm.** 쥔 집게 값 32.4 ↔ Thor 집게 표 53 mm = 31.4. arm-jetson registry는 35 mm(`size_m 0.035`, half 0.0175)이고, main은 53 mm로 바꿨다.
- E0_J_0은 **높이를 registry로 계산하지 않는다**(§2-4: z_hold, z_carry 실측 기준). registry는 dev_goal이 target z를 채우는 데와 sim 시각화에만 쓰인다.
  - 우리 브랜치 sim fixture는 53 mm(`size_m 0.053`), attach_max_opening 0.45(main 값)로 둔다. 쥔 값 32 ≈ opening 0.38이라 0.33으로는 sim에서 attach가 안 된다.
- 놓기 높이: 데이터에서 박스 안 놓는 TCP z ≈ 쥘 때 z이므로 **z_hold + 0.01 m**. 이송 높이 z_carry = 0.10 m(박스 벽을 넘는 데이터 최고 높이 0.085 + 여유). 박스 벽 높이를 한 번 자로 재서 확정한다.
- 쥠 판정: §2-3. 실물에서는 서보가 큐브에 막혀 멈춘 값이 g다. P16에서 정책 명령(≈ g)과 측정의 차이가 작아 **쥐는 힘이 약하다**(데이터도 그렇다). 그래서 넘겨줄 때 조임(g − 6)을 반드시 넣는다.

---

## 4. 작업 방식

### 4-1. ~/Ros2 arm-jetson은 그대로 두고 별도 클론에서

- **worktree 대신 클론**: `git worktree add`는 `~/Ros2/.git`에 메타데이터를 쓴다.
  ```bash
  git clone --branch arm-jetson ~/Ros2 ~/Ros2_e0j0          # 또는 원격에서 clone 후 arm-jetson 체크아웃
  git -C ~/Ros2_e0j0 switch -c e0j0/proto
  ```
  원격 푸시는 박사님 허락 뒤에 한다(브랜치 이름 `e0j0/proto`).
- **빌드 볼륨을 분리한다(중요)**:
  - `dev_container.sh`의 볼륨 이름은 `VOL_PREFIX=twin_ws`로 고정이다. 클론에서 그대로 colcon 빌드하면 **박사님 환경의 install 볼륨을 덮어쓴다**.
  - 우리 브랜치에서 `VOL_PREFIX=${TWIN_VOL_PREFIX:-twin_ws}`로 바꾸고 `TWIN_VOL_PREFIX=twin_e0j0`를 쓴다. 첫 빌드는 전체 colcon 빌드다(에이전트가 하고 사람이 확인).
- 컨테이너 이름(`twin_ws_dev`)과 버스는 공유한다. **한 번에 한 쪽만** 띄운다(dev_up이 이미 거부한다).

### 4-2. 코드 위치

| 무엇 | 어디 | 이유 |
|---|---|---|
| 정책 서버, 가짜 정책 서버, 프로토콜(호스트 쪽), 오프라인 분석(넘겨주기 판정 재현·벽 대조·FK) | `~/so101_boxpick/e0_j0/` | so101-env로 실행. ~/Ros2 밖 |
| ROS 패키지 `twin_e0j0`(상속 실행기, 정책 클라이언트, 넘겨주기 판정, 변환·벽 사전 검사, 그림자 모드 엔트리) | `~/Ros2_e0j0/ros2_ws/src/twin_e0j0/` | 컨테이너는 클론의 `ros2_ws`만 본다(`/ws`) |
| 프로토콜 모듈 | 양쪽에 **같은 파일 사본** + `PROTOCOL_VERSION` 확인(hello) | 컨테이너가 ~/so101_boxpick을 볼 수 없다 |
| 실행 기록 | `~/so101_runs/e0_j0/runs/<시각>/` | 서버 로그, 노드 로그(넘겨주기 시각·z·g), 저장 프레임 |

### 4-3. 시험 순서

**① sim + 가짜 정책(행동 재생)** — 혼자 가능, 하드웨어 없음.
- 사전(오프라인): 넘겨주기 판정을 50 에피소드에 돌려 50/50 검출과 시각 분포가 §2-3 표와 같은지 본다. 변환 단위 테스트, 벽 사전 검사 단위 테스트, 상속 실행기 단위 테스트(부모 테스트 패턴)도 한다.
- `dev_up --executor e0_j0 --registry fixtures/e0j0/registry_53_ep<n>.yaml --viz`(sim, 큐브를 에피소드 n의 쥔 위치에) + 가짜 서버(에피소드 n) → `dev_goal.sh 0.21 0.11 --deadline 90`
- 확인할 것:
  - 30 Hz 발행(`topic hz /robot/joint_cmd`)
  - 넘겨주기가 오프라인 예측 시각 ±0.2 s에 일어나는지
  - LIFT_TOPDOWN IK가 풀리는지(실패율을 에피소드 50개로 집계)
  - DONE까지 단계 로그
  - writer 1(`dev_status`)
- sim 한계: 큐브 물리가 없다. 집게는 명령값에서 멈추고, 실물 동역학은 다르다. 흐름만 본다.

**② 실물 읽기 전용** — 혼자 가능, 팔은 토크 off.
- §3-2의 servo_dump ↔ joint_states 비교(1 tick).
- `dev_up --real-ro --cameras` + **그림자 모드**(`e0_j0_shadow` 엔트리: 실행기 없이 관측 → 실제 정책 서버 → action 로그만, 발행 0. arm_only에는 `/robot/joint_cmd` 구독조차 없다).
- 확인할 것:
  - 카메라 30 Hz와 색·밝기 비교
  - 서버 지연(infer_ms, 왕복)
  - 팔을 손으로 시작 자세에 뒀을 때 정책 chunk가 큐브 쪽으로 향하는지(데이터 첫 chunk와 대략 비교)
  - 로그된 action의 벽 밖 비율(Thor 벽 기준 0이어야 함)

**③ 실물 구동** — **박사님 동석**, 12 V 옆.
- ③a: `--real --executor e0_j0 --cameras`, 정책 단계와 **넘겨주기 뒤 HOLD까지만**(놓기 끔, 플래그). 큐브를 쥐고 3 cm 들면 멈추는지, 조임으로 큐브가 버티는지 본다 → `/twin/release`로 놓는다.
- ③b: 전체(놓기·물러나기·원위치). `dev_goal.sh 0.21 0.11 --deadline 90 --tol 0.03`.
- 끝나면 `dev_down --real` → **12 V 재투입** → servo_dump로 Goal_Velocity 0 확인 → lerobot 쪽 사용 가능.
- 속도 천장은 1.0 rad/s로 시작해서 결과를 보고 올린다.

### 4-4. 박사님 코드에 손대는 곳 (우리 브랜치에서만, 나중에 main 요청 후보)

1. `demo.launch.py`: `executor` 인자 + `PROFILE_NODES` 표(실행기 교체). `dev_up.sh`: `--executor`, `TWIN_CONSTANTS_FILE` 전달.
2. 드라이버 벽: `physical_limits_file` 파라미터(site `measured.yaml`). requests_to_main 7번과 같은 방향이다.
3. `dev_container.sh`: `TWIN_VOL_PREFIX`(볼륨 분리).
4. 우리 전용 `constants_e0j0.yaml`(속도·가속·게인·attach)과 registry fixture(53 mm). 박사님 원본 파일은 고치지 않고 사본을 둔다.
5. 고치지 않고 **상속**만 하는 것: `goal_executor_node.py`(내부 메서드 의존), `servo_map`(import만).

### 4-5. 박사님께 물어볼 것

1. **실행기 안에 정책 슬롯을 두는 방식**(GoalExecutorNode 상속, writer 1개 유지)을 E1 시제품으로 받아도 되는지. 내부 메서드(`_command_and_wait` 등)를 상속해서 쓰는 것에 대한 안정성 약속(rebase 때 깨질 수 있음).
2. **Thor 벽**: lift·elbow·wrist_flex를 EEPROM 창으로 써도 되는지, 하드스톱을 따로 재야 하는지. `physical_limits_file` 방식에 동의하는지.
3. **정책 단계 속도·가속·P 게인**: 천장 1.0 → 2.0 rad/s, 가속 20 rad/s², P16을 실물에서 허용하는지. IK 단계 0.3 rad/s는 괜찮은지. EEPROM P 16 ↔ 32 반복 쓰기는 괜찮은지.
4. **기준 브랜치**: arm-jetson(10-01)에서 시작할지, main(eb90313: 53 mm registry, 집게 토크 가드, cv2 카메라 노드, 이송 중 조임 유지)으로 rebase한 뒤 시작할지. rebase하면 카메라 노드가 바뀌므로 토픽 이름·encoding이 그대로인지도 확인한다.
5. **pan 영점**: Thor 값(−0.2194) 반영 계획. 반영되면 dev_goal 좌표계가 약 20° 돈다(박스 (0.21, 0.11)를 다시 계산).
6. **정책 서버 네트워크**: docker0(172.17.0.1)에 TCP 포트 하나를 여는 것과 Unix 소켓(바인드 마운트) 중 어느 쪽이 괜찮은지.
7. **넘겨준 뒤 실패 처리**: 들고 있는 채 IK가 없거나 단계가 실패하면 "들고 정지 → 사람이 `/twin/release`"로 하는 것에 동의하는지. `/e0j0/stop` 서비스를 추가해도 되는지(다리 allowlist에는 노출하지 않음).
8. 빌드: 클론에서 별도 볼륨(`twin_e0j0_*`)으로 전체 빌드해도 되는지, 이미지는 그대로 쓰는지(추가 패키지 없이 가능하게 설계함).
