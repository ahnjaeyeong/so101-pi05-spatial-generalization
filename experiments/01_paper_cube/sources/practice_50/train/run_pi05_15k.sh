#!/usr/bin/env bash
# practice_50 π0.5 학습 (50편 전체, 15000 스텝, 5000 스텝마다 저장). 허브 업로드 없음.
export PYTHONDONTWRITEBYTECODE=1
exec $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubebox_practice50 \
  --dataset.root=$HOME/so101_runs/practice/practice_50/dataset \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/practice/practice_50/train/pi05_15k \
  --job_name=pi05_15k \
  --batch_size=4 \
  --steps=15000 \
  --log_freq=50 \
  --save_freq=5000 \
  --num_workers=4 \
  --wandb.enable=false
