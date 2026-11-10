# 로컬 원본 ↔ GitHub 파일 단위 비교 (2026-11-02)

생성: `tools/compare_sources.py` (전체 분류·해시) → `tools/focus_report.py main` (요청 항목별 전후 비교). 원본 쪽은 읽기만 했다.

| 파일 | 내용 |
|---|---|
| [`INVENTORY.csv`](INVENTORY.csv) | 로컬 원본 10,873개 파일 한 줄씩: 경로, 크기, 범주, 상태 (`in_repo` / `derived` / `archived` / `unmapped`), 제외 사유, 저장소 경로 |
| [`../ARCHIVE_MANIFEST.csv`](../ARCHIVE_MANIFEST.csv) | Git 에 넣지 않은 파일 (+ 축약본으로만 반영한 원본): 경로·크기·**SHA-256**·사유·대응 축약본. 체크포인트 폴더·영상·외부 공개 데이터·F1 특징은 크기만 (`NOT_HASHED_LARGE_TREE`; 체크포인트 가중치 해시는 `configs/checkpoints/CHECKPOINTS.csv`) |
| [`../DERIVED_MANIFEST.csv`](../DERIVED_MANIFEST.csv) | 저장소 안의 축약·변환·추출 파일과 그 원본 경로·SHA-256·방법 |
| [`../SOURCES_MANIFEST.csv`](../SOURCES_MANIFEST.csv) | 그대로 복사한 파일의 원본 경로·SHA-256 |
| [`FOCUS_TABLE.md`](FOCUS_TABLE.md), [`SUMMARY_TABLES.md`](SUMMARY_TABLES.md) | 아래 표의 원본 |

범위: `/home/user/so101_runs` 전체, `/home/user/so101_boxpick/config`, 10-22 K8 보정 작업 임시 폴더, Desktop 의 연구 이미지 (`redbox*`, `SO101*`, `cam_*`).
제외: 다른 세션이 작업 중이던 `main_k8/r2_grasp_diagnostic` (30,235개, 230 MB — 계속 바뀌는 중이라 복사하지 않음).

## 1. 요청 항목별 (이전 = 이 PR 전 main 브랜치)
| 항목 | 로컬 원본 | 이전 GitHub (main) | 현재 직접 등록 | 축약·변환 반영 | 해시만 기록 | 누락 (매핑 없음) |
|---|---|---|---|---|---|---|
| 카메라 이동 전 사진 (옛 front, ~10-21) | 306 | 1 | 306 | 0 | 0 | 0 |
| 카메라 이동 후 사진 (새 front, 10-22~) | 1635 | 0 | 75 | 52 | 1508 | 0 |
| 카메라 보정·좌표계 | 46 | 3 | 43 | 0 | 3 | 0 |
| 공간 일반화 히트맵·위치 분포 | 40 | 25 | 35 | 0 | 5 | 0 |
| Shoulder Pan / Wrist Roll 시계열 | 143 | 74 | 136 | 6 | 1 | 0 |
| 명령값 vs 실제 관절값 | 204 | 40 | 169 | 24 | 11 | 0 |
| RTC / Action 로그 | 1198 | 0 | 186 | 12 | 1000 | 0 |
| Action Expert 분석 그래프·표 | 80 | 50 | 80 | 0 | 0 | 0 |

- "해시만 기록" 은 Git 에 없지만 `ARCHIVE_MANIFEST.csv` 에 원본 경로·SHA-256 이 있다. 주요 내용: 10-29 계측 관측 PNG 1,508장 (에피소드 첫 chunk 52장은 등록), RTC chunk 원본 `.npz` (계측 780 + 평가 trial 122), 2 MB 넘는 rollout 로그 12개 (축약본 등록), 하네스 시험 기록.
- 이동 후 사진 "직접 등록 75" 에는 10-26 평가 영상에서 추출한 프레임 10장이 포함되지 않는다 (그것들은 축약·변환 쪽의 원본 영상 기준으로 집계).

## 2. 전체 범주별
| 범주 | 로컬 원본 | GitHub 직접 등록 | 축약·변환으로 반영 | 해시만 기록 (Git 제외) | 매핑 없음 |
|---|---|---|---|---|---|
| camera_photo | 2115 | 377 | 52 | 1686 | 0 |
| camera_calibration | 48 | 45 | 0 | 3 | 0 |
| heatmap_spatial | 42 | 37 | 0 | 5 | 0 |
| servo_pan_roll_timeseries | 490 | 291 | 6 | 193 | 0 |
| command_vs_actual | 166 | 46 | 24 | 96 | 0 |
| rtc_action_log | 1398 | 248 | 12 | 1138 | 0 |
| action_expert_analysis | 275 | 204 | 0 | 71 | 0 |
| dataset_or_checkpoint | 1627 | 0 | 4 | 1623 | 0 |
| training_log_config | 86 | 52 | 0 | 34 | 0 |
| other | 4626 | 1606 | 1 | 3019 | 0 |
| **합계** | **10873** | **2906** | **99** | **7868** | **0** |

