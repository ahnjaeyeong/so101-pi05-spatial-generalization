# 파일 구조 정리 — 이동 계획표 (초안, 2026-10-21)

아직 아무것도 옮기지 않았다. 단계마다 확인받고 진행한다.

## 0. 원칙

| | 규칙 |
|---|---|
| 코드 | `~/so101_boxpick` (git) 한 곳. 세션 폴더로 복사하지 않고 `--session` 등 인자로 받는다. |
| 녹화 세션 | `so101_runs/practice/`, `so101_runs/main/` **경로 그대로** (아래 "바꾸지 않는 것") |
| 한 세션의 학습·실물 평가 | 그 세션의 `train/`, `eval/` (지금과 같음) |
| 여러 세션·오프라인 분석 | `so101_runs/analysis/<주제>_<날짜>/` (새로 만듦) |
| 외부 데이터 | `so101_runs/external/` |
| 문서 | `so101_runs/docs/` |
| 실행 환경 | `~/so101-env` (venv), `~/lerobot` (참고용 소스) — 둘 다 그대로 |

### 바꾸지 않는 것과 이유
| 대상 | 이유 |
|---|---|
| `practice/<세션>`, `main/<세션>` 경로 | 체크포인트 `train_config.json` 의 `dataset.root`, notes.md, layout.csv, eval 기록(study.json 등), record_ui·layout_plan·check_dataset 의 `--session main/…` 규칙에 경로가 들어 있다. |
| `main/redbox_all/` 전체 | **학습 중** (pid 1006632, 30k, 오늘 19시 전후 끝). 끝날 때까지 손대지 않는다. |
| 세션 `eval/` 안에 이미 있는 스크립트 복사본 | 그때 실제로 돌린 코드 기록이다. 그대로 두고, 앞으로는 복사하지 않는다. |
| 분석 폴더 안의 일회성 스크립트 (`p0_offline_replay/replay_sim.py` 등) | 결과와 한 묶음. 폴더째 옮긴다. |
| `e0_j0/` | `so101_boxpick/e0_j0/collect_runs.py` 의 기본 출력 위치. |
| `range_check/` | `teleop_view.py` 의 기본 출력 위치. |
| `~/so101-env`, `~/lerobot` | lerobot 수정 없음(567파일 해시 일치), 우리 파일 없음. |

## 1. so101_eval 을 따로 만들지 — 검토

**권장: 따로 만들지 않고 so101_boxpick 안에 둔다.** 근거 (import·경로 확인 결과):

| 평가 쪽 코드 | 함께 쓰는 boxpick 코드 |
|---|---|
| `eval_ab_ui.py` | `import eval_ui` |
| `eval_ui.py`, `eval_ab_ui.py` | record_ui 와 같은 세션 규칙(`RECORD_UI_RUNS`, `<카테고리>/<세션>`) |
| `eval_space_report.py`, `pregrasp_*.py`, `train_roll_*.py` | `import space_geom`, `check_dataset.py` 가 만든 `qa/positions.csv` |
| `pregrasp_review.py` | `import train_roll_census` |
| `eval_ab_child.py`, `rollout_logged.py` | 같은 `arm_filter.py` |
| `check_dataset.py`, `layout_plan.py` | `config/redbox_layouts.yaml` (평가 위치 해석에도 씀) |

- 나누면 `space_geom`·세션 규칙·설정 파일을 두 저장소가 같이 써야 해서, 한쪽만 바뀌면 어긋난다.
- boxpick 의 원래 범위(ROS·Unity)는 비어 있다(`converter/`, `docker/`, `ros2_ws/src/*` 는 `.gitkeep` 뿐). ROS 작업은 `~/Ros2`, `~/Ros2_e0j0` 에서 한다. 지금 boxpick 은 사실상 "lerobot 수집·학습·평가 도구" 저장소다.
- 따로 만들고 싶다면 평가만이 아니라 **수집·학습·평가·분석 도구 전체**를 새 저장소로 옮기는 편이 경계가 맞다 (예: `so101_tools`). 그 경우 3단계 표의 목적지 앞부분만 바뀐다.

## 2. 단계 A — 준비 (학습 중 가능, 파일 이동 없음)

