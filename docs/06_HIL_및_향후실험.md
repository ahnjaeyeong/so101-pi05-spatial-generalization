# 06. HIL 및 향후 실험

---

## 1. "HIL" 은 파일에서 어떻게 정의돼 있나

`~/so101_runs`, `~/so101_boxpick` 아래 `*.md`, `*.yaml`, `*.yml`, `*.py` 전체 검색 결과 (A):

| 검색어 | 결과 |
|---|---|
| `HIL`, `human-in-the-loop`, `human in the loop` | **0건** |
| `DAgger` | 0건 |
| `intervention` | 0건 |
| `개입` | 3건 — 모두 HIL 정의 아님 (E0_J_0 보고서의 "사람 개입으로 중단" 2건, 무관한 문자열 1건) |
| `교정` | 사람 시연의 좌우 교정 동작, 또는 정책 교정 의미로만 사용 |

(위 표는 조사 첫 검색 (11-02 16:10 무렵) 결과다. 그 뒤 16:32–16:37 에 오프라인 Pan 반전 분석이 끝나며 아래 두 파일이 처음으로 "HIL" 을 정의했다.)

| 파일 (수정 시각) | HIL 관련 내용 |
|---|---|
| `R/main_k8/d2/pan_inference_diagnostic/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md` (11-02 16:32) | 제목 "R1 데이터 수집 방향 비교 (수집 · HIL 구현 안 함)". **방안 B — 정책 실행 중 인간 교정 (HIL)** 을 방안 A (수동으로 만든 복구 상태에서 시연) 와 비교 |
| `…/offline_pan_reversal_filter_off/analysis_handoff.md` (11-02 16:37) | "하지 않은 것: HIL 구현"; Q9 "추가 데이터는 수동 OVER 복구와 HIL 교정 중 어느 쪽이 더 적합한가" → **1차 = 방안 A, HIL (방안 B) 은 2차** [제안] |

**결론: 현재 파일 기준 HIL = "정책 실행 중 실패 상태에서 정책을 멈추고 사람이 리더 팔로 이어서 교정하는 시연을 녹화하는 방식" (방안 B). 정의·비교·절차 제안만 있고 구현·실행은 없다 (D).**

### 1-1. 방안 A (수동 복구 상태 시연) vs 방안 B (HIL) — 05 문서 비교 요약
| 항목 | 방안 A (수동 복구 상태) | 방안 B (HIL, 정책 실행 중 교정) |
|---|---|---|
| 시작 상태 | 녹화하지 않는 준비 단계에서 사람이 만든 '지나친·놓친' 자세 | 정책이 실제로 만든 잘못된 상태 |
| 실패 상태와 일치 | 자세·pan 오차·손목 가시성을 맞춰야 함 (현재 R1-B2/B3 는 '팔 일부 폄 · 15–25°' 라 실패 상태 '팔 접은 자세 lift ≈ −100°' 와 다름) | 그대로 일치 |
| 진행 속도·RTC prefix | 정지 상태에서 시작 → 재현 어려움 | 실제 진행 중 상태 |
| 필요한 장치 | 현재 r12 도구로 가능 (구현·시험 완료) | 정책 정지 → RTC/Action Queue 폐기 → 리더를 팔로워 자세에 동기화 → 단일 writer 전환 → 녹화. 새 구현 + 가짜 팔 harness 안전 검증 필요. 정책과 teleop 이 동시에 팔로워에 명령하는 구성은 만들지 않음 |
| 안전 | 천천히 만든 자세에서 시작 | 전환 순간 리더–팔로워 차이로 급한 움직임 위험 (연습에서 34° 차로 28° 튄 사례) |
| 수집 효율 | 판당 1번 확실 | A0·B1 형 실패는 20판 중 2판 |
| 데이터 일관성 | d2 와 같은 녹화 경로 (action = 리더) | 정책 구간과 사람 구간이 한 판에 섞임 → 학습에 쓸 구간 결정 필요 |

