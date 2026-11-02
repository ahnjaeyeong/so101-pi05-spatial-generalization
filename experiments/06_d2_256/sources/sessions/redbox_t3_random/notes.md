# redbox_t3_random (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/redbox_t3_random`
- dataset: `$HOME/so101_runs/main_k8/redbox_t3_random/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-23

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-23 14:01 · 새 녹화 <!-- run:20261023_140158 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3R01-YYOBG · 6개 · 빨강 · 노랑 노랑 · 주황 · 파랑 · 초록 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_140158.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 0=T3R01-YYOBG, 1=T3R02-YYGG, 2=T3R03-YOB, 3=T3R04-OB, 4=T3R05-YYOOOG, 5=T3R06-OBBGGG, 6=T3R07-YOBBG, 7=T3R08-YOG, 8=T3R09-OBGG, 9=T3R10-OB, 10=T3R11-YBGG, 11=T3R12-YOBGG, 12=T3R13-OB, 13=T3R14-YOO, 14=T3R15-YYYOBG, 15=T3R16-YYG

**결과** <!-- results:20261023_140158 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 14:17
- repo_id: `oxr/so101_k8_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 5번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 451 | 15.0 | 29.92 | 0/450 | T3R01-YYOBG |
| 001 | 419 | 14.0 | 29.93 | 0/418 | T3R02-YYGG |
| 002 | 718 | 23.9 | 29.91 | 0/717 | T3R03-YOB |
| 003 | 402 | 13.4 | 29.92 | 0/401 | T3R04-OB |
| 004 | 440 | 14.7 | 29.92 | 0/439 | T3R05-YYOOOG |
| 005 | 441 | 14.7 | 29.92 | 0/440 | T3R06-OBBGGG |
| 006 | 452 | 15.1 | 29.93 | 0/451 | T3R07-YOBBG |
| 007 | 438 | 14.6 | 29.93 | 0/437 | T3R08-YOG |
| 008 | 476 | 15.9 | 29.90 | 0/475 | T3R09-OBGG |
| 009 | 469 | 15.6 | 29.91 | 0/468 | T3R10-OB |
| 010 | 563 | 18.8 | 29.92 | 0/562 | T3R11-YBGG |
| 011 | 453 | 15.1 | 29.91 | 0/452 | T3R12-YOBGG |
| 012 | 399 | 13.3 | 29.91 | 0/398 | T3R13-OB |
| 013 | 482 | 16.1 | 29.92 | 0/481 | T3R14-YOO |
| 014 | 466 | 15.5 | 29.91 | 0/465 | T3R15-YYYOBG |
| 015 | 499 | 16.6 | 29.93 | 0/498 | T3R16-YYG |

```
Cadence summary — whole run, 21 episodes · target 30 Hz (33.3 ms budget per tick): 8987 ticks, 8966 judged
  effective cadence: 29.92 Hz over 299.7 s measured
  ticks over the 33.3 ms work budget: 0/8966 (0.0%) — work mean 2.7 ms, worst 29.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 131
  loop-body steps (share of measured work):
    observe      mean   1.23 ms · worst  26.87 ms ·  45.0% of work · 8987 calls
    process_obs  mean   0.03 ms · worst   1.11 ms ·   1.0% of work · 8987 calls
    teleop       mean   1.09 ms · worst   4.25 ms ·  39.8% of work · 8987 calls
    send         mean   0.20 ms · worst   4.63 ms ·   7.3% of work · 8987 calls
    record       mean   0.15 ms · worst   2.39 ms ·   5.5% of work · 8987 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.5 ms) — near zero means the loop is saturated
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

### 2026-10-23 15:05 · 이어 찍기 <!-- run:20261023_150552 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T3R17-YYOOOB · 7개 · 빨강 · 노랑 노랑 · 주황 주황 주황 · 파랑 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_150552.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 16=T3R17-YYOOOB, 17=T3R18-YOOB, 18=T3R19-OOBBB, 19=T3R20-YG, 20=T3R21-OOOB, 21=T3R22-GG, 22=T3R23-YYYOO, 23=T3R24-YYYBGG, 24=T3R25-YYB, 25=T3R26-OBBG, 26=T3R27-OOB, 27=T3R28-YBBGG, 28=T3R29-YYOOGG, 29=T3R30-YG, 30=T3R31-YBB, 31=T3R32-OOBGGG

**결과** <!-- results:20261023_150552 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 15:26
- repo_id: `oxr/so101_k8_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 21번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 437 | 14.6 | 29.92 | 0/436 | T3R17-YYOOOB |
| 017 | 421 | 14.0 | 29.92 | 0/420 | T3R18-YOOB |
| 018 | 424 | 14.1 | 29.93 | 0/423 | T3R19-OOBBB |
| 019 | 407 | 13.6 | 29.94 | 0/406 | T3R20-YG |
| 020 | 444 | 14.8 | 29.93 | 0/443 | T3R21-OOOB |
| 021 | 436 | 14.5 | 29.91 | 0/435 | T3R22-GG |
| 022 | 423 | 14.1 | 29.93 | 0/422 | T3R23-YYYOO |
| 023 | 443 | 14.8 | 29.93 | 0/442 | T3R24-YYYBGG |
| 024 | 482 | 16.1 | 29.92 | 0/481 | T3R25-YYB |
| 025 | 516 | 17.2 | 29.91 | 0/515 | T3R26-OBBG |
| 026 | 582 | 19.4 | 29.91 | 0/581 | T3R27-OOB |
| 027 | 522 | 17.4 | 29.92 | 0/521 | T3R28-YBBGG |
| 028 | 444 | 14.8 | 29.92 | 0/443 | T3R29-YYOOGG |
| 029 | 468 | 15.6 | 29.90 | 0/467 | T3R30-YG |
| 030 | 400 | 13.3 | 29.92 | 0/399 | T3R31-YBB |
| 031 | 669 | 22.3 | 29.91 | 0/668 | T3R32-OOBGGG |

