# sg_pin (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/sg_pin`
- dataset: `$HOME/so101_runs/main_k8/sg_pin/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-12

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-12 13:17 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261112_131748 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_131748.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261112_131748 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 13:34
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 0–7) · 전체 8개 · 버린 에피소드(←) 5번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 1185 | 39.5 | 29.86 | 0/1184 |  |
| 001 | 1030 | 34.3 | 29.88 | 0/1029 |  |
| 002 | 1029 | 34.3 | 29.86 | 0/1028 |  |
| 003 | 1161 | 38.7 | 29.86 | 0/1160 |  |
| 004 | 1588 | 52.9 | 29.86 | 0/1587 |  |
| 005 | 1162 | 38.7 | 29.87 | 0/1161 |  |
| 006 | 1247 | 41.6 | 29.87 | 0/1246 |  |
| 007 | 1162 | 38.7 | 29.86 | 0/1161 |  |

```
Cadence summary — whole run, 13 episodes · target 30 Hz (33.3 ms budget per tick): 15613 ticks, 15600 judged
  effective cadence: 29.86 Hz over 522.4 s measured
  ticks over the 33.3 ms work budget: 0/15600 (0.0%) — work mean 3.9 ms, worst 11.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 901
  loop-body steps (share of measured work):
    observe      mean   1.44 ms · worst   7.11 ms ·  36.5% of work · 15613 calls
    process_obs  mean   0.06 ms · worst   1.39 ms ·   1.4% of work · 15613 calls
    teleop       mean   1.17 ms · worst   5.24 ms ·  29.7% of work · 15613 calls
    send         mean   0.28 ms · worst   3.88 ms ·   7.0% of work · 15613 calls
    record       mean   0.24 ms · worst   3.98 ms ·   6.1% of work · 15613 calls
    telemetry    mean   0.69 ms · worst   8.87 ms ·  17.4% of work · 15613 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
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

### 2026-11-12 13:36 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_133651 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 8) 큐브를 K7p5 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_133651.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 8–15

**결과** <!-- results:20261112_133651 -->
- 종료: ⚠ 비정상 (코드 1) — 수동 후처리 · 후처리 2026-11-12 14:02
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 1개 (episode 8–8) · 전체 9개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 008 | 1792 | 59.7 | 29.86 | 0/1791 |  |

