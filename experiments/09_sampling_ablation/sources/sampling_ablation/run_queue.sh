#!/usr/bin/env bash
# d2 sampling ablation 학습 큐 (사용자 10-27): A0 → A1 → A2 → A2r → A0′ 를 차례로. A3 · A3c12 는 넣지 않음.
# 시작 조건: d4 (pid 3000922) 종료 + 다른 학습 프로세스 없음 + GPU compute 프로세스 없음 + check_cpu.py 전부 통과.
# 각 실험 뒤 확인: rc 0, checkpoints/002000 · 004000 의 training_step, last → 004000, 로그에 nan/OOM 없음, d2 파일 sha256 그대로.
#   하나라도 어긋나면 다음 실험으로 넘어가지 않고 멈춘다 (runs/QUEUE_STOPPED). SIGKILL · 삭제 · 덮어쓰기 없음.
# 실험 사이에 eval_hook.sh 가 있으면 실행한다 (실패해도 학습 큐는 계속, 기록만).
set -u
SA=$HOME/so101_runs/main_k8/d2/sampling_ablation
PY=$HOME/so101-env/bin/python
cd "$SA"
mkdir -p runs
LOG=runs/queue.log
RUNS=(A0_s2001 A1_s2001 A2_s2001 A2r_s2001 A0_s2002)
say() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
stop() { say "STOP: $*"; echo "$(date '+%F %T') $*" > runs/QUEUE_STOPPED; exit 4; }

say "queue start (pid $$), runs: ${RUNS[*]}"
while kill -0 3000922 2>/dev/null; do sleep 60; done
say "d4 pid 3000922 gone"
for i in $(seq 30); do
  P=$(PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$SA'); import train_weighted as T; print(' '.join(map(str, T.training_processes())))")
  G=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | tr -d ' ' | tr '\n' ' ')
  [ -z "$P" ] && [ -z "${G// /}" ] && break
  say "waiting: training procs [$P] gpu compute [$G]"; sleep 60
done
[ -n "$P" ] && stop "다른 학습 프로세스가 남아 있음: $P"
[ -n "${G// /}" ] && stop "GPU compute 프로세스가 남아 있음: $G"
say "GPU free: $(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader 2>/dev/null) / free -m used $(free -m | awk '/Mem:/{print $3}') MiB"

CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 nice -n 10 $PY check_cpu.py > runs/check_cpu_prestart.log 2>&1 || stop "check_cpu.py 실패 (runs/check_cpu_prestart.log)"
say "check_cpu.py ALL PASS"

for R in "${RUNS[@]}"; do
  [ -e "runs/$R" ] && stop "runs/$R 가 이미 있음 (덮어쓰지 않음)"
  [ -x "runs/run_$R.sh" ] || stop "runs/run_$R.sh 없음"
  say "== $R start"
  echo "start $(date '+%F %T')" > "runs/$R.time"
  "runs/run_$R.sh" > "runs/$R.log" 2>&1 &
  P=$!; echo $P > "runs/$R.pid"
  while kill -0 $P 2>/dev/null; do
    echo "$(date +%T) used_MiB=$(free -m | awk '/Mem:/{print $3}') avail_MiB=$(free -m | awk '/Mem:/{print $7}') gpu=[$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | tr '\n' ' ')]" >> "runs/$R.mem.log"
    sleep 30
  done
  wait $P; RC=$?
  echo "end $(date '+%F %T') rc=$RC" >> "runs/$R.time"
  say "== $R end rc=$RC"
  [ $RC -eq 0 ] || stop "$R rc=$RC (runs/$R.log 끝: $(tail -c 300 runs/$R.log | tr '\r\n' '  '))"
  grep -qiE "out of memory|CUDA error|Traceback" "runs/$R.log" && stop "$R 로그에 OOM/CUDA error/Traceback"
  for S in 002000 004000; do
    J=runs/$R/checkpoints/$S/training_state/training_step.json
    [ -f "$J" ] || stop "$R checkpoint $S 없음"
    [ "$(PYTHONDONTWRITEBYTECODE=1 $PY -c "import json;print(json.load(open('$J'))['step'])")" = "$((10#$S))" ] || stop "$R $S step 불일치"
    [ -f "runs/$R/checkpoints/$S/pretrained_model/model.safetensors" ] || stop "$R $S model.safetensors 없음"
  done
  [ "$(readlink runs/$R/checkpoints/last)" = "004000" ] || stop "$R last 링크가 004000 아님"
  L=$(tr '\r' '\n' < "runs/$R.log" | grep -oE "loss:[0-9.na-]+" | tail -1)
  echo "$L" | grep -qi nan && stop "$R loss nan"
  grep -q "weighted list" "runs/$R.log" || stop "$R 가중 sampler 사용 흔적 없음"
  PYTHONDONTWRITEBYTECODE=1 $PY -c "import sys; sys.path.insert(0,'$SA'); import train_weighted as T; b=T.verify_hashes(full=True); print(b); sys.exit(1 if b else 0)" >> "$LOG" 2>&1 \
    || stop "d2 체크포인트/데이터셋 sha256 변화 감지"
  say "$R checks OK (last $L, $(grep -o 'weighted list [0-9]*' runs/$R.log | head -1))"
  if [ -x eval_hook.sh ]; then
    say "eval_hook $R start"
    ./eval_hook.sh "$R" >> "runs/eval_hook_$R.log" 2>&1 && say "eval_hook $R OK" || say "eval_hook $R FAILED (학습 큐는 계속)"
  fi
done
say "queue DONE: ${RUNS[*]}"
touch runs/QUEUE_DONE
