# redbox_t1_known (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/redbox_t1_known`
- dataset: `$HOME/so101_runs/main_k8/redbox_t1_known/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-22

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-22 15:37 · 새 녹화 <!-- run:20261022_153723 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1K7 · 1개 · K1() · K2() · K3() · K4() · K5() · K6() · K7(빨강 45°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_153723.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 0=T1K7, 1=T1K5, 2=T1K4, 3=T1K3, 4=T1K1, 5=T1K2, 6=T1K8, 7=T1K6, 8=T1K4, 9=T1K6, 10=T1K8, 11=T1K1, 12=T1K7, 13=T1K2, 14=T1K5, 15=T1K3

**결과** <!-- results:20261022_153723 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 15:52
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 8번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 662 | 22.1 | 29.91 | 0/661 | T1K7 |
| 001 | 612 | 20.4 | 29.91 | 0/611 | T1K5 |
| 002 | 692 | 23.1 | 29.90 | 0/691 | T1K4 |
| 003 | 631 | 21.0 | 29.93 | 0/630 | T1K3 |
| 004 | 571 | 19.0 | 29.91 | 0/570 | T1K1 |
| 005 | 506 | 16.9 | 29.92 | 0/505 | T1K2 |
| 006 | 632 | 21.1 | 29.93 | 0/631 | T1K8 |
| 007 | 497 | 16.6 | 29.93 | 0/496 | T1K6 |
| 008 | 445 | 14.8 | 29.92 | 0/444 | T1K4 |
| 009 | 467 | 15.6 | 29.93 | 0/466 | T1K6 |
| 010 | 575 | 19.2 | 29.92 | 0/574 | T1K8 |
| 011 | 476 | 15.9 | 29.91 | 0/475 | T1K1 |
| 012 | 523 | 17.4 | 29.91 | 0/522 | T1K7 |
| 013 | 454 | 15.1 | 29.92 | 0/453 | T1K2 |
| 014 | 459 | 15.3 | 29.92 | 0/458 | T1K5 |
| 015 | 488 | 16.3 | 29.90 | 0/487 | T1K3 |

```
Cadence summary — whole run, 24 episodes · target 30 Hz (33.3 ms budget per tick): 13336 ticks, 13312 judged
  effective cadence: 29.92 Hz over 445.0 s measured
  ticks over the 33.3 ms work budget: 0/13312 (0.0%) — work mean 2.7 ms, worst 22.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 204
  loop-body steps (share of measured work):
    observe      mean   1.22 ms · worst  19.31 ms ·  44.6% of work · 13336 calls
    process_obs  mean   0.03 ms · worst   0.61 ms ·   1.0% of work · 13336 calls
    teleop       mean   1.09 ms · worst   4.51 ms ·  39.8% of work · 13336 calls
    send         mean   0.21 ms · worst   3.77 ms ·   7.7% of work · 13336 calls
    record       mean   0.15 ms · worst   2.45 ms ·   5.4% of work · 13336 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.0 ms) — near zero means the loop is saturated
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

### 2026-10-22 16:10 · 이어 찍기 <!-- run:20261022_161052 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T1K5 · 1개 · K1() · K2() · K3() · K4() · K5(빨강 0°) · K6() · K7() · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_161052.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 16=T1K5, 17=T1K3, 18=T1K1, 19=T1K8, 20=T1K4, 21=T1K7, 22=T1K6, 23=T1K2, 24=T1K1, 25=T1K6, 26=T1K4, 27=T1K3, 28=T1K8, 29=T1K2, 30=T1K5, 31=T1K7

**결과** <!-- results:20261022_161052 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 16:22
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 358 | 11.9 | 29.93 | 0/357 | T1K5 |
| 017 | 526 | 17.5 | 29.92 | 0/525 | T1K3 |
| 018 | 566 | 18.9 | 29.91 | 0/565 | T1K1 |
| 019 | 525 | 17.5 | 29.92 | 0/524 | T1K8 |
| 020 | 483 | 16.1 | 29.93 | 0/482 | T1K4 |
| 021 | 433 | 14.4 | 29.93 | 0/432 | T1K7 |
| 022 | 463 | 15.4 | 29.93 | 0/462 | T1K6 |
| 023 | 542 | 18.1 | 29.93 | 0/541 | T1K2 |
| 024 | 508 | 16.9 | 29.92 | 0/507 | T1K1 |
| 025 | 504 | 16.8 | 29.90 | 0/503 | T1K6 |
| 026 | 524 | 17.5 | 29.93 | 0/523 | T1K4 |
| 027 | 572 | 19.1 | 29.92 | 0/571 | T1K3 |
| 028 | 618 | 20.6 | 29.91 | 0/617 | T1K8 |
| 029 | 504 | 16.8 | 29.93 | 0/503 | T1K2 |
| 030 | 484 | 16.1 | 29.92 | 0/483 | T1K5 |
| 031 | 526 | 17.5 | 29.92 | 0/525 | T1K7 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 8653 ticks, 8634 judged
  effective cadence: 29.92 Hz over 288.6 s measured
  ticks over the 33.3 ms work budget: 0/8634 (0.0%) — work mean 2.7 ms, worst 29.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 104
  loop-body steps (share of measured work):
    observe      mean   1.23 ms · worst  24.99 ms ·  44.9% of work · 8653 calls
    process_obs  mean   0.03 ms · worst   0.27 ms ·   1.0% of work · 8653 calls
    teleop       mean   1.08 ms · worst  21.57 ms ·  39.7% of work · 8653 calls
    send         mean   0.21 ms · worst   3.34 ms ·   7.5% of work · 8653 calls
    record       mean   0.15 ms · worst   2.35 ms ·   5.5% of work · 8653 calls
  pacing headroom: 30.7 ms slept per tick on average (max 36.0 ms) — near zero means the loop is saturated
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

