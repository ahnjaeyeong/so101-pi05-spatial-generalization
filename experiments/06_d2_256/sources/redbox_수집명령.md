# redbox 본 수집 명령 — main_k8 (2026-10-22, 새 front 카메라 · 고정 위치 K1–K8 · 큐브 각도)

- 예전 `main/redbox_*` 와 다른 세션·데이터셋 (repo `oxr/so101_k8_redbox_*`). 설정: `~/so101_boxpick/config/redbox8_layouts.yaml`
  (check_dataset·히트맵은 main_k8/ 세션이면 이 설정을 저절로 씀). 계획은 6개 모두 만들고 verify 통과 (2026-10-22).
- K 배치 (로봇에서 상자를 보는 방향, 배너와 같음): 상자 쪽 `K1 K2 K3` / 가운데 `K4 K5 K6` / 로봇 쪽 `K7 · K8`.
- **Known 은 판마다 큐브 각도도 정해져 있다** (배너 칸 안 숫자): 각도 = 로봇에 가장 가까운 면과 로봇 좌우선의 예각,
  ↺ = 위에서 볼 때 반시계 · ↻ = 시계 · 0° · 45°(꼭짓점이 로봇 쪽). 4가지(0, ↺30, ↻30, 45)를 고르게 (2026-10-22: 15° 뺌).
  **Random 도 각도가 있다** (2026-10-22): 위치는 자유, 배너의 큐브 그림(빨강1 ↺30° 처럼 색+번호)대로 각도만 맞춰 놓는다.
  놓을 때 각도 가이드 `~/Desktop/redbox_K8_큐브각도_가이드_A4.pdf` (100% 인쇄). 녹화 뒤 check_dataset 이 첫 화면에서 각도를 재서
  범위 밖이면 표시 (0 은 ±15°, 30 은 같은 방향 15–37.5°, 45 는 37.5° 넘게). 녹화 전 확인: `python3 ~/so101_boxpick/scripts/cube_angle.py --live`.
- T2-K 는 K 가 8개라 조합을 골라 뽑음 (빨강 2개 24판 · 3개 24판 · 4개 16판, K 마다 23번, 16판마다 6·6·4).

- 녹화는 직접 실행 (로봇이 움직임). 그룹마다 16판씩: 처음은 `--dataset.num_episodes=16`, 이후는 `--resume=true --dataset.num_episodes=16`.
  마지막 실행은 `--dataset.num_episodes` 를 빼면 남은 개수를 자동으로 찍는다 (재촬영 줄 포함). 64를 넘겨 찍지 않는다.
- 권장 순서: T1-K 16 → T1-R 16 → T1-K 16 → … (같은 과제의 K/R 번갈아).
- 실행 전: ROS 를 썼으면 follower 전원 껐다 켜기 · 탁자에 다른 물체·손 없음 · 배너/체크리스트의 첫 판 배치대로 놓기.
- 판 끝 →, 다시 ←, 종료 Esc. 저장된 판을 버릴 때: `python3 ~/so101_boxpick/scripts/layout_plan.py exclude --session <세션> --episodes N --reason "..."`
- 실행마다 확인 (읽기만): `python3 ~/so101_boxpick/scripts/layout_plan.py status --session <세션>` · `python3 ~/so101_boxpick/scripts/check_dataset.py <세션>`

## t1_known — `main_k8/redbox_t1_known` (Known, 판 45초)

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_known --layout auto --target-episodes 64 --resume=true \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t1_known --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

## t1_random — `main_k8/redbox_t1_random` (Random 자유 배치, 판 45초)

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64  \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t1_random --layout auto --target-episodes 64 --resume=true \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t1_random --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

## t2_known — `main_k8/redbox_t2_known` (Known, 판 75초 · 빨강 2~4개)

> 2026-10-14 변경: 빨강 개수를 판마다 2·3·4개로 섞는다 (64판 = 24·24·16, 16판마다 6·6·4). **판마다 배너의 개수·배치대로 놓기** (Random 은 배치 ID 끝 n2/n3/n4 = 개수). 한 판 75초 (→ 로 일찍 넘기면 됨).

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t2_known --layout auto --target-episodes 64 \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t2_known --dataset.no_stamp=true \
  '--dataset.single_task=put all the red cubes in the brown box' \
  --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```
```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t2_known --layout auto --target-episodes 64 --resume=true \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t2_known --dataset.no_stamp=true \
  '--dataset.single_task=put all the red cubes in the brown box' \
  --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```


## t2_random — `main_k8/redbox_t2_random` (Random 자유 배치, 판 75초 · 빨강 2~4개)

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t2_random --layout auto --target-episodes 64 \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t2_random --dataset.no_stamp=true \
  '--dataset.single_task=put all the red cubes in the brown box' \
  --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t2_random --layout auto --target-episodes 64 --resume=true \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t2_random --dataset.no_stamp=true \
  '--dataset.single_task=put all the red cubes in the brown box' \
  --dataset.episode_time_s=75 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

## t3_known — `main_k8/redbox_t3_known` (Known, 판 45초)

> 2026-10-15 변경: 방해 물체 색(노랑·주황·파랑·초록)·개수를 판마다 섞는다. Known = 빨강 K1–K8 8판씩 + 방해 1–3개 (빨강이 안 쓰는 K), Random = 방해 2–6개 자유 배치 (배치 ID 끝 글자 Y노랑·O주황·B파랑·G초록 = 방해 색·개수, 예 T3R01-OOBG = 주황 2·파랑 1·초록 1). **판마다 배너의 색·개수·자리대로 놓기.**

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_known --layout auto --target-episodes 64 --resume=true \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t3_known --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

## t3_random — `main_k8/redbox_t3_random` (Random 자유 배치, 판 45초)

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 \
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```

```bash
python3 ~/so101_boxpick/scripts/record_ui.py --session main_k8/redbox_t3_random --layout auto --target-episodes 64 --resume=true\
  --robot.type=so101_follower --robot.port=/dev/so101_follower --robot.id=my_arm \
  '--robot.cameras={ front: {type: opencv, index_or_path: /dev/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4}, wrist: {type: opencv, index_or_path: /dev/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG", warmup_s: 4} }' \
  --teleop.type=so101_leader --teleop.port=/dev/so101_leader --teleop.id=my_leader \
  --dataset.repo_id=oxr/so101_k8_redbox_t3_random --dataset.no_stamp=true \
  '--dataset.single_task=pick up the red cube and put it in the brown box' \
  --dataset.episode_time_s=45 --dataset.reset_time_s=120 --dataset.push_to_hub=false \
  --dataset.num_episodes=16          # 두 번째 실행부터: 앞에 --resume=true 추가
```
