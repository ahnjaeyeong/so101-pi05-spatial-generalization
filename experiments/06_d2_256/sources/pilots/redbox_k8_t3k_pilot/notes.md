# redbox_k8_t3k_pilot (practice)

- 세션 폴더: `$HOME/so101_runs/practice/redbox_k8_t3k_pilot`
- dataset: `$HOME/so101_runs/practice/redbox_k8_t3k_pilot/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-10-22

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-10-22 15:08 · 새 녹화 <!-- run:20261022_150808 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=1 — ⚠ auto 기대값과 다름 (exposure_dynamic_framerate=1→0)
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=1 — ⚠ auto 기대값과 다름 (exposure_dynamic_framerate=1→0)
- 경고가 있었지만 계속 진행함
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 배치 T3K1-G6B7O8 · 4개 · K1(빨강 45°) · K2() · K3() · K4() · K5() · K6(초록 0°) · K7(파랑 45°) · K8(주황 ↺30°) 대로 놓았나요? — Enter 로 확인

**명령**
```bash
python3 $HOME/so101_boxpick/scripts/record_ui.py --session practice/redbox_k8_t3k_pilot --layout auto --target-episodes 4 --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_k8_t3k_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=4
```
실제 lerobot 명령:
```bash
$HOME/so101-env/bin/lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.repo_id=oxr/so101_redbox_k8_t3k_pilot --dataset.no_stamp=true '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/redbox_k8_t3k_pilot/dataset
```
- 원본 로그: `$HOME/.local/state/record_ui/record_20261022_150808.log`
- 목표: 유효 4편 (계획 줄 4 = 유효 4 + 제외 0) · 실행 전 0편 · 남은 4편 · 이번 num_episodes=4
- 배치 계획: `$HOME/so101_runs/practice/redbox_k8_t3k_pilot/layout.csv` (그룹 `t3_known`) · 이번 실행 배치 0=T3K1-G6B7O8, 1=T3K6-B1G2, 2=T3K3-Y4O8, 3=T3K8-Y6

**결과** <!-- results:20261022_150808 -->
- 종료: 정상 (코드 0) · 후처리 2026-10-22 15:11
- repo_id: `oxr/so101_redbox_k8_t3k_pilot` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=120
- 에피소드: 이번 4개 (episode 0–3) · 전체 4개

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 509 | 17.0 | 29.92 | 0/508 | T3K1-G6B7O8 |
| 001 | 515 | 17.2 | 29.92 | 0/514 | T3K6-B1G2 |
| 002 | 691 | 23.0 | 29.91 | 0/690 | T3K3-Y4O8 |
| 003 | 599 | 20.0 | 29.92 | 0/598 | T3K8-Y6 |

```
Cadence summary — whole run, 4 episodes · target 30 Hz (33.3 ms budget per tick): 2314 ticks, 2310 judged
  effective cadence: 29.92 Hz over 77.2 s measured
  ticks over the 33.3 ms work budget: 0/2310 (0.0%) — work mean 2.8 ms, worst 22.7 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 26
  loop-body steps (share of measured work):
    observe      mean   1.25 ms · worst  20.75 ms ·  45.0% of work · 2314 calls
    process_obs  mean   0.03 ms · worst   0.16 ms ·   1.0% of work · 2314 calls
    teleop       mean   1.09 ms · worst   4.17 ms ·  39.3% of work · 2314 calls
    send         mean   0.21 ms · worst   3.01 ms ·   7.5% of work · 2314 calls
    record       mean   0.16 ms · worst   1.09 ms ·   5.6% of work · 2314 calls
  pacing headroom: 30.6 ms slept per tick on average (max 32.4 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
| 002 | | |
| 003 | | |