```
Cadence summary — whole run, 3 episodes · target 30 Hz (33.3 ms budget per tick): 4356 ticks, 4353 judged
  effective cadence: 29.86 Hz over 145.8 s measured
  ticks over the 33.3 ms work budget: 0/4353 (0.0%) — work mean 4.0 ms, worst 11.0 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 244
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   6.24 ms ·  36.5% of work · 4356 calls
    process_obs  mean   0.06 ms · worst   1.96 ms ·   1.4% of work · 4356 calls
    teleop       mean   1.18 ms · worst   4.66 ms ·  29.5% of work · 4356 calls
    send         mean   0.28 ms · worst   3.10 ms ·   7.0% of work · 4356 calls
    record       mean   0.24 ms · worst   1.70 ms ·   6.1% of work · 4356 calls
    telemetry    mean   0.70 ms · worst   8.35 ms ·  17.6% of work · 4356 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.3 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 008 | | |

### 2026-11-12 13:48 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_134825 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 9) 큐브를 K6p2 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_134825.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 9–16

**결과** <!-- results:20261112_134825 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 14:02
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 9–16) · 전체 17개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 009 | 1427 | 47.6 | 29.86 | 0/1426 |  |
| 010 | 1203 | 40.1 | 29.86 | 0/1202 |  |
| 011 | 1017 | 33.9 | 29.86 | 0/1016 |  |
| 012 | 1275 | 42.5 | 29.86 | 0/1274 |  |
| 013 | 1365 | 45.5 | 29.85 | 0/1364 |  |
| 014 | 1035 | 34.5 | 29.85 | 0/1034 |  |
| 015 | 1210 | 40.3 | 29.86 | 0/1209 |  |
| 016 | 1046 | 34.9 | 29.83 | 0/1045 |  |

```
Cadence summary — whole run, 11 episodes · target 30 Hz (33.3 ms budget per tick): 13254 ticks, 13243 judged
  effective cadence: 29.85 Hz over 443.6 s measured
  ticks over the 33.3 ms work budget: 0/13243 (0.0%) — work mean 4.0 ms, worst 14.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 805
  loop-body steps (share of measured work):
    observe      mean   1.49 ms · worst  12.52 ms ·  36.9% of work · 13254 calls
    process_obs  mean   0.06 ms · worst   2.42 ms ·   1.4% of work · 13254 calls
    teleop       mean   1.19 ms · worst   4.48 ms ·  29.5% of work · 13254 calls
    send         mean   0.29 ms · worst   4.92 ms ·   7.1% of work · 13254 calls
    record       mean   0.24 ms · worst   2.97 ms ·   6.0% of work · 13254 calls
    telemetry    mean   0.69 ms · worst   8.22 ms ·  17.2% of work · 13254 calls
  pacing headroom: 29.4 ms slept per tick on average (max 34.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 009 | | |
| 010 | | |
| 011 | | |
| 012 | | |
| 013 | | |
| 014 | | |
| 015 | | |
| 016 | | |

### 2026-11-12 14:04 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_140425 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 17) 큐브를 K3p7 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_140425.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 17–24

**결과** <!-- results:20261112_140425 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 14:17
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 17–24) · 전체 25개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 017 | 957 | 31.9 | 29.88 | 0/956 |  |
| 018 | 1209 | 40.3 | 29.85 | 0/1208 |  |
| 019 | 969 | 32.3 | 29.86 | 0/968 |  |
| 020 | 1076 | 35.9 | 29.85 | 0/1075 |  |
| 021 | 722 | 24.1 | 29.86 | 0/721 |  |
| 022 | 1312 | 43.7 | 29.87 | 0/1311 |  |
| 023 | 1275 | 42.5 | 29.86 | 0/1274 |  |
| 024 | 1221 | 40.7 | 29.85 | 0/1220 |  |

```
Cadence summary — whole run, 12 episodes · target 30 Hz (33.3 ms budget per tick): 11886 ticks, 11874 judged
  effective cadence: 29.86 Hz over 397.6 s measured
  ticks over the 33.3 ms work budget: 0/11874 (0.0%) — work mean 3.9 ms, worst 11.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 661
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   6.72 ms ·  36.9% of work · 11886 calls
    process_obs  mean   0.05 ms · worst   1.77 ms ·   1.4% of work · 11886 calls
    teleop       mean   1.18 ms · worst   6.71 ms ·  29.7% of work · 11886 calls
    send         mean   0.27 ms · worst   5.72 ms ·   6.9% of work · 11886 calls
    record       mean   0.24 ms · worst   2.32 ms ·   6.0% of work · 11886 calls
    telemetry    mean   0.69 ms · worst   8.34 ms ·  17.4% of work · 11886 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 017 | | |
| 018 | | |
| 019 | | |
| 020 | | |
| 021 | | |
| 022 | | |
| 023 | | |
| 024 | | |

### 2026-11-12 14:18 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_141815 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 25) 큐브를 K3 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_141815.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 25–32

**결과** <!-- results:20261112_141815 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 14:32
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 25–32) · 전체 33개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 025 | 1072 | 35.7 | 29.87 | 0/1071 |  |
| 026 | 1185 | 39.5 | 29.86 | 0/1184 |  |
| 027 | 957 | 31.9 | 29.87 | 0/956 |  |
| 028 | 1474 | 49.1 | 29.87 | 0/1473 |  |
| 029 | 1209 | 40.3 | 29.86 | 0/1208 |  |
| 030 | 1318 | 43.9 | 29.87 | 0/1317 |  |
| 031 | 939 | 31.3 | 29.87 | 0/938 |  |
| 032 | 1227 | 40.9 | 29.86 | 0/1226 |  |

```
Cadence summary — whole run, 11 episodes · target 30 Hz (33.3 ms budget per tick): 11737 ticks, 11726 judged
  effective cadence: 29.87 Hz over 392.6 s measured
  ticks over the 33.3 ms work budget: 0/11726 (0.0%) — work mean 3.9 ms, worst 12.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 637
  loop-body steps (share of measured work):
    observe      mean   1.44 ms · worst   6.72 ms ·  36.6% of work · 11737 calls
    process_obs  mean   0.05 ms · worst   3.18 ms ·   1.4% of work · 11737 calls
    teleop       mean   1.17 ms · worst   6.10 ms ·  29.6% of work · 11737 calls
    send         mean   0.28 ms · worst   5.01 ms ·   7.0% of work · 11737 calls
    record       mean   0.24 ms · worst   3.13 ms ·   6.0% of work · 11737 calls
    telemetry    mean   0.70 ms · worst   9.04 ms ·  17.7% of work · 11737 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 025 | | |
