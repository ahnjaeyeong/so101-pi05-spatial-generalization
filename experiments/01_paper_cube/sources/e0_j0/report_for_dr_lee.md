# E0_J_0 실험 보고 — π0.5 잡기 + E0-lite IK 놓기 (Thor, 2026-10-06 ~ 10-08)

- 작성: 2026-10-08. 이 문서는 기존 기록을 **읽기만** 해서 정리했습니다. 코드·설정·컨테이너는 이 보고를 위해 바꾸지 않았습니다.
- 표시:
  - **[측정]** 로그·파일에 남은 값
  - **[추정]** 측정에서 끌어낸 해석
  - **[사용자 관찰]** 사람이 보고 말한 것(기록 파일 없음)
- 시각: 사람 기준은 KST로 적었습니다. 실행기 기록 파일 이름(`trial_*.jsonl`)과 그 안의 `wall`은 컨테이너 UTC(= KST − 9 h)입니다.
- 자세한 날짜순 기록: `~/so101_runs/e0_j0/experiment_log.md`. 시험별 표: `~/so101_runs/e0_j0/runs/index.md`.

---

## 1. 한 일 요약

### 1-1. practice_50 수집과 π0.5 학습

| 항목 | 내용 | 근거 |
|---|---|---|
| 과제 | "pick up the red cube and put it in the brown box" — 빨간 종이 큐브(≈ 53 mm)를 갈색 종이박스에 넣기 | `dataset/meta/tasks.parquet`, `practice_50/notes.md` |
| 수집 | 2026-10-06 14:02–15:0x, lerobot 0.6.2 `record_ui.py`, 리더–팔로워 원격 조작, 팔로워 P16(lerobot 기본) **[측정]** | `practice_50/notes.md` 녹화 기록 6회 |
| 규모 | **50편, 30,884 프레임, 30 fps**, 편당 14.0–26.6 s, NaN 0. 40·41·42번은 의도한 빗잡기 **[측정]** | `dataset/meta/info.json`, notes.md "사전 점검" |
| 카메라 | front(머리)·wrist 640×480 MJPG 30 fps, 자동 노출·자동 WB(3/1/0) **[측정]** | notes.md, `~/so101_runs/camera_settings.md` |
| 학습 | `lerobot-train --policy.type=pi05 --policy.pretrained_path=lerobot/pi05_base --policy.dtype=bfloat16 --policy.gradient_checkpointing=true --batch_size=4 --steps=15000` (4.14B 전부 학습, lr warmup 500 / decay 15000, peak 2.5e-5) | notes.md "학습 기록", `train/run_pi05_15k.sh` |
| 결과 | 정상 종료. loss 0.131(step 50) → 0.014(15000), 마지막 5회 평균 0.011. 9 h 51 m(2.36 s/step), 메모리 최대 약 65 GB(통합) **[측정]** | `train/pi05_15k.log`, notes.md |
| 체크포인트 | `005000`·`010000`·`015000`(= `last`). 각 `pretrained_model` 8.8 GB + `training_state` 15 GB. 이후 모든 시험은 **015000** | `train/pi05_15k/checkpoints/` |

### 1-2. lerobot rollout (팔 직접, 트윈 없음)

| 날짜 | 횟수 | 결과 | 근거 |
|---|---|---|---|
| 10-07 10:36–10:48 | **3회** (episodic, 녹화) | **3/3 성공** **[측정]** 앞 카메라 마지막 프레임에서 큐브가 박스 안. 관절 기록상 쥠 7.3–9.7 s, 박스 쪽에서 다시 엶 10.4–12.6 s | `eval/rollouts/20261007_{103612,104105,104451}_15k_rtc_fast/` (dataset·analysis.json·console.log) |
| 10-08 10:20–10:27 | **4회** (base 전략, 45 s × 3 + 32 s, **녹화 없음**) | **[사용자 관찰]** 문제없이 진행. 기록은 cadence뿐(29.92 Hz, 굶은 틱 9–24) | `eval/rollout_today_20261008_102000.log` |

- 설정(둘 다): `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40 --robot.max_relative_target=8`, fps 30 **[측정]** (`command.txt`, 로그 argv).
- RTC 추론 지연(10-07): 첫 700–740 ms, 평균 316–317, p95 330–340, 최대 370–380 ms **[측정]** (각 `debug.log`).

### 1-3. E0_J_0을 만든 이유와 구조

- **이유**: arm-jetson(43d25ef)에는 정책으로 움직이는 실행기(E1)가 아직 없습니다 **[측정]** (2026-10-07 조사, `~/so101_runs/ros2_guide.md`). 학습한 π0.5를 트윈에서 돌려 보려고 **시제품**을 따로 만들었습니다. 잡기는 π0.5가, 옮기기·놓기는 E0-lite IK가 맡습니다.
- **구조** (`~/so101_runs/e0_j0/design.md` §0, 커밋 605bd0c~):
  - `twin_e0j0` 패키지의 `e0_j0_executor` = **`GoalExecutorNode`를 상속**합니다. 노드 이름, `/twin/goal` action, `/robot/joint_cmd` 단일 writer는 그대로입니다.
    - 부모 내부 메서드 16개를 그대로 씁니다: `_command_and_wait`, `_stage_criterion`, `_serve_recovery`, `_publish_cmd`, `_sample`, `_seeds`, `_await_ik` 등. 부모 파일은 고치지 않았습니다.
  - 정책 서버는 **호스트**(`~/so101_boxpick/e0_j0/policy_server.py`, so101-env, 설치 없음)에서 돕니다.
    - lerobot `RTCInferenceEngine`을 rollout과 같은 순서로 조립했습니다.
    - 컨테이너와는 docker0 `172.17.0.1:5555` 표준 라이브러리 TCP(JSON 머리 + raw RGB, pickle 없음)로 연결합니다.
  - 매 틱(30 Hz): joint_states·카메라 2대 → rad→lerobot 도 변환 → 정책 → 집게만 [0,100] 묶기 → 측정 기준 ±8 클립 → 명령 벽 사전 검사(밖이면 그 틱 안 보냄, 클램프 없음) → `/robot/joint_cmd`.

