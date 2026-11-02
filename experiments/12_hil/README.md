# EXP-12 · HIL (정책 실행 중 인간 교정) 검토 및 향후 실물 평가

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-12** (보고서 ID S7-03) |
| 날짜 | 정의 2026-11-02 16:32 |
| 상태 | `PLANNED` — **설계·검토 단계. 구현·실물 검증 없음** |

## 목적·정의
- 목적 [계획]: 정책이 실제로 빠지는 실패 상태에서 사람 교정 시연을 얻어 복구 행동을 학습시키는 방안 검토.
- `…/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md` 의 **방안 B "정책 실행 중 인간 교정 (HIL)"**: 정책 정지 → RTC/Action Queue 폐기 → 리더 팔을 팔로워 자세에 동기화 → 단일 writer 로 제어권 전환 → 사람 교정 녹화.
- 이 문서 이전 파일에는 HIL·DAgger·intervention 용어가 없다. 이전 설계 문장: `vision_probe/실험설계.md:173-176` "정책 실패 직후 이어서 사람이 교정하는 판도 포함한다" (설계만).

## 방안 A (EXP-11 수동 복구 시연) 와 비교 [가설·계획]
| 항목 | 방안 A (수동 복구 상태) | 방안 B (HIL) |
|---|---|---|
| 시작 상태 | 준비 단계에서 사람이 만든 상태 | 정책이 실제로 만든 상태 |
| 실패 상태 일치 | 조건을 맞춰야 함 | 그대로 일치 |
| 장치 | 현재 도구로 가능 | 새 구현 + 가짜 팔 harness 안전 검증 필요 |
| 안전 | 천천히 만든 자세 | 전환 순간 리더–팔로워 차이로 급한 움직임 위험 |
| 수집 효율 | 판당 1번 확실 | 해당 실패 빈도 2/20 |
| 데이터 | action = 리더 | 정책 구간·사람 구간 혼재 |
- [계획] 결론: **1차 방안 A (실패 상태 맞춤), HIL 은 2차**. 정책과 teleop 이 동시에 팔로워에 명령하는 구성은 만들지 않음.

## 검증 가설
- [가설] 실패 상태 그대로에서 얻은 교정 시연이 수동으로 만든 상태의 시연보다 분포가 정확하다 (OFF/05). 미검증.

## 데이터셋·모델·학습·평가
없음 (`PLANNED`). 전환 트리거 후보: 안전 정지 조건 S4b (본 뒤 손목 놓침 + 회전), S5 (목표를 30° 넘게 지남) — 오프라인 20판에서 이탈 2판을 4–8 s 일찍 잡음, 구현 안 함.

## 향후 실물 평가 계획 (전체, 모두 `PLANNED`)
- Held-out H 32편 녹화 (지정 위치 U1–U8 × 각도 4, 학습 금지) — [`configs/layouts/redbox8_heldout_h.yaml`](../../configs/layouts/redbox8_heldout_h.yaml) (U `confirmed: false`).
- sampling ablation 정책당 T1 16회 (KT 4 · RT 4 · UF 4 · UN 4), 필터 켬.
- 필터 A/B 남은 12판, 각도 고정 대응 비교.
- R1/R2 재학습 후 평가 (프로토콜 미정).
- 측정 지표 정의: [`evaluations/README.md`](../../evaluations/README.md).

## 한계 및 미확인
연구자가 말하는 "HIL" 과 OFF/05 정의가 같은 의미인지 확인 필요.

## 원본 자료
[`../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md`](../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md), [`analysis_handoff.md`](../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/analysis_handoff.md), [`docs/06`](../../docs/06_HIL_및_향후실험.md).
