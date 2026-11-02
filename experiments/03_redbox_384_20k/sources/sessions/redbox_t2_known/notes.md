# redbox_t2_known (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t2_known`
- dataset: `$HOME/so101_runs/main/redbox_t2_known/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 16:16 · 새 녹화 <!-- run:20261014_161637 -->

> ⚠ **삭제 — 2편 (빨강 3개 고정).** T2 설계를 빨강 2~4개(24/24/16)로 바꾸면서 사용자 요청으로 지움 (2026-10-14). dataset·리뷰 영상·사진은 `~/so101_runs/_deleted/redbox_t2_known_3cube_20261014_161637/` 로, 실행 기록은 `~/.local/state/record_ui/deleted_runs/` 로 옮김. 배치 계획은 새로 만듦.

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T2K1K3K4: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K3(-7.8,12.7) · 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_161637.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_known/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 0=T2K1K3K4, 1=T2K2K3K4, 2=T2K1K2K3, 3=T2K1K2K4, 4=T2K1K2K3, 5=T2K1K3K4, 6=T2K2K3K4, 7=T2K1K2K4, 8=T2K1K3K4, 9=T2K2K3K4, 10=T2K1K2K4, 11=T2K1K2K3, 12=T2K2K3K4, 13=T2K1K3K4, 14=T2K1K2K4, 15=T2K1K2K3

**결과** <!-- results:20261014_161637 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 16:19
- repo_id: `oxr/so101_redbox_t2_known` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=120
- 에피소드: 이번 2개 (episode 0–1) · 전체 2개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 841 | 28.0 | 29.89 | 0/840 | T2K1K3K4 |
| 001 | 708 | 23.6 | 29.89 | 0/707 | T2K2K3K4 |

```
Cadence summary — whole run, 2 episodes · target 30 Hz (33.3 ms budget per tick): 1549 ticks, 1547 judged
  effective cadence: 29.89 Hz over 51.8 s measured
  ticks over the 33.3 ms work budget: 0/1547 (0.0%) — work mean 3.0 ms, worst 27.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 47
  loop-body steps (share of measured work):
    observe      mean   1.37 ms · worst  24.76 ms ·  45.5% of work · 1549 calls
    process_obs  mean   0.05 ms · worst   1.57 ms ·   1.6% of work · 1549 calls
    teleop       mean   1.11 ms · worst   3.71 ms ·  36.6% of work · 1549 calls
    send         mean   0.23 ms · worst   2.70 ms ·   7.6% of work · 1549 calls
    record       mean   0.21 ms · worst   2.02 ms ·   6.9% of work · 1549 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.7 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |

### 2026-10-14 16:28 · 새 녹화 <!-- run:20261014_162811 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T2K1K2: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K2(-16.2,21.3) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_162811.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_known/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 0=T2K1K2, 1=T2K2K3K4, 2=T2K1K2K3K4, 3=T2K3K4, 4=T2K1K2K3, 5=T2K2K3, 6=T2K1K3K4, 7=T2K1K2K3K4, 8=T2K1K2K4, 9=T2K1K2K3K4, 10=T2K1K3K4, 11=T2K1K2K3K4, 12=T2K1K4, 13=T2K2K3K4, 14=T2K1K3, 15=T2K2K4

**결과** <!-- results:20261014_162811 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 16:46
- repo_id: `oxr/so101_redbox_t2_known` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 627 | 20.9 | 29.89 | 0/626 | T2K1K2 |
| 001 | 808 | 26.9 | 29.90 | 0/807 | T2K2K3K4 |
| 002 | 1072 | 35.7 | 29.89 | 0/1071 | T2K1K2K3K4 |
| 003 | 542 | 18.1 | 29.89 | 0/541 | T2K3K4 |
| 004 | 845 | 28.2 | 29.88 | 0/844 | T2K1K2K3 |
| 005 | 545 | 18.2 | 29.91 | 0/544 | T2K2K3 |
| 006 | 934 | 31.1 | 29.90 | 0/933 | T2K1K3K4 |
| 007 | 995 | 33.2 | 29.89 | 0/994 | T2K1K2K3K4 |
| 008 | 775 | 25.8 | 29.88 | 0/774 | T2K1K2K4 |
| 009 | 850 | 28.3 | 29.89 | 0/849 | T2K1K2K3K4 |
| 010 | 786 | 26.2 | 29.88 | 0/785 | T2K1K3K4 |
| 011 | 874 | 29.1 | 29.89 | 0/873 | T2K1K2K3K4 |
| 012 | 604 | 20.1 | 29.87 | 0/603 | T2K1K4 |
| 013 | 812 | 27.1 | 29.89 | 0/811 | T2K2K3K4 |
| 014 | 603 | 20.1 | 29.88 | 0/602 | T2K1K3 |
| 015 | 508 | 16.9 | 29.91 | 0/507 | T2K2K4 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 14018 ticks, 13999 judged
  effective cadence: 29.89 Hz over 468.3 s measured
  ticks over the 33.3 ms work budget: 0/13999 (0.0%) — work mean 3.1 ms, worst 27.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 377
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst   5.92 ms ·  44.6% of work · 14018 calls
    process_obs  mean   0.05 ms · worst   2.14 ms ·   1.5% of work · 14018 calls
    teleop       mean   1.14 ms · worst  21.92 ms ·  37.2% of work · 14018 calls
    send         mean   0.25 ms · worst   3.73 ms ·   8.1% of work · 14018 calls
    record       mean   0.20 ms · worst   3.21 ms ·   6.7% of work · 14018 calls
  pacing headroom: 30.4 ms slept per tick on average (max 36.5 ms) — near zero means the loop is saturated
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

