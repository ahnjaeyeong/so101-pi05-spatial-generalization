# sg50_pilot3 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/sg50_pilot3`
- dataset: `$HOME/so101_runs/practice/sg50_pilot3/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-06

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-06 10:55 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_105523 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=40 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_105523.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–39

### 2026-11-06 11:01 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_110115 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=40 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_110115.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–39

### 2026-11-06 11:03 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_110334 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=40 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_110334.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–39

### 2026-11-06 11:31 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_113136 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_113136.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_113136 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 11:43
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 0–7) · 전체 8개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 1120 | 37.3 | 29.88 | 0/1119 |  |
| 001 | 843 | 28.1 | 29.86 | 0/842 |  |
| 002 | 994 | 33.1 | 29.87 | 0/993 |  |
| 003 | 782 | 26.1 | 29.86 | 0/781 |  |
| 004 | 939 | 31.3 | 29.87 | 0/938 |  |
| 005 | 1155 | 38.5 | 29.85 | 0/1154 |  |
| 006 | 867 | 28.9 | 29.87 | 0/866 |  |
| 007 | 717 | 23.9 | 29.87 | 0/716 |  |

```
Cadence summary — whole run, 10 episodes · target 30 Hz (33.3 ms budget per tick): 8472 ticks, 8462 judged
  effective cadence: 29.87 Hz over 283.3 s measured
  ticks over the 33.3 ms work budget: 0/8462 (0.0%) — work mean 4.0 ms, worst 11.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 399
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   5.74 ms ·  36.6% of work · 8472 calls
    process_obs  mean   0.06 ms · worst   1.90 ms ·   1.4% of work · 8472 calls
    teleop       mean   1.17 ms · worst   5.88 ms ·  29.2% of work · 8472 calls
    send         mean   0.28 ms · worst   3.90 ms ·   6.9% of work · 8472 calls
    record       mean   0.24 ms · worst   4.50 ms ·   6.1% of work · 8472 calls
    telemetry    mean   0.72 ms · worst   8.20 ms ·  17.9% of work · 8472 calls
  pacing headroom: 29.5 ms slept per tick on average (max 41.8 ms) — near zero means the loop is saturated
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

### 2026-11-06 13:03 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_130353 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_130353.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_130353 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 13:13
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-06 13:28 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_132855 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_132855.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_132855 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 13:42
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 0–7) · 전체 8개 · 버린 에피소드(←) 8번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 904 | 30.1 | 29.88 | 0/903 |  |
| 001 | 711 | 23.7 | 29.88 | 0/710 |  |
| 002 | 1095 | 36.5 | 29.89 | 0/1094 |  |
| 003 | 789 | 26.3 | 29.87 | 0/788 |  |
| 004 | 752 | 25.1 | 29.86 | 0/751 |  |
| 005 | 1168 | 38.9 | 29.88 | 0/1167 |  |
| 006 | 765 | 25.5 | 29.87 | 0/764 |  |
| 007 | 812 | 27.1 | 29.86 | 0/811 |  |