| # | 할 일 | 비고 |
|---|---|---|
| A1 | boxpick untracked 코드 커밋 (현재 상태 그대로) | `scripts/*.py` 18개, `e0_j0/`, `config/redbox_layouts.yaml`, `docs/servo_dumps/`. 되돌릴 기준점. |
| A2 | so101_runs 코드·문서 목록과 md5 저장 | `analysis` 이동 뒤 비교용 |

## 3. 단계 B — 공용 평가 코드를 boxpick 으로 (학습 중 가능)

`main/redbox_all/eval/` 의 파일은 **복사**만 한다 (원본은 기록으로 남김).

| 원본 | → boxpick | 할 일 | 세션별 차이 (확인함) |
|---|---|---|---|
| `main/redbox_all/eval/rollout_logged.py` | `scripts/rollout_logged.py` | 그대로 | redbox_all 판이 상위 호환 (새 옵션 기본 꺼짐). 나머지 3벌은 옛 판 |
| `main/redbox_all/eval/arm_filter.py` | `scripts/arm_filter.py` | 그대로 | 1벌 |
| `main/redbox_all/eval/motor_check.py` | `scripts/motor_check.py` | 그대로 | 1벌 |
| `*/eval/plot_rollout.py` (4벌) | `scripts/plot_rollout.py` | 그대로 | 4벌 동일 |
| `*/eval/pose_check.py` (4벌) | `scripts/pose_check.py` | `--session` 인자 추가 | `DATASET = …` 한 줄만 다름 |
| `*/eval/analyze_rollout.py` (4벌) | `scripts/analyze_rollout.py` | `--session` 인자 추가 | `SESSION = …` 한 줄 + 설명 한 줄만 다름 |
| `*/eval/run_rollout.sh` (4벌) | `scripts/run_rollout.sh` | `SESSION`, `CKPT`, `TASK` 를 환경 변수로 | 기본 체크포인트·task 문장·옵션 설명이 다름 |
| `*/train/run_*.sh`, `launch_*.sh` (11개) | `scripts/train_launch.sh` (새 템플릿) | 원본은 그대로 둠 | 학습 기록이므로 |

같이 고칠 boxpick 코드:

| 파일:줄 | 지금 | 바꿀 것 |
|---|---|---|
| `scripts/eval_ui.py:818` | `<세션>/eval/pose_check.py` | `scripts/pose_check.py --session <세션>` |
| `scripts/eval_ui.py:855` | `<세션>/eval/analyze_rollout.py` | `scripts/analyze_rollout.py --session <세션>` |
| `scripts/eval_ab_ui.py:50` | `ARM_FILTER_DIR = ~/so101_runs/main/redbox_all/eval` | boxpick `scripts/` |
| `scripts/eval_ab_ui.py:635` | `…/main/redbox_all/eval/pose_check.py` | `scripts/pose_check.py --session main/redbox_all` |

## 4. 단계 C — so101_runs 맨 위 정리 (학습 끝난 뒤)

| 지금 | → 새 위치 | 경로를 고칠 곳 |
|---|---|---|
| `redbox_all/eval/` (7개 항목 전부) | `analysis/redbox_vibration_20261019/` | 아래 표 (접두어 하나만 바꾸면 됨) |
| `reference/analysis_20261019/` | `analysis/reference_sponge_20261019/` | 없음 (스크립트는 외부 데이터 경로만 씀) |
| `reference/aswinkumar99_so101_pick_place/` | `external/aswinkumar99_so101_pick_place/` | `analysis/reference_sponge_20261019/compute_metrics.py:24` |
| `camera_settings.md`, `camera_settings/` | `docs/camera_settings.md`, `docs/camera_settings/` | `scripts/record_ui.py:8` (설명), `README.md` |
| `ros2_guide.md` | `docs/ros2_guide.md` | 없음 |
| `rollout/이번 rollout 전에는 하나가 특히.txt` | `docs/rollout_precheck_20261008.md` | 없음 |
| `main/redbox_수집명령.md` | `docs/redbox_collect_commands.md` | 없음 |
| `calibration_backup_20261002/` | `backup/calibration_20261002/` | 없음 |
| `_deleted/` | 그대로 | — |
| `~/Desktop/redbox_*` (png 9개, svg 1개) | `docs/figures/redbox/` | 없음 |
| `~/평가.txt` | 지우거나 `docs/` 에 합침 | 없음 (eval_ui 명령 2줄) |

