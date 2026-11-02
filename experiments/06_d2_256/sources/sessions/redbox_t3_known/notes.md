# redbox_t3_known (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/redbox_t3_known`
- dataset: `$HOME/so101_runs/main_k8/redbox_t3_known/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-23

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-23 13:33 · 새 녹화 <!-- run:20261023_133302 -->

> ⚠ **중단 — 저장 0편.** 팔로워 연결(configure) 중 4번 모터(wrist_flex) 응답 이상 (`Failed to write 'Lock' on id_=4 … Incorrect status packet`, 종료 코드 1). 녹화 시작 전 실패. lerobot 이 남긴 빈 dataset(에피소드 0개, meta/info.json 만)은 `dataset_empty_20261023_1333/` 로 이름만 바꿈 (다음 첫 실행을 위해), 실행 기록(json·log)은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-23).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3K1-Y2B4O7 · 4개 · K1(빨강 45°) · K2(노랑 0°) · K3() · K4(파랑 45°) · K5() · K6() · K7(주황 ↺30°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_133302.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 0=T3K1-Y2B4O7, 1=T3K6-O2G4, 2=T3K3-O4, 3=T3K8-O1G3Y7, 4=T3K7-Y1O8, 5=T3K4-B2, 6=T3K2-B3G4, 7=T3K5-G1O6G8, 8=T3K6-Y1Y2, 9=T3K4-B1O5Y8, 10=T3K7-B8, 11=T3K8-G1O2O7, 12=T3K3-O2O5, 13=T3K5-G3, 14=T3K1-Y6O7, 15=T3K2-O3B5G8

### 2026-10-23 13:36 · 새 녹화 <!-- run:20261023_133649 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3K1-Y2B4O7 · 4개 · K1(빨강 45°) · K2(노랑 0°) · K3() · K4(파랑 45°) · K5() · K6() · K7(주황 ↺30°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_133649.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 0=T3K1-Y2B4O7, 1=T3K6-O2G4, 2=T3K3-O4, 3=T3K8-O1G3Y7, 4=T3K7-Y1O8, 5=T3K4-B2, 6=T3K2-B3G4, 7=T3K5-G1O6G8, 8=T3K6-Y1Y2, 9=T3K4-B1O5Y8, 10=T3K7-B8, 11=T3K8-G1O2O7, 12=T3K3-O2O5, 13=T3K5-G3, 14=T3K1-Y6O7, 15=T3K2-O3B5G8

**결과** <!-- results:20261023_133649 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 13:51
- repo_id: `oxr/so101_k8_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 6번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 422 | 14.1 | 29.91 | 0/421 | T3K1-Y2B4O7 |
| 001 | 430 | 14.3 | 29.91 | 0/429 | T3K6-O2G4 |
| 002 | 449 | 15.0 | 29.91 | 0/448 | T3K3-O4 |
| 003 | 463 | 15.4 | 29.93 | 0/462 | T3K8-O1G3Y7 |
| 004 | 605 | 20.2 | 29.90 | 0/604 | T3K7-Y1O8 |
| 005 | 391 | 13.0 | 29.91 | 0/390 | T3K4-B2 |
| 006 | 406 | 13.5 | 29.92 | 0/405 | T3K2-B3G4 |
| 007 | 376 | 12.5 | 29.92 | 0/375 | T3K5-G1O6G8 |
| 008 | 426 | 14.2 | 29.90 | 0/425 | T3K6-Y1Y2 |
| 009 | 525 | 17.5 | 29.91 | 0/524 | T3K4-B1O5Y8 |
| 010 | 538 | 17.9 | 29.90 | 0/537 | T3K7-B8 |
| 011 | 520 | 17.3 | 29.92 | 0/519 | T3K8-G1O2O7 |
| 012 | 407 | 13.6 | 29.93 | 0/406 | T3K3-O2O5 |
| 013 | 347 | 11.6 | 29.91 | 0/346 | T3K5-G3 |
| 014 | 492 | 16.4 | 29.93 | 0/491 | T3K1-Y6O7 |
| 015 | 476 | 15.9 | 29.92 | 0/475 | T3K2-O3B5G8 |

