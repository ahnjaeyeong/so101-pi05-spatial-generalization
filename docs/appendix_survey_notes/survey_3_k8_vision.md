# 조사 3 — 카메라 이동 · K1–K8 단계 (2026-10-22 … 10-27): 데이터 · 학습 · 첫 실물 시험 · 시각 분석

작성 2026-11-02. 읽기 전용 조사 (파일 읽기 + 작은 읽기 전용 python 만 사용, 쓰기는 이 파일만).

신뢰도 표기:
- **A** = 로그·파일에 측정값으로 남아 있음
- **B** = 연구자의 실물 관찰 (파일 메모 또는 Claude 메모리에 사용자 발언으로 기록)
- **C** = 분석에서 나온 가설·해석
- **D** = 계획만 있음 (실행 안 됨)
- "미확인" = 근거 파일을 찾지 못함

주요 경로 약어: `MK8` = `/home/user/so101_runs/main_k8`, `CFG8` = `/home/user/so101_boxpick/config/redbox8_layouts.yaml`

---

## 0. 한눈에 보기 (시간순)

| 날짜 · 시각 | 사건 | 신뢰도 |
|---|---|---|
| 10-22 오전 | front 카메라를 상자 쪽 위로 옮김 (로봇이 화면 위, 상자가 화면 아래). 고정 위치 K1–K8 (3줄 격자) 로 바꿈 | A (CFG8 주석) |
| 10-22 14:59 / 16:27 | 6개 그룹(T1·T2·T3 × Known·Random × 64 = 384편) 배치 계획 생성 (seed 2101/2102/2201/2202/2301/2302) | A (layout_meta.json) |
| 10-22 15:37 ~ 10-23 17:15 | T1-K · T1-R · T3-K · T3-R 녹화 완료 (각 유효 64). **T2-K · T2-R 은 녹화 안 됨 (layout.csv 64줄 모두 `planned`)** | A |
| 10-23 17:26 | d2 = T1-K + T1-R + T3-K + T3-R 합침 (256편, 123,342 프레임) | A |
| 10-23 17:39:34 → 10-26 00:50:55 | d2 학습 (pi05_base 에서, expert-only, bs32, 20k) rc=0 | A |
| 10-26 13:51 / 14:02 | d2 020000 실물 시험 2회 (try3 필터 끔 2판, try3_filt 필터 켬 3판). **성공/실패 판정 기록 없음** | A (로그), 판정 미기록 |
| 10-26 14:20:39 | d4 = T1-K + T1-R + T3-R (192편) 학습 시작 | A |
| 10-26 14:30–16:40 | diag_grasp_bias 1차·2차 (오프라인 추론 프로브) | A |
| 10-26 (오후) | aswin task2 비교, grasp_pose 기울기·가시성 (CPU) | A |
| 10-26 17:00–19:10 | vision_probe 설계 · 영상품질 부록 · F1 CPU 준비/기준선 | A |
| 10-27 09:36–12:10 | F1 본실행 (GPU, d4 SIGSTOP 09:41–10:52) | A |
| 10-27 13:22–15:04 | action_bottleneck G1/G2 (d4 SIGSTOP 14:04–15:04) | A |
| 10-27 22:26 | d4 를 step 10,003 에서 정상 종료 요청 (010000 저장 확인 후). 이유: sampling_ablation 우선 | A |
| 10-29 | d2 실물 pan_diag · filt_on/off (다른 조사 담당, 6절에 목록만) | A |

---

## 1. 재배치와 수집

### E-K8-0. front 카메라 이동 · K1–K8 재배치 (2026-10-22)

- **목적:** 새 front 카메라 구도 + 고정 위치 8개로 본 수집 다시 시작 (예전 `main/redbox_*` K1–K4 384편과 섞지 않음). (A, `MK8/d2/description.md` 2절, CFG8 머리 주석)
- **당시 문제/가설:** 메모리상 직전 단계(redbox_all, 옛 카메라 K1–K4)에서 실물 성공이 없었고 위치 일반화 문제가 관찰됨. 카메라를 옮긴 직접 이유는 파일에 명시 안 됨 → **미확인** (CFG8 에는 "2026-10-22 사용자: front 카메라를 상자 쪽 위로 옮김" 만 있음).
- **K 좌표 (C frame, cm; x=상자 쪽 +, y=로봇 왼쪽 +; 원점 = 상자 앞 벽 바깥면 로봇 기준 오른쪽 끝)** (A, CFG8 `known_positions`):
  - 상자 쪽 줄: K1 (−8.5, 26.5) · K2 (−8.5, 11.5) · K3 (−8.5, −3.5)
  - 가운데 줄: K4 (−17.0, 26.5) · K5 (−17.0, 11.5) · K6 (−17.0, −3.5)
  - 로봇 쪽 줄: K7 (−25.5, 26.5) · K8 (−25.5, −3.5)
  - 열 간격 15 cm, 줄 간격 8.5 cm. x 는 실측, y 원점만 화면 추정 ±0.5 cm. front_px (640×480): K1 (496,280) … K8 (170,113).
- **카메라:** front 640×480 (= 1280×720 의 가로 160–1119 를 1/1.5 축소), H_cm_to_px 를 K1–K8 큐브 8개 검출 중심으로 맞춤, 재투영 오차 평균 2 px ≈ 0.2 cm. 카메라 바로 아래 탁자점 (9.0, 13.7), 높이 약 46 cm (±2 cm 어림). 상자 근처(x > −5)는 덜 정확. 새 front 화면은 상자 카메라 쪽 절반이 화면 밖 → `end_in_box_if_table_clear: true` 규칙 추가. (A, CFG8)
- **로봇 기준값:** base (−31.0, 11.0) cm (T1-K 48판 pan 으로 맞춤, 잔차 평균 1°, 최대 4.3°), pan = −bearing − 1.4°, wrist_roll neutral −1.5°, roll_align_tol 15°, roll_either_way 38° (10-23 사용자 40→38). (A, CFG8)
- **큐브 각도:** 0 · L30(↺) · R30(↻) · 45, "로봇에 가장 가까운 면 모서리와 로봇 좌우축의 예각". 15° 제외(10-22 사용자), 60° 는 반대쪽 30° 와 같아서 제외. QA 허용: 0 ±15°, 30 은 같은 방향 15–37.5°, 45 는 37.5° 초과. Known·Random 모두 각도 계획 (Random 은 위치 자유, 각도만). (A, CFG8 `angles`)
- **집기 어려운 영역 (hard zone):** 로봇 바로 앞 다각형 [[-34.4,-1.5],[-33.8,24.7],[-18.2,24.6],[-18.4,-1.1]] (사용자 텔레옵 시험 후 표시). 히트맵·제안에서만 제외, QA 금지 규칙 아님. (A, CFG8; 원래 관찰은 B)
- **근거:** `/home/user/so101_boxpick/config/redbox8_layouts.yaml`, `/home/user/so101_runs/main_k8/setting/` (redbox_K8_* 사진·가이드 PDF), 메모리 `k8-relayout.md`.

### E-K8-1. main_k8 본 수집 (계획 6×64=384 vs 실제 4×64=256)

- **계획 (D→A):** 6 그룹 × 64편 = 384편 (예전 redbox_all 과 같은 편수·순서). 그룹·seed: t1_known 2101, t1_random 2102, t2_known 2201, t2_random 2202, t3_known 2301, t3_random 2302. repo `oxr/so101_k8_redbox_*`. (A, CFG8 `groups`, `MK8/d3/description.md`)
- **계획 구성 (layout_meta.json stats):**
  - T1-K: K1–K8 각 8판, 각도 0/L30/R30/45 각 16.
  - T1-R: 위치 자유, 각도 각 16.
  - T2-K: 빨강 2개 24 · 3개 24 · 4개 16판, K 마다 빨강 23번, 빨강 각도 각 46. (계획만)
  - T2-R: 같은 개수 구성, 각도 각 46. (계획만)
  - T3-K: 빨강 K 마다 8판, 방해물 1개 16 · 2개 24 · 3개 24판, 방해 색 4가지 각 34, 전체 각도 칸 각 50 (빨강+방해물). description 3.3절은 "방해물 1개 17 · 2개 23 · 3개 24" 와 빨강 각도 16×4 (ep060 relabel 반영 후 값으로 보임).
  - T3-R: 방해물 2개 12 · 3개 13 · 4개 13 · 5개 13 · 6개 13 (layout_meta) — description 3.3절은 "5개 14 · 6개 12" (relabel 반영). 색 64/65/65/64.