### 1-2. 05 문서 제안 [D]
1. 1차는 방안 A. R1-B2 (지나침)·R1-B3 (손목 놓침, front 보임) 시작 단계에 **팔 접은 자세 (lift −95 … −103°)** 를 추가, 지나침 크기를 목표대 끝 기준 **15·25·40° 이상**으로 넓힘, 손목 상태를 '위 테두리로 빠짐' / '안 보임' 으로 나눔, 좌우 모두.
2. 수집 뒤 R1 시작 프레임 분포를 A0·B1 의 over 상태 51개와 비교.
3. 방안 B (HIL) 는 2차, 별도 설계·harness 검증 먼저.
4. 평가 지표: 같은 '손목 놓침·front 보임' 상태 (T4) 에서 실행 구간 목표 쪽 비율, 기준값 U 7.7% · G 4.3% (2,368 seed) 를 학습 전후 비교.
5. RTC 영향 (index ≤ 19 목표 쪽 U 9.2% → G 0.5%) 은 따로 본다.

### 1-3. 그 밖에 HIL 에 가까운 기존 문장
- `~/so101_runs/main_k8/d2/vision_probe/실험설계.md:173-176` Recovery 시연 항목: "정책 실패 직후 이어서 사람이 교정하는 판도 포함한다", 64–96편, 학습안 R1 (expert only + recovery) · R3 (VLM + recovery). 설계만 (D).
- pan_inference_diagnostic 13 의 독립 안전 정지 후보 S4b / S5 (방안 B 의 전환 트리거로 쓸 수 있는 신호), 구현 안 함 (D).

보고서에 "HIL" 을 쓸 경우: **HIL 은 2차 방안으로 정의·제안만 됐고, 실행된 것은 R1/R2 '수동 복구 상태 시연' 수집 도구와 연습 녹화 (12편) 뿐**이라고 적어야 한다.

---

## 2. R1/R2 시연 수집 (10-30 ~ 11-02, 진행 중)

### 2-1. 목적과 근거
- 목적: d2 020000 첫 파지 실패를 줄이기 위한 추가 시연. **R1** = 접촉 전 Pan 방향 재정렬 (복구), **R2** = 파지 직전 국소 정렬·접근 깊이·닫힘 타이밍 (A, 문서).
- 근거 (A/C): 실물 첫 파지 실패 12건 중 R2 형 10건, R1 형 2건 (−109° 이탈) (PD/13); 지나침·손목 놓침 상태가 사람 256편에 없음 (OFF/04).
- 형식: d2 와 같은 features·fps 30·task 문장·캘리브레이션, action = 리더 값 (필터·clamp 없음). 잘못된 시작 자세는 녹화하지 않는 SETUP 단계에서 만들고, 녹화는 바로잡는 행동부터. R1/R2 만으로 학습하지 않고 d2 와 섞는 전제. **혼합 비율·학습 단계 수 미정** (D).
- 도구: `~/so101_runs/main_k8/r1_r2_collection/tools/r12_collect.py` (record_ui 재사용, lerobot `record()` 그대로 + SETUP 단계·안전 게이트·Tk 뷰어). 로봇 미연결 시험: 단위 76, 오류 6, preview 13/11, 가짜 로봇 e2e 19 PASS (A).

