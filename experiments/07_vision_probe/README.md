# EXP-07 · Vision / VLM Feature Probe (F1)

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-07** (보고서 ID S5-01 ~ S5-04) |
| 날짜 | 설계·CPU 2026-10-26, GPU 본실행 10-27 09:36 ~ 12:10 |
| 상태 | `COMPLETED` (오프라인 전용, 로봇 평가 없음) |
| 모델 | d2 020000 (vision·Gemma 가중치는 pi05_base 와 bit 동일) |

> 이 실험의 결과는 **오프라인 probe** 다. 실물 성공률이 아니다.

## 목적·가설
막판 좌우 교정 부족 (G_tt 0.10) 이 frozen Vision/VLM 표현 문제인지 Action Expert 문제인지 분리.

## 데이터
d2 256편, 파지 3 s 안 probe 프레임 7,810. 판 단위 5-fold + 위치 hold-out + 3 cm 완충 ([held-out fold], 정책 자체는 모든 판을 학습함). 편집 프레임 (큐브 ±1 cm 이동) 403쌍. 실물 10-26 5판 프레임 303.

## 방법
SigLIP·Gemma (V/K) 층별 특징 → ridge → 손목 화면 큐브 상대 좌우 (roll 회전, cm). g_rep = 편집에 따라가는 정도. 사전 등록 판정: MAE ≤0.15 cm & g_rep ≥0.7 = 정확.

## 결과
| 항목 | 값 |
|---|---|
| [사실] 가중치 확인 | vision tower 63/63, projector 2/2, Gemma 23/23 bit 동일 |
| [사실] SigLIP L26 | MAE **0.079 cm** (R² 0.97) |
| [사실] Gemma V L0 / L11 / L17 | 0.080 / 0.091 / 0.120 cm |
| [사실] 기준선 | wrist RGB 0.085, wrist 마스크 0.042, state 만 0.297, front RGB 0.540 cm |
| [사실] g_rep | SigLIP 0.57–0.65, Gemma 0.59–0.73 vs **정책 G_tt 0.10** |
| [사실] front 탁자 절대 위치 | Gemma L14 V 6.27 cm, SigLIP L26 10.46 cm (약함) |
| [사실] 실물 프레임 | 50% 가 학습 범위 밖 → 모든 probe R² ≤ 0.02; 범위 안 153 프레임 0.21 cm |
| [사실] 영상 품질 | wrist 밝기 ±20% 무영향; blur σ2 0.077 → 0.120; front crop 1.6× 는 오히려 악화; 실물 wrist 큐브 밝기 5판 모두 학습 하위 7% |
| [사실·규칙] 판정 | Gemma L0 V·L11 V '정확' → 사전 규칙상 병목 = Action Expert |

## 분석 결과
- [가설] 병목은 Action Expert readout ([사실] 은 규칙 적용 결과까지).
- **"Vision 에는 문제가 없다" 고 단정할 수 없음**: front 절대 위치 약함, front 큐브 < 1 패치, 실물 상태에서 표현 붕괴, VLM 학습 비교 없음.

## 한계 및 미확인
probe MAE (0.08) 가 라벨 바닥 (0.3–0.43) 보다 작은 이유, 실물 wrist 어두움 원인, 편집은 큐브 조각 옮겨 붙이기, d2 하나만.

## 다음 실험으로 이어진 이유
Action Expert 가 roll·위치를 어떻게 쓰는지 → EXP-08.

## 원본 자료
[`sources/vision_probe/`](sources/vision_probe/) (실험설계.md, 실험설계_부록_영상품질.md, f1_결과*.md, f1_results/), 원본 `/home/user/so101_runs/main_k8/d2/vision_probe/` (특징 86 GB 는 제외).