### 1-4. 단계별 결과

| 단계 | 내용 | 결과 | 근거 |
|---|---|---|---|
| A 구현 | 패키지·정책 서버·스크립트 | 박사님 패키지 시험 twin_backend 244 · bringup 23 · common 197 · executor 172, 실패 0(10-07, 우리 컨테이너). 지금 twin_e0j0 단위 시험 56 통과 · 1 건너뜀 **[측정]** | experiment_log "A. 구현", 커밋 605bd0c·f309469 |
| B sim + 가짜 정책 | 녹화된 행동을 재생하는 가짜 서버 | **탁자1·탁자2·박스 세 목표 DONE**(23.9 / 26.2 / 40.1 s). 되돌려 놓기(put-back) 확인. 박스 벽 여유 계획 50/50편 **[측정]** | `runs/trial_20261007_080628·080711·080757·081115.jsonl`, experiment_log "B단계" |
| C 그림자 모드(②) | 토크 off, 실제 π0.5, 명령 발행 0 | 관절 변환 0 tick, 추론 지연 rollout과 같거나 빠름, 벽 밖 0, 발행 0 → 합격. 카메라 17–25 Hz(DDS 원인, 고친 뒤 30.1 Hz). chunk 방향은 불합격이었으나 판정 기준 자체가 그림자 모드에 맞지 않음(3-2절) **[측정]** | `runs/shadow_20261008_*`, experiment_log "C단계 결과" |
| ③a 실물 잡고 들기 | 토크 on, 놓기 끔(`--hold-only`) | **6회 시도**: 정책이 큐브를 쥐고 3 cm 들어 넘겨주기까지 **5/5**(정책이 돈 시도 기준). 12 s 버티기·내려놓기까지 완주 **1/6**. 나머지는 놓침 오판 3, 실제 빠짐 추정 1, 링크 stale 1 **[측정]** | 아래 표, `runs/trial_20261008_0554~0643` |
| ③b 실물 놓기 | 놓기 켬 | **아직 완료로 보지 않습니다.** 기록상 탁자1 1회 DONE(15:53), 박스 1회는 박스 위까지 간 뒤 사람이 토크를 꺼 중단(15:55, 사유 미기록), 그 밖 2회 실패 **[측정]** | `runs/trial_20261008_063545·064420·065359·065459` |

**③a·③b 실물 시도** (2026-10-08 KST, 속도 천장 0.5 rad/s, P16)

| 시각 | 단계 | 출발 | 쥠 g / 넘겨주기 TCP z | 결과 | 원인 |
|---|---|---|---|---|---|
| 14:54 | ③a | 0.77 s | 30.3 / 29 mm | FAILED_GRASP @0.40 s | 놓침 **오판**(조임에 종이 큐브 눌림, 26.1 ≤ 26.3) → 큐브 쥔 채 4.2분 → 드라이버 LINK stale |
| 14:59 | ③a | — | — | FAILED_HW | 위 stale로 관측 없음 |
| 15:03 | ③a | 0.30 s | 32.1 / 26 mm | FAILED_GRASP @0.40 s | 놓침 오판(27.6 ≤ 28.1) |
| 15:34 | ③a | 0.30 s | 42.7 / 33 mm | FAILED_GRASP @0.10 s | 집게 42.7 → 25.9(−16.8). **[추정]** 실제로 빠졌거나 모서리 잡기 |
| 15:35 | ③b 탁자1 | 0.30 s | — | FAILED_GRASP | 정책이 40 s 안에 쥐지 못함(상태 search) |
| 15:39 | ③a | 0.30 s | 33.7 / 30 mm | **DONE** | 12 s 버티기 → 내려놓기·열기·물러나기 |
| 15:43 | ③a | 0.33 s | 33.4 / 26 mm | FAILED_GRASP @0.45 s | 놓침 오판(28.7 ≤ 29.4) → 65 s 뒤 LINK stale |
| 15:44 | ③b 탁자1 | — | — | FAILED_HW | 위 stale. 사용자가 `/twin/release` → 15 s 뒤 **LINK 재개** |
| 15:53 | ③b 탁자1 | 0.77 s | 33.0 / 25 mm | **DONE** | place 단계는 정밀 벽 미달(17.8 > 15 mm) → 접촉으로 처리 → 열기 → fold |
| 15:54 | ③b 박스 | 0.43 s | 32.1 / 26 mm | 결과 없음 | box standoff(박스 위) 도달 1.5 s 뒤 `/real/torque False` — 사람 개입 **[추정]** |

- 근거: `~/Ros2_e0j0/ros2_ws/e0j0_runs/trial_20261008_{055454,055917,060338,063424,063545,063959,064302,064420,065359,065459}.jsonl`, 기동 로그 `…/e0j0_runs/up_logs/up_20261008_{145351,150203,153227,153851,154158,155300}_real.log`.
- 15:39 ③a 버티기 12 s **[측정]**:
  - 처짐(서 있어야 할 자세 FK z − 측정 FK z)은 −3.2 mm로 일정했습니다(중력 보상이 명령을 12.8 mm 올렸으나 실제로는 3 mm만 올라감).
  - 집게 31.4 → 31.0으로 큐브를 유지했습니다.
  - **집게 Present_Load 21.6 %가 12 s 내내** 유지됐습니다(집게 Overload_Torque 25, Protection_Time 200 레지스터 대비 근접).