```
Cadence summary — whole run, 37 episodes · target 30 Hz (33.3 ms budget per tick): 13529 ticks, 13492 judged
  effective cadence: 29.92 Hz over 451.0 s measured
  ticks over the 33.3 ms work budget: 0/13492 (0.0%) — work mean 2.7 ms, worst 19.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 197
  loop-body steps (share of measured work):
    observe      mean   1.24 ms · worst  17.76 ms ·  45.1% of work · 13529 calls
    process_obs  mean   0.03 ms · worst   2.57 ms ·   1.0% of work · 13529 calls
    teleop       mean   1.08 ms · worst   3.98 ms ·  39.5% of work · 13529 calls
    send         mean   0.20 ms · worst   3.64 ms ·   7.4% of work · 13529 calls
    record       mean   0.15 ms · worst   1.85 ms ·   5.5% of work · 13529 calls
  pacing headroom: 30.7 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
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

### 2026-10-23 16:03 · 이어 찍기 <!-- run:20261023_160312 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T3R33-YOOBG · 6개 · 빨강 · 노랑 · 주황 주황 · 파랑 · 초록 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_160312.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 32=T3R33-YOOBG, 33=T3R34-YYBB, 34=T3R35-YY, 35=T3R36-OOBBG, 36=T3R37-YOB, 37=T3R38-YOBBBG, 38=T3R39-YOBB, 39=T3R40-YOOBGG, 40=T3R41-OB, 41=T3R42-YBBB, 42=T3R43-YYO, 43=T3R44-YOBBG, 44=T3R45-YYG, 45=T3R46-YOOBGG, 46=T3R47-OOGG, 47=T3R48-YG

**결과** <!-- results:20261023_160312 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 16:20
- repo_id: `oxr/so101_k8_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 517 | 17.2 | 29.92 | 0/516 | T3R33-YOOBG |
| 033 | 647 | 21.6 | 29.92 | 0/646 | T3R34-YYBB |
| 034 | 427 | 14.2 | 29.92 | 0/426 | T3R35-YY |
| 035 | 435 | 14.5 | 29.93 | 0/434 | T3R36-OOBBG |
| 036 | 403 | 13.4 | 29.93 | 0/402 | T3R37-YOB |
| 037 | 339 | 11.3 | 29.92 | 0/338 | T3R38-YOBBBG |
| 038 | 554 | 18.5 | 29.91 | 0/553 | T3R39-YOBB |
| 039 | 407 | 13.6 | 29.92 | 0/406 | T3R40-YOOBGG |
| 040 | 385 | 12.8 | 29.92 | 0/384 | T3R41-OB |
| 041 | 419 | 14.0 | 29.92 | 0/418 | T3R42-YBBB |
| 042 | 415 | 13.8 | 29.92 | 0/414 | T3R43-YYO |
| 043 | 484 | 16.1 | 29.93 | 0/483 | T3R44-YOBBG |
| 044 | 665 | 22.2 | 29.91 | 0/664 | T3R45-YYG |
| 045 | 453 | 15.1 | 29.91 | 0/452 | T3R46-YOOBGG |
| 046 | 341 | 11.4 | 29.93 | 0/340 | T3R47-OOGG |
| 047 | 449 | 15.0 | 29.93 | 0/448 | T3R48-YG |

