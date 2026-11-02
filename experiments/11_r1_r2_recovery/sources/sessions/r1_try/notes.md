# r1_try (practice)

- 세션 폴더: `$HOME/so101_runs/practice/r1_try`
- dataset: `$HOME/so101_runs/practice/r1_try/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-02

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-02 13:20 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_132053 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 방향 재정렬이에요. 손가락이 큐브 옆으로 조금 어긋난 장면은 R2 세션에서 찍어요 — Enter 로 확인
- 체크리스트 추가: 시작은 쉬는 자세 (준비 단계에서 큐브 각도만 맞춤). Pan 어긋남은 녹화 중에 만들고, 주황 선에 닿으면 Space — Enter 로 확인
- 체크리스트 추가: 어긋남 크기는 대략이면 돼요 (주황 선 근처). Pan 절댓값 90° 넘게 돌리지 않기 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 K7 에 각도 ↺30° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_132053.log`
- 계획: `~/so101_runs/practice/r1_try/r12_plan.csv` · 이번 실행 episode 0–3