---

## 2. 박사님 환경과 다른 점 (arm-jetson 43d25ef 대비 e0j0/proto)

### 2-1. 코드 — 박사님 파일을 바꾼 곳

`git -C ~/Ros2_e0j0 diff --stat 43d25ef..e0j0/proto -- . ':!ros2_ws/src/twin_e0j0'` = 13 파일 +354/−10 **[측정]**. 모두 **우리 클론의 브랜치에서만** 바꿨고 `~/Ros2`는 그대로입니다(push 막음).

| 파일 | 무엇을 | 왜 | 원본 동작 영향 | main 후보? |
|---|---|---|---|---|
| `twin_bringup/launch/demo.launch.py` | `executor:=`(goal_executor_node \| e0_j0_executor), `physical_limits_file:=`, `e0j0_config:=`. `PROFILE_NODES` 대조를 고른 실행기로 | 실행기 교체·사이트 벽 | 인자 비우면 기존과 같음 | **예**(실행기 슬롯은 E1에도 필요) |
| `twin_backend/site_limits.py` (새) | 사이트 벽 파일 로더 `e0j0_physical_limits/1` (관절별 `[lo,hi]` 또는 `eeprom`) | Thor 팔 벽. `servo_map`이 yaml을 import하면 안 되는 경계 시험 때문에 별도 파일 | 새 파일 | **예**(requests_to_main 7번 방향) |
| `twin_backend/soarm_driver_node.py` (+16) | `physical_limits_file` 파라미터, 기동 시 벽 전체를 한 줄 로그 | 위와 같음 | 비우면 `PHYSICAL_LIMIT_RAD` 그대로 | **예** |
| `twin_backend/sim_arm_node.py` (+6) | 새 명령으로 선점하기 **전에** 진행 중 동작을 지금까지 적분 | 30 Hz 스트리밍에서 sim 팔이 한 번도 적분되지 않아 서 있었음 | 명령이 하나씩 오는 E0-lite 경로는 같음. twin_backend 244 통과(10-07) | **예**(스트리밍 실행기 전제) |
| `twin_bringup/config/fastdds_shm16mb.xml` (새) | Fast DDS 공유 메모리 구간 16 MB + UDPv4 | 카메라 프레임 손실(3-1절) | 우리 클론 컨테이너에만 적용 | **예**(검토 필요: 규칙 8 — RMW·QoS는 그대로) |
| `scripts/dev_container.sh` (14줄 변경) | `TWIN_VOL_PREFIX`(기본 `twin_e0j0`), `FASTDDS_DEFAULT_PROFILES_FILE`을 컨테이너 env로(`TWIN_FASTDDS_PROFILE=none`이면 끔), 기동 줄에 `dds=` | 빌드 볼륨 분리·DDS | 볼륨 기본값만 우리 클론에서 다름 | DDS 부분 **예**, 볼륨 접두어 **예**(무해) |
| `scripts/dev_up.sh` (+25) | `--executor`, env 전달 `TWIN_CONSTANTS_FILE`·`TWIN_E0J0_CONFIG`·`TWIN_PHYSICAL_LIMITS_FILE`·`TWIN_ARM_LIMITS_FILE`·`TWIN_SIM_SPEED_SCALE`, real_kinematic에서 `--registry` 허용 | 실험 설정 주입 | env 없으면 기존과 같음 | 일부(실행기·사이트 파일 전달) |
| `scripts/lib/dev_common.sh` (1줄) | 정리 대상 패턴에 `e0_j0_executor`·`e0_j0_shadow` | dev_down 정리 | 없음 | E1이 들어갈 때 |
| `.gitignore` | `ros2_ws/e0j0_runs/` | 시험 기록 | 없음 | 아니오 |
| `scripts/e0j0_{up,goal,stop,shadow}.sh` (새) | 실험용 래퍼 | — | — | 아니오 |

- **박사님 패키지 시험 재확인 필요**: 10-07(A단계) 이후 바꾼 `dev_container.sh`(DDS)·`dev_up.sh`(`TWIN_ARM_LIMITS_FILE`) 뒤로는 박사님 패키지 시험을 다시 돌리지 않았습니다 **[측정]**.

### 2-2. 실행 환경

- **무엇을 따로 두고 무엇을 같이 썼나** **[측정]**:

  | | 박사님 환경 | E0_J_0 | 같은가 |
  |---|---|---|---|
  | 도커 이미지 | `twin_ws:lyrical` (ID 560521b2b8a9, 10-01 생성) | **같은 이미지 그대로** — 새로 만들거나 고치지 않음 | 같음 |
  | 소스 | `~/Ros2` (arm-jetson 43d25ef) | `~/Ros2_e0j0` (브랜치 `e0j0/proto`, 43d25ef에서 분기, `pushurl DISABLED`) | 따로 |
  | 빌드 볼륨 | `twin_ws_{build,install,log}` | `twin_e0j0_{build,install,log}` (`dev_container.sh`의 `TWIN_VOL_PREFIX`) | 따로 |
  | 컨테이너 이름 | `twin_ws_dev` | `twin_ws_dev` (같은 이름) | 같음 → **동시에 띄울 수 없음** |

