# EXP-12 · HIL (정책 실행 중 인간 교정) 검토 및 향후 실물 평가

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-12** (보고서 ID S7-03) |
| 날짜 | 정의 2026-11-02 16:32 · 구현 2026-11-04 · 기록 갱신 2026-11-05 |
| 상태 | `IN_PROGRESS` — 수집 도구 구현 · **가짜 장치 검증만** 완료. **실물 안전 검증 0 · 실물 HIL 수집 0 편 · HIL 데이터 학습 0** |
| 상태 이력 | 11-02 `PLANNED` (설계·검토, 구현 없음) → 11-05 `IN_PROGRESS` (11-04 구현 · 가짜 장치 시험 반영. CLAUDE.md 의 "HIL 은 구현·검증 전까지 PLANNED" 에서 검증 = 실물 검증으로 보면 아직 미충족 — 그래서 COMPLETED 가 아님) |

## 2026-11-04 구현 — `main_k8/hil_dagger` (11-05 반영)

표기: [코드] 로컬 코드 확인 · [가짜 장치] FakeBus · FakeCam · stub 정책 시험 (CPU, 장치 경로 `/nonexistent/...`, 연결 함수 차단) · [미검증] 실물에서 확인 안 됨.

- [코드] 설치된 LeRobot 0.6.2 (git e595b790) 에 공식 `lerobot-rollout --strategy.type=dagger` (AUTONOMOUS ⇄ PAUSED ⇄ CORRECTING, 교정 구간만 녹화, `intervention` 열) 가 이미 있음 → LeRobot 갱신 불필요. 차이 기록 `docs/03_local_vs_main.diff` (upstream main ba83e4cf 와 비교; 복사해 둔 upstream 소스 `docs/upstream_main_ba83e4cf/` 는 이 저장소에 넣지 않음).
- [코드] 런타임 adapter `tools/hil_dagger_entry.py` (LeRobot · d2 파일 수정 없음): A1 filter 경로 · A2 `hil_events.jsonl` · A3 표시 키 · A4 정지 전 3 s 기록 · A5 Space debounce · A6 터미널 키 · A7 리더 토크 켜기 전 Goal := 현재 위치 · A8 교정 clamp 8° · A9 PAUSED 로 시작 + 리더 정렬 · A10 추론 오류 래치 · A11 자동 복귀 없는 종료 선택 (home / release / hold, 기본 hold) · A12 화면용 읽기 전용 tap.
- 실행 `tools/run_hil.sh` (사용자 실행 전용, GPU 작업이 돌면 거부, `DRY=1` 은 명령만 출력), 세션 QA `tools/hil_qa.py`, 수집자 화면 `tools/hil_viewer.py` (보기 전용 별도 프로세스, 키는 터미널).
- 사용자 결정 (v2): 교정은 상자에 넣을 때까지 녹화 · Arm Filter OFF (`--rollout_guard=warn` 은 기록만) · 교정 clamp 8° 유지 · 종료 뒤 자동 복귀 없음.
- 정책 실행 action 과 사람 교정 action 은 `intervention` 열로 구분. QA 학습 제외: reset 구간 · 교정 중 종료 · 최종 실패 · 최종 미입력 · 15 frame 미만.

### 가짜 장치 시험 결과
| 시험 | 결과 |
|---|---|
| `tests/run_all.sh` v2 (`docs/01_v2_보고서.md`) | **17 시나리오 179/179** (공식 그대로 8 시나리오 56 · adapter 9 시나리오 123) |
| `tests/run_all.sh` UI 추가 후 (`docs/02_ui_보고서.md`, 로컬 git 브랜치 `hil-ui` 716624b) | **19 시나리오 205/205** · 화면 상태 단위 31/31 · 화면 e2e 62/62 |
| 추론 오류 뒤 정책 명령 (S12, 5회 반복 포함) | 공식 0.6.2: 30 개 / 1.0 s 계속 실행 · adapter A10: **0 개 (6/6)**, 큐 30 → 0, 래치 → 정지 처리 27.6–32.6 ms, 오류 뒤 1 s 팔 이동 8.67° → 0.29° |
| ESC · 리더 오류 · follower 오류 · 정상 종료 뒤 자동 복귀 | 복귀 쓰기 0 (공식은 3 s · 150 쓰기) |
| Policy / Human 단일 writer | C1–C4, C6 PASS |
| QA 매핑 · 공식 변환 | 6/6 · 성공 3, 예상 실패 1 (`intervention` 열이 한쪽에만 있는 병합) |

- [가짜 장치] **저장 action ≠ 실행 목표**: 저장되는 교정 action 은 clamp **전** 리더 값, 실제 보낸 Goal 은 present ±8°. 빠른 손 시나리오 S11 (20°/틱) 에서 저장 action − 보낸 Goal 최대 29.6°, 49 frame 중 28 frame 에서 0.5° 넘게 차이. 느린 시나리오에서는 차이 0. d2 · R1 · RC 녹화는 clamp 없이 녹화되어 action = 보낸 명령이었음 → BC 라벨 일관성 검토 필요.

### 실물 미검증 위험 [미검증] (`docs/01_v2_보고서.md` §5)
리더 2 s 자동 정렬 중 손 끼임 · 토크 off 순간 리더 낙하 · 토크 on 순간 예전 Goal 로 이동 (A7 로 대응, 실물 미확인) · hold 종료 뒤 다음 연결의 `configure()` 가 토크를 꺼 팔이 떨어질 수 있음 · 장시간 hold 발열 · follower 통신 오류 뒤 토크 상태 · 소프트웨어 정지 ≠ 안전 정지 (전원 차단 수단 필요).