- **판 시간:** T1·T3 episode_time_s 45, T2 75 (계획). reset 120 s. 30 fps, front·wrist 640×480 MJPG, 저장 AV1. (A, `MK8/redbox_수집명령.md`, notes.md)
- **수집 장비 설정:** SO101 follower `my_arm` + leader `my_leader`, P=16 I=0 D=32, max_relative_target=None (녹화), use_degrees=True, 카메라 auto exposure (exposure_time 156, WB 4600, dynamic framerate 0). (A, `MK8/redbox_t1_known/notes.md`)
- **실제 녹화 (A, layout.csv status 집계 + 원본 info.json):**

| 세션 | 녹화일 | 원본 편수 / 프레임 | 제외 (원본 ep) · 이유 | 유효 | 사용 경로 |
|---|---|---|---|---|---|
| redbox_t1_known | 10-22~10-23 | 66 / 35,571 | 51 (판 김 29.1 s, K7 처음 잡기 13.4 s), 64 (51 재촬영인데 손목 반대쪽: 필요 ↻38 · 돌림 ↺54) | 64 | `release/` (64 / 33,974) |
| redbox_t1_random | 10-22~10-23 | 68 / 35,799 | 2 (시작 정지 4.6 s), 36 (손목 반대: 필요 ↻37 · 돌림 ↺55), 39 · 41 (구석 큐브, 판 김 31 · 26.5 s) | 64 | `release/` (64 / 32,758) |
| redbox_t3_known | 10-23 | 64 / 28,250 | 없음 | 64 | 원본 `dataset/` |
| redbox_t3_random | 10-23 | 65 / 28,758 | 57 (손목 반대: 필요 ↻34 · 돌림 ↺53) | 64 | `release/` (64 / 28,360) |
| redbox_t2_known | — | 0 | 계획 64줄 모두 `planned` | 0 | — |
| redbox_t2_random | — | 0 | 계획 64줄 모두 `planned` | 0 | — |

- **relabel (데이터는 그대로, 계획만 실제대로 고침):** T3-K ep060 (노랑 K8 안 놓음 → T3K2-O1), T3-R ep006 (주황 하나 더) · ep045 · ep061. (A, layout_meta relabels, d2 description 3.1)
- **QA 요약 (A, 각 `qa_report.md` 3-2절 표에서 직접 셈):**
  - 판 길이: T1-K 11.9–29.1 s (평균 18.0) · T1-R 13.0–31.1 s (17.5) · T3-K 11.4–21.8 s (14.7) · T3-R 10.6–23.9 s (14.7). 45 s 를 채운 판 없음. NaN 0, 영상·데이터 프레임 수 일치.
  - 각도 범위 밖(✗) 표시 행: T1-K 7 · T1-R 6 · T3-K 16 (빨강 4, 나머지 방해물) · T3-R 12 (빨강). 대부분 사용자가 "남김(✓)" 처리 — 30° 배치가 ~40° 로 놓인 경우 등 (B, 메모리 `k8-relayout.md`).
  - 손목 "반대쪽" ✗ 표시: T1-R 1 (ep036), T3-K 1, T3-R 1 (ep057). T1-K 의 ep051/064 은 손목 열에 ✗ 없이 제외 사유로 기록.
  - 손목 회전 범위 경고 기준 `wrist_roll_max_range_deg` 처음 60 → 같은 날 70 (T1-K 첫 16판 중 5판이 60.0–70.6°). (A, CFG8 주석)
- **T2 를 녹화하지 않은 이유:** 파일에 명시된 이유 없음 → **미확인**. d1/d3 description 은 "T2 미녹화 (계획만 있음)" 상태만 기록. 연구자 기억("384 더 모으려다 256 실험도 나빠서 원인 분석 먼저")은 파일로 확인되지 않음 (B, 사용자 기억; 파일 근거 없음). 10-26 이후 작업이 전부 원인 분석(diag, vision probe 등)으로 넘어간 것은 파일 날짜로 확인됨 (A).
- **근거:** `/home/user/so101_runs/main_k8/README.md`, `/home/user/so101_runs/main_k8/redbox_수집명령.md`, `/home/user/so101_runs/main_k8/redbox_{t1,t2,t3}_{known,random}/layout.csv`, `.../layout_meta.json`, `.../qa_report.md`, `.../notes.md`.

### E-K8-2. release 사본과 d2 합침 (2026-10-23)

- **방법:** `lerobot-edit-dataset --operation.type delete_episodes --new_root <세션>/release` (원본 그대로). 제외 판이 든 영상 파일만 재인코딩 (SVT-AV1 CRF 30), 재인코딩 판의 이미지 차 평균 0.5–0.8/255, 나머지 0, state·action 같음. (A, d2 description 3.1)
- **합침 명령 (10-23 17:26):** merge `[t1_known_release, t1_random_release, t3_known(원본), t3_random_release]` → `MK8/d2/dataset`, repo `oxr/so101_k8_d2`, 952 MB.
- **확인 (A, info.json 재확인):** 256편, 123,342 프레임, task 1개 ("pick up the red cube and put it in the brown box"), fps 30. 판 길이 순서 일치, 각 원본 첫·마지막 판 프레임(+5) action·state·front·wrist 8곳 같음.

| 합친 ep | 원본 | 편수 | 프레임 | 판 길이 평균/중앙/범위 (s) |
|---|---|---|---|---|
| 0–63 | T1-K | 64 | 33,974 | 17.7 / 17.5 / 11.9–23.8 |
| 64–127 | T1-R | 64 | 32,758 | 17.1 / 16.8 / 13.0–25.9 |
| 128–191 | T3-K | 64 | 28,250 | 14.7 / 14.3 / 11.4–21.8 |
| 192–255 | T3-R | 64 | 28,360 | 14.8 / 14.6 / 10.6–23.9 |
| 합 | | 256 | 123,342 (68.5 분) | |

- 과제별: T1 128편 66,732 프레임 (54%), T3 128편 56,610 프레임 (46%).
- **근거:** `/home/user/so101_runs/main_k8/d2/description.md`, `/home/user/so101_runs/main_k8/d2/dataset/meta/info.json`.

### 옛 redbox_all (384편) 과 d2 (256편) 의 관계

| 항목 | main/redbox_all | main_k8/d2 | 근거 |
|---|---|---|---|
| 카메라 | 옛 front 위치 | 10-22 옮긴 새 front | CFG8 주석 "기존 384편은 config/redbox_layouts.yaml (K1–K4, 예전 카메라)" |
| 고정 위치 | K1–K4 | K1–K8 | 같음 |
| 녹화 날짜 | 10-14~10-15 세션 (main/README) | 10-22~10-23 | `/home/user/so101_runs/main/README.md`, d2 description |
| repo | `oxr/so101_redbox_*`, `oxr/so101_redbox_all` | `oxr/so101_k8_redbox_*`, `oxr/so101_k8_d2` | train_config |
| 편수 / 프레임 | 384 / 188,530 (T1+T2+T3) | 256 / 123,342 (T1+T3) | info.json |
| 시작 가중치 | `lerobot/pi05_base` | `lerobot/pi05_base` | 각 checkpoints/020000/pretrained_model/train_config.json `policy.pretrained_path` |

