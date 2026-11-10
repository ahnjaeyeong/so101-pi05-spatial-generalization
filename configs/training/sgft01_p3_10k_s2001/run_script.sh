#!/usr/bin/env bash
# sgft01_p3_10k_s2001: d2 020000 → 예비3 (practice/sg50_pilot3) ep3–42 fine-tune. rft01 과 같은 값, steps 10000 · decay 10000 · save 2500 (사용자 2026-11-06).
# 자동 재시작 · 설정 변경 · 삭제 없음. lerobot-train 으로 실행 (io-watch 가 'bin/lerobot-train' 으로 자동 기록).
set -u
T=$HOME/so101_runs/practice/sg50_pilot3/train/sgft01_p3_10k_s2001
cd "$T"
say() { echo "$(date '+%F %T') $*" | tee -a status.log; }
fail() { say "FAILED: $*"; echo "$(date '+%F %T') $*" > FAILED; exit 4; }
[ -e run ] && fail "run/ 이 이미 있음 (덮어쓰지 않음)"
O=$(pgrep -af 'lerobot-train|train_recovery.py|train_weighted.py|lerobot_train' | grep -v pgrep | grep -v run_wrapper)
G=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | tr -d ' ' | tr '\n' ' ')
[ -n "$O" ] && fail "다른 학습 프로세스: $O"
[ -n "${G// /}" ] && fail "GPU compute 프로세스: $G"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
mapfile -t ARGS < args.txt
say "start (wrapper pid $$)"
echo "start $(date '+%F %T')" > time.txt
$HOME/so101-env/bin/lerobot-train "${ARGS[@]}" > train.log 2>&1 &
TP=$!; echo $TP > train.pid
while kill -0 $TP 2>/dev/null; do
  echo "$(date +%T) used_MiB=$(free -m | awk '/Mem:/{print $3}') avail_MiB=$(free -m | awk '/Mem:/{print $7}') disk_free=$(df -BG --output=avail $HOME | tail -1 | tr -d ' ')" >> mem.log
  sleep 30
done
wait $TP; RC=$?
echo "end $(date '+%F %T') rc=$RC" >> time.txt
say "train exit rc=$RC"
[ $RC -eq 0 ] || fail "rc=$RC (log 끝: $(tail -c 400 train.log | tr '\r\n' '  '))"
grep -qiE "out of memory|CUDA error|Traceback" train.log && fail "로그에 OOM/CUDA error/Traceback"
for S in 002500 005000 007500 010000; do
  J=run/checkpoints/$S/training_state/training_step.json
  [ -f "$J" ] || fail "checkpoint $S 없음"
  [ "$($HOME/so101-env/bin/python -c "import json;print(json.load(open('$J'))['step'])")" = "$((10#$S))" ] || fail "$S step 불일치"
  [ -f "run/checkpoints/$S/pretrained_model/model.safetensors" ] || fail "$S model.safetensors 없음"
done
L=$(tr '\r' '\n' < train.log | grep -oE "loss:[0-9.na-]+" | tail -1)
echo "$L" | grep -qi nan && fail "loss nan"
say "DONE 마지막 $L"
touch DONE
