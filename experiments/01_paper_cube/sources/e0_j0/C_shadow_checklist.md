# C단계 (②) 그림자 모드 체크리스트 — 실물 읽기 전용, 명령 발행 0

- **목적**: 팔에 명령을 하나도 보내지 않는 상태에서 다섯 가지를 확인합니다.
  - 트윈 ↔ lerobot 관절 변환
  - 카메라 두 대
  - 실제 π0.5 정책 서버의 추론 지연
  - 정책이 큐브 쪽으로 가려는지
  - 명령 상한(벽) 밖 비율
- **안전**: 팔은 토크 off 그대로입니다(`--real-ro` = arm_only).
  - 드라이버는 `/robot/joint_cmd`를 구독조차 하지 않습니다.
  - 그림자 노드는 시작할 때 자기 발행자를 세어, `/rosout`·`/parameter_events` 말고 하나라도 있으면 기동을 거부합니다.
- 명령은 모두 **Thor 데스크톱 터미널에서 직접** 입력합니다. 터미널은 세 개(T1·T2·T3)를 씁니다.
- 결과는 `~/so101_runs/e0_j0/runs/`(`index.md`의 "그림자 모드" 표, `shadow_<시각>/` 폴더)에 남습니다.

## 0. 시작 전 확인 (T3)

| 확인 | 명령 | 기대 |
|---|---|---|
| 학습이 안 돎 | `pgrep -a -f "lerobot-trai[n]"` | 아무것도 안 나옴 |
| lerobot·다른 서버가 안 돎 | `pgrep -a -f "lerobot-recor[d]\|lerobot-rollou[t]\|lerobot-teleoperat[e]\|record_u[i]\|policy_serve[r]\|fake_polic[y]"` | 아무것도 안 나옴 |
| GPU가 비어 있음 | `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` | 머리줄만 |
| 컨테이너 없음 | `docker ps --format '{{.Names}}'` | 아무것도 안 나옴 (박사님 컨테이너가 있으면 **멈춤**) |
| 팔로워 장치 | `ls -l /dev/serial/by-id/` | `…5B8E116810-if00 -> ../../ttyACM?` |
| 카메라 자동 3/1/0 | `for d in /dev/cam_front /dev/cam_wrist; do v4l2-ctl -d $d -C auto_exposure,white_balance_automatic,exposure_dynamic_framerate; done` | 둘 다 `auto_exposure: 3`, `white_balance_automatic: 1`, `exposure_dynamic_framerate: 0` (2026-10-07 20:4x 조회 때 이미 이 값) |
| (자동이 아니면) | `for d in /dev/cam_front /dev/cam_wrist; do v4l2-ctl -d $d -c auto_exposure=3 -c white_balance_automatic=1 -c exposure_dynamic_framerate=0; done` | 다시 위 조회 |
| 팔 토크 off | 팔을 손으로 살짝 밀어 봅니다. 움직이면 off. 아래 1번 덤프의 Torque_Enable이 6개 모두 0 | 6/6 off |
| 장면 | `~/so101_runs/practice/practice_50/setup_photos/ep000_front_first.png`와 같게: 흰 탁자, 갈색 박스 왼쪽, 빨간 큐브(53 mm) 오른쪽 앞 | 사진과 비교 |
| 팔 자세 | 학습 시작 자세처럼 접힌 휴식 자세 (토크 off라 손으로 놓음) | — |

## 1. 관절 변환 대조용 덤프 — 트윈을 띄우기 **전에** (T3, 버스가 비어 있어야 함)

```bash
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/scripts/servo_dump.py --arm follower
#   → "저장: …/docs/servo_dumps/<시각>_follower.json" 경로를 적어 둔다.  여기서부터 팔에 손대지 않는다.
```

## 2. 정책 서버 기동 (T1) — 처음 실물 세션에서 GPU에 모델을 올림

```bash
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/e0_j0/policy_server.py
```