- **결론 (A):** 두 데이터셋은 **별개 녹화 (겹치는 판 없음)** 이다 — 다른 날짜, 다른 카메라 위치, 다른 repo. d2 는 redbox_all 체크포인트에서 이어 학습한 것이 **아니라 `lerobot/pi05_base` 에서 새로 학습**했다 (train_config `pretrained_path: lerobot/pi05_base`, `resume: false`). 설정(레시피)만 redbox_all `pi05_expert_bs32_20k` 와 같다.

---

## 2. d1 · d2 · d3 · d4 정의와 학습

### E-K8-3. d1 / d3 (계획만, D)

- d1 = T1 + T2 (T2-K·T2-R 녹화 대기), 문장 2개 (T2 = "put all the red cubes in the brown box"). d3 = T1 + T2 + T3 (384편, redbox_all 과 같은 편수·순서). 둘 다 **T2 미녹화로 준비 안 됨**. 정하지 않은 것: 스텝 수(epoch 맞추기 여부), 평가 조건. (D, `MK8/d1/description.md`, `MK8/d3/description.md`)
- 폴더에는 description.md 만 있음 (A, ls).

### E-K8-4. d2 학습 (T1-K·T1-R·T3-K·T3-R, 256편)

- **목적:** main_k8 비교 실험 d1·d2·d3 중 T1+T3 조합 (세 실험 모두 T1 공통, 함께 넣는 과제만 바꿈). (A, d2 description)
- **모델 / 시작:** pi05, `lerobot/pi05_base` (A, train_config).
- **학습 설정 (A, train_config.json + training_params.md):**
  - `train_expert_only=true`, `freeze_vision_encoder=true` (PaliGemma 전체 고정, action expert 만 학습). 학습 파라미터 693,422,112 / 전체 4,143,404,816.
  - AdamW lr 2.5e-5 (β 0.9/0.95, eps 1e-8, wd 0.01, grad clip 1.0). scheduler cosine_decay_with_warmup: config 값 warmup 1000 / decay 30000 / decay_lr 2.5e-6 → steps 20000 에 맞춰 자동 축소된 실효값 warmup 666, decay 20000 (training_params.md). 로그 lr: 1k 2.5e-5, 10k 1.4e-5, 15k 5.8e-6, 20k 2.5e-6.
  - batch 32, steps 20,000 → 640,000 샘플 ≈ 5.19 epoch. seed 1000. bf16, gradient checkpointing, num_workers 4, 이미지 증강 끔 (`image_transforms.enable=false`), chunk_size 50 / n_action_steps 50, num_inference_steps 10 (학습 설정), image_resolution 224×224, normalization VISUAL IDENTITY · STATE/ACTION QUANTILES. use_peft false.
- **실행:** 2026-10-23 17:39:34 → 2026-10-26 00:50:55, rc=0, 55시간 11분, 9.93 s/step, GPU 최대 20.8 GB, 시스템 메모리 최대 43.5 GB. (A, `.time`, training_params.md)
- **loss (A, 로그 50 스텝마다 400개; 순서로 step 대응):**

| step | 50 | 100 | 500 | 1k | 2k | 5k | 10k | 15k | 20k | 최저 |
|---|---|---|---|---|---|---|---|---|---|---|
| loss | 0.176 | 0.148 | 0.044 | 0.034 | 0.030 | 0.027 | 0.022 | 0.021 | 0.020 | 0.019 (첫 등장 step 14,500, 0.019 기록 21회, 마지막 19,950) |

  - grad norm: step 50 0.712 → step 20k 0.251.
- **체크포인트:** 005000 · 010000 · 015000 · 020000 (`last` = 020000), 하나 약 11 GB. (A, ls)
- **I/O 기록:** `~/io-capture/20261023-1739/SUMMARY.md`, zip (A, description; 내용은 이 조사에서 열지 않음).
- **근거:** `/home/user/so101_runs/main_k8/d2/train/32_20000/run_pi05_expert_bs32_20k.sh`, `.../launch_pi05_expert_bs32_20k.sh`, `.../pi05_expert_bs32_20k.log`, `.../pi05_expert_bs32_20k.time`, `.../pi05_expert_bs32_20k/training_params.md`, `.../pi05_expert_bs32_20k/checkpoints/020000/pretrained_model/train_config.json`.

### E-K8-6. d4 (T1-K · T1-R · T3-R, 192편) — 학습 도중 중단

- **목적:** 사용자 요청 (10-26) "t1 128편이랑 t3 r 64편해서 총 192편 다시 파인튜닝" = d2 에서 T3-K 64편 뺀 것. (A, `MK8/d4/description.md`)
- **당시 가설:** description 에는 이유 없음. 메모리 `d2-grasp-bias-diag.md` 에 "same grid probe on d4 (less K share)" 가 다음 제안으로 기록 — K 위치 끌림을 줄이려는 의도로 보이나 파일에 명시 안 됨 → C/미확인.
- **데이터 (A, info.json):** 192편, 95,092 프레임, task 1, 724 MB. 0–63 T1-K (33,974), 64–127 T1-R (32,758), 128–191 T3-R (28,360). T1 70% / T3 30%. 확인: 판 길이 순서, 경계 프레임 6곳 같음.
- **학습 설정:** d2 와 같음 (pi05_base 에서, expert-only, freeze vision, lr 2.5e-5, bs32, 20,000 스텝 계획 ≈ 6.7 epoch). (A, run 스크립트, train_config)
- **실행 (A, `.time`, PAUSE_NOTE_F1.txt, STOP_NOTE_sampling_ablation.txt):**
  - 시작 2026-10-26 14:20:39 (pid 3000922).
  - 일시정지 10-27 09:41:23 step 6,524 → 재개 10:52:02 (F1 GPU 추출용).
  - 일시정지 10-27 14:04:22 step 7,472 → 재개 15:04:04 (action_bottleneck G1/G2).
  - 10-27 22:26:42 SIGINT 정상 종료 요청 — 010000 저장 확인 뒤 step 10,003. 이유: "사용자 10-27 우선순위 변경 (d2 sampling_ablation A0–A2r 먼저)". 22:28:48 종료, `.time` 에 rc=143.
  - 체크포인트: 005000, 010000 (`last`). 015000·020000 없음.
- **loss (A):** step 50 0.182 → 1k 0.034 → 5k 0.026 → 10k 0.022 (최저 0.021, 첫 등장 8,450). 로그 200개.
- **분석 프로브 영향 (A):** diag 2차 동안 d4 10.57 → 15–17 s/step, 지연 약 26분 추정 (diag 리포트 11절).
- **평가:** d4 실물 평가 기록 없음 (`MK8/d4/` 에 eval 폴더 없음) → 미평가.
- **근거:** `/home/user/so101_runs/main_k8/d4/description.md`, `/home/user/so101_runs/main_k8/d4/dataset/meta/info.json`, `/home/user/so101_runs/main_k8/d4/train/32_20000/{run_,launch_}pi05_expert_bs32_20k.sh`, `.../pi05_expert_bs32_20k.log`, `.../pi05_expert_bs32_20k.time`, `.../PAUSE_NOTE_F1.txt`, `.../STOP_NOTE_sampling_ablation.txt`.

---

## 3. d2 실물 시험 (10-26)

### E-K8-5. try3 (필터 끔) · try3_filt (필터 켬)