- **왜 이렇게 했나**:
  1. **코드를 바꿔야 했기 때문**: 실행기 교체 인자, 드라이버 벽 파라미터, sim 팔 적분 수정, 스크립트(2-1절)가 필요했습니다. `~/Ros2`에서 고치면 박사님 arm-jetson 작업 트리가 더러워집니다. 별도 클론·브랜치면 변경이 `git diff 43d25ef..e0j0/proto` 하나로 검토됩니다.
  2. **빌드 결과가 섞이지 않게**: `dev_up`은 colcon 빌드 없이 install 볼륨을 그대로 씁니다. 우리 코드를 `twin_ws_install`에 빌드하면, 박사님이 다음 세션에서 **모르는 채로 우리 코드를 실행**하게 됩니다. 그래서 볼륨 접두어만 바꿨습니다.
- **제약**: 컨테이너 이름이 같아 박사님 세션과 동시에 돌 수 없습니다. `e0j0_up.sh`는 /ws 마운트가 다른 컨테이너(= 박사님 세션)가 떠 있으면 아무것도 하지 않고 거부합니다. 팔·카메라도 한 번에 한쪽만 쓸 수 있으므로, 실물 시험은 박사님 세션이 없을 때만 했습니다.
- **DDS**: 위 SHM 16 MB 프로파일. 실제 카메라 30.08/30.13 Hz, stale 0(10-08 10:57) **[측정]**.
- **launch 인자**: `executor:=e0_j0_executor`, `e0j0_config:=…/e0j0.yaml`, `constants_file:=…/constants_e0j0.yaml`, `physical_limits_file:=…/physical_limits_thor_e0j0.yaml`, `arm_limits_file:=…/arm_limits_thor_e0j0.yaml`, `registry_file:=…/registry_e0j0.yaml` (`up_logs/*.log`의 `== demo.launch.py …` 줄).
- **실행기 상속**: `_execute`·`_on_urdf`·`_selfcheck_joint`(방향만)를 덮어쓰고 부모 내부 메서드 16개를 씁니다. **rebase 때 깨질 수 있습니다.**
- **단일 스레드 실행기 감싸기**: `SingleThreadedExecutor` + 막히는 일은 스레드로 돌리는 async 콜백(`_in_thread`, rclpy Future)을 씁니다. 계획 스레드는 자기 FK/IK 객체를 씁니다(FK가 스레드 안전하지 않음).
- **정책 서버**: 호스트 so101-env 프로세스(설치 없음), GPU 약 9.3 GB. 학습 중이면 띄우지 않는 검사가 있습니다.
- **기동 로그 보관**: `e0j0_up.sh`가 `/tmp/dev_demo.log`를 `ros2_ws/e0j0_runs/up_logs/`로 계속 복사합니다.

### 2-3. 실험 설정값

| 설정 | 원래 (arm-jetson) | 실험 | 이유 | 위험도 |
|---|---|---|---|---|
| 드라이버 명령 벽 | arm #1 하드스톱 표 ∩ EEPROM (wrist_flex 상한 89.7°) | pan = Thor 실측 하드스톱 [−1.278, 1.993] rad(arm #1 영점 좌표), lift·elbow·wrist_flex = Thor EEPROM 창 | practice_50 행동의 **61.8 %**가 wrist_flex 89.7° 밖 **[측정]** | 중 — EEPROM 창은 하드스톱 실측이 아님. 10-08 정책 단계에 wrist_flex 측정 1.5697 > 선언 1.5658 rad WARN 1회(드라이버는 측정을 자르지 않음) |
| 속도 천장 | 0.16 rad/s (0.2 × 0.8) | **0.5 rad/s** (1.0 × 0.5). 1.0은 사용자 지시 뒤 | 학습 관절 속도 p95 0.47–0.96 rad/s | 중 — 학습보다 느림(정책 목표에 팔이 뒤처짐) |
| 가속 천장 | 2.0 rad/s² | **5.0** | 학습 가속 p99 4.1–4.7 | 낮음 |
| 게인 P/I/D | 32/0/32 | **16/0/32** | 학습 조건(lerobot이 연결마다 씀) | 중 — 처짐·불감대 2배(3-2절). 토크 on 때 EEPROM 21–23에 다를 때만 씀 |
| q_tol (관절 잔차) | 0.04 rad (Jetson 완화 파일, P32 기준) | **0.06** (`arm_limits_thor_e0j0.yaml`) | P16 자기 점검에서 wrist_flex 0.043 rad로 보류 | 낮음 — 죽은 관절 감지(이동 ≥ 0.05 rad)는 따로 |
| 자기 점검·`/twin/home` 자세 | URDF 영점(ㄱ자) | **학습 시작 자세** `[70.9, 15.8, 34.1, 74.3, 6.8, 0.6]`(lerobot 도), 왕복은 TCP가 올라가는 쪽 | P16에서 ㄱ자 처짐 37.3 mm > 벽 22.5 mm **[측정]** | 낮음 — 실험 프로파일에서 `dev_home.sh`의 의미가 바뀜 |
| 큐브 | 35 mm | **53 mm**(registry size, attach 0.45, 파지 오프셋 등 main 2004ae5 값) | 실물 큐브 | 낮음 |
| 정책 집게 값 | — | **[0, 100]로 묶음**(집게만, 몸통은 안 묶음) | 정책이 −0.1~−0.3을 냄. 그림자 1645/1645 action이 < 0 **[측정]**. 드라이버는 벽 밖 값이 하나라도 있으면 메시지 전체 거부 | 낮음 — lerobot RANGE_0_100 규약과 같음 |
| 넘겨준 뒤 집게 | 완전 폐합(E0-lite gripper close) | **쥔 값 − 6** | 완전 폐합을 P16에서 오래 걸면 과부하 보호 우려 | **중** — 버티기 부하 21.6 % **[측정]**, 실패 뒤 계속 쥐면 stale 2회 **[추정: 과부하]** |
| 놓침 감지 | — | 쥔 값 − 4가 3틱 → abort (`--slip-log`면 기록만) | 큐브 빠짐 감지 | **중** — 종이 큐브 눌림으로 오판 3–4회 **[측정]** |
| 정책 단계 안전 | — | ±8 클립(측정 기준), TCP 바닥 z ≥ −0.025 m, 관측 1 s 끊기면 중단, 출발 감시 10 s/3° | lerobot 평가와 같은 8 | 낮음 |
| IK 단계 | 드라이버 천장 | 관절 보간 ≤ 0.3 rad/s, URDF 한계 | 안전 | 낮음 |
| 중력 보상 | — | 켬(명령 = 계획 + C·g, C 0.12 rad/N·m @P16) | ③b 완주용 | 중 — 모형 부정확(3-2절), 완주용 임시 |
| 박스 place 판정 | TCP 정밀 벽 | 큐브 중심이 안쪽(22.5 × 12 cm) − 큐브 반 − 5 mm 안, 놓을 높이 + 3 cm 아래로 정착 | 박스 안이 넓음 | 낮음 |
| 정지 | — | `/e0j0/stop`(다음 틱에 FAILED_HW, 팔은 그 자리) | ^C는 goal을 멈추지 않음 | 낮음 |

