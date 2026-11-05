# R2 파지 진단 — 20261105_143609_1k_t08_09_10_11_12_ft_series

자동 생성 (`scripts/r2_analyze.py`). 값 종류: [기록] diag · filter_log · dataset, [재구성] diag/replay (RTC 끔), [자동 후보] 규칙 판정 (사용자 판정 아님).

## 판별 첫 파지 (§11)

| 판 (ds) | 자리 (계획 · 사진 판정) | 사용자 P/F | 첫 파지 T4 [기록] | T0 계획 (s, chunk:idx) | T1 실행 구간 (s) | T2 명령 (s) | T3 실제 닫힘 (s) | T3−T2 (틱) | 손목 큐브 @T2 | Lift · Elbow 0.3 s 속도 (°/s) · 상태 | 닫힌 뒤 계획 남은 Lift / Elbow (°) | Wrist flex · roll 속도 (°/s) | 자동 후보 | R2 교정 추천 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | K1_L30 · Known (K1 0.4 cm, 각도 +37° = L30) | F | empty | 8.0 (12:35) | 8.6 | 9.2 | 9.3 | 2 | edge_below u=0.185 v=0.815 area=0.090 | 0.7 · 0.0 (stopped/stopped) | -4.1 / -4.5 | 1.3 · 4.0 | Empty grasp | — |
| 1 | U2_L30 · Known (K3 3.0 cm, 각도 +24° = L30) | F | undetermined | 12.0 (107:36) | 18.0 | 18.7 | 18.8 | 2 | ahead u=0.280 v=0.473 area=0.087 | 2.0 · 6.6 (stopped/moving) | 0.2 / -3.5 | 0.7 · 0.0 | Undetermined, Insufficient depth, Early close | 추가 접근 |
| 2 | U7_45 · Unknown (K6 5.8 cm, 각도 -40° = 45) | P | grasp | 8.0 (190:32) | 8.6 | 9.1 | 9.1 | 2 | in_zone u=0.368 v=0.762 area=0.110 | 5.3 · 2.0 (moving/stopped) | -12.2 / -24.8 | 1.3 · 2.6 | Successful grasp, Early close | 추가 접근 |
| 3 | U8_0 · Unknown (K4 3.2 cm, 각도 -0° = 0) | F | undetermined | 22.0 (237:19) | 22.0 | 22.6 | 22.7 | 2 | in_zone u=0.374 v=0.614 area=0.138 | 0.0 · 0.7 (stopped/stopped) | -10.1 / 4.3 | 4.0 · 2.6 | Undetermined | — |
| 4 | U1_R30 · Unknown (K2 4.9 cm, 각도 -27° = R30) | F | undetermined | 8.0 (305:40) | 8.6 | 9.4 | 9.5 | 2 | edge_below u=0.350 v=0.832 area=0.072 | 0.0 · 0.0 (stopped/stopped) | -6.1 / -0.7 | 0.0 · 1.3 | Undetermined | — |

## Known / Unknown 별 첫 파지

자리 판정 = 판 시작 front 사진 좌표 (cube_coords): K 명목 자리에서 3 cm 안 = Known (valid_near_K), 밖 = Unknown (valid_off_K, 좌표 정확도 미검증), 검출 · 보정 범위 문제 = invalid.

| 자리 | 판 | 쥠 | 빈 닫힘 | 미확정 | 닫힘 없음 | 사용자 P | 손목 @T2 ahead · below · in_zone · 기타 |
|---|---|---|---|---|---|---|---|
| Known | 2 | 0 | 1 | 1 | 0 | 0 | 1 · 1 · 0 · 0 |
| Unknown | 3 | 1 | 0 | 2 | 0 | 1 | 0 · 1 · 2 · 0 |

## 큐브 각도 별 첫 파지 (판 시작 사진 측정, d2 규칙으로 분류)

| 각도 | 판 | 쥠 | 빈 닫힘 | 미확정 | 닫힘 없음 | 계획 각도와 다름 |
|---|---|---|---|---|---|---|
| 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| L30 | 2 | 0 | 1 | 1 | 0 | 0 |
| R30 | 1 | 0 | 0 | 1 | 0 | 0 |
| 45 | 1 | 1 | 0 | 0 | 0 | 0 |

배치 계획과 다른 판 (r2_safety plan_check, 경고만): ds 1 U2_L30: 계획은 unknown 인데 사진 판정은 Known (K3 3.0 cm)

- T0 은 RTC 뒤 chunk 의 미래 계획 (예측) 이다. 실제 실행과 다를 수 있다.
- 손목 큐브 분류는 d2 사람 닫힘 시작 프레임으로 정한 영역 (r12_wrist_zone.json) 기준의 2D 화면 위치다. 3 차원 깊이 · 접촉이 아니다.
- '닫힌 뒤 계획 남은' = T2 를 낸 chunk 의 index (T2) → 49 까지 계획 변화 [기록 chunk].

## 닫힘 이벤트 전체 (재시도 포함)

