# 조사 1 — 초기 단계 (2026-10-02 … 10-13): 종이 큐브 시기 ~ 나무(?) 2.5 cm 큐브 전환 직전

- 작성: 2026-11-02, 파일을 읽기만 해서 정리 (학습·GPU·로봇 명령 실행 없음, 원본 수정 없음).
- 신뢰도 표시
  - **A** = 로그·파일에 남은 측정값 (lerobot 로그, analysis.json, results.csv, train_config.json 등). P/F 판정처럼 *사람이 판정해 도구가 파일에 기록한 값*은 **A(사람판정)** 으로 따로 표시.
  - **B** = 연구자(사용자)가 실물을 보고 한 관찰이 notes/문서에 사람 말로 적힌 것.
  - **C** = 분석에서 나온 가설·해석 (Claude 가 쓴 notes 의 "→ 가설", 이 조사에서 이미지로 직접 본 것 포함 — **C(이번 조사 육안)** 으로 표시).
  - **D** = 계획.
  - 메모리 파일(`~/.claude/projects/-home-user/memory/*.md`)은 보조 근거 — **[메모리]** 로 표시, 신뢰도 낮음.
- `$HOME` = `/home/user`. 경로는 절대경로로 적음.

---

## 0. 한눈에 보기 (타임라인)

| 날짜·시각 (KST) | 실험 | 핵심 결과 | 신뢰도 |
|---|---|---|---|
| 10-02 15:59 | practice_10 녹화 (10판, 종이 큐브, 수동 카메라 156/4600) | 10판 6,589 프레임 | A |
| 10-02 16:51–18:16 | practice_10 π0.5 `pi05_2k` 학습 (full FT, bs4, 2k) | loss 0.139→0.020 | A |
| 10-06 | practice_10 오프라인 평가 (open-loop, 추론 시간, vision_check) | 팔 5관절 평균 오차 2.28–2.40°, chunk 경계 점프 최대 24.8–42.7° | A |
| 10-06 09:27–10:55 | practice_10 실물 rollout 여러 설정 | 저장된 7판 중 1판만 성공 (rtc_fast, 107초) | A / B |
| 10-06 14:14–15:05 | practice_50 녹화 (50판, 종이 큐브, 자동 카메라) | 50판 30,884 프레임 | A |
| 10-06 15:07 – 10-07 01:01 | practice_50 π0.5 `pi05_15k` 학습 (full FT, bs4, 15k) | loss 0.131→0.014 (마지막 5회 평균 0.011) | A |
| 10-07 10:36–10:48 | practice_50 15k 실물 rollout 3판 (rtc_fast) | 3/3 성공 (Claude 가 마지막 프레임으로 판정) | A |
| 10-08 10:20 등 | practice_50 15k 대화식 rollout (녹화 없음) | "문제없이 진행" (사용자) | B |
| 10-07 ~ 10-12 | E0_J_0 (π0.5 practice_50 15k 잡기 + IK 놓기, 트윈) | 정책이 쥐고 3 cm 들기 성공 다수, **종이 큐브가 조임(g−6)에 눌려 놓침 오판** 반복 | A |
| 10-12 16:55–18:02 | cubemark_v1 녹화 (50판, 큐브→X 표시, **작은 빨간 큐브**로 보임) | 50판 38,816 프레임 | A |
| 10-12 18:05 – 10-13 03:59 | cubemark `4_15000/pi05_15k` 학습 (full FT, bs4, 15k) | loss 0.095→0.011 | A |
| 10-13 09:13–10:44 | cubemark 15k 실물 rollout (판정 없음 2회, eval_ui 5판 F 후 삭제) | 판정 기록 없음 / 삭제된 5판 모두 F | A / B |
| 10-13 10:57 | practice_50 15k eval_ui 8판 (종이 큐브, 상자·큐브 배치 일부 변경) | **P 3 / F 5 (38%)** | A(사람판정) |
| 10-13 11:29–13:52 | cubemark `8_3000/pi05_expert_bs8_3k` 학습 (expert-only, vision 동결, bs8, 3k) | loss 0.095→0.037 | A |
| 10-13 13:54 | cubemark 3k eval_ui 8판 | **P 0 / F 8 (0%)** | A(사람판정) |
| 10-13 | 사용자 확인: redbox 큐브 = **2.5 cm 정육면체** ("5.3 은 practice_50 종이 큐브") | config 주석 | A(사용자 확인 기록) |
| 10-13 17:47 ~ 10-14 | redbox 파일럿 3개 (t1k / t2k / t3r, 각 4판) | 학습·평가 안 함 | A |

---

## 1. 연구자 기억 검증

연구자 기억: "처음에 빨간 종이 큐브로 ~50 데모, π0.5 파인튜닝; 공간 일반화가 나빴다; 잡을 때 종이 큐브가 찌그러졌다; 모양이 일정하지 않았다"

| 기억 | 판정 | 근거 |
|---|---|---|
| 처음에 ~50 데모 | **부분 수정** — 맨 처음은 **10 데모** (practice_10, 10-02, 학습 2k "동작 확인용, 성능 목표 아님"). 그 다음이 **50 데모** (practice_50, 10-06, 학습 15k). | `/home/user/so101_runs/practice/practice_10/notes.md:73,119`, `/home/user/so101_runs/practice/practice_50/notes.md:365-389` (A) |
| 빨간 **종이** 큐브 | **지지** — practice_10: "빨간 큐브(종이)" (사용자 관찰 문단). practice_50: "빨간 종이 큐브(≈ 53 mm)를 갈색 종이박스에 넣기". | `/home/user/so101_runs/practice/practice_10/notes.md:210`, `/home/user/so101_runs/docs/practice_10_pi05_2k.md:14,152`, `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:19` (B/A) |
| π0.5 파인튜닝 | **지지** — 두 번 모두 `lerobot/pi05_base` 에서 full fine-tune (4.14B 전부 학습). | train_config.json (A) |
| 공간 일반화가 나빴다 | **부분 지지 (명시적 측정 없음)** — 초기 단계에 "공간 일반화" 를 이름 붙여 잰 실험은 없다 (그런 평가는 10-20 `eval_space` 부터, 범위 밖). 간접 근거: ① practice_10 오프라인 평가·vision_check 는 "학습에 쓴 판이라 일반화 성능이 아님" 이라고 스스로 적음 (A/C). ② practice_10 실물: "건드려서 자리를 벗어나도 원래 자리를 보고 허우적댐" (B). ③ practice_50 10-13 평가 8판 중 3판 성공 — 시작 사진을 보면 성공 3판은 학습 분포(상자 왼쪽·큐브 오른쪽 가운데)와 비슷하고, 상자를 오른쪽으로 옮긴 판(ep006)·상자를 가로로 돌린 판(ep007)·큐브를 화면 오른쪽 끝/로봇 가까이 둔 판(ep004·ep005)이 모두 실패 (**C(이번 조사 육안)**, 판정 이유는 파일에 없음). ④ E0_J_0 보고서: "여러 큐브 위치에서의 반복 성공률(지금은 모두 기본 자리 근처)" 미확인 항목 (A). ⑤ 이후 redbox 설계의 이유: "the user wants position-generalization comparisons" ([메모리]). | `/home/user/so101_runs/practice/practice_10/notes.md:157,210,216`, `/home/user/so101_runs/practice/practice_50/eval/rollouts/20261013_105742_15k_rtc_fast/start_images/`, `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:204`, `/home/user/.claude/projects/-home-user/memory/redbox-dataset.md:131` |
| 잡을 때 종이 큐브가 찌그러졌다 | **부분 지지** — 기록된 것은 "**눌림**(압축)": E0_J_0 실행기가 넘겨준 뒤 집게를 "쥔 값 − 6" 으로 조이자 종이 큐브가 **0.4 s 사이 4.2–4.5 단위** 더 닫혀 놓침 문턱(쥔 값 − 4)을 넘음 → 놓침 오판 3–4회 (A). 단, 이 조임은 *정책이 아니라 E0_J_0 실행기 규칙*이다. lerobot rollout(정책 단독)에서 큐브가 영구적으로 찌그러졌다는 기록은 **미확인**. "큐브가 찌그러지거나…" 는 D_real_checklist 의 *정지 조건 예시*(계획/주의)일 뿐 관찰 기록이 아님 (D). 사용자 평가: "학습할 때 잡는 세기를 잘 조절해야 할 것 같음" (B). | `/home/user/so101_runs/e0_j0/experiment_log.md:501-502,546`, `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:62,137,198`, `/home/user/so101_runs/e0_j0/runs/notes.md:24,31`, `/home/user/so101_runs/e0_j0/D_real_checklist.md:268`, `/home/user/so101_runs/docs/practice_10_pi05_2k.md:25` |
| 모양이 일정하지 않았다 | **미확인** — 텍스트 기록 없음. 간접: E0_J_0 실물에서 쥔 집게 값이 시도마다 크게 다름 (10-08: 30.3, 32.1, 42.7, 33.7, 33.4, 33.0, 32.1 / 10-12: 49.1, 47.9, 24.8, 31.4, 21.2) (A) — 큐브 모양 때문인지, 대각선·모서리 잡기 때문인지는 기록 없음 (보고서는 42.7 을 "[추정] 실제로 빠졌거나 모서리 잡기" 로만 씀). 10-13 시작 사진에서 종이 큐브 모서리에 흰 종이 단면이 보임 — 변형 여부는 판단 불가 (C(이번 조사 육안)). | `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:60-71`, `/home/user/so101_runs/e0_j0/runs/index.md` |
| (추가) 종이 큐브가 너무 가벼워 밀림 | **지지 (기억에는 없던 항목)** — 사용자 평가 "빨간색 박스[=큐브]가 너무 가벼워서 위치를 벗어나는 바람에 잡는 데 어려움이 있음", "종이 큐브가 밀리면 다시 잡지 못한다". | `/home/user/so101_runs/docs/practice_10_pi05_2k.md:14,23,152` (B) |

