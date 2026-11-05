#!/usr/bin/env bash
# rft01_d2rc16_W5_1k_s2001: d2 020000 → d2 256 + R1 4 + R2(RC) 12 신규 fine-tune (make_run.py 가 만듦 — 직접 고치지 말 것)
export PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1
export RF_WEIGHTS=/home/user/so101_runs/main_k8/d2/recovery_ft/weights/weights_rc16_W5.npy
export RF_RUN_NAME=rft01_d2rc16_W5_1k_s2001
mapfile -t ARGS < /home/user/so101_runs/main_k8/d2/recovery_ft/runs/rft01_d2rc16_W5_1k_s2001.args
exec $HOME/so101-env/bin/python /home/user/so101_runs/main_k8/d2/recovery_ft/scripts/train_recovery.py "${ARGS[@]}"