- **목적:** d2 020000 첫 실물 시험 (녹화 + 자동 분석). 판정은 이 도구가 기록하지 않음. (A, `평가_명령.md`)
- **모델:** `d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000`.
- **평가 환경 (A, command.txt, 평가_명령.md, diag 리포트 1절):**
  - 추론: lerobot-rollout RTC, execution_horizon 20, prefix_attention_schedule EXP, num_inference_steps 5 (학습 기본 10), queue_threshold 30. 30 Hz.
  - `--robot.max_relative_target=8` (녹화 때는 없음). 카메라 warmup 기본 1 s (녹화 4 s).
  - 팔 필터: try3 = 끔, try3_filt = 켬 (`--arm_filter=true`: 팔 5관절 EMA α 0.5 + 관절별 속도 제한, 그리퍼 제외). 사용자 10-26 "둘 다 필터 씌워" 지시는 try3 실행 뒤 (B/A, 메모리 + 평가_명령.md "참고: 10-26 13:51 첫 시험 … 필터 없이").
  - 과제 문장: T1 학습 문장 그대로. 과제 T1 (방해물 없음).
  - 시작 자세 (pose_check): 두 실행 모두 "시작 자세 OK". 단 try3_filt 의 shoulder_lift −100.9 는 표의 "학습 범위 −103.3 ~ −102.4" 밖인데도 OK 로 표시됨 (A, 기록 그대로; 판정 허용치 미확인). diag 리포트: "filt ep2 는 팔을 뻗은 자세에서 시작".
  - 큐브 위치·각도 (diag 리포트 3절, front 첫 프레임 + H 역산):

| 실행 · 판 | 큐브 (cm) | 가까운 K (거리 cm) | 첫 닫힘 시각 | pan 기대 / 실제 state | pan_res | 같은 자리 사람 대비 Δpan | wrist 에 빨강 | 그리퍼 |
|---|---|---|---|---|---|---|---|---|
| try3 ep0 | (−8.3, 26.2) | K1 (0.4) | 19.6 s | −35.2 / −34.8 | +0.4 | −1.0 | 보임 | 14.7 |
| try3 ep1 | (−22.4, 25.5) | K7 (3.3) | 12.5 s | −60.6 / −8.6 | +52.0 | +59.9 | 안 보임 (상자 보임) | 2.6 |
| filt ep0 | (−8.4, −2.9) | K3 (0.6) | 12.4 s | 30.3 / 33.2 | +3.0 | +2.2 | 보임 | 14.1 |
| filt ep1 | (−9.2, 3.7) | K3 (7.3) | 29.0 s | 17.1 / 28.7 | +11.6 | +11.5 | 안 보임 | 9.5 |
| filt ep2 | (−15.3, 26.2) | K4 (1.7) | 12.5 s | −45.5 / −40.4 | +5.2 | +5.0 | 안 보임 | 5.5 |

  - 큐브 각도: 평가 판별 각도 기록 없음 → 미확인.
- **정량 결과 (A):**
  - 판 수: try3 = 2판 저장 (N_EP=3 지정, dataset 2편 2,983 프레임), try3_filt = 3판 (3,129 프레임).
  - analysis.json (판 평균, 관절 순서 pan/lift/elbow/flex/roll/grip):
    - action 방향 반전 /s: try3 9.57/6.44/6.80/3.50/4.06/0.99, filt 2.91/1.81/2.39/0.86/1.19/2.05.
    - 추종 오차 >8° 비율 (%): try3 0.19/7.99/4.53/0/0.16/3.0, filt 0.16/7.97/6.2/0/0/1.44.
    - clamp 경고: try3 416, filt 361. RTC 추론 150 / 159회, 지연 평균 340.5 / 345.2 ms (최대 370 / 390), delay 최대 12틱, starved tick 32 / 43.
    - clamp 관절별 (diag 리포트): try3 lift 247, elbow 134, gripper 118, pan 53, roll 2; filt lift 290, elbow 203, gripper 32, pan 5.
  - 첫 닫힘 5개 중 3개, 재시도 포함 닫힘 18개 중 4개에서 wrist 에 빨강 없음 (학습 첫 파지 0/256). try3 ep1 은 첫 닫힘 뒤 재시도 10번, 큐브가 (−20.2, 27.2) → (−30.2, 27.0) 등으로 밀림.
  - **성공/실패 판정: 기록 없음** (`results.md` 없음, results_all.csv 에 10-26 행 없음; `pan_inference_diagnostic/03_existing_log_inventory.md` 13행 "성공/실패 판정은 기록되지 않았다").
- **정성 관찰:** filt ep1 pan 이 0–14 s 동안 5–15° 근처에서 흔들린 뒤 29 s 까지 28.7° 로 천천히 감 (K3 방향 31.4°, 큐브 방향 17.1°). (A, diag 리포트)
- **연구자 관찰 (B):** 메모리 `d2-grasp-bias-diag.md` — "User asked (10-26) why d2 grasps right of the cube at random positions". 이 질문이 diag_grasp_bias 의 출발점.
- **한계:** 5판뿐, 모두 T1, T3 평가 없음, 판정 미기록, 필터 조건이 판마다 섞임 (2 끔 / 3 켬).
- **다음 실험으로:** 오른쪽 편향 원인 → diag_grasp_bias (E-K8-7/8).
- **근거:** `/home/user/so101_runs/main_k8/d2/eval/평가_명령.md`, `/home/user/so101_runs/main_k8/d2/eval/rollouts/20261026_135128_20k_t1_try3/{command.txt,analysis.json,pose_check.txt,console.log,debug.log}`, `/home/user/so101_runs/main_k8/d2/eval/rollouts/20261026_140246_20k_t1_try3_filt/{command.txt,analysis.json,pose_check.txt,filter_log.csv}`, `/home/user/so101_runs/main_k8/d2/diag_grasp_bias/분석_리포트.md` 3절.

---

## 4. 분석

### E-K8-7. diag_grasp_bias 1차 — 파지 방향 편향 · 위치 일반화 (10-26 오후, 오프라인)

- **목적:** d2 가 Random 위치에서 큐브 오른쪽을 잡는 원인. 학습↔추론 불일치 여부, 영상/state 어느 쪽이 방향을 정하는지, 새 위치 일반화.
- **모델:** d2 020000. 오프라인 추론 (GPU, d4 학습과 동시), seed 3개, num_inference_steps 5.
- **데이터:** 학습 256편 (in-sample), 합성 front 영상 grid 163곳, 평가 5판.
- **결과 (A, 분석_리포트.md 1–4절):**
  - **코드 경로:** 정규화 통계 학습=추론 같은 파일 (pi05 는 rollout dataset_stats 안 씀). q01/q99 = 원본별 분위 중 최소/최대 envelope (실제 1/99% 아님, 예 action wrist_flex q01 0.65 vs 실제 1% 28.26). 절대 관절 action. 영상 전처리 같음, 학습 증강 없음. 학습 영상은 AV1 디코드 / 추론은 MJPEG 원본 (채널 평균 차 ≤7/255). 차이: max_relative_target 8, warmup, step 5 vs 10, 필터.
  - **사람 시연:** 파지 pan = a·기대 + b: Known a 1.012 (R² 0.998, 잔차 SD 2.16°), Random a 1.028 (R² 0.999, 1.90°). Random 큐브의 가까운 K 까지 중앙값 4.92 cm (3 cm 안 11.7%). K vs R pan_res p=0.39. 256/256 닫힘 직전 wrist 에 빨강 보임.
  - **swap 프로브** (T1 판 짝 100쌍, pan 차 >15°): front 만 B → B 영상 계수 0.59; wrist 만 B → −0.04 (A state 계수 0.60); 둘 다 B 0.67. → 출발 방향은 front 영상이 정하고 wrist·state 는 거의 안 씀 (첫 chunk 기준).
  - **start 프로브 (학습 판):** 예측 vs 사람 기울기 Known 0.82 / Random 0.76, |오차| 중앙값 6.7° / 6.4°, seed SD 중앙값 4.4° / 5.7°.
  - **grid (합성, 타당성 r 0.952):** 전체 예측 = 0.46·기대 + 2.4, |오차| 중앙값 14.4°, 오른쪽 48%. 오차 = a·(가까운 K − 기대) + c·(0 − 기대): a 0.30, c 0.29. 가까운 K 거리별 |오차| 0–3 cm 6.8°, 3–6 cm 11.7°, 6 cm↑ 25.3°.
  - **pregrasp (학습 판, 1 s 전 관측):** pan |오차| 중앙값 Known 1.01° / Random 1.04° (p 0.85).
  - **eval 판 시작 관측 예측:** try3 ep1 기대 −60.6 → 예측 −38.1 ± 10.3, 실제 −8.6 등 (표 4.4).
