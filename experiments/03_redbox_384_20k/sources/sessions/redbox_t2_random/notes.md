# redbox_t2_random (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t2_random`
- dataset: `$HOME/so101_runs/main/redbox_t2_random/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 16:57 · 새 녹화 <!-- run:20261014_165734 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T2R01n3: 자유 배치 (빨간 큐브 3개) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_165734.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_random/layout.csv` (그룹 `t2_random`) · 이번 실행 배치 0=T2R01n3, 1=T2R02n2, 2=T2R03n4, 3=T2R04n2, 4=T2R05n2, 5=T2R06n4, 6=T2R07n3, 7=T2R08n3, 8=T2R09n3, 9=T2R10n4, 10=T2R11n3, 11=T2R12n2, 12=T2R13n4, 13=T2R14n2, 14=T2R15n2, 15=T2R16n3

**결과** <!-- results:20261014_165734 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 17:15
- repo_id: `oxr/so101_redbox_t2_random` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 805 | 26.8 | 29.90 | 0/804 | T2R01n3 |
| 001 | 640 | 21.3 | 29.91 | 0/639 | T2R02n2 |
| 002 | 937 | 31.2 | 29.88 | 0/936 | T2R03n4 |
| 003 | 589 | 19.6 | 29.89 | 0/588 | T2R04n2 |
| 004 | 536 | 17.9 | 29.90 | 0/535 | T2R05n2 |
| 005 | 925 | 30.8 | 29.88 | 0/924 | T2R06n4 |
| 006 | 855 | 28.5 | 29.89 | 0/854 | T2R07n3 |
| 007 | 775 | 25.8 | 29.89 | 0/774 | T2R08n3 |
| 008 | 812 | 27.1 | 29.90 | 0/811 | T2R09n3 |
| 009 | 961 | 32.0 | 29.89 | 0/960 | T2R10n4 |
| 010 | 697 | 23.2 | 29.89 | 0/696 | T2R11n3 |
| 011 | 504 | 16.8 | 29.90 | 0/503 | T2R12n2 |
| 012 | 950 | 31.7 | 29.90 | 0/949 | T2R13n4 |
| 013 | 533 | 17.8 | 29.90 | 0/532 | T2R14n2 |
| 014 | 652 | 21.7 | 29.90 | 0/651 | T2R15n2 |
| 015 | 753 | 25.1 | 29.89 | 0/752 | T2R16n3 |

```
Cadence summary — whole run, 20 episodes · target 30 Hz (33.3 ms budget per tick): 14601 ticks, 14581 judged
  effective cadence: 29.89 Hz over 487.8 s measured
  ticks over the 33.3 ms work budget: 0/14581 (0.0%) — work mean 3.0 ms, worst 29.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 345
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst  18.40 ms ·  44.6% of work · 14601 calls
    process_obs  mean   0.05 ms · worst   2.25 ms ·   1.5% of work · 14601 calls
    teleop       mean   1.13 ms · worst  25.19 ms ·  37.4% of work · 14601 calls
    send         mean   0.24 ms · worst   3.58 ms ·   7.8% of work · 14601 calls
    record       mean   0.20 ms · worst   2.35 ms ·   6.8% of work · 14601 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.7 ms) — near zero means the loop is saturated
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

### 2026-10-15 09:43 · 이어 찍기 <!-- run:20261015_094319 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T2R17n3: 자유 배치 (빨간 큐브 3개) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_094319.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_random/layout.csv` (그룹 `t2_random`) · 이번 실행 배치 16=T2R17n3, 17=T2R18n2, 18=T2R19n2, 19=T2R20n3, 20=T2R21n3, 21=T2R22n2, 22=T2R23n4, 23=T2R24n4, 24=T2R25n3, 25=T2R26n3, 26=T2R27n4, 27=T2R28n4, 28=T2R29n2, 29=T2R30n2, 30=T2R31n2, 31=T2R32n3

