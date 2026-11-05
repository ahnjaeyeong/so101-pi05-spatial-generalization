# r12_pilot12_rc (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/r12_pilot12_rc`
- dataset: `$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-04

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-04 11:13 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261104_111309 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K7 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_111309.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261104_111309 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 11:21
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 362 | 12.1 | 29.88 | 0/361 |  |
| 001 | 361 | 12.0 | 29.88 | 0/360 |  |
| 002 | 343 | 11.4 | 29.88 | 0/342 |  |
| 003 | 373 | 12.4 | 29.86 | 0/372 |  |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 1729 ticks, 1724 judged
  effective cadence: 29.88 Hz over 57.7 s measured
  ticks over the 33.3 ms work budget: 0/1724 (0.0%) — work mean 4.0 ms, worst 11.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 72
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   5.13 ms ·  36.7% of work · 1729 calls
    process_obs  mean   0.05 ms · worst   1.91 ms ·   1.3% of work · 1729 calls
    teleop       mean   1.20 ms · worst   5.73 ms ·  30.0% of work · 1729 calls
    send         mean   0.32 ms · worst   3.89 ms ·   8.1% of work · 1729 calls
    record       mean   0.23 ms · worst   1.15 ms ·   5.8% of work · 1729 calls
    telemetry    mean   0.65 ms · worst  11.54 ms ·  16.3% of work · 1729 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |

### 2026-11-04 13:33 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_133328 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 4) 큐브를 K8 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_133328.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 4–7

**결과** <!-- results:20261104_133328 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 13:41
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 4–7) · 전체 8개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 004 | 451 | 15.0 | 29.87 | 0/450 |  |
| 005 | 338 | 11.3 | 29.90 | 0/337 |  |
| 006 | 362 | 12.1 | 29.91 | 0/361 |  |
| 007 | 367 | 12.2 | 29.87 | 0/366 |  |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 1969 ticks, 1964 judged
  effective cadence: 29.88 Hz over 65.7 s measured
  ticks over the 33.3 ms work budget: 0/1964 (0.0%) — work mean 3.9 ms, worst 9.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 69
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   4.62 ms ·  37.0% of work · 1969 calls
    process_obs  mean   0.05 ms · worst   1.33 ms ·   1.4% of work · 1969 calls
    teleop       mean   1.16 ms · worst   3.92 ms ·  30.0% of work · 1969 calls
    send         mean   0.29 ms · worst   3.02 ms ·   7.6% of work · 1969 calls
    record       mean   0.23 ms · worst   0.84 ms ·   5.9% of work · 1969 calls
    telemetry    mean   0.64 ms · worst   9.50 ms ·  16.4% of work · 1969 calls
  pacing headroom: 29.6 ms slept per tick on average (max 32.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 004 | | |
| 005 | | |
| 006 | | |
| 007 | | |

### 2026-11-04 13:47 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_134738 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 8) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_134738.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 8–11

**결과** <!-- results:20261104_134738 -->
- 종료: ⚠ 비정상 (코드 -2, Ctrl+C) — 수동 후처리 · 후처리 2026-11-04 14:04
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 8개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-04 13:48 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_134834 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 8) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_134834.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 8–11

**결과** <!-- results:20261104_134834 -->
- 종료: ⚠ 비정상 (코드 -2, Ctrl+C) — 수동 후처리 · 후처리 2026-11-04 14:04
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 8개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-04 13:59 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_135920 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 8) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_135920.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 8–11

**결과** <!-- results:20261104_135920 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 14:04
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 8–11) · 전체 12개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 008 | 398 | 13.3 | 29.88 | 0/397 |  |
| 009 | 374 | 12.5 | 29.89 | 0/373 |  |
| 010 | 332 | 11.1 | 29.88 | 0/331 |  |
| 011 | 260 | 8.7 | 29.90 | 0/259 |  |

```
Cadence summary — whole run, 5 episodes · target 30 Hz (33.3 ms budget per tick): 1510 ticks, 1505 judged
  effective cadence: 29.88 Hz over 50.4 s measured
  ticks over the 33.3 ms work budget: 0/1505 (0.0%) — work mean 3.9 ms, worst 10.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 62
  loop-body steps (share of measured work):
    observe      mean   1.47 ms · worst   6.01 ms ·  37.4% of work · 1510 calls
    process_obs  mean   0.05 ms · worst   0.61 ms ·   1.3% of work · 1510 calls
    teleop       mean   1.17 ms · worst   4.25 ms ·  29.8% of work · 1510 calls
    send         mean   0.29 ms · worst   3.37 ms ·   7.4% of work · 1510 calls
    record       mean   0.23 ms · worst   2.92 ms ·   5.9% of work · 1510 calls
    telemetry    mean   0.64 ms · worst   5.88 ms ·  16.3% of work · 1510 calls
  pacing headroom: 29.5 ms slept per tick on average (max 31.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 008 | | |
| 009 | | |
| 010 | | |
| 011 | | |

### 2026-11-04 14:06 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_140621 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 회복 시연 (F1 사선 하강 4 · F2 이른 닫힘 4 · F3 정렬 오차 4). 실패 자세는 준비 단계(녹화 안 함)에서 만들고, 녹화는 회복부터 — Enter 로 확인
- 체크리스트 추가: F1 은 그리퍼 열림, F2 · F3 은 그리퍼 닫힘으로 시작. 큐브에 닿지 않게, 큐브 앞에서 닫는 동작(빈 파지)은 하지 않음 — Enter 로 확인
- 체크리스트 추가: 영상 창 F11 = 실제 실패 대표 영상 (review/failure_types) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 12) 큐브를 K2 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_rc --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_recovery.yaml --num 1 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_rc '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=1 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_rc/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_140621.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_rc/r12_plan.csv` · 이번 실행 episode 12–12

**결과** <!-- results:20261104_140621 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 14:07
- repo_id: `oxr/so101_k8_r12_pilot12_rc` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 1개 (episode 12–12) · 전체 13개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 012 | 307 | 10.2 | 29.86 | 0/306 |  |

```
Cadence summary — whole run, 1 episode · target 30 Hz (33.3 ms budget per tick): 307 ticks, 306 judged
  effective cadence: 29.86 Hz over 10.2 s measured
  ticks over the 33.3 ms work budget: 0/306 (0.0%) — work mean 3.9 ms, worst 9.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 22
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   4.68 ms ·  36.7% of work · 307 calls
    process_obs  mean   0.05 ms · worst   0.18 ms ·   1.4% of work · 307 calls
    teleop       mean   1.15 ms · worst   2.97 ms ·  29.1% of work · 307 calls
    send         mean   0.30 ms · worst   3.48 ms ·   7.7% of work · 307 calls
    record       mean   0.24 ms · worst   1.06 ms ·   6.0% of work · 307 calls
    telemetry    mean   0.69 ms · worst   8.16 ms ·  17.3% of work · 307 calls
  pacing headroom: 29.5 ms slept per tick on average (max 32.9 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 012 | | |
