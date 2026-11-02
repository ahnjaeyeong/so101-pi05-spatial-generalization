#!/usr/bin/env bash
# A2_s2001: 가중 A2, seed 2001. d2 020000 에서 새 fine-tune (plan_runs.py 가 만듦 — 직접 고치지 말 것).
export PYTHONDONTWRITEBYTECODE=1
export SA_WEIGHTS=/home/user/so101_runs/main_k8/d2/sampling_ablation/weights/weights_A2.npy
export SA_RUN_NAME=A2_s2001
exec $HOME/so101-env/bin/python /home/user/so101_runs/main_k8/d2/sampling_ablation/train_weighted.py \
  --dataset.repo_id=oxr/so101_k8_d2 \
  --dataset.root=/home/user/so101_runs/main_k8/d2/dataset \
  --policy.path=/home/user/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model \
  --policy.push_to_hub=false \
  --policy.dtype=bfloat16 \
  --policy.train_expert_only=true \
  --policy.freeze_vision_encoder=true \
  --policy.gradient_checkpointing=true \
  --policy.optimizer_lr=1e-5 \
  --policy.scheduler_warmup_steps=200 \
  --policy.scheduler_decay_steps=4000 \
  --policy.scheduler_decay_lr=2.5e-6 \
  --output_dir=/home/user/so101_runs/main_k8/d2/sampling_ablation/runs/A2_s2001 \
  --job_name=A2_s2001 \
  --batch_size=32 \
  --steps=4000 \
  --log_freq=50 \
  --save_freq=2000 \
  --num_workers=4 \
  --seed=2001 \
  --wandb.enable=false