### 2-2. 정의 변천 (A)
| 시점 | R1 | R2 | 수량 |
|---|---|---|---|
| 10-30 최초 | R1-L/R (TCP 3–6 cm 좌우), OL/OR (pan 10–20° 지나침), TL/TR | AHEAD 8 · LOW 4 · LEFT 6 · RIGHT 6 · HIGH 4 · READY 4 | 16 / 32 |
| 10-30 사용자 결정 | 지나침 25·30°, 판마다 Pan 목표 = K 기준 + 어긋남 | LEFT/RIGHT 1.5/2.5/3.5 cm | |
| 11-02 (§11–12) | 녹화 중 어긋남 + Space 표시 (OVER/UNDER/PAN-L/R/DRIFT) | DEPTH 8 · AHEAD 8 · LEFT 4 · RIGHT 4 · READY 8 (손목 화면 시작 영역) | 16 / 32 |
| 11-02 (§13) | 시작 자세 HOME/MID × 손목 보임/안 보임 | 그대로 | |
| **11-02 (§14, 현재)** | **R1-A 초기 방향 (±15–30°) 4 · B1 접근 중 반전 4 · B2 지나침 4 · B3 손목 놓침 4**; 자리 K1–K8 + 자유점 F1–F4 | 그대로 | 16 / 32 |
- 안전 BLOCK: 관절값 NaN, \|pan\| > 95°, Pan 한계 10° 안, 리더−팔로워 > 25° (11-02 완화 후). 실물 평가의 −109° 이탈은 재현하지 않음.
- 사용자 피드백 (B, 메모리): "범위가 너무 빡빡 … 값보다 대략적인 위치랑 방법이 중요".
- 연습에서 측정: 사람 파지 pan 이 K 기준 pan 과 +8.7 / +4.5 / +7.0 / −3.9 / ≈−1 / −6.3° 차이 (±9° 안팎) → 계획된 3–12° pan 오프셋이 사람 자체 산포 안에 있음 (A).

### 2-3. 실제 저장 현황 (A, dataset/meta/info.json)
| 세션 | 정의 세대 | 저장 편 | 결과 라벨 |
|---|---|---|---|
| `main_k8/r1_realign_pilot` (본, 16 계획) | 4차 | **dataset 없음** | — |
| `main_k8/r2_pregrasp_pilot` (본, 32 계획) | | **dataset 없음** | — |
| `practice/r1_trial_old_20261102` | 10-30 | 3 | 미입력 |
| `practice/r1_trial` | §11 | 3 | 미입력 |
| `practice/r1_try` | §12 | 4 (sidecar 0행) | 미입력 |
| `practice/r1_try2` | §13 | 2 | 미입력 (ep1 리더−팔로워 34° 차로 시작해 0.3 s 에 28° 튐 → 이후 RESET 흐름 수정) |
| `practice/r1_try3` | §14 | 0 (빈 dataset 3개, Esc 종료) | — |
| `practice/r2_trial` | | 0 | — |
- 합계: R1 계열 연습 12편 (정의 세대 모두 다름), 결과 라벨 0, **R2 0편, 본 수집 0편.**

---

## 3. Held-out 평가 세트 H (계획, 녹화 안 됨)
- 정의 (A): 평가 전용 32편 (`h_t1`, T1 Known), 지정 위치 U1 (−24.1, 32.0) · U2 (−26.1, −13.0) · U3 (−10.6, 9.5) · U4 (−11.1, −7.0) · U5 (−8.6, 30.0) · U6 (−22.6, −1.5) · U7 (−14.6, 20.0) · U8 (−5.6, 21.0) cm × 각도 4 (0 · ↺30 · ↻30 · 45). 학습 큐브에서 2.0–2.8 cm (볼록껍질 안에 ≥3 cm 지점 없음). 학습·가중·체크포인트 선택에 쓰지 않음 (`train_weighted.py` 가 경로 거부).
- 상태: **녹화 안 됨.** `~/so101_runs/main_k8/heldout_h` 없음, config `redbox8_heldout_h.yaml` U1–U8 모두 `confirmed: false`.
- 설계 충돌: sampling_ablation v2 는 "U 마다 각도 2개 × 2회", H_준비.md 는 "U 마다 각도 4개 × 1회".
- 주의: 10-29 파일럿의 "U1–U8" 은 이 좌표가 아니라 임의로 놓은 자리다.

---

