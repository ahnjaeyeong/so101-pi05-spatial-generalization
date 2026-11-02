# Redbox pi05 진동 — 외부 사례 비교와 우선순위 해결 계획 (2026-10-19)

이 문서는 분석과 계획만 담습니다. 코드는 수정하지 않았고 로봇은 실행하지 않았습니다.
대상: lerobot 0.6.2, pi05, chunk 50, expert만 학습한 20k (`redbox_all/train/32_20000/pi05_expert_bs32_20k`).

## 1. 우리 쪽에서 측정한 사실

| 항목 | 값 | 출처 |
|---|---|---|
| chunk 안 고주파 잡음 | 0.92–1.09° (사람 조작 시연의 부호 바뀜 0–3%, 모델 44–58%) | offline_ckpt_compare, offline_chunk_jitter |
| 8° 넘는 점프 | sync 20k 11.2회/분, 최대 31.1°, **15건 모두 chunk 경계** | rollout 20261019_091114 |
| 〃 (참고, 다른 모델) | cubemark RTC h20 rollout 0.5–1.3회/분, 최대 10.6–11.4° | cubemark eval rollouts |
| sync 멈춤 | 50프레임마다 약 0.35 s, 실효 25 Hz | console.log Cadence summary |
| \|A−S\|>8° 프레임 | rollout 28.8% (693/2404) — chunk 위치와 무관하게 고르게(22–30%), **90%가 빠른 의도 동작 중**, lift 514·elbow 356 | 녹화 데이터 |
| 〃 사람 조작 데이터 | **27.2%** (lift 12.4%, elbow 11.5%) — 녹화 때는 max_relative_target=None | redbox_all dataset, notes |
| 파지 정확도 | 20k 파지 자세 오차 5.4° (wrist_flex 10.6°), 실물 9번 시도 모두 몇 cm 차이로 놓침 | offline v2, 손목 영상 |
| relative action 정규화 폭 / 절대 정규화 폭 | pan 0.6, lift 1.0, elbow 0.9, wrist_flex 0.9, wrist_roll 0.5, gripper 0.7 | compute_relative_action_stats (메모리에서만 계산) |

## 2. 외부 사례: 주장, 검증 여부, 우리 환경 적용성

| 사례 | 내용 | 검증 여부 | 우리 환경 |
|---|---|---|---|
| lerobot #2559 (Open) | lerobot pi05가 openpi보다 떨린다는 보고. 원인 가설은 OpenPi=delta·LeRobot=absolute, 그리고 "scaling·timing mismatch" | **가설만**. 수치·실험 없음. relative 플래그로도 차이가 남는다는 보고(2026-06)도 수치 없음. 메인테이너 답 없음 | absolute로 chunk가 이전 chunk와 다른 곳에서 시작할 수 있다는 설명은 우리 경계 점프와 맞음. chunk 안 백색잡음은 이 가설로 설명 안 됨 |
| jinnymo/so101-pi05-base | lerobot 0.4.1 + VLASH, 17k편 전체 학습, n_action_steps 20, overlap 8, denoise 15, MEAN_STD, use_degrees=false. 경계 ramp `w=(i+1)/(n+1)` 8스텝 | 저자 측정: sync 멈춤 13.7%(로컬). README에 정지 구간 경계 진동 75/89/26% 감소라고 적혀 있으나 원자료 없음. 진동 크기는 1–2°로 우리 31°보다 훨씬 작음 | ramp는 우리 wrapper에서 후처리로 구현 가능(lerobot 수정 불필요). 우리 RTC가 같은 문제를 guidance 방식으로 다룸. 전체 학습 + 대규모 데이터라는 점이 우리와 다름 |
| lerobot #3794 / PR #3893 (Open) | 보낼 목표값에 EMA(α=0.25) + 프레임당 최대 변화 1.25 + 10 넘으면 리셋 | 저자 "잘 동작" — **수치 없음**. PR 미병합, 0.6.2에 없음 | wrapper에서 구현 가능. 단 1.25°/프레임(37.5°/s)은 사람 조작 p99(lift 3.5, wrist_flex 3.8°/프레임)보다 훨씬 느려 빠른 동작을 막고 지연을 늘림 → 오프라인 검증 필수 |
| lerobot #3122 (Closed) | LIBERO 시뮬, v0.5.0 회귀. n_action_steps 50→5/10 제안 | "좋아졌다"만 있고 **수치 없음**. 실제 원인은 0.5.0 전처리 변경(메인테이너) | 진동 사례 아님. 우리 sync에서 n_action_steps를 줄이면 0.35 s 멈춤이 5–10프레임마다 생겨 더 나빠짐. RTC에서는 queue_threshold가 재계획 시점을 정함 |
| lerobot RTC 문서 | 비동기 + 이전 chunk 남은 부분으로 guided inpainting. 기본 h=10, guidance 10, schedule(문서 권장 EXP, 0.6.2 기본 LINEAR) | 공식 구현. 문서에 우리 로봇 수치 없음 | 0.6.2에 있음. 이전 cubemark 평가에서 사용함(h20, threshold 40, 5스텝) |

## 3. 항목별 답