```
Cadence summary — whole run, 22 episodes · target 30 Hz (33.3 ms budget per tick): 9280 ticks, 9258 judged
  effective cadence: 29.92 Hz over 309.5 s measured
  ticks over the 33.3 ms work budget: 0/9258 (0.0%) — work mean 2.7 ms, worst 18.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 148
  loop-body steps (share of measured work):
    observe      mean   1.23 ms · worst  16.52 ms ·  44.9% of work · 9280 calls
    process_obs  mean   0.03 ms · worst   0.38 ms ·   1.0% of work · 9280 calls
    teleop       mean   1.08 ms · worst   5.27 ms ·  39.6% of work · 9280 calls
    send         mean   0.21 ms · worst   4.54 ms ·   7.6% of work · 9280 calls
    record       mean   0.15 ms · worst   2.44 ms ·   5.5% of work · 9280 calls
  pacing headroom: 30.7 ms slept per tick on average (max 35.5 ms) — near zero means the loop is saturated
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

### 2026-10-23 14:45 · 이어 찍기 <!-- run:20261023_144550 -->

> ⚠ **중단 — 저장 0편.** 이어 찍기 시작 때 팔로워 연결(configure) 중 3번 모터(elbow_flex) 응답 이상 (`Failed to write 'Lock' on id_=3 … Incorrect status packet`, 종료 코드 1). 녹화 시작 전 실패 — 기존 16편은 그대로 (파일 변경 없음 확인). 실행 기록(json·log)은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-23).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T3K8-G6Y7 · 3개 · K1() · K2() · K3() · K4() · K5() · K6(초록 ↺30°) · K7(노랑 0°) · K8(빨강 ↺30°) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_144550.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 16=T3K8-G6Y7, 17=T3K4-G2B3B7, 18=T3K1-Y3B6G7, 19=T3K7-B6, 20=T3K5-G7O8, 21=T3K3-Y6, 22=T3K2-O3Y7, 23=T3K6-O2Y7Y8, 24=T3K2-B1G8, 25=T3K6-G1Y4O8, 26=T3K8-Y7, 27=T3K5-B3Y4, 28=T3K7-G1Y3G5, 29=T3K1-G8, 30=T3K3-B4O5G8, 31=T3K4-Y3B5

### 2026-10-23 14:47 · 이어 찍기 <!-- run:20261023_144753 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T3K8-G6Y7 · 3개 · K1() · K2() · K3() · K4() · K5() · K6(초록 ↺30°) · K7(노랑 0°) · K8(빨강 ↺30°) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_144753.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 16=T3K8-G6Y7, 17=T3K4-G2B3B7, 18=T3K1-Y3B6G7, 19=T3K7-B6, 20=T3K5-G7O8, 21=T3K3-Y6, 22=T3K2-O3Y7, 23=T3K6-O2Y7Y8, 24=T3K2-B1G8, 25=T3K6-G1Y4O8, 26=T3K8-Y7, 27=T3K5-B3Y4, 28=T3K7-G1Y3G5, 29=T3K1-G8, 30=T3K3-B4O5G8, 31=T3K4-Y3B5

**결과** <!-- results:20261023_144753 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 15:01
- repo_id: `oxr/so101_k8_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 419 | 14.0 | 29.92 | 0/418 | T3K8-G6Y7 |
| 017 | 453 | 15.1 | 29.92 | 0/452 | T3K4-G2B3B7 |
| 018 | 454 | 15.1 | 29.92 | 0/453 | T3K1-Y3B6G7 |
| 019 | 466 | 15.5 | 29.90 | 0/465 | T3K7-B6 |
| 020 | 564 | 18.8 | 29.93 | 0/563 | T3K5-G7O8 |
| 021 | 446 | 14.9 | 29.92 | 0/445 | T3K3-Y6 |
| 022 | 360 | 12.0 | 29.90 | 0/359 | T3K2-O3Y7 |
| 023 | 513 | 17.1 | 29.90 | 0/512 | T3K6-O2Y7Y8 |
| 024 | 373 | 12.4 | 29.92 | 0/372 | T3K2-B1G8 |
| 025 | 502 | 16.7 | 29.91 | 0/501 | T3K6-G1Y4O8 |
| 026 | 543 | 18.1 | 29.90 | 0/542 | T3K8-Y7 |
| 027 | 497 | 16.6 | 29.92 | 0/496 | T3K5-B3Y4 |
| 028 | 499 | 16.6 | 29.91 | 0/498 | T3K7-G1Y3G5 |
| 029 | 439 | 14.6 | 29.88 | 0/438 | T3K1-G8 |
| 030 | 427 | 14.2 | 29.93 | 0/426 | T3K3-B4O5G8 |
| 031 | 445 | 14.8 | 29.92 | 0/444 | T3K4-Y3B5 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 7652 ticks, 7634 judged
  effective cadence: 29.91 Hz over 255.2 s measured
  ticks over the 33.3 ms work budget: 0/7634 (0.0%) — work mean 2.7 ms, worst 11.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 149
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst   9.82 ms ·  45.0% of work · 7652 calls
    process_obs  mean   0.03 ms · worst   0.47 ms ·   1.0% of work · 7652 calls
    teleop       mean   1.08 ms · worst   3.95 ms ·  39.9% of work · 7652 calls
    send         mean   0.19 ms · worst   3.18 ms ·   7.1% of work · 7652 calls
    record       mean   0.15 ms · worst   1.07 ms ·   5.6% of work · 7652 calls
  pacing headroom: 30.7 ms slept per tick on average (max 33.9 ms) — near zero means the loop is saturated
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