| 026 | | |
| 027 | | |
| 028 | | |
| 029 | | |
| 030 | | |
| 031 | | |
| 032 | | |

### 2026-11-12 14:35 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_143520 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 33) 큐브를 K2p3 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_143520.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 33–40

**결과** <!-- results:20261112_143520 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 14:46
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 33–40) · 전체 41개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 033 | 892 | 29.7 | 29.87 | 0/891 |  |
| 034 | 1132 | 37.7 | 29.89 | 0/1131 |  |
| 035 | 1330 | 44.3 | 29.87 | 0/1329 |  |
| 036 | 753 | 25.1 | 29.87 | 0/752 |  |
| 037 | 1101 | 36.7 | 29.87 | 0/1100 |  |
| 038 | 789 | 26.3 | 29.87 | 0/788 |  |
| 039 | 820 | 27.3 | 29.88 | 0/819 |  |
| 040 | 796 | 26.5 | 29.85 | 0/795 |  |

```
Cadence summary — whole run, 12 episodes · target 30 Hz (33.3 ms budget per tick): 9345 ticks, 9333 judged
  effective cadence: 29.87 Hz over 312.4 s measured
  ticks over the 33.3 ms work budget: 0/9333 (0.0%) — work mean 3.9 ms, worst 12.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 439
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   7.69 ms ·  36.5% of work · 9345 calls
    process_obs  mean   0.05 ms · worst   1.63 ms ·   1.4% of work · 9345 calls
    teleop       mean   1.16 ms · worst   5.58 ms ·  29.5% of work · 9345 calls
    send         mean   0.27 ms · worst   4.62 ms ·   6.9% of work · 9345 calls
    record       mean   0.24 ms · worst   2.54 ms ·   6.0% of work · 9345 calls
    telemetry    mean   0.70 ms · worst   9.96 ms ·  17.9% of work · 9345 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.6 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 033 | | |
| 034 | | |
| 035 | | |
| 036 | | |
| 037 | | |
| 038 | | |
| 039 | | |
| 040 | | |

### 2026-11-12 14:53 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_145302 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 41) 큐브를 K3p5 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_145302.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 41–48

**결과** <!-- results:20261112_145302 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 15:07
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 41–48) · 전체 49개 · 버린 에피소드(←) 7번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 041 | 1072 | 35.7 | 29.87 | 0/1071 |  |
| 042 | 1216 | 40.5 | 29.87 | 0/1215 |  |
| 043 | 1046 | 34.9 | 29.84 | 0/1045 |  |
| 044 | 1017 | 33.9 | 29.86 | 0/1016 |  |
| 045 | 1150 | 38.3 | 29.86 | 0/1149 |  |
| 046 | 885 | 29.5 | 29.87 | 0/884 |  |
| 047 | 1017 | 33.9 | 29.85 | 0/1016 |  |
| 048 | 1108 | 36.9 | 29.87 | 0/1107 |  |

```
Cadence summary — whole run, 15 episodes · target 30 Hz (33.3 ms budget per tick): 14272 ticks, 14257 judged
  effective cadence: 29.86 Hz over 477.5 s measured
  ticks over the 33.3 ms work budget: 0/14257 (0.0%) — work mean 4.0 ms, worst 11.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 868
  loop-body steps (share of measured work):
    observe      mean   1.45 ms · worst   6.43 ms ·  36.4% of work · 14272 calls
    process_obs  mean   0.06 ms · worst   1.16 ms ·   1.4% of work · 14272 calls
    teleop       mean   1.18 ms · worst   6.70 ms ·  29.5% of work · 14272 calls
    send         mean   0.28 ms · worst   5.06 ms ·   7.1% of work · 14272 calls
    record       mean   0.24 ms · worst   3.79 ms ·   6.1% of work · 14272 calls
    telemetry    mean   0.70 ms · worst   8.06 ms ·  17.6% of work · 14272 calls
  pacing headroom: 29.5 ms slept per tick on average (max 35.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 041 | | |
| 042 | | |
| 043 | | |
| 044 | | |
| 045 | | |
| 046 | | |
| 047 | | |
| 048 | | |

### 2026-11-12 15:07 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_150753 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 49) 큐브를 K8p7 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_150753.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 49–56

**결과** <!-- results:20261112_150753 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 15:17
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 49–56) · 전체 57개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 049 | 1265 | 42.2 | 29.88 | 0/1264 |  |
| 050 | 801 | 26.7 | 29.88 | 0/800 |  |
| 051 | 1258 | 41.9 | 29.87 | 0/1257 |  |
| 052 | 1179 | 39.3 | 29.86 | 0/1178 |  |
| 053 | 963 | 32.1 | 29.87 | 0/962 |  |
| 054 | 867 | 28.9 | 29.86 | 0/866 |  |
| 055 | 830 | 27.7 | 29.84 | 0/829 |  |
| 056 | 777 | 25.9 | 29.85 | 0/776 |  |

