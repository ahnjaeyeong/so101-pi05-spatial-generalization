# redbox_t1_random (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/redbox_t1_random`
- dataset: `$HOME/so101_runs/main_k8/redbox_t1_random/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-22

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-22 16:29 · 새 녹화 <!-- run:20261022_162949 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1R01 · 1개 · 빨강 — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_162949.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 0=T1R01, 1=T1R02, 2=T1R03, 3=T1R04, 4=T1R05, 5=T1R06, 6=T1R07, 7=T1R08, 8=T1R09, 9=T1R10, 10=T1R11, 11=T1R12, 12=T1R13, 13=T1R14, 14=T1R15, 15=T1R16

**결과** <!-- results:20261022_162949 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 16:41
- repo_id: `oxr/so101_k8_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 528 | 17.6 | 29.93 | 0/527 | T1R01 |
| 001 | 455 | 15.2 | 29.92 | 0/454 | T1R02 |
| 002 | 547 | 18.2 | 29.92 | 0/546 | T1R03 |
| 003 | 447 | 14.9 | 29.92 | 0/446 | T1R04 |
| 004 | 517 | 17.2 | 29.92 | 0/516 | T1R05 |
| 005 | 434 | 14.5 | 29.92 | 0/433 | T1R06 |
| 006 | 481 | 16.0 | 29.91 | 0/480 | T1R07 |
| 007 | 436 | 14.5 | 29.92 | 0/435 | T1R08 |
| 008 | 468 | 15.6 | 29.93 | 0/467 | T1R09 |
| 009 | 502 | 16.7 | 29.92 | 0/501 | T1R10 |
| 010 | 475 | 15.8 | 29.92 | 0/474 | T1R11 |
| 011 | 433 | 14.4 | 29.93 | 0/432 | T1R12 |
| 012 | 426 | 14.2 | 29.92 | 0/425 | T1R13 |
| 013 | 419 | 14.0 | 29.91 | 0/418 | T1R14 |
| 014 | 390 | 13.0 | 29.91 | 0/389 | T1R15 |
| 015 | 484 | 16.1 | 29.93 | 0/483 | T1R16 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 7759 ticks, 7741 judged
  effective cadence: 29.92 Hz over 258.7 s measured
  ticks over the 33.3 ms work budget: 0/7741 (0.0%) — work mean 2.7 ms, worst 28.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 99
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst  26.40 ms ·  44.9% of work · 7759 calls
    process_obs  mean   0.03 ms · worst   0.61 ms ·   1.0% of work · 7759 calls
    teleop       mean   1.07 ms · worst   4.74 ms ·  39.9% of work · 7759 calls
    send         mean   0.20 ms · worst   3.39 ms ·   7.5% of work · 7759 calls
    record       mean   0.15 ms · worst   1.35 ms ·   5.4% of work · 7759 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
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

### 2026-10-22 16:58 · 이어 찍기 <!-- run:20261022_165820 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T1R17 · 1개 · 빨강 — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_165820.log`
- 목표: 유효 64편 (계획 줄 65 = 유효 64 + 제외 1) · 실행 전 16편 · 남은 49편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 16=T1R17, 17=T1R18, 18=T1R19, 19=T1R20, 20=T1R21, 21=T1R22, 22=T1R23, 23=T1R24, 24=T1R25, 25=T1R26, 26=T1R27, 27=T1R28, 28=T1R29, 29=T1R30, 30=T1R31, 31=T1R32

