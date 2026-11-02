#!/usr/bin/env bash
# pi05_expert_bs32_20k 의 020000 체크포인트에서 이어서 30000 스텝까지 추가학습 (가중치·옵티마이저·RNG·데이터 순서 그대로).
# LR: 원래 스케줄(20000 에 맞춰 압축된 cosine)을 그대로 이어가도록 num_decay_steps=20000 → 20k 이후 2.5e-6 고정.
#     (이 옵션 없이 --steps=30000 만 주면 스케줄이 30000 기준으로 다시 계산돼 LR 이 8.1e-6 으로 올라감)
# 체크포인트는 같은 폴더에 025000, 030000 으로 추가 저장. 허브 업로드 없음.
export PYTHONDONTWRITEBYTECODE=1
C=$HOME/so101_runs/main/redbox_all/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model/train_config.json
exec $HOME/so101-env/bin/lerobot-train \
  --config_path=$C \
  --resume=true \
  --steps=30000 \
  --scheduler.num_decay_steps=20000