### 2026-10-14 17:20 · 이어 찍기 <!-- run:20261014_172051 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T2K1K3: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K3(-7.8,12.7) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_172051.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_known/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 16=T2K1K3, 17=T2K1K2K3, 18=T2K1K2K3K4, 19=T2K1K2K4, 20=T2K1K2K3K4, 21=T2K2K4, 22=T2K1K2, 23=T2K1K2K4, 24=T2K3K4, 25=T2K2K3K4, 26=T2K1K2K3K4, 27=T2K1K4, 28=T2K2K3, 29=T2K1K3K4, 30=T2K1K2K3K4, 31=T2K1K2K3

**결과** <!-- results:20261014_172051 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 17:38
- repo_id: `oxr/so101_redbox_t2_known` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 721 | 24.0 | 29.89 | 0/720 | T2K1K3 |
| 017 | 910 | 30.3 | 29.89 | 0/909 | T2K1K2K3 |
| 018 | 955 | 31.8 | 29.89 | 0/954 | T2K1K2K3K4 |
| 019 | 826 | 27.5 | 29.90 | 0/825 | T2K1K2K4 |
| 020 | 982 | 32.7 | 29.89 | 0/981 | T2K1K2K3K4 |
| 021 | 506 | 16.9 | 29.88 | 0/505 | T2K2K4 |
| 022 | 635 | 21.2 | 29.89 | 0/634 | T2K1K2 |
| 023 | 759 | 25.3 | 29.89 | 0/758 | T2K1K2K4 |
| 024 | 506 | 16.9 | 29.89 | 0/505 | T2K3K4 |
| 025 | 714 | 23.8 | 29.89 | 0/713 | T2K2K3K4 |
| 026 | 832 | 27.7 | 29.89 | 0/831 | T2K1K2K3K4 |
| 027 | 592 | 19.7 | 29.90 | 0/591 | T2K1K4 |
| 028 | 573 | 19.1 | 29.90 | 0/572 | T2K2K3 |
| 029 | 830 | 27.7 | 29.89 | 0/829 | T2K1K3K4 |
| 030 | 836 | 27.9 | 29.89 | 0/835 | T2K1K2K3K4 |
| 031 | 732 | 24.4 | 29.88 | 0/731 | T2K1K2K3 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 13602 ticks, 13583 judged
  effective cadence: 29.89 Hz over 454.4 s measured
  ticks over the 33.3 ms work budget: 0/13583 (0.0%) — work mean 3.1 ms, worst 21.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 337
  loop-body steps (share of measured work):
    observe      mean   1.38 ms · worst  19.54 ms ·  44.9% of work · 13602 calls
    process_obs  mean   0.05 ms · worst   2.12 ms ·   1.5% of work · 13602 calls
    teleop       mean   1.14 ms · worst   5.77 ms ·  37.2% of work · 13602 calls
    send         mean   0.24 ms · worst   6.08 ms ·   7.8% of work · 13602 calls
    record       mean   0.21 ms · worst   4.01 ms ·   6.7% of work · 13602 calls
  pacing headroom: 30.4 ms slept per tick on average (max 35.4 ms) — near zero means the loop is saturated
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

### 2026-10-15 10:24 · 이어 찍기 <!-- run:20261015_102400 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T2K1K2K3K4: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K2(-16.2,21.3) · 빨간 큐브 K3(-7.8,12.7) · 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_102400.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_known/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 32=T2K1K2K3K4, 33=T2K3K4, 34=T2K1K2K3, 35=T2K1K2K4, 36=T2K1K2, 37=T2K2K3K4, 38=T2K2K3, 39=T2K1K2K3K4, 40=T2K1K3K4, 41=T2K2K4, 42=T2K1K4, 43=T2K1K2K3K4, 44=T2K1K2K3, 45=T2K1K2K3K4, 46=T2K1K3K4, 47=T2K1K2

