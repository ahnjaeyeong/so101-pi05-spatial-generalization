# EXP-01 · 종이 큐브 초기 실험 (practice_10, practice_50, E0_J_0)

| 항목 | 내용 |
|---|---|
| 실험 ID | **EXP-01** (보고서 ID S1-01 ~ S1-06, S1-09) |
| 날짜 | 2026-10-02 ~ 2026-10-13 |
| 상태 | `COMPLETED` (학습·실물 평가 완료) |
| 표기 | [사실] 파일 측정값 · [관찰] 연구자 실물 관찰 · [가설] 분석 해석 · [계획] 설계만 |

## 목적
- [사실] practice_10: "성능이 아니라 학습 → 실물 실행까지 끝까지 도는지 확인" (`sources/docs/practice_10_pi05_2k.md`).
- [사실] practice_50: practice_10 다음 단계로 데이터 50편 수집·재학습. 명시 목적 문장은 없음.
- [사실] E0_J_0 (부수 실험): practice_50 15k 정책으로 잡고 ROS2 트윈 IK 로 놓기.

## 검증 가설
- [가설] practice_10 실패는 "데이터가 10판뿐인 게 가장 큰 원인" (practice_10 문서).
- 공간 일반화를 명시적으로 측정한 실험은 이 단계에 없다.

## 데이터셋
| 이름 (repo_id) | 편 / 프레임 | 큐브 | 비고 |
|---|---|---|---|
| practice_10 (`oxr/so101_cubebox_practice10`) | 10 / 6,589 | 빨간 **종이** 큐브 [관찰], 크기 미확인 | 수동 노출 156 / WB 4600 |
| practice_50 (`oxr/so101_cubebox_practice50`) | 50 / 30,884 | 종이 큐브 ≈53 mm (집게 값 역산, 자로 잰 값 아님) | 상자 왼쪽 고정, 큐브 오른쪽 절반 자유; ep040–042 의도적 빗잡기 |
메타데이터: [`configs/datasets/`](../../configs/datasets/) (`practice_10_info.json`, `practice_50_info.json`).

## 모델·학습
| run_id | 시작 | 학습 범위 | batch | steps (epoch) | LR | loss |
|---|---|---|---|---|---|---|
| `practice_10_pi05_2k` | `lerobot/pi05_base` | **full FT** (vision 포함 4.14B) | 4 | 2,000 (1.21) | 2.5e-5 → 2.5e-6 cosine (실효 warmup 66) | 0.139 → 0.020 |
| `practice_50_pi05_15k` | `lerobot/pi05_base` | full FT | 4 | 15,000 (1.94) | 2.5e-5 → 2.5e-6 (실효 warmup 500) | 0.131 → 0.014 (최저 0.009) |
- Vision freeze: **아니오** (두 run 모두).
- 설정·스크립트: [`configs/training/practice_10_pi05_2k/`](../../configs/training/practice_10_pi05_2k/), [`configs/training/practice_50_pi05_15k/`](../../configs/training/practice_50_pi05_15k/). 체크포인트 해시: [`configs/checkpoints/CHECKPOINTS.csv`](../../configs/checkpoints/CHECKPOINTS.csv).

## 추론 설정
- practice_10 실물: sync / RTC h20 q20·q30 / rtc_fast (denoise 5, RTC h20, queue 40), max_relative_target 8°, 필터 없음.
- practice_50 실물: rtc_fast.

## 평가 방법과 결과
| 평가 | 결과 | 판정 |
|---|---|---|
| practice_10 오프라인 (학습 판 ep001·ep004, open-loop) | [사실] 팔 5관절 평균 오차 2.28–2.40°, chunk 경계 점프 최대 24.8–42.7°; 화면 교체 시 pan 예측 21–30° 변화 | 학습 데이터 위 (일반화 아님) |
| practice_10 실물 10-06 | [사실] 저장 7판 중 **1판 성공** (rtc_fast, 107 s) | 판정자 미기재 |
| practice_50 실물 10-07 | [사실] 3/3 | Claude 가 front 마지막 프레임으로 판정 |
| practice_50 실물 10-13 (eval_ui) | [사실] **P 3 / F 5** | 사람 판정; 상자·큐브 배치 일부 변경 |
| E0_J_0 10-08 | [사실] 정책이 쥐고 3 cm 들기 5/5; 실행기 조임 (쥔 값 − 6) 에 종이 큐브가 0.4 s 사이 4.2–4.5 단위 눌려 '놓침' 오판 반복 (10-12 재발) | 로그 |

## 실패 사례
- [관찰] "너무 가벼워서 위치를 벗어나는 바람에 잡는 데 어려움", "건드려서 자리를 벗어나도 원래 자리를 보고 허우적댐", "학습할 때 잡는 세기를 잘 조절해야 할 것 같음".
- [사실] practice_10: 큐브가 손가락 사이에 있는데 그리퍼만 여닫음; 팔이 덜 내려감.
- [가설, 사진 육안] practice_50 10-13 실패 5판 = 큐브 30° 회전·화면 끝·로봇 가까이, 상자 이동·회전 배치.

## 분석 결과
- [가설] 흔들림은 chunk 전환 + 정책 출력 잔떨림, 반응 지연 0.3–1.7 s.
- [가설] 조임·놓침 규칙은 큐브 재질과 함께 정해야 함 (E0_J_0).

## 한계 및 미확인
- 종이 큐브 → 2.5 cm 큐브 **교체 이유**, 2.5 cm 큐브의 **재질 (나무 여부)**: 기록 없음.
- 종이 큐브 영구 변형·형태 불균일 기록 없음 (조임 중 압축만).
- 10-07 (3/3) 과 10-13 (3/8) 은 판정 방식·배치가 달라 같은 척도 아님.

## 다음 실험으로 이어진 이유
- [계획→실행] practice_10 문서: 큐브 위치 다양화, 밀린 큐브 다시 잡기, 끝까지 내려가 잡기, 수십 판 재학습 → practice_50.
- 10-12 작은 큐브 등장 (cubemark), 10-13 사용자가 2.5 cm 정육면체 확인 → EXP-02, EXP-03.

## 원본 자료
- 복사본: [`sources/`](sources/) (출처·해시는 [`SOURCES_MANIFEST.csv`](../../SOURCES_MANIFEST.csv))
- 원본: `/home/user/so101_runs/practice/practice_10/`, `/home/user/so101_runs/practice/practice_50/`, `/home/user/so101_runs/docs/practice_10_pi05_2k.md`, `/home/user/so101_runs/e0_j0/`
- 상세: [`docs/01`](../../docs/01_연구_전체_타임라인.md) 1단계, [`docs/09`](../../docs/09_ChatGPT_전달용_종합자료.md) S1-01~S1-06
