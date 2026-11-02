# practice_50 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/practice_50`
- dataset: `$HOME/so101_runs/practice/practice_50/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-06

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-06 14:14 · 새 녹화 <!-- run:20261006_141453 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/practice_50 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/practice_50/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261006_141453.log`

**결과** <!-- results:20261006_141453 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 14:31
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 20개 (episode 0–19) · 전체 20개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 716 | 23.9 | 29.90 | 0/715 |
| 001 | 747 | 24.9 | 29.90 | 0/746 |
| 002 | 762 | 25.4 | 29.91 | 0/761 |
| 003 | 654 | 21.8 | 29.91 | 0/653 |
| 004 | 676 | 22.5 | 29.90 | 0/675 |
| 005 | 724 | 24.1 | 29.93 | 0/723 |
| 006 | 786 | 26.2 | 29.89 | 0/785 |
| 007 | 593 | 19.8 | 29.91 | 0/592 |
| 008 | 628 | 20.9 | 29.89 | 0/627 |
| 009 | 630 | 21.0 | 29.91 | 0/629 |
| 010 | 600 | 20.0 | 29.90 | 0/599 |
| 011 | 558 | 18.6 | 29.90 | 0/557 |
| 012 | 609 | 20.3 | 29.90 | 0/608 |
| 013 | 531 | 17.7 | 29.90 | 0/530 |
| 014 | 642 | 21.4 | 29.89 | 0/641 |
| 015 | 667 | 22.2 | 29.89 | 0/666 |
| 016 | 704 | 23.5 | 29.90 | 0/703 |
| 017 | 799 | 26.6 | 29.88 | 0/798 |
| 018 | 672 | 22.4 | 29.91 | 0/671 |
| 019 | 599 | 20.0 | 29.91 | 0/598 |

