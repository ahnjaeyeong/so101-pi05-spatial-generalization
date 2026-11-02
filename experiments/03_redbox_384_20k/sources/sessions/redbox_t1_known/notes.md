# redbox_t1_known (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t1_known`
- dataset: `$HOME/so101_runs/main/redbox_t1_known/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 10:52 · 새 녹화 <!-- run:20261014_105202 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1K1: 빨간 큐브 K1(-20.2,31.5) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_105202.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 0=T1K1, 1=T1K4, 2=T1K2, 3=T1K3, 4=T1K4, 5=T1K3, 6=T1K1, 7=T1K2, 8=T1K4, 9=T1K1, 10=T1K3, 11=T1K2, 12=T1K3, 13=T1K2, 14=T1K1, 15=T1K4

**결과** <!-- results:20261014_105202 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 11:05
- repo_id: `oxr/so101_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 5번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 515 | 17.2 | 29.90 | 0/514 | T1K1 |
| 001 | 472 | 15.7 | 29.90 | 0/471 | T1K4 |
| 002 | 514 | 17.1 | 29.89 | 0/513 | T1K2 |
| 003 | 474 | 15.8 | 29.89 | 0/473 | T1K3 |
| 004 | 509 | 17.0 | 29.90 | 0/508 | T1K4 |
| 005 | 492 | 16.4 | 29.90 | 0/491 | T1K3 |
| 006 | 539 | 18.0 | 29.90 | 0/538 | T1K1 |
| 007 | 529 | 17.6 | 29.90 | 0/528 | T1K2 |
| 008 | 453 | 15.1 | 29.89 | 0/452 | T1K4 |
| 009 | 508 | 16.9 | 29.89 | 0/507 | T1K1 |
| 010 | 479 | 16.0 | 29.90 | 0/478 | T1K3 |
| 011 | 467 | 15.6 | 29.85 | 0/466 | T1K2 |
| 012 | 525 | 17.5 | 29.89 | 0/524 | T1K3 |
| 013 | 518 | 17.3 | 29.91 | 0/517 | T1K2 |
| 014 | 458 | 15.3 | 29.89 | 0/457 | T1K1 |
| 015 | 542 | 18.1 | 29.90 | 0/541 | T1K4 |

```
Cadence summary — whole run, 21 episodes · target 30 Hz (33.3 ms budget per tick): 10641 ticks, 10620 judged
  effective cadence: 29.89 Hz over 355.3 s measured
  ticks over the 33.3 ms work budget: 0/10620 (0.0%) — work mean 3.0 ms, worst 28.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 264
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst  12.45 ms ·  44.8% of work · 10641 calls
    process_obs  mean   0.05 ms · worst   2.20 ms ·   1.5% of work · 10641 calls
    teleop       mean   1.13 ms · worst  25.84 ms ·  37.3% of work · 10641 calls
    send         mean   0.24 ms · worst  20.88 ms ·   7.9% of work · 10641 calls
    record       mean   0.20 ms · worst   2.21 ms ·   6.7% of work · 10641 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.7 ms) — near zero means the loop is saturated
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

### 2026-10-14 13:10 · 이어 찍기 <!-- run:20261014_131003 -->

> ⚠ **중단 — 저장 0편.** 화면 출력이 보이지 않았음 (붙여넣을 때 ```bash 줄이 함께 들어간 것으로 추정). episode 16 녹화 시작 10초 뒤(13:10:26) Ctrl+C 로 멈춤 (종료 코드 -6). dataset 은 16편 그대로이고, 실행 기록은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-14).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T1K2: 빨간 큐브 K2(-16.2,21.3) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_131003.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 16=T1K2, 17=T1K4, 18=T1K1, 19=T1K3, 20=T1K2, 21=T1K1, 22=T1K4, 23=T1K3, 24=T1K1, 25=T1K3, 26=T1K4, 27=T1K2, 28=T1K4, 29=T1K2, 30=T1K1, 31=T1K3

