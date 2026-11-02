# cubemark_v1 (main)

- 세션 폴더: `$HOME/so101_runs/main/cubemark_v1`
- dataset: `$HOME/so101_runs/main/cubemark_v1/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-12

## 설정
- 과제: "Pick up the red cube and place it on the X mark." (빨간 큐브를 집어 테이블의 십자(⊕) 표시 위에 놓기)
- 물체·표시 위치: (setup_photos/ 참고 — setup_front_20261012_1450.png = 녹화 전 front 화면)
- 조명·카메라: 자동 노출·자동 WB (3/1/0), 640x480 MJPG 30fps
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-12 16:55 · 새 녹화 <!-- run:20261012_165535 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/cubemark_v1 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main/cubemark_v1/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261012_165535.log`

**결과** <!-- results:20261012_165535 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-12 17:24
- repo_id: `oxr/so101_cubemark_v1` · 과제: "Pick up the red cube and place it on the X mark."
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 20개 (episode 0–19) · 전체 20개 · 버린 에피소드(←) 10번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 000 | 1129 | 37.6 | 29.91 | 0/1128 |
| 001 | 989 | 33.0 | 29.91 | 0/988 |
| 002 | 1051 | 35.0 | 29.90 | 0/1050 |
| 003 | 881 | 29.4 | 29.91 | 0/880 |
| 004 | 861 | 28.7 | 29.90 | 0/860 |
| 005 | 882 | 29.4 | 29.91 | 0/881 |
| 006 | 846 | 28.2 | 29.91 | 0/845 |
| 007 | 1066 | 35.5 | 29.90 | 0/1065 |
| 008 | 820 | 27.3 | 29.89 | 0/819 |
| 009 | 934 | 31.1 | 29.90 | 0/933 |
| 010 | 937 | 31.2 | 29.91 | 0/936 |
| 011 | 803 | 26.8 | 29.91 | 0/802 |
| 012 | 835 | 27.8 | 29.90 | 0/834 |
| 013 | 856 | 28.5 | 29.91 | 0/855 |
| 014 | 781 | 26.0 | 29.89 | 0/780 |
| 015 | 806 | 26.9 | 29.93 | 0/805 |
| 016 | 662 | 22.1 | 29.90 | 0/661 |
| 017 | 697 | 23.2 | 29.91 | 0/696 |
| 018 | 861 | 28.7 | 29.87 | 0/860 |
| 019 | 817 | 27.2 | 29.90 | 0/816 |

```
Cadence summary — whole run, 30 episodes · target 30 Hz (33.3 ms budget per tick): 25820 ticks, 25790 judged
  effective cadence: 29.90 Hz over 862.5 s measured
  ticks over the 33.3 ms work budget: 0/25790 (0.0%) — work mean 2.9 ms, worst 30.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 667
  loop-body steps (share of measured work):
    observe      mean   1.28 ms · worst  27.05 ms ·  44.6% of work · 25820 calls
    process_obs  mean   0.03 ms · worst   2.41 ms ·   1.2% of work · 25820 calls
    teleop       mean   1.11 ms · worst  24.24 ms ·  38.9% of work · 25820 calls
    send         mean   0.23 ms · worst  24.56 ms ·   7.9% of work · 25820 calls
    record       mean   0.17 ms · worst   4.04 ms ·   5.8% of work · 25820 calls
  pacing headroom: 30.6 ms slept per tick on average (max 36.0 ms) — near zero means the loop is saturated
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

### 2026-10-12 17:30 · 이어 찍기 <!-- run:20261012_173049 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/cubemark_v1 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=20 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main/cubemark_v1/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261012_173049.log`

**결과** <!-- results:20261012_173049 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-12 17:52
- repo_id: `oxr/so101_cubemark_v1` · 과제: "Pick up the red cube and place it on the X mark."
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 20개 (episode 20–39) · 전체 40개 · 버린 에피소드(←) 7번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 020 | 649 | 21.6 | 29.90 | 0/648 |
| 021 | 869 | 29.0 | 29.90 | 0/868 |
| 022 | 890 | 29.7 | 29.90 | 0/889 |
| 023 | 766 | 25.5 | 29.90 | 0/765 |
| 024 | 738 | 24.6 | 29.92 | 0/737 |
| 025 | 707 | 23.6 | 29.88 | 0/706 |
| 026 | 719 | 24.0 | 29.90 | 0/718 |
| 027 | 603 | 20.1 | 29.88 | 0/602 |
| 028 | 774 | 25.8 | 29.89 | 0/773 |
| 029 | 755 | 25.2 | 29.90 | 0/754 |
| 030 | 850 | 28.3 | 29.90 | 0/849 |
| 031 | 716 | 23.9 | 29.91 | 0/715 |
| 032 | 711 | 23.7 | 29.91 | 0/710 |
| 033 | 847 | 28.2 | 29.85 | 0/846 |
| 034 | 747 | 24.9 | 29.90 | 0/746 |
| 035 | 713 | 23.8 | 29.91 | 0/712 |
| 036 | 703 | 23.4 | 29.91 | 0/702 |
| 037 | 757 | 25.2 | 29.89 | 0/756 |
| 038 | 626 | 20.9 | 29.91 | 0/625 |
| 039 | 520 | 17.3 | 29.92 | 0/519 |

