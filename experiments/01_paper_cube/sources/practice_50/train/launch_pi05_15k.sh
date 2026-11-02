#!/usr/bin/env bash
# run_pi05_15k.sh 를 백그라운드로 돌리고 시작·끝 시각, pid, 메모리(5초마다)를 기록한다.
cd "$(dirname "$0")"
echo "start $(date '+%F %T')" > pi05_15k.time
./run_pi05_15k.sh > pi05_15k.log 2>&1 &
P=$!; echo $P > pi05_15k.pid
while kill -0 $P 2>/dev/null; do
  echo "$(date +%T) used_MiB=$(free -m | awk '/Mem:/{print $3}') rss_MiB=$(ps -o rss= -p $P 2>/dev/null | awk '{s+=$1} END{print int(s/1024)}') gpu=[$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | tr '\n' ' ')]" >> pi05_15k.mem.log
  sleep 5
done
wait $P; RC=$?
echo "end $(date '+%F %T') rc=$RC" >> pi05_15k.time
