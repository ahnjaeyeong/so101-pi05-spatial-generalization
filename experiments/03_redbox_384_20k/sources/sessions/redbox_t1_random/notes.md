# redbox_t1_random (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t1_random`
- dataset: `$HOME/so101_runs/main/redbox_t1_random/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 11:11 · 새 녹화 <!-- run:20261014_111126 -->

> ⚠ **중단 — 저장 0편.** 리더 팔 연결 직후 진행되지 않아 터미널을 닫음 (사용자). 빈 dataset 은 지웠고 실행 기록은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-14).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1R01: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/deleted_runs/record_20261014_111126.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 0=T1R01, 1=T1R02, 2=T1R03, 3=T1R04, 4=T1R05, 5=T1R06, 6=T1R07, 7=T1R08, 8=T1R09, 9=T1R10, 10=T1R11, 11=T1R12, 12=T1R13, 13=T1R14, 14=T1R15, 15=T1R16

### 2026-10-14 11:15 · 새 녹화 <!-- run:20261014_111558 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1R01: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_111558.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 0=T1R01, 1=T1R02, 2=T1R03, 3=T1R04, 4=T1R05, 5=T1R06, 6=T1R07, 7=T1R08, 8=T1R09, 9=T1R10, 10=T1R11, 11=T1R12, 12=T1R13, 13=T1R14, 14=T1R15, 15=T1R16

**결과** <!-- results:20261014_111558 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 11:27
- repo_id: `oxr/so101_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 447 | 14.9 | 29.90 | 0/446 | T1R01 |
| 001 | 509 | 17.0 | 29.89 | 0/508 | T1R02 |
| 002 | 420 | 14.0 | 29.86 | 0/419 | T1R03 |
| 003 | 439 | 14.6 | 29.88 | 0/438 | T1R04 |
| 004 | 431 | 14.4 | 29.88 | 0/430 | T1R05 |
| 005 | 454 | 15.1 | 29.88 | 0/453 | T1R06 |
| 006 | 429 | 14.3 | 29.88 | 0/428 | T1R07 |
| 007 | 462 | 15.4 | 29.90 | 0/461 | T1R08 |
| 008 | 425 | 14.2 | 29.91 | 0/424 | T1R09 |
| 009 | 454 | 15.1 | 29.89 | 0/453 | T1R10 |
| 010 | 481 | 16.0 | 29.90 | 0/480 | T1R11 |
| 011 | 463 | 15.4 | 29.91 | 0/462 | T1R12 |
| 012 | 450 | 15.0 | 29.89 | 0/449 | T1R13 |
| 013 | 421 | 14.0 | 29.90 | 0/420 | T1R14 |
| 014 | 424 | 14.1 | 29.90 | 0/423 | T1R15 |
| 015 | 420 | 14.0 | 29.82 | 0/419 | T1R16 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 8545 ticks, 8526 judged
  effective cadence: 29.89 Hz over 285.3 s measured
  ticks over the 33.3 ms work budget: 0/8526 (0.0%) — work mean 3.1 ms, worst 27.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 248
  loop-body steps (share of measured work):
    observe      mean   1.37 ms · worst  22.76 ms ·  45.0% of work · 8545 calls
    process_obs  mean   0.05 ms · worst   1.33 ms ·   1.5% of work · 8545 calls
    teleop       mean   1.14 ms · worst  21.90 ms ·  37.3% of work · 8545 calls
    send         mean   0.24 ms · worst   3.22 ms ·   7.8% of work · 8545 calls
    record       mean   0.20 ms · worst   2.39 ms ·   6.7% of work · 8545 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
| 004 | | |
| 005 | | |
| 006 | | |
| 007 | | |
| 008 | | |
| 009 | | |
| 010 | | |
| 011 | | |
| 012 | | |
| 013 | | |
| 014 | | |
| 015 | | |

### 2026-10-14 13:34 · 이어 찍기 <!-- run:20261014_133441 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T1R17: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_133441.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 16=T1R17, 17=T1R18, 18=T1R19, 19=T1R20, 20=T1R21, 21=T1R22, 22=T1R23, 23=T1R24, 24=T1R25, 25=T1R26, 26=T1R27, 27=T1R28, 28=T1R29, 29=T1R30, 30=T1R31, 31=T1R32

