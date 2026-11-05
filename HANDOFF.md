# HANDOFF.md — SO-101 π₀.₅ 공간 일반화 연구 인계

**기준일:** 2026-11-05  
**범위:** R1/R2 수집, rft01 추가 학습, HIL 준비, 실물 평가 Trial 1–16  
**근거:** 초안은 사용자 제공 (대화에서 받은 Claude Code/실험 보고서 기준). 2026-11-05 Claude Code 가 로컬 원본 보고서·결과 CSV·설정과 대조해 수정함 — 수정 내역과 근거 파일은 [부록 A](#부록-a-로컬-원본-대조-수정-내역-2026-11-05). 수치는 파일에 기록된 관측·자동 분석 값이고, 추측과 계획은 따로 표시한다.  
**표기:** [실물 관측] 사람 P/F 또는 실행 기록 · [자동 후보] 규칙 계산 (사람 판정 아님) · [오프라인] 재추론 · [가짜 장치] FakeBus/FakeCam 시험 · [해석] · [후속 권고] · [결정 대기].  
**GitHub:** `ahnjaeyeong/so101-pi05-spatial-generalization` (연구 기록 저장소, Public). 원본 데이터·영상·체크포인트는 Git 제외 (경로·SHA-256 만 기록).

## 1. 핵심 결론

- [실물 관측] **FT (rft01 1000-step) 4/8, BL (d2 020000) 5/8** (eval_ui 사람 P/F). 16회만으로 어느 쪽이 우수하다고 말할 수 없다.
- Known (Trial 1–8): FT **3/4**, BL **2/4**. K3 의 0° 와 R30° 는 FT 두 번 성공, BL 두 번 실패했지만 조건당 1회다.
- Unknown (Trial 9–16): FT **1/4**, BL **3/4**. **불공정한 비교:** FT 9–12 는 모두 그리퍼가 닫힌 채 시작 (0.5–2.3), BL 13–16 은 열린 채 시작 (24.5–24.8). 모델 실행 순서도 FT 일괄 후 BL 일괄이었다. 이 차이를 모델 효과로 해석하면 안 된다.
- [오프라인] R1 Pan 복구 방향의 행동은 개선되었지만, R2 의 실제 실패 상태 (AHEAD) 에서 잘못된 위치 닫힘은 개선되지 않았다. 실물 결과는 이 오프라인 평가와 별개이며, 16회 모두 Wrist 시야 이탈이 없었으므로 **실물 R1 복구 능력은 검증되지 않았다**.
- [결정 대기] 그리퍼 시작 상태 리셋을 고치고, 조건 및 모델 순서를 통제해 반복 평가하는 것이 다음 단계. 승인 없이 실물 추가 평가·HIL 수집·GPU 학습을 시작하지 않는다.

## 2. 프로젝트 기준 조건

- SO-101 leader/follower, Front/Wrist 카메라 (640×480, 30 fps), LeRobot 0.6.2, π₀.₅ Expert-only.
- 기존 d2 **256편**; 기준 checkpoint `~/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model`.
- 과제 문장 (d2 · R1 · RC dataset `meta/tasks.parquet` 과 평가 명령에서 확인): **`pick up the red cube and put it in the brown box`**.
- 실물 표준 추론 (평가 `command.txt` · CHECK_OK 출력 확인): RTC guided, prefix schedule EXP, execution horizon 20, max guidance 10, denoise (num_inference_steps) 5, queue threshold 30, chunk 50, 8° per-tick clamp (`max_relative_target=8`), Arm Filter **OFF**, 자동 복귀 끔. 동일 카메라·보정 유지.
- 목적: 새로운 위치에서 첫 파지 공간 일반화, R1 Pan 방향 지나침 후 복구, R2 접근·조기 닫힘/빈 파지 개선.

## 3. 교정 시연 16편과 QA

- [사용자 QA 판정] 학습 유효 총 **16편**: R1 4편 + R2 회복 시연 (RC) 12편. 데이터셋 v3.0, fps 30, features · robot_type · task · 프레임 연속성 · 영상 길이 d2 호환 확인 (각 세션 `qa/r12_qa_report.md` §1).
- R1: `main_k8/r12_pilot12_r1` (R1-FOLD-OVER, 8편 저장) 중 **ep4–7 만 유효**. ep0–3 제외 사유 (`r12_plan.csv`): "지나침을 녹화 안에서 함 (쉬는 자세 시작) — 사용자 결정 재촬영 11-04".
- R2: `main_k8/r12_pilot12_rc` (RC-F1 4 · RC-F2 5 · RC-F3-L 2 · RC-F3-R 2, 13편 저장) 중 **ep0–10, ep12 (12편)**. ep11 (RC-F2) 은 QA 제외 표시 (끝 프레임이 쉬는 자세 아님, 결과 미입력, camera stall). 출처: EXP-13 `manifest/training_manifest.csv`.
- `main_k8/r12_pilot12_r2p` (R2-P 6편) 은 학습 manifest 에서 세션 전체 제외. ep0/ep1 은 '첫 빈 파지 후 재파지' 로 R2-P 정상 학습 후보에서 제외 (11-04 세션 판정; 이 사유가 적힌 파일 위치는 확인하지 못함). 원본은 삭제하지 않는다.
- 일부 QA 경고는 시나리오와 맞지 않는 초기 Wrist 영역, 계획 큐브 각도 차이, 닫힘 깊이, 카메라 프레임 반복, 결과 입력 누락 등으로 발생. QA 의 `문제 없음 0/12` (RC) · `0/4` (R1) 을 데이터가 전부 불량하다는 뜻으로 해석하지 않는다.
- RC ep4/ep8/ep12 는 그리퍼를 열기 전 팔이 먼저 움직였으나 (`arm_before_gripper_open` 7.8° · 17° · 6.1°), 사용자 QA 에서 학습 사용 승인. 시작 망설임 구간은 자르지 않음 (사용자 결정).
- QA 원본 경로: `~/so101_runs/main_k8/r12_pilot12_rc/qa/r12_qa_report.md`, `~/so101_runs/main_k8/r12_pilot12_r1/qa/r12_qa_report.md`. 저장소 사본: `experiments/11_r1_r2_recovery/sources/sessions/`.
- 이 데이터는 사람이 실패 상태를 준비하고 **올바른 교정 구간부터** 녹화한 시연이며, 실제 정책 도중 개입하는 HIL 과 다르다.

## 4. rft01 추가 학습 및 오프라인 결과

- [실행 기록] run `rft01_d2rc16_W5_1k_s2001`, 2026-11-04 15:05–18:00, exit 0, 1,000/1,000 steps, NaN 없음, 최대 GPU 21.0 GB, loss **0.024 → 0.022**.
- d2 020000 에서 신규 Expert-only Fine-tuning (resume 아님). bs 32, LR peak 1e-5 → 2.5e-6, warmup 50, seed 2001. 데이터: d2 256 + R1 4 + R2 12 = 272편 / 129,470 frames. 실제 샘플 비중 d2 **79.9%**, R1 **5.9%**, R2 **14.2%** (교정 frame 가중 W=5). 교정 프레임 31% 는 한 번도 샘플되지 않음.
- 250/500/750/1000 checkpoint 정규화 통계는 d2 와 동일. `model.safetensors` SHA-256 (`recovery_ft/logs/post/p01_ckpt_sha256.json`):
  - 250 `181b82db06a69f06e988ebd9178d07f2e712a4febc04b99e78ceb072715553d9`
  - 500 `c0e3c88b135eb43354909eea3d0b30415d16106e108c0ad55744c62614c0cbbd`
  - 750 `a2dcc02320c6de1f2173bde945ea1f7c03bb84355c78bb6e331ea786ba66b3ae`
  - 1000 `620c45988a35b77e76b5c0869c560697d9d095143aceee33b98946a7db712af9`
  - (기준 d2 020000 `6c46dee79b167c48ad24b6af739157dc22636505c4c838815a4bf3656a364886`)
- 로컬 학습 보고서 `~/so101_runs/main_k8/d2/recovery_ft/README.md`; 저장소 `experiments/13_recovery_ft/` (EXP-13).
- 저장소 EXP-13 커밋 `4b00f00`, 브랜치 `exp/13-recovery-ft-20261104` — 11-04 에는 미push, **11-05 원격에 push** (§8).

### 오프라인 재추론 지표 (실물 성공률이 아님)

32 seed 실험의 T4 baseline 은 Raw 5.7%, RTC 4.1%. 과거 64-seed 기준 Raw 7.7% / RTC 4.3% 와 조건이 달라 그대로 비교하지 않는다.

| 지표 | 020000 | FT 500 | FT 1000 |
|---|---:|---:|---:|
| R1 wrist-lost, RTC 실행 구간 목표 방향 | 4.1% | 27.3% | **33.5%** |
| R1 RTC cum30 목표 반대 방향 | 86.9% | 51.1% | **43.8%** |
| R1 Raw 실행 구간 목표 방향 | 5.7% | 12.4% | 14.4% |
| R2 미학습 실물 AHEAD 상태 잘못된 위치 닫힘 (p_close30) | 0.536 | 0.527 | 0.536 |
| R2 학습 RC-F1 시작 상태 조기 닫힘 [in-sample] | 0.86 | 0.11 | 0.14 |
| 정상 grasp T2 닫힘 | 0.931 | 0.819 | 0.900 |
| 정상 근접 정렬 T2 불필요 반전 | 14.4% | 17.9% | 20.2% |

- [해석] R1 은 과거 실제 실패 A0/B1 에서 기록된 상태에 복구 방향 신호 개선. 하지만 독립 실물 에피소드는 단 2개, seed 는 독립 시행이 아니다.
- [해석] R2 는 학습 시연 시작 상태에서만 조기 닫힘 감소, 기존 실패 AHEAD 상태에서는 개선 없음. 사람이 준비한 R2 시작 상태와 실제 실패 상태 사이의 분포 차이는 **가설**, 확정 원인이 아님.
- 정상 동작 관련 우려: 근접 상태 Pan 반전 증가 (+5.8 %p), 사람 action 과의 차이 약 0.2° 증가, 닫기 직전 측면 Pan 보정 gain 0.35 → 0.04 (6 상태 기준). 통합 run 1회로 R1/R2 개별 기여 구분 불가.

## 5. 실물 평가 Trial 1–16 (2026-11-05)

FT = rft01 checkpoint 001000, BL = d2 020000. P/F 는 eval_ui 사람 판정, 나머지 관측은 [자동 후보]. 시험당 최대 60초. 세부는 원본 로그로 확인한다.

| # | 모델 | 조건 | 결과 | 시작 그리퍼 | 관측 |
|---:|---|---|---|---:|---|
| 1 | FT | K3 0° | **P**, 18.0s | 0.0 | 9.9s 첫 파지, 빈 닫힘 0, 초기 Pan 지나침 **15.1°** |
| 2 | BL | K3 0° | **F**, 58.8s | 0.55 | 빈 닫힘 4, 파지 못함, Pan 8.1° 지나침; 팔 뻗은 채 종료 (시작과 최대 167°) |
| 3 | BL | K1 0° | **P**, 26.5s | 0.0–2.6 | 첫 파지 16.5s, 빈 닫힘 0, Pan 3.5° 지나침 |
| 4 | FT | K1 0° | **P**, 26.7s | 0.0–2.6 | 첫 파지 13.4s, 빈 닫힘 0, Pan 6.9° 지나침 |
| 5 | FT | K3 R30° | **P**, 21.4s | 0.0–2.6 | 첫 파지 11.5s, 빈 닫힘 0, Pan 8.4° 지나침 |
| 6 | BL | K3 R30° | **F**, 58.9s | 0.0–2.6 | 빈 닫힘 8 (+판정불가 3), 끝내 파지 못함, Pan 3.6° 지나침 |
| 7 | BL | K1 L30° | **P**, 30.5s | **30.6** | **그리퍼 열린 시작**, 첫 0.5s 닫힘을 단순 빈 파지로 세지 말 것; 큐브 각도 측정 실패 (K1 0.9 cm) |
| 8 | FT | K1 L30° | **F**, 58.8s | 0.6 | 9.2s 빈 닫힘 1회, 이후 추가 닫힘 없음 |
| 9 | FT | U2 L30° | **F**, 59.3s | 1.1 | 21.6s 파지했으나 최종 실패 (원인 기록 없음), 이후 닫힘 5 |
| 10 | FT | U7 45° | **P**, 17.1s | 2.3 | 첫 파지 9.1s |
| 11 | FT | U8 0° | **F**, 59.3s | 0.5 | 닫힘 9회, 파지 실패 |
| 12 | FT | U1 R30° | **F**, 59.3s | 1.1 | 닫힘 7회, 파지 실패; 그리퍼 열린 채 종료 (24.8) |
| 13 | BL | U2 L30° | **F**, 58.8s | **24.8** | 50.1s 에야 파지, 최종 실패 |
| 14 | BL | U7 45° | **P**, 15.2s | **24.5** | |
| 15 | BL | U8 0° | **P**, 22.5s | **24.5** | 두 번째 닫힘 (11.7s) 에서 파지 |
| 16 | BL | U1 R30° | **P**, 28.6s | **24.5** | |

(시행 3–6 의 시작 그리퍼는 요약 보고서에 범위로만 기록됨.)

| 구간 | FT | BL |
|---|---:|---:|
| Known K, 1–8 | **3/4** | **2/4** |
| Unknown U, 9–16 | **1/4** | **3/4** |
| 전체 1–16 | **4/8** | **5/8** |

### 평가 해석·교란

1. Known K3 에서는 FT 2/2, BL 0/2 이나 조건당 1회. K1 L30 은 Trial 7/8 사이 그리퍼 시작 상태가 일치하지 않음 (BL 30.6 열림, FT 0.6 닫힘).
2. Unknown U 에서 FT 는 **닫힌 그리퍼 (0.5–2.3)**, BL 은 **열린 그리퍼 (24.5–24.8)** 로 시작. 모델과 시작 상태가 완전히 결합된 교란이므로 **FT 의 Unknown 일반화가 나쁘다고 결론 불가**.
3. 판 사이 복귀 (E5) 는 그리퍼를 세션 시작 값으로 돌리고, 세션 종료 시에는 팔만 반환해 세션 사이 그리퍼 시작 상태가 달라짐. Trial 12 FT 가 열린 상태 (24.8) 로 끝난 뒤 BL 세션이 열린 상태로 시작함 (실행 도구 설계 결함, `pilot_summary_t08_t16.md` §2). Trial 7 도 같은 이유 (Trial 6 이 연 채 끝남, 당시 E5 는 그리퍼를 쓰지 않음).
4. 모델을 판마다 교대하지 않음: 6–7 BL 연속, 8–12 FT 연속, 13–16 BL 연속. 장소·시간·잔여 상태 영향 통제가 부족.
5. U2 및 U8 은 K 표시와 경계에 가까움 (계획상 K3 · K4 에서 3.5 cm). 시작 사진은 Trial 9 (U2) 를 K3 에서 3.0 cm, Trial 15 (U8) 를 K4 에서 2.6 cm 로 Known 판정. 기존 분류와 실제 좌표·레이아웃을 함께 보존하고, 사후 임의 재분류하지 않음. 이 U 는 파일럿 계획 자리이며 Held-out H 의 U1–U8 과 다르다.
6. Trial 1 FT K3 0° 는 Pan −7.6 → 47.3°, 추정 목표 32.1° 보다 15.1° 지나친 뒤 복귀. BL Trial 2 도 8.1° 지나쳤음. **초기 FT Pan 이동이 더 클 가능성**과 복구 가능성은 구분해서 분석.
7. 16회 모두 r2_safety 정지·경고 0, fault_latch 발동 0, 판 중 Ctrl+C·손 개입 기록 없음. Trial 8 첫 세션은 모델 로딩 중 Ctrl+C 로 중단 (저장 판 없음) 후 다시 실행. **정지 기능의 실물 성능이 검증됐다는 뜻이 아님**.
8. Wrist 시야: Trial 1–16 모두 놓친 구간 0 (`pilot_summary_t08_t16.md` "놓친 구간 0 (모든 판)"). 시야 이탈 후 실물 R1 복구 성능은 아직 미확인.
9. FT 검증기 `checkpoint 020000 ✗` (p00b F4) 는 검증 스크립트가 d2 경로를 고정한 알려진 거짓 FAIL. FT checkpoint SHA 는 별도 manifest 로 확인.
10. Trial 5 실행 중 13:27–13:29 에 가짜 장치 시험 (GPU) 이 같이 돌았고 (inference_delay p50 13 vs 12), 실행 중 스크립트 수정으로 `run_trial.sh` 가 eval_ui 종료 직후 중단됨 (판은 정상 저장).

로컬 보고서: `~/so101_runs/main_k8/rft01_real_pilot/reports/pilot_summary_t01_t07.md`, `~/so101_runs/main_k8/rft01_real_pilot/reports/pilot_summary_t08_t16.md`. Trial 1 예시: `~/so101_runs/main_k8/rft01_real_pilot/eval/rollouts/20261105_111427_1k_t01_ft_k3_0`. 저장소: `experiments/14_rft01_real_pilot/` (EXP-14).

## 6. HIL 준비 상태 (실물 수집 미실행)

- 공식 LeRobot 0.6.2 (git e595b790) `lerobot-rollout --strategy.type=dagger` 가 로컬 설치본에 있으며 SO-101 leader + π₀.₅ RTC 조합으로 사용 가능. LeRobot 자체 업데이트 불필요.
- 경로 `~/so101_runs/main_k8/hil_dagger/`; adapter `tools/hil_dagger_entry.py`, `tools/run_hil.sh`, `tools/hil_qa.py`; 보고서 `docs/01_v2_보고서.md` (v2 안전 변경), `docs/02_ui_보고서.md` (수집자 화면). 로컬 git: main ac81fe3 (v2), hil-ui 716624b (UI). 저장소: `experiments/12_hil/` (EXP-12).
- HIL 은 정책이 실제 실패 상태에 접근하면 사람이 개입하여 리더로 교정하는 방식. 정책 실행 Action 과 전문가 교정 Action 을 `intervention` 열로 분리하며, 교정 후 상자 넣기까지 녹화하도록 결정.
- [가짜 장치] v2 **17 시나리오 / 179 검사 PASS**, UI 추가 후 **19 시나리오 / 205 검사 PASS** (화면 상태 31/31, 화면 e2e 62/62). 추론 오류 후 정책 명령 0개 (6/6 실행; 공식은 1.0 s 동안 30개), 큐 폐기, 단일 writer 확인. 실물 HIL 수집을 실행했다고 주장하지 말 것.
- Arm Filter OFF, 교정 구간 8°/tick 제한, 종료 후 자동 복귀 비활성화 (home/release/hold 선택, 기본 hold). **원시 리더 Action 은 제한 전 값으로 저장되며 실행 목표는 제한 후 값**: 빠른 가짜 동작 (S11) 에서 최대 29.6° 차이 (49프레임 중 28). 향후 BC 라벨 일관성 검토가 필요.
- 실물 미검증 위험: 리더 자동 정렬 2초간 끼임, 토크 OFF 낙하, 토크 ON 시 이전 목표로 이동, hold 후 재연결 때 낙하 (`configure()` 가 토크를 끔), 전원 차단 시 팔 낙하.
- HIL 수집·학습은 **미실행**. 기존 R1/R2 와 HIL 비교 실험은 제안에 불과함.

## 7. 평가 코드·안전 및 다음 작업

- 기존 평가 경로의 추론 오류 후 RTC 잔여 Action 실행을 막기 위해 `fault_latch` 를 별도 구현. [가짜 장치] 오류 이후 명령 0 · queue 30→0 · 약 0.03초 처리, unit 25/25 PASS (v1) → 31/31 (v2, 게이트 추가). 실제 평가에서는 해당 정지가 발생한 적 없어 실물 fault 시 동작 미검증.
- 과거 Pan −109° 이탈 사례가 있었으므로 소프트웨어 정지와 물리적 안전을 구분해야 함. 시험 후 토크, return/hold, 전원 차단 시 낙하 위험 확인 필요.
- [후속 권고] 리셋이 그리퍼까지 초기 상태 (절대 목표) 로 정렬하도록 판 사이 · 세션 끝 복귀 모두 수정하되, **닫힘 약 0.6 은 제안값이며 기존 정상 초기 조건·보정·안전 검증 후 확정**. 기존 원본 실험 파일은 수정하지 않는다.
- [후속 권고] FT/BL 번갈아 배치, 동일 K/U 위치·각도·시작 관절값·그리퍼·카메라·RTC·필터 유지. 반복 평가 시 K3 차이 재현 여부와 Unknown 효과를 구분.
- [후속 권고] U2/U8 의 Unknown 정의를 실제 기준과 대조. 단순히 임의 새 위치로 바꾸면 기존 시험과 다른 실험이 되므로 따로 기록.
- [후속 권고] 실물 R1 복구는 Wrist 시야 이탈이 실제로 생기는 조건에서 따로 평가해야 함 (이번 16판에 없음).
- HIL 을 실행한다면 제어권 전환에 관한 실물 안전 검증 (`docs/01_v2_보고서.md` §6 사전 확인 a–c) 과 사용자 별도 승인이 선행돼야 함.

## 8. Git/인계 작업 (2026-11-05 실행 결과)

- 원격 브랜치 구조 (모두 PR 로 main 에 합칠 예정, merge 는 사용자 확인 후):
  1. `data/source-completeness-20261102` — PR #1 (11-02, 열림, 미merge). 원본 완전성 점검.
  2. `exp/13-recovery-ft-20261104` — 커밋 `4b00f00` (EXP-13) 를 그대로 push. PR #1 위에 쌓임.
  3. `records/handoff-20261105` — EXP-13 위에 쌓임. 이 문서 · EXP-11/12/13 갱신 · EXP-14 신규 · 색인 · 도구 변경.
- 저장소 규칙: `CLAUDE.md`. 검사: `python3 tools/check_repo.py`, `git diff --check`. Push 는 `CLAUDE.md` 9 의 ahnjaeyeong 계정 방식 (gh 활성 계정 변경 없음). `git push --force` 금지.
- 11-05 추가 도구: `tools/sync_sources.py --only <prefix>` · `tools/derive_condensed.py --only <prefix>` (선택 매핑만 복사·변환, 나머지 manifest 행 유지), `tools/archive_excluded.py` (실험별 Git 제외 목록 + SHA-256).
- 아직 로컬에만 있는 것 (Git 에 없음, 11-05 확인):
  - `main_k8/d2/visual_dependency` (11-03 VD 실험, 861 파일) — 저장소 매핑 없음, 실험 문서 없음.
  - `main_k8/r2_grasp_diagnostic` (11-02 ~ 11-03 R2 진단, 51,867 파일 / 599 MB) — '작업 중 폴더' 로 계속 제외 중.
  - Desktop `SO101_R2P_가이드_*.png` 3개 — 매핑 없음.
  - 기존부터 `.gitignore` 의 `checkpoints/` · `diag/` 규칙 때문에 로컬 저장소 작업 트리에만 있는 사본: `configs/checkpoints/` (체크포인트 해시 표), `experiments/06_d2_256/sources/d2/eval/rollouts/20261029_*/diag/` (10-29 계측 기록 4 run). README 는 이들을 링크하지만 GitHub 에는 없다.
  - `ARCHIVE_MANIFEST.csv` · `inventory/` 는 11-02 상태. 11-05 전체 재생성 결과가 12 MB · 9.4 MB 로 저장소 크기 제한 (7 MB) 을 넘어 커밋하지 않음 → 새 실험은 `experiments/*/sources/ARCHIVE_EXCLUDED.csv` 사용.
- GPU 학습, 실제 로봇 구동, HIL 실물 시험, 추가 평가 자동 실행 금지 (사용자 승인 필요).

## 9. 다음 세션 시작 시 우선 확인

1. `git -C ~/so101-pi05-spatial-generalization fetch && git branch -a` — 위 세 브랜치 · PR 상태 (merge 여부) 확인.
2. `pgrep -af '[e]val_ui|[l]erobot'` — 실행 중 평가가 없을 때만 스크립트 수정.
3. 그리퍼 리셋 수정 전 `rft01_real_pilot/scripts/run_series.sh` 의 E5 · teardown 경로와 `safe_home.py` 확인.
4. 다음 실험 설계 시 EXP-14 §교란 6 항목을 모두 통제했는지 대조.

**분석 결론:** 이번 16회는 교정 FT 의 K3 개선 가능성을 보여주지만, Unknown 조건에서 그리퍼 시작 상태가 모델과 겹쳐 비교가 무효화됐다. 따라서 **모델 간 우열은 미결정**이다.

---

## 부록 A. 로컬 원본 대조 수정 내역 (2026-11-05)

| # | 초안 | 수정 | 근거 |
|---|---|---|---|
| 1 | 과제 문장 "`pick up the red cube` 라고 언급, 정확한 문자열은 메타데이터 확인" | `pick up the red cube and put it in the brown box` | d2 · r12_pilot12_rc · r12_pilot12_r1 `dataset/meta/tasks.parquet`; 평가 `command.txt` |
| 2 | R2 12편 "정확한 episode ID 는 manifest 확인" | RC ep0–10, ep12 (ep11 QA 제외) | `d2/recovery_ft/manifest/training_manifest.csv`, RC `qa/r12_qa_report.md` |
| 3 | 750 SHA 축약 `a2dcc023…6ba66b3ae` | 전체 해시 `a2dcc023…786ba66b3ae` (끝 8자리 `ba66b3ae`) · 4개 모두 전체 해시로 기재 | `recovery_ft/logs/post/p01_ckpt_sha256.json` |
| 4 | Trial 1 추정 목표 32.2° | 32.1° (47.3 − 15.1 = 32.2 는 반올림 차이) | `pilot_summary_t01_t07.md` §3 |
| 5 | "Trial 8–16 은 보고에 별도 기술 없음" (Wrist) | Trial 8–16 도 놓친 구간 0 | `pilot_summary_t08_t16.md` "Wrist: 놓친 구간 0 (모든 판)" |
| 6 | Trial 9 "상자 넣기 실패" | "최종 실패 (원인 기록 없음)" — 실패 이유는 파일에 없음 | `pilot_summary_t08_t16.md` 표, `results/trials.csv` (상세 판정은 시행 1 만) |
| 7 | HIL "17시나리오/179검사" 만 | v2 17/179 + UI 추가 후 19/205 (상태 31/31, e2e 62/62) | `hil_dagger/docs/01_v2_보고서.md` §4, `docs/02_ui_보고서.md` |
| 8 | fault_latch unit 25/25 만 | v1 25/25, v2 31/31 | `rft01_real_pilot/logs/tests/run_20261105_094837`, `run_20261105_103355` `test_units.log` |
| 9 | (없음) | 교란 추가: 6–7 BL 연속 (Known 구간도 미교대), Trial 5 중 GPU 가짜 시험 동시 실행 · 스크립트 수정으로 run_trial 중단, Trial 8 첫 세션 로딩 중 Ctrl+C, Trial 7 그리퍼 원인 | `pilot_summary_t01_t07.md` §4, `pilot_summary_t08_t16.md` §2 |
| 10 | (없음) | 시작 그리퍼 열 추가 (1–2, 7–16 은 값, 3–6 은 범위) | `results/trials.csv`, 두 요약 보고서 |
| 11 | r2p ep0/ep1 재파지 제외 | 유지하되 "사유가 적힌 파일 위치 미확인" 표시 | `r12_pilot12_r2p/` 의 notes · sheet · QA 에서 해당 문구를 찾지 못함 |
| 12 | §8 Git 작업 "해야 할 일" | 실행 결과 (브랜치 · 로컬 전용 항목) 로 갱신 | 2026-11-05 `git branch -a`, `tools/compare_sources.py` 실행 결과 |

그 밖의 수치 (Trial 1–16 P/F · 길이 · 닫힘 · Pan 지나침, 구간 합계, 오프라인 표, rft01 실행 기록, HIL 위험 목록) 는 위 원본과 일치함을 확인했다.
