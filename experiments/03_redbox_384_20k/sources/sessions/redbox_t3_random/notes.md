# redbox_t3_random (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t3_random`
- dataset: `$HOME/so101_runs/main/redbox_t3_random/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-15

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-15 15:19 · 새 녹화 <!-- run:20261015_151939 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3R01-OOBG: 자유 배치 (빨간 큐브 1개 · 주황 큐브 2개 · 파란 큐브 1개 · 초록 큐브 1개) — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_random --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_151939.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 0=T3R01-OOBG, 1=T3R02-YOBBGG, 2=T3R03-YOO, 3=T3R04-OOOOG, 4=T3R05-BG, 5=T3R06-OG, 6=T3R07-YYOBGG, 7=T3R08-YYBGG, 8=T3R09-GGG, 9=T3R10-YOBG, 10=T3R11-YYGG, 11=T3R12-YOOBG, 12=T3R13-BBG, 13=T3R14-OBBGGG, 14=T3R15-YG, 15=T3R16-OBBGGG

**결과** <!-- results:20261015_151939 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 15:33
- repo_id: `oxr/so101_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 457 | 15.2 | 29.89 | 0/456 | T3R01-OOBG |
| 001 | 319 | 10.6 | 29.88 | 0/318 | T3R02-YOBBGG |
| 002 | 334 | 11.1 | 29.90 | 0/333 | T3R03-YOO |
| 003 | 300 | 10.0 | 29.89 | 0/299 | T3R04-OOOOG |
| 004 | 359 | 12.0 | 29.90 | 0/358 | T3R05-BG |
| 005 | 318 | 10.6 | 29.90 | 0/317 | T3R06-OG |
| 006 | 357 | 11.9 | 29.88 | 0/356 | T3R07-YYOBGG |
| 007 | 302 | 10.1 | 29.89 | 0/301 | T3R08-YYBGG |
| 008 | 324 | 10.8 | 29.91 | 0/323 | T3R09-GGG |
| 009 | 360 | 12.0 | 29.90 | 0/359 | T3R10-YOBG |
| 010 | 324 | 10.8 | 29.88 | 0/323 | T3R11-YYGG |
| 011 | 393 | 13.1 | 29.89 | 0/392 | T3R12-YOOBG |
| 012 | 362 | 12.1 | 29.91 | 0/361 | T3R13-BBG |
| 013 | 370 | 12.3 | 29.87 | 0/369 | T3R14-OBBGGG |
| 014 | 399 | 13.3 | 29.90 | 0/398 | T3R15-YG |
| 015 | 295 | 9.8 | 29.89 | 0/294 | T3R16-OBBGGG |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 5986 ticks, 5969 judged
  effective cadence: 29.89 Hz over 199.7 s measured
  ticks over the 33.3 ms work budget: 0/5969 (0.0%) — work mean 3.0 ms, worst 12.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 166
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst   9.32 ms ·  44.8% of work · 5986 calls
    process_obs  mean   0.05 ms · worst   0.77 ms ·   1.5% of work · 5986 calls
    teleop       mean   1.13 ms · worst   4.06 ms ·  37.2% of work · 5986 calls
    send         mean   0.24 ms · worst   3.64 ms ·   7.8% of work · 5986 calls
    record       mean   0.21 ms · worst   3.95 ms ·   6.8% of work · 5986 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.6 ms) — near zero means the loop is saturated
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

### 2026-10-15 15:49 · 이어 찍기 <!-- run:20261015_154941 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T3R17-YYOBG: 자유 배치 (빨간 큐브 1개 · 노란 큐브 2개 · 주황 큐브 1개 · 파란 큐브 1개 · 초록 큐브 1개) — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_154941.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 16=T3R17-YYOBG, 17=T3R18-OOOB, 18=T3R19-OB, 19=T3R20-YOB, 20=T3R21-OOB, 21=T3R22-YYOBBG, 22=T3R23-YOBG, 23=T3R24-YYYOG, 24=T3R25-BG, 25=T3R26-YOBBB, 26=T3R27-YOG, 27=T3R28-OO, 28=T3R29-YOBGGG, 29=T3R30-YOBG, 30=T3R31-YOB, 31=T3R32-YYOOG

