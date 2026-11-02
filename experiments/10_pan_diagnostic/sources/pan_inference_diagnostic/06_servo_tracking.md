# 06 명령 → 서보 추종 (기존 실물 5 판, 실측)

작성 2026-10-29. 생성: `scripts/p01_timeline.py`, `p02_existing_metrics.py` (→ `tables/p02_tracking.csv`), 관절별 · 사람 비교는 `scripts/p02c_tracking_late.py` (→ `tables/p02_tracking_joints.csv`, `p02c_human_lag.json`).
구간: onset ~ 첫 닫힘. 신호 정의는 03 문서 (raw = queue 출력, out = 필터 뒤, sent = clamp 뒤 Goal_Position, state = 틱 시작 Present_Position).

## 1. pan 단계별 변형

| 판 | raw → out (필터) \|차\| p50 / p95 | out → sent (clamp) \|차\| 최대 | pan clamp 틱 | 모든 관절 clamp 틱 |
|---|---|---|---|---|
| try3/ep0 (필터 없음) | 0 / 0 | 0.00° | 0 | 124 |
| try3/ep1 (필터 없음) | 0 / 0 | 5.07° | 7 | 245 |
| filt/ep0 | 0.24 / 1.25° | 0.00° | 0 | 151 |
| filt/ep1 | 0.16 / 0.95° | 0.06° | 1 | 81 |
| filt/ep2 | 0.20 / 1.63° | 0.64° | 4 | 18 |

- arm_filter 의 pan 속도 제한 (2.46°/틱) 이 걸린 틱: 판 0/1/2 = 7 / 6 / 8 (처음 3 s 안 7 / 0 / 8) (`p02b_timing.json`).
- 같은 제한값을 사람 리더 명령에 대면, onset 뒤 1.5 s 동안 프레임의 중앙값 9.1 % 가 넘고 256 편 중 159 편이 한 번 이상 넘는다. 사람 첫 1.5 s pan 최고 속도 중앙값 79°/s, 95 % 127°/s (제한 73.8°/s).
- 정책 raw pan 처음 3 s 최고 속도: try3/ep0 86, try3/ep1 143, filt/ep0 440 (chunk 경계 −14.7° 한 틱 포함), filt/ep1 33, filt/ep2 165 °/s.

## 2. 지연 · 추종 오차

| 판 | 움직이는 틱 (\|Δsent\| > 0.2°) | 최적 지연 (틱) | 그때 \|state − sent\| 평균 | 지연 0 일 때 | 움직일 때 \|sent − state\| p50 / p95 | 멈춰 있을 때 p50 |
|---|---|---|---|---|---|---|
| try3/ep0 | 302 | 4 | 0.45° | 1.05° | 0.64 / 4.16° | 0.44° |
| try3/ep1 | 218 | 4 | 0.46° | 2.13° | 1.18 / 7.05° | 0.53° |
| filt/ep0 | 174 | 4 | 0.44° | 1.80° | 1.29 / 6.24° | 0.39° |
| filt/ep1 | 273 | 4 | 0.39° | 1.50° | 0.97 / 4.85° | 0.57° |
| filt/ep2 | 155 | 4 | 0.45° | 2.10° | 1.32 / 6.28° | 0.50° |

관절별 (5 판 중앙값, 빠르게 움직일 때 = \|Δsent\| > 1°/틱):

| 관절 | 최적 지연 (틱) 중앙값 [최소, 최대] | \|sent − state\| p50 / p95 | clamp 틱 합 |
|---|---|---|---|
| shoulder_pan | 4 [4, 4] | 5.66 / 7.81° | 12 |
| shoulder_lift | 3 [2, 4] | 8.09 / 8.18° | 151 |
| elbow_flex | 5 [5, 8] | 8.09 / 8.18° | 197 |
| wrist_flex | 4 [4, 5] | 4.08 / 4.75° | 0 |
| wrist_roll | 3 [3, 4] | 3.83 / 5.56° | 0 |

사람 시연 같은 방법 (pan, 리더 action → 팔로워 state, onset ~ 파지, 232 편): 최적 지연 중앙값 4 틱 (p10 3, p90 4), \|Δa\| > 1°/프레임 일 때 \|a − s\| p50 6.95° · p95 12.31°.

## 3. 방법

- 최적 지연 L: 움직이는 틱에서 mean |state[t+L] − sent[t]| 가 가장 작은 L (0–10 틱).
- sent: clamp 경고가 대응된 틱·관절은 경고의 safe goal_pos, 나머지는 out. clamp 에 쓴 Present_Position 은 기록이 없어 state (틱 시작 값) 로 대신하지 않았다.

## 4. 한계

- 명령 '생성 → 전달' 지연 (chunk 가 만들어진 뒤 queue 에서 꺼낼 때까지) 은 chunk index 로만 안다 (02 문서 3 절). 실제 serial 쓰기 시각은 기록되지 않았다.
- 계측 켠 신규 평가 (`07` 문서) 의 ticks.csv 는 clamp 에 쓴 Present_Position 과 send 시간을 틱마다 남긴다.