## 4. 학습 큐 상태 (일시정지)
- sampling_ablation 큐: A0 · A1 · A2 학습 완료, **A2 평가·A2r·A0′(A0_s2002) 미실행**. 10-29 11:25 사용자 작업지시 (pan_inference_diagnostic 우선) 로 `run_A2r_s2001.sh`·`eval_hook.sh` 실행 권한 제거, A2 가 004000 까지 끝난 뒤 13:58:41 QUEUE_STOPPED. 11-02 확인 시에도 정지 상태 (A).
- 재개 절차 (D, `pan_inference_diagnostic/01_training_pause_status.md` 4절): `chmod +x runs/run_A2r_s2001.sh eval_hook.sh; ./eval_hook.sh A2_s2001` (GPU 약 2 h) → 남은 A2r·A0_s2002 는 RUNS 를 바꾼 큐 사본으로. 자동 재개하지 않음.
- d4: 010000 에서 정지, 이어 학습 계획 없음 (A).
- 이 조사에서는 아무것도 재개·중단하지 않았다.

---

## 5. 진행 중·방금 끝난 실험 (11-02 기준)
| 실험 | 상태 | 근거 |
|---|---|---|
| 오프라인 Pan 반전 분석 (filter_off): q02 (223 상태 × noise 64), q02b, q03, q05, 문서 00–05 + analysis_handoff | 조사 도중 **완료** (q02 "done 223 2999s", 문서 16:29–16:37). 조사 시작 시점에는 q02 실행 중이었음 | `…/offline_pan_reversal_filter_off/` |
| R1/R2 연습 녹화 | 사용자 진행 중 (11-02 오후까지 r1_try3 0편) | `r1_r2_collection/02` §14 |
| R1 시나리오 수정 (팔 접은 자세·15/25/40°+ 지나침) | 05 문서 제안, 도구 반영 여부 미확인 | OFF/05 |

---

## 6. 아직 수행하지 않은 실험 (계획·설계만, D)
| 계획 | 내용 | 출처 |
|---|---|---|
| R1/R2 본 수집 | R1 16 + R2 32 (4차 정의) | r1_r2_collection/02 |
| R1 실패 상태 맞춤 시연 (방안 A 수정안) | 팔 접은 자세 + 15/25/40°+ 지나침 + 손목 테두리/안 보임 + front 보임 | OFF/05 |
| HIL (방안 B) 전환 장치 | 정책 정지 → queue 폐기 → 리더 동기화 → 단일 writer 전환, 가짜 팔 harness 검증 먼저 | OFF/05, handoff Q9 |
| R1 학습 전후 오프라인 검증 | T4 상태 실행 구간 목표 쪽 비율 (기준 U 7.7% · G 4.3%) | OFF/05 |
| R1/R2 혼합 재학습 | d2+R1 / d2+R2 / d2+R1+R2, 비율·step 미정 | 〃 §13 |
| 재학습 후 실물 평가 | **프로토콜 미정의** | — |
| Held-out H 녹화 + H 기반 O1-H/O2-H | 32편 | sampling_ablation/H |
| 로봇 평가 (sampling ablation) | 정책당 T1 16회 = KT 4 (K1·K3·K6·K8) + RT 4 + UF 4 (U3·0, U4·L30, U6·L30, U8·0) + UN 4 (U2·45, U1·45, U6·0, U7·0), RTC h20 EXP s5 q30, 필터 켬 | sampling_ablation/실험설계.md 6절 |
| 필터 A/B ABBA 16판 (K1·K3·K6·K7) | K1 4+4 만 실행됨, 나머지 미실행 | PD/12 |
| 대응 필터 비교 (각도 0 고정, 켬·끔 번갈아) | 제안 | PD/14 §6 |
| 안전 정지 S5/S4b 구현 + harness 검증 | 사용자 승인 필요 | PD/13 §6 |
| A2 평가, A2r, A0′, (A3, A3c12) | 큐 재개 시 | 01_training_pause_status |
| P0 정책 기준선 16–24판, P3 시작 pan 다양화 32편, P4 위치 밀도 32편 | 제안 | data_coverage_audit/08 |
| grasp_pose ablation S0–S3, 레퍼런스 위치 민감도 프로브, vision_probe R0–R4 (VLM 학습·full FT 포함) | 설계 | 각 문서 |
| d1 · d3 (T2 포함) | T2 미녹화 | d1/d3 description |
| VLM LoRA / full FT 비교 | peft 미설치; 메모리 기록 "VLM LoRA not first" (C) | checkpoint-offline-compare, action-bottleneck 메모리 |

