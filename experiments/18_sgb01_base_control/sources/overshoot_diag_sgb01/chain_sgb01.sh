#!/usr/bin/env bash
# sgb01 2단계 체인 (GPU 재추론, 로봇 불필요). 학습 DONE 을 기다린 뒤:
#  1) 복사본으로 sgft01 010000 b10 재현 → s0_repro_check (n39 Cc 바깥 +0.96 [+0.78, +1.14]) 불일치면 멈춤
#  2) sgb01 010000 · 002500 · 005000 · 007500 b10
#  3) sg_offline_eval · sg_vis_eval (sgft_010000 기준 + sgb 4개) → train/sgb01_p3_10k_s2001/eval
# 각 GPU 단계 전: 실평가 (eval_ui · run_series · run_trial) 가 돌면 끝날 때까지 기다림, 다른 학습이 있으면 멈춤. 자동 재시작 없음.
set -u
D=$HOME/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/sgb01
T=$HOME/so101_runs/practice/sg50_pilot3/train/sgb01_p3_10k_s2001
S=$HOME/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001
TOOLS=$HOME/so101_runs/main_k8/r1_r2_collection/tools
PY=$HOME/so101-env/bin/python
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
cd "$D"
say() { echo "$(date '+%F %T') $*" | tee -a chain.log; }
stop() { say "STOP: $*"; echo "$(date '+%F %T') $*" > CHAIN_FAILED; exit 4; }
guard() {
  local n=0
  while ps -eo args | grep -qE '[e]val_ui|[r]un_series\.sh|[r]un_trial\.sh'; do
    [ $n -eq 0 ] && say "실평가 실행 중 — 끝날 때까지 대기"; n=1; sleep 60
  done
  O=$(ps -eo pid,args | grep -E '[l]erobot-train|[t]rain_recovery\.py|[t]rain_weighted\.py')
  [ -n "$O" ] && stop "다른 학습 프로세스: $O"
  return 0
}
say "대기 시작 (pid $$): $T/DONE 또는 FAILED"
while [ ! -e $T/DONE ] && [ ! -e $T/FAILED ]; do sleep 60; done
[ -e $T/FAILED ] && stop "학습 FAILED: $(cat $T/FAILED)"
sleep 120
b10() {  # tag ckpt
  guard; say "b10 $1 시작 ($2)"
  OD_TAG=$1 OD_CK=$2 nice -n 10 $PY scripts/b10_height.py > data/b10_$1.log 2>&1 || stop "b10 $1 rc=$? $(tail -c 300 data/b10_$1.log | tr '\r\n' '  ')"
  say "b10 $1 끝 $(tail -1 data/b10_$1.log)"
}
b10 sgft01_010000 $S/run/checkpoints/010000/pretrained_model
$PY scripts/s0_repro_check.py data/height_sgft01_010000.json > data/repro_check.json 2>&1; RC=$?
say "재현 확인 rc=$RC $(cat data/repro_check.json)"
[ $RC -eq 0 ] || stop "sgft01 010000 재현 불일치 — sgb01 측정 안 함"
for s in 010000 002500 005000 007500; do b10 sgb01_$s $T/run/checkpoints/$s/pretrained_model; done
$PY scripts/s1_open_summary.py sgft01_010000=data/height_sgft01_010000.json sgb01_002500=data/height_sgb01_002500.json \
  sgb01_005000=data/height_sgb01_005000.json sgb01_007500=data/height_sgb01_007500.json sgb01_010000=data/height_sgb01_010000.json \
  --out data/compare.json > data/compare.txt 2>&1 || stop "s1 요약 실패"
say "b10 요약 끝 (data/compare.txt)"
CK=$T/run/checkpoints; SCK=$S/run/checkpoints/010000/pretrained_model
mkdir -p $T/eval
[ -e $T/eval/results.json ] && stop "$T/eval/results.json 이 이미 있음"
guard; say "sg_offline_eval 시작"
nice -n 10 $PY $TOOLS/sg_offline_eval.py --out $T/eval --sets A,B,C --n 8 --ckpt sgft_010000=$SCK \
  --ckpt sgb_002500=$CK/002500/pretrained_model --ckpt sgb_005000=$CK/005000/pretrained_model \
  --ckpt sgb_007500=$CK/007500/pretrained_model --ckpt sgb_010000=$CK/010000/pretrained_model > $T/eval/eval.log 2>&1 \
  || stop "sg_offline_eval rc=$? $(tail -c 300 $T/eval/eval.log | tr '\r\n' '  ')"
say "sg_offline_eval 끝"
guard; say "sg_vis_eval 시작"
nice -n 10 $PY $TOOLS/sg_vis_eval.py --out $T/eval --n 4 --ckpt sgft_010000=$SCK \
  --ckpt sgb_002500=$CK/002500/pretrained_model --ckpt sgb_005000=$CK/005000/pretrained_model \
  --ckpt sgb_007500=$CK/007500/pretrained_model --ckpt sgb_010000=$CK/010000/pretrained_model > $T/eval/vis.log 2>&1 \
  || stop "sg_vis_eval rc=$? $(tail -c 300 $T/eval/vis.log | tr '\r\n' '  ')"
say "sg_vis_eval 끝"
touch CHAIN_DONE
say "CHAIN_DONE"
