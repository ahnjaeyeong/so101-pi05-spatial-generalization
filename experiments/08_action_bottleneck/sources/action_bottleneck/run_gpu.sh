#!/bin/bash
# G1 → G2 순서로 GPU 실행 (d4 와 동시, watchdog: MemAvailable ≥ 25 GB, d4 > 2× 느리면 대기). 로봇 연결 없음.
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
PY=~/so101-env/bin/python
echo "start $(date '+%F %T') d4: $(tail -c 300 ~/so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log | grep -o '[0-9]*/20000 [^]]*]' | tail -1)"
nice -n 19 $PY g1_roll_factorial.py > g1.log 2>&1; echo "g1 rc=$? $(date '+%F %T')"
nice -n 19 $PY g2_policy_frames.py > g2.log 2>&1; echo "g2 rc=$? $(date '+%F %T')"
echo "end d4: $(tail -c 300 ~/so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log | grep -o '[0-9]*/20000 [^]]*]' | tail -1)"
