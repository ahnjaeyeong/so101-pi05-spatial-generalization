# EXP-11 · R1/R2 수동 복구·정렬 시연 수집

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-11** (보고서 ID S7-01, S7-02) |
| 날짜 | 2026-10-30 ~ 2026-11-04 (수집), 기록 갱신 2026-11-05 |
| 상태 | `PARTIAL` — pilot12 세션으로 학습 유효 **16편** (R1 4 · RC 12) 수집·QA 완료, EXP-13 학습에 사용. 원래 계획 (R1 16 · R2 32, 아래 4차 정의) 의 본 수집은 하지 않음 |
| 상태 이력 | 11-02 `IN_PROGRESS` (도구·계획 완료, 본 수집 0편, 연습 R1 12편) → 11-05 `PARTIAL` (11-03 ~ 11-04 pilot12 수집 반영) |

> R1/R2 는 **사람이 녹화하지 않는 준비 단계에서 오차 상태를 만들고, 바로잡는 원격조종 시연만 녹화**하는 방식이다. 정책 실행 중 사람이 교정하는 HIL (EXP-12) 과 다르다.

## 목적·가설
- R1 = 접촉 전 Pan 방향 재정렬·복구 16편, R2 = 파지 직전 국소 정렬·깊이·닫힘 타이밍 32편.
- [가설] d2 실패 상태 (지나침, 손목 놓침, 덜 다가감) 가 사람 시연에 없으므로 그 상태의 시연을 d2 에 섞으면 개선된다 (미검증).

## 정의 (현재 4차, 11-02)
- R1-A 초기 방향 (±15–30°) 4 · R1-B1 접근 중 반전 4 · R1-B2 지나침 4 · R1-B3 손목 놓침 4; 위치 K1–K8 + 자유점 F1–F4.
- R2: DEPTH 8 · AHEAD 8 · LEFT 4 · RIGHT 4 · READY 8 (손목 화면 시작 영역).
- 정의 변천 4회 (10-30 → 11-02): [`sources/r1_r2_collection/02_r1_r2_dataset_plan.md`](sources/r1_r2_collection/02_r1_r2_dataset_plan.md).
- [계획, 11-02 OFF/05] R1-B2/B3 에 **팔 접은 자세 (lift −95…−103°)**, 지나침 **15·25·40°+**, 손목 '테두리로 빠짐/안 보임' + front 보임 조건 추가 제안 (현재 R1-B2/B3 는 '팔 일부 폄 · 15–25°' 로 실패 상태와 다름). 도구 반영 여부 미확인.

## 2026-11-05 갱신 — pilot12 수집 (11-03 ~ 11-04)

[사실] 아래는 세션 파일 (`r12_episodes.csv`, `r12_plan.csv`, `qa/r12_qa_report.md`, `dataset/meta/info.json`) 기준. 수집 도구 = `main_k8/r1_r2_collection` (로컬 git, 브랜치 `ui-collector-schematic` 7e0904e 기준으로 11-05 사본 갱신), 설정 `config/r12_pilot12.yaml` (r1 · r2p) · `config/r12_recovery.yaml` (rc) — 세션 notes.md 의 명령 기준.

| 세션 (repo_id) | 만든 날 · 녹화 | 시나리오 | dataset 편 / 프레임 | 학습 유효 | 제외 (사유, 원문) |
|---|---|---|---|---|---|
| `main_k8/r12_pilot12_r1` (`oxr/so101_k8_r12_pilot12_r1`) | 11-03 · 11-04 14:17, 14:28 | R1-FOLD-OVER 8 (팔 접은 자세에서 Pan 지나침 → 복구) | 8 / 3,825 | **ep 4–7 (4편)** | ep 0–3: "지나침을 녹화 안에서 함 (쉬는 자세 시작) — 사용자 결정 재촬영 11-04" (`r12_plan.csv` status excluded) |
| `main_k8/r12_pilot12_rc` (`oxr/so101_k8_r12_pilot12_rc`) | 11-04 · 11:13 – 13:59 (5 실행) | RC-F1 4 · RC-F2 5 · RC-F3-L 2 · RC-F3-R 2 (R2 회복 시연) | 13 / 4,628 | **ep 0–10, 12 (12편)** | ep 11 (RC-F2): QA 제외 표시 — "끝 프레임이 쉬는 자세 아님 (lift 19, elbow −41); 결과 미입력; camera_stall…" |
| `main_k8/r12_pilot12_r2p` (`oxr/so101_k8_r12_pilot12_r2p`) | 11-03 16:04 ~ 11-04 09:50 | R2-P-AHEAD 3 · R2-P-DEPTH 3 (열린 그리퍼 접근 교정) | 6 / 2,711 | 0 (학습 미사용) | 세션 전체 EXP-13 manifest 에서 제외. ep0/ep1 은 '첫 빈 파지 뒤 재파지' 로 후보 아님 판정 (11-04 세션 판정 — 파일 근거 위치 미확인) |
| `main_k8/r12_pilot12_r2o` | 11-03 | — | dataset 없음 | 0 | 계획만 |