- **해석 (리포트 원문 성격):** 학습↔추론 불일치 없음. 새 위치는 가까운 K 와 중앙 쪽으로 끌림 (a≈0.3, c≈0.3). 오차 부호는 K/중앙 쪽을 따름 — "항상 오른쪽" 아님 (48%). (A/C)
- **한계:** 평가 5판, T3 없음, 첫 chunk 방향만 (닫힌 고리 재현 안 함), 합성 wrist 는 큐브 없는 중앙값, base 위치 추정값.
- **근거:** `/home/user/so101_runs/main_k8/d2/diag_grasp_bias/분석_리포트.md`, `summary.json`, `probe_*.csv`, `grasp_train.csv`, `grasp_eval.csv`, `fig1`–`fig6`.

### E-K8-8. diag_grasp_bias 2차 — exp1–4 (10-26 15:10–16:40)

- **exp1 체크포인트 5k/10k/15k/20k (A):** start |오차| 중앙값 K/R 10.9/12.9 → 6.3/7.7 → 7.2/8.5 → 5.8/7.6°. pregrasp pan |오차| 1.49/1.90 → … → 1.09/0.86°. 보정 후 grid K 끌림 0.27 / 0.34 / 0.25 / 0.22 [20k CI 0.07–0.38]; 학습 Random 판 K 끌림(보정 후) 20k 0.21 [0.09, 0.32]. 중앙 끌림 보정 전 0.35 → 보정 후 0.08 (20k). → **K 끌림은 새 위치 특유가 아니라 학습 Random 위치에서도 같은 크기**, 중앙 끌림 대부분은 chunk 안에서 덜 돈 아티팩트 (A 측정, 해석 C).
- **exp2 단계 × 카메라 민감도 (T1 128편, 큐브만 영상 편집):** front 이득 start 0.85 [IQR 0.34, 1.10], mid 0.040, pre 0.006. pre 단계 wrist → 탁자 이득: **접선 G_tt 0.10 [0.02, 0.20]** (K 0.09, R 0.15), 반지름 G_rr 0.34 [0.15, 0.42], G_rt 0.25, G_tr 0.00. 판마다 직접 맞춘 45편: G_tt 0.21, G_rr 0.26 (IQR 음수–0.76). wrist 축: u ≈ 반지름 66 px/cm, v ≈ 접선 −79 px/cm, u 축 각도 = 0.91·roll − 5.5° (r 0.55). (A)
- **exp3 filt ep1 pan 흐름 분해:** 14–29 s 동안 raw − 오프라인 모델 +0.06° (|차| 중앙값 0.66°), 필터 −0.04°, clamp 0.00°, state − sent −0.29° → 흐름은 모델 자체 재계획. 같은 구간 wrist 빨강이 영상 오른쪽 끝 (u 0.92–0.99, 19–26.5 s), 28 s 부터 안 보임. (A)
- **exp4 noise 64개:** pan SD 중앙값 (step 5/10) 학습 start 10.1/12.6°, grid 14.6/17.5°, 평가 start 10.9/13.0°, 학습 pre 1.2/1.8°. (A)
- **exp6 d4 영향:** 위 E-K8-6 참고.
- **한계 (리포트 12절):** 편집은 큐브 조각 옮겨 붙이기 (그림자·원근 미반영), wrist 축 보정은 45/128편만 잘 맞음, exp3 오프라인 재계획은 AV1·RTC 안내 없음, exp2·4 는 20k 만.
- **다음:** 정책이 막판 wrist 좌우 교정을 거의 안 함 (G_tt 0.10) → vision 표현 문제인지 action expert 문제인지 분리 (vision_probe), 레퍼런스 비교 (aswin), 파지 자세 가설 (grasp_pose).
- **근거:** 같은 리포트 6–12절, `/home/user/so101_runs/main_k8/d2/diag_grasp_bias/exp_summary.json`, `exp1/`–`exp4/`, `fig7`–`fig9`.

### E-K8-9. aswinkumar99 task2-all 비교 (10-26, CPU·메타데이터만)

- **목적:** 공개 SO101 π0.5 레퍼런스와 설정·시연 차이 비교 (특히 막판 좌우 교정).
- **데이터:** 레퍼런스 task2 (스펀지 1–6개) fixed 64 + random 64 = 128편 128,446 프레임, 파지 이벤트 515. 우리 d2 256편 123,342 프레임, 파지 256. 영상·가중치 내려받지 않음.
- **설정 차이 (A):** 레퍼런스 lr 5e-5 (warmup 1000, decay 20000), compile, workers 8, H200 4 h 28 m; 우리 lr 2.5e-5, Thor 55 h. 둘 다 expert-only + frozen vision, 증강 없음, bs32 · 20k (≈5.0 vs 5.2 epoch). 레퍼런스 q01/q99 = 프레임 수 가중 평균 (데이터보다 좁음) vs 우리 envelope. 추론: 레퍼런스 lerobot-record 동기, n_action_steps 50, RTC 없음, denoise 10, max_relative_target 없음, "~6 Hz" / 우리 RTC h20 · q30 · step 5 · max_rel 8. 카메라 키: 레퍼런스 base_0_rgb · right_wrist_0_rgb + empty_cameras 1.
- **레퍼런스 실물 결과 (A, trials.json 인용):** ST2 known 8/8, random 6/8 (실패 2 = 잡기 실패). 우리 d2 T1 5판 "성공 판정 미기록".
- **시연 비교 (A):** 마지막 1 s pan 순변화 우리 0.18–0.44° vs 레퍼런스 0.09–0.26°. 마지막 3 s pan 순변화 ≥3° 비율 우리 3–14% vs 레퍼런스 T2 60/63%. 손목 roll 변화 우리 20–23° vs 레퍼런스 5–8°. 접근 시작 상태 pan SD 우리 2.0–3.4° vs 레퍼런스 T2 33.9/35.6°. pan 이 최종 ±2° 안에 머문 시간 우리 3.7–4.4 s vs 레퍼런스 1.9–3.4 s. 마지막 3 s 변화 중 주 회전과 같은 방향 비율 우리 42–46% vs 레퍼런스 49–78%.
- **해석:** 리포트는 사실만 기록. "visual servoing 서술·측정 레퍼런스에 없음". 레퍼런스 위치 민감도 프로브는 **설계만 (D)**.
- **근거:** `/home/user/so101_runs/reference/aswin_task2_compare/비교_리포트.md`, `demo_kinematics_summary.csv`, `demo_roll_late.csv`, `demo_late_direction.csv`, `github/` (trials.json).

### E-K8-10. grasp_pose — 그리퍼 기울기 · 가시성 (10-26, CPU)

- **목적:** 사용자 가설 "우리는 수직 집게 파지, 레퍼런스는 비스듬한 파지" 확인 + 우리 영상의 가림·그림자·조명. (가설 출처: 메모리 `grasp-tilt-visibility.md`, B/C)
- **방법:** URDF `so101_new_calib.urdf` FK, 각 규약 A (lerobot 도) / B (+범위중앙−homing). 우리 256편 · 레퍼런스 770 이벤트 (관절 데이터만).
- **결과 (A):**
  - 규약 검증: 끝 높이 SD 우리 A 0.49 / **B 0.32 cm**, 레퍼런스 A 1.07 / B 1.01 cm → 우리 팔은 B 가 맞음, 레퍼런스는 어느 쪽도 일정하지 않음.
  - 파지 tilt 중앙값: 우리 A 11.1–13.1° / B 3.0–5.4°; 레퍼런스 A 18.2–25.3° / B 36.8–43.9°. 4가지 조합 모두 레퍼런스가 더 기움 (+7–14° … +33–40°), 반지름 바깥 방향, 좌우 lean ≤ 1–3°.
  - 가시성 (d2 6,999 접근 프레임): 닫힘 0–0.5 s front 빨강 보임 비율 0.40, 로봇 가림 0.414. 닫힘 1 s 안 손실 평균 0.57 = 로봇 가림 0.39 + 다른 변화 0.09 + 분류 안 됨 0.09; 보임 50% 미만 프레임 56%. 실내 조명 (상자 영역 밝기 비) 0.97–1.01 일정. 그림자: front 큐브 0.77, 옆 탁자 0.86; wrist 큐브 V 161 → 119. wrist 손가락 가림 ≤ 0.007.
  - 우리 판 안 tilt SD 4–5°: tilt ↔ 닫힘 2 s 전 front 큐브 밝기 ρ +0.36 (p 5e-9), 닫힘 순간 가림과 |ρ| ≤ 0.15.
