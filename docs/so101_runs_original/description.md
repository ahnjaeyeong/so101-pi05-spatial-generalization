# so101_runs — 폴더 설명서 (2026-10-22 기준)

SO-101 팔로 **데이터를 녹화하고 → 검사하고 → π0.5 를 학습하고 → 실물로 평가하고 → 분석한 결과**가 전부 이 폴더에 있다.
이 문서는 지금 실제로 있는 폴더·파일을 위에서부터 한 단계씩 내려가며, 각각 무엇이고 어떤 프로그램이 만들었는지 적는다.

- 크기·에피소드 수·날짜는 2026-10-22 17시대에 `du`, `ls`, `meta/info.json` 으로 직접 확인한 값이다.
- 코드는 여기 없고 `~/so101_boxpick/scripts/` 에 있다 (예외: 세션 `eval/` 안의 스크립트 복사본, 분석 폴더 안의 일회성 스크립트 — [§9](#9-코드는-어디-있나)).
- 이전 판(10-21)은 `/tmp/claude-2001/-home-user/5b310be2-9eda-4f79-b376-bba3cf78afe1/scratchpad/description.before_20261022.md` 에 백업.

## 목차
1. [한눈에 보기](#1-한눈에-보기)
2. [작업 흐름 — 어떤 파일이 언제 생기나](#2-작업-흐름--어떤-파일이-언제-생기나)
3. [세션 목록 (practice · main · main_k8)](#3-세션-목록)
4. [세션 폴더 하나의 구조 (공통)](#4-세션-폴더-하나의-구조-공통)
5. [세션별 내용](#5-세션별-내용)
6. [맨 위 redbox_all/ — 오프라인 분석](#6-맨-위-redbox_all--오프라인-분석-10-19)
7. [reference/ — 공개 데이터와 비교](#7-reference--공개-데이터와-비교)
8. [그 밖의 맨 위 폴더·파일](#8-그-밖의-맨-위-폴더파일)
9. [코드는 어디 있나](#9-코드는-어디-있나)
10. [README.md 와 다른 점](#10-readmemd-와-다른-점)

---

## 1. 한눈에 보기

```
so101_runs/                                   (전체 약 265G)
├── README.md                     4K   폴더·이름 규칙. record_ui.py 가 처음 한 번 만든 템플릿 (옛 구조)
├── description.md               —    이 파일
├── reorg_plan.md                12K   폴더 정리 계획 초안 (10-21, 아직 실행 안 함)
├── camera_settings.md            8K   카메라 노출·화이트밸런스 결정 기록
├── camera_settings/            180K   위 문서의 비교 사진 (cam_wb_compare.jpg)
├── ros2_guide.md                32K   Thor ROS2 트윈(~/Ros2) 사용 설명서 (10-07)
├── docs/                        20K   정리 문서 1개 (practice_10 학습·평가)
│
├── practice/                    93G   연습 수집 세션 6개
├── main/                       172G   본 수집 세션 7개 + 합친 데이터셋 redbox_all  (옛 카메라, K1–K4)
├── main_k8/                    429M   본 수집 세션 6개 (10-22 새 카메라, K1–K8) — 녹화 진행 중
│
├── redbox_all/                  43M   redbox 진동·필터·체크포인트 오프라인 분석 (10-19). 세션 아님
├── reference/                   21M   공개 SO101 sponge 데이터 + 우리 데이터와 비교 분석 2건
├── e0_j0/                       13M   E0_J_0 실험 (π0.5 잡기 + IK 놓기) 설계·체크리스트·시험 기록
├── range_check/                 52K   teleop_view.py 관절 범위 기록 6회
├── rollout/                      8K   rollout 전 확인 메모 (txt 1개)
├── calibration_backup_20261002/ 32K   팔 캘리브레이션 파일 백업
└── _deleted/                    21M   지운 세션 1개 (redbox T2 빨강 3개 판)
```

용량 대부분은 학습 체크포인트다: `practice/` 93G 중 92G, `main/` 172G 중 166G 가 `train/` (체크포인트 하나 약 11G).

---

## 2. 작업 흐름 — 어떤 파일이 언제 생기나

| 단계 | 사람이 실행하는 것 | 생기는 것 (세션 폴더 기준) |
|---|---|---|
| ① 배치 계획 (redbox 계열만) | `layout_plan.py plan --session <카테고리>/<세션>` | `layout.csv`, `layout_meta.json`, `layout_sheet.md`, `layout_map.svg`, (Known) `layout_template_a3.svg` |
| ② 녹화 | `record_ui.py --session … <lerobot-record 옵션>` (팔이 움직임 — 사람이 직접) | `dataset/` (lerobot 이 씀), `notes.md` 에 실행 기록 추가, `setup_photos/`, 카테고리 `README.md` 표 한 줄 |
| ③ 후처리 | `record_ui.py --postprocess` (녹화 끝에 자동) | `review_videos/episode_NNN.mp4` |
| ④ 품질 검사 | `check_dataset.py <세션>` | `qa_report.md`, `qa/` (판별 사진·위치·히트맵·서보 그래프) |
| ⑤ 학습 | `train/<배치>_<스텝>/launch_*.sh` → `lerobot-train` | `train/…/<실행이름>/checkpoints/NNNNNN/`, 로그 |
| ⑥ 실물 평가 | `eval_ui.py`, `eval/run_rollout.sh`, `eval_ab_ui.py` (팔이 움직임) | `eval/rollouts/…`, `eval/index.md`, `eval/eval_ab/…`, `eval/eval_space/…` |
| ⑦ 분석 | `analyze_rollout.py`, `eval_ab_report.py`, `pregrasp_*.py`, `train_roll_*.py`, 일회성 스크립트 | 각 `eval/<연구이름>/`, 맨 위 `redbox_all/eval/`, `reference/…` |

---

## 3. 세션 목록

"세션" = `record_ui.py` 로 녹화한 한 묶음 (데이터셋 하나). 카테고리는 `practice`(연습), `main`(본 수집), `main_k8`(10-22 부터의 본 수집).

### 3-1. 데이터셋 표 (`meta/info.json` 기준)

모든 데이터셋: lerobot dataset v3.0 · 30 fps · 카메라 `front`·`wrist` (640×480) · `observation.state`·`action` 각 6개 (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper). state = 팔로워(로봇) 관절, action = 리더(사람이 잡은 팔) 관절.

| 카테고리 | 세션 | 녹화일 | repo_id | 에피소드 | 프레임 (분) | dataset 크기 | 과제 문장 |
|---|---|---|---|---|---|---|---|
| practice | `practice_10` | 10-02 | `oxr/so101_cubebox_practice10` | 10 | 6,589 (3.7) | 57M | pick up the red cube and put it in the brown box |
| practice | `practice_50` | 10-06 | `oxr/so101_cubebox_practice50` | 50 | 30,884 (17.2) | 274M | 〃 |
| practice | `redbox_t1k_pilot` | 10-13 | `oxr/so101_redbox_t1k_pilot` | 4 | 1,928 (1.1) | 16M | 〃 |
| practice | `redbox_t2k_pilot` | 10-14 | `oxr/so101_redbox_t2k_pilot` | 4 | 3,462 (1.9) | 31M | put all the red cubes in the brown box |
| practice | `redbox_t3r_pilot` | 10-14 | `oxr/so101_redbox_t3r_pilot` | 4 | 1,995 (1.1) | 18M | pick up the red cube and put it in the brown box |
| practice | `redbox_k8_t3k_pilot` | 10-22 | `oxr/so101_redbox_k8_t3k_pilot` | 4 | 2,314 (1.3) | 18M | 〃 |
| main | `cubemark_v1` | 10-12 | `oxr/so101_cubemark_v1` | 50 | 38,816 (21.6) | 335M | Pick up the red cube and place it on the X mark. |
| main | `redbox_t1_known` | 10-14 | `oxr/so101_redbox_t1_known` | 64 | 27,984 (15.5) | 236M | pick up the red cube and put it in the brown box |
| main | `redbox_t1_random` | 10-14 | `oxr/so101_redbox_t1_random` | 64 | 27,658 (15.4) | 232M | 〃 |
| main | `redbox_t2_known` | 10-15 | `oxr/so101_redbox_t2_known` | 64 | 45,261 (25.1) | 402M | put all the red cubes in the brown box |
| main | `redbox_t2_random` | 10-15 | `oxr/so101_redbox_t2_random` | 64 | 46,401 (25.8) | 408M | 〃 |
| main | `redbox_t3_known` | 10-15 | `oxr/so101_redbox_t3_known` | 64 | 18,985 (10.5) | 160M | pick up the red cube and put it in the brown box |
| main | `redbox_t3_random` | 10-15 | `oxr/so101_redbox_t3_random` | 64 | 22,241 (12.4) | 198M | 〃 |
| main | `redbox_all` (합친 것) | 10-15 | `oxr/so101_redbox_all` | 384 | 188,530 (104.7) | 1.6G | T1·T3 문장 + T2 문장 (2개) |
| main_k8 | `redbox_t1_known` | 10-22 | `oxr/so101_k8_redbox_t1_known` | 48 / 64 | 24,739 (13.7) | 178M | pick up the red cube and put it in the brown box |
| main_k8 | `redbox_t1_random` | 10-22 | `oxr/so101_k8_redbox_t1_random` | 32 / 64 | 15,516 (8.6) | 114M | 〃 |
| main_k8 | `redbox_t2_known` | — | `oxr/so101_k8_redbox_t2_known` | 0 (계획만) | — | — | put all the red cubes in the brown box |
| main_k8 | `redbox_t2_random` | — | `oxr/so101_k8_redbox_t2_random` | 0 (계획만) | — | — | 〃 |
| main_k8 | `redbox_t3_known` | — | `oxr/so101_k8_redbox_t3_known` | 0 (계획만) | — | — | pick up the red cube and put it in the brown box |
| main_k8 | `redbox_t3_random` | — | `oxr/so101_k8_redbox_t3_random` | 0 (계획만) | — | — | 〃 |

### 3-2. 이름 읽는 법

| 이름 조각 | 뜻 |
|---|---|
| `cubebox` (practice_10/50) | 빨간 큐브 하나를 갈색 상자에 넣기 — 첫 연습 과제 |
| `cubemark` | 빨간 큐브를 탁자 위 X 표시에 놓기 |
| `redbox` | 빨간 큐브를 갈색 상자에 넣기 — 본 과제. 3가지 변형: |
| `t1` | T1 = 빨간 큐브 1개만 |
| `t2` | T2 = 빨간 큐브 여러 개 (2–4개) 모두 넣기 |
| `t3` | T3 = 빨간 큐브 1개 + 다른 색 큐브(방해물) 여러 개 |
| `known` / `k` | Known = 큐브를 정해진 고정 위치(K1, K2, …)에만 놓음 |
| `random` / `r` | Random = 큐브를 작업 영역 안 아무 곳에 놓음 |
| `k8` | 10-22 에 front 카메라를 옮기고 고정 위치를 K1–K8 (8곳, 3줄 격자) 로 바꾼 뒤의 데이터. 그 전(`main/`)은 K1–K4 |
| `pilot` | 본 수집 전에 4판만 찍어 본 시험 |

### 3-3. 카테고리 폴더 안의 공통 파일

| 파일 | 내용 |
|---|---|
| `practice/README.md`, `main/README.md`, `main_k8/README.md` | 세션 목록 표 (세션·날짜·repo_id·에피소드·상태). `record_ui.py` 후처리가 줄을 추가·갱신. **상태** 칸은 손으로 고쳐도 유지됨 |
| `main/redbox_수집명령.md` | 10-14 redbox 본 수집 때 쓴 녹화 명령 모음 (세션 6개 × 첫 실행/이어 찍기) |
| `main_k8/redbox_수집명령.md` | 10-22 main_k8 수집 명령 모음 + K 배치, 큐브 각도 규칙(0·↺30·↻30·45), 각도 가이드 PDF 위치, 확인 명령 |
| `main_k8/setting/` | main_k8 준비 때 만든 그림 9개 (아래 표) |

`main_k8/setting/` 파일:

| 파일 | 내용 |
|---|---|
| `redbox_K8_front원본_1280.png` | 옮긴 front 카메라의 원본 화면 (1280×720) |
| `redbox_K8_번호_카메라.png` | 카메라 화면 위에 K1–K8 번호 표시 |
| `redbox_K8_위치_평면도.png` | K1–K8 의 평면 좌표(cm) 그림 |
| `redbox_K8_위치_카메라확인.png` | 좌표 → 카메라 화면 변환(H 행렬)을 큐브 위치로 확인한 그림 |
| `redbox_K8_녹화배너_미리보기.png` | record_ui 녹화 배너 (K 격자 표시) 미리보기 |
| `redbox_K8_큐브각도_미리보기.png` | 배너의 큐브 각도 그림 미리보기 |
| `redbox_K8_랜덤_배너_미리보기.png` | Random 세션 배너 (색+번호 큐브 그림) 미리보기 |
| `redbox_K8_파일럿_ep0_배너.png` | 파일럿 첫 판 배너 |
| `redbox_K8_큐브각도_가이드_A4.pdf` | 큐브를 놓을 때 쓰는 각도 가이드 (100% 인쇄, 카드 4장: 0, ↺30, ↻30, 45) |

---

## 4. 세션 폴더 하나의 구조 (공통)

완성된 redbox 세션 하나 (예: `main_k8/redbox_t1_known/`) 를 기준으로 한다. 세션마다 없는 항목은 [§5](#5-세션별-내용) 에 적었다.

```
<세션>/
├── notes.md                    녹화 기록 (record_ui.py)
├── setup_photos/               첫 화면 사진 (record_ui.py)
├── dataset/                    lerobot 원본 데이터 — 녹화 후 수정 금지
├── review_videos/              확인용 영상 (record_ui.py 후처리)
├── layout.csv                  판별 배치 계획 + 진행 상태 (layout_plan.py)
├── layout_meta.json            계획 설정·통계·해시 (layout_plan.py)
├── layout_sheet.md             사람이 보는 배치표 (layout_plan.py)
├── layout_map.svg              위치 그림 (layout_plan.py)
├── layout_template_a3.svg      Known 세션: 실제 크기 바닥 템플릿 (layout_plan.py)
├── positions_manual.csv        (main 의 t1/t2_random 만) 손으로 보정한 큐브 위치
├── *.bak_<YYYYMMDD_HHMMSS>     layout_plan.py 가 계획을 다시 쓸 때 남긴 이전 판
├── qa_report.md                품질 검사 보고서 (check_dataset.py)
├── qa/                         품질 검사 사진·표 (check_dataset.py)
├── train/                      학습 결과 (비어 있으면 학습 안 함)
└── eval/                       실물 평가·분석 (비어 있으면 평가 안 함)
```

### 4-1. `notes.md`
- `record_ui.py` 가 세션을 처음 만들 때 머리말(세션 폴더, dataset 위치, 만든 날, 빈 "설정" 칸)을 쓰고, **녹화할 때마다** `### <날짜 시각> · 새 녹화/이어 찍기 <!-- run:… -->` 절을 아래에 덧붙인다.
- 한 절에 들어가는 것: 녹화 전 점검 결과(카메라 v4l2 설정값, twin_ws 컨테이너 유무, 체크리스트 확인), 실행한 명령 원문, 실제 lerobot 명령, 저장된 판 수, 판별 메모 칸(사람이 채움).
- 판을 지운 경우 그 사실도 여기 남는다 (예: `main/redbox_t2_known/notes.md:18` — 빨강 3개 판 2편 삭제).

### 4-2. `setup_photos/`
- `ep000_front_first.png`, `ep000_wrist_first.png` — 첫 판 시작 순간의 front·wrist 카메라 화면. 세팅(상자·카메라 위치)을 나중에 확인하는 용도.

### 4-3. `dataset/` — lerobot 데이터셋 (v3.0)
`lerobot-record` 가 직접 만든다. **녹화 후 손대지 않는다** (학습·QA·분석은 모두 읽기만).
```
dataset/
├── data/chunk-000/file-NNN.parquet       프레임 단위 표: action, observation.state, timestamp,
│                                         frame_index, episode_index, index, task_index
├── meta/
│   ├── info.json                         전체 정보: 에피소드·프레임 수, fps, 특성(feature) 정의, 경로 규칙
│   ├── stats.json                        관절·이미지 평균/표준편차/최소/최대 (학습 정규화에 쓰임)
│   ├── tasks.parquet                     과제 문장 목록 (task_index ↔ 문장)
│   └── episodes/chunk-000/file-NNN.parquet  에피소드별 길이·시작/끝 위치·영상 구간
└── videos/
    ├── observation.images.front/chunk-000/file-NNN.mp4   front 카메라 (여러 판이 한 파일에 이어 붙음, av1)
    └── observation.images.wrist/chunk-000/file-NNN.mp4   wrist 카메라
```

### 4-4. `review_videos/`
- `episode_000.mp4` … 판마다 하나. front | wrist 를 나란히 붙인 확인용 영상. 이미 있는 파일은 다시 만들지 않는다.

### 4-5. 배치 계획 파일 (`layout_*`) — redbox 계열 세션만
`~/so101_boxpick/scripts/layout_plan.py` 가 설정 파일(`config/redbox_layouts.yaml` — main, `config/redbox8_layouts.yaml` — main_k8·K8 파일럿)과 seed 로 "몇 번째 판에 큐브를 어디에 놓을지"를 미리 정해 둔 것. `record_ui.py --layout auto` 가 이걸 읽어 녹화 배너에 다음 판 배치를 보여 준다.

| 파일 | 내용 |
|---|---|
| `layout.csv` | 한 줄 = 한 판. 열: `episode_index`, `layout_id` (예 `T1K7`, `T3K1-G6B7O8`), `status` (planned/recorded/excluded), `retake_of` (재촬영이면 원래 판), `objects` (예 `red_cube@K7(-25.5,26.5)`), `frames`, `note`, `angles` (main_k8 만, 예 `K7:45`, Random 은 `red1:L30;yellow2:0`) |
| `layout_meta.json` | 계획을 만든 설정 복사본: 생성 시각, 그룹(t1_known…), repo_id, 과제 문장, 설정 파일 경로·sha256, seed, 통계(위치별 횟수, 각도별 횟수), 계획 sha256 |
| `layout_sheet.md` | 사람이 녹화 중 보는 배치표 (판 번호·위치·각도) |
| `layout_map.svg` | 상자·로봇·K 위치를 그린 평면도 |
| `layout_template_a3.svg` | Known 세션만. A3 로 실제 크기 인쇄해 탁자에 까는 위치 템플릿 |
| `*.bak_<시각>` | `layout_plan.py plan --force` 등으로 다시 만들 때 이전 3개 파일(csv·json·md)을 이 이름으로 남김 |
| `positions_manual.csv` | `main/redbox_t1_random`, `main/redbox_t2_random` 만. front 카메라 사각지대라 자동 검출이 안 된 판의 큐브 위치를 손으로 적은 것 (열: episode_index, color, x_cm, y_cm, note). check_dataset·히트맵·train_roll 분석이 읽음 |

좌표계: cm, 원점 = 상자의 로봇 쪽 벽 바깥면 모서리. x = 상자 쪽(+)/로봇 쪽(−), y = 로봇 기준 왼쪽(+).

### 4-6. `qa_report.md` 와 `qa/` — 품질 검사
`~/so101_boxpick/scripts/check_dataset.py <카테고리>/<세션>` 이 dataset 을 읽기만 해서 만든다. 다시 돌리면 덮어쓴다 (사람이 찍은 ✓ 표시는 유지).

`qa_report.md` 의 절:
1. **형식** — 에피소드 수, 길이 범위, fps, 카메라 키·해상도·코덱, 관절 순서, 과제 문장, NaN, timestamp 간격, 계획 대비 유효 판 수, 영상 프레임 수 일치.
2. **팔** — 판마다 관절별 움직인 범위(°), 길이, 속도 제한 의심 여부, (main_k8) 손목 회전 범위 70° 초과 표시, 서보 그래프 링크.
3. **위치·물체** — 판마다 front 첫/끝 화면에서 찾은 큐브 위치, 계획과의 거리, 끝에 상자 안에 들어갔는지, (main_k8) 큐브 각도 계획 대비 측정값.
4. 확인할 판 목록 — 사람이 보고 ✓ 를 찍는 칸.

`qa/` 안:

| 파일 | 내용 |
|---|---|
| `ep_NNN.jpg` | 판마다 한 장: front·wrist 첫/끝 화면 + 검출 표시 |
| `layout_<배치ID>.jpg` | 같은 배치 ID 판들의 첫 화면 모음 (Known 세션) |
| `plan_first.jpg` | 계획 첫 판 배치와 실제 첫 화면 비교 |
| `overview_front_first.jpg`, `overview_front_last.jpg` | 모든 판의 front 첫/끝 화면을 한 장에 축소해 모은 것 |
| `positions.csv` | 판마다 검출한 큐브 위치 (열: episode_index, layout_id, excluded, color, x_cm, y_cm, nearest_known, dist_known_cm) |
| `heatmap.png` | Random 세션: 큐브 시작 위치 분포 (빈 곳·도달 어려운 영역 표시). `redbox_heatmap.py` |
| `servo_data.json`, `servo_시간.png`, `servo_K별.png` | (10-22 부터) 관절 궤적 데이터와 그래프. 시간축 그래프는 항상, K별 그래프는 판마다 빨강 1개인 Known(T1-K·T3-K) 세션만. `servo_plot.py` |

### 4-7. `train/` — 학습 결과
```
train/<배치크기>_<스텝>/                       예: 4_15000, 8_3000, 32_20000 (10-13 부터 이 방식)
├── run_<실행이름>.sh                          lerobot-train 명령 원문 (옵션 전부)
├── launch_<실행이름>.sh                       run_*.sh 를 nohup 으로 띄우고 로그·시간 기록
├── <실행이름>.log                             학습 로그 (손실·속도)
├── <실행이름>.mem.log                         메모리 사용 기록
├── <실행이름>.pid                             실행 중 프로세스 번호
├── <실행이름>.time                            start / end 시각, 종료 코드 rc
└── <실행이름>/                                lerobot output_dir
    ├── training_params.md, .csv               train_summary.py 가 만든 학습 설정 표 (있는 경우)
    └── checkpoints/
        ├── 005000/ 010000/ …                  저장 스텝마다
        │   ├── pretrained_model/              rollout 에 쓰는 정책: model.safetensors, config.json,
        │   │                                  train_config.json, pre/postprocessor(정규화), tokenizer/
        │   └── training_state/                이어 학습용: optimizer·scheduler·rng 상태, training_step.json
        └── last -> 마지막 스텝 (심볼릭 링크)
```
`practice_10`, `practice_50` 은 그 전 방식이라 `train/<실행이름>/` 이 바로 있다 (`train/pi05_2k`, `train/pi05_15k`).

### 4-8. `eval/` — 실물 평가와 분석
세션마다 내용이 다르다. 공통으로 나올 수 있는 것:

| 항목 | 만든 것 | 내용 |
|---|---|---|
| `rollouts/<시각>_<스텝>_<tag>/` | `run_rollout.sh` 또는 `eval_ui.py` | 실물 rollout 한 번 (아래 표) |
| `index.md` | `eval_ui.py` | 실행마다 한 줄: 시각, 체크포인트, tag, 저장 판 수, 성공 P / 실패 F, 성공률, 폴더 링크 |
| `results_all.csv` | `eval_ui.py` | 모든 실행의 판을 이어 붙인 표 (run, ep, verdict, seconds, frames, 시작 사진 경로, memo, ckpt, tag, started, task) |
| `run_rollout.sh` | 사람 (세션마다 복사·수정) | `lerobot-rollout` 실행 래퍼: 체크포인트·과제 문장 고정, pose_check → rollout_logged → analyze_rollout 순서 |
| `rollout_logged.py` | 〃 | `lerobot-rollout` 을 그대로 돌리면서 RTC 추론 지연·큐 길이·max_relative_target 클램프 경고를 ms 시각과 함께 `debug.log` 로 따로 남김. redbox_all 판은 `--arm_filter`, `--rollout_guard`, `--exec_speed` 옵션 추가 (기본 꺼짐) |
| `pose_check.py` | 〃 | 팔로워 현재 자세를 읽기만 해서 학습 데이터 시작 자세와 비교 (토크·설정 쓰기 없음) |
| `analyze_rollout.py` | 〃 | rollout dataset + debug.log → 관절별 흔들림 지표(hf_rms 등) `analysis.json`/`.npz`. 인자 `reference` = 학습 데이터(사람 조작)를 같은 방식으로 계산 |
| `plot_rollout.py` | 〃 | analyze 결과를 `ep<N>_action_state.png` 그래프로 |
| `reference_teleop/` | `analyze_rollout.py reference` | 학습 데이터(사람 조작)의 같은 지표 = 비교 기준 (`analysis.json`, `analysis.npz`) |

`rollouts/<…>/` 한 폴더 안:

| 파일 | 내용 |
|---|---|
| `command.txt` | 실행한 명령·환경 변수 |
| `console.log` | lerobot-rollout 화면 출력 |
| `debug.log` | rollout_logged.py 가 남긴 RTC 지연·클램프 기록 |
| `pose_check.txt` | 시작 자세 확인 결과 |
| `dataset/` | rollout 중 관측·행동을 lerobot 형식으로 녹화한 것 (정책이 본 화면과 낸 명령) |
| `analysis.json`, `analysis.npz`, `ep<N>_action_state.png` | analyze/plot 결과 |
| `results.md`, `results.csv`, `results.json`, `start_images/ep<N>_{front,wrist}.png` | eval_ui.py 로 돌린 경우: 판별 성공/실패와 시작 사진 |
| `filter_log.csv` | `--arm_filter=true` 일 때: 틱마다 필터 전·후 action 과 실제 상태 |

---

## 5. 세션별 내용

### 5-1. `practice/practice_10` (24G) — 첫 학습·실물 실행 확인
- 목적: 성능이 아니라 학습 → 실물 실행이 끝까지 도는지 확인. 정리 문서는 `docs/practice_10_pi05_2k.md`.
- `train/pi05_2k/` — π0.5, batch 4, 2,000 스텝, bf16 (10-02 16:51 → 18:16). 체크포인트 `002000`.
- `eval/` 은 다른 세션보다 스크립트가 많다 (오프라인 점검을 여기서 처음 함):

| 파일 | 내용 |
|---|---|
| `offline_eval_pi05_2k.py` / `.log` / `pi05_2k_offline.json` / `.npz` | 팔 없이 학습 데이터를 넣어 lerobot-rollout sync 경로와 같은 방식으로 추론 → 정답 action 과 오차 |
| `plot_pi05_2k.py`, `pi05_2k_ep001_actions.png`, `pi05_2k_ep004_actions.png`, `pi05_2k_error_vs_horizon.png` | 위 결과 그래프 (판별 예측 vs 정답, 예측 거리별 오차) |
| `rtc_timing_pi05_2k.py` / `.log` / `pi05_2k_rtc_timing.json` | RTC(실시간 chunking) 추론 시간 오프라인 측정 |
| `steps_timing.py`, `steps_timing.json` | `num_inference_steps` 별 추론 시간·정확도 |
| `vision_check.py`, `vision_check.json` | 정책이 화면을 보고 움직이는지 (같은 자세·다른 큐브 위치에서 chunk 비교) |
| `camera_check.py` | rollout 녹화 화면이 학습 때와 같은지, 프레임이 멈추지 않았는지 |
| `rollout_pi05_2k_20261006_092753.log` | 첫 실물 rollout 로그 |
| `rollouts/` 9개 (10-06) | `rtc_h20`, `sync`, `rtc_h20_q20`, `rtc_fast` 등 추론 방식별 실물 실행 (command·console·debug 로그) |
| `reference_teleop/` | 학습 데이터 지표 + `ep0–9_action_state.png`, `cam_ep1/4_sheet.jpg`, `camera_check.json` |
| `run_rollout.sh`, `rollout_logged.py`, `pose_check.py`, `analyze_rollout.py`, `plot_rollout.py` | [§4-8](#4-8-eval--실물-평가와-분석) 공통 스크립트 |

### 5-2. `practice/practice_50` (69G)
- `train/pi05_15k/` — π0.5, batch 4, 15,000 스텝, bf16 (10-06 15:07 → 10-07 01:01, 9시간 54분). 체크포인트 5k·10k·15k. `training_params.md/.csv` 있음.
- 이 15k 체크포인트는 `e0_j0/` 실험의 잡기 정책으로도 쓰였다.
- `eval/rollouts/` 4개 (10-07 3개, 10-13 1개). `index.md` 기준 10-13 실행: 8판 중 성공 3 (38%).
- `eval/rollout_*.log` 5개: 10-08 ~ 10-13 rollout 콘솔 로그.

### 5-3. `practice/redbox_*_pilot` 4개 — 본 수집 전 4판 시험
- `redbox_t1k_pilot` (10-13, T1-Known), `redbox_t2k_pilot` (10-14, T2-Known), `redbox_t3r_pilot` (10-14, T3-Random): 옛 카메라·K1–K4 설정 시험.
- `redbox_k8_t3k_pilot` (10-22, T3-Known): 새 카메라·K1–K8·큐브 각도 시험. 녹화 순서를 적은 `파일럿_명령.md` 가 추가로 있다.
- 모두 `train/`, `eval/` 은 비어 있다 (학습·평가 안 함).

### 5-4. `main/cubemark_v1` (102G) — 큐브를 X 표시에 놓기
- `train/4_15000/pi05_15k/` — π0.5, batch 4, 15k 스텝 (10-12 18:05 → 10-13 03:59). 체크포인트 5k·10k·15k.
- `train/8_3000/pi05_expert_bs8_3k/` — π0.5 action expert 만 학습 (vision encoder 고정), batch 8, 3k 스텝 (10-13 11:29 → 13:52). 체크포인트 1k·2k·3k.
- `eval/rollouts/` 3개 (10-13): 15k 2회, 3k 1회. `index.md` 기준 3k 실행: 8판 중 성공 0.
- `eval/rollout_20261013_*.log` 5개: rollout 콘솔 로그.

### 5-5. `main/redbox_t{1,2,3}_{known,random}` 6개 — redbox 본 수집 (옛 카메라, K1–K4)
- 각 64판. 데이터·QA·배치 파일만 있고 `train/`, `eval/` 은 비어 있다 — 학습·평가는 합친 `redbox_all` 로 했다.
- 차이점:
  - `redbox_t1_random`, `redbox_t2_random` 에만 `positions_manual.csv` 가 있다.
  - `redbox_t2_known` 상태 칸: "계획 변경 (빨강 2~4개) — 2편 삭제". 지운 2편은 `_deleted/` 에.
  - `redbox_t3_known/dataset_empty_20261015_1449/` — 중단된 녹화(저장 0편)가 남긴 빈 데이터셋을 이름만 바꿔 둔 것 (`meta/` 만 있음, 에피소드 0).
  - `*.bak_*` 파일: t2_known (10-14 2회), t2_random (10-14), t3_known·t3_random (10-15 2회) — 계획을 다시 만든 흔적.

### 5-6. `main/redbox_all` (68G) — 6개 세션을 합친 학습용 데이터셋 + 학습 + 평가
- 녹화가 아니라 `lerobot-edit-dataset --operation.type=merge` 결과 (t1k, t1r, t2k, t2r, t3k, t3r 순서 → ep 0–383). lerobot-train 이 repo_id 여러 개를 받지 않아 합쳤다. 그래서 `notes.md`, `setup_photos/`, `review_videos/`, `qa/` 가 없고 `main/README.md` 표에도 없다.
- `dataset/` (1.6G) — 384판, 과제 문장 2개.
- `train/32_20000/` (65G):
  - `pi05_expert_bs32_20k/` — π0.5 action expert 만 학습, batch 32, 20k 스텝 (10-15 17:52 → 10-18 02:31).
  - 같은 폴더에 이어 학습 → 30k (`*_resume30k.*` 파일들, 10-20 12:58 → 10-21 19:29).
  - 체크포인트 5k·10k·15k·20k·25k·30k, `last → 030000`.
- `eval/` — 다른 세션보다 연구 폴더가 많다:

| 항목 | 크기 | 내용 |
|---|---|---|
| `rollouts/` 4개 (10-19) | 61M | 20k 체크포인트 T1 실물 실행: `test1`, `rtc20_filt` 2회, `rtc20_filt_s80` (80% 속도) |
| `run_rollout.sh` | | redbox_all 용: `TASK=t1/t2/t3`, `STEP=…`, 필터·속도 옵션 설명 포함 |
| `rollout_logged.py` | | 가장 새 판 (필터·가드·속도 옵션 포함, 기본 꺼짐) |
| `arm_filter.py` | | 팔 5관절 필터 (EMA α + 관절별 속도 제한, 그리퍼 제외) + RTC 지연·추종 감시. 근거: `redbox_all/eval/p0_offline_replay/report.md` |
| `motor_check.py` | | 팔로워 모터 버스 읽기 전용 점검 (ping 응답률, 전압·온도·오류 비트·위치) |
| `pose_check.py`, `analyze_rollout.py`, `plot_rollout.py`, `reference_teleop/` | | [§4-8](#4-8-eval--실물-평가와-분석) 공통 |
| `eval_ab/20261019_A_vs_B/` | 408M | A/B 실물 평가 40판: A = RTC 필터 없음, B = RTC + 팔 관절 필터 (20k). `eval_ab_ui.py` |
| `eval_space/20261020_space/` | | 공간 일반화 평가: 필터 B 만, K1–K4 고정 위치 + 자유 위치 구역 Z1–Z4 (20k). `eval_ab_ui.py init --design space` |
| `eval_space/20261022_space_30k/` | | 같은 설계를 30k 체크포인트로 (10-22 09:18 시작) |
| `pregrasp_angles/` | 864K | 잡기 직전 wrist 카메라에서 큐브와 그리퍼 턱의 각도 차 (성공/실패 비교). `pregrasp_angles.py` |
| `pregrasp_review/` | 397M | 정책 시험 80판 + 학습 데이터 380판의 잡기 직전 프레임을 위치 유형별로 분류한 검토. `pregrasp_review.py` |
| `train_roll_census/` | 860K | 학습 384판의 손목 회전(wrist_roll)·큐브 위치 분포 조사. `train_roll_census.py`, `train_roll_report.py` |

`eval_ab/…`, `eval_space/…` 연구 폴더 한 개의 구조 (`eval_ab_ui.py` 가 만듦):

| 항목 | 내용 |
|---|---|
| `study.json` | 고정 설정: 종류(정책 평가, 학습 데이터 아님), 체크포인트, 과제, 조건 A/B, 추론 설정(RTC, steps 5, horizon 20, EXP…), 로봇·카메라 설정 |
| `plan.csv` | 판 순서와 결과: trial, 위치(K1… / Z1…), 조건, 상태, 시작 시각, 길이, 첫 잡기 성공 여부, 최종 결과, 시도 횟수, 실패 유형, 메모 |
| `runs/<시각>/` | lerobot 실행 한 번 (여러 판): command.txt, console.log, debug.log, dataset/, pose_check.txt, ctrl/, preview/, viewer.log |
| `trials/<번호>_<조건>_<위치>/` | 판 하나: trial.json, verdict.json(판별), ticks.csv(틱별 상태), inferences.csv·chunks.npz(추론 결과), start_front/wrist.png, review.mp4 |
| `results/` | `eval_ab_report.py`·`eval_space_report.py` 집계: report.md 또는 space_report.md, trials.csv / space_trials.csv, 조건·위치별 요약 csv, space_map.png(위치별 성공 지도), space_factors.png, 날짜별 분석 문서(analysis_20261019.md, 공간일반화_분석_20261020.md, analysis_yaw_roll_20261020.md, 비교_20k_vs_30k_20261022.md), 분석 스크립트(analysis_scripts/a1–a4.py, cmp_20k_30k.py) |
| `zones_guide.png` | (20261020_space) 자유 위치 구역 Z1–Z4 안내 그림 |

`pregrasp_review/` 안:
- `파지직전_검토_리포트.md` — 보고서. `pregrasp_review.csv` (정책 시험), `pregrasp_review_train.csv` (학습 데이터), `review_meta.json`.
- `frames/` — 정책 시험 판마다 front·wrist·sheet 3장 (240장). `frames_train/` — 학습 데이터 판마다 3장 (1,140장).
- `sheet_<성공|실패|학습>_<유형번호>_<유형>.jpg` — 유형별 모음: 1 큐브 안 보임, 2 앞쪽 덜 감, 3 뒤쪽 지나침, 4 좌우 벗어남, 5 위치 정상·비스듬히, 6 위치·정렬 정상.

`pregrasp_angles/` 안: `파지직전_큐브그리퍼각도_리포트.md`, `pregrasp_angles.csv`, `train_wrist_center_at_close.csv`, `wrist_rel_hist.png`, `examples_front.jpg`, `examples_wrist.jpg`.

`train_roll_census/` 안: `train_roll_report.md`, `학습데이터_위치분포_손목회전_리포트.md`, `grasps.csv`·`first_grasps.csv` (판별 잡기 순간), `positions_all_red.csv`, `census_meta.json`, 그래프 `roll_hist.png`, `roll_vs_angle.png`, `roll_vs_yaw.png`, `position_map.png`.

### 5-7. `main_k8/redbox_t{1,2,3}_{known,random}` — 10-22 새 본 수집 (K1–K8)
- 10-22 front 카메라를 옮기고 고정 위치를 K1–K8 로 바꾼 뒤 처음부터 다시 찍는 세트. 설정 `~/so101_boxpick/config/redbox8_layouts.yaml`, repo `oxr/so101_k8_redbox_*`, seed 2101/2102/2201/2202/2301/2302, 각 64판 계획.
- K 배치 (로봇에서 상자를 보는 방향): 상자 쪽 줄 `K1 K2 K3` / 가운데 `K4 K5 K6` / 로봇 쪽 `K7 · K8`. 칸 간격 15 cm × 8.5 cm.
- 새로 생긴 것: 판마다 **큐브 각도** (0, ↺30, ↻30, 45) 가 계획에 있다 → `layout.csv` 의 `angles` 열, 배너 그림, QA 의 각도 측정(`cube_angle.py`).
- 진행 상태 (10-22 17시대):

| 세션 | 녹화 | 있는 것 |
|---|---|---|
| `redbox_t1_known` | 48 / 64 | 전체 구조 (dataset, notes, setup_photos, review_videos, qa — `servo_K별.png` 포함, layout + `.bak_20261022_145907`) |
| `redbox_t1_random` | 32 / 64 (ep002 제외 → 재촬영 줄 ep64 추가) | 전체 구조 (qa 에 `heatmap.png`, layout + `.bak_20261022_162715`) |
| `redbox_t2_known`, `redbox_t2_random`, `redbox_t3_known`, `redbox_t3_random` | 0 | 배치 계획 파일만 (`layout.*` + `.bak_*`). dataset 없음 |

- `.bak_20261022_1459xx` = 큐브 각도 15° 를 빼고 Known 계획을 다시 만들 때 남은 이전 판. `.bak_20261022_1627xx` = Random 에도 각도를 넣어 다시 만들 때의 이전 판.

---

## 6. 맨 위 `redbox_all/` — 오프라인 분석 (10-19)

`main/redbox_all/` 과 이름이 같지만 **세션이 아니라** 10-19 에 만든 분석 폴더다 (`redbox_all/eval/` 하나만 있음). 팔을 움직이지 않고 저장된 데이터·체크포인트로만 계산한 결과. 대상은 `main/redbox_all` 의 20k 체크포인트와 cubemark 체크포인트.

| 폴더·파일 | 내용 | 주요 파일 |
|---|---|---|
| `vibration_fix_plan_20261019.md` | redbox π0.5 진동 문제: 측정 사실, 외부 사례 비교, 우선순위 계획 (P0 오프라인 재생 → P1 실물 → P2 재학습) | — |
| `offline_ckpt_compare/` | 체크포인트별(redbox 5k–20k, cubemark 15k·3k) 학습 데이터 정확도·잡음 비교 | `offline_eval_v2.py`, `rb_0N0000.json/.log`, `cm_*.json/.log`, `results.md`, `done.flag` |
| `p0_offline_replay/` | 정책 chunk 를 열린 루프로 재생하는 시뮬레이션: 추론 방식(sync/RTC, horizon)·필터 조합·지연(1.0 / 1.55 배)별 흔들림과 클램프 | `replay_sim.py`, `analyze_runs.py`, `clamp_analysis.py`, `make_plots.py`, `report.md`, `tables.md`, `metrics_*.csv`, `table_*.csv`, `fig A–E *.png`, `servo_model_v2.json`(서보 응답 모델), `runs_lat1.0/`, `runs_lat1.55/`, `runs_spike/` (실행별 결과) |
| `filter_validation/` | `arm_filter.py` 검증: 단위 시험, 사람 조작 데이터에 넣었을 때의 영향, 빠른 동작 구간 | `test_filter.py`, `test_speed.py`, `test_results.json`, `wide_analysis.py`, `guard_on_replay.py`, `report.md`, `figV1/V2*.png`, `*_table.csv`, `runs_wide_*/` |
| `speed_scaling/` | 실행 속도를 낮췄을 때(예 80%) 효과, 사람 조작 시간 비교, 손목 정렬 시점 | `speed_analysis.py`, `report.md`, `speed_table.csv`, `speed_by_source.csv`, `human_timing.json`, `wrist_alignment_*.{png,csv}`, `runs/` |
| `official_vs_custom/` | 공식 lerobot-rollout 경로와 우리 래퍼(rollout_logged.py)의 출력이 같은지 비교 | `test_abc_path.py`, `abc_streams.npz`, `report.md` |
| `eval_ab_tests/` | `eval_ab_ui.py` 경로 시험 | `test_eval_ab_path.py` |

- `tmp*` 이름의 하위 폴더 (filter_validation 6개, eval_ab_tests 2개, official_vs_custom 1개) 는 시험 스크립트가 만든 임시 폴더가 지워지지 않고 남은 것이다.
- `~/so101_boxpick/scripts/eval_ab_mock.py:18` 과 이 폴더 안 시험 스크립트 몇 개가 `~/so101_runs/redbox_all/eval/…` 경로를 직접 읽는다 (`reorg_plan.md` §4 표).

---

## 7. `reference/` — 공개 데이터와 비교

| 폴더 | 내용 |
|---|---|
| `aswinkumar99_so101_pick_place/` | Hugging Face 공개 SO101 데이터셋 (스펀지를 집어 옮기기). 과제 3종 × 위치 2종: `task1-single-sponge-no-distractors`, `task2-multiple-sponges-no-distractors`, `task3-single-sponge-with-distractors`, 각각 `fixed-locations/`, `random-locations/` (lerobot 데이터셋). `calibration/` 에 그쪽 팔 캘리브레이션, `README.md` 는 원 데이터셋 설명. `.cache/` 는 내려받기 캐시. 우리 redbox T1/T2/T3 × Known/Random 설계와 구조가 같다 |
| `analysis_20261019/` | 10-19: 공개 데이터와 redbox 의 사람 조작 거칠기 비교 (속도 PSD, 고주파 점수, 관절 범위) + 체크포인트 출력 흔들림(`j_*.json`, `offline_chunk_jitter.py`). `compute_metrics.py`, `make_plots.py`, `report.md`, `summary_table.md/.csv`, `metrics_episodes.csv`, `metrics_groups.csv`, `fig1–6 *.png` |
| `range_compare_20261021/` | 10-21: 공개 데이터와 redbox 의 작업 범위·잡는 자세 비교 (정기구학으로 손끝 위치 계산, 잡기 순간 관절값, 시작 자세, 캘리브레이션 차이). `extract_states.py`, `fk.py`, `analyze.py`, `work_ranges.py`, `make_plots.py`, `write_report.py`, `report.md`, `fig1_top_view.png`, `fig2_joint_ranges.png`, `fig3_at_grasp.png`, csv 여러 개, `states.npz`. `__pycache__/` 는 실행 때 생긴 것 |

---

## 8. 그 밖의 맨 위 폴더·파일

### `e0_j0/` — E0_J_0 실험 (10-06 ~ 10-12)
practice_50 의 π0.5 15k 로 큐브를 잡고, ROS2 트윈(`~/Ros2`)의 IK(E0-lite)로 옮겨 놓는 시제품 실험. 코드는 `~/so101_boxpick/e0_j0/` 와 `~/Ros2_e0j0`, 이 폴더는 문서와 기록.

| 파일·폴더 | 내용 |
|---|---|
| `design.md` | 설계 (10-07): 구조, 노드 이름(`twin_e0j0`, `e0_j0_executor`), 근거 소스 |
| `C_shadow_checklist.md` | C단계 그림자 모드 체크리스트 — 팔에 명령 0, 관절 변환·카메라·정책 서버 지연 확인 |
| `D_real_checklist.md` | D단계 실물 구동 체크리스트 — ③a 잡고 들기, ③b 놓기, §10 살포시 놓기 |
| `experiment_log.md` | 날짜순 실험 기록 (바꾼 설정·이유·결과) |
| `report_for_dr_lee.md` | 10-08 보고서 ([측정]/[추정] 구분) |
| `box_plan.json`, `lift_compare.json` | 상자로 옮기는 경로 계획·들어 올리기 방식 비교 (50판 데이터 기준 오프라인 계산) |
| `hz_box.log`, `hz_table1.log`, `hz_table2.log` | 토픽 주기 측정 로그 |
| `policy_server_smoke.log`, `fake_server_ep7.log` | 정책 서버·가짜 정책 서버 시험 로그 |
| `runs/trial_<시각>.jsonl` (57개) | 시험 한 번의 이벤트 기록 (시작 설정, 단계, 결과). `collect_runs.py` 가 읽음 |
| `runs/index.md` | 시험별 표 — `collect_runs.py` 가 매번 새로 만듦 (직접 고치지 않음) |
| `runs/notes.md` | 시험별 사람 메모 → index.md 메모 칸으로 옮겨짐 |
| `runs/shadow_<시각>/` (6개) | 그림자 모드 기록: `summary.json`, `ticks.jsonl`, 5초 간격 front/wrist 사진 |
| `runs/C_diag_20261008/` | C단계 진단 스크립트 (카메라 밝기·코덱·주기·공유 메모리·재생 비교) + 비교 사진 |
| `runs/D_diag_20261008_sag/` | D단계 팔 처짐(sag) 진단 스크립트 (자세 검색·검증, 처짐 모델, 탁자 접촉) |

### `range_check/<YYYYMMDD_HHMMSS>/ranges.json`
`~/so101_boxpick/scripts/teleop_view.py` 의 기본 저장 위치. 실행 한 번에 폴더 하나, 관절 6개의 min/max(°) 를 기록. 10-13 2회, 10-22 4회 (11:17, 13:01, 14:15, 17:23).

### `rollout/이번 rollout 전에는 하나가 특히.txt`
10-08 메모: rollout 전에 트윈 실물 세션 뒤 12V 전원을 껐다 켰는지 확인 (트윈이 서보에 써 둔 속도 제한이 남는 문제), 트윈·정책 서버 종료 확인 명령.

### `calibration_backup_20261002/`
lerobot 캘리브레이션 파일 백업 (10-02). `robots/so_follower/my_arm.json` (팔로워), `teleoperators/so_leader/my_leader.json` (리더) + `my_leader.json.bak-20260929`. 관절마다 id, drive_mode, homing_offset, range_min/max.

### `_deleted/redbox_t2_known_3cube_20261014_161637/`
`main/redbox_t2_known` 에서 지운 2판. T2 를 "빨강 3개 고정"으로 찍다가 "빨강 2–4개"로 설계를 바꾸며 사용자 요청으로 옮김 (10-14). dataset(2판), review_videos 2개, setup_photos, notes.md, layout.csv. 해당 녹화의 record_ui 실행 기록은 `~/.local/state/record_ui/deleted_runs/`.

### 문서 파일
| 파일 | 내용 |
|---|---|
| `README.md` | 폴더·이름·학습·평가 규칙. `record_ui.py` 가 파일이 없을 때 한 번만 쓴 템플릿 + 10-06 손으로 넣은 링크. 이후 구조 변화는 반영 안 됨 ([§10](#10-readmemd-와-다른-점)) |
| `reorg_plan.md` | 10-21 폴더 정리 계획 초안 (analysis/, external/, backup/ 로 옮기기, 공용 평가 코드를 boxpick 으로). **아직 아무것도 옮기지 않음**. main_k8 은 이 계획 뒤에 생겨 계획에 없다 |
| `camera_settings.md` (+ `camera_settings/cam_wb_compare.jpg`) | 수집·평가 모두 자동 노출(`auto_exposure=3`)·자동 화이트밸런스, `exposure_dynamic_framerate=0` 으로 정한 결정과 측정 기록 |
| `ros2_guide.md` | Thor 의 ROS2 트윈(`~/Ros2`, 브랜치 arm-jetson) 사용 설명서 (10-07, 문서·스크립트를 읽고 정리) |
| `docs/practice_10_pi05_2k.md` | practice_10 π0.5 2k 학습과 실물 평가 정리 (10-02 ~ 10-06) |

---

## 9. 코드는 어디 있나

이 폴더의 결과물을 만드는 프로그램은 대부분 `~/so101_boxpick/scripts/` 에 있다.

| 스크립트 | 하는 일 | 쓰는 곳 |
|---|---|---|
| `record_ui.py` | lerobot-record 를 감싼 녹화 UI (배너, 사전 점검, 키, 후처리) | 세션 `notes.md`, `setup_photos/`, `review_videos/`, 카테고리 README, `README.md` (최초) |
| `layout_plan.py` | 배치 계획 만들기·상태·제외(exclude)·검증(verify) | `layout*`, `*.bak_*` |
| `check_dataset.py` | 데이터셋 품질 검사 | `qa_report.md`, `qa/` |
| `redbox_heatmap.py` | 위치 분포 히트맵 | `qa/heatmap.png` |
| `servo_plot.py` | 관절 궤적 그래프 | `qa/servo_*.png` |
| `cube_angle.py`, `cube_glyph.py`, `banner_preview.py` | 큐브 각도 측정 / 배너 큐브 그림 / 배너 미리보기 | main_k8 QA·녹화 |
| `train_summary.py` | 체크포인트 설정 + 학습 로그 → 학습 설정 표 | `train/…/training_params.md/.csv` |
| `eval_ui.py` | 실물 평가 UI (판별 입력) | `eval/rollouts/…/results.*`, `eval/index.md`, `eval/results_all.csv` |
| `eval_ab_ui.py`, `eval_ab_child.py`, `eval_ab_report.py`, `eval_space_report.py`, `space_geom.py`, `eval_ab_mock.py` | A/B·공간 평가 UI, 집계, 구역 정의, 가짜 팔 시험 | `main/redbox_all/eval/eval_ab/`, `eval_space/` |
| `pregrasp_angles.py`, `pregrasp_review.py`, `pregrasp_report.py` | 잡기 직전 분석 | `main/redbox_all/eval/pregrasp_*` |
| `train_roll_census.py`, `train_roll_report.py`, `train_roll_position_report.py` | 학습 데이터 손목 회전·위치 조사 | `main/redbox_all/eval/train_roll_census/` |
| `teleop_view.py` | 텔레오퍼레이션 관절 보기 | `range_check/` |
| `servo_dump.py`, `check_env.py`, `pi05_check.py` | 서보 설정 덤프, 환경 점검, π0.5 점검 | (이 폴더에 출력 없음) |

설정 파일: `~/so101_boxpick/config/redbox_layouts.yaml` (main 의 384판, K1–K4), `~/so101_boxpick/config/redbox8_layouts.yaml` (main_k8·K8 파일럿, K1–K8).
이 폴더 안에 있는 코드: 세션 `eval/` 의 rollout 스크립트 복사본 (세션마다 경로만 바꿔 씀), `redbox_all/eval/`·`reference/`·`e0_j0/runs/*_diag_*` 의 일회성 분석 스크립트.
실행 환경: `~/so101-env` (lerobot 0.6.2 venv).

---

## 10. README.md 와 다른 점

| # | README.md 내용 | 실제 | 원인 |
|---|---|---|---|
| 1 | 맨 위에 README.md, docs/, practice/, main/ 만 | §1 의 항목 전부 | README 는 `record_ui.py` 의 `ROOT_README` 템플릿을 **파일이 없을 때 한 번만** 쓴다. 이후 생긴 폴더는 반영되지 않는다 |
| 2 | 카테고리는 practice, main | + `main_k8` | 10-22 새 카메라·K1–K8 로 다시 찍기 위해 추가 (record_ui·layout_plan·check_dataset·eval_ui 의 세션 이름 규칙에 `main_k8` 허용 추가) |
| 3 | 세션 폴더 = notes.md, setup_photos/, dataset/, review_videos/, train/, eval/ | + qa_report.md, qa/, layout.*, positions_manual.csv, *.bak_* | README 이후에 생긴 도구: `check_dataset.py`, `layout_plan.py` |
| 4 | `train/<실행이름>/` | `train/<배치>_<스텝>/<실행이름>/` + 실행 스크립트·로그 | 10-13 사용자 요청으로 묶음. practice_10·practice_50 은 옛 방식 |
| 5 | `eval/<평가이름>/` 에 영상과 `results.md` | `eval/rollouts/<시각>_<스텝>_<tag>/`, `eval/index.md`, 연구 폴더(`eval_ab/` 등), 스크립트 복사본 | `eval_ui.py` (10-13), `eval_ab_ui.py` (10-19) 의 저장 구조 |
| 6 | 세션은 record_ui.py 로 녹화 | `main/redbox_all` 은 merge 결과 | lerobot-train 이 repo_id 여러 개를 받지 않음 |
| 7 | 분석 결과 위치 규칙 없음 | 세션 `eval/`, 맨 위 `redbox_all/eval/`, `reference/analysis_*`, `reference/range_compare_*` | README 에 규칙 없음. 정리 계획은 `reorg_plan.md` |
| 8 | 이름: 영어 소문자·숫자·밑줄 | 한글 파일 이름 다수 (`redbox_수집명령.md`, `파일럿_명령.md`, `rollout/이번 rollout…txt`, 연구 폴더 안 보고서·그림) | 규칙 대상은 세션·학습 실행·평가 이름. 세션 이름은 모두 규칙을 따른다 |