**결과** <!-- results:20261015_094319 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 10:05
- repo_id: `oxr/so101_redbox_t2_random` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 6번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 983 | 32.8 | 29.89 | 0/982 | T2R17n3 |
| 017 | 740 | 24.7 | 29.90 | 0/739 | T2R18n2 |
| 018 | 570 | 19.0 | 29.90 | 0/569 | T2R19n2 |
| 019 | 804 | 26.8 | 29.89 | 0/803 | T2R20n3 |
| 020 | 771 | 25.7 | 29.90 | 0/770 | T2R21n3 |
| 021 | 633 | 21.1 | 29.90 | 0/632 | T2R22n2 |
| 022 | 1113 | 37.1 | 29.89 | 0/1112 | T2R23n4 |
| 023 | 1182 | 39.4 | 29.90 | 0/1181 | T2R24n4 |
| 024 | 754 | 25.1 | 29.89 | 0/753 | T2R25n3 |
| 025 | 1011 | 33.7 | 29.89 | 0/1010 | T2R26n3 |
| 026 | 1038 | 34.6 | 29.90 | 0/1037 | T2R27n4 |
| 027 | 1012 | 33.7 | 29.88 | 0/1011 | T2R28n4 |
| 028 | 537 | 17.9 | 29.90 | 0/536 | T2R29n2 |
| 029 | 750 | 25.0 | 29.90 | 0/749 | T2R30n2 |
| 030 | 630 | 21.0 | 29.88 | 0/629 | T2R31n2 |
| 031 | 754 | 25.1 | 29.89 | 0/753 | T2R32n3 |

```
Cadence summary — whole run, 22 episodes · target 30 Hz (33.3 ms budget per tick): 17023 ticks, 17001 judged
  effective cadence: 29.89 Hz over 568.7 s measured
  ticks over the 33.3 ms work budget: 0/17001 (0.0%) — work mean 3.0 ms, worst 21.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 401
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst  19.23 ms ·  44.5% of work · 17023 calls
    process_obs  mean   0.05 ms · worst   1.67 ms ·   1.5% of work · 17023 calls
    teleop       mean   1.13 ms · worst   4.93 ms ·  37.1% of work · 17023 calls
    send         mean   0.25 ms · worst   9.55 ms ·   8.2% of work · 17023 calls
    record       mean   0.21 ms · worst   2.55 ms ·   6.8% of work · 17023 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.5 ms) — near zero means the loop is saturated
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

### 2026-10-15 10:47 · 이어 찍기 <!-- run:20261015_104716 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T2R33n2: 자유 배치 (빨간 큐브 2개) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_104716.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_random/layout.csv` (그룹 `t2_random`) · 이번 실행 배치 32=T2R33n2, 33=T2R34n4, 34=T2R35n2, 35=T2R36n3, 36=T2R37n4, 37=T2R38n3, 38=T2R39n2, 39=T2R40n3, 40=T2R41n2, 41=T2R42n4, 42=T2R43n3, 43=T2R44n4, 44=T2R45n2, 45=T2R46n3, 46=T2R47n3, 47=T2R48n2

**결과** <!-- results:20261015_104716 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 11:10
- repo_id: `oxr/so101_redbox_t2_random` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 8번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 686 | 22.9 | 29.89 | 0/685 | T2R33n2 |
| 033 | 1039 | 34.6 | 29.89 | 0/1038 | T2R34n4 |
| 034 | 506 | 16.9 | 29.90 | 0/505 | T2R35n2 |
| 035 | 708 | 23.6 | 29.90 | 0/707 | T2R36n3 |
| 036 | 1036 | 34.5 | 29.89 | 0/1035 | T2R37n4 |
| 037 | 621 | 20.7 | 29.89 | 0/620 | T2R38n3 |
| 038 | 556 | 18.5 | 29.88 | 0/555 | T2R39n2 |
| 039 | 670 | 22.3 | 29.90 | 0/669 | T2R40n3 |
| 040 | 522 | 17.4 | 29.88 | 0/521 | T2R41n2 |
| 041 | 830 | 27.7 | 29.88 | 0/829 | T2R42n4 |
| 042 | 630 | 21.0 | 29.89 | 0/629 | T2R43n3 |
| 043 | 1077 | 35.9 | 29.90 | 0/1076 | T2R44n4 |
| 044 | 482 | 16.1 | 29.87 | 0/481 | T2R45n2 |
| 045 | 745 | 24.8 | 29.90 | 0/744 | T2R46n3 |
| 046 | 652 | 21.7 | 29.88 | 0/651 | T2R47n3 |
| 047 | 394 | 13.1 | 29.90 | 0/393 | T2R48n2 |