**결과** <!-- results:20261015_102400 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 10:40
- repo_id: `oxr/so101_redbox_t2_known` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 949 | 31.6 | 29.90 | 0/948 | T2K1K2K3K4 |
| 033 | 507 | 16.9 | 29.91 | 0/506 | T2K3K4 |
| 034 | 680 | 22.7 | 29.88 | 0/679 | T2K1K2K3 |
| 035 | 715 | 23.8 | 29.90 | 0/714 | T2K1K2K4 |
| 036 | 508 | 16.9 | 29.90 | 0/507 | T2K1K2 |
| 037 | 806 | 26.9 | 29.89 | 0/805 | T2K2K3K4 |
| 038 | 560 | 18.7 | 29.90 | 0/559 | T2K2K3 |
| 039 | 849 | 28.3 | 29.90 | 0/848 | T2K1K2K3K4 |
| 040 | 746 | 24.9 | 29.89 | 0/745 | T2K1K3K4 |
| 041 | 646 | 21.5 | 29.88 | 0/645 | T2K2K4 |
| 042 | 564 | 18.8 | 29.89 | 0/563 | T2K1K4 |
| 043 | 1009 | 33.6 | 29.90 | 0/1008 | T2K1K2K3K4 |
| 044 | 700 | 23.3 | 29.88 | 0/699 | T2K1K2K3 |
| 045 | 845 | 28.2 | 29.89 | 0/844 | T2K1K2K3K4 |
| 046 | 673 | 22.4 | 29.90 | 0/672 | T2K1K3K4 |
| 047 | 566 | 18.9 | 29.89 | 0/565 | T2K1K2 |

```
Cadence summary — whole run, 16 episodes · target 30 Hz (33.3 ms budget per tick): 11323 ticks, 11307 judged
  effective cadence: 29.89 Hz over 378.2 s measured
  ticks over the 33.3 ms work budget: 0/11307 (0.0%) — work mean 3.1 ms, worst 27.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 264
  loop-body steps (share of measured work):
    observe      mean   1.38 ms · worst  25.22 ms ·  44.7% of work · 11323 calls
    process_obs  mean   0.05 ms · worst   0.93 ms ·   1.5% of work · 11323 calls
    teleop       mean   1.14 ms · worst   4.38 ms ·  37.1% of work · 11323 calls
    send         mean   0.25 ms · worst   4.49 ms ·   8.2% of work · 11323 calls
    record       mean   0.21 ms · worst   3.07 ms ·   6.7% of work · 11323 calls
  pacing headroom: 30.3 ms slept per tick on average (max 34.1 ms) — near zero means the loop is saturated
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

### 2026-10-15 13:22 · 이어 찍기 <!-- run:20261015_132238 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T2K1K2K3K4: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K2(-16.2,21.3) · 빨간 큐브 K3(-7.8,12.7) · 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_known --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_132238.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_known/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 48=T2K1K2K3K4, 49=T2K2K4, 50=T2K1K2, 51=T2K1K2K4, 52=T2K1K4, 53=T2K1K3, 54=T2K3K4, 55=T2K2K3K4, 56=T2K1K2K3K4, 57=T2K2K3K4, 58=T2K1K2K3K4, 59=T2K2K3, 60=T2K1K3K4, 61=T2K1K2K3K4, 62=T2K1K2K3, 63=T2K1K2K4

**결과** <!-- results:20261015_132238 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 13:38
- repo_id: `oxr/so101_redbox_t2_known` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 807 | 26.9 | 29.89 | 0/806 | T2K1K2K3K4 |
| 049 | 448 | 14.9 | 29.89 | 0/447 | T2K2K4 |
| 050 | 488 | 16.3 | 29.90 | 0/487 | T2K1K2 |
| 051 | 541 | 18.0 | 29.88 | 0/540 | T2K1K2K4 |
| 052 | 571 | 19.0 | 29.90 | 0/570 | T2K1K4 |
| 053 | 510 | 17.0 | 29.89 | 0/509 | T2K1K3 |
| 054 | 473 | 15.8 | 29.90 | 0/472 | T2K3K4 |
| 055 | 656 | 21.9 | 29.89 | 0/655 | T2K2K3K4 |
| 056 | 907 | 30.2 | 29.89 | 0/906 | T2K1K2K3K4 |
| 057 | 607 | 20.2 | 29.90 | 0/606 | T2K2K3K4 |
| 058 | 681 | 22.7 | 29.90 | 0/680 | T2K1K2K3K4 |
| 059 | 525 | 17.5 | 29.90 | 0/524 | T2K2K3 |
| 060 | 588 | 19.6 | 29.87 | 0/587 | T2K1K3K4 |
| 061 | 777 | 25.9 | 29.90 | 0/776 | T2K1K2K3K4 |
| 062 | 597 | 19.9 | 29.89 | 0/596 | T2K1K2K3 |
| 063 | 673 | 22.4 | 29.89 | 0/672 | T2K1K2K4 |

```
Cadence summary — whole run, 16 episodes · target 30 Hz (33.3 ms budget per tick): 9849 ticks, 9833 judged
  effective cadence: 29.89 Hz over 328.9 s measured
  ticks over the 33.3 ms work budget: 0/9833 (0.0%) — work mean 3.0 ms, worst 10.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 266
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst   6.61 ms ·  44.8% of work · 9849 calls
    process_obs  mean   0.05 ms · worst   2.08 ms ·   1.6% of work · 9849 calls
    teleop       mean   1.13 ms · worst   4.25 ms ·  37.1% of work · 9849 calls
    send         mean   0.24 ms · worst   3.68 ms ·   7.9% of work · 9849 calls
    record       mean   0.21 ms · worst   2.70 ms ·   6.8% of work · 9849 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.1 ms) — near zero means the loop is saturated
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
