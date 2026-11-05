# 평가 20261105_132118_1k_t04_ft_k1_0

- 세션: `main_k8/rft01_real_pilot` · 체크포인트: `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` · tag `t04_ft_k1_0`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-05 13:21 · 끝: 2026-11-05 13:25
- 결과: 저장 1판 · **P 1 / F 0** · 성공률 100%
- 8° 제한 경고: 177회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | P | 26.7 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
