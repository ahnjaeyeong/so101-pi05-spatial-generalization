# Survey 5 — d2 Pan 추론 진단 · 오프라인 Pan 반전 분석 · R1/R2 (HIL 성격) 수집 · Held-out H · 학습 일시정지 (2026-10-29 … 11-02)

조사 시각: 2026-11-02 16:18 KST. 조사 방법: 파일 읽기만 (cat/sed/grep/ls/stat, `ps`, 작은 read-only python). 로봇 · GPU · 학습 · 프로세스 조작 없음.

신뢰도 표기: **A** = 로그 · 파일에서 측정된 값 / **B** = 연구자 실물 관찰 (문서에 '사용자가 본' 으로 적힘) / **C** = 분석 가설 · 해석 / **D** = 계획. 문서의 값 종류 표기 ([실측] [재구성] [재추론] [반사실] [est]) 는 그대로 옮겼다. [재구성]/[반사실] 값은 오프라인 계산이므로 A (파일에 계산 결과로 존재) 이되 '실물 측정이 아님' 을 함께 적는다.

공통 경로 약어:
- `PD` = `/home/user/so101_runs/main_k8/d2/pan_inference_diagnostic`
- `OFF` = `PD/offline_pan_reversal_filter_off`
- `EV` = `/home/user/so101_runs/main_k8/d2/eval`
- `RC` = `/home/user/so101_runs/main_k8/r1_r2_collection`

---

## 0. 한눈에 보는 상태 (11-02 16:18 기준)

| 구분 | 항목 | 상태 | 신뢰도 |
|---|---|---|---|
| 완료 | sampling_ablation 안전 정지 (A2_s2001 004000 정상 종료, 큐 자체 정지) | 10-29 13:58 완료, 지금도 정지 상태 (QUEUE_STOPPED 존재, A2r·A0′ 폴더 없음, eval_hook.sh 실행권한 없음) | A |
| 완료 | 기존 실물 5 판 (10-26 try3 2 + try3_filt 3) 오프라인 재구성 진단 (PD 02–08) | 10-29 | A/C |
| 완료 | ROLLOUT_DIAG 계측 + 가짜 팔 harness 검증 (PD 07 §5–6) | 10-29 14:2x–14:3x | A |
| 완료 | 실물 계측 파일럿 12 판 (U3 1 판 15:55 + 11 판 16:08) | 10-29, P 4/12 | A (판정 B) |
| 완료 | K1 필터 켬/끔 실물 각 4 판 (17:02 ON, 17:08 OFF) — 12 문서의 ABBA 16 판 계획을 **축소 · 변경해 실행** (K1 만, 2 실행) | 10-29, ON P 2/4, OFF P 3/4 | A (판정 B) |
| 완료 | 좌표 역산 검증 (09), 첫 파지 정렬 분석 (11), K1 파지 직전 분석 (13), 하강 경로 (14) | 10-29 … 10-30 | A/C |
| 완료 | OFF 분석 A (01 문서: 실제 rollout 20 판 방향 반응), 분석 C (04 문서: 사람 256 편 복구 커버리지) | 11-02 15:28–15:43 | A/C |
| **진행 중** | `q02_seed_resample.py --n 64` (OFF/scripts, pid 4171232, 11-02 15:35 시작, nice 19, GPU). 로그 `OFF/logs/q02.log` 마지막 줄 `170 K7_c00399 S3_near_aligned … 2300s` → 223 상태 중 170 처리 (16:18 기준 경과 42:48). 출력 `tables/q02_states.csv`·`q02_seed_pan.npz` 는 스크립트 끝 (141–142 행) 에서만 써짐 → 지금 있는 두 파일 (15:35:12, 3 상태) 은 이전 짧은 실행 (`--limit` 추정) 결과로 보임 (미확인) | A (진행), 추정 부분 C |
| 미실행 (계획, OFF 00 §2) | q02b_metrics.py, q05_state_pan_sensitivity.py (GPU), q03_rtc_tables.py — 스크립트는 있음, 출력 표 (q02b_*, q03_*, q05_*) 없음 | D |
| 미작성 (계획, OFF 00 §4) | `02_offline_noise_seed_analysis.md`, `03_rtc_effect.md`, `05_r1_collection_recommendation.md`, `analysis_handoff.md` (OFF) — 파일 없음. 그림 fig3·fig4 도 없음 (fig1·fig2·fig5 만 있음) | D |
| 설계 · 도구 완료, 본 수집 0 | R1 (`main_k8/r1_realign_pilot`, 계획 16) · R2 (`main_k8/r2_pregrasp_pilot`, 계획 32) — dataset 폴더 자체가 없음 | A |
| 연습 녹화 | practice: r1_trial_old 3 · r1_trial 3 · r1_try 4 · r1_try2 2 · r1_try3 0 · r2_trial 0 (dataset/meta/info.json total_episodes 기준). 모두 결과 (first_grasp/final) 미입력 | A |
| 미녹화 | Held-out H (`main_k8/heldout_h`, 32 판 계획) — 세션 폴더 없음, config U1–U8 모두 `confirmed: false` | A |
| 미실행 | sampling_ablation A2 오프라인 평가 (eval_hook), A2r_s2001, A0_s2002 학습 | A |
| 정의 없음 | 파일 안에 'HIL / human-in-the-loop / DAgger / intervention' 정의 **없음** (§6) | A |

---

## 1. 학습 일시정지 상태 (scope 5)

근거: `PD/01_training_pause_status.md`, `/home/user/so101_runs/main_k8/d2/sampling_ablation/runs/` (queue.log, QUEUE_STOPPED, PAUSE_NOTE_pan_diag.txt).

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 실험 ID | sampling_ablation 큐 (A0_s2001 → A1_s2001 → A2_s2001 → A2r_s2001 → A0_s2002) | A |
| 날짜 | 확인 10-29 11:24–11:26, 조치 11:25:47, A2 종료 13:58:31, 큐 정지 13:58:41 | A |
| 목적 | Pan 진단 GPU 작업을 위해 학습을 안전하게 멈춤 (프로세스 kill 없이) | A |
| 끝난 실험 | A0_s2001 (10-28 09:46 rc 0, eval_hook OK), A1_s2001 (10-29 00:34 rc 0, eval_hook OK), A2_s2001 (02:28:37–13:58:31, 11 h 30 m, rc 0, last loss 0.019, weighted list 203776, 004000 저장, last → 004000, 002000 유지, 11 GB) | A |
| A2 실행 중 값 (11:25) | step ≈ 3,100/4,000, 10.9–11.2 s/step, loss 0.020, lr 3.4e-6; 004000 scheduler lr 2.5e-6 | A |
| 조치 | `chmod -x runs/run_A2r_s2001.sh` (큐 다음 반복에서 정상 정지 경로) + `chmod -x eval_hook.sh` (A2 평가 GPU ≈ 2 h 건너뜀) + `runs/PAUSE_NOTE_pan_diag.txt`. 큐 스크립트 수정 없음, 파일 삭제 없음 | A |
| 재개 불가 이유 | `train_weighted.py:121-122` 가 `--resume` 을 막음 (새 fine-tune 만). lerobot 은 신호 받으면 저장하는 기능 없음 (10-27 d4 중단 때 SIGINT 120 s 무응답 → SIGTERM, 15 step 손실) | A |
| 재개 절차 (자동 재개 안 함) | `cd ~/so101_runs/main_k8/d2/sampling_ablation; chmod +x runs/run_A2r_s2001.sh eval_hook.sh; ./eval_hook.sh A2_s2001 >> runs/eval_hook_A2_s2001.log 2>&1` (A2 평가 GPU ≈ 2 h). 남은 A2r_s2001 · A0_s2002 는 `run_queue.sh` 가 이미 있는 runs/A0_s2001 등에서 멈추므로 `RUNS=(A2r_s2001 A0_s2002)` 로 바꾼 사본 (예: `ops/run_queue_resume.sh`) 을 setsid nohup 으로 시작. 두 실험 모두 d2 020000 에서 새 fine-tune, seed 고정 (2001, 2002) → 중단으로 잃는 상태 없음 | D |
| 지금 확인 (11-02 16:1x) | `runs/QUEUE_STOPPED` (10-29 13:58) 있음, `eval_hook.sh` 권한 `-rw-rw-r--`, `run_A2r_s2001.sh` `-rw-r--r--`, `eval_hook_A2_s2001.log` 없음, A2r/A0_s2002 폴더 없음 → **일시정지 상태 그대로** | A |
| A0/A1 오프라인 평가 수치 | 이 조사 범위에서 읽지 않음 (`sampling_ablation/eval/A0_s2001_00{2,4}000`, `A1_…` 폴더 존재만 확인) | 미확인 |

---

## 2. Pan 추론 진단 (PD, 10-29 … 10-30)

### 2.1 공통 정책 · 추론 설정 (모든 d2 실물 평가에 공통)

| 항목 | 값 | 근거 | 신뢰도 |
|---|---|---|---|
| 체크포인트 | d2 `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` (π₀.₅ PI05Policy, expert-only, bs32, 20k) | EV/index.md, PD/analysis_handoff.md §1 | A |
| d2 데이터 | 256 편 (T1 + T3, K 128 + Random) | handoff §1, 09 §2 | A |
| 추론 | num_inference_steps 5 (checkpoint config 기본 10 을 실행 인자로 5), chunk 50, fps 30, n_obs_steps 1 | OFF/01 §1 | A |
| RTC | guided, EXP, execution_horizon 20, max_guidance_weight 10, queue_threshold 30. queue ≤ 30 이면 새 추론, merge 는 `chunk[delay:]`, 실행 index ≈ 10–29 (첫 chunk 는 0–29, prefix 없음 = RTC 안내 없음) | handoff §1 | A |
| inference_delay | 문서 02·08: "세션 두 번째 추론 0, 이후 11–12". OFF/01: 이 20 판 기록값은 **12 (와 0)**. K1 B 116 chunk 중 12 = 114, 0 = 2. applied_delay 10 = 83, 11 = 20, 9 = 6 | PD/02, OFF/01 §1 | A (**불일치 기록됨**) |
| 명령 경로 | queue → arm_filter (EMA α 0.5, pan 속도 제한 2.46°/틱) → clamp (Present ± 8°, max_relative_target 8) → Goal_Position | handoff §1 | A |
| 카메라 | front · wrist 640×480 30 fps MJPG | 07 §1 | A |
| 과제 문장 | `pick up the red cube and put it in the brown box` | 07 §1 | A |
| 시작 자세 | eval_ui 가 판마다 처음 자세로 되돌림, `pose_check.txt` 기록만 (막지 않음) | 07 §1 | A |

