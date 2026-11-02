# CHANGELOG

형식: 날짜 · 바뀐 것 · 관련 실험 ID. 새 실험·결과·정정이 생길 때마다 위에 추가한다.

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
