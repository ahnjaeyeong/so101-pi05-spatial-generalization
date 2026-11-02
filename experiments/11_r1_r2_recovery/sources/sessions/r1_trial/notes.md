# r1_trial (practice)

- 세션 폴더: `$HOME/so101_runs/practice/r1_trial`
- dataset: `$HOME/so101_runs/practice/r1_trial/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-02

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-02 10:56 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_105602 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_trial
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_trial '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=3 --dataset.root=$HOME/so101_runs/practice/r1_trial/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_105602.log`
- 계획: `~/so101_runs/practice/r1_trial/r12_plan.csv` · 이번 실행 episode 0–2

**결과** <!-- results:20261102_105602 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 10:57
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-10-30 16:05 · 새 녹화 <!-- run:20261030_160505 -->

**결과** <!-- results:20261030_160505 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 10:57
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 09:58 · 새 녹화 <!-- run:20261102_095816 -->

**결과** <!-- results:20261102_095816 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 10:57
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 10:27 · 새 녹화 <!-- run:20261102_102757 -->

**결과** <!-- results:20261102_102757 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 10:57
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 10:36 · 새 녹화 <!-- run:20261102_103609 -->

**결과** <!-- results:20261102_103609 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 10:57
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 3개 (episode 0–2) · 전체 3개 · 버린 에피소드(←) 2번

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 2609 ticks, 2604 judged
  effective cadence: 29.89 Hz over 87.1 s measured
  ticks over the 33.3 ms work budget: 0/2604 (0.0%) — work mean 3.7 ms, worst 9.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 67
  loop-body steps (share of measured work):
    observe      mean   1.41 ms · worst   5.12 ms ·  37.6% of work · 2609 calls
    process_obs  mean   0.05 ms · worst   0.63 ms ·   1.4% of work · 2609 calls
    teleop       mean   1.15 ms · worst   4.17 ms ·  30.8% of work · 2609 calls
    send         mean   0.26 ms · worst   3.02 ms ·   6.9% of work · 2609 calls
    record       mean   0.23 ms · worst   1.61 ms ·   6.0% of work · 2609 calls
    telemetry    mean   0.58 ms · worst  10.57 ms ·  15.5% of work · 2609 calls
  pacing headroom: 29.7 ms slept per tick on average (max 31.9 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 11:00 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_110026 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_trial
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_trial '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=3 --dataset.root=$HOME/so101_runs/practice/r1_trial/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_110026.log`
- 계획: `~/so101_runs/practice/r1_trial/r12_plan.csv` · 이번 실행 episode 0–2

**결과** <!-- results:20261102_110026 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 11:01
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 11:06 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_110655 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_trial
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_trial '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=3 --dataset.root=$HOME/so101_runs/practice/r1_trial/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_110655.log`
- 계획: `~/so101_runs/practice/r1_trial/r12_plan.csv` · 이번 실행 episode 0–2

**결과** <!-- results:20261102_110655 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 11:17
- repo_id: `oxr/so101_r1_trial` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 3개 (episode 0–2) · 전체 3개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 582 | 19.4 | 29.87 | 0/581 |  |
| 001 | 631 | 21.0 | 29.88 | 0/630 |  |
| 002 | 565 | 18.8 | 29.88 | 0/564 |  |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 3177 ticks, 3172 judged
  effective cadence: 29.87 Hz over 106.2 s measured
  ticks over the 33.3 ms work budget: 0/3172 (0.0%) — work mean 3.8 ms, worst 11.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 141
  loop-body steps (share of measured work):
    observe      mean   1.41 ms · worst   5.55 ms ·  37.5% of work · 3177 calls
    process_obs  mean   0.05 ms · worst   0.86 ms ·   1.4% of work · 3177 calls
    teleop       mean   1.16 ms · worst   5.03 ms ·  30.9% of work · 3177 calls
    send         mean   0.26 ms · worst   3.05 ms ·   6.8% of work · 3177 calls
    record       mean   0.23 ms · worst   0.96 ms ·   6.0% of work · 3177 calls
    telemetry    mean   0.58 ms · worst   7.44 ms ·  15.5% of work · 3177 calls
  pacing headroom: 29.7 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
