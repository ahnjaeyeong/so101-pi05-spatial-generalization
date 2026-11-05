# recovery_ft — d2 020000 + R1 4 + R2(RC) 12 교정 시연 Fine-tuning (rft01)

작성 2026-11-04. 표기: **[사실]** 파일·로그에서 확인한 값 · **[재추론]** 저장 관측을 체크포인트에 다시 넣은 오프라인 출력 (실물 성공률 아님, noise seed 는 실물 반복 아님) · **[in-sample]** 학습에 쓴 시연의 상태 · **[권고]** 작업 지시 §9 규칙에 따른 다음 단계 (작업 지시가 요구한 항목).

실물 SO-101 연결 · rollout · 텔레오퍼레이션 · 데이터 수집 없음. 일시정지된 Sampling Ablation 큐는 건드리지 않음 (`logs/00_start_state.txt`).

---

## 1. 학습 기록

### 1.1 데이터 (272 편 · 129,470 frame) [사실]

| 원천 | 편 | frame | 사용 episode | 제외 |
|---|---|---|---|---|
| d2 (`main_k8/d2/dataset`) | 256 | 123,342 | 0–255 전부 | — |
| R1 `main_k8/r12_pilot12_r1` | 4 | 1,760 | ep 4, 5, 6, 7 (R1-FOLD-OVER) | ep 0–3 (attempts.jsonl excluded) |
| R2 `main_k8/r12_pilot12_rc` | 12 | 4,368 | ep 0–10, 12 | ep 11 (QA excluded) |

- RC 시나리오: F1 (열린 그리퍼 시작) ep 1, 5, 6, 10 · F2 (닫힌 시작) ep 0, 4, 7, 12 · F3-L ep 2, 9 · F3-R ep 3, 8.
- 태그 `arm_before_gripper_open` (승인 유지): RC ep 4 (7.8°), ep 8 (17.0°), ep 12 (6.1°).
- R2-P regrasp · r2p/r2o 세션 · 연습 시연 미포함. 파일 존재 여부가 아니라 `scripts/r01_manifest.py` 의 명시 목록 + attempts.jsonl · QA 표 교차 확인으로 선정.
- Manifest `manifest/training_manifest.json` sha256 **`a4ab3c4d1d7acd9f4ac40fbe281a928c623bbdd47bd451d0acee91e65fa3b030`** (csv `985641ff…78d62c`).
- 병합 사본 `dataset/` (repo_id `oxr/so101_k8_d2_rc16`, 277 편): 영상 byte 복사 (재인코딩 없음), stats.json = d2 stats.json (byte 동일). 제외 5 편 (병합 번호 256–259, 275) 은 사본에 남아 있으나 `--dataset.episodes` 목록에 없음 — 학습 중 표본 0 개.
  - lerobot `aggregate_datasets` 는 d2 의 `meta/episodes/file_index` (0–3, 실제 파일 1 개) 때문에 FileNotFoundError → 자체 병합 `scripts/r02_build_dataset.py`.
- 사전 검증 `scripts/r03_validate.py` 12 항목 PASS (`tables/r03_checks.csv`): v3.0 · 30 fps · front/wrist · 관절 순서/단위 · gripper 의미 · task 문자열 · 경계 · timestamp (오차 8.9e-7 s) · 제외 편 부재 · 시작 action/state 차이 (d2 p99 이내) · 112 표본 frame 영상·action chunk 원본 동일 · normalizer = 020000 (차이 0).

### 1.2 설정 · 명령 [사실]

| 항목 | 값 |
|---|---|
| 시작 | d2 `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model` (신규 FT, resume 아님) |
| 시작 model.safetensors sha256 | `6c46dee79b167c48ad24b6af739157dc22636505c4c838815a4bf3656a364886` |
| 정책 | π0.5, Expert-only, vision freeze, bf16, gradient checkpointing, chunk 50, normalization QUANTILES |
| 학습 가능 파라미터 | 693,422,112 / 4,143,404,816 (A0 와 같음), frozen 인데 grad 받은 파라미터 0 |
| batch · steps | 32 · 1,000 |
| LR | peak 1e-5, warmup 50, cosine decay 1,000 → 2.5e-6 (EXP-09 의 200/4000 을 1/4 로) |
| seed | 2001 |
| 저장 | 250 · 500 · 750 · 1000 |
| 샘플링 | `sampling_ablation/train_weighted.py` (수정 없음) 의 frame 가중 sampler 재사용, 교정 frame 가중 W=5 (`weights/weights_rc16_W5.npy`) |
| loss 가중 · 시간 구간 가중 | 없음 |
| 환경 | lerobot 0.6.2 · torch 2.11.0+cu130 · python 3.12 · Jetson Thor (`~/so101-env`) |