---

## 7. 성공률·접근 정확도 측정 방법 (현재 정의된 것)

| 지표 | 정의 | 상태 |
|---|---|---|
| 최종 성공 (P/F) | eval_ui 에서 판 끝에 사람이 누름 (상자에 넣었나 / 멈춤 / 1분 넘게 헤맴). 성공률 = P / 저장 판 | 사용 중 (사람 판정) |
| 첫 파지 성공 (사람) | eval_ab_ui 판정 칸 (redbox A/B·공간 평가) | 정의 문서 없음, 메모와 어긋난 판 5개 |
| 판 메모 | `first= lift= drop= final= side=C|L|R|? depth=D|S|E|?` | 정의만, 실제 입력 0 |
| 첫 파지 (자동) | 첫 닫힘 c = 그리퍼 state 첫 닫힘; 그리퍼 바닥 = c 뒤 1 s 최소 (사람 쥠 11.5–13.6, 빈 닫힘 1–4); 들어 올림 = c 뒤 2 s 안 TCP z ≥ 4 cm & 그리퍼 ≥ 9; 놓침 = 들어 올린 뒤 그리퍼 ≤ 6; 손목 화면 좌우·앞뒤 분류 | PD/11 |
| need · pe (목표 pan) | 판 시작 front 사진 → homography → 탁자 XY → bearing → pe; need = pe − 시작 pan | PD/09 (K 근처 RMS 0.65 cm 검증, K 밖 미검증) |
| coord_status | valid_near_K (K 3 cm 안, 검증) / valid_off_K (미검증, 별도 그룹) / invalid_detection / invalid_calibration | PD/09 |
| 첫 1 s 이동 비율 | (chunk[idx29] − 시작 pan) / need; 닫힌 고리 (명령[t+30] − state[t]) / (pe − state[t]) | PD/10 |
| 첫 닫힘 Pan 오차 | (pe − pan) × need 부호; σ_coord · σ_grasp (2.15°) 따로 표시 | PD/10 |
| 목표대 · zone | 사람 파지 pan (p5–p95) ∪ 같은 자리 정책 성공 pan; under / aligned / over (먼 끝 + 8°) | OFF/01 |
| 손목 접근 정확도 | 닫힘 시작 손목 화면 큐브 v (사람 0.64–0.76), u (0.26–0.57); 닫기 영역 u 0.255–0.432, v 0.633–0.78, 넓이 ≥ 0.08 | PD/11·13, R12 |
| TCP 상대 높이 | 닫힘 시작 TCP z − 가장 가까운 사람 10편 중앙 (FK 절대 위치는 K1 에서 4–5 cm 어긋나 상대 차로만) | PD/11 |
| R1 복구 지표 | first_pan_move_dir, pan_reversal(_t_s), cube_reacquired_in_wrist(_t_s), recovery_completed, pan_error_at_grasp_deg | 정의만 |
| R2 지표 | approach_depth_category, first_close_result, close_zone, r2_wrist_start_in_region | 정의만 |
| O1 / O2 / O3 (sampling ablation) | O1 초기 접근 (pre_err, start_err, 합성 격자 새 위치, aK), O2 roll 조건부 (w_rot, G_tt, G_rr, S1·S6), O3 외움 감시 (칸별 loss) | 오프라인 |
- 실물 "접근 깊이"·접촉·쥐는 힘은 어떤 실험도 측정하지 않았다 (손목 v, 그리퍼 값, FK 상대 높이만).
