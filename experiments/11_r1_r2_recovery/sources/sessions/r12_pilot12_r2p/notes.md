# r12_pilot12_r2p (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/r12_pilot12_r2p`
- dataset: `$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-03

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-03 16:04 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261103_160410 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R2-P = 열린 그리퍼 접근 교정 (AHEAD 2 · DEPTH 2) — Enter 로 확인
- 체크리스트 추가: 준비 단계(녹화 안 함)에서 그리퍼를 열고 큐브 앞 파지 높이 근처에서 팔 정지 → → (손목 화면 주황 영역 · 대략) — Enter 로 확인
- 체크리스트 추가: 녹화 중 그리퍼는 연 채, 닫기는 큐브가 손가락 사이에 왔을 때 한 번 (d2 방식 그대로) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 2
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r2p '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=2 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261103_160410.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r2p/r12_plan.csv` · 이번 실행 episode 0–1

**결과** <!-- results:20261103_160410 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-03 16:11
- repo_id: `oxr/so101_k8_r12_pilot12_r2p` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 2개 (episode 0–1) · 전체 2개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 577 | 19.2 | 29.81 | 0/576 |  |
| 001 | 404 | 13.5 | 29.89 | 0/403 |  |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 1753 ticks, 1749 judged
  effective cadence: 29.87 Hz over 58.6 s measured
  ticks over the 33.3 ms work budget: 0/1749 (0.0%) — work mean 3.9 ms, worst 14.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 72
  loop-body steps (share of measured work):
    observe      mean   1.44 ms · worst   6.16 ms ·  37.0% of work · 1753 calls
    process_obs  mean   0.05 ms · worst   1.27 ms ·   1.3% of work · 1753 calls
    teleop       mean   1.16 ms · worst   6.55 ms ·  29.8% of work · 1753 calls
    send         mean   0.30 ms · worst   5.53 ms ·   7.6% of work · 1753 calls
    record       mean   0.23 ms · worst   0.94 ms ·   5.9% of work · 1753 calls
    telemetry    mean   0.65 ms · worst   7.96 ms ·  16.7% of work · 1753 calls
  pacing headroom: 29.6 ms slept per tick on average (max 33.3 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |

### 2026-11-03 16:41 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261103_164125 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R2-P = 열린 그리퍼 접근 교정 (AHEAD 2 · DEPTH 2) — Enter 로 확인
- 체크리스트 추가: 준비 단계(녹화 안 함)에서 그리퍼를 열고 큐브 앞 파지 높이 근처에서 팔 정지 → → (손목 화면 주황 영역 · 대략) — Enter 로 확인
- 체크리스트 추가: 녹화 중 그리퍼는 연 채, 닫기는 큐브가 손가락 사이에 왔을 때 한 번 (d2 방식 그대로) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 2) 큐브를 K8 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 2 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r2p '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=2 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261103_164125.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r2p/r12_plan.csv` · 이번 실행 episode 2–3

**결과** <!-- results:20261103_164125 -->
- 종료: ⚠ 비정상 (코드 1) — 수동 후처리 · 후처리 2026-11-03 16:49
- repo_id: `oxr/so101_k8_r12_pilot12_r2p` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 2개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-03 16:42 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261103_164216 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R2-P = 열린 그리퍼 접근 교정 (AHEAD 2 · DEPTH 2) — Enter 로 확인
- 체크리스트 추가: 준비 단계(녹화 안 함)에서 그리퍼를 열고 큐브 앞 파지 높이 근처에서 팔 정지 → → (손목 화면 주황 영역 · 대략) — Enter 로 확인
- 체크리스트 추가: 녹화 중 그리퍼는 연 채, 닫기는 큐브가 손가락 사이에 왔을 때 한 번 (d2 방식 그대로) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 2) 큐브를 K8 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 2 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r2p '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=2 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261103_164216.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r2p/r12_plan.csv` · 이번 실행 episode 2–3