| 제외 사유 | 파일 수 | 용량 (MB) |
|---|---|---|
| archived · raw_dataset_or_checkpoint | 934 | 424,004.8 |
| archived · dir:f1_features | 8 | 55,663.3 |
| archived · dir:f1_quality_features | 8 | 35,982.0 |
| archived · binary_ext | 289 | 4,119.8 |
| archived · dir:review_videos | 781 | 1,507.2 |
| archived · dir:frames_train | 1140 | 333.2 |
| archived · dir:obs | 1508 | 245.3 |
| archived · dir:frames | 258 | 70.9 |
| archived · qa_episode_sheet | 773 | 44.0 |
| archived · dir:servo | 187 | 38.9 |
| archived · dir:harness | 297 | 26.4 |
| archived · dir:reg | 421 | 22.7 |
| archived · deleted_session | 13 | 21.6 |
| archived · train_log | 22 | 18.3 |
| archived · external_public_dataset | 105 | 8.6 |
| archived · dir:chunks | 780 | 7.9 |
| archived · external_public_dataset_meta | 24 | 4.1 |
| archived · dir:tmp* | 6 | 2.4 |
| archived · dir:replay | 8 | 2.3 |
| archived · dir:weights | 5 | 2.0 |
| archived · dir:runs_lat1.0 | 31 | 2.0 |
| archived · dir:runs_lat1.55 | 27 | 1.7 |
| archived · external_public_repo_clone | 41 | 1.2 |
| archived · dir:runs_wide_lat1.55 | 29 | 1.1 |
| archived · dir:runs_wide_spike | 27 | 0.8 |
| archived · dir:runs_spike | 15 | 0.8 |
| archived · other_ext | 101 | 0.5 |
| archived · dir:preview | 8 | 0.1 |
| archived · dir:backup | 2 | 0.0 |
| archived · dir:dataset_empty_* | 10 | 0.0 |
| archived · dir:plan_preview | 5 | 0.0 |
| archived · dir:__pycache__ | 1 | 0.0 |
| archived · dir:dataset_empty_20261023_1333 | 1 | 0.0 |
| archived · dir:dataset_empty_20261015_1449 | 1 | 0.0 |
| archived · dir:ctrl | 2 | 0.0 |

| 제외: 다른 세션이 작업 중인 폴더 `main_k8/r2_grasp_diagnostic` | 35035 | 261.5 |

## 3. 이번에 새로 추가한 것 (이 PR)
| 종류 | 수 | 위치 |
|---|---|---|
| 직접 복사 (원본 그대로) | 2,906 − 1,336 = 1,570개 추가 (학습·메모리 로그 7개는 규칙에 따라 Git 에서 빠짐) | `SOURCES_MANIFEST.csv` |
| 녹화 첫 화면·설치 시점 사진 | 세션·파일럿 20곳 × front/wrist (+ cubemark 1) | `experiments/*/sources/**/setup_photos/` |
| 평가 trial 기록 | 122판 × (`ticks.csv` 명령·실제 관절 틱 로그, `inferences.csv`, `trial.json`, `verdict.json`, `start_front/wrist.png`) | `experiments/04…/eval_ab`, `…/eval_space_20k`, `experiments/05…/eval_space_30k` 의 `trials/` |
| 10-29 계측 기록 | 4 실행 × (`ticks.csv`, `chunks.jsonl`, `manifest/summary/verify.json`) + 첫 chunk 관측 PNG 52장 | `experiments/06_d2_256/sources/d2/eval/rollouts/20261029_*/diag/` |
| QA 폴더 | 히트맵, 서보 시간축·K별 그래프와 `servo_data.json`, 위치표, overview·layout 시트 (판별 `ep_N.jpg` 773장 제외) | `experiments/*/sources/**/qa/` |
| 카메라 보정 작업 파일 (10-22) | 148개 | `experiments/06_d2_256/sources/k8_relayout_scratch_20261022/` |
| main_k8 설정 그림 | 9개 | `experiments/06_d2_256/sources/main_k8_setting/` |
| Desktop 스냅샷 | 18개 (K1–K4 보정·히트맵·분포, cubemark 장면, R1/R2 UI) | `experiments/{02,03,11}…/sources/desktop_snapshots/` |
| Action Expert 요인 실험 표 | G1·G2·G1c `rows.csv`·`run.json` (action_bottleneck + sampling eval) | `experiments/08…`, `experiments/09…` |
| 팔 캘리브레이션 백업·관절 범위·환경 | | `configs/robot/`, `configs/env/` |
| 축약·변환 (DERIVED_MANIFEST) | 105개: 로그 축약 12, gz 해제 6, 서보 타임라인 10 Hz 1, rollout 명령·실제값 CSV 24, 영상 프레임 10, 원본 관측 PNG 복사 52 | 각 원본 대응 위치 |

## 4. 원본이 없는 항목
| 항목 | 상태 |
|---|---|
| 카메라 거치대·설치 모습을 바깥에서 찍은 사진 (이동 전·후) | 로컬 어디에도 없음. 카메라가 찍은 화면만 있음 |
| 10-22 카메라 이동 이유, 카메라 높이·기울기 실측 | 없음 (높이 46 ± 2 cm 어림만) |
| 10-13 K1–K4 보정 계산 스크립트·중간 결과 | 세션 임시 폴더 삭제됨 (H 행렬 결과만 yaml 에 있음) |
| 10-26 d2 평가 시작 사진 | 저장된 사진 없음 → 원본 AV1 영상에서 추출 (10장, `EXTRACTION.md` 에 영상 경로·시각·해시) |
| 10-19 첫 sync rollout·practice_10 rollout 시작 사진 | 저장된 사진 없음 (영상만; 이번에 추출하지 않음) |
| main_k8 T2 세션 데이터·QA | T2 미녹화 |
| 로봇 base 실측 좌표 | 없음 |
