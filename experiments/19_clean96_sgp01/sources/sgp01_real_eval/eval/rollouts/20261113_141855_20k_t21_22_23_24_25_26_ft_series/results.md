# 평가 20261113_141855_20k_t21_22_23_24_25_26_ft_series

- 세션: `main_k8/sgp01_real_eval` · 체크포인트: `../sg_pin/train/sgp01_pin96_20k_s2001/run/checkpoints/020000` · tag `t21_22_23_24_25_26_ft_series`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-13 14:18 · 끝: 2026-11-13 14:33
- 결과: 저장 6판 · **P 5 / F 1** · 성공률 83%
- 8° 제한 경고: 1177회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | P | 34.7 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 118.9 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 41.2 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | P | 97.8 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
| 004 | P | 53.9 | [front](start_images/ep004_front.png) · [wrist](start_images/ep004_wrist.png) |  |
| 005 | P | 93.1 | [front](start_images/ep005_front.png) · [wrist](start_images/ep005_wrist.png) |  |
