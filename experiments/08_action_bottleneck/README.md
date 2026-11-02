# EXP-08 · Action Expert 및 Wrist Roll 분석 (action_bottleneck)

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-08** (보고서 ID S6-01) |
| 날짜 | 2026-10-27 13:22 ~ 16:51 |
| 상태 | `COMPLETED` (오프라인 전용) |
| 모델 | d2 020000 |

## 목적·가설
F1 다음 단계: 시각 위치 추정 정확도와 Action Expert 행동 정확도를 분리하고, Expert 의 roll 조건부 공간 매핑이 실제로 부족한지 검증. [가설] 정책이 wrist_roll state 를 반영해 영상→탁자 좌표 회전을 하지 않는다.

## 데이터·방법
- G1: T1 128판 × 파지 2.5/1.5/1.0 s 전 프레임, roll state ±15/30° × wrist 영상 편집 (큐브 ±1 cm), noise 4 고정, denoise 5 [반사실].
- 가리기: roll 숫자 토큰만 (KR) / state 전체 (KS).
- G2: F1 프레임에서 정책 기울기 vs 사람 [in-sample], Expert hidden 층별 해독.
- state 경로: QUANTILES → 256 구간 → 숫자를 한 자리씩 프롬프트 토큰 → 고정 Gemma → expert 는 prefix KV 로만 state 를 봄.

## 평가 결과
| 지표 | 2.5 s | 1.5 s | 1.0 s |
|---|---|---|---|
| G_tt (접선 이득) | 0.30 | 0.20 | **0.10** |
| G_rr (반지름 이득) | 0.60 | 0.51 | 0.34 |
| w_rot (1 = roll 반영) | −0.01 | −0.09 | −0.18 |
- [사실] roll state 를 바꾸면 roll 행동은 거의 그대로 복사 (0.97–1.00), 위치 매핑은 돌리지 않음.
- [사실] KR → pan 0.29–0.32° (무효과), KS → pan 32–37°.
- [사실] Expert hidden: roll R² ≈ 1.00 (층 10+), 탁자 위치 MAE 0.19–0.28 cm, g_state 0.6–0.68.
- [사실] 같은 프레임 기울기 0–1 s 정책 0.10 vs 사람 0.21; 1–2 s 0.47 vs 0.42.
- [사실] roll 은 큐브 위치로 예측 안 됨 (R² ≈ 0); 실물 프레임 50% 가 학습 이웃 0개.

## 분석 결과
[가설] Expert 내부에는 roll 조건부 위치가 있으나 최종 행동이 쓰지 않음 (readout 병목). 문서는 판정 규칙의 어느 행을 적용했는지 명시하지 않음.

## 한계 및 미확인
roll 회전 중심 미정 (w_state·w_RC 가정 의존), 편집은 배경 그대로, d2 하나만.

## 다음 실험으로 이어진 이유
"roll 조건부 부족·초기 접근 오차가 표본 비율·희소성 때문인가?" → EXP-09.

## 원본 자료
[`sources/action_bottleneck/`](sources/action_bottleneck/), 원본 `/home/user/so101_runs/main_k8/d2/action_bottleneck/`.
