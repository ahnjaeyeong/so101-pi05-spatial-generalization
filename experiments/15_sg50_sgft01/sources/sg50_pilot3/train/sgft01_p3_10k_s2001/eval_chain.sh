#!/usr/bin/env bash
# 학습 (run_wrapper.sh) 이 DONE 을 남기면 오프라인 테스트 (tools/sg_offline_eval.py) 를 이어서 돌린다. FAILED 면 돌리지 않음.
set -u
T=$HOME/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001
TOOLS=$HOME/so101_runs/main_k8/r1_r2_collection/tools
cd "$T"
say() { echo "$(date '+%F %T') $*" | tee -a eval/chain.log; }
say "대기 시작 (pid $$): DONE 또는 FAILED 를 기다림"
while [ ! -e DONE ] && [ ! -e FAILED ]; do sleep 60; done
if [ -e FAILED ]; then say "학습 FAILED — 오프라인 테스트 안 함: $(cat FAILED)"; exit 3; fi
sleep 120  # 마지막 체크포인트 디스크 기록 (io-watch 꼬리 기록) 뒤
O=$(pgrep -af 'lerobot-train|train_recovery.py|train_weighted.py' | grep -v pgrep)
[ -n "$O" ] && { say "다른 학습 프로세스가 있어 멈춤: $O"; exit 4; }
CK=$T/run/checkpoints
D2CK=$HOME/so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model
say "오프라인 테스트 시작"
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 nice -n 10 $HOME/so101-env/bin/python $TOOLS/sg_offline_eval.py --out $T/eval --sets A,B,C --n 8 \
  --ckpt d2_020000=$D2CK --ckpt sgft_002500=$CK/002500/pretrained_model --ckpt sgft_005000=$CK/005000/pretrained_model \
  --ckpt sgft_007500=$CK/007500/pretrained_model --ckpt sgft_010000=$CK/010000/pretrained_model > eval/eval.log 2>&1
RC=$?
say "오프라인 테스트 끝 rc=$RC"
[ $RC -eq 0 ] && touch eval/EVAL_DONE || echo "rc=$RC $(tail -c 400 eval/eval.log | tr '\r\n' '  ')" > eval/EVAL_FAILED