### 2-4. 동작 흐름 비교

| E0-lite 9단계 | E0_J_0 |
|---|---|
| (없음) | **START_POSE**: 학습 시작 자세로(경로 바닥·벽을 움직이기 전에 전부 검사) |
| APPROACH gripper open → pick standoff | **GRASP_POLICY**: π0.5 30 Hz 스트리밍(접근·열기·잡기·들기 전부 정책) |
| GRASP pick grasp → gripper close → `_is_held` | **넘겨주기 판정**(데이터로 정함): 열림 ≥ 35 → 최고값보다 5 닫힘 + 0.33 s 정지 + 12 ≤ g ≤ 55 → 쥠. 쥔 높이(최근 1 s 최저 TCP z)보다 **3 cm** 오르면 넘겨주기. 가상 세계 `attach_state`는 쓰지 않음(3-2절) |
| TRANSFER lift to pick standoff | **top-down 들기**: 넘겨줄 때 wrist_flex ≈ 95°라 현재 자세 수직 들기는 IK 여유가 없음 → 자세를 top-down으로 다시 풀어 들기(사전 수직 들기는 여유 안에서만). 탁자 TCP 0.07 m(→0.05), 박스는 0.10부터 내려가며 가장 높은 곳. 높이 표·박스 높이 미리 계산으로 **넘겨준 뒤 ≤ 3 s 안에 움직임**(sim 1.93 s, 실물 0.49–2.33 s) |
| TRANSFER place standoff | 박스: 큐브 바닥이 벽 + 1.5 cm 위인 경로(P2/P3/P1 순, 촘촘한 FK), 없으면 **집은 자리에 되돌려 놓고** FAILED_HW |
| PLACE place grasp | 놓기: 쥘 때 z + 1 cm(박스는 판정 완화), 접촉 허용 |
| PLACE gripper open → RETREAT | 같음 |
| (fold) | 같음(실물 `return fold`) |
| — | ③a(`place 끔`): 12 s 버티기(처짐·집게·Present_Load 기록) → 집은 자리에 내려놓기 |

---

## 3. 찾은 문제와 제한사항

### 3-1. 박사님 시스템에도 해당하는 것

1. **rclpy `MultiThreadedExecutor` 멈춤** (Lyrical, Python 3.14)
   - **[측정]** 우리 실행기가 MultiThreaded일 때 30 Hz 구독이 흐르면 프로세스 전체가 0.3–3 s씩 멈췄습니다. sim에서 1.09 s·1.53 s 무응답으로 goal이 실패했습니다(`runs/trial_20261007_073706·073841`). SingleThreaded + 스레드로 바꾼 뒤 사라졌습니다.
   - **[측정]** 박사님 `goal_executor_node.py`도 `MultiThreadedExecutor`를 씁니다(1765행).
   - **[추정]** 같은 멈춤이 박사님 실행기에도 있을 수 있습니다(직접 재현은 안 함).
2. **카메라 프레임 손실 (Fast DDS SHM 구간)**
   - **[측정]** 기본 SHM 구간 549,408 B < 이미지 921,600 B입니다. 카메라는 30 fps로 발행했지만, 구독은 그림자 노드 17–25 Hz, 아무 처리 없는 구독자도 15.9 Hz, 공백 최대 2.3 s였습니다.
   - **[측정]** 같은 컨테이너 재현에서 16 MB 프로파일로 30.0/30.1 Hz(공백 36 ms)가 됐습니다(`runs/C_diag_20261008/`).
3. **Thor 팔에 arm #1 값이 쓰임**
   - **[측정]** 명령 벽이 arm #1 하드스톱 표라 wrist_flex 89.7°에서 막힙니다(practice_50 행동 61.8 % 거부).
   - **[측정]** pan 영점은 1호 팔 값 +0.1381 rad입니다. Thor 실측 중앙(`measured.yaml` −0.2194)은 미반영입니다. **[추정]** 트윈 +x가 Thor 하드스톱 중앙과 약 20° 다릅니다.