---

## 2. 실험별 상세

### E01. practice_10 녹화 (cubebox, 10판)

| 필드 | 내용 |
|---|---|
| 실험 ID | `practice/practice_10` 녹화 (run 20261002_155718 실패, 20261002_155906 정상) |
| 날짜 | 2026-10-02 15:57 (첫 시도 비정상 종료 코드 1, 0판) → 15:59 녹화, 후처리 16:07 (A) |
| 목적 | 첫 연습 수집. 학습→실물 실행이 끝까지 도는지 보기 위한 데이터 (docs: "성능이 아니라 학습 → 실물 실행까지 끝까지 도는지 확인") |
| 데이터셋 | 경로 `/home/user/so101_runs/practice/practice_10/dataset`, repo_id `oxr/so101_cubebox_practice10`, **10판, 6,589 프레임**, 판당 17.4–29.3 s (평균 22.0 s), 30 fps (A) |
| 과제 문장 | "pick up the red cube and put it in the brown box" |
| 큐브 | 빨간 **종이** 큐브 (notes:210 사용자 관찰 문단 "빨간 큐브(종이)") (B). 크기 기록 없음 — practice_50 과 같은 큐브인지 명시 기록 없음 (미확인). 화면에서는 노랗고 초록빛 색조 때문에 주황빛으로 보임 (C(이번 조사 육안) `qa/overview_front_first.jpg`) |
| 카메라 | front·wrist 640×480 MJPG 30fps, **수동 노출 156 / WB 4600** (카메라 기본값, 노랗고 초록빛, 흰 탁자 B/G front 0.50–0.51, wrist 0.53–0.57). 이후 세션은 자동 노출·자동 WB 로 바꿈 (A) |
| 로봇 설정 | P=16 I=0 D=32, max_relative_target=None, use_degrees=True, episode_time_s=30, reset_time_s=120 (A) |
| 배치 | 상자 위치 고정, 큐브 시작 위치·각도는 판마다 다름 (front 화면 오른쪽 절반). 큐브 시작 위치 흩어짐 평균 55 px (자동 추정). ep002·005 는 큐브가 화면 오른쪽 끝에 걸침 (A / 육안 QA) |
| QA 결과 | NaN 0, 영상·데이터 프레임 일치. "학습에 써도 되는 판" 5개 (001,004,007,008,009), 확인 필요 5개 (시작 정지 3.5–5.5 s, 큐브가 화면 끝에 걸침). 학습에는 **10판 전부 사용** (A) |
| 근거 | `/home/user/so101_runs/practice/practice_10/notes.md:10-116`, `/home/user/so101_runs/practice/practice_10/qa_report.md:1-367`, `/home/user/so101_runs/practice/practice_10/qa/overview_front_first.jpg` |

### E02. practice_10 π0.5 학습 `pi05_2k`

| 필드 | 내용 |
|---|---|
| 실험 ID | `practice/practice_10/train/pi05_2k` |
| 날짜 | 2026-10-02 16:51:31 – 18:16:34 (1시간 25분; 학습 1시간 20분 36초, 2.36 s/step) (A) |
| 목적 | "π0.5 연습 학습 (동작 확인용, 성능 목표 아님)" |
| 체크포인트 | `/home/user/so101_runs/practice/practice_10/train/pi05_2k/checkpoints/002000` (`last`→002000), 23 GB (A) |
| 학습 설정 (train_config.json 확인) | policy pi05, pretrained `lerobot/pi05_base`, **dtype bfloat16**, gradient_checkpointing true, **freeze_vision_encoder False, train_expert_only False** (4,143,404,816 파라미터 전부 학습), batch 4, steps 2000, seed 1000, num_workers 4, optimizer AdamW lr 2.5e-5 betas [0.9,0.95] wd 0.01 grad clip 1.0, scheduler cosine_decay_with_warmup — 설정값 warmup 1000 / decay 30000 이지만 lerobot 이 **자동 축소: warmup 66, decay 2000** (peak 2.5e-5 → 2.5e-6), chunk_size 50, n_action_steps 50, num_inference_steps 10, image 224×224, 정규화 STATE·ACTION QUANTILES / VISUAL IDENTITY, 이미지 증강 끔, use_peft False (A) |
| 학습량 | 2000 × 4 = 8,000 샘플 ≈ 1.21 epoch (A) |
| 정량 결과 | loss step 50 0.139 → 100 0.076 → 250 0.053 → 500 0.040 → 1000 0.034 → 2000 0.020 (처음 5회 평균 0.080, 마지막 5회 평균 0.020) (A). 메모리 lerobot mem_gb 36.99, nvidia-smi 최대 39.3 GB, 시스템 최대 66 GB (A) |
| 근거 | `/home/user/so101_runs/practice/practice_10/train/run_pi05_2k.sh`, `/home/user/so101_runs/practice/practice_10/train/pi05_2k.log:200` (Auto-scaling 줄), `/home/user/so101_runs/practice/practice_10/train/pi05_2k/checkpoints/002000/pretrained_model/train_config.json`, `/home/user/so101_runs/practice/practice_10/notes.md:119-151` |

### E03. practice_10 오프라인 평가 (팔 연결 없음)

