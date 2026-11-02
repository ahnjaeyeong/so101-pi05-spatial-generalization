#!/usr/bin/env bash
# redbox_all (redbox_t1~t3 × known/random 6개 합침, 384편) π0.5 학습 — action expert 만 학습 (PaliGemma·비전 인코더 동결), 배치 32, 20000 스텝, 5000 스텝마다 저장.
# 나머지는 cubemark_v1 pi05_expert_bs8_3k 와 같음. 허브 업로드 없음.
export PYTHONDONTWRITEBYTECODE=1
exec $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_redbox_all \
  --dataset.root=$HOME/so101_runs/main/redbox_all/dataset \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.train_expert_only=true \
  --policy.freeze_vision_encoder=true \
  --policy.gradient_checkpointing=true \
  --policy.optimizer_lr=2.5e-5 \
  --output_dir=$HOME/so101_runs/main/redbox_all/train/32_20000/pi05_expert_bs32_20k \
  --job_name=pi05_expert_bs32_20k \
  --batch_size=32 \
  --steps=20000 \
  --log_freq=50 \
  --save_freq=5000 \
  --num_workers=4 \
  --wandb.enable=false