```
Cadence summary — whole run, 9 episodes · target 30 Hz (33.3 ms budget per tick): 7984 ticks, 7975 judged
  effective cadence: 29.86 Hz over 267.0 s measured
  ticks over the 33.3 ms work budget: 0/7975 (0.0%) — work mean 3.9 ms, worst 12.6 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 462
  loop-body steps (share of measured work):
    observe      mean   1.45 ms · worst   7.50 ms ·  36.7% of work · 7984 calls
    process_obs  mean   0.06 ms · worst   3.99 ms ·   1.5% of work · 7984 calls
    teleop       mean   1.16 ms · worst   7.01 ms ·  29.4% of work · 7984 calls
    send         mean   0.27 ms · worst   4.11 ms ·   6.9% of work · 7984 calls
    record       mean   0.24 ms · worst   1.85 ms ·   6.1% of work · 7984 calls
    telemetry    mean   0.69 ms · worst   9.10 ms ·  17.6% of work · 7984 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 049 | | |
| 050 | | |
| 051 | | |
| 052 | | |
| 053 | | |
| 054 | | |
| 055 | | |
| 056 | | |

### 2026-11-12 15:18 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_151818 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 57) 큐브를 K1p4 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_151818.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 57–64

**결과** <!-- results:20261112_151818 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 15:27
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 57–64) · 전체 65개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 057 | 825 | 27.5 | 29.87 | 0/824 |  |
| 058 | 999 | 33.3 | 29.86 | 0/998 |  |
| 059 | 752 | 25.1 | 29.84 | 0/751 |  |
| 060 | 1012 | 33.7 | 29.89 | 0/1011 |  |
| 061 | 963 | 32.1 | 29.87 | 0/962 |  |
| 062 | 801 | 26.7 | 29.86 | 0/800 |  |
| 063 | 789 | 26.3 | 29.86 | 0/788 |  |
| 064 | 999 | 33.3 | 29.86 | 0/998 |  |

```
Cadence summary — whole run, 8 episodes · target 30 Hz (33.3 ms budget per tick): 7140 ticks, 7132 judged
  effective cadence: 29.86 Hz over 238.8 s measured
  ticks over the 33.3 ms work budget: 0/7132 (0.0%) — work mean 4.0 ms, worst 11.5 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 397
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   5.56 ms ·  36.6% of work · 7140 calls
    process_obs  mean   0.06 ms · worst   1.38 ms ·   1.4% of work · 7140 calls
    teleop       mean   1.18 ms · worst   5.39 ms ·  29.5% of work · 7140 calls
    send         mean   0.29 ms · worst   4.49 ms ·   7.3% of work · 7140 calls
    record       mean   0.24 ms · worst   2.83 ms ·   6.0% of work · 7140 calls
    telemetry    mean   0.70 ms · worst   9.95 ms ·  17.4% of work · 7140 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 057 | | |