### 2026-10-22 17:30 · 이어 찍기 <!-- run:20261022_173011 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T1K1 · 1개 · K1(빨강 45°) · K2() · K3() · K4() · K5() · K6() · K7() · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_173011.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 32=T1K1, 33=T1K8, 34=T1K2, 35=T1K4, 36=T1K7, 37=T1K5, 38=T1K6, 39=T1K3, 40=T1K1, 41=T1K3, 42=T1K7, 43=T1K4, 44=T1K6, 45=T1K2, 46=T1K8, 47=T1K5

**결과** <!-- results:20261022_173011 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 17:42
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 450 | 15.0 | 29.91 | 0/449 | T1K1 |
| 033 | 684 | 22.8 | 29.89 | 0/683 | T1K8 |
| 034 | 380 | 12.7 | 29.91 | 0/379 | T1K2 |
| 035 | 430 | 14.3 | 29.93 | 0/429 | T1K4 |
| 036 | 540 | 18.0 | 29.92 | 0/539 | T1K7 |
| 037 | 401 | 13.4 | 29.93 | 0/400 | T1K5 |
| 038 | 586 | 19.5 | 29.91 | 0/585 | T1K6 |
| 039 | 498 | 16.6 | 29.92 | 0/497 | T1K3 |
| 040 | 505 | 16.8 | 29.93 | 0/504 | T1K1 |
| 041 | 497 | 16.6 | 29.91 | 0/496 | T1K3 |
| 042 | 464 | 15.5 | 29.93 | 0/463 | T1K7 |
| 043 | 448 | 14.9 | 29.92 | 0/447 | T1K4 |
| 044 | 539 | 18.0 | 29.93 | 0/538 | T1K6 |
| 045 | 503 | 16.8 | 29.91 | 0/502 | T1K2 |
| 046 | 570 | 19.0 | 29.92 | 0/569 | T1K8 |
| 047 | 418 | 13.9 | 29.91 | 0/417 | T1K5 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 9120 ticks, 9101 judged
  effective cadence: 29.92 Hz over 304.2 s measured
  ticks over the 33.3 ms work budget: 0/9101 (0.0%) — work mean 2.7 ms, worst 28.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 155
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst  26.58 ms ·  44.8% of work · 9120 calls
    process_obs  mean   0.03 ms · worst   1.24 ms ·   1.0% of work · 9120 calls
    teleop       mean   1.07 ms · worst   4.11 ms ·  39.6% of work · 9120 calls
    send         mean   0.20 ms · worst  25.83 ms ·   7.3% of work · 9120 calls
    record       mean   0.15 ms · worst   2.14 ms ·   5.7% of work · 9120 calls
  pacing headroom: 30.7 ms slept per tick on average (max 33.4 ms) — near zero means the loop is saturated
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

### 2026-10-23 10:36 · 이어 찍기 <!-- run:20261023_103654 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T1K1 · 1개 · K1(빨강 ↻30°) · K2() · K3() · K4() · K5() · K6() · K7() · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_103654.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 48=T1K1, 49=T1K4, 50=T1K2, 51=T1K7, 52=T1K5, 53=T1K6, 54=T1K8, 55=T1K3, 56=T1K6, 57=T1K5, 58=T1K2, 59=T1K8, 60=T1K1, 61=T1K7, 62=T1K4, 63=T1K3

