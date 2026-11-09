# CHANGELOG

형식: 날짜 · 바뀐 것 · 관련 실험 ID. 새 실험·결과·정정이 생길 때마다 위에 추가한다.

## 2026-11-09 — EXP-15 SG50 수집 + sgft01 FT · EXP-16 실물 평가 (branch: exp/15-sg50-sgft01-20261109, records/handoff-20261105 위)
- **EXP-15 신규** `experiments/15_sg50_sgft01/`: SG50 수집 도구 · 결정 (11-05 ~ 11-06) — 손목 주황 닫기 프레임 (ref-v5), 수평계 (FK 0 점 보정), 그리퍼 열기 알림, 수직 최대거리, K 8 + 영역 무작위 32 계획, 시작 자세 S0, 진행 순서 숄더팬 → 열기 → 찾기 → 이동. 예비3 43 편 (학습 40). sgft01 = d2 020000 → 40 편 expert-only 10k (11-06 16:07 ~ 11-07 20:11, loss 0.213→0.019). 오프라인 [in-sample]·[반사실] 표 요약. 상태: 수집 PARTIAL · 학습 COMPLETED · 오프라인 COMPLETED.
- **EXP-16 신규** `experiments/16_sgft01_real_eval/`: sgft01 010000 실물 8 판 (11-09 10:03 ~ 10:19) 2/8 [사람] — K 2/5 · U 0/3, HU3 미시험 · K8 2 회, 안전 정지 0. 단계별 측정 · 실패 모양 · 장면 표 (원본 영상에서 추출 8 장, `EXTRACTED.csv`).
- **EXP-11** 수집 도구 사본 `sources/r1_r2_collection/` 갱신 (신규 34 · 변경 3: `tools/sg_*.py` · `config/sg50.yaml` · `13_sg50_sticker.md` · 시험 · 화면 사진).
- 메타: `configs/training/RUNS.csv` + `sgft01_p3_10k_s2001/`, `configs/datasets/` (sg50_pilot · pilot2 · pilot3 · sgft01_real_eval_rollout), `analysis/loss/sgft01_p3_10k_s2001_loss.csv`, 체크포인트 SHA-256 4 개 `experiments/15_sg50_sgft01/checkpoints_sha256.txt` (configs/checkpoints 는 로컬만).
- `EXPERIMENT_INDEX.md` (16 실험 · 13 학습), `README.md` 4 · 5 · 9 · 10 절, `evaluations/real_robot/README.md` (EXP-16 1 행), `evaluations/offline/README.md` (EXP-15 1 행).
- 도구: `tools/sync_sources.py` MAPPINGS (practice/sg50_pilot{,2,3} · io-capture 20261106-1607 SUMMARY · main_k8/sgft01_real_eval), `tools/archive_excluded.py` TARGETS (15 · 16). `SOURCES_MANIFEST.csv` +315 / −3 행.
- Git 제외 목록: `experiments/15_sg50_sgft01/sources/ARCHIVE_EXCLUDED.csv` (609 파일, 47,319 MB — 체크포인트 · dataset 영상) · `16_sgft01_real_eval/sources/ARCHIVE_EXCLUDED.csv` (2,295 파일, 340 MB) · EXP-11 목록 갱신 (3,887 파일, 201 MB).
- **갱신하지 않음**: `ARCHIVE_MANIFEST.csv` · `inventory/` (11-05 와 같은 이유 — 전체 재생성이 크기 제한 초과).

