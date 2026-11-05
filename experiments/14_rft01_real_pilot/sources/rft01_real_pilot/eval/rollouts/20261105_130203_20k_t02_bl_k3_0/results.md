# 평가 20261105_130203_20k_t02_bl_k3_0

- 세션: `main_k8/rft01_real_pilot` · 체크포인트: `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` · tag `t02_bl_k3_0`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-05 13:02 · 끝: 2026-11-05 13:06
- 결과: 저장 1판 · **P 0 / F 1** · 성공률 0%
- 8° 제한 경고: 88회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 58.8 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
