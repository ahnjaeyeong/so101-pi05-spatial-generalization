# r1_try2 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/r1_try2`
- dataset: `$HOME/so101_runs/practice/r1_try2/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-02

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-02 13:52 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_135216 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 재탐색·재정렬이에요. 손가락이 큐브 옆으로 조금 어긋난 장면은 R2 세션에서 찍어요 — Enter 로 확인
- 체크리스트 추가: 잘못된 시작 자세는 준비 단계(녹화 안 함)에서 만들어요: 팔을 접은 채 Pan 을 주황 선으로 → (접근 중간이면) 그다음 팔을 폄. 녹화는 고쳐 돌아오는 동작만 — Enter 로 확인
- 체크리스트 추가: 그리퍼는 d2 와 같이 열어 둔 채 시작. 탁자·상자 충돌, 케이블 당김, 관절이 끝에 닿아 미는 자세면 오차를 줄이거나 그 판을 건너뛰기 — Enter 로 확인
- 체크리스트 추가: 손목 화면에 큐브가 안 보이는 판도 front 에는 큐브가 보여야 해요 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K6 에 각도 ↻30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try2
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try2 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try2/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_135216.log`
- 계획: `~/so101_runs/practice/r1_try2/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261102_135216 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 14:08
- repo_id: `oxr/so101_r1_try2` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 2개 (episode 0–1) · 전체 2개 · 버린 에피소드(←) 1번

| ep | 프레임 | 길이(s) | Cadence (Hz) | 기준 초과 프레임 | 배치 |
|---|---|---|---|---|---|
| 000 | 481 | 16.0 | 29.87 | 0/480 |  |
| 001 | 313 | 10.4 | 29.87 | 0/312 |  |

```
Cadence summary — whole run, 3 episodes · target 30 Hz (33.3 ms budget per tick): 825 ticks, 822 judged
  effective cadence: 29.87 Hz over 27.5 s measured
  ticks over the 33.3 ms work budget: 0/822 (0.0%) — work mean 4.0 ms, worst 9.4 ms
  ticks whose cadence slipped outside the loop body (sleep overshoot / CPU starvation while pacing): 47
  loop-body steps (share of measured work):
    observe      mean   1.45 ms · worst   3.80 ms ·  36.2% of work · 825 calls
    process_obs  mean   0.06 ms · worst   0.48 ms ·   1.5% of work · 825 calls
    teleop       mean   1.20 ms · worst   5.77 ms ·  29.8% of work · 825 calls
    send         mean   0.28 ms · worst   2.91 ms ·   6.9% of work · 825 calls
    record       mean   0.25 ms · worst   1.06 ms ·   6.2% of work · 825 calls
    telemetry    mean   0.70 ms · worst   5.02 ms ·  17.5% of work · 825 calls
  pacing headroom: 29.4 ms slept per tick on average (max 33.8 ms) — near zero means the loop is saturated
```

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| 000 | | |
| 001 | | |