### 2026-10-23 15:35 · 이어 찍기 <!-- run:20261023_153549 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T3K5-Y3G4 · 3개 · K1() · K2() · K3(노랑 ↻30°) · K4(초록 45°) · K5(빨강 ↻30°) · K6() · K7() · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_153549.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 32=T3K5-Y3G4, 33=T3K1-G8, 34=T3K4-B1G5B8, 35=T3K8-Y4O7, 36=T3K6-G3Y4O5, 37=T3K3-G4, 38=T3K2-Y1G7B8, 39=T3K7-Y5Y6, 40=T3K6-B8, 41=T3K1-O3O7G8, 42=T3K8-G3G6, 43=T3K3-O5B8, 44=T3K5-G4O7G8, 45=T3K2-B6, 46=T3K7-O1Y6, 47=T3K4-B1O2Y8

**결과** <!-- results:20261023_153549 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 15:49
- repo_id: `oxr/so101_k8_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 461 | 15.4 | 29.91 | 0/460 | T3K5-Y3G4 |
| 033 | 443 | 14.8 | 29.90 | 0/442 | T3K1-G8 |
| 034 | 426 | 14.2 | 29.93 | 0/425 | T3K4-B1G5B8 |
| 035 | 462 | 15.4 | 29.92 | 0/461 | T3K8-Y4O7 |
| 036 | 419 | 14.0 | 29.92 | 0/418 | T3K6-G3Y4O5 |
| 037 | 447 | 14.9 | 29.93 | 0/446 | T3K3-G4 |
| 038 | 391 | 13.0 | 29.92 | 0/390 | T3K2-Y1G7B8 |
| 039 | 514 | 17.1 | 29.91 | 0/513 | T3K7-Y5Y6 |
| 040 | 523 | 17.4 | 29.91 | 0/522 | T3K6-B8 |
| 041 | 409 | 13.6 | 29.92 | 0/408 | T3K1-O3O7G8 |
| 042 | 655 | 21.8 | 29.92 | 0/654 | T3K8-G3G6 |
| 043 | 449 | 15.0 | 29.92 | 0/448 | T3K3-O5B8 |
| 044 | 397 | 13.2 | 29.92 | 0/396 | T3K5-G4O7G8 |
| 045 | 378 | 12.6 | 29.92 | 0/377 | T3K2-B6 |
| 046 | 387 | 12.9 | 29.93 | 0/386 | T3K7-O1Y6 |
| 047 | 422 | 14.1 | 29.91 | 0/421 | T3K4-B1O2Y8 |

```
Cadence summary — whole run, 19 episodes · target 30 Hz (33.3 ms budget per tick): 8090 ticks, 8071 judged
  effective cadence: 29.92 Hz over 269.8 s measured
  ticks over the 33.3 ms work budget: 0/8071 (0.0%) — work mean 2.7 ms, worst 9.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 110
  loop-body steps (share of measured work):
    observe      mean   1.20 ms · worst   7.48 ms ·  44.6% of work · 8090 calls
    process_obs  mean   0.03 ms · worst   0.48 ms ·   1.0% of work · 8090 calls
    teleop       mean   1.07 ms · worst   5.94 ms ·  40.0% of work · 8090 calls
    send         mean   0.20 ms · worst   3.17 ms ·   7.4% of work · 8090 calls
    record       mean   0.15 ms · worst   1.19 ms ·   5.5% of work · 8090 calls
  pacing headroom: 30.7 ms slept per tick on average (max 34.3 ms) — near zero means the loop is saturated
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