### 2.2 d2 실물 rollout 전체 목록 (EV/index.md, EV/results_all.csv, EV/rollouts/)

| 날짜 시각 | 폴더 | ckpt | tag | filter | guard | n 저장 | P/F | 비고 | 신뢰도 |
|---|---|---|---|---|---|---|---|---|---|
| 10-26 13:51 | `EV/rollouts/20261026_135128_20k_t1_try3` | d2 020000 | try3 | 끔 | — | 2 (N_EP=3 요청, dataset total_episodes 2, 2983 프레임) | **판정 기록 없음** (run_rollout.sh 는 판정 안 남김, PD/03 §1) | 시작 pan −2.3 | A |
| 10-26 14:02 | `EV/rollouts/20261026_140246_20k_t1_try3_filt` | d2 020000 | try3_filt | 켬 | — | 3 (3129 프레임) | **판정 기록 없음** | 시작 pan −2.7 | A |
| 10-29 15:55 | `EV/rollouts/20261029_155513_32_20000_20k_pan_diag` | d2 020000 | pan_diag | 켬 | off | 1 (U3) | P 0 / F 1 | 8° 제한 경고 46 회 | A (판정 B) |
| 10-29 16:08 | `EV/rollouts/20261029_160831_32_20000_20k_pan_diag` | d2 020000 | pan_diag | 켬 | off | 11 (+ 버림 6) | P 4 / F 7 (index 36 %) | 경고 1227 회, 16:08–16:23 | A (판정 B) |
| 10-29 17:02 | `EV/rollouts/20261029_170219_32_20000_20k_filt_on` | d2 020000 | filt_on | 켬 | warn | 4 (K1) | P 2 / F 2 (ep2·ep3 P) | 경고 631 회, 17:02–17:08, 시작 pan +5.5 | A (판정 B) |
| 10-29 17:08 | `EV/rollouts/20261029_170818_32_20000_20k_filt_off` | d2 020000 | filt_off | 끔 | warn | 4 (K1) | P 3 / F 1 (ep1 F) | 경고 459 회, 17:08–17:41 (33 분, 이유 미확인), 시작 pan +4.8 | A (판정 B) |

- index.md 는 10-29 4 실행만 담는다 (eval_ui 실행만 추가). 10-26 두 실행은 index 에 없다.
- P/F 판정 = 사용자가 eval_ui 에서 판 끝에 누른 최종 결과 (상자에 넣었나). 판 메모 (first/final) 는 6 실행 모두 비어 있음.
- 10-29 합계: 20 판 저장, P 9 (파일럿 4/12, K1 ON 2/4, K1 OFF 3/4).
- 판별 P/F (results_all.csv): 16:08 실행 ep 0–10 = F F F F F P P F F P P → 이름 순서 (K1 U2 U5 K3 U6 U7 K6 U4 U1 K7 U8) 와 맞추면 P = U7 · K6 · K7 · U8 (PD/10 §2 와 일치).

### 2.3 실험 P0 — 기존 실물 5 판 오프라인 재구성 진단 (PD/02–06, 08)

| 필드 | 내용 |
|---|---|
| 실험 ID | Pan 추론 진단 (기존 로그) — PD 02 · 03 · 04 · 05 · 06 · 08 |
| 날짜 | 10-29 (문서 11:43–14:55) |
| 목적 | d2 020000 이 pan 을 느리게 / 틀리게 움직이는 원인을 '모델 Raw Action / RTC / 서보 / 구분 불가' 로 가름 |
| 당시 문제 | 10-26 실물 5 판에서 첫 chunk pan 부족, 접근 느림, chunk 경계 역전 (filt/ep0 −14.7°), 새 위치 3.7 s 정지 (filt/ep1) [A] |
| 데이터 | 10-26 try3 2 판 + try3_filt 3 판 (dataset AV1 영상, filter_log, debug.log). 사람 비교 d2 256 편 |
| 모델 | d2 020000 |
| 평가 환경 | 큐브 위치 기록 없음 → front 첫 프레임에서 추정 (pe SD 2.31°). 큐브 각도 기록 · 추정 없음. 시작 pan −2.3 … −2.8° |
| 방법 | 틱 시간축 복원 (p01), 기존 지표 (p02), 같은 관측에 noise 바꿔 재추론 (U = 안내 없음, G = guided) (p03b/c, p06), A/B/C/D 분류 (p06e) |
| 정량 결과 [A, 출처 handoff §2–3, 08 §1] | 첫 chunk idx29 need 비율: try3/ep0 0.10 · try3/ep1 0.56 · filt/ep0 0.89 · filt/ep1 −0.07 · filt/ep2 0.83 [실측]. need: −31.8 / −57.8 / +35.5 / +22.3 / −42.7°. 닫힌 고리 1 s 이동 비율 (남은 오차 6–12 / 12–25 / ≥25°): 정책 0.12 / 0.21 / 0.48 vs 사람 0.60 / 0.95 / 0.95 [실측]. filt/ep1 noise 256 개: 54 % 가 < 0.1, 24 % ≥ 0.5, 기록값 백분위 0.07 [재구성]. 계획 1 s 비율 중앙 0.14–0.49 [재구성]. RTC 가 실행 끝 pan 을 바꾼 양 중앙 0.3° [재구성]. 첫 chunk f29 중앙 0.06–0.38 vs f49 0.43–0.95 [재구성]. filt/ep0 경계: U 중앙 −7.9° (p10 −20°), G(d=0) 중앙 −4.7 … −5.2° (p10 ≈ −16°), d=11 반사실 ±2.6° [반사실]. A/B/C/D (72 chunk): A 38 · D 7 · B 2 · B′ 5 · C 0 · ok 20. 서보 pan 지연 4 틱 (사람 4 틱), 필터 · clamp pan 변경 p95 ≤ 1.63°, 첫 닫힘 직전 3 s \|sent − state(+4)\| 중앙 0.23–0.44°. 첫 닫힘 직전 명령 − pe: filt/ep1 −9.8° (지나침), filt/ep2 +5.1°, try3/ep1 +5.5° |
| 서보 (06) [A] | 판별 최적 지연 4 틱, 움직일 때 \|sent − state\| p50 0.64–1.32° · p95 4.16–7.05°. 관절별 clamp 틱 합: lift 151 · elbow 197 · pan 12. 사람 pan 최고 속도 중앙 79°/s (95 % 127°/s) vs 필터 제한 73.8°/s; 같은 제한을 사람에 대면 256 편 중 159 편이 한 번 이상 넘음 |
| 해석 (as stated, C) | 첫 chunk 부족 · 접근 느림 · 실행 구간 역전 · 새 위치 정지 · 닫힐 때 남은 오차 = **모델 Raw Action**; filt/ep0 경계 = 모델 Raw + RTC (세션 두 번째 추론 inference_delay 0); 서보 = 근거 없음; filt/ep2 첫 chunk 가 재구성 분포 위 1 % = 구분 불가. 가설 H1 (bimodal '기다림/감' + 계획 앞 1/3 느림 → 앞부분만 반복 실행), H2 (연속 chunk 의 다른 속도 표본 → 역전), H3 (새 위치에서 '기다림' 비율 큼, 근거 약함) |
| 한계 | 5 판, 새 위치 1 개, AV1 재부호화 영상, 첫 chunk 실제 관측 틱 · noise 기록 없음, 재구성이 기록 p10–p90 에 든 비율 65–70 % (기대 80 %), 반사실은 한 chunk 열린 고리 |
| 다음으로 이어진 이유 | 기존 로그에 없는 것 (원 chunk 50 개, noise, prefix, 관측 PNG, clamp 에 쓴 Present) 을 남기는 계측 (`ROLLOUT_DIAG=1`) 을 만들어 실물 파일럿으로 확인 (07) |
| 근거 | `PD/02_inference_pipeline.md`, `PD/03_existing_log_inventory.md`, `PD/04_initial_action_chunk.md`, `PD/05_replanning_feedback.md`, `PD/06_servo_tracking.md`, `PD/08_diagnostic_conclusion.md`, `PD/analysis_handoff.md`, `PD/tables/p01–p06*`, `PD/figs/fig1–fig5` |

### 2.4 실험 P1 — 계측 도구 · harness 검증 (PD/07 §5–6)

| 필드 | 내용 |
|---|---|
| 날짜 | 10-29 14:2x–14:3x (harness), preflight 15:04:52 ALL_OK (`PD/preflight/preflight_20261029_150452.json`), 15:53:15 두 번째 preflight 파일 존재 |
| 방법 | 같은 RTC 엔진 · 정책을 가짜 팔 (FakeBus · FakeCam, connect 차단, Fake assert) 에 붙여 diag 끔 3 회 · 켬 2 회, 기록 판 filt/ep1 영상 · state, 450 틱 |
| 결과 [A] | 추론 22 · starved 21–22 (첫 추론 동안) 끔/켬 같음; 첫 추론 지연 0.68–0.72 s; 이후 p50 0.30–0.33 s; 루프 본체 p50 끔 0.26–0.27 ms vs 켬 0.34–0.38 ms; 감싸기 p50 6.2–6.9 µs (제어) · 35.9–39.5 µs (RTC); writer chunk p50 71.7–72.4 ms (별도 스레드); 22 chunk 재계산 차 0.0. 버그 1 건 (`self._stop` 이 Thread._stop 을 가림 → `_stop_ev`, sha 08662d05 → b1425bab) |
| 코드 sha | rollout_logged.py cf72afe0… → 8fcd4b6b… (ROLLOUT_DIAG 분기 3 곳), diag_log.py b1425bab…, arm_filter a5307329 |
| 한계 | harness 는 rollout_logged 의 필터 · 로그 감싸기와 함께 걸린 실제 경로, 실제 카메라 · 직렬 통신 시간을 덮지 않음 |