- **확인 안 됨:** 레퍼런스 가시성 (영상 없음), 20–45° 기울기에서의 가림, 기울기 차가 성능 차 원인이라는 것.
- **Ablation S0–S3: 설계만 (D).**
- **근거:** `/home/user/so101_runs/main_k8/d2/grasp_pose/분석_리포트.md`, `tilt_summary.json`, `vis_summary.json`.

### E-K8-11. vision_probe 설계 + CPU 검사 (10-26 17:00–17:40)

- **목적:** 막판 좌우 교정 부족 (G_tt 0.10) 이 Vision/VLM 표현 문제인지 Action Expert 문제인지 분리.
- **가중치 동결 확인 (A, 실험설계.md A1):** d2 vs pi05_base 텐서 비교 — vision_tower 63/63 bit 동일 (최대 차 0), projector 2/2, Gemma 23/23 (표본), action expert 201 중 1 동일 (최대 차 0.02), action in/out proj · time MLP 9 중 1 (0.019). → **SigLIP·Gemma 특징 = pi05_base 특징** (d2 학습이 바꾸지 않음).
- **모델 구조 (A):** SigLIP 27층 폭 1152, 224 입력 → 256 토큰 (실제 영상 16×12 패치, 패치 1개 ≈ 원본 40 px). projector 1152→2048. Gemma 18층 폭 2048, KV head 1 × 256. expert 18층 폭 1024, 층마다 prefix K/V 를 읽음.
- **라벨 (A):** wrist 카메라는 고정 집게에 붙어 있음 (오른쪽 손가락 끝 (368, 304) px 고정). 손가락 검출 63–98% 불안정 → 라벨 = 큐브 중심 − 사람 파지 기준점 u\*(d), v\*(d) = a + b/√넓이 (잔차 u 0.43 / v 0.29 cm = "라벨 바닥"), cm 환산 √넓이/2.5 (중앙값 73.7 px/cm). roll 회전 θ = 0.91·roll − 5.5° 로 tan/rad. probe 프레임 7,810 / 256편 (큐브 있음, 테두리 안 닿음, 넓이 ≥3,000 px, 닫힘 3 s 안).
- **라벨 타당성 (A):** roll 보정 tan 이 사람의 다음 좌우 이동을 설명 R² 0.13 (0.5–1 s) / 0.32 (1–2 s) / 0.51 (2–3 s) vs 영상 좌표 선형 0.10 / 0.26 / 0.16.
- **분할 (A):** 판 단위 5-fold. Known K 쌍 (K1,K6)(K2,K7)(K3,K4)(K5,K8) = fold 0–3 test, Random k-means 5군집 = fold f. test 큐브 3 cm 안 판은 train 에서 제외 (완충). fold test 판 58/51/49/69/28. ep30 은 어느 test 에도 안 듦.
- **판정 규칙 (사전 등록, D→A):** 처음 설계 기준 (MAE ≤0.45 cm 등) → F1 CPU 기준선 뒤 "MAE ≤0.15 cm & g_rep ≥0.7 = 정확, MAE ≥0.30 또는 g_rep ≤0.4 = 부정확" 으로 다시 고정 (특징 결과 전).
- **후속 학습 계획 R0–R4 (hold-out 재학습, recovery 시연, VLM 학습, full FT): 설계만 (D).**
- **근거:** `/home/user/so101_runs/main_k8/d2/vision_probe/실험설계.md`, `labels.py`, `splits.py`, `labels_v2.csv`, `folds.json`, `split_check.json`, `label_check.json`.

### E-K8-11b. 영상 품질 부록 (10-26 17:30–17:40, CPU)

- **입력 전처리 (A, 코드 확인):** 640×480 → bilinear (antialias 없음) 224×168 → 위아래 28행 패딩 → 224×224 → ×2−1.
- **224 입력 큐브 크기 (A):** front 13×14 px (0.93 패치) start, pre1 11×12 (0.79 패치); 1 cm = 3.74 px (0.27 패치). wrist mid 51×52, pre1 61×72 px (4.36 패치); 1 cm = 17.1 (mid) – 25.0 (pre1) px (1.2–1.8 패치).
- **선명도 (A):** Laplacian 분산 front 161–402 vs wrist 5.2–6.3. 포화 0%. wrist ΔE 64–72.
- **라벨 오차 vs 품질 (A):** front Known 라벨 오차 중앙값 0.48 cm (K 배치 오차 ±0.5 포함), 품질과 |ρ| ≤ 0.16; wrist 라벨 흔들림 중앙값 0.27 cm, |ρ| ≤ 0.26.
- **학습 vs 평가 영상 (A, 평가 5판 = 10-26 try3·filt):** front 배경 V·색 학습 범위 안 (전체 V 는 3판이 2% 이하). **wrist pre3 큐브 V 5판 모두 학습 분포 7% 이하** (130.3, 129.1, 141.4, 81.0, 132.8 vs 학습 중앙값 159.3). 첫 3 s warmup 색 변화 없음.
- **가설 (C):** H1 막판 교정 부족은 wrist 해상도·조명으로 설명 어려움; H2 front 1 패치 미만 크기가 출발 방향 정밀도 제한 가능; H3 평가 wrist 큐브 어두움 = 정책 자세에 따른 그림자·시점.
- **근거:** `/home/user/so101_runs/main_k8/d2/vision_probe/실험설계_부록_영상품질.md`, `iq_summary.json`, `iq_frames.csv`.

### E-K8-12. F1 준비 + CPU 기준선 (10-26 18:00–19:10)

- **상태:** GPU 추출 **안 함** (d4 실행 중, 사용자 조건). 누출 검사 전부 통과 (판 겹침 0, train–test 최소 거리 3.01–3.09 cm). (A, `f1_결과.md`)
- **probe 방식 변경 (A):** 설계의 softmax 주의 probe 가 합성 자료에서 퇴화 → patch(점유) probe 로 교체.
- **CPU 기준선 (held-out 5-fold, test 7,779 프레임, img→rot tan MAE cm (R²)) (A):** wrist 마스크 0.042 (0.98), wrist RGB 32×24 0.085 (0.95), 점유 읽기 한계 0.051 (0.99), state 6관절+roll 0.297 (0.59), front RGB 32×24 0.540 (−0.51), 섞은 라벨 0.508. roll 없는 tab tan 은 픽셀 기준선도 R² 0.43–0.60.
- **근거:** `/home/user/so101_runs/main_k8/d2/vision_probe/f1_결과.md`, `f1_leak_check.json`, `f1_results/` (기준선 json).

### E-K8-13. F1 본실행 — SigLIP · Gemma 층 probe (10-27 09:36–12:10)

