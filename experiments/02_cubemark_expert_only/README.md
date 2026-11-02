# EXP-02 · cubemark_v1 및 첫 Expert-only 학습

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-02** (보고서 ID S1-07, S1-08) |
| 날짜 | 2026-10-12 ~ 2026-10-13 |
| 상태 | `COMPLETED` (full FT 15k 는 실물 판정 기록 없음 → 해당 부분 `NOT_EVALUATED`) |

## 목적
- [사실] 새 과제 "Pick up the red cube and place it on the X mark." — 과제를 만든 목적 문장은 없음 (미확인).
- [사실] 8_3000 = action expert 만 학습 + vision 동결 — "사용자 지정 설정", 이유 문장 없음 (미확인). 이후 모든 학습이 이 방식을 따름.

## 검증 가설
- 명시된 가설 없음.

## 데이터셋
- cubemark_v1 (`oxr/so101_cubemark_v1`): 50편 38,816 프레임, X 표시 매판 이동, 상자 없음. 화면상 작은 빨간 큐브 [가설, 사진] (크기 기록 없음). ep40·41 놓침→재파지, ep42·43 잘못 둠→교정 (의도).

## 모델·학습
| run_id | 시작 | 학습 범위 | batch | steps (epoch) | LR | loss |
|---|---|---|---|---|---|---|
| `cubemark_pi05_15k` | pi05_base | full FT | 4 | 15,000 (1.55) | 2.5e-5 → 2.5e-6 | 0.095 → 0.011 |
| `cubemark_expert_bs8_3k` | pi05_base | **expert-only (693M), vision 동결** | 8 | 3,000 (0.62) | 2.5e-5 → 2.5e-6 (실효 warmup 100) | 0.095 → 0.037 |
설정: [`configs/training/cubemark_pi05_15k/`](../../configs/training/cubemark_pi05_15k/), [`configs/training/cubemark_expert_bs8_3k/`](../../configs/training/cubemark_expert_bs8_3k/).

## 추론 설정
rtc_fast (denoise 5, RTC h20, queue 40), max_relative_target 8°, 필터 없음.

## 평가 결과
| 평가 | 결과 |
|---|---|
| 15k 실물 10-13 오전 | [사실] rollout 2판 판정 없음; eval_ui 5판 (F F F / F F) 은 사용자 요청으로 **삭제** (notes 기록만) → `NOT_EVALUATED` |
| 3k 실물 10-13 eval_ui | [사실] **P 0 / F 8** (사람 판정), 8° 제한 경고 1,426회 |
| 오프라인 (학습 데이터, EXP-04 의 체크포인트 비교) | [사실] 15k 파지 자세 오차 1.76°, 잡음 0.33° (가장 정확·매끄러움); 3k 7.91°, 0.27° |

## 실패 사례
- [관찰, Claude 메모리 기록] 3k: "2판 멈춤, 나머지는 빈 파지 반복; 그리퍼가 큐브에서 2–10 cm 떨어져 닫힘". 메모 칸은 비어 있음.

## 분석 결과
- [가설] (EXP-04 진동 진단) cubemark expert-only 는 매끄러우므로 "expert-only 자체가 진동 원인은 아님".
- [사실] 학습 데이터 위 정확도가 가장 좋은 15k 도 실물 판정이 남은 성공이 없음 → 오프라인 지표가 실물 성능을 과대평가.

## 한계 및 미확인
cubemark 목적·큐브 크기, expert-only 선택 이유, 15k 실물 판정 (삭제됨).

## 다음 실험으로 이어진 이유
redbox 과제·2.5 cm 큐브로 위치 일반화 비교용 본 수집 (EXP-03) 으로 이동.

## 원본 자료
[`sources/cubemark_v1/`](sources/cubemark_v1/), 원본 `/home/user/so101_runs/main/cubemark_v1/`, 상세 [`docs/09`](../../docs/09_ChatGPT_전달용_종합자료.md) S1-07·S1-08.
