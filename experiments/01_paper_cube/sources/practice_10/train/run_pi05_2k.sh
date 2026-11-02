#!/usr/bin/env bash
# practice_10 π0.5 연습 학습 (동작 확인용). 허브 업로드 없음.
export PYTHONDONTWRITEBYTECODE=1
exec $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubebox_practice10 \
  --dataset.root=$HOME/so101_runs/practice/practice_10/dataset \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --output_dir=$HOME/so101_runs/practice/practice_10/train/pi05_2k \
  --job_name=pi05_2k \
  --batch_size=4 \
  --steps=2000 \
  --log_freq=50 \
  --save_freq=2000 \
  --num_workers=4 \
  --wandb.enable=false
