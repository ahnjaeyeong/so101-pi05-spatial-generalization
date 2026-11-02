#!/bin/bash
# run_gpu.sh (G1 K 0–31 → G2) 가 끝난 뒤 G1 Random 판 64–95 를 g1b/ 에. 로봇 연결 없음.
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
while pgrep -f run_gpu.sh >/dev/null; do sleep 30; done
echo "g1b start $(date '+%F %T')"
nice -n 19 ~/so101-env/bin/python g1_roll_factorial.py --eps 64-95 --out g1b > g1b.log 2>&1; echo "g1b rc=$? $(date '+%F %T')"
echo "end d4: $(tail -c 300 ~/so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log | grep -o '[0-9]*/20000 [^]]*]' | tail -1)"