```
Cadence summary — whole run, 20 episodes · target 30 Hz (33.3 ms budget per tick): 8761 ticks, 8741 judged
  effective cadence: 29.92 Hz over 292.1 s measured
  ticks over the 33.3 ms work budget: 0/8741 (0.0%) — work mean 2.7 ms, worst 23.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 110
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst   5.29 ms ·  45.0% of work · 8761 calls
    process_obs  mean   0.03 ms · worst   1.11 ms ·   1.0% of work · 8761 calls
    teleop       mean   1.08 ms · worst   4.06 ms ·  39.9% of work · 8761 calls
    send         mean   0.20 ms · worst  19.92 ms ·   7.3% of work · 8761 calls
    record       mean   0.15 ms · worst   1.67 ms ·   5.4% of work · 8761 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.0 ms) — near zero means the loop is saturated
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

### 2026-10-23 16:47 · 이어 찍기 <!-- run:20261023_164750 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T3R49-OOBBG · 6개 · 빨강 · 주황 주황 · 파랑 파랑 · 초록 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_164750.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 48=T3R49-OOBBG, 49=T3R50-YYBBG, 50=T3R51-YY, 51=T3R52-YYOOBG, 52=T3R53-YOBG, 53=T3R54-YBB, 54=T3R55-OBGGG, 55=T3R56-OG, 56=T3R57-YOOG, 57=T3R58-YYBBGG, 58=T3R59-BBB, 59=T3R60-OGGG, 60=T3R61-GGG, 61=T3R62-YOBGGG, 62=T3R63-YOOBG, 63=T3R64-OB

**결과** <!-- results:20261023_164750 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 17:05
- repo_id: `oxr/so101_k8_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 8번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 324 | 10.8 | 29.92 | 0/323 | T3R49-OOBBG |
| 049 | 318 | 10.6 | 29.92 | 0/317 | T3R50-YYBBG |
| 050 | 379 | 12.6 | 29.92 | 0/378 | T3R51-YY |
| 051 | 346 | 11.5 | 29.92 | 0/345 | T3R52-YYOOBG |
| 052 | 340 | 11.3 | 29.92 | 0/339 | T3R53-YOBG |
| 053 | 404 | 13.5 | 29.93 | 0/403 | T3R54-YBB |
| 054 | 428 | 14.3 | 29.90 | 0/427 | T3R55-OBGGG |
| 055 | 343 | 11.4 | 29.91 | 0/342 | T3R56-OG |
| 056 | 370 | 12.3 | 29.93 | 0/369 | T3R57-YOOG |
| 057 | 398 | 13.3 | 29.92 | 0/397 | T3R58-YYBBGG |
| 058 | 343 | 11.4 | 29.92 | 0/342 | T3R59-BBB |
| 059 | 327 | 10.9 | 29.92 | 0/326 | T3R60-OGGG |
| 060 | 358 | 11.9 | 29.91 | 0/357 | T3R61-GGG |
| 061 | 399 | 13.3 | 29.92 | 0/398 | T3R62-YOBGGG |
| 062 | 444 | 14.8 | 29.91 | 0/443 | T3R63-YOOBG |
| 063 | 321 | 10.7 | 29.93 | 0/320 | T3R64-OB |

```
Cadence summary — whole run, 24 episodes · target 30 Hz (33.3 ms budget per tick): 7688 ticks, 7664 judged
  effective cadence: 29.92 Hz over 256.2 s measured
  ticks over the 33.3 ms work budget: 0/7664 (0.0%) — work mean 2.7 ms, worst 7.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 97
  loop-body steps (share of measured work):
    observe      mean   1.20 ms · worst   5.56 ms ·  44.7% of work · 7688 calls
    process_obs  mean   0.03 ms · worst   0.48 ms ·   1.1% of work · 7688 calls
    teleop       mean   1.07 ms · worst   4.74 ms ·  39.9% of work · 7688 calls
    send         mean   0.20 ms · worst   3.35 ms ·   7.3% of work · 7688 calls
    record       mean   0.15 ms · worst   1.83 ms ·   5.6% of work · 7688 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.9 ms) — near zero means the loop is saturated
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

### 2026-10-23 17:15 · 이어 찍기 <!-- run:20261023_171556 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 64) 배치 T3R58-YYBBGG · 7개 · 빨강 · 노랑 노랑 · 파랑 파랑 · 초록 초록 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_random/dataset --dataset.num_episodes=1
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_171556.log`
- 목표: 유효 64편 (계획 줄 65 = 유효 64 + 제외 1) · 실행 전 64편 · 남은 1편 · 이번 num_episodes=1
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 64=T3R58-YYBBGG

**결과** <!-- results:20261023_171556 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 17:16
- repo_id: `oxr/so101_k8_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 1개 (episode 64–64) · 전체 65개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 064 | 490 | 16.3 | 29.92 | 0/489 | T3R58-YYBBGG |

```
Cadence summary — whole run, 2 episodes · target 30 Hz (33.3 ms budget per tick): 566 ticks, 564 judged
  effective cadence: 29.91 Hz over 18.9 s measured
  ticks over the 33.3 ms work budget: 0/564 (0.0%) — work mean 2.7 ms, worst 7.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 7
  loop-body steps (share of measured work):
    observe      mean   1.24 ms · worst   3.92 ms ·  44.9% of work · 566 calls
    process_obs  mean   0.03 ms · worst   0.31 ms ·   1.0% of work · 566 calls
    teleop       mean   1.10 ms · worst   3.34 ms ·  39.8% of work · 566 calls
    send         mean   0.21 ms · worst   3.26 ms ·   7.5% of work · 566 calls
    record       mean   0.15 ms · worst   1.11 ms ·   5.4% of work · 566 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.0 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 064 | | |
