# sg_pin_pilot2 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/sg_pin_pilot2`
- dataset: `$HOME/so101_runs/practice/sg_pin_pilot2/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-12

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-12 13:06 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261112_130658 -->

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
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K3 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/sg_pin_pilot2 --config $HOME/so101_runs/main_k8/r1_r2_collection/config/sg50.yaml --scale 0.9
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_sg_pin_pilot2 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=60 --dataset.reset_time_s=3600 --dataset.num_episodes=3 --dataset.root=$HOME/so101_runs/practice/sg_pin_pilot2/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261112_130658.log`
- 계획: `~/so101_runs/practice/sg_pin_pilot2/r12_plan.csv` · 이번 실행 episode 0–2

**결과** <!-- results:20261112_130658 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-12 13:08
- repo_id: `oxr/so101_sg_pin_pilot2` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=60 · reset_time_s=3600
- 에피소드: 이번 1개 (episode 0–0) · 전체 1개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 1091 | 36.4 | 29.86 | 0/1090 |  |

```
Cadence summary — whole run, 1 episode · target 30 Hz (33.3 ms budget per tick): 1091 ticks, 1090 judged
  effective cadence: 29.86 Hz over 36.5 s measured
  ticks over the 33.3 ms work budget: 0/1090 (0.0%) — work mean 3.9 ms, worst 9.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 64
  loop-body steps (share of measured work):
    observe      mean   1.42 ms · worst   4.28 ms ·  35.9% of work · 1091 calls
    process_obs  mean   0.06 ms · worst   1.07 ms ·   1.4% of work · 1091 calls
    teleop       mean   1.15 ms · worst   3.63 ms ·  29.2% of work · 1091 calls
    send         mean   0.29 ms · worst   4.19 ms ·   7.4% of work · 1091 calls
    record       mean   0.24 ms · worst   1.30 ms ·   6.0% of work · 1091 calls
    telemetry    mean   0.72 ms · worst   8.12 ms ·  18.2% of work · 1091 calls
  pacing headroom: 29.5 ms slept per tick on average (max 33.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