### 2.5 실험 P2 — 실물 계측 파일럿 12 판 (PD/07 계획, PD/09 좌표, PD/10 결과)

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 실험 ID | pan_diag 파일럿 (U3 단계 1 + 11 판 단계 2) | A |
| 날짜 | 10-29 15:55–15:59 (U3), 16:08–16:23 (11 판, 버린 시도 6) | A |
| 목적 | 원인 단계 가르기용 소규모 파일럿 (성공률 확정용 아님), 기록은 학습에 쓰지 않음 (07 머리말) | A |
| 가설 | 08 의 H1–H3, '새 위치' 효과 분리 | C |
| 평가 환경 | 카메라 front/wrist 동일 위치·노출, 카메라 이동 2–3 px; 큐브 위치 K1·K3·K6·K7 (표시 자리) + U1–U8 임의 자리 ('참고' 방향만, 지정 좌표 없음); **큐브 각도 프로토콜 0° 였으나 실제 측정 11 판 중 7 판 \|각도\| > 10°** (U5 −35°, U8 +39°, K1 +24°, K6 −25° …); 시작 pan +5.4 … +7.0° (학습 시작 범위 −14.8 … +3.8° 밖, pose_check 는 OK 로 기록); filter 켬; RTC 위 공통값; guard off | A |
| 순서 | U3, K1, U2, U5, K3, U6, U7, K6, U4, U1, K7, U8 | A |
| 기록 점검 | 두 실행 모두 p00b VERIFY_OK; chunk 87 + 447 = 534 모두 재계산 차 0.0°; 추론 p50 350 / 366 ms (첫 669 ms); front 프레임 나이 p50 15.7 / 16.0 ms; 버린 기록 · wrapper 오류 0. 점검기 수정 1 건 (HOMING 틱 U3 259 · 11 판 2,887 행을 정책 틱에서 제외) | A |
| 좌표 | 12/12 유효: valid_near_K 4, valid_off_K 8, invalid 0. K 4 판 사진 − 명목 0.17–0.58 cm | A |
| 정량 결과 — 판정 | P 4/12: K 2/4 (K6, K7), U 2/8 (U7, U8) | A (판정 B) |
| 정량 결과 — 첫 chunk [실측] | idx29 비율 중앙: 왼쪽 need 6 판 0.035, 오른쪽 6 판 0.69; K 4 판 0.11, U 8 판 0.43. 첫 3° 방향 12/12 need 쪽. 판별 idx29: U3 0.02, K1 0.05, U4 0.01, U1 0.23, K7 −0.00, U8 0.73, U2 0.79, U5 0.62, K3 0.17, U6 0.13, U7 1.03, K6 0.75 | A |
| noise 64 개 [재추론] | 큰 왼쪽 need (−41 … −92°) 5 판 (U3·K1·U4·K7·U8) 에서 53–80 % 가 1 s 에 need 10 % 미만 (학습 K1·K7 포함); 오른쪽 6 판은 2–11 %. U8 기록 0.73 = 위쪽 5 % 안, K3 기록 0.17 = 아래쪽 꼬리 | A (오프라인) |
| 시작 pan 반사실 [반사실] | state pan 만 −4.3° 로: 왼쪽 idx29 0.05 → 0.12, <0.1 비율 66 → 48 %; 오른쪽 0.71 → 0.45. 영상 속 팔은 그대로라 불완전 | A (오프라인) / 해석 C |
| 정지 구간 | U3 4 chunk (2.8 s), K7 6 (3.7 s), U4 3 (1.7 s), K1 2 (1.0 s), K3 3 (1.7 s); 계획 이동은 idx 30–49 에 몰림, 실행 idx 10–29 는 정지 근처; RTC 끔 반사실도 0.00–0.08 | A |
| RTC | 실행 끝 \|기록 − RTC 끔\| 판별 중앙 0.27–1.33°; seam 최소 기록 −0.5 … −1.7° vs RTC 끔 −3.7 … −37.0°; 실행 구간 안 되돌림 최대 기록 3.0–20.0° (U8 20.0, U3 16.2, K1 11.2) vs RTC 끔 3.7–37.8° | A (반사실 포함) |
| 첫 닫힘 Pan 오차 (pe − pan, need 부호, + = 못 미침) | K1 −2.59, K3 +0.44, K6 +0.86, K7 +2.95, U3 +4.99, U2 +5.32, U5 −0.07, U6 −7.35, U7 +5.28, U4 −4.62, U1 +2.39, U8 +2.53°. \|오차\| 중앙 near_K 1.7°, off_K 4.8°. > 2σ_grasp (4.3°): near_K 0/4, off_K 5/8. 첫 닫힘 시각 6.3–21.2 s | A (pe 는 est) |
| 서보 | 최적 지연 3–4 틱, 움직일 때 \|sent − present\| p50 4.2–7.0° · p95 6.0–8.0°, pan clamp 틱 0–13, 필터 pan 변경 p95 0.5–2.1° | A |
| 해석 (as stated) | 첫 1 s 부족 = 모델 Raw (학습 K 에서도); 시작 pan 영향 = 구분 불가; 정지 지속 = 모델 Raw (+ 실행 구조); 경계 역전 = RTC 가 억제; 실행 구간 되돌림 = 모델 Raw; off-K 오차 큼 = 구분 불가 (off-K 좌표 미검증); 서보 = 근거 없음 | C |
| 한계 | 위치마다 1 판, 한 정책, 좌우 비교 6 판씩; 기존 5 판 (시작 pan −2 … −3°) 과 같은 조건 비교 안 함; 판 메모 없음 → 첫 닫힘 성공 여부는 11 문서에서 영상 · 관절로 따로 분류; 큐브 각도 통제 실패 | A |
| 다음으로 | 사용자가 '파지 직전 정렬' 로 우선순위 변경 → 11 (첫 파지 분석), 12 (필터 A/B 계획) | A (메모리 · 11/12 문서) |
| 근거 | `PD/07_evaluation_protocol.md`, `PD/09_coordinate_inversion.md`, `PD/10_pilot_results.md`, `PD/pilot/pilot_episodes.csv`, `PD/pilot/pilot_summary.json`, `PD/pilot/p12_*`, `PD/pilot/p13_static_phase.csv`, `PD/figs/fig6_pilot_pan_timeline.png`, `fig7_pilot_first_chunk.png`, 각 rollout 폴더 `diag/`, `analysis_pan/` | |

### 2.6 실험 P3 — 좌표 역산 · 기준 Pan (pe) 검증 (PD/09)

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 날짜 | 10-29 | A |
| 목적 | 판 시작 front 사진으로 큐브 XY → 기준 pan (pe) 을 정해 '접근 정확도' 의 정답으로 씀. 정책 행동은 정답에 쓰지 않음 | A |
| 방법 | 기존 Homography (`redbox8_layouts.yaml` camera.front_640x480.H_cm_to_px, 10-22 K1–K8 큐브 8 개로 맞춤, 재투영 2 px ≈ 0.2 cm) + red_mask + `ac.py` pe = pan_sign · bearing + offset (베이스 (−30.55, 11.18), offset −0.75° — 사람 256 편 첫 파지로 맞춤) | A |
| 검증 결과 (학습 K 128 편) | 2D 오차 RMS 0.65 · 중앙 0.48 · p90 0.98 · 최대 2.30 cm; 편향 dx +0.32 · dy +0.18 cm; pe 영향 SD 1.25° · \|p90\| 1.99° · \|최대\| 3.94°; 기존 QA 검출과 차 중앙 0.04 cm; K 별 2D 중앙 0.28 (K6) … 0.93 (K5) cm | A |
| 사람 파지 pan − pe | 잔차 SD 2.12° (in-sample), 5-fold CV SD 2.15°, \|p90\| 3.45°; 같은 K 16 편 SD 중앙 1.92° (K1 1.17 … K7 3.18); 잔차-wrist_roll 상관 +0.66 (0.052° pan/° roll) → pe 는 '사람 파지 pan 분포의 중심' | A / 해석 C |
| off-K 간접 점검 (p10b) | 잔차 SD: K 판 2.19° (127), R 1.5–3 cm 1.53° (15), 3–6 cm 1.60° (62), ≥ 6 cm 2.63° (50); \|잔차\|-K 거리 상관 +0.45 → 좌표 오차와 사람 산포 구분 불가 | A / C |
| coord_status 정의 | valid_near_K (검출 정상 · H 범위 안 · K 3 cm 이내, 검증됨) / valid_off_K (K 3 cm 초과, pe 저장 · 별도 그룹, 미검증) / invalid_detection (빨강 없음 · 넓이 비 0.5–1.6 밖 · 둘째 빨강 ≥ 0.3 배 · 사진 없음) / invalid_calibration (카메라 이동 > 6 px · H 범위 x −35 … −5, y −15 … +37 밖). invalid 두 가지만 pe 지표에서 빠짐 | A (정의) |
| 불확실성 열 | pe_sigma_coord_deg (K 검증 RMS 0.65 cm 접선 / 반지름; off-K 는 '미검증 참고치'), pe_sigma_grasp_deg 2.15° — 섞지 않고 따로 표시 | A |
| 한계 | 보정 정답점 K 8 곳뿐, H 는 큐브 중심 높이 면 기준, base · offset 은 사람 파지로 맞춘 값 (로봇 베이스 실측 아님), PNG vs AV1 검출 차 미측정 | A |
| 근거 | `PD/09_coordinate_inversion.md`, `PD/scripts/cube_coords.py`, `PD/scripts/p10_coord_validation.py`, `p10b_offk_indirect.py`, `PD/tables/p10_*` (tables 목록에는 보이지 않음 — 미확인, 문서에 경로만 기재) | |

