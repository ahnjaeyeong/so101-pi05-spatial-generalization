# analysis_handoff — SO-101 π₀.₅ d2 020000 Shoulder Pan 추론 진단 (2026-10-29)

다른 분석자 (ChatGPT 등) 에게 넘기는 요약이다. 숫자의 출처는 같은 폴더 문서 · `tables/` 다. 값 종류 표기:
- [실측] = 실물 실행 기록.
- [재구성] = 기록 dataset 프레임 · state 를 정책에 다시 넣은 오프라인 계산 (당시 noise 모름).
- [반사실] = 기록과 다른 조건의 오프라인 계산. 실물 미적용.

## 1. 설정

- **로봇 · 소프트웨어**: SO-101 팔로워, LeRobot 0.6.2.
- **정책**: π₀.₅ (PI05Policy), d2 = 256 편 (T1 + T3) expert-only 파인튜닝 020000.
  - 추론: num_inference_steps 5, chunk 50, fps 30.
- **RTC**: guided, EXP, execution_horizon 20, max_guidance_weight 10, queue_threshold 30.
  - queue 가 30 이하가 되면 새 추론을 시작한다.
  - merge 는 `chunk[delay:]` 로 queue 를 교체한다. 실물 적용 delay 는 10 틱이다.
  - 그래서 chunk 마다 index 10–29 가 실행된다. 판 첫 chunk 는 0–29 다.
- **inference_delay (정책에 넘기는 값, 기록 없음, 코드 규칙)**: 세션 두 번째 추론은 0, 이후 ceil(세션 최대 지연 × 30) = 11–12.
- **RTC 안내 weight**:
  - d = 11: index 10 → 1.0 · 14 → 0.29 · 18 → 0.03 · ≥ 20 → 0.
  - d = 0: index 10 → 0.17.
- **명령 경로**: queue 출력 → arm_filter (EMA α 0.5, pan 속도 제한 2.46°/틱) → clamp (Present ± 8°) → Goal_Position.
- **Pan 정의**:
  - need = pe − s0. pe 는 영상 추정 큐브 방위로 정한 기준 pan (사람 잡기 pan 대비 SD 2.31°).
  - 1 s 이동 비율 = (명령[t+30] − state[t]) / (pe − state[t]).

## 2. 기존 실물 5 판 [실측]

| 판 | 큐브 · 가까운 K 거리 | need | 첫 chunk index 29 비율 |
|---|---|---|---|
| try3/ep0 | K1 0.39 cm | −31.8° | 0.10 |
| try3/ep1 | K7 3.28 cm | −57.8° | 0.56 |
| filt/ep0 | K3 0.57 cm | +35.5° | 0.89 (그 뒤 경계 −14.7° 역전) |
| filt/ep1 | 새 위치, K3 7.25 cm | +22.3° | −0.07 (3.7 s 정지) |
| filt/ep2 | K4 1.70 cm | −42.7° | 0.83 (chunk 1 안 23° 되돌림) |

- 서보: pan 지연 4 틱 (사람 시연과 같음). 필터 · clamp 영향 p95 ≤ 1.63°.
- 닫힌 고리 1 s 이동 비율 (남은 오차 구간별) 은 아래와 같다.

| 남은 오차 | 정책 [실측] | 사람 [실측] |
|---|---|---|
| 6–12° | 0.12 | 0.60 |
| 12–25° | 0.21 | 0.95 |
| ≥ 25° | 0.48 | 0.95 |

## 3. 핵심 결과

1. 첫 chunk 는 RTC 를 거치지 않는다 (queue 비움 → prefix 없음). 따라서 filt/ep1 의 −7 % 는 Action Expert 출력 그대로다 [실측 + 코드].
2. 같은 관측에서 noise 만 바꾸면 첫 chunk 1 s pan 이 0 부근부터 need 전체까지 퍼진다. filt/ep1 은 256 개 중 54 % 가 < 10 %, 24 % 가 ≥ 50 % 이고, 기록값은 백분위 0.07 이다 [재구성].
3. 계획 자체 (RTC · 서보 없음) 의 1 s 이동 비율 중앙 0.14–0.49 는 실물 기록 0.12–0.48 과 같은 범위이고 사람 0.60–0.95 보다 작다 [재구성 vs 실측].
4. 같은 관측 · noise 에서 RTC 안내가 실행 끝 pan 을 바꾸는 양은 중앙 0.3° 다 [재구성].
5. 재구성 계획의 이동은 chunk 뒤쪽 (index 30–49, 실행 안 됨) 에 몰려 있다. 첫 chunk 기준 f29 중앙 0.06–0.38, f49 중앙 0.43–0.95 [재구성].
6. filt/ep0 경계 −14.7° [재구성 · 반사실]:
   - 안내 없는 U 에서도 중앙 −7.9° 다.
   - 기록 당시 inference_delay 0 이라 안내가 약했다. G(d = 0) 는 중앙 −5°, p10 −16° 이다.
   - inference_delay 11 이면 끊김이 ±2.6° 안으로 준다.
7. 실행 구간 안 역전 (filt/ep2 c1, try3/ep0 c4) [재구성]:
   - U 에서는 경계에서 바로 끊긴다.
   - G 는 경계를 잇지만, 안내가 끝나는 index 20 이후 22–34 % 의 noise 에서 10° 이상 되돌아간다.
8. A/B/C/D (72 chunk, 임의 문턱): A (모델이 보정 안 함) 38 · D (반대 방향) 7 · B (RTC 가 줄임) 2 · B′ 5 · C (서보) 0.
9. 첫 닫힘 직전 3 s 의 명령 자체가 pe 와 5–10° 다르고, 서보는 명령을 0.2–0.4° 안으로 따라갔다 [실측].

