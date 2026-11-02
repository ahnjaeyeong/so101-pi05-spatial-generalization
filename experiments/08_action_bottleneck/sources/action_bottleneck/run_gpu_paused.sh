#!/bin/bash
# 사용자 10-27 14:0x "D4 학습을 일단 멈추고 진행해": d4 (pid 3000922 + 자식) SIGSTOP → G1 ep 32–127 (g1c/) → G2 → SIGCONT.
# 실패해도 끝에서 반드시 SIGCONT (trap). 로봇 연결 없음.
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
NOTE=~/so101_runs/main_k8/d4/train/32_20000/PAUSE_NOTE_F1.txt
PIDS="3000922 $(pgrep -P 3000922 | tr '\n' ' ')"
resume() { kill -CONT $PIDS; echo "resumed $(date '+%F %T')" >> $NOTE; echo "d4 resumed $(date '+%F %T')"; }
trap resume EXIT
STEP=$(tail -c 400 ~/so101_runs/main_k8/d4/train/32_20000/pi05_expert_bs32_20k.log | grep -o '[0-9]*/20000' | tail -1)
kill -STOP $PIDS
echo "paused $(date '+%F %T') at $STEP pids=$PIDS (action_bottleneck G1/G2)" >> $NOTE
echo "d4 paused $(date '+%F %T') at $STEP"
nice -n 19 ~/so101-env/bin/python g1_roll_factorial.py --eps 32-127 --out g1c --d4_ratio inf > g1c.log 2>&1; echo "g1c rc=$? $(date '+%F %T')"
nice -n 19 ~/so101-env/bin/python g2_policy_frames.py --d4_ratio inf > g2.log 2>&1; echo "g2 rc=$? $(date '+%F %T')"