| 필드 | 내용 |
|---|---|
| 날짜 | 2026-10-06 |
| 목적 | 체크포인트가 녹화 동작을 따라 하는지, 추론 시간이 30 Hz 실행에 맞는지, 정책이 화면을 쓰는지 확인 |
| 방법 | ① `eval/offline_eval_pi05_2k.py`: ep001·ep004 (둘 다 **학습에 쓴 판**) 에서 50프레임마다 녹화 관측 → chunk(50) → 이어 붙여 녹화 action 과 비교 (open-loop, lerobot-rollout sync 경로와 같은 전처리, bf16, seed 0). ② `rtc_timing_pi05_2k.py`, `steps_timing.py`: 추론 시간. ③ `vision_check.py`: 움직임 시작 순간 화면만 회색/다른 판 화면으로 바꿔 예측 비교. ④ `camera_check.py`: rollout 프레임 반복·색 점검 |
| 정량 결과 (A) | 관절별 평균 오차 (°, gripper 0–100; 괄호 = "chunk 시작 자세 유지" 기준선): ep001 pan 2.59 (7.77), lift 2.63 (5.91), elbow 2.87 (6.28), w_flex 0.42 (0.69), w_roll 3.48 (6.72), gripper 1.73 (4.99), 팔 5관절 2.40 / ep004 pan 2.29 (11.77), lift 2.05 (11.81), elbow 2.31 (6.59), w_flex 0.73 (1.34), w_roll 4.01 (5.62), gripper 2.26 (8.13), 팔 5관절 2.28. chunk 첫 스텝 ≈0.9° → 50번째 3–4°. 최대 오차 wrist_roll 46°(ep1)·40°(ep4), shoulder_lift 22–32°. **chunk 경계 점프** ep1 최대 24.8°, ep4 36.4°·42.7° (녹화 action p99 2.6–3.8°/frame) |
| 추론 시간 (A) | sync 10단계: 평균 212.8 ms, p95 220.4, 최대 229.9 (첫 호출 698 ms, GPU 9.5 GB). guided RTC 10단계: 평균 308.5 ms, 최대 329.1 (첫 호출 717 ms). steps_timing: 10단계 sync 225 / RTC 324 ms, 오차 2.61° ; **5단계 sync 161 / RTC 208 ms, 오차 2.39°** → "5단계로 줄여도 정확도 손해 없음" |
| vision_check (A) | 움직임 시작 시 팔 자세 퍼짐 pan 3.6°; 회색 화면 → pan 예측 30.3° 바뀜, 다른 판 화면 → 21° 바뀜 (판 사이 실제 차이 18.9°), 다른 판 화면을 넣으면 pan 예측이 그 판 쪽으로 가는 비율 63%. 해석: "화면을 보고 방향을 정함 (단, 학습에 쓴 판이라 처음 보는 위치에 대한 일반화는 아님)" (C) |
| 30 Hz 판단 (C) | 추론 ≈213 ms = 루프 예산 33.3 ms 의 6.4배 → sync 에서 1.67 s 마다 ≈0.21 s 멈칫, chunk 경계 점프와 겹쳐 큰 이동 가능 → RTC + horizon 20 + max_relative_target 권장 |
| 한계 | 학습에 쓴 판만 평가 (일반화 아님) — 문서 스스로 명시 |
| 근거 | `/home/user/so101_runs/practice/practice_10/notes.md:153-181,209-223`, `/home/user/so101_runs/practice/practice_10/eval/pi05_2k_offline.json`, `/home/user/so101_runs/practice/practice_10/eval/vision_check.json`, `/home/user/so101_runs/practice/practice_10/eval/steps_timing.json`, `/home/user/so101_runs/practice/practice_10/eval/pi05_2k_rtc_timing.json`, `/home/user/so101_runs/docs/practice_10_pi05_2k.md:60-90` |

### E04. practice_10 실물 rollout (pi05_2k, 10-06)

| 필드 | 내용 |
|---|---|
| 날짜 | 2026-10-06 09:27 – 10:55 |
| 목적 | 학습한 정책이 실물에서 끝까지 도는지; 흔들림 원인; 추론 방식 비교 |
| 평가 환경 | `lerobot-rollout` (0.6.2) — 09:27 대화식, 이후 `eval/run_rollout.sh` (episodic 녹화 + DEBUG 로그 + 자동 분석). 공통 max_relative_target 8, 30 Hz, 카메라 수동 156/4600 (학습과 같게). 큐브 위치: 기록 없음 (start_end_front.jpg 만) |
| 실행 표 (A, 결과 칸 일부 B) | 09:27 대화식 RTC h20, 20 s, 녹화 없음 → "약간 흔들흔들"(B) / 09:42–09:51 3회 repo 이름 규칙(`rollout_` 접두어)으로 시작 실패 / 09:56 rtc_h20 q30 → Ctrl+C 로 0판 저장 / 10:00 **sync** 20 s×2 → 2판 못 넣음 / 10:04 **rtc_h20_q20** 20 s×2 → 2판 못 넣음 ("큐브 위에서 그리퍼만 여닫음") / 10:16 **rtc_h20** 45 s×2 → 2판 못 넣음 ("2판째 시작 때 상자 위치 바뀜") / 10:39 rtc_fast 45 s → 리셋 중 종료로 0판 / 10:49 **rtc_fast** (flow 5단계, RTC h20, queue 40, 시간 제한 없음) → **1판 107초에 큐브 상자 안**, 2판째 0프레임 에러 |
| 정량 결과 | **저장된 7판 중 성공 1판** (docs "7번 실행해 1번") (A; 성공 판단 근거는 start_end_front.jpg — 판정자 명시 없음). RTC 실측 지연: rtc_h20_q20 평균 494/최대 520 ms, rtc_h20 497/570 ms, rtc_fast 318/370 ms (A, analysis.json). 8° 제한 경고: sync 41, q20 97, rtc_h20 426, rtc_fast 107 (A). 흔들림 (state 방향 바뀜 pan / w_roll, 회/초): 사람 0.16/0.12, sync 0.27/0.36, q20 0.42/0.50, rtc_h20 0.85/0.82, **rtc_fast 0.23/0.54**; 고주파 pan/gripper: 사람 0.20/0.33, rtc_fast 0.16/0.37 (A) |
| 정성 관찰 (B) | 사용자 평가 (docs:16-30): "빨간색 박스[=큐브]라는 것을 인지하고 있음", "빨간색 박스를 잡으면 갈색 박스에 넣는 것은 잘함". 제한: "**너무 가벼워서 위치를 벗어나는 바람에 잡는 데 어려움**", "집는 데까지 시간이 걸리기 때문에 시간 제한을 두면 안 됨", "**학습할 때 잡는 세기를 잘 조절해야 할 것 같음**". notes:210 "빨간 큐브(종이)를 인지는 하는데 반응이 느림. 건드려서 자리를 벗어나도 원래 자리를 보고 허우적댐" |
| 실패 사례 (A/C) | rtc_h20_q20 ep0: 2.5 s 부터 wrist 화면에 큐브가 손가락 사이에 있는데 그리퍼가 24–55 사이를 여닫기만 함. 팔이 덜 내려감: lift 15–27·elbow −12~−22 vs 학습 때 잡는 순간 lift 38–46·elbow −36~−42 (A). 시작 자세가 학습 시작 평균과 다름 ([pan 80–83, lift −7…−5, elbow 49–51, w_flex 63–64, roll 25] vs [75, 43, 6, 98, 1.5]) (A) — 이후 사용자 판단으로 "평가에 상관없음" 처리 |
| 가설 (C) | 흔들림 크기는 chunk 전환에서, 잔떨림은 정책 출력 자체(pan·wrist_roll ~2회/초)에서 옴; 흔들림 주기 = chunk 전환 주기 (sync 50프레임, q20 30프레임). 반응 지연 계산: RTC q30 0.5–1.2 s, q20 0.5–1.5 s, sync 0–1.7 s, rtc_fast 0.3–0.7 s 전 화면으로 만든 동작 → "종이 큐브가 밀려도 이 시간 동안은 원래 자리로 가는 계획을 계속 실행". "데이터가 10판뿐인 게 가장 큰 원인으로 보인다" |
| 한계 | 판 길이·판 수가 설정마다 달라 비교가 엄밀하지 않음 (문서 스스로 명시); rtc_fast 는 1판뿐 |
| 다음으로 이어진 이유 (D) | 다음 할 일: rtc_fast 로 더 돌리기; **데이터 늘리기 — 큐브 위치 더 다양하게, 밀린 큐브 다시 잡는 장면, 끝까지 내려가 잡는 장면, 수십 판 단위로 재학습**; 이후 세션은 자동 노출·WB → practice_50 으로 이어짐 |
| 근거 | `/home/user/so101_runs/practice/practice_10/notes.md:183-228`, `/home/user/so101_runs/docs/practice_10_pi05_2k.md:8-30,92-174`, `/home/user/so101_runs/practice/practice_10/eval/rollouts/*/analysis.json`, `/home/user/so101_runs/practice/practice_10/eval/rollout_pi05_2k_20261006_092753.log` |