**결과** <!-- results:20261023_103654 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 10:50
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 560 | 18.7 | 29.93 | 0/559 | T1K1 |
| 049 | 609 | 20.3 | 29.92 | 0/608 | T1K4 |
| 050 | 567 | 18.9 | 29.92 | 0/566 | T1K2 |
| 051 | 873 | 29.1 | 29.92 | 0/872 | T1K7 |
| 052 | 550 | 18.3 | 29.91 | 0/549 | T1K5 |
| 053 | 546 | 18.2 | 29.91 | 0/545 | T1K6 |
| 054 | 579 | 19.3 | 29.92 | 0/578 | T1K8 |
| 055 | 606 | 20.2 | 29.91 | 0/605 | T1K3 |
| 056 | 539 | 18.0 | 29.92 | 0/538 | T1K6 |
| 057 | 514 | 17.1 | 29.93 | 0/513 | T1K5 |
| 058 | 525 | 17.5 | 29.91 | 0/524 | T1K2 |
| 059 | 619 | 20.6 | 29.91 | 0/618 | T1K8 |
| 060 | 565 | 18.8 | 29.92 | 0/564 | T1K1 |
| 061 | 567 | 18.9 | 29.92 | 0/566 | T1K7 |
| 062 | 584 | 19.5 | 29.92 | 0/583 | T1K4 |
| 063 | 590 | 19.7 | 29.92 | 0/589 | T1K3 |

```
Cadence summary — whole run, 20 episodes · target 30 Hz (33.3 ms budget per tick): 11178 ticks, 11158 judged
  effective cadence: 29.92 Hz over 373.0 s measured
  ticks over the 33.3 ms work budget: 0/11158 (0.0%) — work mean 2.7 ms, worst 23.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 179
  loop-body steps (share of measured work):
    observe      mean   1.22 ms · worst  22.01 ms ·  44.9% of work · 11178 calls
    process_obs  mean   0.03 ms · worst   1.60 ms ·   1.0% of work · 11178 calls
    teleop       mean   1.08 ms · worst   5.29 ms ·  39.7% of work · 11178 calls
    send         mean   0.20 ms · worst   3.35 ms ·   7.5% of work · 11178 calls
    record       mean   0.15 ms · worst   1.70 ms ·   5.5% of work · 11178 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.1 ms) — near zero means the loop is saturated
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

### 2026-10-23 10:58 · 이어 찍기 <!-- run:20261023_105805 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 64) 배치 T1K7 · 1개 · K1() · K2() · K3() · K4() · K5() · K6() · K7(빨강 ↺30°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset --dataset.num_episodes=1
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_105805.log`
- 목표: 유효 64편 (계획 줄 65 = 유효 64 + 제외 1) · 실행 전 64편 · 남은 1편 · 이번 num_episodes=1
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 64=T1K7

**결과** <!-- results:20261023_105805 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 10:59
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 1개 (episode 64–64) · 전체 65개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 064 | 724 | 24.1 | 29.90 | 0/723 | T1K7 |

```
Cadence summary — whole run, 1 episode · target 30 Hz (33.3 ms budget per tick): 724 ticks, 723 judged
  effective cadence: 29.90 Hz over 24.2 s measured
  ticks over the 33.3 ms work budget: 0/723 (0.0%) — work mean 2.7 ms, worst 5.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 17
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst   3.58 ms ·  44.4% of work · 724 calls
    process_obs  mean   0.03 ms · worst   1.73 ms ·   1.2% of work · 724 calls
    teleop       mean   1.09 ms · worst   3.11 ms ·  39.7% of work · 724 calls
    send         mean   0.20 ms · worst   2.70 ms ·   7.4% of work · 724 calls
    record       mean   0.16 ms · worst   1.13 ms ·   5.7% of work · 724 calls
  pacing headroom: 30.7 ms slept per tick on average (max 33.5 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 064 | | |

### 2026-10-23 11:03 · 이어 찍기 <!-- run:20261023_110350 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 65) 배치 T1K7 · 1개 · K1() · K2() · K3() · K4() · K5() · K6() · K7(빨강 ↺30°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main_k8/redbox_t1_known/dataset --dataset.num_episodes=1
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_110350.log`
- 목표: 유효 64편 (계획 줄 66 = 유효 64 + 제외 2) · 실행 전 65편 · 남은 1편 · 이번 num_episodes=1
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t1_known/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 65=T1K7

**결과** <!-- results:20261023_110350 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 11:05
- repo_id: `oxr/so101_k8_redbox_t1_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 1개 (episode 65–65) · 전체 66개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 065 | 715 | 23.8 | 29.91 | 0/714 | T1K7 |

```
Cadence summary — whole run, 2 episodes · target 30 Hz (33.3 ms budget per tick): 1470 ticks, 1468 judged
  effective cadence: 29.91 Hz over 49.1 s measured
  ticks over the 33.3 ms work budget: 0/1468 (0.0%) — work mean 2.7 ms, worst 23.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 38
  loop-body steps (share of measured work):
    observe      mean   1.22 ms · worst  21.77 ms ·  44.9% of work · 1470 calls
    process_obs  mean   0.03 ms · worst   0.09 ms ·   1.0% of work · 1470 calls
    teleop       mean   1.07 ms · worst   3.68 ms ·  39.6% of work · 1470 calls
    send         mean   0.20 ms · worst   2.91 ms ·   7.4% of work · 1470 calls
    record       mean   0.15 ms · worst   0.71 ms ·   5.6% of work · 1470 calls
  pacing headroom: 30.7 ms slept per tick on average (max 32.3 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 065 | | |
