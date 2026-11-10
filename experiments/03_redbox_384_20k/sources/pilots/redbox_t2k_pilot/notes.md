# redbox_t2k_pilot (practice)

- 세션 폴더: `$HOME/so101_runs/practice/redbox_t2k_pilot`
- dataset: `$HOME/so101_runs/practice/redbox_t2k_pilot/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-14

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-14 10:34 · 새 녹화 <!-- run:20261014_103417 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T2K1K3K4: 빨간 큐브 K1(-20.2,31.5) · 빨간 큐브 K3(-7.8,12.7) · 빨간 큐브 K4(-15.4,2.6) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/redbox_t2k_pilot --layout auto --target-episodes 4 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2k_pilot --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=90 --dataset.reset_time_s=120 --dataset.push_to_hub=false
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_t2k_pilot --dataset.no_stamp=true '--dataset.single_task=put all the red cubes in the brown box' --dataset.episode_time_s=90 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.root=$HOME/so101_runs/practice/redbox_t2k_pilot/dataset --dataset.num_episodes=4
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261014_103417.log`
- 목표: 유효 4편 (계획 줄 4 = 유효 4 + 제외 0) · 실행 전 0편 · 남은 4편 · 이번 num_episodes=4
- 배치 계획: `$HOME/so101_runs/practice/redbox_t2k_pilot/layout.csv` (그룹 `t2_known`) · 이번 실행 배치 0=T2K1K3K4, 1=T2K2K3K4, 2=T2K1K2K3, 3=T2K1K2K4

**결과** <!-- results:20261014_103417 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-14 10:38
- repo_id: `oxr/so101_redbox_t2k_pilot` · 과제: "put all the red cubes in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=90 · reset_time_s=120
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 1043 | 34.8 | 29.90 | 0/1042 | T2K1K3K4 |
| 001 | 836 | 27.9 | 29.90 | 0/835 | T2K2K3K4 |
| 002 | 717 | 23.9 | 29.90 | 0/716 | T2K1K2K3 |
| 003 | 866 | 28.9 | 29.88 | 0/865 | T2K1K2K4 |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 3462 ticks, 3458 judged
  effective cadence: 29.89 Hz over 115.7 s measured
  ticks over the 33.3 ms work budget: 0/3458 (0.0%) — work mean 3.0 ms, worst 22.3 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 79
  loop-body steps (share of measured work):
    observe      mean   1.33 ms · worst  20.68 ms ·  44.6% of work · 3462 calls
    process_obs  mean   0.04 ms · worst   0.59 ms ·   1.5% of work · 3462 calls
    teleop       mean   1.12 ms · worst   4.75 ms ·  37.5% of work · 3462 calls
    send         mean   0.23 ms · worst   3.58 ms ·   7.8% of work · 3462 calls
    record       mean   0.20 ms · worst   1.91 ms ·   6.7% of work · 3462 calls
  pacing headroom: 30.4 ms slept per tick on average (max 35.2 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