**결과** <!-- results:20261015_154941 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 16:04
- repo_id: `oxr/so101_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 316 | 10.5 | 29.90 | 0/315 | T3R17-YYOBG |
| 017 | 374 | 12.5 | 29.89 | 0/373 | T3R18-OOOB |
| 018 | 328 | 10.9 | 29.89 | 0/327 | T3R19-OB |
| 019 | 387 | 12.9 | 29.87 | 0/386 | T3R20-YOB |
| 020 | 404 | 13.5 | 29.90 | 0/403 | T3R21-OOB |
| 021 | 402 | 13.4 | 29.90 | 0/401 | T3R22-YYOBBG |
| 022 | 311 | 10.4 | 29.91 | 0/310 | T3R23-YOBG |
| 023 | 323 | 10.8 | 29.90 | 0/322 | T3R24-YYYOG |
| 024 | 359 | 12.0 | 29.90 | 0/358 | T3R25-BG |
| 025 | 469 | 15.6 | 29.90 | 0/468 | T3R26-YOBBB |
| 026 | 366 | 12.2 | 29.89 | 0/365 | T3R27-YOG |
| 027 | 331 | 11.0 | 29.89 | 0/330 | T3R28-OO |
| 028 | 337 | 11.2 | 29.89 | 0/336 | T3R29-YOBGGG |
| 029 | 438 | 14.6 | 29.90 | 0/437 | T3R30-YOBG |
| 030 | 356 | 11.9 | 29.89 | 0/355 | T3R31-YOB |
| 031 | 274 | 9.1 | 29.90 | 0/273 | T3R32-YYOOG |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 6983 ticks, 6964 judged
  effective cadence: 29.89 Hz over 233.0 s measured
  ticks over the 33.3 ms work budget: 0/6964 (0.0%) — work mean 3.0 ms, worst 11.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 160
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst   9.91 ms ·  44.6% of work · 6983 calls
    process_obs  mean   0.05 ms · worst   1.52 ms ·   1.6% of work · 6983 calls
    teleop       mean   1.13 ms · worst   4.02 ms ·  37.3% of work · 6983 calls
    send         mean   0.24 ms · worst   5.82 ms ·   7.9% of work · 6983 calls
    record       mean   0.21 ms · worst   3.49 ms ·   6.8% of work · 6983 calls
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

### 2026-10-15 16:30 · 이어 찍기 <!-- run:20261015_163036 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T3R33-YYBB · 5개 · 빨강 · 노랑 노랑 · 파랑 파랑 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_163036.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 32=T3R33-YYBB, 33=T3R34-YYOBBG, 34=T3R35-YYYOB, 35=T3R36-BBGG, 36=T3R37-OBBGGG, 37=T3R38-YG, 38=T3R39-OOB, 39=T3R40-YY, 40=T3R41-YYO, 41=T3R42-OOBBG, 42=T3R43-YYOGGG, 43=T3R44-OOBG, 44=T3R45-BB, 45=T3R46-YOBB, 46=T3R47-OOBBGG, 47=T3R48-YYOOG

**결과** <!-- results:20261015_163036 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 16:42
- repo_id: `oxr/so101_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 367 | 12.2 | 29.90 | 0/366 | T3R33-YYBB |
| 033 | 403 | 13.4 | 29.90 | 0/402 | T3R34-YYOBBG |
| 034 | 286 | 9.5 | 29.88 | 0/285 | T3R35-YYYOB |
| 035 | 256 | 8.5 | 29.88 | 0/255 | T3R36-BBGG |
| 036 | 387 | 12.9 | 29.90 | 0/386 | T3R37-OBBGGG |
| 037 | 293 | 9.8 | 29.89 | 0/292 | T3R38-YG |
| 038 | 400 | 13.3 | 29.91 | 0/399 | T3R39-OOB |
| 039 | 298 | 9.9 | 29.90 | 0/297 | T3R40-YY |
| 040 | 606 | 20.2 | 29.89 | 0/605 | T3R41-YYO |
| 041 | 357 | 11.9 | 29.90 | 0/356 | T3R42-OOBBG |
| 042 | 280 | 9.3 | 29.91 | 0/279 | T3R43-YYOGGG |
| 043 | 308 | 10.3 | 29.90 | 0/307 | T3R44-OOBG |
| 044 | 252 | 8.4 | 29.91 | 0/251 | T3R45-BB |
| 045 | 332 | 11.1 | 29.89 | 0/331 | T3R46-YOBB |
| 046 | 381 | 12.7 | 29.89 | 0/380 | T3R47-OOBBGG |
| 047 | 297 | 9.9 | 29.88 | 0/296 | T3R48-YYOOG |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 5787 ticks, 5770 judged
  effective cadence: 29.90 Hz over 193.0 s measured
  ticks over the 33.3 ms work budget: 0/5770 (0.0%) — work mean 3.0 ms, worst 17.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 133
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst   6.48 ms ·  44.7% of work · 5787 calls
    process_obs  mean   0.05 ms · worst   0.63 ms ·   1.5% of work · 5787 calls
    teleop       mean   1.13 ms · worst   6.71 ms ·  37.1% of work · 5787 calls
    send         mean   0.24 ms · worst   7.90 ms ·   8.0% of work · 5787 calls
    record       mean   0.20 ms · worst   2.54 ms ·   6.8% of work · 5787 calls
  pacing headroom: 30.4 ms slept per tick on average (max 35.0 ms) — near zero means the loop is saturated
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