## 2026-11-05 — HANDOFF · EXP-14 실물 파일럿 · EXP-11/12 현행화 (branch: records/handoff-20261105, EXP-13 위)
- `HANDOFF.md` 추가: 사용자 제공 초안을 로컬 원본과 대조해 수정 (12 항목, 문서 부록 A — 과제 문장, RC episode ID, 750 SHA, Trial 1 목표 32.1°, Trial 8–16 Wrist 놓침 0, HIL 19/205 · fault_latch 31/31, 교란 추가 등).
- **EXP-14 신규** `experiments/14_rft01_real_pilot/`: rft01 001000 vs d2 020000 실물 16판 (11-05). FT 4/8 · BL 5/8 [사람]; Known 3/4 vs 2/4, Unknown 1/4 vs 3/4 — Unknown 은 시작 그리퍼 (FT 닫힘 / BL 열림) · 모델 순서 교란으로 비교 무효, 모델 우열 미결정. 사본 `sources/rft01_real_pilot/` (scripts, config, results, reports, run 별 작은 로그, 시작 사진, 시험).
- **EXP-11** 상태 `IN_PROGRESS` → `PARTIAL`: 11-02 의 '본 수집 0편' 이후 11-03 ~ 11-04 pilot12 수집 반영 (R1 8 중 유효 4, RC 13 중 유효 12, R2-P 6 미사용, r2o dataset 없음). 세션 사본 `sources/sessions/r12_pilot12_{r1,rc,r2p,r2o}/`, 수집 도구 사본 `sources/r1_r2_collection/` 다시 복사 (신규 78 · 변경 7). 11-02 기록은 '이력' 으로 남김.
- **EXP-12** 상태 `PLANNED` → `IN_PROGRESS`: 11-04 HIL 수집 도구 구현 (LeRobot 0.6.2 dagger + adapter A1–A12), 가짜 장치 시험 179/179 (v2) · 205/205 (UI). 실물 안전 검증 · 수집 0. 사본 `sources/hil_dagger/` (가짜 장치 출력 · upstream LeRobot 소스 사본 제외).
- **EXP-13** 실물 상태 `NOT_EVALUATED` → EXP-14 연결.
- `EXPERIMENT_INDEX.md` (14 실험), `README.md` 5 · 9 · 10 · 11 절, `evaluations/real_robot/README.md` (EXP-14 2행), `evaluations/comparisons/README.md` (FT vs BL 1행).
- 도구: `tools/sync_sources.py` MAPPINGS 추가 (pilot12 세션 4 · hil_dagger · rft01_real_pilot), `--only <prefix>` (선택 매핑만 복사, 다른 manifest 행 유지), `.git` 폴더 제외; `tools/derive_condensed.py --only` (rft01 FT 세션 `debug.log` 축약 1, `ticks_ep1.csv.gz` 해제 16, rollout `dataset_state_action.csv` 8); `tools/archive_excluded.py` 신규.
- `SOURCES_MANIFEST.csv` +659 / −45 행 (r1_r2_collection 45 행은 새 해시로 교체), `DERIVED_MANIFEST.csv` +25 행.
- Git 제외 목록 (경로 · 크기 · SHA-256, 영상 포함): `experiments/{11_r1_r2_recovery,12_hil,14_rft01_real_pilot}/sources/ARCHIVE_EXCLUDED.csv` — 3,514 · 830 · 43,270 파일 (188 · 98 · 838 MB). 50개 넘는 폴더 (프레임 JPG 등) 는 폴더 1행 요약.
- **갱신하지 않음**: `ARCHIVE_MANIFEST.csv` · `inventory/` (11-02 상태 유지). 11-05 전체 재생성 결과가 12 MB · 9.4 MB 로 `check_repo.py` 크기 제한 7 MB 초과. 그 실행에서 '매핑 없음' 864 파일 = `main_k8/d2/visual_dependency` 861 + Desktop R2P 가이드 PNG 3 (이번 범위 밖, 미기록).