```
Cadence summary — whole run, 27 episodes · target 30 Hz (33.3 ms budget per tick): 18760 ticks, 18733 judged
  effective cadence: 29.90 Hz over 626.6 s measured
  ticks over the 33.3 ms work budget: 0/18733 (0.0%) — work mean 2.9 ms, worst 29.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 498
  loop-body steps (share of measured work):
    observe      mean   1.30 ms · worst  20.83 ms ·  44.6% of work · 18760 calls
    process_obs  mean   0.03 ms · worst   1.75 ms ·   1.1% of work · 18760 calls
    teleop       mean   1.14 ms · worst  25.03 ms ·  39.1% of work · 18760 calls
    send         mean   0.24 ms · worst  23.97 ms ·   8.1% of work · 18760 calls
    record       mean   0.16 ms · worst   2.01 ms ·   5.7% of work · 18760 calls
  pacing headroom: 30.5 ms slept per tick on average (max 34.4 ms) — near zero means the loop is saturated
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

### 2026-10-12 17:54 · 이어 찍기 <!-- run:20261012_175408 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session main/cubemark_v1 --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=10 --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_cubemark_v1 --dataset.no_stamp=true '--dataset.single_task=Pick up the red cube and place it on the X mark.' --dataset.num_episodes=10 --dataset.episode_time_s=60 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/main/cubemark_v1/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261012_175408.log`

**결과** <!-- results:20261012_175408 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-12 18:02
- repo_id: `oxr/so101_cubemark_v1` · 과제: "Pick up the red cube and place it on the X mark."
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=120
- 에피소드: 이번 10개 (episode 40–49) · 전체 50개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 |
|---|---|---|---|---|
| 040 | 773 | 25.8 | 29.91 | 0/772 |
| 041 | 808 | 26.9 | 29.90 | 0/807 |
| 042 | 824 | 27.5 | 29.91 | 0/823 |
| 043 | 770 | 25.7 | 29.91 | 0/769 |
| 044 | 575 | 19.2 | 29.90 | 0/574 |
| 045 | 520 | 17.3 | 29.90 | 0/519 |
| 046 | 525 | 17.5 | 29.92 | 0/524 |
| 047 | 661 | 22.0 | 29.91 | 0/660 |
| 048 | 589 | 19.6 | 29.89 | 0/588 |
| 049 | 597 | 19.9 | 29.92 | 0/596 |

```
Cadence summary — whole run, 10 episodes · target 30 Hz (33.3 ms budget per tick): 6642 ticks, 6632 judged
  effective cadence: 29.91 Hz over 221.7 s measured
  ticks over the 33.3 ms work budget: 0/6632 (0.0%) — work mean 2.8 ms, worst 24.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 156
  loop-body steps (share of measured work):
    observe      mean   1.27 ms · worst  22.11 ms ·  44.9% of work · 6642 calls
    process_obs  mean   0.03 ms · worst   1.84 ms ·   1.2% of work · 6642 calls
    teleop       mean   1.10 ms · worst   6.20 ms ·  38.9% of work · 6642 calls
    send         mean   0.22 ms · worst   3.19 ms ·   7.6% of work · 6642 calls
    record       mean   0.17 ms · worst   2.15 ms ·   5.9% of work · 6642 calls
  pacing headroom: 30.6 ms slept per tick on average (max 35.4 ms) — near zero means the loop is saturated
```

**판별 메모**

- 40·41 = 놓침 → 다시 집기(의도) · 42·43 = 잘못 둠 → 다시 옮기기(의도)

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 040 | | 놓침 → 다시 집기(의도) |
| 041 | | 놓침 → 다시 집기(의도) |
| 042 | | 잘못 둠 → 다시 옮기기(의도) |
| 043 | | 잘못 둠 → 다시 옮기기(의도) |
| 044 | | |
| 045 | | |
| 046 | | |
| 047 | | |
| 048 | | |
| 049 | | |

