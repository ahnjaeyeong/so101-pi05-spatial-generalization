#!/usr/bin/env bash
# d4 학습을 010000 체크포인트 저장이 끝난 뒤 정상 종료한다 (사용자 10-27: 우선순위 변경, d4 종료).
# 규칙: SIGKILL 금지. 체크포인트 · 로그는 건드리지 않음. last -> 010000 이고 로그가 10001 step 이상을 찍은 뒤 SIGINT,
#       120 s 안에 안 끝나면 SIGTERM, 다시 120 s 안에 안 끝나면 그대로 두고 보고만 한다.
PID=3000922
D=$HOME/so101_runs/main_k8/d4/train/32_20000
CK=$D/pi05_expert_bs32_20k/checkpoints
LOG=$D/pi05_expert_bs32_20k.log
NOTE=$D/STOP_NOTE_sampling_ablation.txt
say() { echo "$(date '+%F %T') $*"; }
step() { tail -c 400 "$LOG" | tr '\r' '\n' | grep -oE '\| *[0-9]+/20000' | tail -1 | grep -oE '[0-9]+' | head -1; }
say "watch start pid=$PID step=$(step) last=$(readlink $CK/last)"
while kill -0 $PID 2>/dev/null; do
  if [ "$(readlink $CK/last)" = "010000" ] && [ -f $CK/010000/training_state/training_step.json ] && [ "$(step)" -ge 10002 ] 2>/dev/null; then
    break
  fi
  sleep 30
done
if ! kill -0 $PID 2>/dev/null; then say "d4 already exited (step $(step)); nothing sent"; exit 2; fi
say "010000 saved: $(du -sb $CK/010000 | cut -f1) bytes; step now $(step) → SIGINT"
echo "$(date '+%F %T') d4 정상 종료 요청 (SIGINT) — 010000 저장 확인 뒤, step $(step). 이유: 사용자 10-27 우선순위 변경 (d2 sampling_ablation A0–A2r 먼저). 체크포인트 · 로그 수정 없음." >> $NOTE
kill -INT $PID
for i in $(seq 120); do kill -0 $PID 2>/dev/null || break; sleep 1; done
if kill -0 $PID 2>/dev/null; then
  say "still alive after SIGINT 120 s → SIGTERM"; kill -TERM $PID
  for i in $(seq 120); do kill -0 $PID 2>/dev/null || break; sleep 1; done
fi
if kill -0 $PID 2>/dev/null; then say "STILL ALIVE — no SIGKILL by rule; manual decision needed"; exit 3; fi
sleep 5
say "d4 exited. children: $(pgrep -P $PID | wc -l); launcher time file: $(cat $D/pi05_expert_bs32_20k.time | tr '\n' ' ')"
say "gpu apps: $(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr '\n' ' ')"
echo "$(date '+%F %T') d4 종료 확인." >> $NOTE
