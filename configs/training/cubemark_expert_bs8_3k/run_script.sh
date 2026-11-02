#!/usr/bin/env bash
# cubemark_v1 π0.5 학습 2 — action expert 만 학습 (PaliGemma·비전 인코더 동결), 배치 8, 3000 스텝, 1000 스텝마다 저장.
# 나머지는 pi05_15k 와 같음. 허브 업로드 없음. 결과는 train/8_3000/pi05_expert_bs8_3k/ (4_15000 은 그대로 둠).
export PYTHONDONTWRITEBYTECODE=1
exec $HOME/so101-env/bin/lerobot-train \
  --dataset.repo_id=oxr/so101_cubemark_v1 \
  --dataset.root=$HOME/so101_runs/main/cubemark_v1/dataset \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.train_expert_only=true \
  --policy.freeze_vision_encoder=true \
  --policy.gradient_checkpointing=true \
  --policy.optimizer_lr=2.5e-5 \
  --output_dir=$HOME/so101_runs/main/cubemark_v1/train/8_3000/pi05_expert_bs8_3k \
  --job_name=pi05_expert_bs8_3k \
  --batch_size=8 \
  --steps=3000 \
  --log_freq=50 \
  --save_freq=1000 \
  --num_workers=4 \
  --wandb.enable=false