명령 (`runs/run_rft01_d2rc16_W5_1k_s2001.sh`, 인자 `runs/rft01_d2rc16_W5_1k_s2001.args` 22 줄; `scripts/make_run.py` 가 생성):

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
export RF_WEIGHTS=$RF/weights/weights_rc16_W5.npy RF_RUN_NAME=rft01_d2rc16_W5_1k_s2001
~/so101-env/bin/python $RF/scripts/train_recovery.py \
  --dataset.repo_id=oxr/so101_k8_d2_rc16 --dataset.root=$RF/dataset --dataset.episodes=[0..255,260..274,276] \
  --policy.path=<d2 020000>/pretrained_model --policy.push_to_hub=false --policy.dtype=bfloat16 \
  --policy.train_expert_only=true --policy.freeze_vision_encoder=true --policy.gradient_checkpointing=true \
  --policy.optimizer_lr=1e-5 --policy.scheduler_warmup_steps=50 --policy.scheduler_decay_steps=1000 \
  --policy.scheduler_decay_lr=2.5e-6 --output_dir=$RF/runs/rft01_d2rc16_W5_1k_s2001 \
  --job_name=rft01_d2rc16_W5_1k_s2001 --batch_size=32 --steps=1000 --log_freq=50 --save_freq=250 \
  --num_workers=4 --seed=2001 --wandb.enable=false