### 2026-10-14 13:11 · 이어 찍기 <!-- run:20261014_131146 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T1K2: 빨간 큐브 K2(-16.2,21.3) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_131146.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 16=T1K2, 17=T1K4, 18=T1K1, 19=T1K3, 20=T1K2, 21=T1K1, 22=T1K4, 23=T1K3, 24=T1K1, 25=T1K3, 26=T1K4, 27=T1K2, 28=T1K4, 29=T1K2, 30=T1K1, 31=T1K3

**결과** <!-- results:20261014_131146 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 13:22
- repo_id: `oxr/so101_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 439 | 14.6 | 29.90 | 0/438 | T1K2 |
| 017 | 444 | 14.8 | 29.90 | 0/443 | T1K4 |
| 018 | 432 | 14.4 | 29.89 | 0/431 | T1K1 |
| 019 | 506 | 16.9 | 29.89 | 0/505 | T1K3 |
| 020 | 443 | 14.8 | 29.90 | 0/442 | T1K2 |
| 021 | 485 | 16.2 | 29.90 | 0/484 | T1K1 |
| 022 | 449 | 15.0 | 29.89 | 0/448 | T1K4 |
| 023 | 418 | 13.9 | 29.89 | 0/417 | T1K3 |
| 024 | 465 | 15.5 | 29.89 | 0/464 | T1K1 |
| 025 | 423 | 14.1 | 29.90 | 0/422 | T1K3 |
| 026 | 393 | 13.1 | 29.90 | 0/392 | T1K4 |
| 027 | 494 | 16.5 | 29.89 | 0/493 | T1K2 |
| 028 | 498 | 16.6 | 29.90 | 0/497 | T1K4 |
| 029 | 497 | 16.6 | 29.90 | 0/496 | T1K2 |
| 030 | 521 | 17.4 | 29.89 | 0/520 | T1K1 |
| 031 | 449 | 15.0 | 29.89 | 0/448 | T1K3 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 8167 ticks, 8149 judged
  effective cadence: 29.90 Hz over 272.6 s measured
  ticks over the 33.3 ms work budget: 0/8149 (0.0%) — work mean 3.0 ms, worst 29.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 180
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst  13.04 ms ·  44.8% of work · 8167 calls
    process_obs  mean   0.05 ms · worst   0.50 ms ·   1.5% of work · 8167 calls
    teleop       mean   1.12 ms · worst  23.67 ms ·  37.2% of work · 8167 calls
    send         mean   0.24 ms · worst   3.50 ms ·   8.0% of work · 8167 calls
    record       mean   0.20 ms · worst   1.96 ms ·   6.7% of work · 8167 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.5 ms) — near zero means the loop is saturated
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

### 2026-10-14 14:02 · 이어 찍기 <!-- run:20261014_140236 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T1K4: 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_140236.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 32=T1K4, 33=T1K2, 34=T1K3, 35=T1K1, 36=T1K4, 37=T1K1, 38=T1K3, 39=T1K2, 40=T1K3, 41=T1K2, 42=T1K4, 43=T1K1, 44=T1K4, 45=T1K1, 46=T1K2, 47=T1K3

**결과** <!-- results:20261014_140236 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 14:12
- repo_id: `oxr/so101_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 431 | 14.4 | 29.89 | 0/430 | T1K4 |
| 033 | 425 | 14.2 | 29.89 | 0/424 | T1K2 |
| 034 | 367 | 12.2 | 29.91 | 0/366 | T1K3 |
| 035 | 432 | 14.4 | 29.90 | 0/431 | T1K1 |
| 036 | 411 | 13.7 | 29.89 | 0/410 | T1K4 |
| 037 | 396 | 13.2 | 29.90 | 0/395 | T1K1 |
| 038 | 409 | 13.6 | 29.90 | 0/408 | T1K3 |
| 039 | 357 | 11.9 | 29.90 | 0/356 | T1K2 |
| 040 | 358 | 11.9 | 29.90 | 0/357 | T1K3 |
| 041 | 392 | 13.1 | 29.90 | 0/391 | T1K2 |
| 042 | 376 | 12.5 | 29.90 | 0/375 | T1K4 |
| 043 | 405 | 13.5 | 29.90 | 0/404 | T1K1 |
| 044 | 370 | 12.3 | 29.90 | 0/369 | T1K4 |
| 045 | 429 | 14.3 | 29.91 | 0/428 | T1K1 |
| 046 | 382 | 12.7 | 29.89 | 0/381 | T1K2 |
| 047 | 426 | 14.2 | 29.90 | 0/425 | T1K3 |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 6581 ticks, 6564 judged
  effective cadence: 29.90 Hz over 219.5 s measured
  ticks over the 33.3 ms work budget: 0/6564 (0.0%) — work mean 3.0 ms, worst 11.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 121
  loop-body steps (share of measured work):
    observe      mean   1.34 ms · worst   9.83 ms ·  44.7% of work · 6581 calls
    process_obs  mean   0.05 ms · worst   1.21 ms ·   1.5% of work · 6581 calls
    teleop       mean   1.12 ms · worst   4.88 ms ·  37.3% of work · 6581 calls
    send         mean   0.24 ms · worst   3.53 ms ·   7.9% of work · 6581 calls
    record       mean   0.20 ms · worst   1.92 ms ·   6.7% of work · 6581 calls
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