## 학습 기록

### 2026-10-12 18:05 · π0.5 학습 `train/pi05_15k` (50편 전체) — 2026-10-13 부터 `train/4_15000/pi05_15k`

**사전 점검**
- QA (`check_dataset.py main/cubemark_v1`, 2026-10-12 18:04): 50편, 17.3–37.6초, NaN 0, 영상·데이터 프레임 수 일치 → 50편 전부 사용
  - "박스" 관련 경고(박스 자리·끝에 박스 밖)는 이전 과제(cubebox) 기준이라 이 과제와 무관. X 표시는 판마다 위치를 바꿈 (qa/ep_002·ep_023 확인)
  - 40·41 = 놓침 → 다시 집기(의도), 42·43 = 잘못 둠 → 다시 옮기기(의도) — 그대로 사용
  - 049 시작 |state−action| 21.5° (shoulder_lift, 시작 순간 리더·팔로워 차이) — 그대로 사용
- 녹화 프로세스·twin_ws 컨테이너·GPU 사용 없음. stats.json 에 q01/q99 있음. 디스크 여유 727 GB

**명령** (`train/run_pi05_15k.sh` — practice_50 `pi05_15k` 와 같은 설정, `train/launch_pi05_15k.sh` 가 백그라운드 실행, 로그 `train/pi05_15k.log`, 메모리 `train/pi05_15k.mem.log`, 시각 `train/pi05_15k.time`)
```bash
PYTHONDONTWRITEBYTECODE=1 $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubemark_v1 \
  --dataset.root=$HOME/so101_runs/main/cubemark_v1/dataset \
  --policy.type=pi05 --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/main/cubemark_v1/train/pi05_15k --job_name=pi05_15k \
  --batch_size=4 --steps=15000 --log_freq=50 --save_freq=5000 --num_workers=4 \
  --wandb.enable=false
```
- 15000 스텝 × 배치 4 = 60000 샘플 ≈ 1.55 epoch (38816 프레임). 예상 약 10시간 (practice_50 2.36 s/step 기준)

**결과**
- 종료: 정상 ("End of training", rc=0), Traceback 없음. 경고: vision patch_embedding 키 2개 "might need handling" (practice_10·50 때와 같음)
- lr 스케줄 자동 축소: warmup 1000→500, decay 30000→15000
- loss (50 스텝마다 기록, 300개): step 50 0.095 → 100 0.069 → 500 0.052 → 1000 0.039 → 2000 0.028 → 5000 0.019 → 7500 0.019 → 10000 0.013 → 12500 0.011 → 15000 0.011
  - 구간 평균: 0–1k 0.050 · 1k–2.5k 0.032 · 2.5k–5k 0.024 · 5k–7.5k 0.018 · 7.5k–10k 0.014 · 10k–12.5k 0.011 · 12.5k–15k 0.010 — 끝까지 줄어듦 (처음 5회 평균 0.068, 마지막 5회 0.011, 최저 0.008 @12300)
  - grad norm 2.1 → 0.43–0.46
- 시간: 2026-10-12 18:05:05 – 10-13 03:59:11 (9시간 54분) = 모델 생성 약 2분 45초 + 학습 2.36 s/step
- 메모리: nvidia-smi 프로세스 39.3 GB, 시스템 전체 최대 약 68 GB
- 체크포인트 (`train/pi05_15k/checkpoints/`, `last` → 015000), 각 23 GB (pretrained_model 8.8 GB + training_state 15 GB), 합계 69 GB: `005000/` (10-12 21:24), `010000/` (10-13 00:42), `015000/` (03:58)
- 허브 업로드 없음

### 2026-10-13 · 실물 rollout 준비 `eval/` (팔 연결 없음)
- practice_50/eval 에서 복사: `run_rollout.sh` (경로·과제 문장·repo `oxr/rollout_cubemark_v1_pi05_15k_<15k>_<tag>` 만 바꿈, `STEP=005000|010000|015000`, 기본 015000), `rollout_logged.py`·`plot_rollout.py` (그대로), `pose_check.py`·`analyze_rollout.py` (경로만)
- 기준값 `eval/reference_teleop/analysis.json` (50편 사람 조작): action 방향 바뀜 0.20/0.13/0.21/0.34/0.18/0.18 회/초, hf_rms 0.18/0.27/0.29/0.28/0.24/0.40°
- 첫 실행 권장: `./run_rollout.sh rtc_fast --policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40`
- 2026-10-13 직접 평가용 래퍼 `$HOME/so101_boxpick/scripts/eval_ui.py` 추가 (episodic, 첫 판 시작 대기, 판마다 시작 사진 `start_images/`, 초기화 단계에서 P/F 판정 → `results.md`, 실행마다 `eval/index.md` 한 줄). `--check` 로 옵션 파싱 확인 OK (팔 연결 없음), 가짜 자식으로 키·단계 흐름 시험 OK
  - 실행: `python3 $HOME/so101_boxpick/scripts/eval_ui.py --session main/cubemark_v1`
