# d2 — T1 + T3 (main_k8)

작성 2026-10-23. main_k8 비교 실험 d1 · d2 · d3 중 하나.

| 실험 | 학습 데이터 | 상태 |
|---|---|---|
| d1 | T1 + T2 | T2 미녹화 (계획만 있음) |
| **d2** | **T1 + T3** | **학습 완료 (2026-10-26 00:50), 실물 평가 준비됨** |
| d3 | T1 + T2 + T3 | T2 미녹화 |

세 실험 모두 T1 을 공통으로 넣고, 함께 넣는 과제(T2 / T3 / 둘 다)만 바꾼다.

## 1. 과제 정의

| 과제 | 내용 | 학습 문장 (task) |
|---|---|---|
| T1 | 탁자 위 빨강 큐브 1개를 갈색 상자에 넣기. 다른 물체 없음 | `pick up the red cube and put it in the brown box` |
| T3 | 빨강 큐브 1개 + 다른 색 큐브(방해물)가 있는 상태에서 빨강만 상자에 넣기 | `pick up the red cube and put it in the brown box` |
| (T2) | 빨강 큐브 2~4개를 모두 상자에 넣기 — d2 에는 없음 | `put all the red cubes in the brown box` |

- T1 과 T3 의 문장이 같아서 d2 데이터셋의 task 는 1개다 (2026-10-22 사용자 결정: 문장 통일 안 함, 기존 문장 유지).
- Known(K) = 정해진 위치 K1–K8 에 놓음. Random(R) = 위치 자유 (손 닿는 범위).
- 모든 판에 큐브 각도 계획이 있다: 0 · ↺30(L30) · ↻30(R30) · 45 (로봇 좌우선 기준, 로봇에 가장 가까운 면).

## 2. 수집 환경 (main_k8 공통)

- 2026-10-22 front 카메라 위치 변경 + 고정 위치 8개(K1–K8) 로 바꾼 뒤 새로 찍은 데이터. 예전 `main/redbox_*`(K1–K4, 384편)와 섞지 않음.
- 설정: `~/so101_boxpick/config/redbox8_layouts.yaml`
- K 배치 (로봇에서 상자를 볼 때): 상자 쪽 `K1 K2 K3` / 가운데 `K4 K5 K6` / 로봇 쪽 `K7 · K8`. 열 간격 15 cm, 행 간격 8.5 cm.
- 로봇 SO101 follower(`my_arm`) + leader(`my_leader`) 원격조종, 30 fps.
- 카메라 2대: front · wrist, 640×480 MJPG. 영상 AV1.
- state = follower 관절 6개, action = leader 관절 6개 (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper).
- 녹화 날짜: T1-K 10-22~10-23, T1-R 10-22~10-23, T3-K 10-23, T3-R 10-23.
- 판마다 check_dataset QA 통과 (경계선 각도·손목 표시는 사용자가 보고 ✓). 세부는 각 세션의 `qa_report.md`, `notes.md`.

## 3. 원본 → release → 합침

### 3.1 원본 세션과 제외한 판

| 순서 | 세션 | 원본 편수 | 제외 (원본 episode_index) | 유효 | 사용한 경로 |
|---|---|---|---|---|---|
| 1 | `redbox_t1_known` | 66 | 51, 64 (K7 ↺30 손목 먼 쪽으로 돌림·긴 판) | 64 | `redbox_t1_known/release` |
| 2 | `redbox_t1_random` | 68 | 2 (시작 정지 4.6 s), 36 (손목 반대로), 39, 41 (먼 구석, 긴 판) | 64 | `redbox_t1_random/release` |
| 3 | `redbox_t3_known` | 64 | 없음 | 64 | `redbox_t3_known/dataset` (원본 그대로) |
| 4 | `redbox_t3_random` | 65 | 57 (손목 반대로) | 64 | `redbox_t3_random/release` |