## 2026-11-04 — EXP-13 d2 + R1/R2 교정 시연 Fine-tuning (branch: exp/13-recovery-ft-20261104)
- `experiments/13_recovery_ft/` 추가: d2 020000 → d2 256 + R1 4 + R2(RC) 12 (272편) expert-only 1,000 step (run `rft01_d2rc16_W5_1k_s2001`, seed 2001) 와 오프라인 재추론 평가 요약.
- `sources/recovery_ft/` (63개, 1.7 MB): 데이터 선정 · 병합 · 검증 · 학습 · 평가 스크립트, manifest, 검증·평가 표, 작은 로그. 데이터셋 · 체크포인트 · eval/raw · 가중치 npy 제외. `tools/sync_sources.py` MAPPINGS 에 recovery_ft 추가 (이번에는 이 매핑만 복사, `SOURCES_MANIFEST.csv` 에 63행 추가).
- `configs/training/rft01_d2rc16_W5_1k_s2001/`, `configs/training/RUNS.csv` 1행. 체크포인트 해시는 `experiments/13_recovery_ft/sources/recovery_ft/logs/post/p01_ckpt_sha256.json` (로컬 `configs/checkpoints/` 은 `.gitignore` 의 `checkpoints/` 규칙으로 Git 미추적 — 기존부터; 이번에 바꾸지 않음).
- 상태: 학습 COMPLETED · 오프라인 평가 COMPLETED · 실물 NOT_EVALUATED. EXP-11 (시연 세션 매핑) · inventory/ARCHIVE_MANIFEST 는 이번에 갱신하지 않음.

## 2026-11-02 — 원본 완전성 점검 (PR: data/source-completeness-20261102)
- 로컬 원본 10,873개를 파일 단위로 분류·비교 (`tools/compare_sources.py`, `inventory/`): GitHub 직접 2,906 · 축약 반영 99 · 해시만 기록 7,868 · 매핑 없음 0. 작업 중인 `main_k8/r2_grasp_diagnostic` (다른 세션) 제외.
- 추가: 녹화 첫 화면 사진 20곳, 평가 trial 122판 기록 (틱별 명령·실제 관절 `ticks.csv`, 추론 기록, 시작 화면), 10-29 계측 diag 기록·첫 chunk 관측 PNG 52장, QA 히트맵·서보 그래프·`servo_data.json`, 10-22 카메라 보정 작업 파일 148개, main_k8 설정 그림, Desktop 스냅샷 18개, Action Expert G1/G2 결과 표, 팔 캘리브레이션 백업·관절 범위·환경 requirements, 세션 폴더 잔여 파일.
- 축약·변환 105개 (`DERIVED_MANIFEST.csv`): 2 MB 넘는 rollout 로그 12개 축약, gz 표 6개 해제, 사람 시연 서보 타임라인 10 Hz wide CSV, rollout 24개의 명령 (action) vs 실제 (state) CSV, 10-26 d2 평가 영상 첫 프레임 10장 추출 (영상 경로·시각 기록), 10-29 원본 관측 PNG 52장.
- `ARCHIVE_MANIFEST.csv`: Git 제외 원본 경로·크기·SHA-256 (6,452개 해시; 체크포인트·영상·외부 데이터·F1 특징은 크기만).
- 규칙 변경: 텍스트 최대 6.5 MB, 로그 2 MB; 진행 막대 학습 로그·메모리 로그 7개는 Git 에서 제거 (loss 는 `analysis/loss/`, 해시는 ARCHIVE_MANIFEST).
- `configs/camera/README.md`: 카메라 설정·이동 전후 화면·보정·좌표계 기록. 카메라 설치 모습 외부 사진은 원본 없음.

## 2026-11-02 — 저장소 생성
- 11-02 전수 조사 문서 01–10 과 조사 노트 5개를 `docs/` 로 이관.
- 실험 12개 (EXP-01 ~ EXP-12) 폴더와 README 작성, 보고서 ID (S1-01 …) 연결.
- 원본 기록 1,335개 (약 99 MB) 를 `experiments/*/sources/` 등으로 복사, `SOURCES_MANIFEST.csv` 에 원본 경로·SHA-256 기록 (`tools/sync_sources.py`).
- 학습 실행 11개 설정 (`configs/training/`), 체크포인트 28개 경로·크기·SHA-256 (`configs/checkpoints/`), 데이터셋 23개 메타 (`configs/datasets/`), loss 표·그림 (`analysis/`) 생성 (`tools/collect_run_metadata.py`).
- 평가 요약 (`evaluations/`), 템플릿, `CLAUDE.md`, 검사 스크립트 (`tools/check_repo.py`) 추가.
- 상태 기준: EXP-09 PAUSED, EXP-11 IN_PROGRESS, EXP-12 PLANNED.
