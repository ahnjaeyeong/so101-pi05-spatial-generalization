#!/usr/bin/env bash
# runs/queue.log 에 새 줄이 생길 때까지 기다렸다가 새 줄을 출력하고 끝난다 (Claude 알림용, 읽기만).
Q=$HOME/so101_runs/main_k8/d2/sampling_ablation/runs/queue.log
N=${1:-$(wc -l < "$Q")}
while [ "$(wc -l < "$Q")" -le "$N" ]; do
  pgrep -f "run_queue.sh" > /dev/null || { echo "run_queue.sh not running"; tail -3 "$Q"; exit 1; }
  sleep 60
done
tail -n +$((N + 1)) "$Q"
