# 01. 기존 d2 수집 파이프라인 조사

조사일 2026-10-30. 코드·데이터는 읽기만 했다. 값은 모두 파일·데이터에서 직접 확인한 것.

## 1. 실행 경로

| 단계 | 파일 | 내용 |
|---|---|---|
| 명령 모음 | `~/so101_runs/main_k8/redbox_수집명령.md` | 그룹마다 `record_ui.py` 명령 (첫 실행 / `--resume=true`) |
| 래퍼 | `~/so101_boxpick/scripts/record_ui.py` (1497줄) | 세션 폴더·녹화 전 점검·단계 배너·저장 중 키 차단·sidecar·후처리. `lerobot-record` 를 **pty 안에서** 실행 |
| 녹화 엔진 | `~/so101-env/bin/lerobot-record` → `lerobot/scripts/lerobot_record.py` (lerobot 0.6.2) | `record()` · `record_loop()` |
| 배치 계획 | `~/so101_boxpick/scripts/layout_plan.py` | 세션의 `layout.csv` (줄 i = episode i, K·각도) |
| 품질 검사 | `~/so101_boxpick/scripts/check_dataset.py`, `redbox_heatmap.py` | 녹화 후 `qa_report.md`, `qa/` |
| 설정 | `~/so101_boxpick/config/redbox8_layouts.yaml` | K1–K8 좌표, front H(cm→px), 색 HSV, 과제 문장 |
| 병합 | `lerobot-edit-dataset` (release 복사본) → `main_k8/d2/dataset` | t1_known·t1_random·t3_known·t3_random |

d2 세션 `notes.md` 에 남은 실제 lerobot 명령 (예: `main_k8/redbox_t3_known/notes.md` 34행):

```
lerobot-record --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4},
                     wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }'
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader
  --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true
  '--dataset.single_task=pick up the red cube and put it in the brown box'
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false --dataset.num_episodes=16
  --dataset.root=$HOME/so101_runs/main_k8/redbox_t3_known/dataset
```
같은 notes 65행 (lerobot 설정 로그): `P=16 · I=0 · D=32 · max_relative_target=None · use_degrees=True · fps=30`.

## 2. Leader / Follower · 카메라

- Follower `lerobot/robots/so_follower/so_follower.py` (`name = "so_follower"`), Leader `lerobot/teleoperators/so_leader/so_leader.py`.
- `record()` 는 리더를 먼저, 팔로워를 다음에 `connect()` (lerobot_record.py 484–488행).
- 카메라: OpenCV `/dev/cam_front`, `/dev/cam_wrist`, 640×480, 30 fps, MJPG, `warmup_s 4`. 팔로워 `get_observation()` 이 관절값과 두 영상을 함께 돌려준다.
- 캘리브레이션: `~/.cache/huggingface/lerobot/calibration/robots/so_follower/my_arm.json`, `.../teleoperators/so_leader/my_leader.json`.

## 3. 녹화 루프 · FPS · 시간

`record_loop()` (lerobot_record.py 228–383행) 한 틱:
1. `obs = robot.get_observation()` → `robot_observation_processor` (기본 항등) → `observation.*`
2. `act = teleop.get_action()` → `teleop_action_processor` (기본 항등) → **`action` 으로 기록**
3. `robot.send_action(...)` (보낸 값은 기록하지 않음. `max_relative_target=None` 이라 리더 값과 같음)
4. `dataset.add_frame({...observation, ...action, task})`
5. `display_data` 면 `log_visualization_data(...)` (d2 는 끔)
6. `CycleTimer.wait()` 로 30 Hz

- d2 `timestamp` = `frame_index / 30` (ep0 간격 0.0333 s 한 가지만 확인).
- 판 길이 (d2 256편): 최소 10.6 s · p5 11.9 · 중앙 15.6 · p95 21.3 · 최대 25.9 s.

## 4. `observation.state` · `action` 의미와 단위

| 항목 | 값 |
|---|---|
| 이름 (둘 다) | `shoulder_pan.pos, shoulder_lift.pos, elbow_flex.pos, wrist_flex.pos, wrist_roll.pos, gripper.pos` (float32 ×6) |
| `observation.state` | 팔로워 서보 현재 위치 |
| `action` | **리더 서보 위치 그대로** (항등 처리기, 필터 없음) |
| 관절 5개 단위 | `use_degrees=True` → `MotorNormMode.DEGREES`: (raw − (min+max)/2) × 360 / 4095 [°] |
| 그리퍼 단위 | `MotorNormMode.RANGE_0_100` (0 = 캘리브레이션 최소, 100 = 최대) |
| 그리퍼 값 (d2) | 닫힘 ≈ 1 (첫·끝 프레임 중앙 1.1) · 접근 중 열림 중앙 28.2 (p1 7.0, p99 42.7) |

팔로워 캘리브레이션 한계를 같은 식으로 바꾼 값: pan ±110.2°, lift ±103.7°, elbow ±96.7°, wrist_flex ±102.1°, wrist_roll ±180°.

d2 상태값 분포 (123,342 프레임, `observation.state`):