- 기대 출력:
  - `[policy] loaded in ~166 s: pi05_15k@015000 steps=5 rtc(h=20,q=40)  cuda mem ~9.4 GB`
  - 그다음 `[policy] listening 172.17.0.1:5555 …`
- `REFUSED: 학습이 돌고 있다`가 나오면 학습이 끝난 뒤에 합니다.
- 실행 중에는 `RTC inference latency=…` DEBUG 줄이 초당 약 3개씩 흐릅니다(지연을 눈으로 보려고 일부러 둠).
- (참고) 2026-10-07 오프라인 시험(팔 없음, 학습 첫 프레임 사진 입력): 로딩 166 s, 9.36 GB. 추론 첫 680 ms, 이후 평균 280 ms, 최대 310 ms.

## 3. 트윈 읽기 전용 + 카메라 기동 (T2)

```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_up.sh real-ro
```

- 기대 출력:
  - `== 실물 사전 점검 …` → `리더: 없음`
  - `cameras.launch.py (손목 /dev/video2 · 머리 /dev/video0 …)`
  - 헬스체크 `1/6 실물 링크·토크: torque disabled: 6/6 (verified)` … `6/6 읽기 전용 계약 … joint_cmd subscriptions=0 read_only=True`
  - 마지막 줄 `E2 ready … [real  /dev/ttyACM0, torque off]`
- 실패하면 4번으로 가지 말고 6번 정리로 갑니다.

## 4. 확인 (T3)

### 4-1. probe — 관절 변환·카메라 (정책 안 씀, 20 s)
```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_shadow.sh probe 20
#   마지막에 summary JSON 이 찍히고 "dir": "/ws/e0j0_runs/shadow_<시각>" — 호스트 폴더는 ~/Ros2_e0j0/ros2_ws/e0j0_runs/shadow_<시각>
D=$(ls -td ~/Ros2_e0j0/ros2_ws/e0j0_runs/shadow_* | head -1); echo $D
/usr/bin/python3 ~/so101_boxpick/e0_j0/compare_joint_dump.py <1번 덤프 경로> $D
PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python ~/so101_boxpick/e0_j0/compare_camera.py $D
```

### 4-2. shadow — 실제 정책 (60 s)
```bash
cd ~/Ros2_e0j0 && bash scripts/e0j0_shadow.sh shadow 60            # 큐브 xy 를 알면 끝에: 0.19 -0.04
#   실행 중 다른 터미널(T2 에서 해도 됨):  bash scripts/dev_ros.sh topic info /robot/joint_cmd
#   → "Unknown topic" 또는 Publisher count: 0
```

### 합격 기준

| 항목 | 어디서 보나 | 합격 기준 |
|---|---|---|
| 관절 변환 | `compare_joint_dump.py` 마지막 줄 | 6관절 모두 **\|Δ\| ≤ 1 tick** |
| 카메라 주기 | probe summary `camera_hz` | front·wrist 모두 **≥ 28 Hz** (`joint_states_hz` ≈ 30) |
| 카메라 색·밝기 | `compare_camera.py` (그림 `camera_compare.jpg`도 눈으로) | 탁자 ROI **밝기 차 ≤ 15 %, 색 치우침 차 ≤ 5 %p** (조명이 학습 때와 다르면 기록하고 판단) |
| 추론 지연 | shadow summary `infer_ms`, T1 서버가 끝날 때 찍는 `RTC 추론 지연 (이번 세션)` | lerobot rollout(2026-10-07 practice_50 rtc_fast 3회: 첫 700–740, 평균 316–317, p95 330–340, 최대 370–380 ms)과 비교해 **평균 ≤ 350 ms, 최대 ≤ 450 ms** |
| 정책 왕복 | shadow summary `rtt_ms` | p95 ≤ 10 ms (이미지 2장 포함, 오프라인 p50 1.8 ms) |
| chunk 방향 | shadow summary `chunk_direction` | `pass_suggested: true` — 처음 300 action(10 s) 안에서 가장 멀리 간 TCP가 시작점에서 **수평 ≥ 2 cm**, 큐브 방향과 **각도 ≤ 45°**. 함께 볼 것: `min_tcp_z_in_window`(내려가는가), `gripper_max_in_window`(집게를 여는가 — 학습에서는 40–60) |
| 벽 밖 비율 | shadow summary `wall_out_ratio`, `counts.wall_out` | **0** (`gripper_bounded`는 집게만 [0,100]으로 묶은 횟수 — 0이 아니어도 됨, 아래 주의) |
| 바닥 밖 | `floor_out_ratio` | 0 |
| 명령 발행 0 | summary `publishers_besides_rosout_parameter_events` = `[]` + 위 `topic info` | 발행자 0 |