**결과** <!-- results:20261103_164216 -->
- 종료: ⚠ 비정상 (코드 1) — 수동 후처리 · 후처리 2026-11-03 16:49
- repo_id: `oxr/so101_k8_r12_pilot12_r2p` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 2개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-03 16:44 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261103_164442 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R2-P = 열린 그리퍼 접근 교정 (AHEAD 2 · DEPTH 2) — Enter 로 확인
- 체크리스트 추가: 준비 단계(녹화 안 함)에서 그리퍼를 열고 큐브 앞 파지 높이 근처에서 팔 정지 → → (손목 화면 주황 영역 · 대략) — Enter 로 확인
- 체크리스트 추가: 녹화 중 그리퍼는 연 채, 닫기는 큐브가 손가락 사이에 왔을 때 한 번 (d2 방식 그대로) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 2) 큐브를 K8 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 2 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r2p '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=2 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261103_164442.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r2p/r12_plan.csv` · 이번 실행 episode 2–3

**결과** <!-- results:20261103_164442 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-03 16:49
- repo_id: `oxr/so101_k8_r12_pilot12_r2p` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 2개 (episode 2–3) · 전체 4개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 002 | 434 | 14.5 | 29.90 | 0/433 |  |
| 003 | 536 | 17.9 | 29.89 | 0/535 |  |

```
Cadence summary — whole run, 3 episodes · target 30 Hz (33.3 ms budget per tick): 1068 ticks, 1065 judged
  effective cadence: 29.89 Hz over 35.6 s measured
  ticks over the 33.3 ms work budget: 0/1065 (0.0%) — work mean 3.8 ms, worst 9.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 24
  loop-body steps (share of measured work):
    observe      mean   1.40 ms · worst   4.47 ms ·  36.3% of work · 1068 calls
    process_obs  mean   0.05 ms · worst   0.19 ms ·   1.3% of work · 1068 calls
    teleop       mean   1.13 ms · worst   2.86 ms ·  29.3% of work · 1068 calls
    send         mean   0.30 ms · worst   3.68 ms ·   7.8% of work · 1068 calls
    record       mean   0.23 ms · worst   3.01 ms ·   6.0% of work · 1068 calls
    telemetry    mean   0.67 ms · worst  10.23 ms ·  17.4% of work · 1068 calls
  pacing headroom: 29.6 ms slept per tick on average (max 32.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 002 | | |
| 003 | | |

### 2026-11-04 09:50 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_095039 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R2-P = 열린 그리퍼 접근 교정 (AHEAD 2 · DEPTH 2) — Enter 로 확인
- 체크리스트 추가: 준비 단계(녹화 안 함)에서 그리퍼를 열고 큐브 앞 파지 높이 근처에서 팔 정지 → → (손목 화면 주황 영역 · 대략) — Enter 로 확인
- 체크리스트 추가: 녹화 중 그리퍼는 연 채, 닫기는 큐브가 손가락 사이에 왔을 때 한 번 (d2 방식 그대로) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 4) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r2p --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 2 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r2p '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=2 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r2p/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_095039.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r2p/r12_plan.csv` · 이번 실행 episode 4–5

**결과** <!-- results:20261104_095039 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 10:08
- repo_id: `oxr/so101_k8_r12_pilot12_r2p` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 2개 (episode 4–5) · 전체 6개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 004 | 422 | 14.1 | 29.88 | 0/421 |  |
| 005 | 338 | 11.3 | 29.89 | 0/337 |  |

```
Cadence summary — whole run, 2 episodes · target 30 Hz (33.3 ms budget per tick): 760 ticks, 758 judged
  effective cadence: 29.88 Hz over 25.4 s measured
  ticks over the 33.3 ms work budget: 0/758 (0.0%) — work mean 3.9 ms, worst 10.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 25
  loop-body steps (share of measured work):
    observe      mean   1.42 ms · worst   5.20 ms ·  36.6% of work · 760 calls
    process_obs  mean   0.05 ms · worst   0.47 ms ·   1.4% of work · 760 calls
    teleop       mean   1.15 ms · worst   3.85 ms ·  29.5% of work · 760 calls
    send         mean   0.29 ms · worst   4.37 ms ·   7.6% of work · 760 calls
    record       mean   0.23 ms · worst   1.50 ms ·   6.0% of work · 760 calls
    telemetry    mean   0.66 ms · worst   8.51 ms ·  17.1% of work · 760 calls
  pacing headroom: 29.6 ms slept per tick on average (max 32.3 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 004 | | |
| 005 | | |