**결과** <!-- results:20261022_165820 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 17:16
- repo_id: `oxr/so101_k8_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 10번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 559 | 18.6 | 29.93 | 0/558 | T1R17 |
| 017 | 614 | 20.5 | 29.91 | 0/613 | T1R18 |
| 018 | 450 | 15.0 | 29.92 | 0/449 | T1R19 |
| 019 | 437 | 14.6 | 29.93 | 0/436 | T1R20 |
| 020 | 556 | 18.5 | 29.90 | 0/555 | T1R21 |
| 021 | 528 | 17.6 | 29.91 | 0/527 | T1R22 |
| 022 | 529 | 17.6 | 29.91 | 0/528 | T1R23 |
| 023 | 544 | 18.1 | 29.93 | 0/543 | T1R24 |
| 024 | 503 | 16.8 | 29.91 | 0/502 | T1R25 |
| 025 | 491 | 16.4 | 29.91 | 0/490 | T1R26 |
| 026 | 454 | 15.1 | 29.92 | 0/453 | T1R27 |
| 027 | 522 | 17.4 | 29.92 | 0/521 | T1R28 |
| 028 | 431 | 14.4 | 29.92 | 0/430 | T1R29 |
| 029 | 470 | 15.7 | 29.92 | 0/469 | T1R30 |
| 030 | 462 | 15.4 | 29.92 | 0/461 | T1R31 |
| 031 | 524 | 17.5 | 29.92 | 0/523 | T1R32 |

```
Cadence summary — whole run, 26 episodes · target 30 Hz (33.3 ms budget per tick): 12082 ticks, 12056 judged
  effective cadence: 29.92 Hz over 403.0 s measured
  ticks over the 33.3 ms work budget: 0/12056 (0.0%) — work mean 2.7 ms, worst 26.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 187
  loop-body steps (share of measured work):
    observe      mean   1.23 ms · worst  24.06 ms ·  45.1% of work · 12082 calls
    process_obs  mean   0.03 ms · worst   0.71 ms ·   1.0% of work · 12082 calls
    teleop       mean   1.08 ms · worst  23.87 ms ·  39.7% of work · 12082 calls
    send         mean   0.20 ms · worst   5.51 ms ·   7.4% of work · 12082 calls
    record       mean   0.15 ms · worst   2.35 ms ·   5.5% of work · 12082 calls
  pacing headroom: 30.7 ms slept per tick on average (max 35.0 ms) — near zero means the loop is saturated
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

### 2026-10-23 09:50 · 이어 찍기 <!-- run:20261023_095034 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T1R33 · 1개 · 빨강 — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_095034.log`
- 목표: 유효 64편 (계획 줄 65 = 유효 64 + 제외 1) · 실행 전 32편 · 남은 33편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 32=T1R33, 33=T1R34, 34=T1R35, 35=T1R36, 36=T1R37, 37=T1R38, 38=T1R39, 39=T1R40, 40=T1R41, 41=T1R42, 42=T1R43, 43=T1R44, 44=T1R45, 45=T1R46, 46=T1R47, 47=T1R48

**결과** <!-- results:20261023_095034 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 10:10
- repo_id: `oxr/so101_k8_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 9번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 549 | 18.3 | 29.92 | 0/548 | T1R33 |
| 033 | 561 | 18.7 | 29.90 | 0/560 | T1R34 |
| 034 | 435 | 14.5 | 29.93 | 0/434 | T1R35 |
| 035 | 509 | 17.0 | 29.92 | 0/508 | T1R36 |
| 036 | 765 | 25.5 | 29.91 | 0/764 | T1R37 |
| 037 | 475 | 15.8 | 29.91 | 0/474 | T1R38 |
| 038 | 656 | 21.9 | 29.91 | 0/655 | T1R39 |
| 039 | 933 | 31.1 | 29.91 | 0/932 | T1R40 |
| 040 | 702 | 23.4 | 29.89 | 0/701 | T1R41 |
| 041 | 796 | 26.5 | 29.92 | 0/795 | T1R42 |
| 042 | 556 | 18.5 | 29.92 | 0/555 | T1R43 |
| 043 | 532 | 17.7 | 29.90 | 0/531 | T1R44 |
| 044 | 552 | 18.4 | 29.90 | 0/551 | T1R45 |
| 045 | 527 | 17.6 | 29.92 | 0/526 | T1R46 |
| 046 | 605 | 20.2 | 29.92 | 0/604 | T1R47 |
| 047 | 579 | 19.3 | 29.90 | 0/578 | T1R48 |

```
Cadence summary — whole run, 25 episodes · target 30 Hz (33.3 ms budget per tick): 13472 ticks, 13447 judged
  effective cadence: 29.91 Hz over 449.5 s measured
  ticks over the 33.3 ms work budget: 0/13447 (0.0%) — work mean 2.8 ms, worst 27.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 246
  loop-body steps (share of measured work):
    observe      mean   1.23 ms · worst  24.89 ms ·  44.7% of work · 13472 calls
    process_obs  mean   0.03 ms · worst   0.57 ms ·   1.0% of work · 13472 calls
    teleop       mean   1.09 ms · worst  22.68 ms ·  39.7% of work · 13472 calls
    send         mean   0.21 ms · worst   3.89 ms ·   7.6% of work · 13472 calls
    record       mean   0.15 ms · worst   2.35 ms ·   5.5% of work · 13472 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.6 ms) — near zero means the loop is saturated
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

### 2026-10-23 11:15 · 이어 찍기 <!-- run:20261023_111528 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T1R49 · 1개 · 빨강 — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_111528.log`
- 목표: 유효 64편 (계획 줄 68 = 유효 64 + 제외 4) · 실행 전 48편 · 남은 20편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 48=T1R49, 49=T1R50, 50=T1R51, 51=T1R52, 52=T1R53, 53=T1R54, 54=T1R55, 55=T1R56, 56=T1R57, 57=T1R58, 58=T1R59, 59=T1R60, 60=T1R61, 61=T1R62, 62=T1R63, 63=T1R64