**결과** <!-- results:20261014_133441 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 13:47
- repo_id: `oxr/so101_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 493 | 16.4 | 29.90 | 0/492 | T1R17 |
| 017 | 403 | 13.4 | 29.90 | 0/402 | T1R18 |
| 018 | 436 | 14.5 | 29.90 | 0/435 | T1R19 |
| 019 | 443 | 14.8 | 29.90 | 0/442 | T1R20 |
| 020 | 496 | 16.5 | 29.91 | 0/495 | T1R21 |
| 021 | 374 | 12.5 | 29.90 | 0/373 | T1R22 |
| 022 | 372 | 12.4 | 29.90 | 0/371 | T1R23 |
| 023 | 382 | 12.7 | 29.90 | 0/381 | T1R24 |
| 024 | 501 | 16.7 | 29.90 | 0/500 | T1R25 |
| 025 | 346 | 11.5 | 29.89 | 0/345 | T1R26 |
| 026 | 409 | 13.6 | 29.90 | 0/408 | T1R27 |
| 027 | 425 | 14.2 | 29.88 | 0/424 | T1R28 |
| 028 | 391 | 13.0 | 29.88 | 0/390 | T1R29 |
| 029 | 414 | 13.8 | 29.89 | 0/413 | T1R30 |
| 030 | 437 | 14.6 | 29.90 | 0/436 | T1R31 |
| 031 | 476 | 15.9 | 29.90 | 0/475 | T1R32 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 8024 ticks, 8005 judged
  effective cadence: 29.90 Hz over 267.8 s measured
  ticks over the 33.3 ms work budget: 0/8005 (0.0%) — work mean 3.0 ms, worst 14.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 181
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst  11.87 ms ·  44.7% of work · 8024 calls
    process_obs  mean   0.05 ms · worst   0.97 ms ·   1.5% of work · 8024 calls
    teleop       mean   1.13 ms · worst   5.18 ms ·  37.2% of work · 8024 calls
    send         mean   0.24 ms · worst   4.44 ms ·   7.9% of work · 8024 calls
    record       mean   0.21 ms · worst   2.36 ms ·   6.8% of work · 8024 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 016 | | |
| 017 | | |
| 018 | | |
| 019 | | |
| 020 | | |
| 021 | | |
| 022 | | |
| 023 | | |
| 024 | | |
| 025 | | |
| 026 | | |
| 027 | | |
| 028 | | |
| 029 | | |
| 030 | | |
| 031 | | |

### 2026-10-14 14:28 · 이어 찍기 <!-- run:20261014_142821 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T1R33: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_142821.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 32=T1R33, 33=T1R34, 34=T1R35, 35=T1R36, 36=T1R37, 37=T1R38, 38=T1R39, 39=T1R40, 40=T1R41, 41=T1R42, 42=T1R43, 43=T1R44, 44=T1R45, 45=T1R46, 46=T1R47, 47=T1R48

**결과** <!-- results:20261014_142821 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 14:41
- repo_id: `oxr/so101_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 390 | 13.0 | 29.90 | 0/389 | T1R33 |
| 033 | 461 | 15.4 | 29.91 | 0/460 | T1R34 |
| 034 | 427 | 14.2 | 29.90 | 0/426 | T1R35 |
| 035 | 460 | 15.3 | 29.90 | 0/459 | T1R36 |
| 036 | 465 | 15.5 | 29.90 | 0/464 | T1R37 |
| 037 | 400 | 13.3 | 29.90 | 0/399 | T1R38 |
| 038 | 451 | 15.0 | 29.90 | 0/450 | T1R39 |
| 039 | 425 | 14.2 | 29.90 | 0/424 | T1R40 |
| 040 | 500 | 16.7 | 29.88 | 0/499 | T1R41 |
| 041 | 416 | 13.9 | 29.89 | 0/415 | T1R42 |
| 042 | 377 | 12.6 | 29.88 | 0/376 | T1R43 |
| 043 | 437 | 14.6 | 29.91 | 0/436 | T1R44 |
| 044 | 429 | 14.3 | 29.90 | 0/428 | T1R45 |
| 045 | 520 | 17.3 | 29.90 | 0/519 | T1R46 |
| 046 | 511 | 17.0 | 29.89 | 0/510 | T1R47 |
| 047 | 471 | 15.7 | 29.90 | 0/470 | T1R48 |

