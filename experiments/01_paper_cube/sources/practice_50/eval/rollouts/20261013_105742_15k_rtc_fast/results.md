# 평가 20261013_105742_15k_rtc_fast

- 세션: `practice/practice_50` · 체크포인트: `train/pi05_15k/checkpoints/015000` · tag `rtc_fast`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.queue_threshold=40`
- 시작: 2026-10-13 10:57 · 끝: 2026-10-13 11:08
- 결과: 저장 8판 · **P 3 / F 5** · 성공률 38%
- 8° 제한 경고: 549회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | P | 21.8 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
| 001 | F | 29.0 | [front](start_images/ep001_front.png) · [wrist](start_images/ep001_wrist.png) |  |
| 002 | P | 18.4 | [front](start_images/ep002_front.png) · [wrist](start_images/ep002_wrist.png) |  |
| 003 | P | 22.5 | [front](start_images/ep003_front.png) · [wrist](start_images/ep003_wrist.png) |  |
| 004 | F | 14.0 | [front](start_images/ep004_front.png) · [wrist](start_images/ep004_wrist.png) |  |
| 005 | F | 30.4 | [front](start_images/ep005_front.png) · [wrist](start_images/ep005_wrist.png) |  |
| 006 | F | 31.8 | [front](start_images/ep006_front.png) · [wrist](start_images/ep006_wrist.png) |  |
| 007 | F | 26.5 | [front](start_images/ep007_front.png) · [wrist](start_images/ep007_wrist.png) |  |