```
Cadence summary — whole run, 16 episodes · target 30 Hz (33.3 ms budget per tick): 11388 ticks, 11372 judged
  effective cadence: 29.87 Hz over 380.7 s measured
  ticks over the 33.3 ms work budget: 0/11372 (0.0%) — work mean 4.0 ms, worst 12.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 549
  loop-body steps (share of measured work):
    observe      mean   1.45 ms · worst   5.23 ms ·  36.6% of work · 11388 calls
    process_obs  mean   0.06 ms · worst   1.68 ms ·   1.4% of work · 11388 calls
    teleop       mean   1.16 ms · worst   5.40 ms ·  29.3% of work · 11388 calls
    send         mean   0.28 ms · worst   3.47 ms ·   6.9% of work · 11388 calls
    record       mean   0.24 ms · worst   2.69 ms ·   6.1% of work · 11388 calls
    telemetry    mean   0.71 ms · worst   7.96 ms ·  17.8% of work · 11388 calls
  pacing headroom: 29.5 ms slept per tick on average (max 35.4 ms) — near zero means the loop is saturated
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

### 2026-11-06 13:47 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_134725 -->

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
- 체크리스트 추가: 첫 판(episode 8) 큐브를 K7r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_134725.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 8–15

**결과** <!-- results:20261106_134725 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 13:58
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 8–15) · 전체 16개 · 버린 에피소드(←) 7번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 008 | 975 | 32.5 | 29.88 | 0/974 |  |
| 009 | 813 | 27.1 | 29.88 | 0/812 |  |
| 010 | 1131 | 37.7 | 29.87 | 0/1130 |  |
| 011 | 674 | 22.5 | 29.88 | 0/673 |  |
| 012 | 915 | 30.5 | 29.86 | 0/914 |  |
| 013 | 686 | 22.9 | 29.86 | 0/685 |  |
| 014 | 729 | 24.3 | 29.87 | 0/728 |  |
| 015 | 711 | 23.7 | 29.89 | 0/710 |  |

```
Cadence summary — whole run, 15 episodes · target 30 Hz (33.3 ms budget per tick): 9078 ticks, 9063 judged
  effective cadence: 29.87 Hz over 303.4 s measured
  ticks over the 33.3 ms work budget: 0/9063 (0.0%) — work mean 4.0 ms, worst 15.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 415
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   6.80 ms ·  36.5% of work · 9078 calls
    process_obs  mean   0.06 ms · worst   1.51 ms ·   1.4% of work · 9078 calls
    teleop       mean   1.18 ms · worst   6.79 ms ·  29.5% of work · 9078 calls
    send         mean   0.28 ms · worst   6.44 ms ·   6.9% of work · 9078 calls
    record       mean   0.25 ms · worst   4.18 ms ·   6.2% of work · 9078 calls
    telemetry    mean   0.70 ms · worst   8.29 ms ·  17.6% of work · 9078 calls
  pacing headroom: 29.5 ms slept per tick on average (max 36.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 008 | | |
| 009 | | |
| 010 | | |
| 011 | | |
| 012 | | |
| 013 | | |
| 014 | | |
| 015 | | |

### 2026-11-06 14:19 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_141955 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_141955.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_141955 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 14:27
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-06 14:27 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_142710 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_142710.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_142710 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 14:27
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-06 14:34 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261106_143430 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K5r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_143430.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 0–7

**결과** <!-- results:20261106_143430 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 14:43
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 3개 (episode 0–2) · 전체 3개 · 버린 에피소드(←) 9번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 777 | 25.9 | 29.87 | 0/776 |  |
| 001 | 692 | 23.1 | 29.86 | 0/691 |  |
| 002 | 1257 | 41.9 | 29.86 | 0/1256 |  |

```
Cadence summary — whole run, 12 episodes · target 30 Hz (33.3 ms budget per tick): 7608 ticks, 7596 judged
  effective cadence: 29.87 Hz over 254.3 s measured
  ticks over the 33.3 ms work budget: 0/7596 (0.0%) — work mean 4.0 ms, worst 12.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 375
  loop-body steps (share of measured work):
    observe      mean   1.47 ms · worst   7.94 ms ·  36.9% of work · 7608 calls
    process_obs  mean   0.06 ms · worst   1.20 ms ·   1.4% of work · 7608 calls
    teleop       mean   1.18 ms · worst   5.25 ms ·  29.5% of work · 7608 calls
    send         mean   0.28 ms · worst   3.90 ms ·   7.0% of work · 7608 calls
    record       mean   0.24 ms · worst   3.97 ms ·   6.0% of work · 7608 calls
    telemetry    mean   0.70 ms · worst   7.59 ms ·  17.5% of work · 7608 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |

### 2026-11-06 14:45 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_144505 -->

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
- 체크리스트 추가: 첫 판(episode 3) 큐브를 K1r1 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_144505.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 3–10

**결과** <!-- results:20261106_144505 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 14:55
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 3–10) · 전체 11개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 003 | 927 | 30.9 | 29.88 | 0/926 |  |
| 004 | 981 | 32.7 | 29.87 | 0/980 |  |
| 005 | 938 | 31.3 | 29.85 | 0/937 |  |
| 006 | 837 | 27.9 | 29.86 | 0/836 |  |
| 007 | 903 | 30.1 | 29.87 | 0/902 |  |
| 008 | 843 | 28.1 | 29.87 | 0/842 |  |
| 009 | 1035 | 34.5 | 29.86 | 0/1034 |  |
| 010 | 716 | 23.9 | 29.83 | 0/715 |  |

```
Cadence summary — whole run, 11 episodes · target 30 Hz (33.3 ms budget per tick): 8098 ticks, 8087 judged
  effective cadence: 29.86 Hz over 270.8 s measured
  ticks over the 33.3 ms work budget: 0/8087 (0.0%) — work mean 4.0 ms, worst 12.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 410
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   8.83 ms ·  36.7% of work · 8098 calls
    process_obs  mean   0.06 ms · worst   0.90 ms ·   1.4% of work · 8098 calls
    teleop       mean   1.18 ms · worst   4.95 ms ·  29.5% of work · 8098 calls
    send         mean   0.28 ms · worst   3.85 ms ·   7.0% of work · 8098 calls
    record       mean   0.25 ms · worst   1.79 ms ·   6.2% of work · 8098 calls
    telemetry    mean   0.69 ms · worst   9.68 ms ·  17.3% of work · 8098 calls
  pacing headroom: 29.5 ms slept per tick on average (max 35.1 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 003 | | |
| 004 | | |
| 005 | | |
| 006 | | |
| 007 | | |
| 008 | | |
| 009 | | |
| 010 | | |

### 2026-11-06 14:55 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_145530 -->

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
- 체크리스트 추가: 첫 판(episode 11) 큐브를 K3r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_145530.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 11–18

**결과** <!-- results:20261106_145530 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 15:10
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 11–18) · 전체 19개 · 버린 에피소드(←) 3번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 011 | 796 | 26.5 | 29.88 | 0/795 |  |
| 012 | 1173 | 39.1 | 29.88 | 0/1172 |  |
| 013 | 855 | 28.5 | 29.87 | 0/854 |  |
| 014 | 824 | 27.5 | 29.85 | 0/823 |  |
| 015 | 722 | 24.1 | 29.87 | 0/721 |  |
| 016 | 747 | 24.9 | 29.86 | 0/746 |  |
| 017 | 777 | 25.9 | 29.86 | 0/776 |  |
| 018 | 687 | 22.9 | 29.86 | 0/686 |  |

```
Cadence summary — whole run, 11 episodes · target 30 Hz (33.3 ms budget per tick): 8049 ticks, 8038 judged
  effective cadence: 29.86 Hz over 269.2 s measured
  ticks over the 33.3 ms work budget: 0/8038 (0.0%) — work mean 4.0 ms, worst 11.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 409
  loop-body steps (share of measured work):
    observe      mean   1.47 ms · worst   4.96 ms ·  36.5% of work · 8049 calls
    process_obs  mean   0.06 ms · worst   2.50 ms ·   1.4% of work · 8049 calls
    teleop       mean   1.18 ms · worst   6.70 ms ·  29.4% of work · 8049 calls
    send         mean   0.28 ms · worst   4.96 ms ·   7.0% of work · 8049 calls
    record       mean   0.24 ms · worst   4.74 ms ·   6.1% of work · 8049 calls
    telemetry    mean   0.72 ms · worst   8.58 ms ·  17.8% of work · 8049 calls
  pacing headroom: 29.4 ms slept per tick on average (max 35.3 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 011 | | |
| 012 | | |
| 013 | | |
| 014 | | |
| 015 | | |
| 016 | | |
| 017 | | |
| 018 | | |

### 2026-11-06 15:16 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_151610 -->

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
- 체크리스트 추가: 첫 판(episode 19) 큐브를 K2r2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_151610.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 19–26

**결과** <!-- results:20261106_151610 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 15:25
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 19–26) · 전체 27개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 019 | 645 | 21.5 | 29.89 | 0/644 |  |
| 020 | 982 | 32.7 | 29.88 | 0/981 |  |
| 021 | 795 | 26.5 | 29.86 | 0/794 |  |
| 022 | 963 | 32.1 | 29.88 | 0/962 |  |
| 023 | 735 | 24.5 | 29.87 | 0/734 |  |
| 024 | 927 | 30.9 | 29.87 | 0/926 |  |
| 025 | 950 | 31.7 | 29.83 | 0/949 |  |
| 026 | 662 | 22.1 | 29.86 | 0/661 |  |

```
Cadence summary — whole run, 10 episodes · target 30 Hz (33.3 ms budget per tick): 6963 ticks, 6953 judged
  effective cadence: 29.87 Hz over 232.8 s measured
  ticks over the 33.3 ms work budget: 0/6953 (0.0%) — work mean 3.9 ms, worst 12.9 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 336
  loop-body steps (share of measured work):
    observe      mean   1.45 ms · worst   8.44 ms ·  36.6% of work · 6963 calls
    process_obs  mean   0.06 ms · worst   1.24 ms ·   1.4% of work · 6963 calls
    teleop       mean   1.16 ms · worst   7.20 ms ·  29.4% of work · 6963 calls
    send         mean   0.28 ms · worst   3.59 ms ·   7.0% of work · 6963 calls
    record       mean   0.24 ms · worst   2.13 ms ·   6.1% of work · 6963 calls
    telemetry    mean   0.69 ms · worst   9.74 ms ·  17.5% of work · 6963 calls
  pacing headroom: 29.5 ms slept per tick on average (max 34.5 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 019 | | |
| 020 | | |
| 021 | | |
| 022 | | |
| 023 | | |
| 024 | | |
| 025 | | |
| 026 | | |

### 2026-11-06 15:27 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_152714 -->

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
- 체크리스트 추가: 첫 판(episode 27) 큐브를 K7r2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_152714.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 27–34

**결과** <!-- results:20261106_152714 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 15:38
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 27–34) · 전체 35개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 027 | 879 | 29.3 | 29.86 | 0/878 |  |
| 028 | 819 | 27.3 | 29.87 | 0/818 |  |
| 029 | 807 | 26.9 | 29.87 | 0/806 |  |
| 030 | 548 | 18.3 | 29.85 | 0/547 |  |
| 031 | 806 | 26.9 | 29.86 | 0/805 |  |
| 032 | 1190 | 39.7 | 29.82 | 0/1189 |  |
| 033 | 806 | 26.9 | 29.86 | 0/805 |  |
| 034 | 818 | 27.3 | 29.86 | 0/817 |  |

```
Cadence summary — whole run, 12 episodes · target 30 Hz (33.3 ms budget per tick): 10586 ticks, 10574 judged
  effective cadence: 29.86 Hz over 354.1 s measured
  ticks over the 33.3 ms work budget: 0/10574 (0.0%) — work mean 4.0 ms, worst 12.8 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 520
  loop-body steps (share of measured work):
    observe      mean   1.48 ms · worst   6.22 ms ·  36.5% of work · 10586 calls
    process_obs  mean   0.06 ms · worst   2.47 ms ·   1.5% of work · 10586 calls
    teleop       mean   1.19 ms · worst   6.81 ms ·  29.3% of work · 10586 calls
    send         mean   0.28 ms · worst   4.13 ms ·   6.9% of work · 10586 calls
    record       mean   0.24 ms · worst   2.44 ms ·   6.0% of work · 10586 calls
    telemetry    mean   0.72 ms · worst   8.94 ms ·  17.9% of work · 10586 calls
  pacing headroom: 29.4 ms slept per tick on average (max 35.5 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 027 | | |
| 028 | | |
| 029 | | |
| 030 | | |
| 031 | | |
| 032 | | |
| 033 | | |
| 034 | | |

### 2026-11-06 15:41 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261106_154124 -->

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
- 체크리스트 추가: 첫 판(episode 35) 큐브를 K4r4 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg50_pilot3 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --num 8 --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg50_pilot3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=8 --dataset.root=$HOME/so101_runs/practice/sg50_pilot3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261106_154124.log`
- 계획: `~/so101_runs/practice/sg50_pilot3/r12_plan.csv` · 이번 실행 episode 35–42

**결과** <!-- results:20261106_154124 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-06 15:51
- repo_id: `oxr/so101_sg50_pilot3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 8개 (episode 35–42) · 전체 43개 · 버린 에피소드(←) 4번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 035 | 693 | 23.1 | 29.88 | 0/692 |  |
| 036 | 693 | 23.1 | 29.88 | 0/692 |  |
| 037 | 849 | 28.3 | 29.88 | 0/848 |  |
| 038 | 837 | 27.9 | 29.86 | 0/836 |  |
| 039 | 849 | 28.3 | 29.85 | 0/848 |  |
| 040 | 687 | 22.9 | 29.87 | 0/686 |  |
| 041 | 680 | 22.7 | 29.85 | 0/679 |  |
| 042 | 891 | 29.7 | 29.87 | 0/890 |  |

```
Cadence summary — whole run, 12 episodes · target 30 Hz (33.3 ms budget per tick): 9034 ticks, 9022 judged
  effective cadence: 29.87 Hz over 302.0 s measured
  ticks over the 33.3 ms work budget: 0/9022 (0.0%) — work mean 4.0 ms, worst 12.2 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 409
  loop-body steps (share of measured work):
    observe      mean   1.46 ms · worst   6.28 ms ·  36.5% of work · 9034 calls
    process_obs  mean   0.06 ms · worst   2.42 ms ·   1.4% of work · 9034 calls
    teleop       mean   1.18 ms · worst   6.20 ms ·  29.4% of work · 9034 calls
    send         mean   0.29 ms · worst   3.90 ms ·   7.2% of work · 9034 calls
    record       mean   0.24 ms · worst   2.75 ms ·   6.1% of work · 9034 calls
    telemetry    mean   0.70 ms · worst  12.71 ms ·  17.6% of work · 9034 calls
  pacing headroom: 29.4 ms slept per tick on average (max 34.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 035 | | |
| 036 | | |
| 037 | | |
| 038 | | |
| 039 | | |
| 040 | | |
| 041 | | |
| 042 | | |
