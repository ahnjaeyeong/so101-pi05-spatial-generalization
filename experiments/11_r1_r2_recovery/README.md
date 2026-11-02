# EXP-11 · R1/R2 수동 복구·정렬 시연 수집

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-11** (보고서 ID S7-01, S7-02) |
| 날짜 | 2026-10-30 ~ (진행 중) |
| 상태 | `IN_PROGRESS` (도구·계획 완료, 본 수집 0편, 연습 R1 12편) |

> R1/R2 는 **사람이 녹화하지 않는 준비 단계에서 오차 상태를 만들고, 바로잡는 원격조종 시연만 녹화**하는 방식이다. 정책 실행 중 사람이 교정하는 HIL (EXP-12) 과 다르다.

## 목적·가설
- R1 = 접촉 전 Pan 방향 재정렬·복구 16편, R2 = 파지 직전 국소 정렬·깊이·닫힘 타이밍 32편.
- [가설] d2 실패 상태 (지나침, 손목 놓침, 덜 다가감) 가 사람 시연에 없으므로 그 상태의 시연을 d2 에 섞으면 개선된다 (미검증).

## 정의 (현재 4차, 11-02)
- R1-A 초기 방향 (±15–30°) 4 · R1-B1 접근 중 반전 4 · R1-B2 지나침 4 · R1-B3 손목 놓침 4; 위치 K1–K8 + 자유점 F1–F4.
- R2: DEPTH 8 · AHEAD 8 · LEFT 4 · RIGHT 4 · READY 8 (손목 화면 시작 영역).
- 정의 변천 4회 (10-30 → 11-02): [`sources/r1_r2_collection/02_r1_r2_dataset_plan.md`](sources/r1_r2_collection/02_r1_r2_dataset_plan.md).
- [계획, 11-02 OFF/05] R1-B2/B3 에 **팔 접은 자세 (lift −95…−103°)**, 지나침 **15·25·40°+**, 손목 '테두리로 빠짐/안 보임' + front 보임 조건 추가 제안 (현재 R1-B2/B3 는 '팔 일부 폄 · 15–25°' 로 실패 상태와 다름). 도구 반영 여부 미확인.

## 데이터셋 (저장 현황)
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
- 학습: `PLANNED` (d2+R1 / d2+R2 / d2+R1+R2, 혼합 비율·step 미정).
- 평가: `NOT_EVALUATED`. 재학습 후 실물 평가 프로토콜 미정의. 오프라인 기준 지표 제안: '손목 놓침·front 보임' 상태 (T4) 실행 구간 목표 쪽 비율 기준값 U 7.7% / G 4.3%.
- 도구 시험 (로봇 미연결): 단위 76, 오류 6, preview 13/11, 가짜 로봇 e2e 19 PASS.

## 실패 사례 (수집 과정)
[사실] 연습 중 SETUP 에서 Esc 로 0편 종료 반복 → 안전 게이트 완화 (NaN / |pan|>95 / 한계 10° / 리더–팔로워 >25° 만 BLOCK); r1_try2 ep1 리더–팔로워 34° 차로 28° 튐 → RESET 흐름 수정. [관찰] "범위가 너무 빡빡 … 값보다 대략적인 위치랑 방법이 중요".

## 한계 및 미확인
본 수집 0, 연습 편의 정의 세대 혼재, 결과 라벨 0, 사람 파지 pan 이 K 기준과 ±9° 달라 측정 pan 오차 신뢰도 낮음.

## 다음 실험으로 이어진 이유
수집 → 재학습 → 오프라인 T4 지표·실물 평가 (계획).

## 원본 자료
[`sources/r1_r2_collection/`](sources/r1_r2_collection/) (01–06 md, config, tools, tests), [`sources/sessions/`](sources/sessions/), 원본 `/home/user/so101_runs/main_k8/r1_r2_collection/`, `/home/user/so101_runs/practice/r1_*`.