### 2026-10-14 15:18 · 이어 찍기 <!-- run:20261014_151851 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T1K4: 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_151851.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 48=T1K4, 49=T1K2, 50=T1K3, 51=T1K1, 52=T1K4, 53=T1K1, 54=T1K3, 55=T1K2, 56=T1K3, 57=T1K1, 58=T1K2, 59=T1K4, 60=T1K3, 61=T1K4, 62=T1K1, 63=T1K2

**결과** <!-- results:20261014_151851 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 15:28
- repo_id: `oxr/so101_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 393 | 13.1 | 29.89 | 0/392 | T1K4 |
| 049 | 366 | 12.2 | 29.89 | 0/365 | T1K2 |
| 050 | 363 | 12.1 | 29.89 | 0/362 | T1K3 |
| 051 | 375 | 12.5 | 29.89 | 0/374 | T1K1 |
| 052 | 409 | 13.6 | 29.90 | 0/408 | T1K4 |
| 053 | 432 | 14.4 | 29.89 | 0/431 | T1K1 |
| 054 | 372 | 12.4 | 29.89 | 0/371 | T1K3 |
| 055 | 416 | 13.9 | 29.90 | 0/415 | T1K2 |
| 056 | 385 | 12.8 | 29.91 | 0/384 | T1K3 |
| 057 | 397 | 13.2 | 29.91 | 0/396 | T1K1 |
| 058 | 437 | 14.6 | 29.91 | 0/436 | T1K2 |
| 059 | 381 | 12.7 | 29.90 | 0/380 | T1K4 |
| 060 | 341 | 11.4 | 29.90 | 0/340 | T1K3 |
| 061 | 372 | 12.4 | 29.91 | 0/371 | T1K4 |
| 062 | 432 | 14.4 | 29.90 | 0/431 | T1K1 |
| 063 | 397 | 13.2 | 29.91 | 0/396 | T1K2 |

```
Cadence summary — whole run, 16 episodes · target 30 Hz (33.3 ms budget per tick): 6268 ticks, 6252 judged
  effective cadence: 29.90 Hz over 209.1 s measured
  ticks over the 33.3 ms work budget: 0/6252 (0.0%) — work mean 3.0 ms, worst 23.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 128
  loop-body steps (share of measured work):
    observe      mean   1.34 ms · worst  20.73 ms ·  44.6% of work · 6268 calls
    process_obs  mean   0.05 ms · worst   0.39 ms ·   1.5% of work · 6268 calls
    teleop       mean   1.12 ms · worst   5.23 ms ·  37.4% of work · 6268 calls
    send         mean   0.23 ms · worst   4.79 ms ·   7.8% of work · 6268 calls
    record       mean   0.20 ms · worst   2.61 ms ·   6.8% of work · 6268 calls
  pacing headroom: 30.4 ms slept per tick on average (max 32.8 ms) — near zero means the loop is saturated
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