```
Cadence summary — whole run, 24 episodes · target 30 Hz (33.3 ms budget per tick): 17473 ticks, 17449 judged
  effective cadence: 29.89 Hz over 583.8 s measured
  ticks over the 33.3 ms work budget: 0/17449 (0.0%) — work mean 3.0 ms, worst 16.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 451
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst  15.25 ms ·  44.8% of work · 17473 calls
    process_obs  mean   0.05 ms · worst   0.78 ms ·   1.5% of work · 17473 calls
    teleop       mean   1.13 ms · worst   6.00 ms ·  37.2% of work · 17473 calls
    send         mean   0.24 ms · worst   4.01 ms ·   7.9% of work · 17473 calls
    record       mean   0.20 ms · worst   2.12 ms ·   6.7% of work · 17473 calls
  pacing headroom: 30.4 ms slept per tick on average (max 39.5 ms) — near zero means the loop is saturated
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

### 2026-10-15 13:44 · 이어 찍기 <!-- run:20261015_134431 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T2R49n2: 자유 배치 (빨간 큐브 2개) — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t2_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2_random --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t2_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_134431.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t2_random/layout.csv` (그룹 `t2_random`) · 이번 실행 배치 48=T2R49n2, 49=T2R50n3, 50=T2R51n3, 51=T2R52n3, 52=T2R53n4, 53=T2R54n2, 54=T2R55n4, 55=T2R56n2, 56=T2R57n4, 57=T2R58n3, 58=T2R59n2, 59=T2R60n3, 60=T2R61n2, 61=T2R62n4, 62=T2R63n2, 63=T2R64n3

**결과** <!-- results:20261015_134431 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 14:01
- repo_id: `oxr/so101_redbox_t2_random` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=75 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 535 | 17.8 | 29.88 | 0/534 | T2R49n2 |
| 049 | 646 | 21.5 | 29.90 | 0/645 | T2R50n3 |
| 050 | 977 | 32.6 | 29.89 | 0/976 | T2R51n3 |
| 051 | 656 | 21.9 | 29.89 | 0/655 | T2R52n3 |
| 052 | 713 | 23.8 | 29.90 | 0/712 | T2R53n4 |
| 053 | 517 | 17.2 | 29.90 | 0/516 | T2R54n2 |
| 054 | 758 | 25.3 | 29.89 | 0/757 | T2R55n4 |
| 055 | 480 | 16.0 | 29.89 | 0/479 | T2R56n2 |
| 056 | 839 | 28.0 | 29.89 | 0/838 | T2R57n4 |
| 057 | 594 | 19.8 | 29.89 | 0/593 | T2R58n3 |
| 058 | 447 | 14.9 | 29.89 | 0/446 | T2R59n2 |
| 059 | 579 | 19.3 | 29.89 | 0/578 | T2R60n3 |
| 060 | 483 | 16.1 | 29.90 | 0/482 | T2R61n2 |
| 061 | 739 | 24.6 | 29.90 | 0/738 | T2R62n4 |
| 062 | 481 | 16.0 | 29.90 | 0/480 | T2R63n2 |
| 063 | 597 | 19.9 | 29.89 | 0/596 | T2R64n3 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 10778 ticks, 10760 judged
  effective cadence: 29.89 Hz over 360.0 s measured
  ticks over the 33.3 ms work budget: 0/10760 (0.0%) — work mean 3.1 ms, worst 29.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 241
  loop-body steps (share of measured work):
    observe      mean   1.37 ms · worst  11.84 ms ·  44.7% of work · 10778 calls
    process_obs  mean   0.05 ms · worst   1.97 ms ·   1.5% of work · 10778 calls
    teleop       mean   1.13 ms · worst   7.86 ms ·  37.1% of work · 10778 calls
    send         mean   0.25 ms · worst  22.49 ms ·   8.1% of work · 10778 calls
    record       mean   0.21 ms · worst   1.84 ms ·   6.7% of work · 10778 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
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