### E05. practice_50 녹화 (cubebox, 50판)

| 필드 | 내용 |
|---|---|
| 실험 ID | `practice/practice_50` (run 20261006_141453 새 녹화 20판 → 143454 이어 찍기 20판 → 145732 이어 찍기 10판). 14:02 / 14:07 / 14:12 의 "새 녹화" 3회(1·2·1판)는 14:14 새 녹화로 대체된 것으로 보임 (C — notes 에 각 결과 표가 남아 있으나 최종 데이터셋은 0–49 = 14:14·14:34·14:57 세 번) |
| 날짜 | 2026-10-06 14:14 – 15:05 (A) |
| 목적 | practice_10 의 "데이터 늘리기" 다음 단계 (명시 목적 문장은 notes 에 없음 — practice_10 docs §6 "수십 판 단위로 모아서 다시 학습" 과 이어짐) |
| 데이터셋 | `/home/user/so101_runs/practice/practice_50/dataset`, repo_id `oxr/so101_cubebox_practice50`, **50판, 30,884 프레임** (17.2분), 14.0–26.6 s (평균 20.6 s), 274 MB (A) |
| 과제 문장 | "pick up the red cube and put it in the brown box" |
| 큐브 | 빨간 **종이 큐브 ≈ 53 mm** (보고서 표현). 단 **53 mm 는 자로 잰 값이 아니라** 쥔 집게 값 중앙값 32.4 (experiment_log 에는 31.9) ↔ Thor 집게 표 53 mm = 31.4 로 역산한 값 (C/A). 박사님 main 브랜치도 "운영 큐브 = 실물 53 mm" (ros2_guide). 2026-10-13 config 주석 "5.3 은 practice_50 종이 큐브" (사용자 확인 시점 기록) |
| 카메라 | front·wrist 640×480 MJPG 30 fps, **자동 노출 3 / 자동 WB 1 / exposure_dynamic_framerate 0** (녹화 전 점검 기록) (A) |
| 로봇 설정 | P16 I0 D32, max_relative_target None, episode_time_s 45 (마지막 10판 60), reset 120 (A) |
| 의도된 변형 | ep040·041·042 = **빗잡기(의도)** (판별 메모, 사람 입력) (B) |
| 배치 | 상자는 왼쪽 고정, 큐브는 front 화면 오른쪽 절반에서 위치·각도 다양 (C(이번 조사 육안) `qa/overview_front_first.jpg`). QA 자동 추정 "큐브 시작 위치 흩어짐 평균 117 px" 은 **신뢰 불가** — 옛 빨강 HSV 규칙이 갈색 상자 벽을 큐브로 잡음 ([메모리] redbox-dataset.md: "the old one detected the brown box wall as the cube in practice_50"; 실제로 qa 표에 (265,118) 같은 상자 안 좌표가 다수) |
| QA | NaN 0, 프레임 일치. 자동 판정 "학습에 써도 되는 판" 30, 확인 필요 20 (시작 |s−a| 5–10°, 정지 3–6 s, 박스 자리 다름 5판, 14 s 짧은 판 2) — "육안 확인 칸이 아직 비어 있다". 학습에는 **50판 전부 사용** (notes:367 "50편 전부 사용") (A) |
| 근거 | `/home/user/so101_runs/practice/practice_50/notes.md:16-360`, `/home/user/so101_runs/practice/practice_50/qa_report.md:1-360`, `/home/user/so101_runs/practice/practice_50/qa/overview_front_first.jpg`, `/home/user/so101_runs/e0_j0/design.md:143,308`, `/home/user/so101_runs/e0_j0/experiment_log.md:44` |

### E06. practice_50 π0.5 학습 `pi05_15k`

| 필드 | 내용 |
|---|---|
| 실험 ID | `practice/practice_50/train/pi05_15k` |
| 날짜 | 2026-10-06 15:07:41 – 10-07 01:01:46 (9시간 54분; 학습 9시간 51분 07초, 2.36 s/step) (A) |
| 체크포인트 | `/home/user/so101_runs/practice/practice_50/train/pi05_15k/checkpoints/{005000,010000,015000}` (`last`→015000), 각 23 GB. 이후 모든 평가·E0_J_0 은 **015000** (A) |
| 학습 설정 (train_config.json + training_params.md 확인) | pi05, `lerobot/pi05_base`, **bfloat16**, gradient_checkpointing True, **freeze_vision_encoder False, train_expert_only False, use_peft False** (4,143,404,816 전부), batch 4, grad accum 1, GPU 1, steps 15000, save_freq 5000, seed 1000, num_workers 4, AdamW lr 2.5e-5 (끝 2.5e-6), betas [0.9,0.95], eps 1e-8, wd 0.01, grad clip 1.0, cosine_decay_with_warmup **warmup 500, decay 15000** (설정 1000/30000 → 자동 축소, 로그 200행), chunk 50 / n_action_steps 50, num_inference_steps 10, 224×224, 이미지 증강 끔 (A) |
| 학습량 | 15000 × 4 = 60,000 샘플 ≈ **1.94 epoch** (A) |
| 정량 결과 | loss step 50 0.131 → 100 0.077 → 500 0.046 → 1000 0.040 → 2000 0.030 → 5000 0.027 → 7500 0.016 → 10000 0.018 → 12500 0.010 → 15000 0.014; 구간 평균 0–1k 0.055 · 1k–2.5k 0.034 · 2.5k–5k 0.027 · 5k–7.5k 0.022 · 7.5k–10k 0.016 · 10k–12.5k 0.014 · 12.5k–15k 0.012; 처음 5회 평균 0.081, 마지막 5회 평균 0.011, 최저 0.009 @13000; grad norm 3.4 → 0.4–0.5 (A) |
| 메모리 | lerobot mem_gb 36.99; nvidia-smi 프로세스 **39.3 GB (notes) vs 38.4 GB (training_params.md)** — 충돌, §5 참고; 시스템 최대 ≈65 GB (65.4) (A) |
| 근거 | `/home/user/so101_runs/practice/practice_50/train/run_pi05_15k.sh`, `/home/user/so101_runs/practice/practice_50/train/pi05_15k.log:200`, `/home/user/so101_runs/practice/practice_50/train/pi05_15k/training_params.md:1-52`, `/home/user/so101_runs/practice/practice_50/train/pi05_15k/checkpoints/015000/pretrained_model/train_config.json`, `/home/user/so101_runs/practice/practice_50/notes.md:365-405` |

### E07. practice_50 15k 실물 rollout — 10-07 녹화 3판, 10-08~10-13 대화식