- **목적:** frozen vision/VLM 특징이 wrist 큐브 상대 좌우 위치를 담는지, 편집에 따라가는지 (g_rep), 품질 변형 영향.
- **모델:** d2 020000 (vision·Gemma = pi05_base 와 bit 동일).
- **추출 (A):** 10,111 프레임 (train 7,810 · edit 1,743 · eval 558), GPU 1,264 s; 품질 6,536 프레임 GPU 881 s. 유효: train 7,810, edit 1,727, eval 483. 결정성 최대 차 0.0. 디스크 f1_features 52 GB, f1_quality_features 34 GB. d4 SIGSTOP 09:41–10:52.
- **결과 A·B — 학습 데이터 held-out fold (판·위치 분리), wrist 상대 좌우 (img→rot tan MAE cm [CI] (R²)) (A):**
  - SigLIP L13 0.091 (0.96), **SigLIP L26 0.079 [0.075, 0.083] (0.97)**, Gemma V L0 0.080 (0.96), L3 0.086, L7 0.088, L11 0.091 (0.96), L14 0.103 (0.95), L17 0.120 (0.93). Gemma K L0 0.076, L11 0.087, L17 0.109.
  - 비교: wrist RGB 기준선 0.085, state 0.297. → 특징은 픽셀 기준선과 같은 수준, 마지막 Gemma 층에서 약간 나빠짐.
  - front 토큰으로 wrist 상대 좌우: SigLIP L26 0.401 (0.27), Gemma L11 V 0.236 (0.74), L17 V 0.275 (0.65).
  - probe 종류: mean-pool 0.092–0.167, patch 0.118–0.174 (ridge 가 가장 좋음).
- **결과 C — roll 보정 (A):** roll 없이 특징만 → tan: SigLIP · Gemma L0–L3 R² 0.59–0.63, **Gemma L7–L17 R² 0.83–0.87** (Gemma 층에서 state 토큰의 roll 과 합성되는 것으로 리포트는 기록; 메모리 요약 "Gemma mixes roll from state tokens" 는 해석 C).
- **결과 D — g_rep (편집 세트 T1 128편 닫힘 1·2 s 전 249 프레임, ±1 cm, 쌍 403개, 그 판을 본 적 없는 probe) (A):** g_tan (roll 보정) SigLIP L13 0.57, L26 0.65, **Gemma L0 V 0.72, L11 V 0.73**, L3 0.69, L7 0.66, L14 0.65, L17 V 0.59, L17 K 0.64. 기준선 wrist RGB 0.76, 마스크 0.98. front 편집에 대한 반응 0.000 (카메라 분리). **정책 행동 G_tt 0.10 [0.02, 0.20]** (exp2b, 같은 편집 방식).
- **판정 (사전 규칙 적용, A):** Gemma L0 V · L11 V 가 "표현 정확" (MAE ≤0.15 & g ≥0.7) → 규칙상 병목 = **Action Expert**. 어느 층도 "부정확" 아님. (규칙 적용 결과는 A, "병목이 expert" 라는 해석 자체는 C)
- **평가 롤아웃 프레임 (실물 10-26 try3·filt 5판, 닫힘 3 s 전~닫힘) (A):** QC 통과 303 프레임 중 150 (50%) 은 라벨이 사람 train 범위 밖 (tan 최대 19.4 cm vs train 최대 1.46). 303 전체에서는 픽셀 기준선 포함 모든 probe R² ≤ 0.02 (SigLIP L26 1.554 cm). train 범위 안 153 프레임: SigLIP L26 0.215 (0.88), Gemma L0 V 0.210 (0.88), wrist RGB 0.346 (0.68), wrist 마스크 0.457 (−0.43).
- **결과 E — 품질 변형 (A):**
  - wrist 1,000 프레임 transfer MAE: 밝기 ×0.8/×1.2 영향 거의 없음 (SigLIP L26 0.077 → 0.080 / 0.077); blur σ2 (224 기준) 0.077 → 0.120 (예측 이동 0.100 cm).
  - front 작업영역 crop 1.6× (창 안 판 197/256): front 특징으로 탁자 큐브 절대 위치 (프레임 0·30·60, 768 프레임, 평균 예측 MAE 14.66 cm): 원본 SigLIP L26 10.46 cm (x R² 0.45 / y 0.36), Gemma L11 V 6.38 (0.56/0.77), L14 V 6.27 (0.53/0.80); **crop 하면 더 나빠짐** (L14 V 8.87, SigLIP L26 12.81). 학습 표본 fold 당 약 600 프레임 · 4,096 차원.
- **한계:** 라벨 바닥 0.3–0.43 cm 인데 MAE 0.08 cm 는 라벨 정의(같은 영상 마스크 기반) 때문에 작게 나올 수 있음 — 리포트에 직접 서술 없음 (C). 편집 = 큐브 조각 옮겨 붙이기. eval 프레임은 5판뿐, 정책 상태가 train 범위 밖. front crop 은 표본 작음 (fold 당 ~200 위치). d2 020000 하나만.
- **다음:** action_bottleneck (expert 가 roll·위치를 어떻게 쓰는지).
- **근거:** `/home/user/so101_runs/main_k8/d2/vision_probe/f1_결과_본실행.md`, `f1_results/` (sig_*, kv_*, summary_features*.csv, sensitivity_A/B.json, sensitivity_baselines.json, eval_label_qc.csv, quality.json), 로그 `f1_*.log`.

### E-K8-14. action_bottleneck — Expert 가 roll·위치를 쓰는가 (10-27 13:22–15:04, 범위 경계 · 요약만)

(브리프 목록에는 없지만 10-27 이고 "특징에 있음 ≠ 정책이 씀" 을 직접 다루므로 요약. 상세는 다른 조사와 겹칠 수 있음.)
- **state 경로 (A):** roll → QUANTILES (q01 −57.01 / q99 55.16) → 256 구간 (0.438°/구간) → 숫자 한 자리씩 프롬프트 토큰 → 고정 Gemma → expert 는 prefix KV 만 읽음 (expert 입력에 state 없음).
- **학습 데이터 roll × 위치 (A):** 닫힘 1 s 전 roll 범위 −55.2…55.2°, roll 을 큐브 위치로 예측 CV R² −0.02 (위치와 무관하게 퍼짐). roll × tan 72칸 중 판 ≥5 인 칸 30. 평가 프레임 303 중 train 이웃 0개 비율 0.50.
- **같은 프레임 시각 vs 행동 (in-sample 7,810):** F1 해독값~라벨 r 0.95–0.98 인데 닫힘 0–1 s 정책 tan 기울기 0.07–0.08 vs 사람 0.18–0.19; 1–2 s 는 정책 0.45–0.47 ≈ 사람 0.41–0.42. (A)
- **요인 실험 G1 (T1 128판 × 3 단계, noise 4):** w_rot (1 = roll 반영) t2.5 −0.01 [−0.11, 0.08], t1.5 −0.09, t1.0 −0.18 → **행동이 roll 을 반영하지 않음**. G_tt 0.30 / 0.20 / 0.10. roll 토큰 가리기 (KR) 시 pan |Δ| 0.29–0.32° (효과 거의 없음), state 전체 가리기 (KS) pan |Δ| 32–37°. (A)
- **Expert hidden (A):** roll 은 층 10 이후 R² 1.00 으로 담김, img→rot tan R² 0.79–0.91 — 내부에 담지만 최종 행동이 반영 안 함 (리포트 수치; 해석 C).
- **한계 (A):** 회전 중심 미정 → C·D 기대값 가정 의존, 편집은 배경 불일치, d2 020000 만.
- **근거:** `/home/user/so101_runs/main_k8/d2/action_bottleneck/분석결과.md`, `실험설계.md`, `a1_g1.json`, `a2_g2.json`, `c3_state_path.json`, `c5_coverage.json`.

---

## 5. "특징에 위치 정보가 있다" vs "정책이 그것을 쓴다" — 무엇을, 어떤 데이터로 확인했나

