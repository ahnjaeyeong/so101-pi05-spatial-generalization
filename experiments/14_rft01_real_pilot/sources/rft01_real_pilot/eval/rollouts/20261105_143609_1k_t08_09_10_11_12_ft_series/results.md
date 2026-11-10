# 평가 20261105_143609_1k_t08_09_10_11_12_ft_series

- 세션: `main_k8/rft01_real_pilot` · 체크포인트: `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` · tag `t08_09_10_11_12_ft_series`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-05 14:36 · 끝: 2026-11-05 14:46
- 결과: 저장 5판 · **P 1 / F 4** · 성공률 20%
- 8° 제한 경고: 467회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 58.8 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 59.3 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 17.1 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | F | 59.3 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
| 004 | F | 59.3 | [front](start_images/ep004_front.png) · [wrist](start_images/ep004_wrist.png) |  |
