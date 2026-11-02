# 평가 전용 H — 준비 · 녹화 명령 (2026-10-27)

H 는 **평가에만** 쓴다.
- 어떤 학습 · 가중 계산 · LR/step 선택 · checkpoint 선택에도 넣지 않는다.
- train_weighted.py 는 `heldout` 이 들어간 경로를 거부한다.
- 가중 파일은 d2 256 판에서만 만든다 (check_cpu T6).

## 1. 설정 · 계획

| 항목 | 값 |
|---|---|
| config | `~/so101_boxpick/config/redbox8_heldout_h.yaml` (새 파일; `redbox8_layouts.yaml` 은 그대로) |
| 위치 | U1–U8 (d2 학습 큐브에서 2.0–2.8 cm, `s1_untrained_candidates.csv`) — 지금은 `confirmed: false` |
| 그룹 | `h_t1`: T1, Known, 32 판 (U 마다 4 판 = 각도 0 · ↺30 · ↻30 · 45 하나씩), seed 2901 |
| 세션 · repo | `main_k8/heldout_h` · `oxr/so101_k8_heldout_h` (아직 만들지 않음) |
| 미리보기 계획 | `H/plan_preview/` (layout.csv · layout_sheet.md · layout_map.svg · layout_template_a3.svg) — 세션에는 쓰지 않았음 |

| U | x, y (cm) | front px (640×480) | 최근접 학습 큐브 | 최근접 K |
|---|---|---|---|---|
| U1 | −24.1, 32.0 | 531, 121 | 2.8 cm | K7 5.7 cm |
| U2 | −26.1, −13.0 | 78, 109 | 2.3 | K8 9.5 |
| U3 | −10.6, 9.5 | 296, 256 | 2.1 | K2 2.9 |
| U4 | −11.1, −7.0 | 112, 250 | 2.0 | K3 4.4 |
| U5 | −8.6, 30.0 | 538, 279 | 2.1 | K1 3.5 |
| U6 | −22.6, −1.5 | 186, 138 | 2.3 | K8 3.5 |
| U7 | −14.6, 20.0 | 413, 213 | 2.3 | K4 6.9 |
| U8 | −5.6, 21.0 | 433, 314 | 2.1 | K1 6.2 |

## 2. 순서 (사용자 실행 — 로봇 · 카메라)

1. 위치 확인:
   - `H/plan_preview/layout_template_a3.svg` 를 100 % 로 인쇄하거나 자로 재서 U 마다 큐브를 놓는다.
   - front 화면 (`cube_angle.py --live` 또는 record_ui 미리보기) 에서 화면 좌표가 위 표와 맞는지 확인한다.
2. 확인되면 위치마다 확인 표시를 한다 (config 파일만 바뀜):
   ```bash
   cd ~/so101_boxpick
   for u in U1 U2 U3 U4 U5 U6 U7 U8; do python3 scripts/layout_plan.py set-known $u --confirm --config config/redbox8_heldout_h.yaml; done
   python3 scripts/layout_plan.py check-config --config config/redbox8_heldout_h.yaml
   ```
3. 계획을 만든다 (세션 폴더가 새로 생김):
   ```bash
   python3 scripts/layout_plan.py plan --config config/redbox8_heldout_h.yaml --group h_t1
   ```
4. 녹화 (main_k8 T1-K 와 같은 설정, 16 판씩 2 번):
   ```bash
   python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/heldout_h --layout auto --target-episodes 32 \
     --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
     '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
     --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
     --dataset.repo_id=oxr/so101_k8_heldout_h --dataset.no_stamp=true \
     '--dataset.single_task=pick up the red cube and put it in the brown box' \
     --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
     --dataset.num_episodes=16          # 두 번째 실행: 앞에 --resume=true 추가
   ```
5. QA (읽기만): `python3 ~/so101_boxpick/scripts/check_dataset.py main_k8/heldout_h`.
   - 실제 놓인 큐브 좌표는 `qa/positions.csv`, 각도는 check_dataset 의 각도 측정으로 남는다.
   - H 평가는 계획 좌표가 아니라 이 **실측값** 을 쓴다.

## 3. 알아 둘 점
- 로봇 평가 U layout 8 개 (실험설계 6 절: UF = U3·0, U4·L30, U6·L30, U8·0 / UN = U2·45, U1·45, U6·0, U7·0) 는 모두 이 32 판 안에 있다.
- 각도 4 개 중 |필요 손목 회전| ≥ 38° 인 조합 (U1·L30, U2·R30, U5·0 등) 도 들어 있다 (layout_plan 의 각도 균형을 바꾸지 않음). 분석할 때 따로 표시한다.
- H 녹화는 GPU 학습과 동시에 해도 된다 (로봇 · 카메라만 씀). 다만 io-watch 가 학습 · 녹화를 함께 기록한다.
