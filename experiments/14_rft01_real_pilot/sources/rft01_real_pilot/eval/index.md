# 실물 평가 목록

`eval_ui.py` 가 실행마다 한 줄씩 추가한다. 판별 기준·메모는 각 폴더의 results.md.

| 시각 | 체크포인트 | tag | 저장 | P | F | 성공률 | 폴더 |
|---|---|---|---|---|---|---|---|
| 2026-11-05 11:14 | `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` | t01_ft_k3_0 | 1 | 1 | 0 | 100% | [rollouts/20261105_111427_1k_t01_ft_k3_0](rollouts/20261105_111427_1k_t01_ft_k3_0/results.md) |
| 2026-11-05 13:02 | `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` | t02_bl_k3_0 | 1 | 0 | 1 | 0% | [rollouts/20261105_130203_20k_t02_bl_k3_0](rollouts/20261105_130203_20k_t02_bl_k3_0/results.md) |
| 2026-11-05 13:17 | `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` | t03_bl_k1_0 | 1 | 1 | 0 | 100% | [rollouts/20261105_131723_20k_t03_bl_k1_0](rollouts/20261105_131723_20k_t03_bl_k1_0/results.md) |
| 2026-11-05 13:21 | `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` | t04_ft_k1_0 | 1 | 1 | 0 | 100% | [rollouts/20261105_132118_1k_t04_ft_k1_0](rollouts/20261105_132118_1k_t04_ft_k1_0/results.md) |
| 2026-11-05 13:25 | `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` | t05_ft_k3_r30 | 1 | 1 | 0 | 100% | [rollouts/20261105_132513_1k_t05_ft_k3_r30](rollouts/20261105_132513_1k_t05_ft_k3_r30/results.md) |
| 2026-11-05 13:41 | `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` | t06_07_bl_series | 2 | 1 | 1 | 50% | [rollouts/20261105_134136_20k_t06_07_bl_series](rollouts/20261105_134136_20k_t06_07_bl_series/results.md) |
| 2026-11-05 14:36 | `../d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000` | t08_09_10_11_12_ft_series | 5 | 1 | 4 | 20% | [rollouts/20261105_143609_1k_t08_09_10_11_12_ft_series](rollouts/20261105_143609_1k_t08_09_10_11_12_ft_series/results.md) |
| 2026-11-05 14:46 | `../d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000` | t13_14_15_16_bl_series | 4 | 3 | 1 | 75% | [rollouts/20261105_144650_20k_t13_14_15_16_bl_series](rollouts/20261105_144650_20k_t13_14_15_16_bl_series/results.md) |
