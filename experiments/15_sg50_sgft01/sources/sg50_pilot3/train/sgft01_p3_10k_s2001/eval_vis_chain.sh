#!/usr/bin/env bash
# 첫 오프라인 테스트 (eval_chain.sh → eval/EVAL_DONE 또는 EVAL_FAILED) 가 끝나면 시각 의존 시험 (tools/sg_vis_eval.py) 을 이어서 돌린다.
# 학습이 FAILED 면 돌리지 않음. (2026-11-06 사용자 중점: front→숄더팬, 손목→다시 맞추기, 주황 프레임 맞으면 닫기)
set -u
T=$HOME/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001
TOOLS=$HOME/so101_runs/main_k8/r1_r2_collection/tools
cd "$T"
say() { echo "$(date '+%F %T') $*" | tee -a eval/vis_chain.log; }
say "대기 시작 (pid $$): eval/EVAL_DONE 또는 EVAL_FAILED (학습 FAILED 면 끝)"
while [ ! -e eval/EVAL_DONE ] && [ ! -e eval/EVAL_FAILED ]; do
  [ -e FAILED ] && { say "학습 FAILED — 시각 시험 안 함"; exit 3; }
  sleep 60
done
O=$(pgrep -af 'lerobot-train|train_recovery.py|train_weighted.py|sg_offline_eval.py' | grep -v pgrep)
[ -n "$O" ] && { say "다른 GPU 작업이 있어 멈춤: $O"; exit 4; }
CK=$T/run/checkpoints
D2CK=$HOME/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model
say "시각 시험 시작"
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 $HOME/so101-env/bin/python $TOOLS/sg_vis_eval.py --out $T/eval --n 4 \
  --ckpt d2_020000=$D2CK --ckpt sgft_002500=$CK/002500/pretrained_model --ckpt sgft_005000=$CK/005000/pretrained_model \
  --ckpt sgft_007500=$CK/007500/pretrained_model --ckpt sgft_010000=$CK/010000/pretrained_model > eval/vis.log 2>&1
RC=$?
say "시각 시험 끝 rc=$RC"
[ $RC -eq 0 ] && touch eval/VIS_DONE || echo "rc=$RC $(tail -c 400 eval/vis.log | tr '\r\n' '  ')" > eval/VIS_FAILED
