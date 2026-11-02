# EXP-03 · redbox 384편 데이터셋 (K1–K4, 옛 카메라) 및 20k 학습

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-03** (보고서 ID S2-01, S2-02, S2-12, S2-15) |
| 날짜 | 수집 2026-10-13 ~ 10-15, 학습 10-15 17:52 ~ 10-18 02:31 |
| 상태 | `COMPLETED` (평가는 EXP-04) |

## 목적
- [가설, 메모리] 고정 위치(Known)와 자유 배치(Random)를 같은 수로 모아 위치 일반화 비교, 그룹당 유효 64편.

## 데이터셋 — redbox_all (`oxr/so101_redbox_all`), 2.5 cm 큐브
| 그룹 | 편 | 프레임 | 구성 |
|---|---|---|---|
| T1-K | 64 | 27,984 | 빨강 1, K1–K4 각 16 |
| T1-R | 64 | 27,658 | 빨강 1, 손으로 자유 배치 |
| T2-K | 64 | 45,261 | 빨강 2/3/4 = 24/24/16 |
| T2-R | 64 | 46,401 | 같은 구성, 자유 |
| T3-K | 64 | 18,985 | 빨강 1 + 방해 1–3 |
| T3-R | 64 | 22,241 | 빨강 1 + 방해 2–6 |
| **합** | **384** (Known 192 + Random 192) | **188,530** | 과제 문장 2개 |
- K 좌표 (cm): K1 (−20.2, 31.5) · K2 (−16.2, 21.3) · K3 (−7.8, 12.7, 로봇 정면) · K4 (−15.4, 2.6) — [`configs/layouts/redbox_layouts.yaml`](../../configs/layouts/redbox_layouts.yaml).
- [사실] 큐브 회전 **통제 안 함**, 사후 측정 +178 / −192, 0–15° 141 · 15–30° 122 · 30–45° 107.
- [사실] QA 자동 64/64 ×6, 육안 칸 비어 있음, held-out 분리 없음.

## 모델·학습 — `redbox_expert_bs32_20k`
| 항목 | 값 |
|---|---|
| 시작 | `lerobot/pi05_base` |
| Vision freeze / Expert-only | **예 / 예** (693M 학습) |
| batch / steps | 32 / 20,000 (3.39 epoch) |
| LR | 2.5e-5 → 2.5e-6 cosine (실효 warmup 666 / decay 20,000; train_config 에는 설정값 1000/30000 저장) |
| loss | 0.154 → 0.024 (최저 0.022 @18,100); 5k 0.030, 10k 0.026, 15k 0.024 |
| 체크포인트 | 005000 · 010000 · 015000 · 020000 (+ EXP-05 의 025000 · 030000) |
설정: [`configs/training/redbox_expert_bs32_20k/`](../../configs/training/redbox_expert_bs32_20k/), loss: [`analysis/loss/redbox_expert_bs32_20k_loss.csv`](../../analysis/loss/redbox_expert_bs32_20k_loss.csv).

## 학습 데이터 분석 (오프라인, 학습 데이터 위)
- [사실] 손목 회전 census (380 첫 파지): −방향 70%, 45° 초과 30% (그룹별 13–53%, p<0.001); 사람 큐브 면 정렬 15° 안 91%.
- [사실] 공개 SO101 sponge 데이터 대비 \|roll 변화\| 30.8° vs 6.3°, wrist_flex 67.5° vs 26.9°.

## 추론 설정·평가
→ [EXP-04](../04_rtc_filter_space_eval/README.md).

## 한계 및 미확인
로봇 base 미측정 (추정 (−33.5, 11.6)), 큐브 yaw·조명 미통제, T2 계획 184 vs 측정 182 등 개수 차이.

## 다음 실험으로 이어진 이유
첫 실물에서 진동과 파지 실패 → EXP-04.

## 원본 자료
[`sources/`](sources/) (세션 notes·qa_report·layout, train 스크립트, census, reference 비교), 원본 `/home/user/so101_runs/main/redbox_*`, `/home/user/so101_runs/main/redbox_all/`.