| 주장 | 확인된 내용 | 데이터 | 신뢰도 |
|---|---|---|---|
| frozen SigLIP/Gemma 의 **wrist** 토큰에 큐브의 **집게 기준 상대 좌우 위치**가 선형으로 있다 | img→rot tan MAE 0.076–0.120 cm, R² 0.93–0.97 | **학습 데이터(d2 256편) 의 held-out fold** (판 분리 + 위치 hold-out + 3 cm 완충), 닫힘 3 s 안 7,779 프레임 | A |
| 위 표현이 큐브 이동을 따라간다 | g_rep 0.57–0.73 (픽셀 RGB 0.76) | 학습 판 T1 128편을 **영상 편집**한 반사실 프레임 (그 판을 안 본 probe) | A |
| **front** 특징에 큐브 **탁자 절대 위치**가 있다 | 약함~중간: Gemma L14 V MAE 6.27 cm (y R² 0.80), SigLIP L26 10.46 cm (R² 0.45/0.36); 평균 예측 14.66 cm | 학습 판 프레임 0·30·60, held-out fold, 768 프레임 | A |
| front 영상이 **출발 방향**을 정한다 | swap 계수 0.59–0.67, front 이득 start 0.85 | 학습 판 + 영상 교체/편집 (오프라인 정책 추론, 첫 chunk) | A |
| 정책이 막판 wrist 좌우 정보를 **행동에 쓴다** | **거의 안 씀**: pre 단계 G_tt 0.10 [0.02, 0.20]; front pre 이득 0.006; 닫힘 0–1 s 정책 기울기 0.07–0.08 vs 사람 0.18–0.19 | 학습 판 편집 프레임 (오프라인), in-sample 회귀 | A |
| 정책이 roll 을 공간 매핑에 쓴다 | 안 씀: w_rot ≈ 0 (−0.18…−0.01) | 학습 판 T1 128 편집 (오프라인) | A |
| 실물 평가 상태에서도 특징이 위치를 담는다 | **부분적으로만**: train 범위 안 153 프레임 SigLIP L26 0.215 cm (R² 0.88); 범위 밖 포함 303 프레임은 모든 probe R² ≤ 0.02 | 10-26 실물 try3·filt 5판 프레임 (외부 test) | A |
| "병목 = Action Expert" | 사전 규칙상 해당 (Gemma L0 V, L11 V 가 '정확') | 위 held-out 결과 + 정책 G_tt | 규칙 적용 A, 원인 단정은 C |
| 실물 성공률과의 연결 | 10-26 판정 없음 → 연결 근거 없음 | — | 미확인 |

---

## 6. 10-29 실물 롤아웃 (다른 조사 담당 — 목록만, A: `MK8/d2/eval/index.md`, `results_all.csv`)

모두 d2 `checkpoints/020000`, 과제 문장 T1.

| 시각 | tag | 저장 판 | P | F | 성공률 | 폴더 |
|---|---|---|---|---|---|---|
| 10-29 15:55 | pan_diag | 1 | 0 | 1 | 0% | `rollouts/20261029_155513_32_20000_20k_pan_diag` |
| 10-29 16:08 | pan_diag | 11 | 4 | 7 | 36% | `rollouts/20261029_160831_32_20000_20k_pan_diag` |
| 10-29 17:02 | filt_on | 4 | 2 | 2 | 50% | `rollouts/20261029_170219_32_20000_20k_filt_on` |
| 10-29 17:08 | filt_off | 4 | 3 | 1 | 75% | `rollouts/20261029_170818_32_20000_20k_filt_off` |
| 합 | | 20 | 9 | 11 | 45% | |

- 10-26 try3 · try3_filt 는 index.md / results_all.csv 에 없음 (eval_ui 가 아닌 run_rollout.sh 로 돌려서 판정 칸 없음).

---

## 7. 충돌 · 불일치 기록

1. **T3-K / T3-R 방해물 개수 표:** layout_meta.json stats (계획 생성 시점) T3-K 1개 16 · 2개 24 · 3개 24, T3-R 5개 13 · 6개 13 vs d2 description 3.3절 T3-K 17 · 23 · 24, T3-R 5개 14 · 6개 12. relabel (T3-K ep060, T3-R ep006/045/061) 반영 여부 차이로 보임 (C).
2. **d4 종료 신호:** STOP_NOTE 는 "정상 종료 요청 (SIGINT)" 인데 `.time` 은 `rc=143` (관례상 128+15 = SIGTERM). 실제 보낸 신호와 rc 관계 미확인.
3. **scheduler 값:** train_config.json 은 warmup 1000 / decay 30000 (설정값), training_params.md · description 은 실효값 666 / 20000 (자동 축소). 둘 다 맞는 기록 (설정값 vs 실효값).
4. **d2 최저 loss step:** training_params.md "최저 0.019 (step 14500)" — 로그 순서 대응으로 0.019 첫 등장 14,500 확인, 이후 19,950 까지 21회 반복 (소수 3자리 표기라 동률).
5. **try3 판 수:** 명령은 N_EP=3 인데 dataset 은 2편 (2,983 프레임). 1판이 버려졌는지 등 이유 미확인.
6. **try3_filt 시작 자세:** shoulder_lift −100.9 가 표시된 "학습 범위 −103.3 ~ −102.4" 밖인데 판정 "OK" (pose_check 허용치 미확인).
7. **"d2 가 큐브 오른쪽을 잡는다" (사용자 관찰, B) vs 분석:** grid 프로브는 오른쪽 48% (편향이 '항상 오른쪽'이 아니라 K/중앙 쪽). 실물 5판 pan_res 는 +0.4 … +52.0 으로 모두 + (로봇 오른쪽). 두 결과는 서로 다른 데이터 (실물 5판 vs 합성 grid) 이다.
8. **front 위치 정보:** 메모리 요약은 "front crop 1.6× made front abs-position probe WORSE" — 리포트 8.2 와 일치. 단 front 특징의 절대 위치 정확도 자체가 6–10 cm 수준이라 "vision features contain cube position" 은 **wrist 상대 위치에 대해서는 강하게, front 절대 위치에 대해서는 약하게** 성립.

---

## 8. 미확인/누락 목록

- 카메라를 옮기고 K1–K8 로 바꾼 **직접적인 이유** (파일에 없음).
- T2-K · T2-R 을 **녹화하지 않은 이유·결정 시점** — 파일에 기록 없음. "256 실험도 나빠서 원인 분석 먼저" 는 연구자 기억 (B) 으로만 존재.
- 10-26 try3 · try3_filt 5판의 **성공/실패 판정** — 기록 없음 (run_rollout.sh 는 판정 안 남김). 그래서 "d2 256편 실험이 나빴다" 를 수치(성공률)로 뒷받침하는 10-26 자료 없음. 10-29 에 d2 020000 로 20판 9 P (45%) 가 있으나 다른 프로토콜.
- 10-26 평가 판별 **큐브 각도**, try3 3번째 판이 저장 안 된 이유.
- eval_ui 로 계획된 `t1_eval_filt` (8판) · `t3_eval_filt` 평가 — 실행 기록 없음 (index.md 에 없음).
- **T3 과제 실물 평가** — 없음.
- **d4 실물·오프라인 평가** — 없음 (005000·010000 만 있음, 015000/020000 없음).
- d1 · d3 — 데이터 없음, 학습 없음.
- d4 를 만든 **가설** (T3-K 를 뺀 이유) — description 에 없음.
- io-capture SUMMARY (`~/io-capture/20261023-1739/`, `20261026-1420/`) 내용 — 이 조사에서 열지 않음.
- 레퍼런스(aswin) 모델 위치 민감도 프로브, grasp_pose ablation S0–S3, vision_probe 후속 학습 R0–R4 — 설계만 (D), 실행 기록 없음 (이 기간 기준).
- F1 의 라벨 바닥 (0.3–0.43 cm) 보다 probe MAE (0.08 cm) 가 훨씬 작은 이유 (라벨과 특징이 같은 영상 마스크에서 나온 영향인지) — 리포트에 명시 논의 없음.
- 10-26 평가 wrist 큐브가 학습보다 어두운 원인 (H3 그림자·시점) — 미검증.
- action_bottleneck 의 회전 중심 미정 (C·D 지표 가정 의존) — 리포트 자체 한계.
- 옛 redbox_all (K1–K4) 과 d2 의 **같은 조건 성능 비교** — 이 기간에 없음.
