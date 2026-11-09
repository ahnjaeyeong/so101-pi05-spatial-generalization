# 오프라인 평가 요약 (실물 성공률 아님)

| 실험 | 모델 | 데이터 종류 | 핵심 지표 |
|---|---|---|---|
| [EXP-01](../../experiments/01_paper_cube/README.md) practice_10 | 2k | [in-sample] | 팔 오차 2.28–2.40°, chunk 경계 점프 ≤42.7° |
| [EXP-04](../../experiments/04_rtc_filter_space_eval/README.md) 체크포인트 비교 | redbox 5k–20k, cubemark | [in-sample] | 파지 자세 오차 6.47→5.43°, 잡음 0.92–1.09°; cubemark 15k 1.76° |
| EXP-04 P0 재생 | redbox 20k | [재생] | RTC h20 EXP s5 + EMA → 경계 점프 0, 잡음 0.45° |
| EXP-04 파지 직전 분석 | redbox 20k | [in-sample] + 실물 80판 기록 | 정렬 각도 성공 2.0° vs 실패 15.3°; 위치·정렬 정상 사람 87% vs 정책 32% |
| [EXP-06](../../experiments/06_d2_256/README.md) 파지 편향 | d2 5k–20k | [in-sample]·[합성]·[반사실] | K 끌림 0.21–0.34, 중앙 끌림 보정 후 0.08, front 교체 계수 0.59–0.67, G_tt 0.10 |
| [EXP-07](../../experiments/07_vision_probe/README.md) Vision Probe | d2 (= base vision) | [held-out fold], 편집, 실물 프레임 | SigLIP L26 MAE 0.079 cm (R² 0.97); g_rep 0.57–0.73; 실물 범위 밖 R² ≤0.02 |
| [EXP-08](../../experiments/08_action_bottleneck/README.md) Action Expert | d2 020000 | [반사실]·[in-sample] | G_tt 0.30/0.20/0.10, w_rot −0.01/−0.09/−0.18, KR 무효과, hidden roll R² ≈1.0 |
| [EXP-09](../../experiments/09_sampling_ablation/README.md) 재표집 | d2, A0, A1 (A2 미평가) | [in-sample]·[합성] | A1−A0 새 위치 −0.256° [−0.648, +0.133]; G_rr −0.097 |
| EXP-09 커버리지 감사 | — | [in-sample] | −2 s ≥1.5 cm 오차 0편; 보정 오른쪽 31 : 왼쪽 6; 정책 pan t90 2.2–14.6 s vs 사람 0.8 s |
| [EXP-10](../../experiments/10_pan_diagnostic/README.md) Pan 진단 | d2 020000 | [재구성] | 왼쪽 첫 chunk 정지 53–80%; T4 목표 쪽 U 7.7% / G 4.3%; state pan ±30° 에도 방향 유지 13/14 |
| [EXP-15](../../experiments/15_sg50_sgft01/README.md) SG50 FT | d2 020000, sgft01 2500–10000 | [in-sample]·[반사실] (B = 같은 작업자 안 쓴 판, held-out 아님) | 앞 10 스텝 오차 A 10.37→2.19 · B 10.62→3.22 · d2 판 2.24→9.49; front→pan 이득 0.59→0.93; 손목 앞뒤→wflex +27.5→+2.0 (사람 +18.6), 크기→lift −12.2→+0.2 (사람 −42.7); 프레임 밖 닫기 49/42/78% |
| [EXP-17](../../experiments/17_grasp_bias_diag/README.md) 집기 직전 편향 | sgft01 010000 (EXP-16 실물 관측) | [재구성]·[반사실]·[in-sample] (사람 예비3) | 그리퍼 열림 장면 큐브만 중심: 바깥 +0.96 cm (사람 +0.13); 교차: 큐브 모습 −0.55 · 배경 −0.40, 높이 −0.25, 기세 −0.03, 서보 속도 무관; 손목 기울기 v 27 % · u 10 %; 관절값 k 0.81 (사람 0.94); 흔들림 크기 영상 변화 → 명령 0.24–0.40° |

학습 loss (train loss 만, 검증 loss 없음): [`analysis/loss/`](../../analysis/loss/), 그림 [`analysis/figures/loss_curves.png`](../../analysis/figures/loss_curves.png).
상세: [`docs/05_오프라인_실험결과.md`](../../docs/05_오프라인_실험결과.md).