- **absolute 방식과 OpenPi의 차이**: 우리 action은 절대 관절 목표(°)이고 QUANTILES로 정규화합니다. OpenPi가 delta를 쓴다는 건 #2559 댓글의 주장이고 OpenPi 코드는 직접 확인하지 않았습니다. absolute에서는 새 chunk가 새 관측에서 독립적으로 샘플링되기 때문에, 이전 chunk 끝과 연결되도록 강제하는 장치가 없습니다(sync일 때).
- **relative action 지원과 조건**
  - 0.6.2에서 `--policy.use_relative_actions=true`로 켭니다. 변환 방식은 action − state(관측 시점)이고, gripper는 기본으로 절대값을 유지합니다(`relative_exclude_joints=["gripper"]`).
  - **재학습이 필요합니다.** 학습할 때 전처리·후처리는 자동으로 켜지지만, 정규화 통계는 데이터셋의 절대 action 통계를 그대로 씁니다. 그래서 먼저 `lerobot-edit-dataset --operation.type=recompute_stats --operation.relative_action=true --operation.chunk_size=50 --new_root=<사본>`으로 상대 통계를 담은 사본을 만들어야 합니다.
  - 기대 효과: 같은 정규화 잡음이 pan·wrist_roll에서는 약 절반이 되지만, lift·elbow·wrist_flex는 거의 그대로(0.9–1.0)입니다.
  - RTC와 함께 쓰는 경우를 위한 재기준 코드(`reanchor_relative_rtc_prefix`)도 있습니다.
- **RTC가 해결할 수 있는 것**
  - sync 멈춤(비동기 실행)
  - chunk 경계 불연속(앞 `execution_horizon` 스텝을 이전 chunk 쪽으로 끌어당김)
- **RTC가 해결할 수 없는 것**
  - chunk 안 고주파 잡음: 앞부분만 유도하고 나머지는 그대로입니다. cubemark 3k RTC rollout에도 방향 바뀜 1.8–4.5회/초가 남았습니다.
  - 파지 위치 오차
  - 빠른 동작 중의 추종 지연과 그로 인한 clamp
- **현재 코드의 action 스무딩**: 없습니다. 0.6.2 rollout에는 `interpolation_multiplier`(정책 action 사이 선형 보간으로 제어 주기를 높임, 잡음 제거 효과 없음)와 RTC guidance만 있습니다. EMA·속도 제한은 PR #3893에만 있습니다. 우리 `rollout_logged.py`는 로그만 남깁니다.
- **다른 프로젝트 방법의 적용성**
  - ramp, EMA, 속도 제한: 우리 wrapper에서 lerobot 수정 없이 적용 가능합니다.
  - VLASH의 지연 학습: 0.6.2의 `rtc_training_max_delay`(trained RTC)가 비슷하지만 재학습이 필요합니다.
  - 17k편 전체 학습: 다른 조건이라 결과를 그대로 옮길 수 없습니다.

## 4. 31° 경계 점프와 clamp 경고: 원인 분리와 검증 방법

경고는 두 출처가 섞여 있습니다.
1. **chunk 경계 점프** (15건, 최대 31°): RTC 또는 ramp로 제거 대상입니다.
   - 검증: 오프라인 재생에서 chunk 전환 때의 |Δaction|. 목표는 8° 넘는 점프 0건입니다.
2. **빠른 동작 중 추종 지연** (clamp 프레임의 90%, lift·elbow): 사람 조작 데이터도 27%가 8°를 넘으니, `max_relative_target=8`이 학습 때와 다른 조건(더 느린 동작)을 강제하고 있는 셈입니다.
   - 제거하는 방법은 관절별로 더 느슨한 제한(예: dict로 lift·elbow·wrist_flex만 완화)뿐입니다.
   - 반대로 속도를 제한하면 경고는 줄지만 동작이 느려져 학습 분포에서 벗어납니다.
   - **안전 설정이므로 값은 사용자가 결정합니다.**
   - 검증: rollout 데이터로 관절별 1차 서보 모델(state가 action을 따라가는 지연)을 맞춘 뒤, 후보 제한값과 필터 조합으로 clamp 비율을 시뮬레이션합니다. 기준은 사람 조작 데이터와 같은 조건에서의 비율입니다.

## 5. 우선순위 계획

### P0 — 오프라인 (재학습 없음, 로봇 없음)
1. **재생 시뮬레이터**
   - 녹화된 rollout(2404프레임, 영상 포함)과 학습 에피소드의 관측을 순서대로 넣습니다.
   - (a) sync 50, (b) RTC h=10/20 × schedule LINEAR/EXP × delay 5–8스텝 × denoise 5/10, (c) sync + ramp 8, (d) 각각 + EMA/속도 제한을 비교합니다.
   - 지표: 경계 점프, chunk 안 잔차, 지연(필터 전후 상호상관 이동), 파지 자세 오차 변화(offline_eval_v2의 pregrasp).
   - 열린 루프라 관측이 action에 반응하지 않는다는 한계를 명시합니다.
2. **필터 후보의 정확도 비용**: 사람 조작 action 자체에 필터를 걸었을 때 원 신호와의 차이. 이 값이 허용 상한입니다.
3. **서보·clamp 모델**: 위 4절 방법으로 max_relative_target 후보별 clamp 비율을 추정합니다.
4. **통과 기준(제안)**: 8° 넘는 경계 점프 0건, 잔차 0.4° 이하(사람 조작 0.25–0.5°), 지연 2프레임 이하, 파지 자세 오차 증가 0.5° 이하.

### P1 — 실물 안정성 확인 (사용자 실행, P0 통과 설정만)
- 현재 20k + RTC + 선택한 필터 + 사용자가 정한 관절별 제한으로 T1 1–3판을 돌립니다.
- 목적은 진동 제거 확인입니다. 파지 성공은 기대하지 않습니다(오프라인 파지 오차 5.4°).

### P2 — 재학습 (파지 성능, 별도 승인 후)
- 검증용 에피소드 24편(그룹별 4편)을 떼어 두고 전체 학습을 합니다(이전 분석).
- 2차 비교 후보는 relative action(상대 통계 사본 필요)과 trained RTC(`rtc_training_max_delay`)입니다.
- 평가 순서: 검증 에피소드에서 정확도와 잡음 → P0 재생 → 실물.
