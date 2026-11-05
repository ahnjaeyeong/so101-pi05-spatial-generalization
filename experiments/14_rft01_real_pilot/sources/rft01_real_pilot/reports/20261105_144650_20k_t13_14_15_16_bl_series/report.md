# R2 파지 진단 — 20261105_144650_20k_t13_14_15_16_bl_series

자동 생성 (`scripts/r2_analyze.py`). 값 종류: [기록] diag · filter_log · dataset, [재구성] diag/replay (RTC 끔), [자동 후보] 규칙 판정 (사용자 판정 아님).

## 판별 첫 파지 (§11)

| 판 (ds) | 자리 (계획 · 사진 판정) | 사용자 P/F | 첫 파지 T4 [기록] | T0 계획 (s, chunk:idx) | T1 실행 구간 (s) | T2 명령 (s) | T3 실제 닫힘 (s) | T3−T2 (틱) | 손목 큐브 @T2 | Lift · Elbow 0.3 s 속도 (°/s) · 상태 | 닫힌 뒤 계획 남은 Lift / Elbow (°) | Wrist flex · roll 속도 (°/s) | 자동 후보 | R2 교정 추천 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | U2_L30 · Unknown (K3 3.5 cm, 각도 +21° = L30) | F | empty | 0.0 (0:0) | 0.0 | 0.1 | 0.1 | 0 | not_visible | 0.0 · 1.3 (stopped/stopped) | 46.7 / -32.7 | 1.3 · 4.0 | Empty grasp | — |
| 1 | U7_45 · Unknown (K6 6.1 cm, 각도 -45° = 45) | P | empty | 0.0 (89:0) | 0.0 | 0.1 | 0.1 | 0 | not_visible | 0.0 · 1.3 (stopped/stopped) | 40.8 / -30.0 | 2.6 · 9.2 | Empty grasp | — |
| 2 | U8_0 · Known (K4 2.6 cm, 각도 +4° = 0) | P | grasp | 0.0 (112:0) | 0.0 | 0.6 | 11.8 | 335 | not_visible | 0.0 · 1.3 (stopped/stopped) | 23.0 / -19.0 | 0.0 · 0.0 | Successful grasp | 정상 닫힘 (기준 시연) |
| 3 | U1_R30 · Unknown (K2 4.5 cm, 각도 -38° = 45) | P | undetermined | 0.0 (146:20) | 0.0 | 1.6 | 12.1 | 316 | left u=0.096 v=0.413 area=0.028 | 15.2 · 4.0 (moving/slow) | 2.6 / -2.9 | 1.3 · 1.3 | Undetermined, Center offset | 중심 정렬 |

## Known / Unknown 별 첫 파지

자리 판정 = 판 시작 front 사진 좌표 (cube_coords): K 명목 자리에서 3 cm 안 = Known (valid_near_K), 밖 = Unknown (valid_off_K, 좌표 정확도 미검증), 검출 · 보정 범위 문제 = invalid.

| 자리 | 판 | 쥠 | 빈 닫힘 | 미확정 | 닫힘 없음 | 사용자 P | 손목 @T2 ahead · below · in_zone · 기타 |
|---|---|---|---|---|---|---|---|
| Known | 1 | 1 | 0 | 0 | 0 | 1 | 0 · 0 · 0 · 1 |
| Unknown | 3 | 0 | 2 | 1 | 0 | 2 | 0 · 0 · 0 · 3 |

## 큐브 각도 별 첫 파지 (판 시작 사진 측정, d2 규칙으로 분류)

| 각도 | 판 | 쥠 | 빈 닫힘 | 미확정 | 닫힘 없음 | 계획 각도와 다름 |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| L30 | 1 | 0 | 1 | 0 | 0 | 0 |
| 45 | 2 | 0 | 1 | 1 | 0 | 0 |

배치 계획과 다른 판 (r2_safety plan_check, 경고만): ds 2 U8_0: 계획은 unknown 인데 사진 판정은 Known (K4 2.6 cm)

- T0 은 RTC 뒤 chunk 의 미래 계획 (예측) 이다. 실제 실행과 다를 수 있다.
- 손목 큐브 분류는 d2 사람 닫힘 시작 프레임으로 정한 영역 (r12_wrist_zone.json) 기준의 2D 화면 위치다. 3 차원 깊이 · 접촉이 아니다.
- '닫힌 뒤 계획 남은' = T2 를 낸 chunk 의 index (T2) → 49 까지 계획 변화 [기록 chunk].