- 2026-10-13 `eval_ui.py` 에 CSV 추가: 실행마다 `results.csv` (판마다 시작 사진 파일 이름·판정·길이·메모 한 줄), 세션 전체 `eval/results_all.csv`
- 2026-10-13 학습 설정 정리 파일 `train/pi05_15k/training_params.csv` · `.md` (epoch 1.55 · batch 4 · steps 15000 · lr 2.5e-5 등) — `python3 $HOME/so101_boxpick/scripts/train_summary.py <학습폴더>` 로 다른 학습도 만들 수 있음
- 2026-10-13 10:32 eval_ui 첫 실물 평가(3판 F/F/F)는 사용자 요청으로 삭제. 확인된 문제: 판이 끝나도 처음 자세로 다 안 돌아감 (ep1 시작 shoulder_lift −19.7° vs 처음 −102.5°). 원인: lerobot episodic 의 복귀가 1초 보간뿐이라 max_relative_target 8° 와 P=16 에 잘림
  - 수정: eval_ui 가 복귀를 거리에 맞춰 30°/s 로 보간한 뒤 오차 3° 안이 될 때까지 목표를 계속 보냄 (최대 8초+4초). 모의 팔(8° 제한·40°/s)로 원래 1초 방식 93° 모자람 → 수정 후 0° 확인
- 2026-10-13 10:44 eval_ui 실물 평가(2판 F/F)도 사용자 요청으로 삭제. 처음 자세 복귀는 실물에서 확인됨: 125°→1.8°, 113°→1.8° (각 약 4초)

### 2026-10-13 11:29 · π0.5 학습 2 `train/8_3000/pi05_expert_bs8_3k` (50편 전체, action expert 만)

- train/ 정리 (사용자 요청, 2026-10-13 11:29): 학습마다 `train/<배치>_<스텝>/` 묶음 — `train/4_15000/` = 기존 pi05_15k (폴더만 옮김: 체크포인트·로그·스크립트 그대로), `train/8_3000/` = 이 학습
  - 11:22 에 `train/pi05_expert_bs8_3k` 로 먼저 시작했다가 73 스텝에서 멈추고 지운 뒤 새 위치에서 다시 시작 (그때 측정: 2.8 s/step, GPU 15 GB, 학습 파라미터 693,422,112 / 전체 4,143,404,816, warmup 1000→100·decay 30000→3000 자동 축소)
- 사용자 지정 설정: `--policy.train_expert_only=true --policy.freeze_vision_encoder=true --policy.gradient_checkpointing=true --policy.optimizer_lr=2.5e-5 --batch_size=8 --steps=3000`
- 나머지는 4_15000 과 같음 (pi05_base, bfloat16, num_workers 4, log 50). 저장 1000 스텝마다
- 명령: `train/8_3000/run_pi05_expert_bs8_3k.sh` (백그라운드 `launch_pi05_expert_bs8_3k.sh`, 로그 `train/8_3000/pi05_expert_bs8_3k.log`·`.mem.log`·`.time`)
- 3000 스텝 × 배치 8 = 24000 샘플 ≈ 0.62 epoch (38816 프레임). 예상 약 2시간 20분

**결과**
- 종료: 정상 ("End of training", rc=0) · 2026-10-13 11:29:43 – 13:52:23 (2시간 22분, 2.83 s/step)
- loss: 0.095 (50) → 0.037 (3000), 최저 0.035 @2600 — 4_15000 의 같은 0.62 epoch 무렵(약 6000 스텝, 0.019)보다 높음 (학습 범위가 작음)
- 학습 파라미터 693,422,112 / 4,143,404,816 · GPU 14.9 GB
- 체크포인트 001000 · 002000 · 003000 (각 11 GB), `last` → 003000. 설정 정리 `train/8_3000/pi05_expert_bs8_3k/training_params.csv`