| | pan | lift | elbow | wflex | wroll | grip |
|---|---:|---:|---:|---:|---:|---:|
| 최소 | −108.5 | −103.3 | −82.1 | 1.6 | −57.0 | 0.8 |
| p0.5 | −102.8 | −103.1 | −66.0 | 25.1 | −49.5 | 0.9 |
| 중앙 | −2.8 | −10.8 | 34.5 | 68.7 | 3.1 | 1.2 |
| p99.5 | 99.1 | 55.0 | 96.2 | 98.7 | 47.0 | 40.0 |
| 최대 | 103.3 | 63.3 | 96.3 | 100.0 | 55.2 | 49.6 |

'처음 열기(명령 >15) → 처음 닫기(<10)' 구간 26,637 프레임의 p0.5–p99.5: pan −105.8…101.0, lift −30.4…57.5, elbow −62.8…58.0, wflex 44.9…96.0, wroll −55.3…50.6, grip 5.7…45.7.
(meta/stats.json 의 q01 등은 판별 값을 합친 근사라 위 직접 계산과 다르다.)

## 5. 필터

- 녹화 경로(`record_ui.py` → `lerobot-record`)에 필터 코드가 없다 (`record_ui.py` 에 `arm_filter` 문자열 없음, `teleop_action_processor` 기본 항등).
- `--arm_filter` / `--rollout_guard` 는 정책 추론 경로에만 있다: `main_k8/d2/eval/rollout_logged.py`, `eval_ui.py`.
- 따라서 R1/R2 녹화 action 은 d2 와 같이 리더 값 그대로. 필터 ON/OFF 는 추론 때 선택이며 데이터와 무관.

## 6. 판 진행 · 키 · 저장

- `record()` 판 반복 (lerobot_record.py 501–563행): `Recording episode N` → 녹화 루프 (`episode_time_s`) → (마지막 판이 아니거나 ← 이면) `Reset the environment` 녹화 안 하는 루프 (`reset_time_s`, 리더로 팔 조종) → ← 였으면 버퍼 비우고 같은 번호 다시, 아니면 `save_episode()`.
- **저장은 reset 단계가 끝난 뒤** 일어난다. reset 중 ← 를 누르면 방금 판을 버린다. 마지막 판 뒤에는 reset 이 없다.
- 키 (`lerobot/utils/keyboard_input.py`): → 또는 n = 루프 끝 · ← 또는 r = 다시 찍기 · Esc 또는 q = 종료. record_ui 는 자식에게 `XDG_SESSION_TYPE=wayland` 를 줘서 터미널 키 리스너를 쓰게 한다 → 키는 그 터미널에서.
- record_ui: 저장 중(`Map` 로그)에는 키를 버리고, Ctrl+C 는 항상 넘긴다.
- 홈 복귀: 자동 홈 동작이 없다. 사람이 리더로 쉬는 자세로 돌린다. d2 첫·끝 프레임 중앙값 pan −4.0, lift −102.9, elbow 96.1, wflex 61.8–62.1, wroll 2.4–2.7, grip 1.1.

## 7. 저장 구조 · 형식

- 세션 `~/so101_runs/main_k8/<세션>/`: `dataset/` (lerobot 원본), `layout.csv`·`layout_meta.json` (계획), `notes.md`, `review_videos/`, `setup_photos/`, `qa/`. 실행 기록 sidecar 는 `~/.local/state/record_ui/record_<시각>.{json,log}`.
- d2 `meta/info.json`: `codebase_version v3.0`, fps 30, `robot_type so_follower`, 256편 / 123,342 프레임, 과제 1개 (`pick up the red cube and put it in the brown box`), 영상 av1 · yuv420p · g 2 · crf 30 · preset 12, 640×480.
- LeRobot Dataset v3: `data/chunk-*/file-*.parquet`, `videos/<key>/chunk-*/file-*.mp4` (여러 판을 이은 파일), `meta/episodes/*.parquet` (판별 길이·영상 위치·통계).
- 판별 메타데이터(K, 각도)는 lerobot 표준 스키마가 아니라 `layout.csv` sidecar 로 관리됐다. `save_episode(episode_data=None)` 에 임의 필드를 넣는 인자는 없다.

## 8. 기존 수집 UI

- 터미널 배너만 (REC 흰색 / RESET 회색 / 저장 중 파랑 / 저장 완료 초록, K 격자·큐브 각도 그림).
- 녹화 중 실시간 영상 없음: lerobot 이 카메라를 쥐고 있고, `--display_data` (rerun) 는 so101-env 에 rerun 이 없어 안 씀.
- 별도 도구 `teleop_view.py` (Tk 창, 리더 조종 + 영상 + 관절 범위) 는 녹화하지 않는다.

## 9. R1/R2 에서 그대로 쓴 것

`record_ui.py` 의 `precheck` (twin_ws 컨테이너·카메라 v4l2 값 읽기 + 체크리스트), `run_lerobot` (pty·키 차단·로그), `UI` 배너·저장 판정, sidecar 형식, `--postprocess` (review 영상·첫 프레임·notes 결과), 그리고 lerobot `record()` 전체. 새 녹화 엔진은 만들지 않았다 (03 문서).