| 058 | | |
| 059 | | |
| 060 | | |
| 061 | | |
| 062 | | |
| 063 | | |
| 064 | | |

### 2026-11-12 15:29 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_152919 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 65) 큐브를 K4p7 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_152919.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 65–72

**결과** <!-- results:20261112_152919 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 15:39
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 65–72) · 전체 73개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 065 | 867 | 28.9 | 29.86 | 0/866 |  |
| 066 | 939 | 31.3 | 29.87 | 0/938 |  |
| 067 | 873 | 29.1 | 29.88 | 0/872 |  |
| 068 | 1503 | 50.1 | 29.86 | 0/1502 |  |
| 069 | 837 | 27.9 | 29.87 | 0/836 |  |
| 070 | 922 | 30.7 | 29.88 | 0/921 |  |
| 071 | 1142 | 38.1 | 29.83 | 0/1141 |  |
| 072 | 1059 | 35.3 | 29.85 | 0/1058 |  |

```
Cadence summary — whole run, 8 episodes · target 30 Hz (33.3 ms budget per tick): 8142 ticks, 8134 judged
  effective cadence: 29.86 Hz over 272.4 s measured
  ticks over the 33.3 ms work budget: 0/8134 (0.0%) — work mean 4.0 ms, worst 11.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 500
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   7.09 ms ·  36.5% of work · 8142 calls
    process_obs  mean   0.06 ms · worst   1.44 ms ·   1.5% of work · 8142 calls
    teleop       mean   1.17 ms · worst   5.70 ms ·  29.3% of work · 8142 calls
    send         mean   0.28 ms · worst   5.19 ms ·   7.0% of work · 8142 calls
    record       mean   0.24 ms · worst   1.81 ms ·   6.0% of work · 8142 calls
    telemetry    mean   0.72 ms · worst   8.95 ms ·  18.0% of work · 8142 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 065 | | |
| 066 | | |
| 067 | | |
| 068 | | |
| 069 | | |
| 070 | | |
| 071 | | |
| 072 | | |

### 2026-11-12 15:39 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_153920 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 73) 큐브를 K8p6 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_153920.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 73–80

**결과** <!-- results:20261112_153920 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 15:55
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 73–80) · 전체 81개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 073 | 729 | 24.3 | 29.87 | 0/728 |  |
| 074 | 1077 | 35.9 | 29.87 | 0/1076 |  |
| 075 | 1288 | 42.9 | 29.87 | 0/1287 |  |
| 076 | 753 | 25.1 | 29.86 | 0/752 |  |
| 077 | 934 | 31.1 | 29.85 | 0/933 |  |
| 078 | 862 | 28.7 | 29.88 | 0/861 |  |
| 079 | 987 | 32.9 | 29.87 | 0/986 |  |
| 080 | 921 | 30.7 | 29.87 | 0/920 |  |

```
Cadence summary — whole run, 10 episodes · target 30 Hz (33.3 ms budget per tick): 9274 ticks, 9264 judged
  effective cadence: 29.87 Hz over 310.2 s measured
  ticks over the 33.3 ms work budget: 0/9264 (0.0%) — work mean 3.9 ms, worst 10.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 495
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   5.78 ms ·  36.5% of work · 9274 calls
    process_obs  mean   0.06 ms · worst   1.48 ms ·   1.4% of work · 9274 calls
    teleop       mean   1.16 ms · worst   5.14 ms ·  29.6% of work · 9274 calls
    send         mean   0.27 ms · worst   4.58 ms ·   6.9% of work · 9274 calls
    record       mean   0.24 ms · worst   2.21 ms ·   6.0% of work · 9274 calls
    telemetry    mean   0.70 ms · worst   9.24 ms ·  17.7% of work · 9274 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 073 | | |