### 꼬리표 push (2026-10-15)
- episode 30, 33, 36, 40: 덩어리 가운데 빨강을 긁어서 공간을 확보한 뒤 집음. 데이터는 그대로 두고, 학습이 잘 안 되면 빼 볼 후보.
- 빼고 학습: `python3 $HOME/so101_boxpick/scripts/layout_plan.py train-args --session main/redbox_t3_random --without-tag push`

### 2026-10-15 17:22 · 이어 찍기 <!-- run:20261015_172200 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T3R49-YBG · 4개 · 빨강 · 노랑 · 파랑 · 초록 — 붙여 놓아도 됨 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_random --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_random --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_random/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_172200.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_random/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 48=T3R49-YBG, 49=T3R50-YYOBGG, 50=T3R51-BBB, 51=T3R52-YG, 52=T3R53-OBBG, 53=T3R54-YYOGG, 54=T3R55-YY, 55=T3R56-YOBBG, 56=T3R57-YYYO, 57=T3R58-YYYBBB, 58=T3R59-OBG, 59=T3R60-YOOOOG, 60=T3R61-YBBG, 61=T3R62-YYOBG, 62=T3R63-OG, 63=T3R64-YYO

**결과** <!-- results:20261015_172200 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 17:33
- repo_id: `oxr/so101_redbox_t3_random` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 274 | 9.1 | 29.90 | 0/273 | T3R49-YBG |
| 049 | 377 | 12.6 | 29.91 | 0/376 | T3R50-YYOBGG |
| 050 | 302 | 10.1 | 29.90 | 0/301 | T3R51-BBB |
| 051 | 382 | 12.7 | 29.89 | 0/381 | T3R52-YG |
| 052 | 271 | 9.0 | 29.89 | 0/270 | T3R53-OBBG |
| 053 | 287 | 9.6 | 29.90 | 0/286 | T3R54-YYOGG |
| 054 | 405 | 13.5 | 29.90 | 0/404 | T3R55-YY |
| 055 | 384 | 12.8 | 29.90 | 0/383 | T3R56-YOBBG |
| 056 | 372 | 12.4 | 29.90 | 0/371 | T3R57-YYYO |
| 057 | 285 | 9.5 | 29.89 | 0/284 | T3R58-YYYBBB |
| 058 | 364 | 12.1 | 29.89 | 0/363 | T3R59-OBG |
| 059 | 384 | 12.8 | 29.90 | 0/383 | T3R60-YOOOOG |
| 060 | 339 | 11.3 | 29.90 | 0/338 | T3R61-YBBG |
| 061 | 371 | 12.4 | 29.89 | 0/370 | T3R62-YYOBG |
| 062 | 280 | 9.3 | 29.90 | 0/279 | T3R63-OG |
| 063 | 313 | 10.4 | 29.89 | 0/312 | T3R64-YYO |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 6127 ticks, 6108 judged
  effective cadence: 29.90 Hz over 204.3 s measured
  ticks over the 33.3 ms work budget: 0/6108 (0.0%) — work mean 3.0 ms, worst 28.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 118
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst  26.22 ms ·  45.0% of work · 6127 calls
    process_obs  mean   0.05 ms · worst   1.76 ms ·   1.6% of work · 6127 calls
    teleop       mean   1.12 ms · worst   5.49 ms ·  37.0% of work · 6127 calls
    send         mean   0.23 ms · worst   3.27 ms ·   7.6% of work · 6127 calls
    record       mean   0.21 ms · worst   1.31 ms ·   6.9% of work · 6127 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
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