- 제외 목록은 `layout_plan.py train-args --session main_k8/<세션>` 출력 그대로 (꼬리표 tag 없음).
- relabel (실제 놓은 대로 계획을 고친 판, 데이터는 그대로): T3-K ep060 (노랑 없음), T3-R ep006 · ep045 · ep061.
- release 는 `lerobot-edit-dataset --operation.type delete_episodes --new_root <세션>/release` 로 만든 사본. 원본 `dataset/` 은 손대지 않음.
  - 확인: 남은 판의 길이 순서가 원본에서 제외 판만 뺀 것과 3개 모두 일치.
  - 제외 판이 들어 있던 영상 파일만 다시 인코딩됨 (SVT-AV1 CRF 30). 다시 인코딩된 판의 이미지 차이 평균 0.5~0.8 / 255, 그 밖의 판은 0. state·action 은 같음.

### 3.2 합친 데이터셋

- 경로: `~/so101_runs/main_k8/d2/dataset` · repo_id `oxr/so101_k8_d2` · 952 MB
- 명령 (2026-10-23 17:26):

```bash
$HOME/so101-env/bin/lerobot-edit-dataset --new_repo_id oxr/so101_k8_d2 --new_root $HOME/so101_runs/main_k8/d2/dataset --operation.type merge \
  "--operation.repo_ids=[oxr/so101_k8_redbox_t1_known_release, oxr/so101_k8_redbox_t1_random_release, oxr/so101_k8_redbox_t3_known, oxr/so101_k8_redbox_t3_random_release]" \
  "--operation.roots=[$HOME/so101_runs/main_k8/redbox_t1_known/release, $HOME/so101_runs/main_k8/redbox_t1_random/release, $HOME/so101_runs/main_k8/redbox_t3_known/dataset, $HOME/so101_runs/main_k8/redbox_t3_random/release]"
```

- 확인 (2026-10-23):
  - 256 편, 123,342 프레임, task 1개.
  - 판 길이 순서가 원본 4개를 차례로 이은 것과 일치.
  - 각 원본의 첫 판·마지막 판에서 프레임 하나씩(+5) 골라 action · state · front · wrist 를 합친 쪽과 비교 → 8곳 모두 같음.

| 합친 episode_index | 원본 | 편수 | 프레임 | 판 길이 (s) 평균 / 중앙 / 최소–최대 | 합계 |
|---|---|---|---|---|---|
| 0–63 | T1-K | 64 | 33,974 | 17.7 / 17.5 / 11.9–23.8 | 18.9 분 |
| 64–127 | T1-R | 64 | 32,758 | 17.1 / 16.8 / 13.0–25.9 | 18.2 분 |
| 128–191 | T3-K | 64 | 28,250 | 14.7 / 14.3 / 11.4–21.8 | 15.7 분 |
| 192–255 | T3-R | 64 | 28,360 | 14.8 / 14.6 / 10.6–23.9 | 15.8 분 |
| 합 | | 256 | 123,342 | | 68.5 분 |

- 과제별: T1 128편 · 66,732 프레임 (54%), T3 128편 · 56,610 프레임 (46%).

### 3.3 배치·각도 구성 (계획 기준, layout.csv)

| 원본 | 빨강 위치 | 빨강 각도 (0 / L30 / R30 / 45) | 방해물 개수 (판 수) | 방해물 각도 (0 / L30 / R30 / 45) |
|---|---|---|---|---|
| T1-K | K1–K8 각 8판 | 16 / 16 / 16 / 16 | 없음 | — |
| T1-R | 자유 | 16 / 16 / 16 / 16 | 없음 | — |
| T3-K | K1–K8 각 8판 | 16 / 16 / 16 / 16 | 1개 17 · 2개 23 · 3개 24 (방해물도 K 위치) | 34 / 34 / 34 / 33 |
| T3-R | 자유 | 16 / 16 / 16 / 16 | 2개 12 · 3개 13 · 4개 13 · 5개 14 · 6개 12 | 65 / 63 / 63 / 66 (QA 에서 판정 안 함, 참고값) |