| 074 | | |
| 075 | | |
| 076 | | |
| 077 | | |
| 078 | | |
| 079 | | |
| 080 | | |

### 2026-11-12 16:05 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_160542 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 81) 큐브를 K1p7 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_160542.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 81–88

**결과** <!-- results:20261112_160542 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 16:14
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 81–88) · 전체 89개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 081 | 832 | 27.7 | 29.86 | 0/831 |  |
| 082 | 1133 | 37.8 | 29.89 | 0/1132 |  |
| 083 | 716 | 23.9 | 29.85 | 0/715 |  |
| 084 | 933 | 31.1 | 29.88 | 0/932 |  |
| 085 | 939 | 31.3 | 29.88 | 0/938 |  |
| 086 | 759 | 25.3 | 29.87 | 0/758 |  |
| 087 | 879 | 29.3 | 29.88 | 0/878 |  |
| 088 | 765 | 25.5 | 29.85 | 0/764 |  |

```
Cadence summary — whole run, 8 episodes · target 30 Hz (33.3 ms budget per tick): 6956 ticks, 6948 judged
  effective cadence: 29.87 Hz over 232.6 s measured
  ticks over the 33.3 ms work budget: 0/6948 (0.0%) — work mean 3.9 ms, worst 11.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 316
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   4.98 ms ·  36.6% of work · 6956 calls
    process_obs  mean   0.05 ms · worst   1.27 ms ·   1.4% of work · 6956 calls
    teleop       mean   1.16 ms · worst   4.78 ms ·  29.6% of work · 6956 calls
    send         mean   0.27 ms · worst   4.59 ms ·   6.8% of work · 6956 calls
    record       mean   0.23 ms · worst   2.36 ms ·   6.0% of work · 6956 calls
    telemetry    mean   0.70 ms · worst   7.56 ms ·  17.8% of work · 6956 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 081 | | |
| 082 | | |
| 083 | | |
| 084 | | |
| 085 | | |
| 086 | | |
| 087 | | |
| 088 | | |

### 2026-11-12 16:15 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_161505 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 89) 큐브를 K3 에 각도 45° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_161505.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 89–96

**결과** <!-- results:20261112_161505 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 16:24
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 89–96) · 전체 97개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 089 | 1055 | 35.2 | 29.89 | 0/1054 |  |
| 090 | 1306 | 43.5 | 29.88 | 0/1305 |  |
| 091 | 819 | 27.3 | 29.86 | 0/818 |  |
| 092 | 1042 | 34.7 | 29.88 | 0/1041 |  |
| 093 | 951 | 31.7 | 29.87 | 0/950 |  |
| 094 | 963 | 32.1 | 29.88 | 0/962 |  |
| 095 | 807 | 26.9 | 29.87 | 0/806 |  |
| 096 | 932 | 31.1 | 29.85 | 0/931 |  |

```
Cadence summary — whole run, 8 episodes · target 30 Hz (33.3 ms budget per tick): 7875 ticks, 7867 judged
  effective cadence: 29.87 Hz over 263.3 s measured
  ticks over the 33.3 ms work budget: 0/7867 (0.0%) — work mean 3.9 ms, worst 10.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 364
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   5.98 ms ·  36.8% of work · 7875 calls
    process_obs  mean   0.05 ms · worst   1.19 ms ·   1.4% of work · 7875 calls
    teleop       mean   1.16 ms · worst   5.61 ms ·  29.8% of work · 7875 calls
    send         mean   0.27 ms · worst   3.73 ms ·   6.9% of work · 7875 calls
    record       mean   0.24 ms · worst   3.31 ms ·   6.1% of work · 7875 calls
    telemetry    mean   0.67 ms · worst   8.12 ms ·  17.3% of work · 7875 calls
  pacing headroom: 29.6 ms slept per tick on average (max 34.0 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 089 | | |
| 090 | | |
| 091 | | |
| 092 | | |
| 093 | | |
| 094 | | |
| 095 | | |
| 096 | | |

### 2026-11-12 16:25 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261112_162537 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 SG50 = 일반 파지 시연 (큐브 위치 · 시작 자세만 다양화). 큐브 각도는 늘 0° (로봇 좌우축과 나란함) — Enter 로 확인
- 체크리스트 추가: 큐브 흰 스티커 면 · 크기 · 방향이 예비 시연 때와 같은가요? (config sg50.sticker 와 같아야 함) — Enter 로 확인
- 체크리스트 추가: 카메라 위치 · 조명 · 서보 설정을 예비 시연 뒤 바꾸지 않았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계 (노란 배너) 에서 큐브를 front 화면 흰 점선 자리에 놓고, 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: 첫 파지 실패 · 재파지 · 재정렬이 있었으면 결과 2/3 과 메모(m)로 남겨요 (자동으로 지우거나 성공으로 바꾸지 않음) — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 97) 큐브를 K1 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/sg_pin --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 4 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_sg_pin '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/sg_pin/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_162537.log`
- 계획: `~/so101_runs/main_k8/sg_pin/r12_plan.csv` · 이번 실행 episode 97–100