4. **`dev_down` 때 컨테이너 로그가 사라짐**: **[측정]** 10-08 14:47 자기 점검 실패 로그가 dev_down과 함께 없어져 원인을 코드로 추론해야 했습니다(우리는 `up_logs`로 보관).
5. **Goal_Velocity(46) 잔류**: **[측정]** SRAM이라 `dev_down --real` 뒤에도 남고, 12 V 재투입 전에 lerobot을 쓰면 팔로워가 약 9°/s로 제한됩니다(2026-10-02 사례, `ros2_guide.md` §4). 우리는 `check_restored.py`로 재투입 뒤 46 = 0을 확인하는 절차를 둡니다.
6. **`--device` 생략 시 리더 포트를 잡음**: **[측정]** `/dev/serial/by-id` 첫 링크(알파벳 순 리더 5B79…)를 고릅니다(`ros2_guide.md` §1-2).
7. **서보 오류 비트 → 전체 관측 정지**
   - **[측정]** 드라이버는 서보 응답에 오류 비트가 있으면 그 서보 위치를 버리고, 3주기 연속 부족하면 `LINK` stale로 발행을 멈춥니다(`sts_bus.read_positions`).
   - **[측정]** 10-08 집게가 큐브를 계속 조이는 동안 2회 stale(4.2분 뒤, 65 s 뒤). 두 번째는 `/twin/release` 15 s 뒤 재개했습니다.
   - **[추정]** 원인은 집게 과부하 보호입니다(로그에 서보 번호 없음). 한 서보의 보호 상태가 관측 전체를 끊고 다음 goal·fold까지 막습니다.
8. **실패 뒤 마지막 명령 유지**: **[측정]** goal이 실패해도 드라이버·서보는 마지막 목표(집게 조임 포함)를 계속 잡습니다. 사람이 release하기 전까지 조임이 계속되어 7번으로 이어졌습니다.
9. **sim 팔 스트리밍**: **[측정]** 매 틱 명령이 오면 선점된 동작이 적분되지 않아 팔이 서 있었습니다(2-1절 수정).
10. **자기 점검 home = URDF 영점(ㄱ자)**
    - **[측정]** P16에서는 처짐 37.3 mm > 벽 22.5 mm로 READY가 안 납니다.
    - **[추정]** P32에서는 모형상 18.4 mm로, 완화 파일 주석의 실측 19.1 mm와 같은 수준이며 여유 약 4 mm입니다.

### 3-2. E1 설계에 걸리는 것

1. **가상 세계가 실제 큐브 위치를 모름**: **[측정]** 실물 모드의 world는 큐브가 registry 자리에 있다고 가정합니다. 정책이 다른 곳에서 잡으면 `attach_state`가 맞지 않습니다. E0_J_0은 집게·TCP 높이로 넘겨주기를 판정해 우회했습니다. E1에는 **인식(큐브 위치)**이 필요합니다.
2. **정책 집게 출력 범위**: **[측정]** π0.5가 집게를 0 아래(−0.1~−0.3)로 냅니다. lerobot은 [0,100]으로 자르지만, 트윈 드라이버는 메시지 전체를 버립니다. E1은 집게 규약을 정해야 합니다.
3. **속도·게인과 학습 조건의 차이**: **[측정]** 학습은 속도 제한 없음 + P16, 트윈 기본은 0.16 rad/s + P32입니다. 실험은 0.5 rad/s + P16으로 돌렸습니다. **[추정]** 속도 천장이 학습보다 낮아 정책 목표에 팔이 뒤처집니다(클립 108–121틱/시도).
4. **P16 위치 오차 (처짐·불감대)**
   - **[측정]** 위로 크게(home): 37 mm, 모형 36.7. 넘겨준 직후 측정 자세를 명령하면 −4~+1 mm(모형 +8~12). 시작 자세 근처 작은 이동: −7~+7 mm, 다가온 방향 따라 부호가 바뀜. 아래로(fold): 14 mm(`runs/D_diag_20261008_sag/hold_sag_check.py`).
   - **[추정]** 기어 마찰 불감대(관절당 최대 약 0.05–0.07 rad)가 크고 방향에 따라 달라, 중력 모형 하나로는 보정이 안 됩니다.
   - 영향: 자기 점검 실패(위), 놓기 정밀도(탁자 place 17.8 mm > 정밀 벽 15 mm **[측정]**), 박스 벽 여유(계획 최저 6.9 cm, 벽 5 cm; 이동 중 오차 미측정).
5. **넘겨받는 자세의 IK 여유**: **[측정]** 3 cm 들렸을 때 wrist_flex 중앙값이 95°입니다. URDF ±95°와 이송 여유 0.1 rad 때문에 E0-lite의 "현재 자세 그대로 수직 들기"는 대부분 불가였고, top-down 재해석으로 50/50편 해결했습니다(`runs/` lift_compare·box_plan).
6. **그림자 모드로 못 보는 판정**: **[측정]** 토크 off에서는 정책이 출발하지 않았습니다(60 s). 같은 날 lerobot rollout은 정상 출발했습니다(**[사용자 관찰]**). **[추정]** 손목 카메라가 팔과 함께 움직이는 되먹임이 없어서입니다. chunk 방향 같은 "정책 출발" 판정은 그림자 모드 기준으로 쓸 수 없습니다.
7. **넘겨준 뒤 집게 규칙**: **[측정]** 종이 큐브는 조임(−6)에 0.4 s 사이 4.2–4.5 단위 눌려 놓침(−4)을 오판시켰습니다. 버티기 부하는 21.6 %입니다. 조임·놓침 규칙은 큐브 재질과 함께 정해야 합니다.
8. **실패 처리**: 큐브를 든 채 실패하면 사람이 `/twin/release`해야 합니다. 늦으면 3-1절 7번(stale)으로 이어집니다.

### 3-3. 아직 확인 못 한 것