## 4. 판정 (잠정, 해석)

| 현상 | 판정 |
|---|---|
| 첫 chunk Pan 부족 | 모델 Raw Action 문제 |
| 닫힌 고리 접근 느림 | 모델 Raw Action 문제. 실행 구간 제한 (index 10–29) 의 몫은 아직 구분 불가 |
| filt/ep0 경계 −14.7° | 모델 Raw (연속 chunk 불일치) + RTC (세션 두 번째 추론의 inference_delay 0) |
| 실행 구간 안 역전 | 모델 Raw Action 문제 (RTC 는 index < 20 만 완화) |
| 새 위치 3.7 s 정지 | 모델 Raw Action 문제. 새 위치 효과는 아직 구분 불가 (판 1 개) |
| 닫힐 때 남은 Pan 오차 | 모델 Raw Action 문제 |
| 서보 | 근거 없음 (지연 = 사람, C 0 건) |
| filt/ep2 첫 chunk 가 재구성 분포 밖 | 아직 구분 불가 (당시 관측 · noise 기록 없음) |

## 5. 검증된 도구 · 다음 단계 재료

- **`ROLLOUT_DIAG=1`** (`d2/eval/diag_log.py`, 기본 꺼짐) 이 남기는 것:
  - chunk 마다 원 chunk · RTC 뒤 chunk · noise · prefix · inference_delay · 관측 PNG.
  - 틱마다 Goal 입력 · 보낸 Goal · clamp 에 쓴 Present · 카메라 프레임 나이.
- **가짜 팔 harness 결과** (diag 끔 3 · 켬 2): RTC 지연 · starved 수 같음, 루프 p50 +0.1 ms. 기록 입력으로 다시 계산한 22 chunk 가 기록과 차 0.0 이다. harness 에서 writer 종료 버그 1 건을 찾아 고쳤다.
- **실물 파일럿 절차**: `07_evaluation_protocol.md`.
  - 12 판, 각도 0. 순서 U3, K1, U2, U5, K3, U6, U7, K6, U4, U1, K7, U8.
  - 기존 d2 평가와 같은 설정이다.
  - 사용자가 직접 실행한다. Claude 는 로봇을 연결하지 않는다.
- **파일럿 뒤 분석**: `p05_replay_check.py` (재현 + RTC 끔 반사실, 오프라인), `p07_new_eval_analysis.py`.

## 6. 하지 않은 것 · 한계

- 학습 · 파인튜닝 · 데이터 수집 · 로봇 연결 · RTC 설정 변경 실물 적용은 하지 않았다.
- sampling_ablation:
  - A2_s2001 은 004000 까지 정상 종료한 뒤 큐가 스스로 멈췄다 (2026-10-29 13:58).
  - A2r · A0′ 는 미시작, A2 eval_hook 은 미실행이다. 재개 절차는 01 문서 4 절에 있다.
- 재구성은 AV1 재부호화 영상을 쓴다. 첫 chunk 의 실제 관측 틱 · noise 는 기록이 없다.
- 기록값이 재구성 p10–p90 에 든 비율은 65–70 % 다 (기대 80 %).
- 반사실은 한 chunk 열린 고리 계산이다.
- 판 5 개, 새 위치 1 개, 정책 1 개다.

## 7. 파일

- 문서: `01_training_pause_status.md` … `08_diagnostic_conclusion.md`.
- 표: `tables/`
  - `p01_ticks.parquet`: 틱 시간축 (raw · out · sent · state).
  - `p02_*`: 기존 지표.
  - `p03b_*.npz`: U/G 재구성.
  - `p03c_*`: 반사실.
  - `p04_harness_summary.csv`
  - `p06b_chunks.csv`, `p06c_*`, `p06d_*`, `p06e_abcd.csv`
- 그림: `figs/`
  - fig1: pan 시간축.
  - fig2: 1 s 이동 비율 사람 vs 정책.
  - fig3: 집중 chunk 기록 vs U/G.
  - fig4: 경계 반사실.
  - fig5: 첫 chunk 분포.

## 8. 실물 계측 파일럿 12 판 (2026-10-29 오후) — 자세히는 `10_pilot_results.md`

- **기록**: 두 실행 모두 VERIFY_OK. 534 chunk 모두 기록 입력으로 다시 계산하면 기록과 같다 (차 0.0°).
- **판 구성**: 좌표 12/12 유효 (near_K 4, off_K 8).
  - 시작 pan +5.4 … +7.0° (학습 범위 −14.8 … +3.8° 밖).
  - 큐브 각도 7/11 판이 |각도| > 10°.
  - P 4/12.
- **첫 chunk (RTC 없음)** 1 s 이동 비율 중앙: 왼쪽 need 6 판 0.035, 오른쪽 6 판 0.69.
  - 같은 관측에서 noise 64 개: 큰 왼쪽 need 5 판은 53–80 % 가 거의 정지. 학습 K1 · K7 도 같다.
- **정지 구간**: chunk 마다 계획 이동은 idx 30–49 에 있고, 실행되는 10–29 는 정지에 가깝다. RTC 끔 반사실도 같다.
- **RTC**: chunk 경계 끊김을 막는다 (기록 seam ≥ −1.7°, RTC 끔이면 −4 … −37°). 실행 구간 안 되돌림은 최대 20° 남는다.
- **첫 닫힘 \|Pan 오차\| 중앙**: near_K 1.7°, off_K 4.8°. off-K 정답 좌표는 미검증 → 아직 구분 불가.
- **판정 (잠정)**:
  - 초기 Pan 부족 · 정지 = 모델 Raw.
  - 시작 pan 영향 = 구분 불가.
  - 경계 역전 = RTC 가 억제.
  - 서보 = 근거 없음.