## 닫힘 이벤트 전체 (재시도 포함)

| 판 | k | 성공 뒤 | T2 (s) | T3−T2 | T4 | T0 chunk:idx (예정 틱) | T1 chunk:idx | T0raw (RTC 끔) | 닫힘 계획 chunk 수 | 순서 OK |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 |  | 0.07 | 0 | empty | 0:0 (0) | 0:0 | —:— | 1 | True |
| 0 | 1 |  | 27.00 | 2 | empty | 33:25 (684) | 33:25 | —:— | 7 | True |
| 0 | 2 |  | 42.10 | 1 | undetermined | 52:38 (1078) | 58:28 | —:— | 5 | True |
| 0 | 3 |  | 43.00 | 3 | undetermined | 64:11 (1291) | 64:11 | —:— | 1 | True |
| 0 | 4 |  | 50.10 | 0 | grasp | 67:43 (1383) | 74:23 | —:— | 4 | True |
| 0 | 5 | 예 | 53.27 | 1 | undetermined | 79:18 (1598) | 79:18 | —:— | 1 | True |
| 0 | 6 | 예 | 56.50 | 2 | undetermined | 80:0 (1600) | 82:29 | —:— | 3 | True |
| 1 | 0 |  | 0.07 | 0 | empty | 89:0 (0) | 89:0 | —:— | 1 | True |
| 1 | 1 |  | 6.40 | 2 | grasp | 98:13 (193) | 98:13 | —:— | 1 | True |
| 1 | 2 | 예 | 10.17 | 2 | empty | 99:0 (200) | 103:25 | —:— | 4 | True |
| 2 | 0 |  | 0.60 | 335 | grasp | 112:0 (0) | 112:0 | —:— | 1 | True |
| 2 | 1 | 예 | 11.67 | 3 | grasp | 128:30 (350) | 129:10 | —:— | 2 | True |
| 2 | 2 | 예 | 15.20 | 3 | empty | 130:0 (360) | 134:16 | —:— | 3 | True |
| 3 | 0 |  | 1.60 | 316 | undetermined | 146:20 (20) | 146:20 | —:— | 2 | True |
| 3 | 1 |  | 12.07 | 2 | undetermined | 161:33 (333) | 163:22 | —:— | 4 | True |
| 3 | 2 |  | 13.53 | 2 | undetermined | 165:26 (406) | 165:26 | —:— | 2 | True |
| 3 | 3 |  | 17.20 | 1 | grasp | 167:22 (442) | 167:22 | —:— | 4 | True |
| 3 | 4 | 예 | 18.60 | 107 | empty | 172:0 (520) | 173:23 | —:— | 2 | True |
| 3 | 5 | 예 | 22.10 | 2 | empty | 174:0 (560) | 178:23 | —:— | 3 | True |

## 첫 파지: 쥠 vs 빈 닫힘 (관절별 중앙)

| joint | 결과 | 판 | 0.3 s 속도 중앙 | 1 s 이동 | T2 이후 계획 남은 (49 까지) | sent − present @T2 |
|---|---|---|---|---|---|---|
| shoulder_lift | grasp | 1 | 0.0 | 0.4 | 23.0 | -0.7 |
| shoulder_lift | empty | 2 | 0.0 | 0.0 | 43.8 | 1.1 |
| shoulder_lift | undetermined | 1 | 15.2 | 0.6 | 2.6 | -0.7 |
| elbow_flex | grasp | 1 | 1.3 | -1.4 | -19.0 | -0.9 |
| elbow_flex | empty | 2 | 1.3 | -0.1 | -31.4 | -4.4 |
| elbow_flex | undetermined | 1 | 4.0 | -3.0 | -2.9 | -1.4 |
| wrist_flex | grasp | 1 | 0.0 | 0.2 | -3.0 | -0.7 |
| wrist_flex | empty | 2 | 2.0 | 0.1 | -12.4 | 0.9 |
| wrist_flex | undetermined | 1 | 1.3 | -0.8 | 0.7 | -0.1 |
| wrist_roll | grasp | 1 | 0.0 | 0.2 | -1.0 | -0.5 |
| wrist_roll | empty | 2 | 6.6 | 0.4 | 0.4 | 0.3 |
| wrist_roll | undetermined | 1 | 1.3 | 0.4 | 3.0 | 0.6 |

## r2_safety

- STOP 0 행, warn 0 행 (`r2_safety.csv`).
