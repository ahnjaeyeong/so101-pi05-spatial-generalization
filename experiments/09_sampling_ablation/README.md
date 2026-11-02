# EXP-09 · Sampling Ablation (A0 / A1 / A2 / A2r / A0′) 및 데이터 커버리지 감사

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-09** (보고서 ID S6-02, S6-03) |
| 날짜 | 설계 2026-10-27, 학습 10-27 22:29 ~ 10-29 13:58, 감사 10-29 |
| 상태 | `PAUSED` (10-29 11:25 사용자 지시로 큐 일시정지) |

## 실행별 상태
| run | 가중 | 학습 | 오프라인 평가 | 로봇 평가 |
|---|---|---|---|---|
| A0_s2001 | 균일 | ✅ 10-27 22:29 → 10-28 09:46 | ✅ | `NOT_EVALUATED` |
| A1_s2001 | 접근·정렬 구간 ×3 | ✅ 10-28 13:20 → 10-29 00:34 | ✅ | `NOT_EVALUATED` |
| A2_s2001 | Random ×2 × roll×tan 희소칸 (최대 16) | ✅ 10-29 02:28 → 13:58 | ❌ `NOT_EVALUATED` (eval_hook 미실행) | `NOT_EVALUATED` |
| A2r_s2001 | Random ×2 만 | ❌ `PLANNED` (스크립트만) | — | — |
| A0′ (A0_s2002) | 균일, seed 2002 | ❌ `PLANNED` | — | — |
| A3 / A3c12 | A1×A2 | ❌ 보류 | — | — |

## 목적·가설
[가설] d2 Expert 의 roll 조건부 부족과 초기 접근 오차가 학습 표본 비율·희소성 때문인가. 같은 데이터·step·LR 에서 표본 비율만 바꿔 검증 (d4 개선 실험 아님).

## 데이터셋·모델·학습
- d2 256편 그대로, 가중 sampler (`train_weighted.py`, LeRobot 수정 없음).
- 시작 = d2 020000, **새 fine-tune** (resume 아님), LR peak 1e-5 (실제 최대 9.954e-6), warmup 200, cosine → 2.5e-6, batch 32, 4,000 step (≈1.04 epoch), seed 2001, Vision freeze 예, Expert-only 예.
- loss: 세 run 모두 0.019 (차이 구분 안 됨).
- 설정: [`configs/training/sampling_A0_s2001/`](../../configs/training/sampling_A0_s2001/) 등.

## 평가 방법 (오프라인)
O1 초기 접근 (학습 판 pan 오차, 합성 front 격자 새 위치 30점, K 끌림 aK), O2 roll 조건부 (w_rot, G_tt, G_rr), O3 칸별 loss. bootstrap 95% CI. **진짜 held-out (H) 없음 → 새 위치는 합성 영상 대리값.**

## 결과 (004000, 오프라인)
| 비교 | 새 위치 pan 오차 차 | aK 차 | w_rot 차 | G_rr 1.0 s 차 | 판정 |
|---|---|---|---|---|---|
| A1 − A0 | −0.256° [−0.648, +0.133] | −0.033 [−0.050, −0.016] | −0.029 | −0.097 [−0.175, −0.017] | O1·O2 개선 없음, G_rr '악화' |
| A0 − d2 (+4k step) | +0.253° [+0.007, +0.532] | +0.007 | −0.027 | −0.058 | 없음 |
- [사실] 실물 정책 프레임 34% 는 빈 칸·표 밖 → 재표집으로 만들 수 없음.

## 데이터 커버리지 감사 (10-29, CPU)
- [사실] 사람 256편 모두 첫 닫힘 성공 (재파지 0), 시작 pan SD 2.5°, pan 첫 움직임 98%·t90 0.8 s; 파지 2 s 전 ≥1.5 cm 오차 0편; 1 cm 넘는 보정 오른쪽 31 : 왼쪽 6.
- [사실] 정책 (10-26 5판) pan t90 2.2–14.6 s.
- [사실] 이전 fk_fit 접선 오차는 bearing 편향 (SD 2.07 cm) → 극좌표 TCP 0.59 cm.
- [가설] 부족한 것은 '큰 오차를 양쪽으로 고친 시연'. [계획] P0 기준선 → P1 회복 시연 → P3 시작 pan → P4 위치 밀도.

## 한계 및 미확인
A2·A2r·A0′ 미완 → 최종 판정 불가, seed 변동 δ 없음, 희소칸 라벨 편향 (roll 과 r −0.82), 로봇 평가 없음.

## 재개 절차
`/home/user/so101_runs/main_k8/d2/pan_inference_diagnostic/01_training_pause_status.md` 4절 (자동 재개 금지, 사용자 지시 필요).

## 다음 실험으로 이어진 이유
10-29 사용자 작업지시로 Pan 진단 우선 → EXP-10.

## 원본 자료
[`sources/sampling_ablation/`](sources/sampling_ablation/), [`sources/data_coverage_audit/`](sources/data_coverage_audit/), 원본 `/home/user/so101_runs/main_k8/d2/{sampling_ablation,data_coverage_audit}/`.