### 2.7 실험 P4 — 첫 파지 정렬 분석 + 필터 끔 오프라인 비교 (PD/11)

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 날짜 | 10-29 (16:58) | A |
| 목적 | 파일럿 12 판 첫 파지 실패 유형 분류, arm_filter 가 실패에 기여하는지 오프라인 확인 | A |
| 첫 파지 정의 | 첫 닫힘 c = state gripper 첫 닫힘 이벤트; 닫힘 시작 on = c 전 2 s 안 최대 열림 뒤 3 넘게 줄어든 첫 프레임; 그리퍼 바닥 = c 뒤 1 s 최솟값 (사람 쥠 5–95 % 11.5–13.6, 빈 닫힘 ≈ 1–4); 들어 올림 = c 뒤 2 s 안 TCP z ≥ 4 cm 상승 & 그리퍼 ≥ 9; 놓침 = 들어 올린 뒤 그리퍼 ≤ 6; 깊이 분류 헛잡기 (바닥 ≤ 5) / 얕은 / 깊은 / 판단 불가; 좌우 = 손목 u 가 사람 5–95 % (0.26–0.57) ± 0.02 밖 | A (정의) |
| 결과 [A] | 첫 파지 성공 4/12 (U7·K6·K7·U8) = 최종 성공 4 판과 같음; 들어 올린 뒤 놓침 0; 실패 8 판 모두 빈 닫힘 (바닥 1.9–4.3). 사람 256 편: 첫 파지 성공 253, 빈 닫힘 0, 놓침 0. 손목 화면: '앞쪽 (덜 다가감)' 3 (K1·K3·U4, v 0.45–0.58 vs 사람 0.64–0.76), '아래쪽 · 손가락 사이 · 화면 아래 가장자리' 4 (U3·U2·U5·U6, v 0.80–0.87), '손가락에 가려짐' 1 (U1, 볼록도 0.66). 이후 닫힘에서 16.6–19.4 에서 멈춘 닫힘 6 번 (모두 들어 올리지 못함) | A |
| kNN 사람 10 편 대비 (닫힘 시작) | 덜 다가감 실패 4 판 (K1·K3·U4·U1) TCP z +2.45 … +3.02 cm (사람 p10–p90 폭 0.75 cm), shoulder_lift −6 … −19°; 성공 4 판 TCP z −0.34 … +0.24 cm; pan 차 11/12 판 ±6.1° 안 (U6 +9.2°) | A |
| 명령 사슬 (닫힘 전 1 s) | RTC 뒤 − RTC 끔 pan 0.29–1.19°; 필터 out − raw 관절별 중앙 ≤ 0.4° (K3 elbow 0.82); clamp 0 | A |
| 필터 끔 오프라인 [열린 고리] | \|out − raw\| pan p50 0.19 / p95 0.94 / 최대 11.6°; 9,273 틱 중 속도 제한 145, EMA 재설정 6; FK TCP 차 p50 0.16 · p95 0.53 · 최대 3.27 cm (닫힘 전 1 s 최대 0.56 cm). 실물 비교: try3 (끔) 틱당 \|Δ\| 최대 pan 4.26° vs filt 2.46° | A (오프라인) |
| 안전 평가 (해석) | 필터를 꺼도 8° clamp 유지, 10-26 try3 (끔) 에서 이상 정지 · 충돌 기록 없음 → 새 큰 위험 근거 없음, 단 열린 고리 | C |
| 해석 | 가장 큰 오차 방향 = TCP 높이 (+2.5–3.0 cm, '덜 다가감'), pan 은 대부분 ±6° 안 ('사용자 관찰과 일치' — B), 필터가 주원인이라는 근거 없음 → 실물 대조 필요 | C (사용자 관찰 B) |
| 근거 | `PD/11_grasp_alignment_and_filter.md`, `PD/pilot/p14_*`, `p14b_*`, `p15_*`, `PD/pilot/p14_wrist_sheet.jpg` | |

### 2.8 실험 P5 — arm_filter 켬/끔 실물 대조: 계획 (12) vs 실제 실행 (13)

**계획 (PD/12, 10-29 16:58, D)**: K1·K3·K6·K7 각 2 판 × 조건, ABBA 16 판 (S1 A K1-K3-K6-K7 → S2 B → S3 B 역순 → S4 A 역순), 큐브 각도 0, `--rollout_guard=warn` 양쪽, 유일 변수 `--arm_filter`. 판 메모 형식 `first= lift= drop= final= side=C|L|R|? depth=D|S|E|?`. 비교 지표 우선순위: ① 첫 파지 손목 화면 위치 ② 깊이 ③ 첫 파지 성공 ④ 놓침 ⑤ 최종 투입 ⑥ 닫힘 시작 TCP z · 관절 이웃 사람 대비 ⑦ Pan t90 (참고). "판 8 개씩이라 차이 확정 불가, 판별 표와 개수로만".