| 필드 | 내용 |
|---|---|
| 날짜 | 10-07 10:36 / 10:41 / 10:44 (episodic, 각 1판), 대화식 로그 10-08 10:20, 10-08 16:12, 10-12 16:18·16:24, 10-13 09:29 |
| 평가 환경 | `run_rollout.sh rtc_fast` = `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40`, max_relative_target 8, 30 fps (A, command.txt). 대화식(base 전략)은 RTC, 45 s 등. 필터 없음. 큐브 위치 기록 없음 |
| 정량 결과 | 10-07: 판 길이 1020 / 783 / 787 프레임 (34.0 / 26.1 / 26.2 s); RTC 지연 평균 316.3 / 315.3 / 316.8 ms, 최대 350–370 ms; 8° 제한 경고 84 / 114 / 108; 첫 추론 대기 22–23틱 (A, analysis.json). **3/3 성공** — 보고서: "[측정] 앞 카메라 마지막 프레임에서 큐브가 박스 안. 쥠 7.3–9.7 s, 박스 쪽에서 다시 엶 10.4–12.6 s" (A, 판정자 = Claude 분석). eval/index.md·results_all.csv 에는 이 3판이 없음 (eval_ui 는 10-13 에 생김) |
| 정성 관찰 (B) | 10-08 10:20–10:27 대화식 4회 (45 s×3 + 32 s, 녹화 없음): "[사용자 관찰] 문제없이 진행" (`report_for_dr_lee.md:31`). 10-08 16:12 / 10-12 16:18·16:24 / 10-13 09:29 대화식 로그: cadence 만 있고 결과 기록 **없음** |
| 근거 | `/home/user/so101_runs/practice/practice_50/eval/rollouts/20261007_{103612,104105,104451}_15k_rtc_fast/`, `/home/user/so101_runs/practice/practice_50/eval/rollout_today_20261008_102000.log`, `/home/user/so101_runs/practice/practice_50/eval/rollout_2026101{2,3}_*.log`, `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:27-34` |

### E08. practice_50 15k eval_ui 평가 (10-13, P 3 / F 5)

| 필드 | 내용 |
|---|---|
| 실험 ID | `practice/practice_50/eval/rollouts/20261013_105742_15k_rtc_fast` |
| 날짜 | 2026-10-13 10:57 – 11:08 |
| 평가 환경 | `eval_ui.py` (episodic, 판마다 시작 사진, 사람이 P/F 판정), ckpt 015000, rtc_fast (flow 5단계, RTC h20, queue 40), max_relative_target 8, 필터 없음. 과제 문장 그대로. 큐브 = **종이 큐브 (큰 큐브)** (C(이번 조사 육안) start_images) |
| 정량 결과 | 저장 8판, **P 3 / F 5 = 38%** (ep000 P 21.8 s, ep001 F 29.0, ep002 P 18.4, ep003 P 22.5, ep004 F 14.0, ep005 F 30.4, ep006 F 31.8, ep007 F 26.5). 8° 제한 경고 549회, RTC 지연 평균 320.3 / 최대 380 ms, 첫 추론 대기 합 94틱 (A(사람판정) results.csv / A analysis.json) |
| 메모 칸 | 비어 있음 — 실패 이유 기록 없음 (미확인) |
| 시작 배치 (C(이번 조사 육안)) | 학습 때(상자 왼쪽 위 x≈157–344, y≈88–403) 와 달리 상자가 아래쪽(y≈155–470)으로 옮겨져 있음. ep000·002·003(P): 상자 왼쪽, 큐브 오른쪽 가운데 — 학습과 비슷. ep001(F): 큐브 오른쪽 ≈30° 회전. ep004(F): 큐브 화면 오른쪽 끝. ep005(F): 큐브 오른쪽 아래(로봇 가까이). **ep006(F): 상자를 화면 오른쪽으로, 큐브를 가운데 왼쪽으로 — 학습에 없는 배치**. **ep007(F): 상자를 오른쪽 위에 가로로 돌려 둠 — 학습에 없는 배치** |
| 해석 | 10-07 의 3/3 과 10-13 의 3/8 차이는 배치 변화(상자·큐브 위치)와 겹침 (C). 10-13 은 같은 날 오전 cubemark 평가 직후, 상자 재배치가 있던 날 (redbox config: "2026-10-13: 상자를 로봇 정면…으로 옮겼다") — 단 이 8판의 배치를 바꾼 의도는 기록 없음 (미확인) |
| 근거 | `/home/user/so101_runs/practice/practice_50/eval/index.md:7`, `/home/user/so101_runs/practice/practice_50/eval/results_all.csv`, `/home/user/so101_runs/practice/practice_50/eval/rollouts/20261013_105742_15k_rtc_fast/results.md`, `.../analysis.json`, `.../start_images/ep00{0-7}_front.png` |

### E09. E0_J_0 — practice_50 π0.5 잡기 + 트윈 IK 놓기 (10-06 ~ 10-12) — 잡기 성능·종이 큐브 관련만

| 필드 | 내용 |
|---|---|
| 목적 | arm-jetson 트윈에 정책 실행기(E1)가 없어, π0.5 (practice_50 015000) 로 잡고 E0-lite IK 로 옮겨 놓는 시제품 (A) |
| 정책·환경 | practice_50 ckpt 015000, 정책 서버(호스트, lerobot RTCInferenceEngine 과 같은 순서), 매 틱 ±8 클립, 집게 [0,100] 묶기, P16, 속도 천장 0.5 rad/s, 가속 5 rad/s². 장면: "학습 때처럼 흰 탁자, 갈색 박스 왼쪽, 빨간 큐브(53 mm) 오른쪽 앞" (D_real_checklist:43) — **"모두 기본 자리 근처"** (보고서 3-3) |
| 큐브 크기 근거 | practice_50 쥔 집게 값 중앙값 32.4 (p5 25.4) ↔ Thor 집게 표 53 mm = 31.4 → "큐브는 약 53 mm" (design §2-3, §3-6). experiment_log 설정표에는 중앙값 31.9 로 적힘 (충돌, §5). 조작자는 큐브 폭까지만 닫음(명령 중앙값 31.3, "꽉 쥐지 않음"), P16 에서 "쥐는 힘이 약하다(데이터도 그렇다)" (C) |
| 10-08 실물 ③a/③b (A) | 6회 ③a 시도 중 정책이 쥐고 3 cm 들어 넘겨주기까지 **5/5** (정책이 돈 시도 기준), 12 s 버티기·내려놓기 완주 **1/6**. 실패: 놓침 **오판 3** (조임에 종이 큐브 눌림: 26.1≤26.3, 27.6≤28.1, 28.7≤29.4), 실제 빠짐 추정 1 (집게 42.7→25.9, "[추정] 실제로 빠졌거나 모서리 잡기"), LINK stale 1. ③b: 탁자1 DONE 1 (15:53), 박스 1회 사람 개입 중단, 탁자1 1회 "정책이 40 s 안에 쥐지 못함(상태 search)". 쥔 값 g: 30.3 / 32.1 / 42.7 / 33.7 / 33.4 / 33.0 / 32.1 |
| 종이 큐브 눌림 (A + C) | "종이 큐브가 조임(쥔 값 − 6)에 눌려 0.4 s 사이 4.2–4.5 단위 닫혔고, 문턱(쥔 값 − 4)을 지났습니다. 큐브가 빠진 것이 아닙니다 (목표 26.1, 측정 27.6 = 막혀 1.5 단위 앞에서 정지)". 버티기 중 집게 Present_Load **21.6 %** (Overload_Torque 25 % 근접). 4.2 분 쥔 뒤 LINK stale = 집게 과부하 보호 "추정, 미확정". 보고서 결론: "조임·놓침 규칙은 **큐브 재질과 함께** 정해야 합니다" |
| 10-12 실물 (A) | backend real 7회: 09:56 DONE (g 49.1), 09:59 쥠 뒤 취소 → 40 s 안에 넘겨주기 없음 (g 47.9, search), 10:02 DONE (g 24.8), **15:46 ③a 놓침 오판 재발** (쥔 31.4 → 조임 25.4 → 26.9 ≤ 27.4; "사용자: 큐브는 놓치지 않았다" (B)), 16:10 DONE (살포시 놓기, g 31.4, 접촉 −6 mm), 16:11 쥠(g 21.2) 뒤 취소 → 실패 (hold), 16:14 쥐지 못함 (search). → **3 DONE / 7** (이 조사에서 jsonl 집계). "이 종이 큐브로는 위치만 보고 놓침을 가를 수 없습니다 → --slip-log" |
| 근거 | `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:15-85,189-212`, `/home/user/so101_runs/e0_j0/experiment_log.md:36-56,480-556`, `/home/user/so101_runs/e0_j0/design.md:137-160,306-312`, `/home/user/so101_runs/e0_j0/runs/index.md`, `/home/user/so101_runs/e0_j0/runs/notes.md:24,31`, `/home/user/so101_runs/e0_j0/runs/trial_20261012_*.jsonl`, `/home/user/so101_runs/e0_j0/D_real_checklist.md:43,170,256,268` |

