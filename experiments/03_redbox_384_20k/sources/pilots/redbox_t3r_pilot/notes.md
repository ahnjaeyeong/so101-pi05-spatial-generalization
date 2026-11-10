# redbox_t3r_pilot (practice)

- 세션 폴더: `$HOME/so101_runs/practice/redbox_t3r_pilot`
- dataset: `$HOME/so101_runs/practice/redbox_t3r_pilot/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 10:39 · 새 녹화 <!-- run:20261014_103939 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3R01: 자유 배치 (빨간 큐브 1 · 파란 큐브 1 · 초록 큐브 1) — K1, K2, K3, K4 에서 3 cm 넘게, 서로 8 cm 넘게 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/redbox_t3r_pilot --layout auto --target-episodes 4 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3r_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t3r_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/redbox_t3r_pilot/dataset --dataset.num_episodes=4
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_103939.log`
- 목표: 유효 4편 (계획 줄 4 = 유효 4 + 제외 0) · 실행 전 0편 · 남은 4편 · 이번 num_episodes=4
- 배치 계획: `$HOME/so101_runs/practice/redbox_t3r_pilot/layout.csv` (그룹 `t3_random`) · 이번 실행 배치 0=T3R01, 1=T3R02, 2=T3R03, 3=T3R04

**결과** <!-- results:20261014_103939 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 10:42
- repo_id: `oxr/so101_redbox_t3r_pilot` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 476 | 15.9 | 29.90 | 0/475 | T3R01 |
| 001 | 538 | 17.9 | 29.89 | 0/537 | T3R02 |
| 002 | 485 | 16.2 | 29.89 | 0/484 | T3R03 |
| 003 | 496 | 16.5 | 29.91 | 0/495 | T3R04 |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 1995 ticks, 1991 judged
  effective cadence: 29.90 Hz over 66.6 s measured
  ticks over the 33.3 ms work budget: 0/1991 (0.0%) — work mean 3.0 ms, worst 11.5 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 43
  loop-body steps (share of measured work):
    observe      mean   1.33 ms · worst   9.38 ms ·  44.9% of work · 1995 calls
    process_obs  mean   0.04 ms · worst   0.31 ms ·   1.5% of work · 1995 calls
    teleop       mean   1.12 ms · worst   3.53 ms ·  37.7% of work · 1995 calls
    send         mean   0.22 ms · worst   2.97 ms ·   7.4% of work · 1995 calls
    record       mean   0.20 ms · worst   1.36 ms ·   6.7% of work · 1995 calls
  pacing headroom: 30.5 ms slept per tick on average (max 32.7 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