```
Cadence summary — whole run, 21 episodes · target 30 Hz (33.3 ms budget per tick): 14106 ticks, 14085 judged
  effective cadence: 29.90 Hz over 471.1 s measured
  ticks over the 33.3 ms work budget: 0/14085 (0.0%) — work mean 2.8 ms, worst 23.5 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 410
  loop-body steps (share of measured work):
    observe      mean   1.27 ms · worst  21.52 ms ·  44.8% of work · 14106 calls
    process_obs  mean   0.03 ms · worst   0.67 ms ·   1.1% of work · 14106 calls
    teleop       mean   1.11 ms · worst   6.51 ms ·  39.1% of work · 14106 calls
    send         mean   0.22 ms · worst   5.48 ms ·   7.8% of work · 14106 calls
    record       mean   0.16 ms · worst   2.38 ms ·   5.7% of work · 14106 calls
  pacing headroom: 30.6 ms slept per tick on average (max 36.3 ms) — near zero means the loop is saturated
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
| 016 | | |
| 017 | | |
| 018 | | |
| 019 | | |

### 2026-10-06 14:02 · 새 녹화 <!-- run:20261006_140258 -->

**결과** <!-- results:20261006_140258 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 14:31
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=30 · reset_time_s=120
- 에피소드: 이번 1개 (episode 0–0) · 전체 1개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 716 | 23.9 | 29.89 | 0/896 |

```
Cadence summary — whole run, 1 episode · target 30 Hz (33.3 ms budget per tick): 897 ticks, 896 judged
  effective cadence: 29.89 Hz over 30.0 s measured
  ticks over the 33.3 ms work budget: 0/896 (0.0%) — work mean 2.9 ms, worst 28.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 42
  loop-body steps (share of measured work):
    observe      mean   1.31 ms · worst   4.70 ms ·  44.6% of work · 897 calls
    process_obs  mean   0.03 ms · worst   0.94 ms ·   1.1% of work · 897 calls
    teleop       mean   1.14 ms · worst   4.31 ms ·  38.7% of work · 897 calls
    send         mean   0.24 ms · worst  24.89 ms ·   8.3% of work · 897 calls
    record       mean   0.17 ms · worst   1.03 ms ·   5.8% of work · 897 calls
  pacing headroom: 30.5 ms slept per tick on average (max 32.5 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |

### 2026-10-06 14:07 · 새 녹화 <!-- run:20261006_140731 -->

**결과** <!-- results:20261006_140731 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 14:31
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 2개 (episode 0–1) · 전체 2개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 716 | 23.9 | 29.91 | 0/758 |
| 001 | 747 | 24.9 | 29.89 | 0/684 |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 3153 ticks, 3148 judged
  effective cadence: 29.90 Hz over 105.3 s measured
  ticks over the 33.3 ms work budget: 0/3148 (0.0%) — work mean 2.8 ms, worst 24.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 74
  loop-body steps (share of measured work):
    observe      mean   1.25 ms · worst  22.81 ms ·  44.7% of work · 3153 calls
    process_obs  mean   0.03 ms · worst   0.64 ms ·   1.1% of work · 3153 calls
    teleop       mean   1.10 ms · worst   6.63 ms ·  39.4% of work · 3153 calls
    send         mean   0.21 ms · worst   3.07 ms ·   7.5% of work · 3153 calls
    record       mean   0.16 ms · worst   1.17 ms ·   5.8% of work · 3153 calls
  pacing headroom: 30.6 ms slept per tick on average (max 40.7 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |

### 2026-10-06 14:12 · 새 녹화 <!-- run:20261006_141217 -->

**결과** <!-- results:20261006_141217 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 14:31
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 1개 (episode 0–0) · 전체 1개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 716 | 23.9 | 29.91 | 0/1023 |

```
Cadence summary — whole run, 2 episodes · target 30 Hz (33.3 ms budget per tick): 1162 ticks, 1160 judged
  effective cadence: 29.91 Hz over 38.8 s measured
  ticks over the 33.3 ms work budget: 0/1160 (0.0%) — work mean 2.8 ms, worst 6.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 24
  loop-body steps (share of measured work):
    observe      mean   1.25 ms · worst   4.15 ms ·  44.5% of work · 1162 calls
    process_obs  mean   0.03 ms · worst   0.56 ms ·   1.1% of work · 1162 calls
    teleop       mean   1.11 ms · worst   3.73 ms ·  39.3% of work · 1162 calls
    send         mean   0.22 ms · worst   3.01 ms ·   8.0% of work · 1162 calls
    record       mean   0.16 ms · worst   1.37 ms ·   5.6% of work · 1162 calls
  pacing headroom: 30.6 ms slept per tick on average (max 32.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |

### 2026-10-06 14:34 · 이어 찍기 <!-- run:20261006_143454 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/practice_50 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true --resume=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true --resume=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/practice_50/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261006_143454.log`

**결과** <!-- results:20261006_143454 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 14:50
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 20개 (episode 20–39) · 전체 40개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 020 | 615 | 20.5 | 29.92 | 0/614 |
| 021 | 658 | 21.9 | 29.90 | 0/657 |
| 022 | 632 | 21.1 | 29.92 | 0/631 |
| 023 | 542 | 18.1 | 29.89 | 0/541 |
| 024 | 590 | 19.7 | 29.90 | 0/589 |
| 025 | 617 | 20.6 | 29.91 | 0/616 |
| 026 | 656 | 21.9 | 29.90 | 0/655 |
| 027 | 718 | 23.9 | 29.90 | 0/717 |
| 028 | 546 | 18.2 | 29.91 | 0/545 |
| 029 | 613 | 20.4 | 29.93 | 0/612 |
| 030 | 578 | 19.3 | 29.87 | 0/577 |
| 031 | 533 | 17.8 | 29.91 | 0/532 |
| 032 | 602 | 20.1 | 29.89 | 0/601 |
| 033 | 754 | 25.1 | 29.89 | 0/753 |
| 034 | 588 | 19.6 | 29.91 | 0/587 |
| 035 | 554 | 18.5 | 29.92 | 0/553 |
| 036 | 749 | 25.0 | 29.91 | 0/748 |
| 037 | 541 | 18.0 | 29.92 | 0/540 |
| 038 | 604 | 20.1 | 29.91 | 0/603 |
| 039 | 545 | 18.2 | 29.92 | 0/544 |

```
Cadence summary — whole run, 21 episodes · target 30 Hz (33.3 ms budget per tick): 12800 ticks, 12779 judged
  effective cadence: 29.91 Hz over 427.3 s measured
  ticks over the 33.3 ms work budget: 0/12779 (0.0%) — work mean 2.8 ms, worst 22.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 300
  loop-body steps (share of measured work):
    observe      mean   1.26 ms · worst   9.50 ms ·  44.7% of work · 12800 calls
    process_obs  mean   0.03 ms · worst   0.88 ms ·   1.1% of work · 12800 calls
    teleop       mean   1.10 ms · worst  20.44 ms ·  39.3% of work · 12800 calls
    send         mean   0.22 ms · worst   3.90 ms ·   7.7% of work · 12800 calls
    record       mean   0.16 ms · worst   2.60 ms ·   5.7% of work · 12800 calls
  pacing headroom: 30.6 ms slept per tick on average (max 35.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
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
| 032 | | |
| 033 | | |
| 034 | | |
| 035 | | |
| 036 | | |
| 037 | | |
| 038 | | |
| 039 | | |

### 2026-10-06 14:57 · 이어 찍기 <!-- run:20261006_145732 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/practice_50 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true --resume=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubebox_practice50 --dataset.no_stamp=true --resume=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=10 --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/practice_50/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261006_145732.log`

**결과** <!-- results:20261006_145732 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-06 15:05
- repo_id: `oxr/so101_cubebox_practice50` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=120
- 에피소드: 이번 10개 (episode 40–49) · 전체 50개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 040 | 743 | 24.8 | 29.91 | 0/742 |
| 041 | 567 | 18.9 | 29.92 | 0/566 |
| 042 | 752 | 25.1 | 29.92 | 0/751 |
| 043 | 500 | 16.7 | 29.92 | 0/499 |
| 044 | 421 | 14.0 | 29.89 | 0/420 |
| 045 | 423 | 14.1 | 29.90 | 0/422 |
| 046 | 458 | 15.3 | 29.91 | 0/457 |
| 047 | 474 | 15.8 | 29.91 | 0/473 |
| 048 | 490 | 16.3 | 29.93 | 0/489 |
| 049 | 524 | 17.5 | 29.91 | 0/523 |

```
Cadence summary — whole run, 13 episodes · target 30 Hz (33.3 ms budget per tick): 7418 ticks, 7405 judged
  effective cadence: 29.91 Hz over 247.6 s measured
  ticks over the 33.3 ms work budget: 0/7405 (0.0%) — work mean 2.8 ms, worst 27.5 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 140
  loop-body steps (share of measured work):
    observe      mean   1.28 ms · worst  25.69 ms ·  44.9% of work · 7418 calls
    process_obs  mean   0.03 ms · worst   0.70 ms ·   1.1% of work · 7418 calls
    teleop       mean   1.12 ms · worst  10.53 ms ·  39.2% of work · 7418 calls
    send         mean   0.22 ms · worst   4.45 ms ·   7.8% of work · 7418 calls
    record       mean   0.16 ms · worst   1.84 ms ·   5.6% of work · 7418 calls
  pacing headroom: 30.6 ms slept per tick on average (max 33.5 ms) — near zero means the loop is saturated
```

**판별 메모**

- 40·41·42 = 빗잡기(의도)

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 040 | | 빗잡기(의도) |
| 041 | | 빗잡기(의도) |
| 042 | | 빗잡기(의도) |
| 043 | | |
| 044 | | |
| 045 | | |
| 046 | | |
| 047 | | |
| 048 | | |
| 049 | | |

## 학습 기록

### 2026-10-06 15:07 · π0.5 학습 `train/pi05_15k` (50편 전체)

**사전 점검**
- QA 재실행 (`check_dataset.py practice/practice_50`, 2026-10-06 15:06): 50편, 14.0–26.6초, NaN 0, 영상·데이터 프레임 수 일치, 빈 판·잘린 판 없음 → 50편 전부 사용. 40·41·42 = 빗잡기(의도), 그대로 사용
- 녹화 프로세스·twin_ws 컨테이너 없음 (녹화와 겹치지 않음). `~/so101-env` 설치·변경 없음
- dataset stats.json 에 q01/q99 있음. 디스크 여유 796 GB

**명령** (`train/run_pi05_15k.sh` — `train/launch_pi05_15k.sh` 가 백그라운드 실행, 로그 `train/pi05_15k.log`, 메모리 기록 `train/pi05_15k.mem.log`, 시각 `train/pi05_15k.time`)
```bash
PYTHONDONTWRITEBYTECODE=1 $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubebox_practice50 \
  --dataset.root=$HOME/so101_runs/practice/practice_50/dataset \
  --policy.type=pi05 --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/practice/practice_50/train/pi05_15k --job_name=pi05_15k \
  --batch_size=4 --steps=15000 --log_freq=50 --save_freq=5000 --num_workers=4 \
  --wandb.enable=false
```
- 학습 파라미터 4.14B (전부 학습). lr 스케줄 자동 축소: warmup 1000→500, decay 30000→15000 (peak 2.5e-5 → 2.5e-6)
- 15000 스텝 × 배치 4 = 60000 샘플 ≈ 1.94 epoch (30884 프레임). 시작 전 예상 약 10시간 (practice_10 의 2.36 s/step 기준)

**결과**
- 종료: 정상 ("End of training", 코드 0), Traceback 없음. 경고: vision patch_embedding 키 2개 "might need handling" (practice_10 때와 같음)
- loss (50 스텝마다 기록, 300개): step 50 0.131 → 100 0.077 → 500 0.046 → 1000 0.040 → 2000 0.030 → 5000 0.027 → 7500 0.016 → 10000 0.018 → 12500 0.010 → 15000 0.014
  - 구간 평균: 0–1k 0.055 · 1k–2.5k 0.034 · 2.5k–5k 0.027 · 5k–7.5k 0.022 · 7.5k–10k 0.016 · 10k–12.5k 0.014 · 12.5k–15k 0.012 — 끝까지 줄어듦 (처음 5회 평균 0.081, 마지막 5회 평균 0.011, 최저 0.009 @13000)
  - grad norm 3.4 → 0.4–0.5
- 시간: 전체 2026-10-06 15:07:41 – 10-07 01:01:46 (9시간 54분) = 모델 생성 약 2분 45초 (pi05_base 캐시 사용) + 학습 9시간 51분 07초 (2.36 s/step, 저장 3회 포함) + 마무리 약 10초
- 메모리: lerobot 표시 mem_gb 36.99, nvidia-smi 프로세스 39.3 GB. 시스템 전체(통합 메모리) 최대 약 65 GB
- 체크포인트 (`train/pi05_15k/checkpoints/`, `last` → 015000), 각 23 GB, 합계 69 GB
  - `005000/` (10-06 18:27), `010000/` (21:44), `015000/` (10-07 01:01)
  - 각각 `pretrained_model/` 8.8 GB (config·model.safetensors·전처리/후처리 normalizer·tokenizer·train_config) + `training_state/` 15 GB (optimizer_state·scheduler·rng·step)
  - 015000 의 optimizer 상태 보존 (이어서 학습용). 005000·010000 의 training_state 도 지우지 않음
- 허브 업로드 없음 (push_to_hub=false)

### 2026-10-07 10:35 · 실물 rollout 준비 `eval/` (팔 연결 없음)
- practice_10/eval 에서 복사: `run_rollout.sh` (체크포인트 `STEP=005000|010000|015000`, 기본 015000; 결과 `eval/rollouts/<시각>_<15k>_<tag>/`, repo `oxr/rollout_practice50_pi05_15k_<15k>_<tag>`), `rollout_logged.py`, `plot_rollout.py` (그대로), `pose_check.py`·`analyze_rollout.py` (경로만 practice_50 으로)
- 옵션 파싱 오프라인 확인 (`build_rollout_context` 전에 멈춤, 팔·카메라 연결 없음): pi05 15000 체크포인트, RTC guided horizon 20 · queue 40 · 5단계, max_relative_target 8 → OK
- 카메라: 지금 front·wrist 모두 자동 노출·자동 WB (156/4600 기본값) = practice_50 녹화 때와 같음
- 기준값: `eval/reference_teleop/analysis.json` (50편 사람 조작) — action 방향 바뀜 0.21/0.27/0.28/0.34/0.34/0.21 회/초, hf_rms 0.27/0.30/0.31/0.28/0.31/0.48°
- 첫 실행 권장 (practice_10 에서 유일하게 성공한 설정): `./run_rollout.sh rtc_fast --policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40`
