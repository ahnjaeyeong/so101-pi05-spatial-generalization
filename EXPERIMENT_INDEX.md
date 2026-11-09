# 실험 인덱스

상태 코드: `COMPLETED` · `PARTIAL` (계획 일부만 실행) · `NOT_EVALUATED` (학습은 했으나 평가 없음) · `IN_PROGRESS` · `PAUSED` · `STOPPED` (중단) · `PLANNED` (설계만).
"보고서 ID" 는 [`docs/`](docs/) 의 S1-01 등과 같다.

## 실험 폴더 (16)
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
| [EXP-11](experiments/11_r1_r2_recovery/README.md) | R1/R2 수동 복구 시연 | 10-30 ~ 11-04 | S7-01, S7-02 | pilot12: R1 8 (유효 4) · RC 13 (유효 12) · R2-P 6 (미사용); 연습 R1 12 | — | PARTIAL (11-02 IN_PROGRESS → 11-05) | 학습 유효 16편 (R1 4 · RC 12) QA 완료 → EXP-13; 원래 계획 R1 16 · R2 32 본 수집은 안 함 |
| [EXP-12](experiments/12_hil/README.md) | HIL (정책 실행 중 교정) | 11-02 ~ | S7-03 | 실물 0 | — | IN_PROGRESS (11-02 PLANNED → 11-05) | LeRobot 0.6.2 dagger + adapter 구현; **가짜 장치만** 179/179 (v2) · 205/205 (UI); 실물 안전 검증·수집 0 |
| [EXP-13](experiments/13_recovery_ft/README.md) | d2 + R1 4 · R2 12 교정 시연 FT (rft01) | 11-04 | — | d2 256 + R1 4 + R2(RC) 12 = 272 | d2 020000 → expert-only 1k (250/500/750/1000) | 학습 COMPLETED · 오프라인 COMPLETED · 실물 → EXP-14 | [재추론] T4 G exec 목표 쪽 4.1→33.5 % (2판); AHEAD 잘못된 닫힘 변화 없음; T2 reverse +5.8 %p |
| [EXP-14](experiments/14_rft01_real_pilot/README.md) | rft01 vs d2 020000 실물 파일럿 | 11-05 | — | 실물 16 판 (K 8 · 파일럿 U 8) | FT rft01 001000 / BL d2 020000 | COMPLETED (결론 미결정) | [사람] FT 4/8 · BL 5/8; Known 3/4 vs 2/4, Unknown 1/4 vs 3/4 — **Unknown 은 시작 그리퍼 (FT 닫힘 / BL 열림) · 모델 순서 교란**; K3 FT 2/2 vs BL 0/2 (조건당 1 회) |
| [EXP-15](experiments/15_sg50_sgft01/README.md) | SG50 수집 (S0 시작 · 손목 안내 화면) + sgft01 FT · 오프라인 | 11-05 ~ 11-07 | — | sg50_pilot3 40 (예비 1·2 는 학습 안 씀) | d2 020000 → expert-only 10k (2500/5000/7500/10000) | 수집 PARTIAL (본 수집 안 함) · 학습 COMPLETED · 오프라인 COMPLETED · 실물 → EXP-16 | [in-sample] 앞 10 스텝 오차 10.37→2.19; [반사실] front→pan 이득 0.93, 손목 앞뒤→wflex +2.0 (사람 +18.6) · 크기→lift +0.2 (사람 −42.7), 프레임 밖이어도 닫기 유지; d2 판 오차 2.24→9.49 |
| [EXP-16](experiments/16_sgft01_real_eval/README.md) | sgft01 010000 실물 평가 | 11-09 | — | 실물 8 판 (K 5 · U 3, HU3 미시험 · K8 2 회) | sgft01 010000 (기준선 없음) | COMPLETED | [사람] 2/8 (K 2/5 · U 0/3); 실패 4 판 = 손목 큐브 아래쪽 (그리퍼가 앞 · 위) 인 채 닫기 반복, U7 첫 pan 반대, K2 옮기다 놓침; 안전 정지 0 |

## 학습 실행 (13)
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
| rft01_d2rc16_W5_1k_s2001 | EXP-13 | 완료 (오프라인 평가 · 실물 파일럿 EXP-14) | [configs/training/rft01_d2rc16_W5_1k_s2001](configs/training/rft01_d2rc16_W5_1k_s2001/) |
| sgft01_p3_10k_s2001 | EXP-15 | 완료 (오프라인 평가 · 실물 EXP-16) | [configs/training/sgft01_p3_10k_s2001](configs/training/sgft01_p3_10k_s2001/) |
전체 표: [configs/training/RUNS.csv](configs/training/RUNS.csv) · 체크포인트 32개 경로·SHA-256: [configs/checkpoints/CHECKPOINTS.csv](configs/checkpoints/CHECKPOINTS.csv)

## 계획만 있는 실험
Held-out H 녹화 (32편) · A2 평가 / A2r / A0′ / A3 · 재학습 정책 로봇 평가 (정책당 16회) · 필터 A/B 남은 12판 · R1/R2 본 수집 · SG50 본 수집 (48 편 계획) · d2+R2 단독 FT · rft01 반복 실물 평가 (그리퍼 시작 통제 · 모델 교대) · HIL 실물 안전 확인·파일럿 · d1/d3 (T2 녹화 필요) · VLM 학습 비교 — [docs/06](docs/06_HIL_및_향후실험.md) 6절.
