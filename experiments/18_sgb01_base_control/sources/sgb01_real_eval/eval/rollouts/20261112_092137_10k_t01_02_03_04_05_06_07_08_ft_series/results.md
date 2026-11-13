# 평가 20261112_092137_10k_t01_02_03_04_05_06_07_08_ft_series

- 세션: `main_k8/sgb01_real_eval` · 체크포인트: `../../practice/sg50_pilot3/train/sgb01_p3_10k_s2001/run/checkpoints/010000` · tag `t01_02_03_04_05_06_07_08_ft_series`
- 과제: "pick up the red cube and put it in the brown box"
- 추론: `--policy.num_inference_steps=5 --inference.type=rtc --inference.rtc.execution_horizon=20 --inference.rtc.prefix_attention_schedule=EXP --inference.queue_threshold=30 --arm_filter=false --rollout_guard=warn`
- 시작: 2026-11-12 09:21 · 끝: 2026-11-12 09:31
- 결과: 저장 1판 · **P 0 / F 0** · 성공률 0% · 미판정 1
- 8° 제한 경고: 0회 (debug.log)

| ep | 판정 | 길이(s) | 시작 사진 | 메모 |
|---|---|---|---|---|
| 000 | — | 9.9 | [front](start_images/ep000_front.png) · [wrist](start_images/ep000_wrist.png) |  |