### 실물 시험 전 조건 (보고서 §6, 모두 미실행)
사용자 직접: (a) 리더만 연결해 토크 on/off Goal · 낙하 확인, (b) 2 s 정렬 중 손으로 막았을 때 힘, (c) hold 종료 뒤 다음 연결 낙하 (손으로 받친 채). 그 뒤 첫 파일럿 범위 (예: K1 1–2 시행) 사용자 결정 · 별도 승인.

### 사본
[`sources/hil_dagger/`](sources/hil_dagger/) — README, docs (00 · 01 v2 · 02 UI 보고서, diff, 논문 메모, UI 스크린샷), tools, tests (시험 코드 + `tests/_out/` 의 FACTS.md · 시나리오 console log). 가짜 장치 출력 폴더 (`tests/_out*/` 하위), `backup/`, upstream 소스 사본은 Git 제외 — [`sources/ARCHIVE_EXCLUDED.csv`](sources/ARCHIVE_EXCLUDED.csv). 원본 `/home/user/so101_runs/main_k8/hil_dagger` (로컬 git: main ac81fe3 = v2, hil-ui 716624b = UI; 사본은 hil-ui 작업 트리).

---

## 11-02 기록 (이력)

## 목적·정의
- 목적 [계획]: 정책이 실제로 빠지는 실패 상태에서 사람 교정 시연을 얻어 복구 행동을 학습시키는 방안 검토.
- `…/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md` 의 **방안 B "정책 실행 중 인간 교정 (HIL)"**: 정책 정지 → RTC/Action Queue 폐기 → 리더 팔을 팔로워 자세에 동기화 → 단일 writer 로 제어권 전환 → 사람 교정 녹화.
- 이 문서 이전 파일에는 HIL·DAgger·intervention 용어가 없다. 이전 설계 문장: `vision_probe/실험설계.md:173-176` "정책 실패 직후 이어서 사람이 교정하는 판도 포함한다" (설계만).

## 방안 A (EXP-11 수동 복구 시연) 와 비교 [가설·계획]
| 항목 | 방안 A (수동 복구 상태) | 방안 B (HIL) |
|---|---|---|
| 시작 상태 | 준비 단계에서 사람이 만든 상태 | 정책이 실제로 만든 상태 |
| 실패 상태 일치 | 조건을 맞춰야 함 | 그대로 일치 |
| 장치 | 현재 도구로 가능 | 새 구현 + 가짜 팔 harness 안전 검증 필요 |
| 안전 | 천천히 만든 자세 | 전환 순간 리더–팔로워 차이로 급한 움직임 위험 |
| 수집 효율 | 판당 1번 확실 | 해당 실패 빈도 2/20 |
| 데이터 | action = 리더 | 정책 구간·사람 구간 혼재 |
- [계획] 결론: **1차 방안 A (실패 상태 맞춤), HIL 은 2차**. 정책과 teleop 이 동시에 팔로워에 명령하는 구성은 만들지 않음.

## 검증 가설
- [가설] 실패 상태 그대로에서 얻은 교정 시연이 수동으로 만든 상태의 시연보다 분포가 정확하다 (OFF/05). 미검증.

## 데이터셋·모델·학습·평가
(11-05) HIL 데이터셋 0 · 학습 0 · 평가 0. 학습 계획 (H1-W5 / concat / IWR50 / match, PH1-W5 = rft01 레시피) 은 [계획] 만.
(11-02 기록) 없음 (`PLANNED`). 전환 트리거 후보: 안전 정지 조건 S4b (본 뒤 손목 놓침 + 회전), S5 (목표를 30° 넘게 지남) — 오프라인 20판에서 이탈 2판을 4–8 s 일찍 잡음, 구현 안 함.

## 향후 실물 평가 계획 (전체, 모두 `PLANNED`)
- Held-out H 32편 녹화 (지정 위치 U1–U8 × 각도 4, 학습 금지) — [`configs/layouts/redbox8_heldout_h.yaml`](../../configs/layouts/redbox8_heldout_h.yaml) (U `confirmed: false`).
- sampling ablation 정책당 T1 16회 (KT 4 · RT 4 · UF 4 · UN 4), 필터 켬.
- 필터 A/B 남은 12판, 각도 고정 대응 비교.
- R1/R2 재학습 후 평가 (프로토콜 미정).
- 측정 지표 정의: [`evaluations/README.md`](../../evaluations/README.md).

## 한계 및 미확인
- (11-05) 가짜 장치에는 중력 · 손 · 서보 전류 제한이 없어 위 시험은 실물 안전을 입증하지 못한다. 실물 HIL 수집 · 실물 안전 검증을 했다고 쓰지 않는다.
- (11-05) 기존 R1/R2 (EXP-11) 와 HIL 의 비교 실험은 제안만 있음.
- (11-02 기록) 연구자가 말하는 "HIL" 과 OFF/05 정의가 같은 의미인지 확인 필요.

## 원본 자료
(11-05) [`sources/hil_dagger/`](sources/hil_dagger/), [`sources/ARCHIVE_EXCLUDED.csv`](sources/ARCHIVE_EXCLUDED.csv). (11-02) [`../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md`](../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/05_r1_collection_recommendation.md), [`analysis_handoff.md`](../10_pan_diagnostic/sources/pan_inference_diagnostic/offline_pan_reversal_filter_off/analysis_handoff.md), [`docs/06`](../../docs/06_HIL_및_향후실험.md).
