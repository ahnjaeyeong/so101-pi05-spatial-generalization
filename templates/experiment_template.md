# EXP-NN · <실험 이름>

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-NN** (세부 ID 예: EXP-NN-a) |
| 날짜 | YYYY-MM-DD ~ YYYY-MM-DD |
| 상태 | `PLANNED` / `IN_PROGRESS` / `COMPLETED` / `NOT_EVALUATED` / `PAUSED` / `PARTIAL` / `STOPPED` |
| 표기 | [사실] 파일 측정값 · [관찰] 연구자 실물 관찰 · [가설] 분석 해석 · [계획] 설계만 |

## 목적
<무엇을 알고 싶은가>

## 검증 가설
- [가설] …
- 사전에 정한 판정 기준 (결과 보기 전에 적는다): …

## 데이터셋
| 이름 (repo_id) | 버전·경로 | 편 / 프레임 | 구성 (위치·각도·과제) |
|---|---|---|---|
- 메타데이터: `configs/datasets/<name>_info.json` (tools/collect_run_metadata.py 에 추가)
- held-out 여부: …

## 모델·학습
| 항목 | 값 |
|---|---|
| 시작 체크포인트 | |
| Vision freeze / Expert-only | |
| batch / steps (epoch) | |
| LR (peak → end, warmup, decay 실효값) | |
| seed | |
| 설정 파일 | `configs/training/<run_id>/` |
| 체크포인트 (경로·SHA-256) | `configs/checkpoints/CHECKPOINTS.csv` |
| loss | `analysis/loss/<run_id>_loss.csv` |

## 추론 설정
RTC (horizon, schedule, guidance, queue), denoise steps, max_relative_target, 필터, 실행 속도.

## 평가 방법
- 실물 / 오프라인 구분, 판정 방식 (사람·자동·분석), 위치·각도·시작 자세 통제 방법.

## 평가 결과
| 조건 | n | 첫 파지 | 최종 | 기타 지표 |
|---|---|---|---|---|

## 실패 사례
- [관찰] … (메모 원문)
- [사실] …

## 분석 결과
- [사실] …
- [가설] …

## 한계 및 미확인
- …

## 다음 실험으로 이어진 이유
- …

## 원본 자료
- 복사본: `sources/` (tools/sync_sources.py 의 MAPPINGS 에 추가)
- 원본 경로: `/home/user/so101_runs/...`
