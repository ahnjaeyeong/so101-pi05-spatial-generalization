# 평가 20261113_131552_20k_t17_18_19_20_ft_series_qt18eh15

- 세션: `main_k8/sgp01_real_eval` · 체크포인트: `../sg_pin/train/sgp01_pin96_20k_s2001/run/checkpoints/020000` · tag `t17_18_19_20_ft_series_qt18eh15`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=18 --inference.rtc.execution_horizon=15 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-13 13:15 · 끝: 2026-11-13 13:26
- 결과: 저장 4판 · **P 1 / F 3** · 성공률 25%
- 8° 제한 경고: 301회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 58.8 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 43.9 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 59.3 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | F | 59.3 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
