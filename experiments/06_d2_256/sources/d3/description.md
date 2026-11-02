# d3 — T1 + T2 + T3 (main_k8)

작성 2026-10-23. main_k8 비교 실험 d1 · d2 · d3 중 하나. **아직 준비 안 됨 — T2 미녹화.**

| 실험 | 학습 데이터 | 상태 |
|---|---|---|
| d1 | T1 + T2 | T2 미녹화 → `../d1/description.md` |
| d2 | T1 + T3 | 데이터셋 합침·검증 완료, 학습 스크립트 준비됨 → `../d2/description.md` |
| **d3** | **T1 + T2 + T3** | **T2-K · T2-R 녹화 대기** |

세 실험 모두 T1 을 공통으로 넣고, 함께 넣는 과제(T2 / T3 / 둘 다)만 바꾼다. d3 는 d1 과 d2 의 데이터를 모두 넣은 것.

## 1. 과제 정의

| 과제 | 내용 | 학습 문장 (task) |
|---|---|---|
| T1 | 빨강 큐브 1개를 갈색 상자에 넣기. 다른 물체 없음 | `pick up the red cube and put it in the brown box` |
| T2 | 빨강 큐브 2~4개를 모두 상자에 넣기. 다른 물체 없음 | `put all the red cubes in the brown box` |
| T3 | 빨강 1개 + 다른 색 큐브(방해물) 중 빨강만 상자에 넣기 | `pick up the red cube and put it in the brown box` |

- task 는 2개 (T1 · T3 문장이 같음).
- 수집 환경은 d2 와 같다 → `../d2/description.md` 2절. T3 배치·각도 구성은 같은 문서 3.3절, T2 계획은 `../d1/description.md` 2절.

## 2. 들어갈 데이터

| 순서 | 세션 | 상태 (2026-10-23) | 편수 |
|---|---|---|---|
| 1 | `redbox_t1_known` | 완료, `release/` | 64 · 33,974 프레임 |
| 2 | `redbox_t1_random` | 완료, `release/` | 64 · 32,758 프레임 |
| 3 | `redbox_t2_known` | 계획만 | 목표 64 |
| 4 | `redbox_t2_random` | 계획만 | 목표 64 |
| 5 | `redbox_t3_known` | 완료, 제외 없음 → 원본 `dataset/` | 64 · 28,250 프레임 |
| 6 | `redbox_t3_random` | 완료, `release/` | 64 · 28,360 프레임 |

- 합계 384편 (예전 `main/redbox_all` 과 같은 편수·같은 순서 t1k, t1r, t2k, t2r, t3k, t3r).
- T1 · T3 의 release 사본과 확인 결과: `../d2/description.md` 3.1.

## 3. 준비 순서 (T2 녹화 뒤)

1. T2 두 세션 제외 목록 확인 (`layout_plan.py train-args`), 필요하면 `release/` 사본.
2. 6개 합침 → `main_k8/d3/dataset`, repo `oxr/so101_k8_d3`.
3. 판 길이 순서·경계 프레임·task 2개 확인.
4. 학습 스크립트는 d2 와 같은 설정에 경로만 바꿔 `d3/train/` 에 둔다.

## 4. 정하지 않은 것

- 스텝 수: d3 는 d1 · d2 보다 데이터가 약 1.5배라, 같은 20k (bs32) 이면 epoch 가 적다 (참고: redbox_all 384편 20k = 3.4 epoch, d2 256편 20k = 5.2 epoch).
- 평가 과제·조건·판 수.