### E10. cubemark_v1 녹화 (큐브 → X 표시, 50판)

| 필드 | 내용 |
|---|---|
| 실험 ID | `main/cubemark_v1` (run 20261012_165535 20판·버림 10, 173049 이어 20판·버림 7, 175408 이어 10판) |
| 날짜 | 2026-10-12 16:55 – 18:02 (setup 사진 `setup_front_20261012_1450.png`, 파일 시각 14:55) (A) |
| 목적 | 새 과제 "큐브를 X 표시에 놓기" — 목적·이유 문장은 notes 에 없음 (미확인). X 표시는 판마다 위치를 바꿈 (A) |
| 데이터셋 | `/home/user/so101_runs/main/cubemark_v1/dataset`, repo_id `oxr/so101_cubemark_v1`, **50판, 38,816 프레임** (21.6분), 17.3–37.6 s (평균 25.9 s), 335 MB (A) |
| 과제 문장 | "Pick up the red cube and place it on the X mark." |
| 큐브 | notes 에는 "빨간 큐브" 만 — 크기·재질 기록 없음 (미확인). 화면상 practice_50 종이 큐브보다 훨씬 작고 진한 빨강 — redbox 파일럿 사진의 큐브와 같은 종류로 보임 (C(이번 조사 육안) `qa/overview_front_first.jpg`, `setup_photos/setup_front_20261012_1450.png`) |
| 카메라 | 자동 노출·자동 WB (3/1/0), 640×480 MJPG 30 fps. 화면 구도는 practice_50 과 다름 — 로봇이 화면 오른쪽 아래에 보이고 상자 없음 (C(이번 조사 육안)) |
| 의도된 변형 | ep040·041 = 놓침 → 다시 집기(의도), ep042·043 = 잘못 둠 → 다시 옮기기(의도); ep049 시작 |s−a| 21.5° 그대로 사용 (B/A) |
| QA | 50판 모두 학습 사용. 자동 판정 "박스" 경고는 이전 과제 기준이라 무관 (notes:265). 큐브 시작 위치 흩어짐 평균 125 px (자동) (A) |
| 근거 | `/home/user/so101_runs/main/cubemark_v1/notes.md:1-266`, `/home/user/so101_runs/main/cubemark_v1/qa_report.md`, `/home/user/so101_runs/main/cubemark_v1/qa/overview_front_first.jpg` |

### E11. cubemark π0.5 학습 `4_15000/pi05_15k`

| 필드 | 내용 |
|---|---|
| 날짜 | 2026-10-12 18:05:05 – 10-13 03:59:11 (9시간 54분, 2.36 s/step) (A) |
| 체크포인트 | `/home/user/so101_runs/main/cubemark_v1/train/4_15000/pi05_15k/checkpoints/{005000,010000,015000}` (10-13 에 `train/pi05_15k` 에서 폴더 이동) |
| 학습 설정 (train_config.json 확인) | practice_50 pi05_15k 와 같은 레시피: pi05_base, bf16, grad ckpt, **freeze_vision_encoder False, train_expert_only False**, batch 4, steps 15000, lr 2.5e-5→2.5e-6 cosine, warmup 500 / decay 15000 (자동 축소), seed 1000, 증강 끔, chunk 50 (A) |
| 학습량 | 60,000 샘플 ≈ **1.55 epoch** (A) |
| 정량 결과 | loss 50 0.095 → 100 0.069 → 500 0.052 → 1000 0.039 → 2000 0.028 → 5000 0.019 → 7500 0.019 → 10000 0.013 → 12500 0.011 → 15000 0.011; 구간 평균 0–1k 0.050 … 12.5k–15k 0.010; 처음 5회 0.068, 마지막 5회 0.011, 최저 0.008 @12300; grad norm 2.1 → 0.43–0.46; GPU 39.3 GB, 시스템 최대 ≈68 GB (A) |
| 근거 | `/home/user/so101_runs/main/cubemark_v1/notes.md:261-293`, `/home/user/so101_runs/main/cubemark_v1/train/4_15000/run_pi05_15k.sh`, `/home/user/so101_runs/main/cubemark_v1/train/4_15000/pi05_15k/training_params.md`, `.../checkpoints/015000/pretrained_model/train_config.json` |

### E12. cubemark 15k 실물 rollout (10-13 오전)

| 필드 | 내용 |
|---|---|
| 날짜 | 10-13 09:13, 09:18 (run_rollout.sh rtc_fast, episodic), 09:40–09:55 대화식 5개 로그, 10:32·10:44 eval_ui (삭제됨) |
| 평가 환경 | ckpt 015000, flow 5단계, RTC h20, queue 40, max_relative_target 8 (A, console argv). 시작 자세 pose_check OK (학습 시작 범위 안) |
| 정량 결과 | 09:13: 1판 2025 프레임 (67.5 s), 8° 제한 경고 0, RTC 평균 312.1 ms. 09:18: 1판 **6820 프레임 (227 s)**, 경고 439, RTC 315.4 ms (A). **두 판 모두 성공/실패 판정 기록 없음** (미확인). 대화식 09:40–09:55: 45 s·45 s·90 s 세션, 결과 기록 없음 (미확인) |
| 삭제된 평가 (A 기록, 데이터는 삭제) | "10:32 eval_ui 첫 실물 평가(3판 F/F/F)는 사용자 요청으로 삭제" — 확인된 문제: 판 끝 복귀가 1초 보간뿐이라 max_relative_target 8° 와 P16 에 잘려 처음 자세로 다 안 돌아감 (ep1 시작 shoulder_lift −19.7° vs 처음 −102.5°) → eval_ui 가 30°/s 보간 + 오차 3° 안까지 반복하도록 수정. "10:44 eval_ui 실물 평가(2판 F/F)도 사용자 요청으로 삭제" (복귀 125°→1.8°, 113°→1.8° 확인). 체크포인트는 문맥상 4_15000 (8_3000 학습은 11:29 시작) (C) |
| 근거 | `/home/user/so101_runs/main/cubemark_v1/eval/rollouts/20261013_09{1349,1856}_15k_rtc_fast/`, `/home/user/so101_runs/main/cubemark_v1/eval/rollout_20261013_09*.log`, `/home/user/so101_runs/main/cubemark_v1/notes.md:295-305` |

### E13. cubemark π0.5 학습 2 `8_3000/pi05_expert_bs8_3k` (action expert 만)

