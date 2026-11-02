# 실험 인덱스

상태 코드: `COMPLETED` · `PARTIAL` (계획 일부만 실행) · `NOT_EVALUATED` (학습은 했으나 평가 없음) · `IN_PROGRESS` · `PAUSED` · `STOPPED` (중단) · `PLANNED` (설계만).
"보고서 ID" 는 [`docs/`](docs/) 의 S1-01 등과 같다.

## 실험 폴더 (12)
| ID | 이름 | 기간 | 보고서 ID | 데이터 | 모델 / 체크포인트 | 상태 | 핵심 결과 (상세는 폴더) |
|---|---|---|---|---|---|---|---|
| [EXP-01](experiments/01_paper_cube/README.md) | 종이 큐브 초기 (practice_10/50, E0_J_0) | 10-02 ~ 10-13 | S1-01~06, S1-09 | practice_10 (10), practice_50 (50) | full FT 2k / 15k | COMPLETED | 실물 1/7; 3/3 (분석 판정), 3/8 (사람) |
| [EXP-02](experiments/02_cubemark_expert_only/README.md) | cubemark + 첫 expert-only | 10-12 ~ 10-13 | S1-07, S1-08 | cubemark_v1 (50) | full FT 15k / expert bs8 3k | COMPLETED (15k 실물 NOT_EVALUATED) | 3k 0/8 |
| [EXP-03](experiments/03_redbox_384_20k/README.md) | redbox 384편 + 20k | 10-13 ~ 10-18 | S2-01, S2-02, S2-12, S2-15 | redbox_all (384) | expert bs32 20k (pi05_base) | COMPLETED | loss 0.154→0.024 |
| [EXP-04](experiments/04_rtc_filter_space_eval/README.md) | RTC·필터·공간 평가 (20k) | 10-19 ~ 10-20 | S2-03~11, S2-13, S2-14 | — | redbox 020000 | COMPLETED (공간 40/60) | A/B 필터 무효과 (p=1.0); 공간 첫 22/40·최종 30/40; 손목 회전 크기가 실패와 관련 |
| [EXP-05](experiments/05_redbox_30k/README.md) | redbox 20k→30k 추가 학습 | 10-20 ~ 10-22 | S3-01, S3-02 | redbox_all (384) | redbox 030000 (resume, LR 2.5e-6) | COMPLETED (40/60) | 첫 22→12/40 (p=0.041), 최종 30→29/40; 시작 자세 다름 |
| [EXP-06](experiments/06_d2_256/README.md) | K1–K8 재배치, d2 256 (+d4) | 10-22 ~ 10-27 | S4-01~08 | d2 (256), d4 (192) | d2 020000 (pi05_base 새 학습), d4 010000 | d2 COMPLETED (10-26 판정 없음) · d4 STOPPED/NOT_EVALUATED · d1/d3 PLANNED | 새 위치 K 끌림 0.3, G_tt 0.10 |
| [EXP-07](experiments/07_vision_probe/README.md) | Vision/VLM Feature Probe | 10-26 ~ 10-27 | S5-01~04 | d2 (held-out fold) | d2 020000 | COMPLETED (오프라인) | wrist 특징 MAE 0.079 cm vs 정책 G_tt 0.10 |
| [EXP-08](experiments/08_action_bottleneck/README.md) | Action Expert · Wrist Roll | 10-27 | S6-01 | d2 | d2 020000 | COMPLETED (오프라인) | w_rot ≈ 0, roll 토큰 가림 무효과 |
| [EXP-09](experiments/09_sampling_ablation/README.md) | Sampling Ablation + 커버리지 감사 | 10-27 ~ 10-29 | S6-02, S6-03 | d2 (가중) | A0/A1/A2 004000 | PAUSED | A1−A0 효과 없음; A2 미평가, A2r·A0′ 미실행 |
| [EXP-10](experiments/10_pan_diagnostic/README.md) | Shoulder Pan 초기 접근·반전 | 10-29 ~ 11-02 | S6-04~11 | 실물 20판 | d2 020000 | COMPLETED (필터 A/B PARTIAL) | 실물 P 9/20; 왼쪽 첫 chunk 정지; 손목 놓침 후 방향 지속 = 모델 raw |
| [EXP-11](experiments/11_r1_r2_recovery/README.md) | R1/R2 수동 복구 시연 | 10-30 ~ | S7-01, S7-02 | 본 0, 연습 R1 12 | — | IN_PROGRESS | 도구 완료, 본 수집 0 |
| [EXP-12](experiments/12_hil/README.md) | HIL (정책 실행 중 교정) 검토 | 11-02 ~ | S7-03 | — | — | PLANNED | 2차 방안으로 제안만 |

## 학습 실행 (11)
| run_id | 실험 | 상태 | 설정 |
|---|---|---|---|
| practice_10_pi05_2k | EXP-01 | 완료 | [configs/training/practice_10_pi05_2k](configs/training/practice_10_pi05_2k/) |
| practice_50_pi05_15k | EXP-01 | 완료 | [configs/training/practice_50_pi05_15k](configs/training/practice_50_pi05_15k/) |
| cubemark_pi05_15k | EXP-02 | 완료 | [configs/training/cubemark_pi05_15k](configs/training/cubemark_pi05_15k/) |
| cubemark_expert_bs8_3k | EXP-02 | 완료 | [configs/training/cubemark_expert_bs8_3k](configs/training/cubemark_expert_bs8_3k/) |
| redbox_expert_bs32_20k | EXP-03 | 완료 | [configs/training/redbox_expert_bs32_20k](configs/training/redbox_expert_bs32_20k/) |
| redbox_expert_bs32_resume30k | EXP-05 | 완료 | [configs/training/redbox_expert_bs32_resume30k](configs/training/redbox_expert_bs32_resume30k/) |
| d2_expert_bs32_20k | EXP-06 | 완료 | [configs/training/d2_expert_bs32_20k](configs/training/d2_expert_bs32_20k/) |
| d4_expert_bs32_20k_stopped10k | EXP-06 | 10,003 step 에서 정지 | [configs/training/d4_expert_bs32_20k_stopped10k](configs/training/d4_expert_bs32_20k_stopped10k/) |
| sampling_A0_s2001 | EXP-09 | 완료 | [configs/training/sampling_A0_s2001](configs/training/sampling_A0_s2001/) |
| sampling_A1_s2001 | EXP-09 | 완료 | [configs/training/sampling_A1_s2001](configs/training/sampling_A1_s2001/) |
| sampling_A2_s2001 | EXP-09 | 완료 (평가 안 함) | [configs/training/sampling_A2_s2001](configs/training/sampling_A2_s2001/) |
전체 표: [configs/training/RUNS.csv](configs/training/RUNS.csv) · 체크포인트 28개 경로·SHA-256: [configs/checkpoints/CHECKPOINTS.csv](configs/checkpoints/CHECKPOINTS.csv)

## 계획만 있는 실험
Held-out H 녹화 (32편) · A2 평가 / A2r / A0′ / A3 · 재학습 정책 로봇 평가 (정책당 16회) · 필터 A/B 남은 12판 · R1/R2 본 수집·재학습 · HIL 전환 장치 · d1/d3 (T2 녹화 필요) · VLM 학습 비교 — [docs/06](docs/06_HIL_및_향후실험.md) 6절.
