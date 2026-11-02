# redbox_t3_known (main)

- 세션 폴더: `$HOME/so101_runs/main/redbox_t3_known`
- dataset: `$HOME/so101_runs/main/redbox_t3_known/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-15

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-15 14:49 · 새 녹화 <!-- run:20261015_144917 -->

> ⚠ **중단 — 저장 0편.** 팔로워 연결(configure) 중 5번 모터(wrist_roll) 응답 없음 (`Failed to write 'Lock' on id_=5 … no status packet`, 종료 코드 1). 녹화 시작 전 실패. lerobot 이 남긴 빈 dataset(에피소드 0개, meta/info.json 만)은 `dataset_empty_20261015_1449/` 로 이름만 바꿈 (다음 첫 실행을 위해), 실행 기록(json·log)은 `~/.local/state/record_ui/deleted_runs/` 로 옮김 (2026-10-15).

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3K1-O3: 빨간 큐브 K1(-20.2,31.5) · 주황 큐브 K3(-7.8,12.7) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_144917.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 0=T3K1-O3, 1=T3K3-O1Y2B4, 2=T3K2-B3B4, 3=T3K4-Y1B3, 4=T3K3-O1Y2O4, 5=T3K2-O1Y3, 6=T3K4-O1O2Y3, 7=T3K1-Y3, 8=T3K3-B4, 9=T3K2-O1Y3Y4, 10=T3K1-G3Y4, 11=T3K4-Y1O2G3, 12=T3K2-B3O4, 13=T3K4-G1B2, 14=T3K1-Y2B3B4, 15=T3K3-G4

### 2026-10-15 14:54 · 새 녹화 <!-- run:20261015_145404 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3K1-O3: 빨간 큐브 K1(-20.2,31.5) · 주황 큐브 K3(-7.8,12.7) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_known --layout auto --target-episodes 64 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_145404.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 0편 · 남은 64편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 0=T3K1-O3, 1=T3K3-O1Y2B4, 2=T3K2-B3B4, 3=T3K4-Y1B3, 4=T3K3-O1Y2O4, 5=T3K2-O1Y3, 6=T3K4-O1O2Y3, 7=T3K1-Y3, 8=T3K3-B4, 9=T3K2-O1Y3Y4, 10=T3K1-G3Y4, 11=T3K4-Y1O2G3, 12=T3K2-B3O4, 13=T3K4-G1B2, 14=T3K1-Y2B3B4, 15=T3K3-G4

**결과** <!-- results:20261015_145404 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 15:06
- repo_id: `oxr/so101_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 0–15) · 전체 16개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 392 | 13.1 | 29.90 | 0/391 | T3K1-O3 |
| 001 | 373 | 12.4 | 29.91 | 0/372 | T3K3-O1Y2B4 |
| 002 | 315 | 10.5 | 29.91 | 0/314 | T3K2-B3B4 |
| 003 | 333 | 11.1 | 29.91 | 0/332 | T3K4-Y1B3 |
| 004 | 307 | 10.2 | 29.89 | 0/306 | T3K3-O1Y2O4 |
| 005 | 314 | 10.5 | 29.90 | 0/313 | T3K2-O1Y3 |
| 006 | 296 | 9.9 | 29.88 | 0/295 | T3K4-O1O2Y3 |
| 007 | 333 | 11.1 | 29.90 | 0/332 | T3K1-Y3 |
| 008 | 289 | 9.6 | 29.91 | 0/288 | T3K3-B4 |
| 009 | 289 | 9.6 | 29.92 | 0/288 | T3K2-O1Y3Y4 |
| 010 | 336 | 11.2 | 29.89 | 0/335 | T3K1-G3Y4 |
| 011 | 359 | 12.0 | 29.90 | 0/358 | T3K4-Y1O2G3 |
| 012 | 291 | 9.7 | 29.90 | 0/290 | T3K2-B3O4 |
| 013 | 345 | 11.5 | 29.90 | 0/344 | T3K4-G1B2 |
| 014 | 308 | 10.3 | 29.91 | 0/307 | T3K1-Y2B3B4 |
| 015 | 309 | 10.3 | 29.91 | 0/308 | T3K3-G4 |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 5490 ticks, 5473 judged
  effective cadence: 29.90 Hz over 183.0 s measured
  ticks over the 33.3 ms work budget: 0/5473 (0.0%) — work mean 3.0 ms, worst 25.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 103
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst   5.69 ms ·  44.8% of work · 5490 calls
    process_obs  mean   0.05 ms · worst   2.20 ms ·   1.6% of work · 5490 calls
    teleop       mean   1.12 ms · worst   4.18 ms ·  37.2% of work · 5490 calls
    send         mean   0.24 ms · worst  22.52 ms ·   7.9% of work · 5490 calls
    record       mean   0.20 ms · worst   2.32 ms ·   6.7% of work · 5490 calls
  pacing headroom: 30.4 ms slept per tick on average (max 32.7 ms) — near zero means the loop is saturated
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