**실제 실행 (A, EV/index.md + PD/13)**: K1 만, 켬 4 판 (17:02, A0–A3) + 끔 4 판 (17:08, B0–B3), 실행 2 개. K3·K6·K7 · ABBA 순서는 실행되지 않음. 축소 이유는 파일에서 찾지 못함 (미확인). 판 메모 없음.

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 혼란변수 | 큐브 각도 켬 +31 · +31 · +31 · −45°, 끔 +23 · +2 · +3 · −15° (프로토콜 0° 아님); 시작 pan 켬 +5.5°, 끔 +4.8° (둘 다 학습 범위 밖); noise 판마다 다름 | A |
| 판정 | 켬 P 2/4 (A2, A3), 끔 P 3/4 (B0, B2, B3); 첫 파지 1/4 vs 3/4 (A3 은 첫 닫힘 실패 뒤 재시도 성공) | A (판정 B) |
| 닫힘 이벤트 [실측 · 반사실] | 빈 닫힘 3 (A1 #0 · A1 #1 · A3 #0): 손목 v 0.54–0.60 (앞쪽); 쥠 5 (A2 · A3 #1 · B0 · B2 · B3): v 0.69–0.77. 닫힘 순간 FK 명령 z − 현재 z +0.07 … +0.97 cm (성공·실패 차 없음); 계획 남은 하강 ≤ 0.57 cm (실패 3 건 idx 29 이후 0.20–0.46 cm) → '모델이 그 자세에서 닫기로 계획'. A1 #0: RTC 끔 같은 noise 도 같은 틱 (272) 닫힘; noise 32 개 이른 닫힘 RTC 44 % vs 끔 9 %. A3 #0: RTC prefix 가 앞 chunk 그리퍼 열림을 이어받고 곧 닫음, RTC 끔 31/32 은 안 엶. 쥔 4 번은 RTC 끔이 4–12 틱 일찍 닫음 | A (반사실 포함) |
| 필터 기계적 차이 | 필터 out − rtc 관절별 중앙 ≤ 0.38°; 그리퍼 명령 → 실제 닫힘 시작 켬 4·5·7·8·15 틱 vs 끔 3·3·3 틱; 손목 화면 가로 변화폭 중앙 켬 0.084 vs 끔 0.042 (사용자 관찰 '켬에서 좌우로 벗어남' 과 같은 방향 — B); pan 실제 변화폭 1.41 vs 1.14° | A / B |
| −109° 이탈 (A0 켬, B1 끔) | A0: 손목에서 사라질 때 pan −65.0° (pe −35.5 보다 30° 지남), −105° 도달 15.2 s, 명령 최저 −126.5°, 상태 −108.9, guard stall 경고 12 회. B1: −44.0°, 14.5 s, 명령 −119.3°, 상태 −109.0, 경고 0. front 에는 큐브 계속 보임 | A |
| 안전 정지 후보 (오프라인만, 20 판) | S1 관절 범위 0 걸림; S2 명령 범위 A0 17.2 s · 다른 판 1; S3 한계 버팀 A0 17.1 s; S4 큐브 놓침 + 회전 A0 11.4 · B1 6.7 s, 다른 5 판 오경보; **S4b** '본 뒤 놓침' + 회전 A0 11.4 s · B1 6.7 s, 다른 0; **S5** pe 를 지나 30° 더 감 A0 7.0 s (−66°) · B1 6.0 s (−66°), 다른 1 (U3 37.5 s, 첫 닫힘 실패 뒤). 구현 안 함 (사용자 승인 · harness 검증 먼저) | A (오프라인) / D (구현) |
| 실패 유형 → 데이터 후보 | 첫 파지 실패 12 번 중 R2 해당 10 (덜 다가감 5, 아래쪽 4, 가려짐 1), R1 해당 2 (−109° 이탈) + 첫 실패 뒤 복구 1/10 만 성공 | A (분류) / C (대응 판단) |
| 해석 (as stated) | 빈 닫힘 · 이탈 원인 = Raw Action; RTC 는 양방향 일부 관여; 필터 영향 = 기계적 차이 작음, 결과 영향 구분 불가; "현재 실패 유형에 더 직접적인 것은 R2" | C |
| 한계 | 비대응 4 + 4, FK 절대 위치가 K1 에서 손목 영상과 4–5 cm 어긋남 (상대 차로만 씀), 깊이는 손목 v 뿐 (접촉 · 힘 없음) | A |
| 근거 | `PD/12_filter_ab_protocol.md`, `PD/13_k1_pregrasp_analysis.md`, `PD/filter_ab/p16*.csv`, `p16.log`, `p17_safety_offline.csv`, `p17.log`, `p17_train_range.json`, `PD/filter_ab/A/`, `PD/filter_ab/B/` | |

### 2.9 실험 P6 — K1 하강 경로 (PD/14, 10-30)

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 목적 | 사용자 관찰 '켬은 사선 하강' 확인, 필터 설정을 R2 전에 바꿀 근거 있는지 | A (B 관찰 포함) |
| 방법 | s0 = tc 앞 2 s 안 FK 높이 최고 틱, 구간 1.47–2.00 s; 기울기 = atan(수평/수직); 반사실 필터 (명령 열만 재계산, 재현 최대 차 0.0°) | A |
| 결과 | 첫 닫힘 실제 기울기 켬 17 · 21 · 59° (중앙 21°) vs 끔 8 · 7 · 33° (중앙 8°); RTC 명령 (필터 전) 이미 켬 16 · 16 · 72° vs 끔 8 · 8 · 34°; 필터는 16→16, 16→16, 72→69°; 끔 명령에 필터 반사실 8→8, 8→7, 34→29°. 하강 중 속도 제한 · clamp 0 틱. lift 지연 켬 1–3 · 끔 0–1 틱; elbow 7–10 틱 (양쪽). 실제가 명령보다 더 기운 경우 켬 3/5 · 끔 0/3. 손목 \|Δu\| 중앙 0.12 vs 0.05 (roll 섞임), front 가로는 오히려 끔이 큼 (14.5 vs 2.0 px) | A |
| 해석 | 기울기 차는 필터 앞 (모델 · RTC 출력) 에서; 성공·실패는 기울기가 아니라 닫힘 때 손목 v (0.54–0.60 vs 0.69–0.77) 로 갈림; R2 전에 필터를 바꿀 근거 약함; 대응 비교 (각도 0 고정, 켬·끔 번갈아) 필요; R2 전후 비교는 필터 설정 하나로 고정해야 함 (어느 쪽인지는 사용자 결정) | C / D |
| 근거 | `PD/14_k1_descent_path.md`, `PD/filter_ab/p18_*.csv`, `p18.log`, `PD/figs/fig8_k1_descent_paths.png` | |

---

## 3. 오프라인 Pan 반전 분석 (OFF, 11-02, 현재 진행 작업)

근거: `OFF/00_실행명령_환경.md`, `OFF/01_actual_rollout_reversal.md`, `OFF/04_d2_recovery_coverage.md`, `OFF/logs/`, `OFF/tables/`, `OFF/scripts/`, `OFF/figs/`.

환경 (A): Jetson Thor aarch64, Python 3.12, `~/so101-env` (lerobot 0.6.2), 정책 객체를 GPU 에 올려 `predict_action_chunk` 만 호출, robot 클래스 생성 없음. 그림은 시스템 python3 (so101-env 에 matplotlib 없음). 분석 동안 사용자 `r12_collect.py record --session practice/r1_try` (pid 4142748, 13:20 시작) 가 떠 있었고 건드리지 않았다고 적힘 (지금은 r12/record 프로세스 없음 — ps 확인).

### 3.1 단계별 상태

| 순서 (00 §2) | 스크립트 | 상태 (11-02 16:18) | 근거 |
|---|---|---|---|
| 1 | q01_timeline.py | 완료 (15:28) | logs/q01.log, tables/q01_* |
| 2 | q01b_zones_reversal.py | 완료 (15:30) | logs/q01b.log, tables/q01b_* |
| 3 | q01c_summary.py | 완료 (15:43) | logs/q01c*.log, tables/q01c_* |
| 4 | q00_env_facts.py | 완료 (15:41) | tables/q00_env_facts.json |
| 5 | q02_seed_resample.py --n 64 | **진행 중** (15:35 시작, 170/223 상태 @ 2300 s; 재현 차 repG 0.0 · repU 0.0 로그 줄마다). 상태 구성: dense_A0B1 65 · S3_near_aligned 51 · S1_approach_moving 40 · S2_approach_static 39 · S6_moving_away 25 · S7_post_close_over 3. noise bank torch.randn((N,50,32), seed 2026), U (prefix 없음) vs G (기록 prefix · inference_delay) 짝 비교 | logs/q02.log, ps |
| 6 | q02b_metrics.py | 미실행 (출력 없음) | — |
| 7 | q05_state_pan_sensitivity.py (GPU) | 미실행 (`tables/q05_sensitivity.csv` 없음). 내용: state pan 만 Δ ∈ {−30…+30}° 바꾼 U 추론, '물리적으로 일관된 반사실 아님' 명시 | 스크립트 머리말 |
| 8 | q04_human_recovery_coverage.py | 완료 (15:36) | logs/q04.log, tables/q04_* |
| 9 | q04b_human_wrist_lost.py | 완료 (15:38) | tables/q04b_summary.json |
| 10 | q04c_export_human_pan.py | 완료 (15:41) | tables/q04c_* |
| 11 | q06_figs.py | 부분 (fig1, fig2, fig5 있음; fig3, fig4 없음) | figs/ |
| 12 | q03_rtc_tables.py | 미실행 (q02 결과 필요, `q03_pairs.csv`·`q03_group.csv` 없음) | 스크립트 머리말 |

계획되어 있으나 없는 문서 (00 §4): `02_offline_noise_seed_analysis.md` (분석 B), `03_rtc_effect.md` (RTC · Arm Filter 영향 분리), `05_r1_collection_recommendation.md` (R1 수집 방안 비교, 수집 안 함), OFF `analysis_handoff.md` (질문 1–10 답). → D.

### 3.2 분석 A — 실제 rollout 20 판 Pan 방향 반응 (OFF/01, A/C)

| 필드 | 내용 |
|---|---|
| 데이터 | 파일럿 12 (켬) + K1 A0–A3 (켬) + K1 B0–B3 (끔) = 20 판, diag 기록 (chunks npz, obs PNG, ticks, replay.npz rtc_off) |
| 목표 판정 (공식 pe 를 정답으로 쓰지 않음) | 목표대 = [사람 (3 cm 안 ≥ 5 편 p5–p95, 2–4 편 min/max ± 2.63°, ≤ 1 편 pe ± 5.3°) ∪ 같은 자리 정책 성공 파지 pan]. K1 사람 p5–p95 −35.0 … −31.6° (pe −35.4) vs 정책 성공 5 판 −25.7 · −25.2 · −25.6 · −28.6 · −22.9° → K1 목표대 −37.2 (또는 −35.0) … −22.9°. zone: under (가까운 끝보다 3° 넘게 덜 감) / aligned / over (먼 끝보다 8° 넘게 지나침) / undetermined. 반전 = present pan hysteresis 3° 전환점. wrist_lost = 본 뒤 ≥ 1 s 연속 안 보임 |
| 정량 결과 [실측] | 첫 닫힘 전 over 판 2/20 (A0 over 21.1 s, 먼 끝 넘은 최대 71.7°; B1 13.2 s, 74.0°); 나머지 18 판 전환점 63 개 모두 under/aligned/undetermined, 목표대 근처 3–17° 왕복. A0: 목표대 진입 4.1 s, over 4.6 s, 손목 놓침 6.9–15.9 s (9.0 s), −105° 15.2 s. B1: 진입 2.6 s, over 2.8 s, 놓침 3.9–15.6 s (11.7 s), −105° 14.5 s. 두 판 front 에는 큐브 계속 검출 |
| 지나침 시작 chunk | A0 chunk 6 (4.0 s, −18.8°, under, 손목 보임) · B1 chunk 30 (2.0 s, −4.3°, under, 손목 보임) 이 한 chunk 안에서 목표대 먼 끝을 17.3° / 13.3° 지나는 pan 계획; RTC 끔 재구성도 같음 (차 ≤ 1°) [재구성]. B1 chunk 31 (손목 보임) 은 RTC 끔이면 목표대 안, 기록은 prefix 이어받은 뒤 되돌아옴 = 실제 반전 16.0° |
| over 이후 방향 | 목표 쪽 실행 Δ ≥ 2° chunk: RTC 끔 0/32, 기록 RTC 1/32, 필터 뒤 1/32, Present 1/32. 반대쪽 ≥ 2°: RTC 끔 10/32, 기록 20/32. under 에서 RTC 끔 반대쪽 0/115, 기록 RTC 8/115. over 목표 쪽: A0+B1 RTC 끔 2/51, 기록 4/51; 손목 놓침 상태 1/37 · 1/37 |
| 필터 비교 | A0 (켬) · B1 (끔) 모두 −109° 이탈. 필터 뒤 − RTC \|최대\| 4.0° vs 0.0°. 큐브 각도 A0 +31°, B1 +2° → 필터 효과 분리 비교 아님 |
| 필터 끔 확인 | B: filter_log out − raw 최대 0.0°, Goal ≠ out pan 틱 34/2,271 (B1 32, clamp 때문). A: out − RTC 최대 4.0°, clamp 틱 259/2,561 |
| 해석 [해석] | 지나침 시작 = 손목에 큐브가 보이는 under 상태의 한 chunk 큰 pan 계획 (서보 · 필터 · RTC 탓 아님); 손목 시야에서 빠진 뒤 chunk 는 RTC 와 무관하게 목표 쪽 이동 거의 없음; 기록 RTC 가 '반대쪽 계속' 이 더 많음 (20 vs 10/32) = prefix 가 직전 진행을 이어 붙인 몫 → 03 문서에서 noise 64 개로 재확인 예정 (03 문서 없음) |
| 근거 | `OFF/01_actual_rollout_reversal.md`, `OFF/tables/q01b_*`, `q01c_*`, `OFF/figs/fig1_A0_B1_timeline.png`, `fig2_normal_vs_fail.png` |

### 3.3 분석 C — d2 사람 256 편 복구 커버리지 (OFF/04, A/C)

| 필드 | 내용 |
|---|---|
| 데이터 | `d2/data_coverage_audit/02_servo_timeline.parquet`, `a02_events.csv`, `a04_cube_positions.csv`, d2 dataset 손목 영상. 창 = 판 시작 … close_start (판 길이 중앙 15.6 s). 목표 = 그 판 자신의 첫 파지 pan (256 편 모두 첫 파지 성공). \|need\| < 1° 8 편은 방향 분류 제외 |
| 반전 빈도 (h 3°) | 전환점 있는 판 113/256, 전환점 170: overshoot_return 101 (95 판), early_backoff 18 (18), wrong_way_fix 50 (47). h 5°: 37 판 · 49; h 10°: 2 판 · 2 (ep 86 −98.6° 지남 11.6° 되돌림 13.1°; ep 98 −48.1°, 8.1°, 5.7°) |
| overshoot_return (h3) | 지난 각 중앙 3.5° [0.1–11.6], 되돌림 4.1° [3.1–13.1], lift −93.7°, 판 시작 3.0 s, 손목 큐브 보임 101/101; 101 중 51 은 팔 접은 자세 (lift < −90°) |
| 지나침 크기 ovs (248 편) | 50 % 1.76 · 75 % 3.45 · 90 % 4.86 · 95 % 6.44 · 99 % 7.88 · 최대 11.60°. ovs ≥ 3° 73 판, ≥ 5° 23, ≥ 8° 3, ≥ 15° 0, ≥ 30° 0 |
| 손목 놓침 | 닫기 전 손목에서 큐브 본 판 256/256, 처음 본 시각 p10/중앙/p90 0.0/1.4/2.5 s; 본 뒤 ≥ 1 s 연속 안 보인 판 **0/256**; 최장 ≥ 0.3 s 11 판, ≥ 0.5 s 3 판, 최대 0.8 s |
| 위치별 | 첫 이동 방향 = need 방향 243/256; '멈춤 뒤 같은 방향 계속' 263 건/220 판; K7 ovs 중앙 4.4°, 최대 11.6°, ≥ 5° 10 판 (가장 많음) |
| 요약 [실측] | '손목 시야 밖 + front 에만 큐브 + 목표를 15° 넘게 지나침' 상태와 그 상태에서 되돌아오는 시연은 d2 에 없음 |
| 해석 [해석] | A0 · B1 상태 (지나침 20–70°, 손목 놓침 수 s) 는 사람 시연 상태 분포 밖 → 이 상태의 정책 행동은 학습 데이터가 직접 정하지 않음. 이 결과가 R1-B2/B3 (지나침 · 손목 놓침) 시나리오 정의의 근거로 이어짐 (02 plan §14 와 같은 날) |
| 한계 | 손목 가시성 = 빨강 덩어리 검출 (가려짐 · 테두리도 '보임' 일 수 있음); 사람 지나침은 자기 파지 pan 기준 (roll 조정 섞일 수 있음); h 1–2° 행은 잡음 포함 가능 |
| 근거 | `OFF/04_d2_recovery_coverage.md`, `OFF/tables/q04_summary.json`, `q04_human_episodes.csv`, `q04_human_turnpoints.csv`, `q04_over_frames.csv`, `q04_by_position.csv`, `q04b_summary.json`, `OFF/figs/fig5_human_coverage.png` |

---

## 4. R1/R2 사람 시연 수집 — 이 프로젝트에서 'HIL' 에 가장 가까운 것 (RC, 10-30 … 11-02)

### 4.1 목적 · 문제 · 근거

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 목적 | d2 020000 첫 파지 실패를 줄이기 위한 추가 사람 시연: R1 = 접촉 전 Pan 방향 재정렬 (복구), R2 = 파지 직전 국소 정렬 · 접근 깊이 · 닫힘 타이밍 | A (문서) |
| 근거 (as stated) | 첫 파지 실패 12 건 중 R2 계열 10 건; 실패 대부분 'close short, cube ahead'; −109° 이탈은 손목에서 큐브가 사라진 뒤 같은 방향 회전 (PD/13, OFF/04) | A / C |
| 형식 | 정책 rollout 중 사람이 개입하는 방식이 **아님**. 리더 팔 원격조종 시연을 '오차 상태' 에서 시작 (준비 단계는 녹화 안 함) 하는 별도 LeRobot dataset. d2 와 같은 features · fps 30 · task 문장 · 캘리브레이션 · action = 리더 값 (필터 · clamp 없음, max_relative_target=None). R1/R2 만으로 학습하지 않고 d2 와 섞는 전제, 혼합 비율 · 학습 단계 수 미정 (Ablation 대상) | A (설계) / D |
| 정책 실패 직후 사람 교정 | R1/R2 설계에는 없음. 별도로 `d2/vision_probe/실험설계.md:173-176` 의 'Recovery 시연 (판정 1·4 일 때 수집)' 항목에 "정책 실패 직후 이어서 사람이 교정하는 판도 포함한다", 규모 64–96 편, 학습안 R1 (expert only, d2-holdout + recovery) · R3 (VLM + recovery) — 설계만 (D) | D |

### 4.2 정의 변천 (RC/02 §1–§14, RC/analysis_handoff.md)

| 시점 | R1 정의 | R2 정의 | 수량 | 신뢰도 |
|---|---|---|---|---|
| 10-30 최초 | R1-L/R (TCP 3–6 cm 좌우) 4/4, R1-OL/OR (pan 10–20° 지나침) 2/2, R1-TL/TR 2/2 = 16; R1C-REGRASP 설계만 (수량 0) | R2-AHEAD 8 · LOW 4 · LEFT 6 · RIGHT 6 · HIGH 4 · READY 4 = 32 | 16 / 32 | A |
| 10-30 사용자 결정 | L3 R3 OL3 OR3 TL2 TR2, 지나침 25·30°, 판마다 Pan 목표 = K 기준 + 어긋남 | R2-LEFT/RIGHT 1.5/2.5/3.5 cm (pan 3.1–12.0°) | | A |
| 11-02 §11 | 녹화 중 어긋남 + Space 표시: R1-OVER 6 · UNDER 6 · TL/TR 2+2 | | | A |
| 11-02 §12 | R1-PAN-L/R 4/4 · R1-OVER 4 · R1-DRIFT 4 (녹화 중 오차 + Space) | R2-DEPTH 8 · AHEAD 8 · LEFT 4 · RIGHT 4 · READY 8 (손목 화면 시작 영역으로 정의, 닫기 영역 u 0.255–0.432, v 0.633–0.78) | 16 / 32 | A |
| 11-02 §13 (3차 지시서) | 잘못된 시작 자세는 준비 단계 (녹화 안 함): R1-HOME-VIS/OUT, R1-MID-VIS/OUT 각 4 | 그대로 | | A |
| **11-02 §14 (4차, 현재 기준)** | R1-A 초기 방향 (±15–30°) 4 · R1-B1 접근 중 반전 (±15, 20) 4 · R1-B2 지나침 (±15–25) 4 · R1-B3 손목 놓침 (±20, 25) 4. 자리 K1–K8 각 1 + 자유 점 F1–F4 각 2. 녹화는 되돌리는 행동부터 | R2 32 그대로 | 16 / 32 | A (정의) / D (수집) |

- K 기준 pan (d2 t1k+t3k 125 편 파지 순간 중앙값): K1 −33.5 · K2 −1.9 · K3 31.2 · K4 −46.2 · K5 −2.6 · K6 44.6 · K7 −70.7 · K8 69.5°. 11-02 연습 6 판에서 사람 파지 pan 이 K 기준과 +8.7, +4.5, +7.0, −3.9, ≈−1, −6.3° 달랐음 (±9° 안팎) → 측정 Pan 오차는 신뢰도 low/medium 으로만 기록 [A].
- 안전 (config `safety`): BLOCK = 관절값 없음/NaN · \|pan\| > 95° · Pan 한계 10° 안 · 리더−팔로워 > 25°; 그리퍼 < 15 는 WARN (11-02 완화). 계획 \|Pan 목표\| ≤ 92°, 실물 평가의 −109° 이탈 재현 금지 [A].
- R1 복구 측정 열 (4차, `r12_episodes.csv`): start_pan_deg, approach_stage_at_start (early < 0.4 ≤ mid < 0.85 ≤ late, lift 진행률), first_pan_move_dir (toward/away) · deg, pan_reversal · _t_s · _kind, pan_change_before/after_reversal_deg, cube_reacquired_in_wrist · _t_s, first_grasp_success, final_success, recovery_completed, grasp_start_t_s, pan_error_at_grasp_deg 등 [A, 정의].
- R2 열: local_alignment_type, nominal_local_error_cm, cube_relative_position_in_wrist (u, v, 넓이), approach_depth_category (partial/not_entered/lateral_offset/sufficient), first_close_result (grasped/missed_then_retry/failed), retry_count, r2_wrist_start_in_region [A, 정의].
- QA (RC/06): d2 형식 일치, 길이, timestamp, NaN, 프레임당 > 20° 변화, 시작 자세 재검사, 파지 시각, 끝 자세 (lift < −90, elbow > 85), 첫 화면 손목/front 큐브, close_zone (사람 d2 도 약 23 % 밖), 저장 무결성, R1 r1_start · r1_recovery 열 [A, 정의].
- 로봇 미연결 검증 (RC/05, 10-30): 단위 37/37, 오류 6/6, Preview 흐름 13/13, 진입점 + 실제 lerobot `record()` 가짜 로봇 13/13 PASS; features · fps · robot_type · codebase_version d2 와 같음 [A].

### 4.3 세션별 실제 저장 편수 (dataset/meta/info.json total_episodes, r12_attempts.jsonl 사건)

| 세션 | 정의 세대 | 녹화 시각 | info.json total_episodes (frames) | attempts: saved / discarded | r12_episodes.csv 행 | 결과 (first/final) 입력 | 시나리오 | 신뢰도 |
|---|---|---|---|---|---|---|---|---|
| `main_k8/r1_realign_pilot` | 4차 계획 16 | — | **dataset 없음** | — | — | — | 계획 R1-A/B1/B2/B3 × 4 (`r12_plan.csv` 16 행) | A |
| `main_k8/r2_pregrasp_pilot` | 계획 32 | — | **dataset 없음** | — | — | — | AHEAD 8 · DEPTH 8 · LEFT 4 · RIGHT 4 · READY 8 | A |
| `practice/r1_trial_old_20261102` | 10-30 옛 방식 | run 20261102_103609 | 3 (1815) | 3 / 2 | 3 | 미입력 | R1-L (K7?), R1-R, R1-OL (02 §11 표: K7 / K8 / K3) | A |
| `practice/r1_trial` | §11 (녹화 중 어긋남) | run 20261102_110655 | 3 (1778) | 3 / 2 | 3 | 미입력, realign_mark_frames 빈칸 | R1-UNDER, R1-OVER, R1-TL | A |
| `practice/r1_try` | §12 (PAN-L/R · OVER · DRIFT, Space) | 13:20 run 20261102_132053 | 4 (2684) | 4 / 0 | **0** (sync 안 됨) | 미입력, Space 0 (handoff) | 계획 R1-OVER K7, R1-PAN-R K5, R1-DRIFT K8, R1-PAN-L K4 | A |
| `practice/r1_try2` | §13 (HOME/MID) | 13:52 run 20261102_135216 | 2 (794) | 2 / 1 | 2 | 미입력 | R1-MID-OUT K6, R1-MID-VIS K4. ep1 첫 프레임 리더 −26.5 vs 팔로워 −60.7 (34°, 0.3 s 에 28° 튐); ep1 그리퍼 안 열고 끝 (파지 시작 없음); QA: ep0 시작 Pan +68.7 (K6 기준 +24.1), 파지 시작 9.97 s Pan 오차 −1.8° | A |
| `practice/r1_try3` | §14 (4차, A/B1/B2/B3) | 14:23 · 14:36 · 14:39 (빈 dataset 3 개) · 14:43 run | **0** | override 1 건만 | 0 | — | 계획 R1-B3 F2, B1 F1, B2 K1, A K2 | A |
| `practice/r2_trial` | 10-30 R2 | 10-30 16:06, 11-02 10:03 | **0** | — | 0 | — | 계획 R2-HIGH K3, AHEAD K8, LEFT K5 | A |

- 합계: 연습 R1 계열 저장 12 편 (3 + 3 + 4 + 2), 정의 세대가 모두 다름, 결과 라벨 0 편. R2 저장 0 편. 본 파일럿 세션 저장 0 편.
- 11-02 오전 10:03 · 10:27 · 10:30 · 10:56 · 11:00 실행은 준비 단계 Esc 로 녹화 0 (BLOCK: 쉬는 자세 lift −102.9° 와 닫힌 그리퍼, 오전 완화 전 규칙) [A, RC/02 §14].
- 혼동 주의: `r1_trial` 폴더 notes.md 의 여러 실행 결과 줄에 '에피소드: 이번 0개' 가 반복되지만 마지막 실행 (11:06) 은 '이번 3개 · 버린 2번' [A].

### 4.4 R1/R2 를 쓴 학습 · 평가 계획

- 혼합 구성 d2+R1, d2+R2, d2+R1+R2 는 형식상 합칠 수 있음 (같은 features · fps · task), 혼합 비율 · 가중치 · 학습 단계 미정 [A/D, RC/02 §13].
- R1/R2 학습 뒤 실물 평가 프로토콜은 파일에서 찾지 못함 (세션의 `eval/`, `train/` 폴더는 비어 있음 — ls 로 존재만 확인, 내용 미확인). PD/14 는 "R2 전후 비교에서는 필터 설정을 하나로 고정" 만 적음 [D].

---

## 5. Held-out 평가 세트 H (scope 4)

| 필드 | 내용 | 신뢰도 |
|---|---|---|
| 정의 | 평가 전용 32 판 (`h_t1`: T1 Known, U1–U8 각 4 판 = 각도 0 · ↺30 · ↻30 · 45, seed 2901), 세션 `main_k8/heldout_h`, repo `oxr/so101_k8_heldout_h`. 어떤 학습 · 가중 · LR/step · ckpt 선택에도 쓰지 않음 (`train_weighted.py` 가 heldout 경로 거부) | A (정의) |
| 위치 | U1 (−24.1, 32.0) · U2 (−26.1, −13.0) · U3 (−10.6, 9.5) · U4 (−11.1, −7.0) · U5 (−8.6, 30.0) · U6 (−22.6, −1.5) · U7 (−14.6, 20.0) · U8 (−5.6, 21.0) cm. d2 학습 큐브에서 2.0–2.8 cm (≥ 3 cm 자리는 학습 위치 볼록 껍질 안에 없음, 최대 2.85 cm) | A |
| 녹화 여부 | **녹화 안 됨.** `~/so101_runs/main_k8/heldout_h` 없음; config 의 U1–U8 모두 `confirmed: false` (파일 수정 시각 10-27 17:28); 미리보기 계획 `sampling_ablation/H/plan_preview/` 만 있음 | A |
| 녹화 절차 (D) | U 위치 확인 → `layout_plan.py set-known U# --confirm --config config/redbox8_heldout_h.yaml` → `plan --group h_t1` → `record_ui.py --session main_k8/heldout_h --target-episodes 32` (16 판 × 2) → `check_dataset.py` (실측 좌표 · 각도로 평가) | D |
| 로봇 평가 U layout | sampling_ablation 실험설계 6 절: UF = U3·0, U4·L30, U6·L30, U8·0 / UN = U2·45, U1·45, U6·0, U7·0 (H 32 판 안에 포함) | D |
| **이름 충돌 (주의)** | 파일럿 (PD/07, 10) 의 'U1–U8' 은 H 의 U1–U8 좌표가 **아니다** — 파일럿 U 는 지정 좌표 없이 임의로 놓은 자리 (예: 파일럿 U3 (−21.6, 30.6) vs H U3 (−10.6, 9.5); 파일럿 U4 (−28.9, 32.4) vs H U4 (−11.1, −7.0)). 보고서에서 두 U 를 섞으면 안 됨 | A |
| 근거 | `/home/user/so101_runs/main_k8/d2/sampling_ablation/H/H_준비.md`, `/home/user/so101_boxpick/config/redbox8_heldout_h.yaml`, `/home/user/so101_runs/main_k8/d2/sampling_ablation/실행기록.md:86` | |

---

## 6. HIL / human-in-the-loop 용어 검색 결과 (scope 3)

검색 범위: `~/so101_runs`, `~/so101_boxpick` 아래 `*.md`, `*.yaml`, `*.yml`, `*.py` (grep -rI).

| 용어 | 결과 |
|---|---|
| `HIL` (단어 경계), `human-in-the-loop`, `human in the loop` | **0 건** |
| `DAgger` / `dagger` (대소문자 무시) | **0 건** |
| `intervention` (대소문자 무시) | **0 건** |
| `개입` | 3 건, 모두 HIL 정의 아님: `so101_runs/e0_j0/report_for_dr_lee.md:71` ("`/real/torque False` — 사람 개입 [추정]"), `:203` ("그 뒤 사람 개입으로 중단"), `so101_runs/reference/analysis_20261019/report.md:61` ('1개입니다' 문자열 일치, 무관) |
| `교정` | 5 파일, 모두 '사람 시연의 좌우 교정 동작' 또는 정책 교정 의미: `main_k8/d2/vision_probe/실험설계.md:61, :144, :175`, `vision_probe/실험설계_부록_영상품질.md:107`, `main_k8/d2/grasp_pose/분석_리포트.md:130`, `reference/aswin_task2_compare/비교_리포트.md:95, :115`, `aswin_task2_compare/demo_kinematics.py:1` |

결론: **HIL (human-in-the-loop) 은 이 프로젝트 파일 어디에도 정의되어 있지 않다.** 가장 가까운 것은 (1) R1/R2 오차 상태 시작 원격조종 시연 (§4, 오프라인 데이터 추가 방식, 정책 rollout 중 개입 아님), (2) `d2/vision_probe/실험설계.md:173-176` 의 Recovery 시연 설계 중 "정책 실패 직후 이어서 사람이 교정하는 판도 포함한다" 한 줄 (DAgger 류에 가장 가까운 문장, 설계만, 수집 없음), (3) PD/13 §6 의 독립 안전 정지 조건 후보 S4b/S5 (사람 개입 트리거로 쓸 수 있는 신호이나 문서에는 '안전 정지' 로만 정의, 구현 안 함).

---

## 7. 지표 정의 모음 (성공률 · 첫 파지 · Pan 오차 · 접근 정확도)

| 지표 | 정의 | 출처 | 상태 |
|---|---|---|---|
| 최종 성공 (P/F) | eval_ui 에서 사용자가 판 끝 (상자에 넣었거나, 멈췄거나, 1 분 넘게 헤맴) 에 누른 판정. 성공률 = P / 저장 판 | PD/07 §3, EV/index.md | 사용 중 (B) |
| 판 메모 | `<번호> <이름> first=<Y|N> final=<Y|N> …` (파일럿), `first= lift= drop= final= side=C|L|R|? depth=D|S|E|?` (12) | PD/07 §3.1, PD/12 §4 | 정의만, **실제 입력 0** |
| 첫 파지 (자동) | §2.7 정의 (첫 닫힘 c, on, 그리퍼 바닥, 들어 올림 ≥ 4 cm, 놓침, 깊이 · 좌우 분류) | PD/11 §1 | 사용 중 (A) |
| 1 s 이동 비율 (gain) | (chunk[idx] − 시작 pan) / need, idx 29 (≈ 1 s 실행) · idx 49 (계획); 닫힌 고리: (명령[t+30] − state[t]) / (pe − state[t]) | PD/10 §3.1, handoff §1 | A |
| need · pe | need = pe − s0; pe = 판 시작 front 사진 좌표 → bearing → pan (09) | PD/09 | A |
| 첫 닫힘 Pan 오차 | (pe − pan) × need 부호 (+ = 못 미침), σ_coord · σ_grasp 로 각각 나눈 값 따로 | PD/10 §6 | A |
| coord_status | valid_near_K / valid_off_K / invalid_detection / invalid_calibration | PD/09 §5 | A |
| zone | under / aligned / over (먼 끝 + 8°) / undetermined, 목표대 = 사람 ∪ 정책 성공 파지 pan | OFF/01 §2 | A |
| 반전 · 전환점 | present pan hysteresis 3° (h 1/2/3/5/10° 표) | OFF/01 §2, OFF/04 §1 | A |
| 손목 접근 정확도 | 닫힘 시작 손목 화면 큐브 v (사람 0.64–0.76) · u (사람 0.26–0.57); 닫기 영역 u 0.255–0.432, v 0.633–0.78, 넓이 ≥ 0.08 (사람 main 88.6 % / all 76.5 %) | PD/11, PD/13, RC/02 §12, 메모리 | A |
| TCP 상대 높이 | 닫힘 시작 TCP z − 최근접 사람 10 편 중앙 (사람 p10–p90 폭 0.75 cm). FK 절대 위치는 K1 에서 4–5 cm 틀림 → 상대 차로만 | PD/11 §3, PD/13 §4 | A (한계 있음) |
| 정지 구간 · t90 | 팔이 시작 pan 3° 안인 chunk 수 · 시각; state_t90_s | PD/10 §4, PD/07 §9 | A |
| RTC seam · back | chunk 경계 seam 최소, 실행 구간 안 되돌림 최대, RTC 끔 반사실 | PD/10 §5 | A |
| 서보 추종 | 최적 지연 (0–10 틱), \|sent − present\| p50/p95 (움직일 때), clamp 틱, 필터 변경 p95 | PD/06, PD/10 §7 | A |
| 안전 정지 후보 | S1–S5, S4b | PD/13 §6 | 오프라인 평가만 (D 구현) |
| R1 복구 지표 | first_pan_move_dir, pan_reversal(_t_s), cube_reacquired_in_wrist(_t_s), recovery_completed, pan_error_at_grasp_deg | RC/02 §14 | 정의만 (D) |
| R2 지표 | approach_depth_category, first_close_result, close_zone, r2_wrist_start_in_region | RC/02 §13, RC/06 | 정의만 (D) |

---

## 8. 실물 평가 계획 · 평가 데이터셋 목록

| 계획 | 내용 | 상태 | 근거 |
|---|---|---|---|
| 파일럿 12 판 (07) | U3 → VERIFY → 11 판 | **완료** 10-29 | PD/07, PD/10 |
| 필터 A/B ABBA 16 판 (12) | K1·K3·K6·K7 × 2 × 2 조건 | **부분 실행** (K1 만 4 + 4); 나머지 미실행 | PD/12, PD/13 |
| 대응 필터 비교 (14 제안) | 큐브 각도 0 고정, 켬·끔 번갈아, 같은 자리 · 같은 시작 자세 | 제안만 (D) | PD/14 §6 |
| Held-out H 녹화 + U layout 로봇 평가 | 32 판 녹화 → H 평가 (sampling ablation 실험설계 6 절의 UF/UN 8 layout) | 미녹화 (D) | §5 |
| sampling ablation A2 오프라인 평가 · A2r · A0′ | eval_hook | 미실행 (일시정지) | §1 |
| R1/R2 본 수집 (16 + 32) | 4차 정의 | 미녹화 (연습만) | §4 |
| R1/R2 혼합 재학습 · 평가 | d2+R1 / d2+R2 / d2+R1+R2 | 미정 (D) | RC/02 §13 |
| 안전 정지 (S5/S4b) 구현 · harness 검증 | rollout_logged send 경로 → shutdown_event | 미구현 (사용자 승인 필요) | PD/13 §6 |

평가 데이터셋 (실물 rollout 기록): `EV/rollouts/` 6 폴더 (§2.2) — 10-29 4 폴더는 `diag/` (chunks.jsonl, chunks/*.npz 원 chunk 50×6 · noise 50×32 · prefix, obs PNG, ticks.csv, manifest.json, summary.json, replay/) 포함, 10-26 2 폴더는 dataset · debug.log (· filter_log) 뿐.

---

## 9. 기록된 불일치 · 충돌

1. **inference_delay**: PD/02·08·handoff "이후 11–12" vs OFF/01 "이 20 판 기록값 12 (와 0)". (OFF/01 §1 이 직접 지적.)
2. **필터 A/B 실행 범위**: PD/12 계획 = 4 위치 ABBA 16 판; 실제 = K1 만 4 + 4 (2 실행). 메모리 노트에는 "user approval 대기" 로 남아 있음. 축소 이유 문서 없음.
3. **큐브 각도**: 파일럿 · A/B 프로토콜은 0°; 실제 측정은 파일럿 7/11 판 \|각도\| > 10°, A/B ON +31/+31/+31/−45°, OFF +23/+2/+3/−15°.
4. **시작 pan**: pose_check 는 'OK' 로 기록했지만 +5.4 … +7.0° 는 학습 시작 범위 (−14.8 … +3.8°) 밖 (PD/10 §2). pose_check 의 판정 기준이 범위 밖도 OK 로 둔 것 (기록만 하는 규칙).
5. **파일럿 성공률 표기**: index.md 는 실행별 0 % · 36 %, 문서들은 합쳐서 P 4/12 (33 %).
6. **U1–U8 이름 충돌**: 파일럿 U (임의 자리) ≠ H U (지정 좌표) (§5).
7. **목표 pan 기준 차이**: K1 사람 파지 −35.0 … −31.6° vs 정책 성공 파지 −22.9 … −28.6°; R1 계획의 K 기준 pan (−33.5) 은 연습 사람 파지와 ±9° 다름. 지표마다 기준 (pe, 목표대, K 기준, 자기 파지 pan) 이 다르다.
8. **서보 추종 수치**: PD/06 (기존 5 판, 움직임 \|Δsent\| > 0.2°) p50 0.64–1.32° vs PD/10 (파일럿) 움직일 때 p50 4.2–7.0°. 정의 · 문턱이 달라 직접 비교 불가 (문서가 차이를 설명하지 않음).
9. **필터 영향 해석**: 사용자 관찰 '켬에서 좌우로 벗어남 · 사선 하강' (B) vs 측정 (손목 가로 변화폭 켬 2 배 · FK 기울기 켬 큼, 그러나 필터 전 RTC 명령이 이미 기울었고 front 영상은 반대 방향) — PD/13·14 는 '필터 때문인지 구분 불가' 로 결론.
10. **q02 출력 파일**: `OFF/tables/q02_states.csv` (3 상태) · `q02_seed_pan.npz` (3 상태, 15:35:12) 가 현재 진행 중인 223 상태 실행 (15:35 시작) 의 최종 출력이 아님 (스크립트가 끝에만 씀) — 보고서에 인용하면 안 됨.
11. **r1_try r12_episodes.csv**: dataset 4 편인데 sidecar 0 행 (sync · QA 미실행, handoff "그대로 둠").

---

## 미확인/누락 목록

1. 10-26 try3 (2 판) · try3_filt (3 판) 의 P/F 판정 — 기록 없음 (run_rollout.sh 는 판정 안 남김).
2. 10-29 6 실행 모두 판 메모 (first/final, side, depth) 미입력 → 사람 눈 관찰 기반 첫 파지 · 깊이 기록 없음 (자동 분류만 있음).
3. 필터 A/B 를 K1 만으로 축소한 이유, filt_off 실행이 33 분 (17:08–17:41) 걸린 이유 — 파일에서 찾지 못함.
4. OFF 의 02 · 03 · 05 문서, OFF analysis_handoff.md, fig3 · fig4, q02b · q03 · q05 출력 — 아직 없음 (계획). q02 최종 결과 (223 상태 × 64 noise) — 진행 중.
5. q02_states.csv / q02_seed_pan.npz (3 상태) 를 만든 이전 실행의 명령 (`--limit 3` 추정) — 로그가 덮어써져 확인 불가.
6. sampling_ablation A0/A1 오프라인 평가 수치 — 이 조사 범위에서 읽지 않음. A2 평가 · A2r · A0_s2002 — 미실행.
7. Held-out H — 녹화 안 됨; H 기반 성공률 · 접근 정확도 값 없음.
8. R1/R2 본 수집 0 편; 연습 12 편 결과 라벨 0; R2 저장 0 편; 4차 정의 (R1-A/B1/B2/B3) 로 저장된 편 0 (r1_try3 0).
9. R1/R2 학습 혼합 비율 · 학습 설정 · 학습 뒤 실물 평가 프로토콜 — 정의 없음.
10. HIL / human-in-the-loop / DAgger / intervention 정의 — 파일 어디에도 없음. '정책 실패 직후 사람 교정' 은 vision_probe 실험설계 한 줄 (설계만).
11. 안전 정지 S5/S4b — 구현 · harness 검증 · 실물 적용 없음; 오경보율 · 놓침률 확정 안 됨 (20 판).
12. off-K 자리 좌표 정확도 (pe) — 검증 안 됨 (간접 점검만). off_K 판 Pan 오차 4.8° 가 정책 오차인지 정답 오차인지 구분 불가.
13. 시작 pan (+5–7°) 효과 — 실물에서 학습 범위 안 시작 자세로 같은 위치를 다시 해 보지 않음 (반사실만).
14. `PD/tables/p10_*` (09 문서가 언급하는 좌표 검증 표) — tables/ 목록에서 보이지 않음 (다른 위치일 수 있음, 미확인). `PD/notes/` 폴더는 비어 있음.
15. R1/R2 세션의 `eval/`, `train/` 하위 폴더 내용 — 존재만 확인, 내용 미확인.
16. 실물 '물리적 접근 깊이' · 접촉 · 쥐는 힘 — 어떤 실험도 측정하지 않음 (손목 v · 그리퍼 값 · FK 상대 높이만).
