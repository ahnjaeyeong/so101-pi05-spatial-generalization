# CHANGELOG

형식: 날짜 · 바뀐 것 · 관련 실험 ID. 새 실험·결과·정정이 생길 때마다 위에 추가한다.

## 2026-11-02 — 저장소 생성
- 11-02 전수 조사 문서 01–10 과 조사 노트 5개를 `docs/` 로 이관.
- 실험 12개 (EXP-01 ~ EXP-12) 폴더와 README 작성, 보고서 ID (S1-01 …) 연결.
- 원본 기록 1,335개 (약 99 MB) 를 `experiments/*/sources/` 등으로 복사, `SOURCES_MANIFEST.csv` 에 원본 경로·SHA-256 기록 (`tools/sync_sources.py`).
- 학습 실행 11개 설정 (`configs/training/`), 체크포인트 28개 경로·크기·SHA-256 (`configs/checkpoints/`), 데이터셋 23개 메타 (`configs/datasets/`), loss 표·그림 (`analysis/`) 생성 (`tools/collect_run_metadata.py`).
- 평가 요약 (`evaluations/`), 템플릿, `CLAUDE.md`, 검사 스크립트 (`tools/check_repo.py`) 추가.
- 상태 기준: EXP-09 PAUSED, EXP-11 IN_PROGRESS, EXP-12 PLANNED.