**결과** <!-- results:20261023_111528 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 11:31
- repo_id: `oxr/so101_k8_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 12번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 529 | 17.6 | 29.92 | 0/528 | T1R49 |
| 049 | 608 | 20.3 | 29.90 | 0/607 | T1R50 |
| 050 | 568 | 18.9 | 29.92 | 0/567 | T1R51 |
| 051 | 398 | 13.3 | 29.93 | 0/397 | T1R52 |
| 052 | 486 | 16.2 | 29.92 | 0/485 | T1R53 |
| 053 | 505 | 16.8 | 29.92 | 0/504 | T1R54 |
| 054 | 475 | 15.8 | 29.92 | 0/474 | T1R55 |
| 055 | 431 | 14.4 | 29.92 | 0/430 | T1R56 |
| 056 | 400 | 13.3 | 29.93 | 0/399 | T1R57 |
| 057 | 489 | 16.3 | 29.91 | 0/488 | T1R58 |
| 058 | 490 | 16.3 | 29.91 | 0/489 | T1R59 |
| 059 | 470 | 15.7 | 29.91 | 0/469 | T1R60 |
| 060 | 407 | 13.6 | 29.93 | 0/406 | T1R61 |
| 061 | 637 | 21.2 | 29.92 | 0/636 | T1R62 |
| 062 | 532 | 17.7 | 29.91 | 0/531 | T1R63 |
| 063 | 506 | 16.9 | 29.92 | 0/505 | T1R64 |

```
Cadence summary — whole run, 28 episodes · target 30 Hz (33.3 ms budget per tick): 12356 ticks, 12328 judged
  effective cadence: 29.92 Hz over 412.1 s measured
  ticks over the 33.3 ms work budget: 0/12328 (0.0%) — work mean 2.7 ms, worst 27.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 199
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst  20.40 ms ·  44.7% of work · 12356 calls
    process_obs  mean   0.03 ms · worst   4.17 ms ·   1.0% of work · 12356 calls
    teleop       mean   1.08 ms · worst   6.19 ms ·  39.8% of work · 12356 calls
    send         mean   0.20 ms · worst  23.93 ms ·   7.5% of work · 12356 calls
    record       mean   0.15 ms · worst   2.42 ms ·   5.5% of work · 12356 calls
  pacing headroom: 30.7 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
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

### 2026-10-23 12:53 · 이어 찍기 <!-- run:20261023_125328 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 64) 배치 T1R03 · 1개 · 빨강 — 서로 닿지 않게 (중심 3.5 cm 넘게) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_random/dataset --dataset.num_episodes=4
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_125328.log`
- 목표: 유효 64편 (계획 줄 68 = 유효 64 + 제외 4) · 실행 전 64편 · 남은 4편 · 이번 num_episodes=4
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_random/layout.csv` (그룹 `t1_random`) · 이번 실행 배치 64=T1R03, 65=T1R37, 66=T1R40, 67=T1R42

**결과** <!-- results:20261023_125328 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 12:57
- repo_id: `oxr/so101_k8_redbox_t1_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 4개 (episode 64–67) · 전체 68개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 064 | 710 | 23.7 | 29.92 | 0/709 | T1R03 |
| 065 | 598 | 19.9 | 29.92 | 0/597 | T1R37 |
| 066 | 776 | 25.9 | 29.92 | 0/775 | T1R40 |
| 067 | 536 | 17.9 | 29.90 | 0/535 | T1R42 |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 2779 ticks, 2774 judged
  effective cadence: 29.92 Hz over 92.7 s measured
  ticks over the 33.3 ms work budget: 0/2774 (0.0%) — work mean 2.8 ms, worst 16.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 42
  loop-body steps (share of measured work):
    observe      mean   1.25 ms · worst   7.85 ms ·  44.5% of work · 2779 calls
    process_obs  mean   0.03 ms · worst   0.33 ms ·   1.0% of work · 2779 calls
    teleop       mean   1.11 ms · worst   7.51 ms ·  39.6% of work · 2779 calls
    send         mean   0.22 ms · worst   3.23 ms ·   7.9% of work · 2779 calls
    record       mean   0.15 ms · worst   1.85 ms ·   5.5% of work · 2779 calls
  pacing headroom: 30.6 ms slept per tick on average (max 32.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 064 | | |
| 065 | | |
| 066 | | |
| 067 | | |