- 주의 — **집게 묶기**:
  - 정책은 집게를 −0.1~−0.3처럼 [0, 100] 밖으로 살짝 냅니다(오프라인 시험).
  - lerobot은 이 값을 원래 [0, 100]으로 자릅니다(RANGE_0_100 규약). 트윈 드라이버는 그런 값을 벽 밖으로 보고 **메시지 전체**를 버립니다.
  - 그래서 집게만 lerobot과 같이 묶습니다(`grasp.gripper_bound_like_lerobot: true`). 몸통 관절은 묶지 않습니다.
  - 묶기 전 값의 벽 밖 횟수는 `counts.wall_out_unbounded`에 따로 남습니다.

## 5. 끝낼 때 정리 순서

1. shadow가 끝났는지 확인합니다(60 s 뒤 summary가 찍힘). 중간에 끊으려면 T3에서 Ctrl-C.
2. **T1 정책 서버를 Ctrl-C로 끕니다** → `[policy] RTC 추론 지연 (이번 세션): {…}`, `[policy] stop`. GPU 확인: `nvidia-smi --query-compute-apps=pid,used_memory --format=csv` → 머리줄만.
3. T2: `cd ~/Ros2_e0j0 && bash scripts/dev_down.sh`
   - 읽기 전용이라 `--real`이 필요 없습니다. 토크는 켜진 적이 없고 서보 레지스터 쓰기도 0입니다.
   - 기대: `OK: processes=0 zombies=0 container=removed`
4. `docker ps --format '{{.Names}}'` → 아무것도 안 나와야 합니다.
5. (선택) 팔을 건드리지 않았다면 덤프를 한 번 더 해서 1번과 같은지 봅니다(관절 변환 대조의 전제).
6. 기록 모으기: `/usr/bin/python3 ~/so101_boxpick/e0_j0/collect_runs.py` → `runs/index.md`의 "그림자 모드" 표.
7. 12 V 재투입은 **필요 없습니다**. 읽기 전용이라 Goal_Velocity 등을 쓰지 않았습니다. 카메라 설정도 그대로(자동)입니다.

## 6. 문제가 생기면

| 증상 | 할 것 |
|---|---|
| `e0j0_up.sh`: `REFUSED: 다른 컨테이너가 떠 있다` | 박사님 세션일 수 있으니 건드리지 말고 멈춤 |
| 헬스체크 `1/6`에서 `TORQUE_ON` (rc 6) | 토크가 켜져 있습니다(lerobot이 남김). 팔을 받치고 `bash scripts/dev_down.sh` → 12 V 끄고 켬 → 0번부터 |
| `REASON:PORT_BUSY` | lerobot 등이 버스를 쥐고 있습니다. 0번의 pgrep으로 찾아 끄기 |
| rc 7 / `FAIL at stage 1/6` | 캘리브레이션 불일치. 팔로워가 맞는지(`by-id 5B8E116810`) 확인 |
| shadow: `정책 서버 … 연결 실패` | T1 서버가 `listening 172.17.0.1:5555`까지 왔는지 |
| `camera_hz`가 0 | `e0j0_up.sh real-ro` 출력에 `cameras.launch.py` 줄이 있는지, `bash scripts/dev_cams.sh` |