**결과** <!-- results:20261112_162537 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 16:30
- repo_id: `oxr/so101_k8_sg_pin` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 97–100) · 전체 101개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 097 | 970 | 32.3 | 29.87 | 0/969 |  |
| 098 | 1288 | 42.9 | 29.88 | 0/1287 |  |
| 099 | 879 | 29.3 | 29.86 | 0/878 |  |
| 100 | 826 | 27.5 | 29.88 | 0/825 |  |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 3963 ticks, 3959 judged
  effective cadence: 29.87 Hz over 132.5 s measured
  ticks over the 33.3 ms work budget: 0/3959 (0.0%) — work mean 3.9 ms, worst 12.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 195
  loop-body steps (share of measured work):
    observe      mean   1.43 ms · worst   5.91 ms ·  36.6% of work · 3963 calls
    process_obs  mean   0.05 ms · worst   1.64 ms ·   1.4% of work · 3963 calls
    teleop       mean   1.15 ms · worst   4.05 ms ·  29.4% of work · 3963 calls
    send         mean   0.27 ms · worst   3.32 ms ·   6.9% of work · 3963 calls
    record       mean   0.24 ms · worst   3.00 ms ·   6.1% of work · 3963 calls
    telemetry    mean   0.70 ms · worst   7.38 ms ·  17.9% of work · 3963 calls
  pacing headroom: 29.6 ms slept per tick on average (max 33.7 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 097 | | |
| 098 | | |
| 099 | | |
| 100 | | |
