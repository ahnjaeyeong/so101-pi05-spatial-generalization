# EXP-13 · d2 + R1/R2 교정 시연 16편 Fine-tuning (rft01)

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-13** (run `rft01_d2rc16_W5_1k_s2001`) |
| 날짜 | 2026-11-04 |
| 상태 | 학습 `COMPLETED` · 오프라인 재추론 평가 `COMPLETED` · 실물 파일럿 `COMPLETED` → [EXP-14](../14_rft01_real_pilot/README.md) (16 판, 모델 간 결론 미결정) |
| 상태 이력 | 11-04 실물 `NOT_EVALUATED` → 11-05 실물 파일럿 16 판 (EXP-14) |
| 표기 | [사실] 파일 측정값 · [가설] 분석 해석 · [계획] 설계만 · 데이터 [in-sample] · 오프라인 값은 모두 재추론 (실물 성공률 아님) |

상세 보고·전체 표: [`sources/recovery_ft/README.md`](sources/recovery_ft/README.md). 이 문서는 요약.

## 목적
d2 020000 에 사람 교정 시연 16편 (R1 4 · R2 12) 을 섞어 짧게 추가 학습했을 때, d2 의 실패 상태 (Pan 지나침 후 반대쪽 지속, 파지 직전 잘못된 닫힘) 에서 예측 action 이 바뀌는지, 정상 접근·파지가 유지되는지 오프라인으로 확인.

## 검증 가설
- [가설] H1 Pan 복구: 손목 놓침 · 지나침 상태에서 목표 쪽 pan 예측이 늘어난다.
- [가설] H2 pre-grasp 복구: AHEAD 등에서 잘못된 위치 닫힘이 줄고, 닫힌 상태에서 열기 예측이 는다.
- [가설] H3 정상 유지: d2 정상 접근 · 파지 상태의 예측이 크게 변하지 않는다.
- 판정 규칙 (학습 전 작업 지시 §9): R1·R2 모두 개선 / R1 만 / R2 만 / 정상 악화 / 효과 없음 → 각각 다음 단계 지정.

## 데이터셋
| 이름 (repo_id) | 경로 | 편 / 프레임 | 구성 |
|---|---|---|---|
| oxr/so101_k8_d2_rc16 (병합 사본, 277편 중 272편 사용) | `/home/user/so101_runs/main_k8/d2/recovery_ft/dataset` | 272 / 129,470 | d2 0–255 (123,342) + R1 `r12_pilot12_r1` ep 4–7 (1,760) + R2 `r12_pilot12_rc` ep 0–10, 12 (4,368) |

- [사실] 제외: R1 ep 0–3 (수집 기록 excluded), RC ep 11 (QA excluded). R2-P regrasp · r2p/r2o · 연습 시연 미포함. Manifest sha256 `a4ab3c4d1d7acd9f4ac40fbe281a928c623bbdd47bd451d0acee91e65fa3b030` ([manifest](sources/recovery_ft/manifest/training_manifest.csv)).
- [사실] 영상 byte 복사 (재인코딩 없음), stats.json = d2 (020000 normalizer 와 차이 0). lerobot `aggregate_datasets` 는 d2 의 `meta/episodes/file_index` 때문에 실패 → 자체 병합 (`scripts/r02_build_dataset.py`). 사전 검증 12 항목 PASS.
- held-out 여부: 평가 상태 중 실물 정책 상태 (q02 · R2 진단) 는 학습에 없음. 시연 상태는 [in-sample] 또는 같은 세션 제외 편 (held-out 아님).

## 모델·학습
| 항목 | 값 |
|---|---|
| 시작 체크포인트 | d2 020000 (`6c46dee7…a364886`), 신규 FT (resume 아님) |
| Vision freeze / Expert-only | true / true (학습 693,422,112 파라미터) |
| batch / steps (epoch) | 32 / 1,000 (32,000 표본 ≈ 0.25 epoch) |
| LR | peak 1e-5 → 2.5e-6, warmup 50, cosine decay 1,000 |
| 샘플링 | 교정 frame 가중 W=5 → 실제 d2 79.9 % · R1 5.9 % · R2 14.2 %, loss 가중 없음 |
| seed | 2001 |
| 설정 파일 | [`configs/training/rft01_d2rc16_W5_1k_s2001/`](../../configs/training/rft01_d2rc16_W5_1k_s2001/) |
| 체크포인트 | 250 / 500 / 750 / 1000 — 경로·SHA-256 [`sources/recovery_ft/logs/post/p01_ckpt_sha256.json`](sources/recovery_ft/logs/post/p01_ckpt_sha256.json), 상세 보고 1.4절 (로컬 `configs/checkpoints/` 에도 4행 추가했으나 그 폴더는 .gitignore 대상) |
| loss | 0.024 (step 50) → 0.022 (step 1000), 최소 0.021 (750) — [로그](sources/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001.log) |

[사실] 2026-11-04 15:05 → 18:00 rc=0, NaN 없음, GPU 21.0 GB, 실제 표본 index = dry-run 예측과 동일, 원본 hash 변화 없음.

