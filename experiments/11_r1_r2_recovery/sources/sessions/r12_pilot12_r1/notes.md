# r12_pilot12_r1 (main_k8)

- 세션 폴더: `$HOME/so101_runs/main_k8/r12_pilot12_r1`
- dataset: `$HOME/so101_runs/main_k8/r12_pilot12_r1/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-03

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-04 14:17 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261104_141725 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R1 = 팔 접힘 지나침 → Pan 복구 (4편). 지나침 크기는 대략 20–25°, 실패 때의 −109° 를 재현하지 않아요 — Enter 로 확인
- 체크리스트 추가: 오차 상태(지나침)는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 주황 선은 참고 — 정확히 맞추지 않아도 됨 — Enter 로 확인
- 체크리스트 추가: Pan 을 한계 근처까지 돌리지 않기 (|pan| > 95 이면 녹화 시작 BLOCK, 녹화 중 Pan 명령은 ±95 에서 멈춤) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K4 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r1 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r1 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r1/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_141725.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r1/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261104_141725 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 14:23
- repo_id: `oxr/so101_k8_r12_pilot12_r1` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개 · 버린 에피소드(←) 2번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 494 | 16.5 | 29.87 | 0/493 |  |
| 001 | 470 | 15.7 | 29.87 | 0/469 |  |
| 002 | 524 | 17.5 | 29.87 | 0/523 |  |
| 003 | 577 | 19.2 | 29.85 | 0/576 |  |

```
Cadence summary — whole run, 6 episodes · target 30 Hz (33.3 ms budget per tick): 2891 ticks, 2885 judged
  effective cadence: 29.87 Hz over 96.6 s measured
  ticks over the 33.3 ms work budget: 0/2885 (0.0%) — work mean 3.9 ms, worst 11.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 138
  loop-body steps (share of measured work):
    observe      mean   1.42 ms · worst   5.04 ms ·  36.4% of work · 2891 calls
    process_obs  mean   0.05 ms · worst   1.27 ms ·   1.4% of work · 2891 calls
    teleop       mean   1.15 ms · worst   5.90 ms ·  29.6% of work · 2891 calls
    send         mean   0.30 ms · worst   5.55 ms ·   7.6% of work · 2891 calls
    record       mean   0.23 ms · worst   1.03 ms ·   5.8% of work · 2891 calls
    telemetry    mean   0.68 ms · worst   7.22 ms ·  17.4% of work · 2891 calls
  pacing headroom: 29.6 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |

### 2026-11-04 14:28 · 이어 찍기 (R1/R2 r12_collect) <!-- run:20261104_142812 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 파일럿 R1 = 팔 접힘 지나침 → Pan 복구 (4편). 지나침 크기는 대략 20–25°, 실패 때의 −109° 를 재현하지 않아요 — Enter 로 확인
- 체크리스트 추가: 오차 상태(지나침)는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 주황 선은 참고 — 정확히 맞추지 않아도 됨 — Enter 로 확인
- 체크리스트 추가: Pan 을 한계 근처까지 돌리지 않기 (|pan| > 95 이면 녹화 시작 BLOCK, 녹화 중 Pan 명령은 ±95 에서 멈춤) — Enter 로 확인
- 체크리스트 추가: 끝낼 때(Esc) 팔을 쉬는 자세에 두기 — 종료하면 토크가 꺼져요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 4) 큐브를 K4 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session main_k8/r12_pilot12_r1 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/r12_pilot12.yaml --num 4 --scale 0.8
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --resume=true --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_k8_r12_pilot12_r1 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/main_k8/r12_pilot12_r1/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261104_142812.log`
- 계획: `~/so101_runs/main_k8/r12_pilot12_r1/r12_plan.csv` · 이번 실행 episode 4–7

**결과** <!-- results:20261104_142812 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-04 14:32
- repo_id: `oxr/so101_k8_r12_pilot12_r1` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 4개 (episode 4–7) · 전체 8개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 004 | 428 | 14.3 | 29.88 | 0/427 |  |
| 005 | 386 | 12.9 | 29.87 | 0/385 |  |
| 006 | 470 | 15.7 | 29.87 | 0/469 |  |
| 007 | 476 | 15.9 | 29.88 | 0/475 |  |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 1760 ticks, 1756 judged
  effective cadence: 29.87 Hz over 58.8 s measured
  ticks over the 33.3 ms work budget: 0/1756 (0.0%) — work mean 4.0 ms, worst 11.1 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 79
  loop-body steps (share of measured work):
    observe      mean   1.47 ms · worst   4.49 ms ·  36.8% of work · 1760 calls
    process_obs  mean   0.06 ms · worst   1.17 ms ·   1.4% of work · 1760 calls
    teleop       mean   1.17 ms · worst   4.21 ms ·  29.2% of work · 1760 calls
    send         mean   0.32 ms · worst   4.14 ms ·   8.1% of work · 1760 calls
    record       mean   0.24 ms · worst   1.70 ms ·   5.9% of work · 1760 calls
    telemetry    mean   0.67 ms · worst   7.93 ms ·  16.8% of work · 1760 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 004 | | |
| 005 | | |
| 006 | | |
| 007 | | |