- ③b **박스 완주**(박스 위까지 1회, 그 뒤 사람 개입으로 중단). 탁자 완주는 1회뿐입니다.
- 여러 큐브 위치에서의 반복 성공률(지금은 모두 기본 자리 근처).
- 속도 천장 1.0 rad/s.
- 중력 보상의 실제 효과. 모형이 버티기·작은 이동에서 맞지 않음은 확인했습니다. 측정 기반 보정(정착 뒤 오차만큼 다시 명령)은 설계만 했습니다.
- 이동 중(이송) 높이 오차 → 박스 벽 여유.
- 탁자 놓기 품질(1 cm 위에서 떨어뜨림 vs 누름; 접촉 감지 방식은 검토만).
- 과부하 보호가 실제 원인인지(서보 번호), 집게 부하 21.6 %의 여유.
- 각 실물 세션 뒤 Goal_Velocity 복구(`check_restored.py`) 결과 — 10-08 오후 세션 덤프는 기록에 없습니다.
- A단계 이후 바꾼 스크립트 기준 박사님 패키지 시험 재실행.

---

## 4. 박사님께 결정·확인을 부탁드릴 것 (design.md §4-5 갱신)

1. **실행기 상속 방식**: `GoalExecutorNode` 상속으로 정책 슬롯을 두는 구조(writer 1개 유지)를 E1의 출발점으로 받아도 되는지. 내부 메서드 16개 의존을 rebase 때 어떻게 다룰지(공개 API로 올릴지).
2. **Thor 명령 벽**: lift·elbow·wrist_flex를 EEPROM 창으로 쓰는 것(실물 ③a·③b 내내 사용), `physical_limits_file`+`site_limits.py` 방식을 main에 올릴지. pan 영점(−0.2194) 반영 시점(박스·탁자 좌표 재계산 필요).
3. **속도·가속·게인**: 정책 단계 0.5 rad/s → 1.0으로 올려도 되는지. P16(학습 조건) vs P32(트윈 기본). 실험 프로파일 전용 q_tol 0.06·자기 점검 자세(`TWIN_ARM_LIMITS_FILE`, 실험 실행기의 home)를 받아들이실지. EEPROM 21–23 반복 쓰기(lerobot↔트윈 전환마다 1회).
4. **DDS 프로파일**: `fastdds_shm16mb.xml`을 main 컨테이너에 넣을지(규칙 8: RMW·QoS는 그대로, 전송 구간만).
5. **MultiThreadedExecutor**: 박사님 실행기에서 같은 멈춤이 있는지 확인, SingleThreaded + 스레드로 바꿀지.
6. **드라이버의 서보 오류 처리**: 한 서보의 오류 비트(과부하 보호 등)로 관측 전체를 끊는 대신 서보 번호·오류 비트를 로그에 남기고 나머지는 발행할지. 실패 뒤 집게 조임을 자동으로 풀지(시간 제한).
7. **운영 절차**: `dev_down`에서 로그 보관, `dev_down --real`에서 Goal_Velocity 되돌리기(또는 12 V 재투입을 문서화), `--device` 기본값을 팔로워 by-id로.
8. **기준 브랜치**: arm-jetson(10-01)을 계속 쓸지, main(53 mm registry, 집게 가드, cv2 카메라 노드, 이송 중 조임 유지)으로 rebase할지.
9. **E1 인식**: 실물에서 큐브 위치를 world에 넣는 방법(머리 카메라 + Thor 캘리브레이션).
10. **정책 서버 연결**: docker0 TCP 포트(172.17.0.1:5555)를 계속 써도 되는지(Unix 소켓 대안).
11. **박사님 동석이 필요한 단계**: ③b 박스 완주, 속도 1.0 시험.

---

## 5. 넘겨드릴 자료

같은 Thor이므로 **경로로 드리면 됩니다**. 다만 두 가지는 지금 형태로는 넘기기 불편합니다(아래 "묶을 것").