### 2026-10-15 15:37 · 이어 찍기 <!-- run:20261015_153700 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 16) 배치 T3K1-B2G3Y4 · 4개 · K1(빨강) · K2(파랑) · K3(초록) · K4(노랑) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_153700.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 16편 · 남은 48편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 16=T3K1-B2G3Y4, 17=T3K3-Y1B2, 18=T3K2-G1G3, 19=T3K4-G2, 20=T3K2-B1O3Y4, 21=T3K3-G1, 22=T3K1-Y2B3B4, 23=T3K4-Y1G2, 24=T3K1-O2G3G4, 25=T3K2-B1O3, 26=T3K3-G4, 27=T3K4-G2B3, 28=T3K1-O2G3B4, 29=T3K3-G1, 30=T3K4-G1Y2, 31=T3K2-O1G3B4

**결과** <!-- results:20261015_153700 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 15:46
- repo_id: `oxr/so101_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 16–31) · 전체 32개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 016 | 328 | 10.9 | 29.90 | 0/327 | T3K1-B2G3Y4 |
| 017 | 282 | 9.4 | 29.90 | 0/281 | T3K3-Y1B2 |
| 018 | 248 | 8.3 | 29.90 | 0/247 | T3K2-G1G3 |
| 019 | 278 | 9.3 | 29.89 | 0/277 | T3K4-G2 |
| 020 | 256 | 8.5 | 29.92 | 0/255 | T3K2-B1O3Y4 |
| 021 | 283 | 9.4 | 29.90 | 0/282 | T3K3-G1 |
| 022 | 277 | 9.2 | 29.90 | 0/276 | T3K1-Y2B3B4 |
| 023 | 261 | 8.7 | 29.91 | 0/260 | T3K4-Y1G2 |
| 024 | 289 | 9.6 | 29.91 | 0/288 | T3K1-O2G3G4 |
| 025 | 275 | 9.2 | 29.89 | 0/274 | T3K2-B1O3 |
| 026 | 271 | 9.0 | 29.91 | 0/270 | T3K3-G4 |
| 027 | 256 | 8.5 | 29.90 | 0/255 | T3K4-G2B3 |
| 028 | 288 | 9.6 | 29.89 | 0/287 | T3K1-O2G3B4 |
| 029 | 301 | 10.0 | 29.90 | 0/300 | T3K3-G1 |
| 030 | 278 | 9.3 | 29.90 | 0/277 | T3K4-G1Y2 |
| 031 | 263 | 8.8 | 29.88 | 0/262 | T3K2-O1G3B4 |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 5005 ticks, 4988 judged
  effective cadence: 29.90 Hz over 166.8 s measured
  ticks over the 33.3 ms work budget: 0/4988 (0.0%) — work mean 3.0 ms, worst 16.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 97
  loop-body steps (share of measured work):
    observe      mean   1.35 ms · worst   6.31 ms ·  44.7% of work · 5005 calls
    process_obs  mean   0.05 ms · worst   1.59 ms ·   1.6% of work · 5005 calls
    teleop       mean   1.13 ms · worst   9.47 ms ·  37.3% of work · 5005 calls
    send         mean   0.24 ms · worst   3.74 ms ·   8.0% of work · 5005 calls
    record       mean   0.20 ms · worst   1.60 ms ·   6.7% of work · 5005 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.4 ms) — near zero means the loop is saturated
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

### 2026-10-15 16:10 · 이어 찍기 <!-- run:20261015_161057 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 32) 배치 T3K3-G1G2 · 3개 · K1(초록) · K2(초록) · K3(빨강) · K4() 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_161057.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 32편 · 남은 32편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 32=T3K3-G1G2, 33=T3K1-Y4, 34=T3K4-Y1B2O3, 35=T3K2-G1B3G4, 36=T3K3-O1G2, 37=T3K2-G4, 38=T3K1-Y2O3O4, 39=T3K4-O1G2, 40=T3K1-B2Y3Y4, 41=T3K3-O1, 42=T3K2-B1Y3, 43=T3K4-O3, 44=T3K1-Y2Y3G4, 45=T3K3-G2G4, 46=T3K2-G1O3Y4, 47=T3K4-Y1B2

**결과** <!-- results:20261015_161057 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 16:19
- repo_id: `oxr/so101_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 32–47) · 전체 48개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 032 | 287 | 9.6 | 29.91 | 0/286 | T3K3-G1G2 |
| 033 | 267 | 8.9 | 29.90 | 0/266 | T3K1-Y4 |
| 034 | 225 | 7.5 | 29.86 | 0/224 | T3K4-Y1B2O3 |
| 035 | 313 | 10.4 | 29.90 | 0/312 | T3K2-G1B3G4 |
| 036 | 240 | 8.0 | 29.90 | 0/239 | T3K3-O1G2 |
| 037 | 270 | 9.0 | 29.90 | 0/269 | T3K2-G4 |
| 038 | 263 | 8.8 | 29.90 | 0/262 | T3K1-Y2O3O4 |
| 039 | 273 | 9.1 | 29.89 | 0/272 | T3K4-O1G2 |
| 040 | 322 | 10.7 | 29.89 | 0/321 | T3K1-B2Y3Y4 |
| 041 | 277 | 9.2 | 29.91 | 0/276 | T3K3-O1 |
| 042 | 276 | 9.2 | 29.91 | 0/275 | T3K2-B1Y3 |
| 043 | 272 | 9.1 | 29.90 | 0/271 | T3K4-O3 |
| 044 | 314 | 10.5 | 29.90 | 0/313 | T3K1-Y2Y3G4 |
| 045 | 293 | 9.8 | 29.90 | 0/292 | T3K3-G2G4 |
| 046 | 263 | 8.8 | 29.91 | 0/262 | T3K2-G1O3Y4 |
| 047 | 337 | 11.2 | 29.90 | 0/336 | T3K4-Y1B2 |