- [사실] 형식 (QA §1): 두 유효 세션 모두 d2 와 features · fps 30 · robot_type `so_follower` · codebase v3.0 · 과제 문장 `pick up the red cube and put it in the brown box` 동일. 판 번호·전역 index·frame_index 연속, 영상 프레임 수 = 판 길이 (±1).
- [사실] RC 12편 분포: K1–K8 모두 포함 (K1·K3·K5·K7 2편, 나머지 1편), 각도 0° · 45° · ↺30° · ↻30° 각 3편.
- [사실] QA 요약 줄 "문제 없음 0/12" (RC), "0/4" (R1) 은 QA 경고 (시작 Wrist 영역, 계획 각도 차이, 닫힘 깊이, 카메라 프레임 반복, 결과 미입력 등) 가 판마다 하나 이상 있다는 뜻이며, 사용자는 16편 모두 학습 사용을 승인했다 (EXP-13 `r01_manifest.py` 명시 목록). 경고 내역은 각 세션 `qa/r12_qa_report.md`.
- [사실] RC ep4 · ep8 · ep12 는 그리퍼를 열기 전에 팔이 먼저 움직임 (`arm_before_gripper_open` 7.8° · 17° · 6.1°, EXP-13 manifest 태그). 사용자 결정: 시작 망설임 구간 자르지 않음.
- [사실] 이 시연은 사람이 준비 단계 (녹화 안 함) 에서 실패 상태를 만든 뒤 교정 구간부터 녹화한 것으로, 정책 실행 중 개입하는 HIL (EXP-12) 과 다르다.
- 원본 보존: 제외 편 · r2p · r2o 포함 모든 세션 원본은 삭제·수정하지 않았다.
- 사본: [`sources/sessions/r12_pilot12_r1/`](sources/sessions/r12_pilot12_r1/), [`r12_pilot12_rc/`](sources/sessions/r12_pilot12_rc/), [`r12_pilot12_r2p/`](sources/sessions/r12_pilot12_r2p/), [`r12_pilot12_r2o/`](sources/sessions/r12_pilot12_r2o/) (notes · plan · episodes · attempts · QA · 시작 프레임 · setup 사진 · dataset meta info.json). dataset · review 영상은 Git 제외 — 경로·크기·SHA-256 [`sources/ARCHIVE_EXCLUDED.csv`](sources/ARCHIVE_EXCLUDED.csv).
- 학습 결과: [EXP-13](../13_recovery_ft/README.md). 실물 평가: [EXP-14](../14_rft01_real_pilot/README.md).

## 데이터셋 (저장 현황, 11-02 기준 — 이력)
| 세션 | 정의 세대 | 저장 편 | 결과 라벨 |
|---|---|---|---|
| main_k8/r1_realign_pilot (본, 16 계획) | 4차 | dataset 없음 | — |
| main_k8/r2_pregrasp_pilot (본, 32 계획) | | dataset 없음 | — |
| practice/r1_trial_old_20261102 | 10-30 | 3 | 미입력 |
| practice/r1_trial | §11 | 3 | 미입력 |
| practice/r1_try | §12 | 4 | 미입력 |
| practice/r1_try2 | §13 | 2 | 미입력 |
| practice/r1_try3 | §14 | 0 | — |
| practice/r2_trial | | 0 | — |

## 모델·학습·평가
- (11-05) 학습: d2 + R1 4 + RC 12 혼합 1 run 완료 → [EXP-13](../13_recovery_ft/README.md). d2+R1 단독 · d2+R2 단독은 미실행.
- (11-05) 평가: EXP-13 오프라인 재추론, EXP-14 실물 파일럿 16 판.
- (11-02 기록) 학습: `PLANNED` (d2+R1 / d2+R2 / d2+R1+R2, 혼합 비율·step 미정).
- (11-02 기록) 평가: `NOT_EVALUATED`. 재학습 후 실물 평가 프로토콜 미정의. 오프라인 기준 지표 제안: '손목 놓침·front 보임' 상태 (T4) 실행 구간 목표 쪽 비율 기준값 U 7.7% / G 4.3%.
- 도구 시험 (로봇 미연결): 단위 76, 오류 6, preview 13/11, 가짜 로봇 e2e 19 PASS.

## 실패 사례 (수집 과정)
[사실] 연습 중 SETUP 에서 Esc 로 0편 종료 반복 → 안전 게이트 완화 (NaN / |pan|>95 / 한계 10° / 리더–팔로워 >25° 만 BLOCK); r1_try2 ep1 리더–팔로워 34° 차로 28° 튐 → RESET 흐름 수정. [관찰] "범위가 너무 빡빡 … 값보다 대략적인 위치랑 방법이 중요".

## 한계 및 미확인
(11-05) 유효 16편은 원래 계획 (R1 16 · R2 32) 보다 적고 정의도 pilot12 로 바뀜. R1 은 FOLD-OVER 한 종류, 4편. 결과 라벨 (verdict) 은 11-04 수집 도구에서 제거되어 입력 안 함.
(11-02 기록) 본 수집 0, 연습 편의 정의 세대 혼재, 결과 라벨 0, 사람 파지 pan 이 K 기준과 ±9° 달라 측정 pan 오차 신뢰도 낮음.

## 다음 실험으로 이어진 이유
수집 → 재학습 (EXP-13, 완료) → 오프라인 T4 지표 (EXP-13) · 실물 파일럿 (EXP-14). [계획] EXP-13 §9 "R1 만 개선" 판정에 따라 R2 시연 시작 상태와 실물 AHEAD/BELOW 상태 분포 비교 후 d2 + R2 단독 FT 검토.

## 원본 자료
[`sources/r1_r2_collection/`](sources/r1_r2_collection/) (01–06 md, 07–12 pilot12 · collector mode · RC 설계·사용법, config, tools, tests; 11-05 다시 복사 — 신규 78 · 변경 7 파일), pilot12 세션 [`sources/sessions/r12_pilot12_*`](sources/sessions/), 제외 목록 [`sources/ARCHIVE_EXCLUDED.csv`](sources/ARCHIVE_EXCLUDED.csv), [`sources/sessions/`](sources/sessions/), 원본 `/home/user/so101_runs/main_k8/r1_r2_collection/`, `/home/user/so101_runs/practice/r1_*`.
