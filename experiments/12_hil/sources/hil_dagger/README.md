# hil_dagger — LeRobot 공식 DAgger (0.6.2) 재사용 HIL 교정 수집 준비

보고서: `docs/02_ui_보고서.md` (수집자 화면) · `docs/01_v2_보고서.md` (v2 안전 변경, 우선) · `docs/00_보고서.md` (v1 조사). 2026-11-04 작성, 실물 미시험.

- 수집 = 설치된 lerobot 0.6.2 `lerobot-rollout --strategy.type=dagger` (교정만 녹화) + `tools/hil_dagger_entry.py` (런타임 adapter, lerobot · d2 파일 수정 없음).
- 실물 명령: `tools/run_hil.sh <tag>`. 사용자가 직접 실행하고, 실물 시험 승인 전에는 실행하지 않는다. `DRY=1` 을 붙이면 명령만 출력한다.
- 세션 QA: `python tools/hil_qa.py sessions/<세션>`.
- 가짜 장치 시험 전체: `tests/run_all.sh`. CPU 전용이며 실물 · GPU · 사용자 키보드를 차단한다. 약 4 분 걸리고 결과는 `tests/_out/FACTS.md` 에 나온다.
- 공식 변환 시험: `tests/test_convert.sh`. 실물 명령 인자 파싱 확인: `env -u DISPLAY CUDA_VISIBLE_DEVICES= python tests/test_cli_parse.py`.

키 (실물 세션 터미널):

| 키 | 동작 |
|---|---|
| Space | 정책 시작/정지 |
| Tab | 교정 시작/끝 (끝 = 저장) |
| m | 복구 완료 |
| 1 / 2 / 3 | 유형 R1 / R2 / R2-O |
| g / h | 첫 파지 성공 / 실패 |
| b / f | 최종 작업 (상자 안) 성공 / 실패 |
| r | 원위치 구간 |
| Esc | 종료 → 터미널에서 home / release / hold 선택 (자동 복귀 없음, Enter = hold) |

정책 추론 오류가 나면 정책 명령을 끊고 정지한다. 그 세션에서는 정책을 재개할 수 없다.

## 수집자 화면 (Collector Mode)

- `run_hil.sh` 가 화면 프로세스를 함께 띄운다 (`VIEWER=0` 이면 끔). 화면은 보기만 하고, **키는 터미널 창에서** 누른다.
- 미리보기 (로봇 · 카메라 · GPU 없음): `python3 tools/hil_viewer.py --preview`. ← / → 로 17 상태를 넘긴다.
- 스크린샷: `docs/ui/` (`sheet_preview_all.png`, `live/`, `compare_before_after.png`).