```
Cadence summary — whole run, 18 episodes · target 30 Hz (33.3 ms budget per tick): 5094 ticks, 5076 judged
  effective cadence: 29.90 Hz over 169.8 s measured
  ticks over the 33.3 ms work budget: 0/5076 (0.0%) — work mean 3.0 ms, worst 13.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 113
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst   4.97 ms ·  44.7% of work · 5094 calls
    process_obs  mean   0.05 ms · worst   0.59 ms ·   1.5% of work · 5094 calls
    teleop       mean   1.13 ms · worst   4.23 ms ·  37.3% of work · 5094 calls
    send         mean   0.24 ms · worst   6.68 ms ·   7.9% of work · 5094 calls
    record       mean   0.20 ms · worst   1.25 ms ·   6.7% of work · 5094 calls
  pacing headroom: 30.4 ms slept per tick on average (max 33.2 ms) — near zero means the loop is saturated
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

### 2026-10-15 17:03 · 이어 찍기 <!-- run:20261015_170323 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 48) 배치 T3K2-Y4 · 2개 · K1() · K2(빨강) · K3() · K4(노랑) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/redbox_t3_known --layout auto --target-episodes 64 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3_known --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16 --dataset.root=$HOME/so101_runs/main/redbox_t3_known/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261015_170323.log`
- 목표: 유효 64편 (계획 줄 64 = 유효 64 + 제외 0) · 실행 전 48편 · 남은 16편 · 이번 num_episodes=16
- 배치 계획: `$HOME/so101_runs/main/redbox_t3_known/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 48=T3K2-Y4, 49=T3K1-B3O4, 50=T3K3-G1O2G4, 51=T3K4-G1Y3, 52=T3K3-O1B2G4, 53=T3K2-B1O3B4, 54=T3K1-B3O4, 55=T3K4-Y1, 56=T3K3-O1O2Y4, 57=T3K1-O2, 58=T3K4-B2B3, 59=T3K2-B1G4, 60=T3K4-O1B2O3, 61=T3K1-Y2B3O4, 62=T3K2-B3Y4, 63=T3K3-Y1

**결과** <!-- results:20261015_170323 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-15 17:12
- repo_id: `oxr/so101_redbox_t3_known` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 16개 (episode 48–63) · 전체 64개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 048 | 271 | 9.0 | 29.78 | 0/270 | T3K2-Y4 |
| 049 | 329 | 11.0 | 29.84 | 0/328 | T3K1-B3O4 |
| 050 | 304 | 10.1 | 29.90 | 0/303 | T3K3-G1O2G4 |
| 051 | 324 | 10.8 | 29.90 | 0/323 | T3K4-G1Y3 |
| 052 | 307 | 10.2 | 29.91 | 0/306 | T3K3-O1B2G4 |
| 053 | 272 | 9.1 | 29.90 | 0/271 | T3K2-B1O3B4 |
| 054 | 319 | 10.6 | 29.90 | 0/318 | T3K1-B3O4 |
| 055 | 292 | 9.7 | 29.89 | 0/291 | T3K4-Y1 |
| 056 | 282 | 9.4 | 29.89 | 0/281 | T3K3-O1O2Y4 |
| 057 | 305 | 10.2 | 29.91 | 0/304 | T3K1-O2 |
| 058 | 313 | 10.4 | 29.90 | 0/312 | T3K4-B2B3 |
| 059 | 291 | 9.7 | 29.88 | 0/290 | T3K2-B1G4 |
| 060 | 329 | 11.0 | 29.91 | 0/328 | T3K4-O1B2O3 |
| 061 | 379 | 12.6 | 29.90 | 0/378 | T3K1-Y2B3O4 |
| 062 | 283 | 9.4 | 29.91 | 0/282 | T3K2-B3Y4 |
| 063 | 270 | 9.0 | 29.90 | 0/269 | T3K3-Y1 |

```
Cadence summary — whole run, 17 episodes · target 30 Hz (33.3 ms budget per tick): 4884 ticks, 4867 judged
  effective cadence: 29.89 Hz over 162.8 s measured
  ticks over the 33.3 ms work budget: 0/4867 (0.0%) — work mean 3.1 ms, worst 15.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 131
  loop-body steps (share of measured work):
    observe      mean   1.37 ms · worst   8.09 ms ·  44.5% of work · 4884 calls
    process_obs  mean   0.05 ms · worst   0.51 ms ·   1.5% of work · 4884 calls
    teleop       mean   1.15 ms · worst  13.56 ms ·  37.4% of work · 4884 calls
    send         mean   0.25 ms · worst   7.59 ms ·   8.1% of work · 4884 calls
    record       mean   0.20 ms · worst   2.20 ms ·   6.6% of work · 4884 calls
  pacing headroom: 30.4 ms slept per tick on average (max 36.3 ms) — near zero means the loop is saturated
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
