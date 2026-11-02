# 평가 20261029_170219_32_20000_20k_filt_on

- 세션: `main_k8/d2` · 체크포인트: `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` · tag `filt_on`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true --rollout_guard=warn`
- 시작: 2026-10-29 17:02 · 끝: 2026-10-29 17:08
- 결과: 저장 4판 · **P 2 / F 2** · 성공률 50%
- 8° 제한 경고: 631회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 25.7 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 16.2 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 19.6 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | P | 23.8 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
