# 평가 20261113_113232_20k_t01_02_03_04_05_06_07_08_ft_series

- 세션: `main_k8/sgp01_real_eval` · 체크포인트: `../sg_pin/train/sgp01_pin96_20k_s2001/run/checkpoints/020000` · tag `t01_02_03_04_05_06_07_08_ft_series`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-13 11:32 · 끝: 2026-11-13 11:46
- 결과: 저장 8판 · **P 6 / F 2** · 성공률 75%
- 8° 제한 경고: 1390회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | P | 26.3 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | P | 35.8 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 59.2 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | P | 34.8 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
| 004 | F | 59.2 | [front](start_images/ep004_front.png) · [wrist](start_images/ep004_wrist.png) |  |
| 005 | P | 33.5 | [front](start_images/ep005_front.png) · [wrist](start_images/ep005_wrist.png) |  |
| 006 | F | 59.3 | [front](start_images/ep006_front.png) · [wrist](start_images/ep006_wrist.png) |  |
| 007 | P | 26.5 | [front](start_images/ep007_front.png) · [wrist](start_images/ep007_wrist.png) |  |
