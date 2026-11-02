# redbox_t1k_pilot (practice)

- 세션 폴더: `$HOME/so101_runs/practice/redbox_t1k_pilot`
- dataset: `$HOME/so101_runs/practice/redbox_t1k_pilot/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-13

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-13 17:47 · 새 녹화 <!-- run:20261013_174749 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T1K1: 빨간 큐브 K1(-20.2,31.5) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/redbox_t1k_pilot --layout auto --target-episodes 8 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1k_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=4 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t1k_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.num_episodes=4 --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/redbox_t1k_pilot/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261013_174749.log`
- 목표: 유효 8편 (계획 줄 8 = 유효 8 + 제외 0) · 실행 전 0편 · 남은 8편 · 이번 num_episodes=4
- 배치 계획: `$HOME/so101_runs/practice/redbox_t1k_pilot/layout.csv` (그룹 `t1_known`) · 이번 실행 배치 0=T1K1, 1=T1K4, 2=T1K2, 3=T1K3

**결과** <!-- results:20261013_174749 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-13 17:50
- repo_id: `oxr/so101_redbox_t1k_pilot` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 532 | 17.7 | 29.90 | 0/531 | T1K1 |
| 001 | 539 | 18.0 | 29.89 | 0/538 | T1K4 |
| 002 | 438 | 14.6 | 29.89 | 0/437 | T1K2 |
| 003 | 419 | 14.0 | 29.90 | 0/418 | T1K3 |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 1928 ticks, 1924 judged
  effective cadence: 29.90 Hz over 64.4 s measured
  ticks over the 33.3 ms work budget: 0/1924 (0.0%) — work mean 3.0 ms, worst 21.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 47
  loop-body steps (share of measured work):
    observe      mean   1.36 ms · worst  19.15 ms ·  45.3% of work · 1928 calls
    process_obs  mean   0.04 ms · worst   0.28 ms ·   1.4% of work · 1928 calls
    teleop       mean   1.12 ms · worst   4.85 ms ·  37.2% of work · 1928 calls
    send         mean   0.23 ms · worst   3.35 ms ·   7.7% of work · 1928 calls
    record       mean   0.19 ms · worst   0.97 ms ·   6.5% of work · 1928 calls
  pacing headroom: 30.4 ms slept per tick on average (max 34.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