```
Cadence summary — whole run, 16 episodes · target 30 Hz (33.3 ms budget per tick): 7140 ticks, 7124 judged
  effective cadence: 29.90 Hz over 238.3 s measured
  ticks over the 33.3 ms work budget: 0/7124 (0.0%) — work mean 3.0 ms, worst 13.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 159
  loop-body steps (share of measured work):
    observe      mean   1.33 ms · worst  11.20 ms ·  44.7% of work · 7140 calls
    process_obs  mean   0.04 ms · worst   0.43 ms ·   1.5% of work · 7140 calls
    teleop       mean   1.12 ms · worst   4.29 ms ·  37.5% of work · 7140 calls
    send         mean   0.23 ms · worst   5.48 ms ·   7.8% of work · 7140 calls
    record       mean   0.20 ms · worst   1.77 ms ·   6.7% of work · 7140 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 032 | | |
| 033 | | |
| 034 | | |
| 035 | | |
| 036 | | |
| 037 | | |
| 038 | | |
| 039 | | |
| 040 | | |
| 041 | | |
| 042 | | |
| 043 | | |
| 044 | | |
| 045 | | |
| 046 | | |
| 047 | | |

### 2026-10-14 15:51 · 이어 찍기 <!-- run:20261014_155146 -->

> ⚠ **중단 — 저장 0편.** 팔로워 연결(configure) 중 5번 모터(wrist_roll) 응답 없음 (`Failed to write 'Lock' on id_=5 … no status packet`, 종료 코드 1). 녹화 시작 전 실패, dataset 은 48편 그대로이고 실행 기록은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-14).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T1R49: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_155146.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 48=T1R49, 49=T1R50, 50=T1R51, 51=T1R52, 52=T1R53, 53=T1R54, 54=T1R55, 55=T1R56, 56=T1R57, 57=T1R58, 58=T1R59, 59=T1R60, 60=T1R61, 61=T1R62, 62=T1R63, 63=T1R64

### 2026-10-14 15:56 · 이어 찍기 <!-- run:20261014_155644 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T1R49: 자유 배치 (빨간 큐브 1) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_155644.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 48=T1R49, 49=T1R50, 50=T1R51, 51=T1R52, 52=T1R53, 53=T1R54, 54=T1R55, 55=T1R56, 56=T1R57, 57=T1R58, 58=T1R59, 59=T1R60, 60=T1R61, 61=T1R62, 62=T1R63, 63=T1R64

**결과** <!-- results:20261014_155644 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 16:10
- repo_id: `oxr/so101_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 540 | 18.0 | 29.89 | 0/539 | T1R49 |
| 049 | 367 | 12.2 | 29.90 | 0/366 | T1R50 |
| 050 | 386 | 12.9 | 29.91 | 0/385 | T1R51 |
| 051 | 436 | 14.5 | 29.91 | 0/435 | T1R52 |
| 052 | 415 | 13.8 | 29.91 | 0/414 | T1R53 |
| 053 | 493 | 16.4 | 29.90 | 0/492 | T1R54 |
| 054 | 422 | 14.1 | 29.90 | 0/421 | T1R55 |
| 055 | 388 | 12.9 | 29.91 | 0/387 | T1R56 |
| 056 | 377 | 12.6 | 29.89 | 0/376 | T1R57 |
| 057 | 369 | 12.3 | 29.90 | 0/368 | T1R58 |
| 058 | 432 | 14.4 | 29.90 | 0/431 | T1R59 |
| 059 | 369 | 12.3 | 29.90 | 0/368 | T1R60 |
| 060 | 387 | 12.9 | 29.89 | 0/386 | T1R61 |
| 061 | 396 | 13.2 | 29.90 | 0/395 | T1R62 |
| 062 | 394 | 13.1 | 29.91 | 0/393 | T1R63 |
| 063 | 420 | 14.0 | 29.88 | 0/419 | T1R64 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 8044 ticks, 8025 judged
  effective cadence: 29.90 Hz over 268.4 s measured
  ticks over the 33.3 ms work budget: 0/8025 (0.0%) — work mean 3.0 ms, worst 28.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 172
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst  26.19 ms ·  44.7% of work · 8044 calls
    process_obs  mean   0.05 ms · worst   2.11 ms ·   1.5% of work · 8044 calls
    teleop       mean   1.12 ms · worst   5.30 ms ·  37.3% of work · 8044 calls
    send         mean   0.24 ms · worst   5.74 ms ·   8.0% of work · 8044 calls
    record       mean   0.20 ms · worst   2.28 ms ·   6.7% of work · 8044 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 048 | | |
| 049 | | |
| 050 | | |
| 051 | | |
| 052 | | |
| 053 | | |
| 054 | | |
| 055 | | |
| 056 | | |
| 057 | | |
| 058 | | |
| 059 | | |
| 060 | | |
| 061 | | |
| 062 | | |
| 063 | | |