### 2026-10-23 16:23 · 이어 찍기 <!-- run:20261023_162357 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T3K5-G2B7 · 3개 · K1() · K2(초록 45°) · K3() · K4() · K5(빨강 0°) · K6() · K7(파랑 ↺30°) · K8() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261023_162357.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main_k8/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 48=T3K5-G2B7, 49=T3K1-Y8, 50=T3K3-Y4B6O8, 51=T3K4-G1G5B7, 52=T3K2-O6B8, 53=T3K6-Y3, 54=T3K8-B2B3, 55=T3K7-O1B3B5, 56=T3K6-B1O3Y5, 57=T3K5-Y3Y6, 58=T3K3-O8, 59=T3K1-B2G3B5, 60=T3K2-O1Y8, 61=T3K4-O1Y8, 62=T3K7-O2, 63=T3K8-G3B4B5

**결과** <!-- results:20261023_162357 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-23 16:35
- repo_id: `oxr/so101_k8_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 341 | 11.4 | 29.92 | 0/340 | T3K5-G2B7 |
| 049 | 370 | 12.3 | 29.93 | 0/369 | T3K1-Y8 |
| 050 | 368 | 12.3 | 29.93 | 0/367 | T3K3-Y4B6O8 |
| 051 | 387 | 12.9 | 29.93 | 0/386 | T3K4-G1G5B7 |
| 052 | 393 | 13.1 | 29.92 | 0/392 | T3K2-O6B8 |
| 053 | 399 | 13.3 | 29.92 | 0/398 | T3K6-Y3 |
| 054 | 458 | 15.3 | 29.91 | 0/457 | T3K8-B2B3 |
| 055 | 393 | 13.1 | 29.92 | 0/392 | T3K7-O1B3B5 |
| 056 | 388 | 12.9 | 29.90 | 0/387 | T3K6-B1O3Y5 |
| 057 | 444 | 14.8 | 29.93 | 0/443 | T3K5-Y3Y6 |
| 058 | 466 | 15.5 | 29.90 | 0/465 | T3K3-O8 |
| 059 | 375 | 12.5 | 29.93 | 0/374 | T3K1-B2G3B5 |
| 060 | 402 | 13.4 | 29.92 | 0/401 | T3K2-O1Y8 |
| 061 | 407 | 13.6 | 29.91 | 0/406 | T3K4-O1Y8 |
| 062 | 409 | 13.6 | 29.91 | 0/408 | T3K7-O2 |
| 063 | 394 | 13.1 | 29.93 | 0/393 | T3K8-G3B4B5 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 6962 ticks, 6944 judged
  effective cadence: 29.92 Hz over 232.1 s measured
  ticks over the 33.3 ms work budget: 0/6944 (0.0%) — work mean 2.7 ms, worst 25.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 88
  loop-body steps (share of measured work):
    observe      mean   1.21 ms · worst   4.36 ms ·  44.7% of work · 6962 calls
    process_obs  mean   0.03 ms · worst   0.50 ms ·   1.0% of work · 6962 calls
    teleop       mean   1.08 ms · worst   6.29 ms ·  40.1% of work · 6962 calls
    send         mean   0.20 ms · worst  21.96 ms ·   7.4% of work · 6962 calls
    record       mean   0.14 ms · worst   2.12 ms ·   5.3% of work · 6962 calls
  pacing headroom: 30.7 ms slept per tick on average (max 35.9 ms) — near zero means the loop is saturated
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
