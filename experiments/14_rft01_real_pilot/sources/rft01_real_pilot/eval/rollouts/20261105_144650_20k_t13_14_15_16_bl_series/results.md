# 평가 20261105_144650_20k_t13_14_15_16_bl_series

- 세션: `main_k8/rft01_real_pilot` · 체크포인트: `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` · tag `t13_14_15_16_bl_series`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-05 14:46 · 끝: 2026-11-05 14:54
- 결과: 저장 4판 · **P 3 / F 1** · 성공률 75%
- 8° 제한 경고: 470회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 58.8 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | P | 15.2 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 22.5 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | P | 28.6 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
