# 평가 20261105_111427_1k_t01_ft_k3_0

- 세션: `main_k8/rft01_real_pilot` · 체크포인트: `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` · tag `t01_ft_k3_0`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-05 11:14 · 끝: 2026-11-05 11:18
- 결과: 저장 1판 · **P 1 / F 0** · 성공률 100%
- 8° 제한 경고: 140회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | P | 18.0 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
