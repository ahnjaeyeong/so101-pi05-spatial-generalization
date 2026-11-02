# 평가 20261029_155513_32_20000_20k_pan_diag

- 세션: `main_k8/d2` · 체크포인트: `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` · tag `pan_diag`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true`
- 시작: 2026-10-29 15:55 · 끝: 2026-10-29 15:59
- 결과: 저장 1판 · **P 0 / F 1** · 성공률 0%
- 8° 제한 경고: 46회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 57.6 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