## 추론 설정 (오프라인 재추론)
기존 vd 엔진: denoise 5 step, RTC guided EXP (guidance 10, horizon 20), noise bank seed 2026. G = 저장 RTC prefix 사용, U = prefix 없음. Baseline 은 020000 의 기존 저장 배열; 같은 코드 재현 차이 평균 0.05°, 최대 0.52°, 방향 일치 99.5 %.

## 평가 방법
오프라인 재추론만. 판정 = 분석 지표 (`scripts/e02_metrics.py`). R1 q02 223 상태 × 32 seed, R2 실물 진단 168 × 16, d2 사람 상태 96 × 16, 신규 시연 상태 50 × 16.

## 평가 결과
| 조건 | n | 020000 | 500 | 1000 |
|---|---|---|---|---|
| T4 손목 놓침 · front 보임, G exec 목표 쪽 % | 2판 39상태 | 4.1 | 27.3 | 33.5 |
| T4, G cum30 반대쪽 % | 2판 39상태 | 86.9 | 51.1 | 43.8 |
| T4, U exec 목표 쪽 % | 2판 39상태 | 5.7 | 12.4 | 14.4 |
| R2 AHEAD T0, G 잘못된 위치 닫힘 p_close30 | 7판 | 0.536 | 0.527 | 0.536 |
| 정상 파지 T2, G p_close30 | 10판 | 0.931 | 0.819 | 0.900 |
| d2 사람 H_preclose p_close30 | 32 상태 | 0.969 | 0.951 | 0.953 |
| T2 거의 정렬, G reverse % | 13판 52상태 | 14.4 | 17.9 | 20.2 |
| [in-sample] RC-F1 시작 조기 닫힘 p_close30 | 4판 | 0.86 | 0.11 | 0.14 |

(T4 기준값: 문서의 7.7 % / 4.3 % 는 64 seed, 이 표는 32 seed.)

## 분석 결과
- [사실] H1: 실물 정책 상태 T4 · T3 에서 목표 쪽 증가 · 반대쪽 감소, A0 · B1 두 판 모두 같은 방향. 1000 에서도 cum30 반대쪽이 목표 쪽보다 많음.
- [사실] H2: 학습 미사용 R2 진단 상태에서 AHEAD 잘못된 위치 닫힘 변화 없음; 관절 변화 (elbow +1…2°, lift −0.5…−1.4°) 는 정상 파지 상태에도 같은 모양; BELOW T2 닫힘 0.641 → 0.407. 개선 징후는 [in-sample] 시연 상태에서만.
- [사실] H3: T1 접근 · 정상 닫힘 · 재개방은 대체로 유지. T2 reverse 증가 (+5.8 %p, CI +2.7…+10.3), d2 사람 상태 action 차이 +0.19…0.24°, H_preclose pan gain 0.35 → 0.04 (6 상태).
- [가설] §9 분류는 "R1 만 개선됨" 에 가장 가깝다.

## 한계 및 미확인
- R1 근거 상태는 실물 2판. seed 는 독립 시행 아님. 단일 run · seed · 혼합 비율. R1 · R2 의 개별 기여 미분리.
- 오프라인 재추론 — 실물 성공률 미확인. 교정 frame 31 % 는 한 번도 표본되지 않음.

## 다음 실험으로 이어진 이유
- [계획] (§9 "R1 만 개선됨") R2 시연 시작 상태와 AHEAD/BELOW 실물 진단 상태의 분포 비교 → d2 + R2 단독 FT (같은 시작 · steps · LR · seed) 검토.
- [계획] 정상 능력 감시 지표: T2 reverse · H_preclose pan gain · 사람 상태 action 차이. 실물 비교 후보는 500 · 1000.
- [계획] 실물 평가 · R1/R2 추가 촬영은 사용자 지시 후.
- (11-05) 실물 파일럿 실행 → [EXP-14](../14_rft01_real_pilot/README.md): FT (001000) 4/8 · BL (020000) 5/8 [사람 P/F], Known 3/4 vs 2/4, Unknown 1/4 vs 3/4 — Unknown 구간은 시작 그리퍼 상태가 모델과 겹친 교란으로 비교 무효. 16 판 모두 Wrist 놓침 0 → 실물 R1 복구는 검증 안 됨. 오프라인 R1 복구 신호 개선과 실물 복구 성공은 별개.

## 원본 자료
- 복사본: `sources/recovery_ft/` (scripts, manifest, 검증·평가 표, 작은 로그; tools/sync_sources.py MAPPINGS)
- 원본 경로: `/home/user/so101_runs/main_k8/d2/recovery_ft` (dataset · checkpoints · eval/raw · weights 는 Git 제외)
- 시연 원본 세션 `main_k8/r12_pilot12_r1`, `main_k8/r12_pilot12_rc` 는 11-05 에 EXP-11 `sources/sessions/` 로 매핑함 ([EXP-11](../11_r1_r2_recovery/README.md)).