| 자료 | 경로 | 크기 | 주요 파일 sha256 |
|---|---|---|---|
| 데이터셋 (lerobot v3.0, 50편, 30,884 프레임) | `~/so101_runs/practice/practice_50/dataset/` | 274 MB | `meta/info.json` 69adab0f9939992fea8d3fb37924566e74d383bc60e868ed848dc037f78180e0 · `meta/stats.json` f9b44ffeafda50f2fe0dd70607705f0fae583f63ad2ceea0ce7ea6887f95e303 · `data/chunk-000/file-000.parquet` 138606d58f422cbecebc600e8b195dc8b06974184f95f6234c71ffdb23b745f3 · `file-001` 5b2ad8a0a0e4b4c154bc7baf9d03224a387e416820f1a6f643e790d27c74d6a5 · `file-002` ffe63c6512741ddf4dfaf8343f53dbc596ac9ce7e3c786416116047cb25396e7 |
| 셋업 사진·QA | `…/practice_50/setup_photos/`, `qa/`, `qa_report.md`, `review_videos/` | — | — |
| 학습 체크포인트 015000 (추론용) | `…/practice_50/train/pi05_15k/checkpoints/015000/pretrained_model/` | 8.8 GB | `model.safetensors` 702eef6f69835e881706966de8febfffab6b42695494b3b55d7066f19a87eb81 · `config.json` d78da10af0f9b4c2ed2498222959d6e798c6581c2973b03804d34cc495a90d78 · `train_config.json` dfe8d128cc1ef5993543be019d605174b5c2f3250fa386e4c51ad31861f26716 · 전처리 normalizer fcf23a8b212b0a534916413ecb09c82f3206dfb16bae958377aee8de69323cfb · 후처리 unnormalizer 63f83cb368dc167815b2cd7017982fa7f0e19b104b1f5b586da0b9b643988df8 |
| 체크포인트 전체 (005000·010000·015000, optimizer 포함) | `…/train/pi05_15k/checkpoints/` | 디렉터리별 8.8 + 15 GB × 3 (du 합계 46 GB) | — |
| 학습 로그·명령 | `…/train/pi05_15k.log`, `run_pi05_15k.sh`, `pi05_15k.time` | — | — |
| lerobot rollout 10-07 (3회) | `…/practice_50/eval/rollouts/` | 27 MB | 103612·104105·104451 순 — analysis.json 98fa79590fb8c5a61e68ad17a3e794521386876703b2ec8f8e1df6cc7bbb49f1 / ea1c15451ddeffe126af562dc320c239432f384f904c458232264ee3a109c85b / 51ca7cc56153321b9b96d163de243cff2b7498ae5507bf27c9c66208a77e6720 · dataset parquet b6aaba5032fea6c74b83d1b8e66b3355c1550c1c3c93329c025d130d21381a69 / 36272bb669fe89e4cb1024bb481aacd85e4c7b0e1ae4710f27a84997df160ffb / 480f0482f8e0b42a5ca08d5fb88d4b61da76aed50062ddd19583914747f7ce9f |
| lerobot rollout 10-08 (4회, 녹화 없음) | `…/eval/rollout_today_20261008_102000.log` | 12 KB | 47873110bfc83dd117f61e5d03306f5cc7be339636fe9055b0fff9df25b8a816 |
| E0_J_0 문서 | `~/so101_runs/e0_j0/{design.md, experiment_log.md, C_shadow_checklist.md, D_real_checklist.md, report_for_dr_lee.md}` | 12 MB(폴더 전체) | design.md aeb089ef5a9b9f5614abce8d953d2b46e0629108d924632153c0f58a4ca424d2 · experiment_log.md 60f8328752d0290c5416031751e78aa4140e04023364f16728440404e39dc020 |
| E0_J_0 시험 기록 | `~/so101_runs/e0_j0/runs/`(trial jsonl 사본·shadow·진단 스크립트·`index.md`·`notes.md`) | (위 12 MB 안) | notes.md c868bff9851a515fe44a8a4e0b61845e0b7092a8581cebfd3af68d5fb2182261 |
| 기동 로그 (자기 점검 표 포함) | `~/Ros2_e0j0/ros2_ws/e0j0_runs/up_logs/` (**runs/로 모으지 않음**) | e0j0_runs 전체 14 MB | — |
| 트윈 코드 | `~/Ros2_e0j0` 브랜치 `e0j0/proto` (10 커밋, 아래) | — | 커밋 해시가 곧 식별자 |
| 정책 서버·도구 | `~/so101_boxpick/e0_j0/` (policy_server.py, protocol.py, server_base.py, fake_policy_server.py, collect_runs.py, check_restored.py 등) | 72 KB | policy_server.py d4eb721a17c8dce334158a3db5f491d33eeafff63086bf739c125e284cab04f9 · protocol.py f98dc18a1bb36ecc60cdb1a1e8d26407a83a5147697233c8990a5451c8f39afa · server_base.py 976aa3e7a7083165cafbaae922effa531d2c3951a3d000061410731af9c6fa5c |

**커밋 목록** (`git -C ~/Ros2_e0j0 log 43d25ef..e0j0/proto`):

| 커밋 | 시각 (KST) | 내용 |
|---|---|---|
| 605bd0c | 10-07 15:33 | E0_J_0 시제품 (A) |
| 55ec756 | 10-07 16:05 | 들기 방식 오프라인 비교 반영 (top-down) |
| 4ae0f6b | 10-07 16:30 | 박스 벽 여유 경로·되돌려 놓기·조임 −6·놓침 −4 |
| 6be2726 | 10-07 17:12 | B sim: SingleThreaded+스레드·sim 팔 적분 |
| 4104380 | 10-07 20:44 | C 준비: 계획 ≤3 s·③a 기록·집게 묶기·그림자 노드 |
| cc8627d | 10-08 10:51 | D 준비: DDS 16 MB·시작 자세·출발 감시·③a 내려놓기 |
| f5cec74 | 10-08 14:45 | 자기 점검·home = 학습 시작 자세·중력 보상·박스 판정·로그 보관 |
| 700097f | 10-08 14:52 | 실험 프로파일 q_tol 0.06 |
| 3341e43 | 10-08 15:12 | 놓침 abort/log·`--cube`·기록 필드 |
| f309469 | 10-08 15:21 | ③b 완주용 중력 보상 켬 |

**묶을 것 (의견)**
- **트윈 코드**: 클론은 push가 막혀 있어 박사님 저장소에서 볼 수 없습니다. 같은 기계라 `~/Ros2_e0j0`를 직접 보셔도 되지만, 검토용으로 `git format-patch 43d25ef..e0j0/proto` 또는 `git bundle` 한 개로 드리는 편이 깔끔합니다(사용자 승인 뒤 만들겠습니다).
- **`~/so101_boxpick/e0_j0/`**: `~/so101_boxpick` 저장소에서 **추적되지 않는(untracked)** 폴더입니다(`servo_dumps`, `record_ui.py`, `check_dataset.py`도 마찬가지). 커밋하거나 tar로 묶어야 버전이 고정됩니다.
- **기동 로그**: `up_logs/`는 `collect_runs.py`가 옮기지 않으므로 경로를 따로 알려 드리거나 함께 묶습니다.
- **데이터셋·체크포인트**: 같은 기계라 경로로 충분합니다. 추론만 보시면 `015000/pretrained_model`(8.8 GB)만, 이어서 학습하시면 `015000/training_state`(15 GB)까지 필요합니다. 복사보다 위 sha256으로 같은 파일인지 확인하시는 것을 권합니다.
