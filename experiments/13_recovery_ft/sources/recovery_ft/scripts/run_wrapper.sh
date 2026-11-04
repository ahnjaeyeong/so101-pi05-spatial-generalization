#!/usr/bin/env bash
# 정식 run 1 개 실행 + 감시 + 사후 점검 (자동 재시작 · 설정 변경 · SIGKILL · 삭제 없음).
# 사용: setsid nohup scripts/run_wrapper.sh <RUN_ID> > runs/<RUN_ID>.wrapper.log 2>&1 &
set -u
RF=$HOME/so101_runs/main_k8/d2/recovery_ft
PY=$HOME/so101-env/bin/python
R=$1
cd "$RF"
say() { echo "$(date '+%F %T') $*" | tee -a runs/$R.status.log; }
fail() { say "FAILED: $*"; echo "$(date '+%F %T') $*" > runs/$R.FAILED; exit 4; }
[ -e "runs/$R" ] && fail "runs/$R 가 이미 있음 (덮어쓰지 않음)"
P=$(PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$HOME/so101_runs/main_k8/d2/sampling_ablation'); import train_weighted as T; print(' '.join(map(str, T.training_processes())))")
G=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | tr -d ' ' | tr '\n' ' ')
[ -n "$P" ] && fail "다른 학습 프로세스: $P"
[ -n "${G// /}" ] && fail "GPU compute 프로세스: $G"
say "start $R (wrapper pid $$)"
echo "start $(date '+%F %T')" > runs/$R.time
runs/run_$R.sh > runs/$R.log 2>&1 &
TP=$!; echo $TP > runs/$R.pid
while kill -0 $TP 2>/dev/null; do
  echo "$(date +%T) used_MiB=$(free -m | awk '/Mem:/{print $3}') avail_MiB=$(free -m | awk '/Mem:/{print $7}') gpu=[$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | tr '\n' ' ')]" >> runs/$R.mem.log
  sleep 30
done
wait $TP; RC=$?
echo "end $(date '+%F %T') rc=$RC" >> runs/$R.time
say "train exit rc=$RC"
[ $RC -eq 0 ] || fail "rc=$RC (log 끝: $(tail -c 400 runs/$R.log | tr '\r\n' '  '))"
grep -qiE "out of memory|CUDA error|Traceback" runs/$R.log && fail "로그에 OOM/CUDA error/Traceback"
for S in 000250 000500 000750 001000; do
  J=runs/$R/checkpoints/$S/training_state/training_step.json
  [ -f "$J" ] || fail "checkpoint $S 없음"
  [ "$(PYTHONDONTWRITEBYTECODE=1 $PY -c "import json;print(json.load(open('$J'))['step'])")" = "$((10#$S))" ] || fail "$S step 불일치"
  [ -f "runs/$R/checkpoints/$S/pretrained_model/model.safetensors" ] || fail "$S model.safetensors 없음"
done
[ "$(readlink runs/$R/checkpoints/last)" = "001000" ] || fail "last 링크가 001000 아님"
L=$(tr '\r' '\n' < runs/$R.log | grep -oE "loss:[0-9.na-]+" | tail -1)
echo "$L" | grep -qi nan && fail "loss nan"
grep -q "weighted list" runs/$R.log || fail "가중 sampler 흔적 없음"
[ -f runs/$R.sampled_abs_idx.npy ] || fail "표본 index 기록 없음"
PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$HOME/so101_runs/main_k8/d2/sampling_ablation'); import train_weighted as T; b=T.verify_hashes(full=True); print('d2 hash diff', b); sys.exit(1 if b else 0)" >> runs/$R.status.log 2>&1 || fail "d2 020000/dataset sha256 변화"
PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$RF/scripts'); import train_recovery as T; b=T.verify_dataset_hashes(); print('merged dataset hash diff', b); sys.exit(1 if b else 0)" >> runs/$R.status.log 2>&1 || fail "병합 사본 sha256 변화"
say "checks OK (last $L)"
touch runs/$R.DONE
