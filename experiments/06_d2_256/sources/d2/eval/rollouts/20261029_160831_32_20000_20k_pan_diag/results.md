# 평가 20261029_160831_32_20000_20k_pan_diag

- 세션: `main_k8/d2` · 체크포인트: `train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` · tag `pan_diag`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=true`
- 시작: 2026-10-29 16:08 · 끝: 2026-10-29 16:23
- 결과: 저장 11판 · **P 4 / F 7** · 성공률 36%
- 8° 제한 경고: 1227회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | F | 33.9 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 50.8 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | F | 17.9 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | F | 13.5 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
| 004 | F | 13.3 | [front](start_images/ep004_front.png) · [wrist](start_images/ep004_wrist.png) |  |
| 005 | P | 17.5 | [front](start_images/ep005_front.png) · [wrist](start_images/ep005_wrist.png) |  |
| 006 | P | 22.3 | [front](start_images/ep006_front.png) · [wrist](start_images/ep006_wrist.png) |  |
| 007 | F | 24.3 | [front](start_images/ep007_front.png) · [wrist](start_images/ep007_wrist.png) |  |
| 008 | F | 15.2 | [front](start_images/ep008_front.png) · [wrist](start_images/ep008_wrist.png) |  |
| 009 | P | 24.6 | [front](start_images/ep009_front.png) · [wrist](start_images/ep009_wrist.png) |  |
| 010 | P | 18.3 | [front](start_images/ep010_front.png) · [wrist](start_images/ep010_wrist.png) |  |