`redbox_all/eval` → `analysis/redbox_vibration_20261019` 로 바꿀 때 고칠 곳 (`~/so101_runs/redbox_all/eval` 문자열):

| 파일 | 종류 |
|---|---|
| `so101_boxpick/scripts/eval_ab_mock.py:18` | 실제 읽는 경로 (`servo_model_v2.json`) |
| `analysis/…/speed_scaling/speed_analysis.py:27` | 실제 경로 |
| `analysis/…/filter_validation/test_filter.py:23`, `wide_analysis.py:19` | 실제 경로 |
| `analysis/…/official_vs_custom/test_abc_path.py:20` | 실제 경로 |
| `analysis/…/eval_ab_tests/test_eval_ab_path.py:19` | 실제 경로 |
| `scripts/rollout_logged.py`, `scripts/arm_filter.py` (B단계 복사본) | 주석 (근거 문서 위치) |
| Claude 메모리 7개 파일 | 기록 |

`main/redbox_all/eval/` 안의 연구 폴더(`eval_ab/`, `eval_space/`, `pregrasp_*`, `train_roll_census/`)는 옮기지 않는다 — redbox_all 실물 평가 결과와 그 분석이고, boxpick 스크립트 기본 출력 위치다.

### 정리 뒤 so101_runs 맨 위
```
so101_runs/
├── README.md            새로 씀 (이 구조와 규칙)
├── description.md       현재 구성 (정리 뒤 다시 씀)
├── practice/  main/     녹화 세션 (경로 그대로)
├── analysis/            redbox_vibration_20261019/, reference_sponge_20261019/
├── external/            aswinkumar99_so101_pick_place/
├── docs/                camera_settings.md, ros2_guide.md, rollout_precheck_20261008.md, redbox_collect_commands.md, figures/, practice_10_pi05_2k.md
├── e0_j0/               그대로
├── range_check/         그대로
├── backup/              calibration_20261002/
└── _deleted/            그대로
```

## 5. 단계 D — so101_boxpick 정리

| # | 할 일 | 비고 |
|---|---|---|
| D1 | `record_ui.py` 의 `ROOT_README` 를 새 구조로 고침 | 지금 README 가 옛 구조인 원인 |
| D2 | README.md·STATUS.md 를 현재 쓰임새(수집·학습·평가·분석 도구 + e0_j0)로 다시 씀. 09-29 ROS 분리 설계 내용은 `docs/` 로 | |
| D3 | 빈 폴더 `converter/`, `docker/`, `ros2_ws/`, `calibration/urdf/` 정리 | 남길지 결정 필요 |
| D4 | (선택, 지금은 안 함) `scripts/` 를 `collect/ eval/ analysis/ tools/` 로 나누기 | 아래 이유로 코드 수정이 따라옴 |

D4 를 하면 고쳐야 하는 것: `layout_plan.py:63`·`check_dataset.py:811` (`config/` 를 `scripts` 의 상위 폴더로 찾음), `check_env.py:40`·`servo_dump.py:42` (`parents[1]`), 같은 폴더 import 6종(`layout_plan`, `space_geom`, `eval_ui`, `arm_filter`, `pregrasp_angles`, `train_roll_census`), notes.md·메모리에 적힌 `~/so101_boxpick/scripts/<이름>.py` 명령.

## 6. 단계 E — 확인

| 확인 | 방법 |
|---|---|
| 옛 경로가 코드에 남지 않음 | `grep -rn "so101_runs/redbox_all\|so101_runs/reference" ~/so101_boxpick ~/so101_runs/analysis` → 0 |
| 이동 전후 파일 같음 | A2 의 md5 목록과 비교 |
| 평가 도구 동작 | `eval_ui.py --check` (파싱만), `pose_check.py`·`analyze_rollout.py --help` — 팔 움직이는 명령은 사용자가 직접 |
| 분석 스크립트 경로 | 각 `test_*.py` 를 `PYTHONDONTWRITEBYTECODE=1` 로 실행 |
| 메모리 | 경로가 적힌 메모리 파일 갱신 |

## 7. 이 계획에 넣지 않은 것
- 체크포인트 용량(학습 결과 약 247G, 체크포인트 하나 23G) — 지울지는 따로 결정.
- `~/Downloads` 의 handover md, `~/Ros2`·`~/Ros2_e0j0`·`~/ref` — so101_runs 와 관계없음.