- 방해물 색: 노랑 · 주황 · 파랑 · 초록. T3-R 은 빨강만 각도를 맞췄고 방해물은 자유롭게 놓음 (사용자, 10-23).

## 4. 학습

- 폴더: `~/so101_runs/main_k8/d2/train/32_20000/`
  - `run_pi05_expert_bs32_20k.sh` — lerobot-train 명령
  - `launch_pi05_expert_bs32_20k.sh` — 백그라운드 실행 + 시작/끝 시각(`.time`), pid, 5초마다 메모리(`.mem.log`) 기록
- 실행: 2026-10-23 17:39:34 시작 → 2026-10-26 00:50:55 끝 (rc=0, 55시간 11분). 체크포인트 005000 · 010000 · 015000 · 020000 (`last` = 020000).
- 결과: loss 처음 0.176 (step 50) → 마지막 0.020 (step 20000), 최저 0.019 (step 14500). 9.92 s/step, GPU 최대 20.8 GB. 상세 `pi05_expert_bs32_20k/training_params.md`.
- I/O 기록 (io-watch): `~/io-capture/20261023-1739/SUMMARY.md`, `~/io-capture-20261023-1739.zip`.
- 설정은 `main/redbox_all` 의 `pi05_expert_bs32_20k` 과 같고 데이터셋·출력 경로만 다르다:

| 항목 | 값 |
|---|---|
| policy | pi05, `lerobot/pi05_base` 에서 시작 |
| 학습 범위 | `train_expert_only=true`, `freeze_vision_encoder=true` |
| dtype | bfloat16, gradient checkpointing |
| lr | AdamW (β 0.9/0.95, wd 0.01, grad clip 1.0). 스케줄 = pi05 기본 `cosine_decay_with_warmup`: 기본값 warmup 1000 / decay 30000 이 steps 20000 에 맞춰 자동 축소 → 0→666 스텝 선형 warmup, 2.5e-5 에서 20000 스텝에 2.5e-6 까지 cosine 감소 (redbox_all 로그 확인: 10K 1.4e-5, 20K 2.5e-6) |
| batch / steps | 32 / 20,000 → 640,000 샘플 ≈ 5.2 epoch (123,342 프레임 기준) |
| 저장 | 5,000 스텝마다 (005000 · 010000 · 015000 · 020000), 체크포인트 하나 약 11 GB |
| 기타 | num_workers 4, log 50 스텝마다, wandb·허브 업로드 끔 |

- 참고 (redbox_all 같은 설정 실측): 10.2 s/step, GPU 21 GB, 시스템 최대 49 GB, 20k 에 56시간 39분.
- redbox_all 은 384편·188,530 프레임으로 같은 20k 스텝 = 약 3.4 epoch 였다.
- io-watch(systemd --user) 가 학습 실행을 자동으로 잡아 SUMMARY·zip 을 만든다.

## 5. 정하지 않은 것

- d1 · d2 · d3 의 스텝 수를 같게 둘지 (같은 20k 면 데이터 양이 다른 d3 는 epoch 가 적어진다), epoch 를 맞출지.
- 평가: 어떤 과제(T1 / T3 / T2)를 어떤 조건(Known K1–K8, Random, 각도)으로 몇 판 돌릴지. `eval/` 준비됨 (2026-10-26): 명령은 `eval/평가_명령.md`.

## 6. 폴더

```
main_k8/d2/
  description.md      이 파일
  dataset/            합친 데이터셋 (oxr/so101_k8_d2)
  train/32_20000/     학습 스크립트·로그, 출력 pi05_expert_bs32_20k/
  eval/               실물 평가 (run_rollout.sh · 분석 도구는 main/redbox_all/eval 에서 복사, 경로만 d2 로; reference_teleop = d2 학습 데이터 기준)
```