| 판 | k | 성공 뒤 | T2 (s) | T3−T2 | T4 | T0 chunk:idx (예정 틱) | T1 chunk:idx | T0raw (RTC 끔) | 닫힘 계획 chunk 수 | 순서 OK |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 |  | 9.20 | 2 | empty | 12:35 (275) | 13:16 | —:— | 2 | True |
| 1 | 0 |  | 18.73 | 2 | undetermined | 107:36 (396) | 116:23 | —:— | 3 | True |
| 1 | 1 |  | 21.57 | 2 | grasp | 120:27 (647) | 120:27 | —:— | 1 | True |
| 1 | 2 | 예 | 35.47 | 0 | undetermined | 122:42 (702) | 141:24 | —:— | 4 | True |
| 1 | 3 | 예 | 42.30 | 2 | empty | 145:27 (1147) | 145:27 | —:— | 3 | True |
| 1 | 4 | 예 | 43.07 | 63 | undetermined | 153:12 (1292) | 153:12 | —:— | 1 | True |
| 1 | 5 | 예 | 45.10 | 2 | undetermined | 156:13 (1353) | 156:13 | —:— | 1 | True |
| 1 | 6 | 예 | 57.37 | 2 | empty | 157:0 (1360) | 173:28 | —:— | 5 | True |
| 2 | 0 |  | 9.07 | 2 | grasp | 190:32 (272) | 191:12 | —:— | 2 | True |
| 2 | 1 | 예 | 12.43 | 2 | empty | 192:0 (280) | 196:13 | —:— | 3 | True |
| 3 | 0 |  | 22.63 | 2 | undetermined | 237:19 (679) | 237:19 | —:— | 2 | True |
| 3 | 1 |  | 28.00 | 1 | empty | 243:32 (812) | 245:19 | —:— | 4 | True |
| 3 | 2 |  | 35.43 | 3 | undetermined | 248:19 (899) | 248:19 | —:— | 5 | True |
| 3 | 3 |  | 36.23 | 3 | undetermined | 258:6 (1086) | —:— | —:— | 1 | True |
| 3 | 4 |  | 38.73 | 2 | undetermined | 259:40 (1140) | 261:22 | —:— | 4 | True |
| 3 | 5 |  | 42.73 | 2 | empty | 264:29 (1229) | 264:29 | —:— | 4 | True |
| 3 | 6 |  | 49.57 | 3 | empty | 277:27 (1487) | 277:27 | —:— | 2 | True |
| 3 | 7 |  | 56.53 | 2 | undetermined | 279:0 (1500) | 288:16 | —:— | 3 | True |
| 3 | 8 |  | 57.87 | 2 | undetermined | 289:0 (1700) | 290:16 | —:— | 2 | True |
| 4 | 0 |  | 9.43 | 2 | undetermined | 305:40 (280) | 306:23 | —:— | 3 | True |
| 4 | 1 |  | 10.90 | 151 | undetermined | 308:27 (327) | 308:27 | —:— | 2 | True |
| 4 | 2 |  | 15.83 | 3 | undetermined | 310:28 (368) | 310:28 | —:— | 5 | True |
| 4 | 3 |  | 17.13 | 3 | undetermined | 317:0 (480) | 318:14 | —:— | 2 | True |
| 4 | 4 |  | 47.83 | 0 | undetermined | 319:0 (520) | 323:20 | —:— | 8 | True |
| 4 | 5 |  | 50.53 | 103 | empty | 368:16 (1516) | 368:16 | —:— | 1 | True |
| 4 | 6 |  | 53.87 | 3 | empty | 369:0 (1520) | 373:15 | —:— | 2 | True |

## 첫 파지: 쥠 vs 빈 닫힘 (관절별 중앙)

| joint | 결과 | 판 | 0.3 s 속도 중앙 | 1 s 이동 | T2 이후 계획 남은 (49 까지) | sent − present @T2 |
|---|---|---|---|---|---|---|
| shoulder_lift | grasp | 1 | 5.3 | 10.5 | -12.2 | -0.1 |
| shoulder_lift | empty | 1 | 0.7 | 4.8 | -4.1 | -0.4 |
| shoulder_lift | undetermined | 3 | 0.0 | 2.9 | -6.1 | -0.8 |
| elbow_flex | grasp | 1 | 2.0 | -0.4 | -24.8 | -1.2 |
| elbow_flex | empty | 1 | 0.0 | -3.6 | -4.5 | -2.6 |
| elbow_flex | undetermined | 3 | 0.7 | -2.4 | -0.7 | -1.4 |
| wrist_flex | grasp | 1 | 1.3 | -7.6 | 1.8 | 0.4 |
| wrist_flex | empty | 1 | 1.3 | 0.1 | 1.9 | 1.2 |
| wrist_flex | undetermined | 3 | 0.7 | 0.1 | 0.9 | -0.7 |
| wrist_roll | grasp | 1 | 2.6 | -1.9 | 13.1 | 0.4 |
| wrist_roll | empty | 1 | 4.0 | -1.8 | 0.1 | -0.1 |
| wrist_roll | undetermined | 3 | 1.3 | -2.4 | 3.8 | 0.9 |

## r2_safety

- STOP 0 행, warn 0 행 (`r2_safety.csv`).