| 필드 | 내용 |
|---|---|
| 날짜 | 2026-10-13 11:29:43 – 13:52:23 (2시간 22분, 2.80–2.83 s/step). 11:22 첫 시작은 73 스텝에서 멈추고 지움 (A) |
| 목적 / 가설 | "사용자 지정 설정" — 왜 expert-only 를 골랐는지 문장 기록 **없음** (미확인) |
| 학습 설정 (train_config.json 확인) | pi05_base, bf16, grad ckpt, **train_expert_only True, freeze_vision_encoder True**, lr 2.5e-5 (끝 2.5e-6), **batch 8**, **steps 3000**, warmup 100 / decay 3000 (자동 축소), save 1000, seed 1000, 증강 끔. 학습 파라미터 **693,422,112 / 4,143,404,816** (A) |
| 학습량 | 24,000 샘플 ≈ **0.62 epoch** (A) |
| 정량 결과 | loss 0.095 (50) → 0.037 (3000), 최저 0.035 @2600 — "4_15000 의 같은 0.62 epoch 무렵(약 6000 스텝, 0.019)보다 높음 (학습 범위가 작음)"; GPU 14.9 GB, 시스템 38.9 GB; 체크포인트 001000·002000·003000 (각 11 GB) (A / C) |
| 근거 | `/home/user/so101_runs/main/cubemark_v1/notes.md:307-320`, `/home/user/so101_runs/main/cubemark_v1/train/8_3000/run_pi05_expert_bs8_3k.sh`, `/home/user/so101_runs/main/cubemark_v1/train/8_3000/pi05_expert_bs8_3k/training_params.md`, `.../checkpoints/003000/pretrained_model/train_config.json` |

### E14. cubemark 3k eval_ui 평가 (10-13, P 0 / F 8)

| 필드 | 내용 |
|---|---|
| 실험 ID | `main/cubemark_v1/eval/rollouts/20261013_135424_8_3000_3k_rtc_fast` |
| 날짜 | 2026-10-13 13:54 – 14:11 |
| 평가 환경 | `eval_ui.py --session main/cubemark_v1 --ckpt 8_3000`, ckpt 003000, flow 5단계, RTC h20, queue 40, max_relative_target 8 |
| 정량 결과 | 저장 8판, **P 0 / F 8 = 0%**; 판 길이 53.8–102.4 s (72.2, 53.8, 68.5, 102.4, 91.4, 69.8, 67.5, 77.7); 8° 제한 경고 **1426회**; RTC 평균 317.1 / 최대 370 ms; 첫 추론 대기 97틱 (A(사람판정) / A) |
| 정성·실패 이유 | 메모 칸 비어 있음 — 기록 없음 (미확인) |
| 비교 | 같은 데이터의 full-FT 15k 는 P/F 판정이 남은 평가가 없음 (삭제된 5판은 모두 F) → 15k vs 3k 성공률 비교 **불가** |
| 근거 | `/home/user/so101_runs/main/cubemark_v1/eval/index.md:7`, `/home/user/so101_runs/main/cubemark_v1/eval/results_all.csv`, `.../20261013_135424_8_3000_3k_rtc_fast/results.md`, `.../analysis.json` |

### E15. redbox 파일럿 3개 (본 수집 전 시험, 간단)

| 세션 | 날짜 | repo_id | 판 | 프레임 | 과제 문장 | 배치 | QA |
|---|---|---|---|---|---|---|---|
| `practice/redbox_t1k_pilot` | 10-13 17:47 | `oxr/so101_redbox_t1k_pilot` | 4 (T1K1, T1K4, T1K2, T1K3) | 1,928 | pick up the red cube and put it in the brown box | K1–K4 (빨강 1개) | 14.0–18.0 s; 육안 메모 없음 |
| `practice/redbox_t2k_pilot` | 10-14 | `oxr/so101_redbox_t2k_pilot` | 4 | 3,462 | put all the red cubes in the brown box | 빨강 3개 (K1·K3·K4 등) | 23.9–34.8 s; 학습 가능 3, 확인 1 |
| `practice/redbox_t3r_pilot` | 10-14 | `oxr/so101_redbox_t3r_pilot` | 4 | 1,995 | pick up the red cube and put it in the brown box | 자유 배치 빨강+파랑+초록 | 15.9–17.9 s; 학습 가능 3, 확인 1 |

- 공통: 자동 카메라, P16, 학습·평가 안 함 (`train/`, `eval/` 비어 있음). 상자 위치를 로봇 정면(front 화면 오른쪽 위, 긴 변이 가로)으로 옮긴 뒤의 배치 (A, config 주석). 큐브 2.5 cm (config). 판별 메모 칸 비어 있음.
- 근거: `/home/user/so101_runs/practice/redbox_t1k_pilot/notes.md:15-72`, `/home/user/so101_runs/practice/redbox_t2k_pilot/qa_report.md`, `/home/user/so101_runs/practice/redbox_t3r_pilot/qa_report.md`, `/home/user/so101_runs/description.md:300-303`, `/home/user/so101_runs/practice/redbox_t1k_pilot/setup_photos/ep000_front_first.png`

---

## 3. 종이 큐브(≈5.3 cm) → 2.5 cm 큐브 전환: 무엇이 기록돼 있나

**결론: 바꾼 이유를 적은 문장은 찾지 못함 → 미확인.** "나무(wood)" 재질 기록도 없음 (`grep 나무|wood|wooden|목재` → 토크나이저 파일만 걸림) → **2.5 cm 큐브가 나무라는 것도 미확인**.

기록된 사실:

| 사실 | 신뢰도 | 근거 |
|---|---|---|
| practice_10 큐브 = 종이 ("빨간 큐브(종이)") | B | `/home/user/so101_runs/practice/practice_10/notes.md:210` |
| practice_50 큐브 = "빨간 종이 큐브(≈ 53 mm)" | A(문서)/C(크기) | `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:19` |
| 53 mm 는 집게 값 역산: 쥔 값 중앙값 32.4 (또는 31.9) ↔ Thor 집게 표 53 mm = 31.4. 박사님 main 브랜치 "운영 큐브 = 실물 53 mm". 자로 잰 기록 없음 | C | `/home/user/so101_runs/e0_j0/design.md:143,308`, `/home/user/so101_runs/e0_j0/experiment_log.md:44`, `/home/user/so101_runs/ros2_guide.md:273` |
| 종이 큐브 문제 ① 가벼워서 밀림·밀리면 다시 못 잡음 (practice_10 실물) | B | `/home/user/so101_runs/docs/practice_10_pi05_2k.md:14,23,152` |
| 종이 큐브 문제 ② 조임(g−6)에 0.4 s 사이 4.2–4.5 단위 눌림 → 놓침 오판 (E0_J_0 10-08, 10-12 재발). "조임·놓침 규칙은 큐브 재질과 함께 정해야" | A / C | `/home/user/so101_runs/e0_j0/experiment_log.md:501-502,546`, `/home/user/so101_runs/e0_j0/report_for_dr_lee.md:137,198` |
| 사용자 평가 "학습할 때 잡는 세기를 잘 조절해야 할 것 같음" | B | `/home/user/so101_runs/docs/practice_10_pi05_2k.md:25` |
| 10-12 14:55 (setup 사진 파일 시각) cubemark 장면에 이미 **작은 빨간 큐브** | C(이번 조사 육안) | `/home/user/so101_runs/main/cubemark_v1/setup_photos/setup_front_20261012_1450.png` |
| 같은 10-12 15:46·16:10–16:14 E0_J_0 실물은 여전히 큰 큐브로 보임 (쥔 값 31.4 ≈ 53 mm 표값; 15:46 기록 "종이 큐브가 눌려") | A/C | `/home/user/so101_runs/e0_j0/runs/index.md`, `/home/user/so101_runs/e0_j0/runs/notes.md:31` |
| 10-13 오전 practice_50 eval (10:57) 은 **종이 큐브**로 진행 | C(이번 조사 육안) | `/home/user/so101_runs/practice/practice_50/eval/rollouts/20261013_105742_15k_rtc_fast/start_images/` |
| 10-13 **사용자 확인: 2.5 cm 정육면체** ("5.3 은 practice_50 종이 큐브"). 검출 문턱도 바뀜: `min_blob_area_px: 100 # 2.5 cm 큐브: 탁자 위 ≈1100 px² … 예전 300 은 5.3 cm 큐브 기준`, `grip_dip_min: 5 # 2.5 cm 큐브는 조금만 열어 7 정도 (기본 8)`, `qa len_s [10,40] # 2.5 cm 큐브 시험 녹화 14–18 초 (2026-10-13)` | A(사용자 확인 기록) | `/home/user/so101_boxpick/config/redbox_layouts.yaml:39,80,118,127`, [메모리] `redbox-dataset.md:33` |
| 10-15 사용자: "노랑·주황·파랑·초록 큐브 5개씩 있음" (방해물 큐브, 같은 2.5 cm 로 가정) | A(사용자 말 기록) | `/home/user/so101_boxpick/config/redbox_layouts.yaml:42` |

