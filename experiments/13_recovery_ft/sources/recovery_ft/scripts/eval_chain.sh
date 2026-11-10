#!/usr/bin/env bash
# 학습 뒤 오프라인 평가 체인 (GPU 재추론 → 지표). 로봇 연결 없음. 실패하면 그 자리에서 멈춘다 (다시 시도 · 설정 변경 없음).
# 학습 run 이 DONE 일 때만 시작. 다른 학습 프로세스가 있으면 시작하지 않는다.
set -u
RF=$HOME/so101_runs/main_k8/d2/recovery_ft
PY=$HOME/so101-env/bin/python
R=rft01_d2rc16_W5_1k_s2001
CK=$RF/runs/$R/checkpoints
D2CK=$HOME/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model
cd "$RF"; mkdir -p logs
LOG=logs/eval_chain.log
say() { echo "$(date '+%F %T') $*" | tee -a $LOG; }
stop() { say "STOP: $*"; touch logs/EVAL_CHAIN_STOPPED; exit 4; }
while [ ! -e runs/$R.DONE ] && [ ! -e runs/$R.FAILED ]; do sleep 60; done
[ -e runs/$R.DONE ] || stop "학습 run FAILED — 평가 안 함"
P=$(PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$HOME/so101_runs/main_k8/d2/sampling_ablation'); import train_weighted as T; print(' '.join(map(str, T.training_processes())))")
[ -n "$P" ] && stop "학습 프로세스 있음: $P"
run() { say "start $*"; PYTHONDONTWRITEBYTECODE=1 nice -n 10 $PY "$@" >> logs/eval_$(echo "$*" | grep -oE -- '--tag [^ ]+' | cut -d' ' -f2).log 2>&1 || stop "실패: $*"; say "done"; }
run scripts/e01_reinfer.py --ckpt $D2CK --tag d2_020000_repro --sets q02,vd_b,vd_h --limit 6
run scripts/e01_reinfer.py --ckpt $D2CK --tag d2_020000_demo --sets demo
PYTHONDONTWRITEBYTECODE=1 $PY scripts/e00_base_from_existing.py --n 32 >> $LOG 2>&1 || stop "e00 실패"
for S in 001000 000500 000250 000750; do
  run scripts/e01_reinfer.py --ckpt $CK/$S/pretrained_model --tag rft01_$S
done
PYTHONDONTWRITEBYTECODE=1 $PY scripts/e02_metrics.py --base d2_020000 --tags rft01_000250,rft01_000500,rft01_000750,rft01_001000 > logs/e02.log 2>&1 || stop "e02 실패"
say "EVAL_CHAIN_DONE"
touch logs/EVAL_CHAIN_DONE
