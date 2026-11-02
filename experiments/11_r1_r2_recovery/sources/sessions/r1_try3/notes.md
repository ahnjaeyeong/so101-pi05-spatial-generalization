# r1_try3 (practice)

- 세션 폴더: `$HOME/so101_runs/practice/r1_try3`
- dataset: `$HOME/so101_runs/practice/r1_try3/dataset` (lerobot 원본 — 녹화 후 수정 금지)
- 만든 날: 2026-11-02

## 설정
- 과제:
- 물체·박스 위치: (setup_photos/ 참고)
- 조명·카메라:
- 기타:

## 녹화 기록
record_ui.py 가 실행마다 아래에 기록을 추가한다. **판별 메모** 칸은 직접 채운다.

### 2026-11-02 14:23 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_142341 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 재탐색·재정렬 (A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침). 손가락 미세 어긋남은 R2 — Enter 로 확인
- 체크리스트 추가: 오차 상태는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 틀린 쪽으로 일부러 움직이는 장면은 녹화하지 않아요 — Enter 로 확인
- 체크리스트 추가: 그리퍼는 d2 와 같이 열어 둔 채 시작. 편 팔에서는 그리퍼를 탁자에서 띄우고 상자·탁자에 닿지 않게 — Enter 로 확인
- 체크리스트 추가: 시나리오·위치·방향이 계획과 달라도 녹화돼요 (s 시나리오 · d 방향 · k/x 큐브 자리로 바꿔 기록). 막는 것은 안전 조건뿐 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 F2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try3
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_142341.log`
- 계획: `~/so101_runs/practice/r1_try3/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261102_142341 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 14:25
- repo_id: `oxr/so101_r1_try3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 14:36 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_143601 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 재탐색·재정렬 (A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침). 손가락 미세 어긋남은 R2 — Enter 로 확인
- 체크리스트 추가: 오차 상태는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 틀린 쪽으로 일부러 움직이는 장면은 녹화하지 않아요 — Enter 로 확인
- 체크리스트 추가: 그리퍼는 d2 와 같이 열어 둔 채 시작. 편 팔에서는 그리퍼를 탁자에서 띄우고 상자·탁자에 닿지 않게 — Enter 로 확인
- 체크리스트 추가: 시나리오·위치·방향이 계획과 달라도 녹화돼요 (s 시나리오 · d 방향 · k/x 큐브 자리로 바꿔 기록). 막는 것은 안전 조건뿐 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 F2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try3
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_143601.log`
- 계획: `~/so101_runs/practice/r1_try3/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261102_143601 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 14:36
- repo_id: `oxr/so101_r1_try3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 14:38 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_143855 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 재탐색·재정렬 (A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침). 손가락 미세 어긋남은 R2 — Enter 로 확인
- 체크리스트 추가: 오차 상태는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 틀린 쪽으로 일부러 움직이는 장면은 녹화하지 않아요 — Enter 로 확인
- 체크리스트 추가: 그리퍼는 d2 와 같이 열어 둔 채 시작. 편 팔에서는 그리퍼를 탁자에서 띄우고 상자·탁자에 닿지 않게 — Enter 로 확인
- 체크리스트 추가: 시나리오·위치·방향이 계획과 달라도 녹화돼요 (s 시나리오 · d 방향 · k/x 큐브 자리로 바꿔 기록). 막는 것은 안전 조건뿐 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 F2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try3
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_143855.log`
- 계획: `~/so101_runs/practice/r1_try3/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261102_143855 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 14:39
- repo_id: `oxr/so101_r1_try3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |

### 2026-11-02 14:43 · 새 녹화 (R1/R2 r12_collect) <!-- run:20261102_144322 -->

**녹화 전 점검**
- 카메라 기대값: `--camera-mode auto`
- twin_ws 컨테이너: 없음
- /dev/cam_front: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- /dev/cam_wrist: auto_exposure=3, exposure_time_absolute=156, white_balance_automatic=1, white_balance_temperature=4600, exposure_dynamic_framerate=0 — auto 기대값과 같음
- 체크리스트(팔로워 전원 재투입 / 카메라·박스 위치 / 리더 팔·손 안 보임): Enter 로 확인
- 체크리스트 추가: 이 세션은 R1 = Pan 재탐색·재정렬 (A 초기 방향 · B1 접근 중 반전 · B2 지나침 · B3 손목 놓침). 손가락 미세 어긋남은 R2 — Enter 로 확인
- 체크리스트 추가: 오차 상태는 준비 단계(녹화 안 함)에서 만들고, 녹화는 되돌리는 동작부터. 틀린 쪽으로 일부러 움직이는 장면은 녹화하지 않아요 — Enter 로 확인
- 체크리스트 추가: 그리퍼는 d2 와 같이 열어 둔 채 시작. 편 팔에서는 그리퍼를 탁자에서 띄우고 상자·탁자에 닿지 않게 — Enter 로 확인
- 체크리스트 추가: 시나리오·위치·방향이 계획과 달라도 녹화돼요 (s 시나리오 · d 방향 · k/x 큐브 자리로 바꿔 기록). 막는 것은 안전 조건뿐 — Enter 로 확인
- 체크리스트 추가: 첫 판(episode 0) 큐브를 F2 에 각도 0° 로 놓았나요? — Enter 로 확인
- 체크리스트 추가: 준비 단계(노란 배너)에서 리더로 시작 자세를 만든 뒤 → — 그 전 움직임은 녹화되지 않아요 — Enter 로 확인
- 체크리스트 추가: → 뒤 '저장 중'(파란 배너) 동안 리더 팔을 그대로 두기 — 저장이 끝나면 그 자세에서 바로 녹화 시작 — Enter 로 확인
- 체크리스트 추가: 필터 없음: 녹화 action = 리더 팔 값 그대로 (d2 와 같음) — Enter 로 확인

**명령**
```bash
$HOME/so101-env/bin/python $HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py record --session practice/r1_try3
```
실제 실행 (lerobot-record 대신 r12_record_entry.py — lerobot record() 그대로 + 준비 단계·화면 탭):
```bash
$HOME/so101_runs/main_k8/r1_r2_collection/tools/r12_record_entry.py --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader --dataset.no_stamp=true --dataset.push_to_hub=false --dataset.repo_id=oxr/so101_r1_try3 '--dataset.single_task=pick up the red cube and put it in the brown box' --dataset.episode_time_s=45 --dataset.reset_time_s=3600 --dataset.num_episodes=4 --dataset.root=$HOME/so101_runs/practice/r1_try3/dataset
```
- 원본 로그: `~/.local/state/record_ui/record_20261102_144322.log`
- 계획: `~/so101_runs/practice/r1_try3/r12_plan.csv` · 이번 실행 episode 0–3

**결과** <!-- results:20261102_144322 -->
- 종료: 정상 (코드 0) · 후처리 2026-11-02 14:44
- repo_id: `oxr/so101_r1_try3` · 과제: "pick up the red cube and put it in the brown box"
- 로봇 설정 (lerobot 설정 로그): P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30 · episode_time_s=45 · reset_time_s=3600
- 에피소드: 이번 0개 · 전체 0개

**판별 메모**

| ep | 판정 (성공/실패/버림) | 메모 |
|---|---|---|
| | | |