```
(`$RF` = `~/so101_runs/main_k8/d2/recovery_ft`. `train_recovery.py` 는 실행 전 다른 학습/GPU 프로세스 부재, manifest·데이터 hash, 출력 경로 미존재, stats 동일 여부를 확인하고 lerobot_train 을 그대로 호출.)

코드: recovery_ft 는 git 저장소가 아님 → 스크립트 sha256 `logs/post/p03_code_sha256.txt`. 기록 저장소 커밋은 §4.

### 1.3 실행 결과 [사실]

- 2026-11-04 15:05:00 시작 → 18:00:43 종료 rc=0 (1,000 step, 약 10.3 s/step). `runs/rft01_d2rc16_W5_1k_s2001.DONE`.
- 사후 검사 (`run_wrapper.sh`): checkpoint 4 개 + last→001000, NaN 없음, OOM/Traceback 없음, d2 원본 · 병합 사본 hash 변화 없음.
- GPU 학습 프로세스 최대 21.0 GB (`runs/*.mem.log`).
- 실제 표본 32,000 개 index = dry-run 예측과 완전 동일 → 실제 비중 d2 79.9 % · R1 5.9 % · R2 14.2 %, 교정 frame 당 평균 노출 ≈ 1.04 회, 교정 frame 의 69 % 가 1 회 이상 노출 (`tables/r05_sampler_summary.json`).
- normalizer · unnormalizer: 4 checkpoint 모두 020000 과 차이 0.0.

loss (log_freq 50, 배치 평균):

| step | 50 | 100 | 250 | 500 | 750 | 1000 |
|---|---|---|---|---|---|---|
| loss | 0.024 | 0.023 | 0.024 | 0.023 | 0.021 | 0.022 |
| lr | 5.2e-6 | 9.9e-6 | 9.1e-6 | 6.5e-6 | 3.8e-6 | 2.5e-6 |

grad norm 0.245–0.279. 참고: dry-run 에서 020000 의 유형별 loss (각 8 표본) d2 0.018 · R1 0.071 · RC-F1/F2 0.053 · RC-F3 0.017.

### 1.4 checkpoint [사실]

`runs/rft01_d2rc16_W5_1k_s2001/checkpoints/{000250,000500,000750,001000}/pretrained_model` (전체 44 GB, git 제외).

| ckpt | model.safetensors sha256 |
|---|---|
| 000250 | `181b82db06a69f06e988ebd9178d07f2e712a4febc04b99e78ceb072715553d9` |
| 000500 | `c0e3c88b135eb43354909eea3d0b30415d16106e108c0ad55744c62614c0cbbd` |
| 000750 | `a2dcc02320c6de1f2173bde945ea1f7c03bb84355c78bb6e331ea786ba66b3ae` |
| 001000 | `620c45988a35b77e76b5c0869c560697d9d095143aceee33b98946a7db712af9` |

---

## 2. 오프라인 평가 [재추론]

### 2.1 방법

- 엔진: 기존 vd `v02_engine.Engine` (num_inference_steps 5, RTC guided EXP, max_guidance_weight 10, execution_horizon 20), noise bank `randn((64,50,32), seed 2026)` 동일. G = 저장된 RTC prefix 사용, U = prefix 없음.
- 상태: R1 q02 223 상태 (A0/B1 등 실물 정책 rollout, 32 seed) · R2 실물 진단 상태 168 (vd_b, 16 seed) · d2 사람 상태 96 (vd_h, 16 seed) · 신규 시연 상태 50 (승인 in-sample + 제외 편, 16 seed).
- Baseline: 020000 의 기존 저장 배열 (q02_seed_pan.npz 첫 32 seed, vd b_raw/h_raw) 재사용. 020000 을 같은 코드로 다시 돌린 재현 검사 (각 6 상태): 평균 |차이| 0.05°, p99 0.2°, 최대 0.52°; 30 step pan 이동량 차이 평균 0.10°, 방향 일치 99.5 % (`logs/post/p02_repro_noise.txt`). → **약 0.5° 이하 · 1 %p 이하 차이는 수치 잡음과 구분하지 않는다.**
- 기준 수치 주의: 문서 기준값 T4 U 7.7 % · G 4.3 % 는 64 seed. 이 평가는 32 seed 라 같은 020000 의 값이 U 5.7 % · G 4.1 % 다.
- 지표 정의: `scripts/e02_metrics.py` 머리말 (q02b/q02c 정의 import). exec = a29 − a9, cum30 = a29 − s0, 방향 문턱 2°.
- 표: `eval/tables/e02_*.csv`, 짝 차이 + episode bootstrap 95 % CI `e02_paired_diffs.csv`.

### 2.2 R1 — Pan 복구 (실물 정책 상태, 학습 미사용)

T4 손목 놓침 · front 보임 (A0 · B1, 39 상태 × 32 seed), 단위 %:

| 지표 | 020000 | 250 | 500 | 750 | 1000 |
|---|---|---|---|---|---|
| G (RTC) exec 목표 쪽 | 4.1 | 22.8 | 27.3 | 30.2 | **33.5** |
| G exec 반대쪽 | 68.8 | 32.1 | 28.6 | 22.9 | 21.3 |
| G cum30 목표 쪽 | 0.4 | 10.3 | 13.2 | 15.5 | 19.0 |
| G cum30 반대쪽 | 86.9 | 57.4 | 51.1 | 46.5 | 43.8 |
| U (raw) exec 목표 쪽 | 5.7 | 16.1 | 12.4 | 14.2 | 14.4 |
| U exec 반대쪽 | 49.8 | 23.9 | 30.2 | 23.5 | 26.2 |
| U first (a0) 목표 쪽 | 13.3 | 21.0 | 42.7 | 40.1 | 49.5 |
| U cum30 목표 쪽 | 0.6 | 12.8 | 15.5 | 18.2 | 20.9 |

- A0 · B1 두 episode 모두 같은 방향으로 변함 (G exec 목표 쪽 A0 3.6 → 28.6, B1 4.6 → 38.2). episode 가 2 개라 bootstrap CI 는 의미 없음 — 표본은 사실상 2 판.
- 1000 에서도 cum30 기준 반대쪽 (43.8 %) 이 목표 쪽 (19.0 %) 보다 많음.
- T3 지나침 · 손목 봄 (A0, 14 상태): G exec 목표 쪽 16.3 → 47.5 %, 반대쪽 47.1 → 16.7 %; cum30 반대쪽 97.8 → 92.9 % (거의 그대로).
- T5 멀어짐 (12 판 23 상태): 변화 ≤ 3 %p.

### 2.3 R2 — 접근 · 그리퍼 (실물 진단 상태, 학습 미사용)

| 상태 (판) | 지표 | 020000 | 1000 | 1000 − base 95 % CI |
|---|---|---|---|---|
| AHEAD T0 (7) | G p_close30 (잘못된 위치 닫힘) | 0.536 | 0.536 | −0.045 … 0.036 |
| AHEAD preT0 (6) | G p_open30 | 0.427 | 0.271 | −0.292 … −0.042 |
| AHEAD reach/T0 (7) | G elbow Δ29 (1000 − base) | — | +0.47 / +0.82° | 0.07 … 1.01 / 0.21 … 1.57 (normal_grasp 도 +1.0 … +1.5°) |
| BELOW T2 (4) | G p_close30 | 0.641 | 0.407 | −0.422 … −0.062 |
| BELOW T0 (6) | G p_close50 | 0.729 | 0.625 | −0.229 … 0.000 |
| normal_grasp T2 (10) | G p_close30 (정상 닫힘 유지) | 0.931 | 0.900 | −0.081 … 0.000 |
| normal_grasp T0 (12) | G p_close30 | 0.193 | 0.250 | −0.005 … 0.141 |

- 모든 R2 · 정상 상태에서 elbow Δ29 +1 … +2°, lift Δ29 −0.5 … −1.4° 의 비슷한 이동 — AHEAD 에만 나타난 변화가 아님.
- wrist 큐브 위치 class (ahead · in_zone · left · right · below · not_visible 등) 별 p_close30 · p_open30 변화 ≤ 0.07.
- 실물 R2 평가 결과 (성공률) 와는 다른 양이다. 이 표는 같은 관측에서 예측 chunk 만 비교한 것.

### 2.4 신규 시연 상태 [in-sample / 제외 편]

| 그룹 | 지표 | 사람 | 020000 | 250 | 500 | 750 | 1000 |
|---|---|---|---|---|---|---|---|
| RC-F1 시작 (열림, 4) [in-sample] | p_close30 | 0.00 | 0.86 | 0.31 | 0.11 | 0.12 | 0.14 |
| RC-F1 pre_close (4) [in-sample] | p_close30 | 0.75 | 0.41 | 0.31 | 0.23 | 0.31 | 0.33 |
| RC-F2 시작 (닫힘, 4) [in-sample] | p_open30 | 0.00 | 0.50 | 0.34 | 0.42 | 0.39 | 0.33 |
| RC-F2 pre_open (4) [in-sample] | p_open30 | 1.00 | 0.56 | 0.55 | 0.77 | 0.67 | 0.62 |
| RC-F3 pre_open (4) [in-sample] | p_open30 | 1.00 | 0.59 | 0.58 | 0.75 | 0.72 | 0.73 |
| R1 승인 (12 상태) [in-sample] | pan 방향 일치 | — | 0.27 | 0.34 | 0.40 | 0.49 | 0.48 |
| R1 제외 ep 0–3 (12 상태) [미학습] | pan 방향 일치 | — | 0.54 | 0.55 | 0.66 | 0.68 | 0.68 |
| R1 제외 ep 0–3 | arm L1 0–49 (°) | — | 9.5 | 7.3 | 8.5 | 6.0 | 6.7 |

- R1 제외 편은 학습에 안 썼지만 같은 세션 · 같은 조작자 · 같은 장면 → held-out 이 아님 (근접 분포).
- R2 제외 ep 11 은 1 판 (2 상태) 이라 해석하지 않음.

### 2.5 정상 능력 유지

d2 사람 상태 (vd_h, 각 32 상태, d2 학습 데이터 = in-sample d2):

| 상태 | 지표 | 020000 | 1000 | 1000 − base 95 % CI |
|---|---|---|---|---|
| H_init | pan 방향 일치 (8) | 0.781 | 0.765 | −0.031 … 0.000 |
| H_init | pan Δ29 (°) | −8.93 | −10.23 | −2.19 … −0.39 |
| H_init | arm L1 vs 사람 0–29 (°) | 2.67 | 2.72 | −0.12 … 0.25 |
| H_reach | p_open30 (18) | 0.951 | 0.930 | −0.035 … −0.007 |
| H_reach | arm L1 vs 사람 | 1.83 | 2.01 | 0.10 … 0.27 |
| H_preclose | p_close30 | 0.969 | 0.953 | −0.049 … 0.004 |
| H_preclose | arm L1 vs 사람 | 1.45 | 1.68 | 0.15 … 0.32 |
| H_preclose | pan gain (6) | 0.349 | 0.044 | −0.506 … −0.102 |

실물 정책 상태 (q02, 학습 미사용):

| 유형 | 지표 | 020000 | 250 | 500 | 750 | 1000 |
|---|---|---|---|---|---|---|
| T1 first chunk G (20 판) | cum30 목표 쪽 % | 87.3 | 81.1 | 90.5 | 83.9 | 83.9 |
| T1 approach G (70) | exec 목표 쪽 % | 60.2 | 55.6 | 64.2 | 55.9 | 57.5 |
| T1 approach U | first 목표 쪽 % | 76.7 | 79.5 | 75.3 | 72.6 | 71.3 |
| T2 거의 정렬 G (13 판 52) | reverse % | 14.4 | 11.5 | 17.9 | 16.7 | 20.2 (CI +2.7 … +10.3 %p) |
| T2 거의 정렬 U | reverse % | 16.0 | 14.0 | 21.5 | 20.4 | 24.2 (CI +4.3 … +13.2 %p) |

- 불필요한 재개방: 정상 파지 상태 p_open30 증가 없음 (normal_grasp reach U 0.865 → 0.823, G 1.00 → 1.00).
- 사람 상태 arm L1 (사람 action 과의 차이) 이 +0.19 … +0.24° 증가 (약 +10 … 16 %). 재현 잡음 평균 0.05° 보다 큼.

---

## 3. 판단 · 한계 · 다음 실험

### 3.1 가설별 정리

| 가설 | 학습 미사용 상태 | in-sample |
|---|---|---|
| H1 Pan 복구 | T4 · T3 에서 목표 쪽 증가 · 반대쪽 감소 (2 판) [재추론] | R1 승인 상태 pan 방향 일치 0.27 → 0.48 |
| H2 pre-grasp 복구 | AHEAD 잘못된 위치 닫힘 변화 없음; R2 상태의 관절 변화는 정상 상태와 같은 모양; BELOW T2 닫힘 감소 | RC-F1 시작 조기 닫힘 0.86 → 0.14, F2/F3 pre_open 열기 소폭 증가 |
| H3 정상 유지 | T1 접근 · 정상 닫힘 · 재개방 대체로 유지; T2 reverse +5.8 %p (G), H_preclose pan gain −0.31, 사람 상태 L1 +0.2° | — |

### 3.2 통계적 한계

- R1 개선 근거인 T4/T3 상태는 A0 · B1 실물 rollout 2 판에서 나옴. seed 는 같은 관측의 noise 반복이지 독립 시행이 아님.
- R2 실물 진단 상태 판 수 4 … 12, 승인 시연 상태 4 판/시나리오. CI 는 판 단위 bootstrap 이지만 판 수가 작음.
- 단일 run · 단일 seed (2001) · 단일 혼합 비율 (W=5). R1 · R2 각각의 기여는 이 run 으로 분리되지 않음 (§10).
- 모두 오프라인 재추론. 실물에서 RTC 실행 · 지연 · 관측 변화가 겹친 결과와 다를 수 있음 — 실물 비교 없이 성공률 개선을 말할 수 없음.
- 교정 frame 의 31 % 는 한 번도 표본되지 않음 (1,000 step × 32).

### 3.3 다음 실험 [권고, §9 규칙 적용]

§9 분류: **"R1 만 개선됨"** 에 가장 가깝다 (R2 의 개선 징후는 in-sample 시연 상태에서만 보이고, 학습 미사용 실물 진단 상태에서는 보이지 않음). 정상 능력은 크게 악화되지 않았으나 T2 reverse 증가와 사람 상태 L1 증가가 있음.

1. R2 데이터 추가 분석: RC 12 편의 시작 상태가 AHEAD/BELOW 실물 진단 상태와 얼마나 가까운지 (관절 · wrist 큐브 위치) 비교. 이후 R2 단독 FT (d2 + R2, 같은 시작 · steps · LR · seed) 검토.
2. 정상 능력 감시 지표로 T2 reverse · H_preclose pan gain · 사람 상태 L1 을 계속 사용. 500 은 1000 보다 T2 reverse 증가가 작고 (G +3.5 %p) T4 개선은 비슷한 수준 (G exec 27.3 %) — 실물 비교 후보를 고를 때 500 · 1000 을 함께 검토.
3. R1 은 실물 비교 계획 준비 대상 (T4 cum30 반대쪽 여전히 44 %) — 실물 평가는 별도 사용자 지시 후.
4. R1/R2 추가 촬영은 자동으로 시작하지 않음.

---

## 4. 파일

| 경로 | 내용 | git |
|---|---|---|
| `scripts/` | r01–r05, train_recovery.py, make_run.py, run_wrapper.sh, e00–e02, eval_chain.sh | 기록 저장소 EXP-13 에 복사 |
| `manifest/` | training_manifest.{csv,json,sha256}, merge_map.json, dataset_sha256.json | 복사 |
| `tables/`, `eval/tables/`, `eval/e02_summary.json` | 검증 · 평가 표 | 복사 (npy 제외) |
| `runs/*.args`, `run_*.sh`, `*.status.log` | 설정 · 명령 · 종료 상태 | 복사 |
| `logs/` | 시작 상태, dry-run, eval chain, post 검사 | 작은 텍스트만 복사 |
| `dataset/` (1 GB), `runs/<run>/checkpoints` (44 GB), `eval/raw` (113 MB), `weights/`, `*.npy` | 데이터 · 모델 · 원시 출력 | 제외 |
