#!/usr/bin/env bash
# run_queue.sh 가 실험 하나가 끝나고 검사를 통과한 뒤 부른다: $1 = 실험 이름 (예 A0_s2001). 학습 사이에만 GPU 를 쓴다.
#   1) d2 020000 기준선이 아직 없으면 먼저 (전 단계, 처음 한 번)
#   2) <실험> 004000 전 단계 (o3 · o1 · g1 · g2) — 최종 비교용
#   3) <실험> 002000 o3 · o1 — 안정성 점검용 (판정에 쓰지 않음)
#   4) report.py 로 결과표 갱신
# 실패하면 0 이 아닌 값으로 끝난다 (run_queue.sh 는 기록만 하고 학습 큐는 계속).
set -u
SA=$HOME/so101_runs/main_k8/d2/sampling_ablation
PY=$HOME/so101-env/bin/python
cd "$SA"
mkdir -p eval
R=$1
export PYTHONDONTWRITEBYTECODE=1
if [ ! -f eval/d2_020000/DONE ]; then
  echo "$(date '+%F %T') d2 baseline"
  $PY eval_run.py --run d2 > eval/d2_020000.log 2>&1 || { echo "d2 baseline failed"; exit 1; }
fi
echo "$(date '+%F %T') $R 004000"
$PY eval_run.py --run "$R" --step 004000 > "eval/${R}_004000.log" 2>&1 || { echo "$R 004000 failed"; exit 1; }
echo "$(date '+%F %T') $R 002000 (o3, o1)"
$PY eval_run.py --run "$R" --step 002000 --stages o3,o1 > "eval/${R}_002000.log" 2>&1 || { echo "$R 002000 failed"; exit 1; }
$PY report.py > eval/report.log 2>&1 || echo "report.py failed (결과표 갱신 안 됨)"
echo "$(date '+%F %T') done $R"