정리: 전환은 **10-12 (cubemark_v1 녹화) 무렵**에 일어났고 (화면 근거, C), 2.5 cm 라는 크기는 **10-13 에 사용자가 확인**했다 (A). 종이 큐브의 문제(가벼움·밀림, 조임에 눌림, 잡는 세기)는 그 전에 기록돼 있지만 (B/A), **"그래서 바꿨다"는 인과 문장은 어디에도 없다** (미확인).

---

## 4. 학습 설정 비교표 (모두 train_config.json 으로 확인)

| 항목 | practice_10 pi05_2k | practice_50 pi05_15k | cubemark 4_15000 | cubemark 8_3000 |
|---|---|---|---|---|
| 데이터 | 10판 / 6,589 | 50판 / 30,884 | 50판 / 38,816 | 50판 / 38,816 |
| 시작 가중치 | lerobot/pi05_base | 〃 | 〃 | 〃 |
| 학습 범위 | 전체 4.14B | 전체 4.14B | 전체 4.14B | **expert 만 693M** (vision 동결) |
| dtype | bf16 | bf16 | bf16 | bf16 |
| batch | 4 | 4 | 4 | **8** |
| steps | 2,000 | 15,000 | 15,000 | 3,000 |
| epoch | 1.21 | 1.94 | 1.55 | 0.62 |
| lr peak→end | 2.5e-5→2.5e-6 | 〃 | 〃 | 〃 |
| warmup / decay (실제) | 66 / 2,000 | 500 / 15,000 | 500 / 15,000 | 100 / 3,000 |
| 증강 | 끔 | 끔 | 끔 | 끔 |
| 첫 loss → 끝 loss | 0.139 → 0.020 | 0.131 → 0.014 (끝 5회 0.011) | 0.095 → 0.011 | 0.095 → 0.037 |
| 시간 | 1h25m | 9h54m | 9h54m | 2h22m |
| 실물 결과 | 저장 7판 중 1 성공 | 10-07 3/3 (Claude 판정), 10-13 3/8 (사람 판정) | 판정 남은 평가 없음 (삭제 5판 F) | 0/8 |

평가 공통 (practice_10 의 rtc_fast 이후): `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40`, `max_relative_target=8`, 30 Hz, 필터 없음 (arm_filter 는 10-19 이후, 범위 밖).

---

## 5. 소스 사이 충돌·주의

1. **practice_50 GPU 메모리**: notes "nvidia-smi 프로세스 39.3 GB" vs training_params.md "38.4 GB". (작은 차이, 측정 시점 차이로 보임 — 미확인)
2. **practice_50 쥔 집게 값 중앙값**: design.md 32.4 vs experiment_log.md 31.9. 둘 다 "53 mm" 결론에 사용.
3. **practice_50 성공률**: 10-07 3/3 (보고서, Claude 가 마지막 프레임으로 판정, eval index 에 없음) vs 10-13 3/8 (eval_ui 사람 판정). 판정 방법·배치가 다르므로 같은 척도가 아님 (10-13 은 학습에 없는 상자 배치 2판 포함 — C(이번 조사 육안)).
4. **practice_10 "7번 중 1번"**: docs 의 "7번" = 저장된 판 수 (sync 2 + q20 2 + rtc_h20 2 + rtc_fast 1). 09:27 대화식 1판, 09:56·10:39 지워진 판, 시작 실패 3회는 셈에 없음.
5. **사용자 평가 용어**: docs:19-23 "빨간색 박스" = 문맥상 빨간 **큐브** (갈색 박스와 구별). 원문 그대로 인용 시 주의.
6. **10-12 장면 순서**: cubemark setup 사진(작은 큐브, 14:55) 이 E0_J_0 실물(큰 종이 큐브로 보임, 15:46–16:14) 보다 앞섬 → 같은 날 두 큐브·두 장면을 오간 것으로 보임 (C). 15:46 기록의 "종이 큐브" 표현은 Claude 가 쓴 분석 문장이고, 사용자 말은 "큐브는 놓치지 않았다" 뿐.
7. **practice_50 QA 큐브 위치 자동 추정 (평균 117 px)**: 옛 HSV 규칙이 상자 벽을 큐브로 잡은 값이라 쓰면 안 됨 ([메모리] + 표의 상자 안 좌표).
8. **description.md 의 cubemark 평가 요약** ("3k 실행: 8판 중 성공 0") 은 index.md 와 일치. cubemark 15k 의 판정 결과는 description 에도 없음.
9. **"공간 일반화"** 라는 말은 초기 단계 파일에 없고 (`grep 일반화` → practice_10 의 "일반화 성능이 아님" 두 줄뿐), 연구자 기억은 나중 정리로 보임.

---

## 6. 미확인/누락 목록

1. 종이 큐브 → 2.5 cm 큐브로 **바꾼 이유** (인과 문장) — 기록 없음.
2. 2.5 cm 큐브의 **재질(나무 여부)** — 기록 없음 (색상 큐브 "5개씩 있음" 만).
3. 종이 큐브의 **실측 크기** (자로 잰 값) — 없음; 53 mm 는 집게 값 역산 + 박사님 브랜치 값.
4. practice_10 과 practice_50 이 **같은 종이 큐브**였는지 — 명시 없음.
5. 종이 큐브가 **영구적으로 찌그러졌다/모양이 변했다**는 관찰 — 없음 (기록은 조임 중 "눌림" 만, 그리고 체크리스트의 주의 문구).
6. cubemark_v1 의 **큐브 크기·재질** 및 **cubemark 과제를 만든 목적** — notes 에 없음.
7. cubemark 15k (4_15000) 실물 **성공/실패 판정** — 09:13·09:18 rollout, 09:40–09:55 대화식 모두 판정 없음; eval_ui 5판(F) 은 삭제됨.
8. cubemark 8_3000 을 **expert-only·vision 동결·bs8·3k** 로 고른 이유 — "사용자 지정 설정" 외 없음.
9. practice_50 10-13 평가의 **실패 이유 메모**, **배치(상자 이동·회전)를 바꾼 의도** — 없음.
10. practice_50 10-08 16:12, 10-12 16:18·16:24, 10-13 09:29 대화식 rollout 결과 — 로그에 cadence 만.
11. practice_10 실물 rollout 의 **큐브 시작 위치** — 기록 없음 (start_end_front.jpg 만).
12. practice_10·50 녹화 **판별 메모(성공/실패/버림)** — practice_50 의 빗잡기 3판 외 비어 있음.
13. practice_50 의 14:02 / 14:07 / 14:12 녹화 시도(1·2·1판)가 어떻게 처리됐는지 (덮어쓰기 추정) — 명시 없음.
14. redbox 파일럿 3개의 판별 메모·육안 QA — 비어 있음.
15. 초기 단계의 **명시적 공간 일반화 평가** (학습에 없는 위치에서의 성공률) — 없음. E0_J_0 도 "모두 기본 자리 근처".
16. practice_10 rtc_fast 성공 1판의 **판정자** (사람 vs 이미지 분석) — 문서에 명시 없음.
