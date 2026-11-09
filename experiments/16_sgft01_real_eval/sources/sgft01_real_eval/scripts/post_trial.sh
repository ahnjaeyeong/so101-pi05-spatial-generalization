#!/usr/bin/env bash
# rft01 실물 파일럿 — 시행 뒤 분석 (로봇 · 카메라 연결 없음). 사용자 실행용. 원본 run 폴더에는 diag/ 아래 새 파일만 생긴다 (p00b · p05, 기존 R2 와 같음).
# 사용: ~/so101_runs/main_k8/sgft01_real_eval/scripts/post_trial.sh <run 폴더> [--no-replay]
#   1) p00b_verify_run.py  기록 점검 → <run>/diag/verify.json, 마지막 줄 VERIFY_OK / VERIFY_FAIL
#   2) p05_replay_check.py chunk 재현 + RTC 끔 재구성 (GPU 2–5 분) → <run>/diag/replay/
#   3) r2_analyze.py       T0–T4 · 관절 · 손목 → <세션>/reports/<run>/   (R2 세션 코드 그대로, 출력만 이 세션)
#   4) trial_auto.py       자동 지표 (첫 닫힘 · 빈 닫힘 · Pan 반전 · Wrist 재획득 · 안전 기록) → reports/<run>/trial_auto.{json,md}
set -euo pipefail
[ $# -ge 1 ] || { echo "사용: $0 <run 폴더> [--no-replay]"; exit 2; }
RUN=$(realpath "$1"); NOREPLAY=${2:-}
S=$HOME/so101_runs/main_k8/sgft01_real_eval
PY="$HOME/so101-env/bin/python"
PDS="$HOME/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts"
R2S="$HOME/so101_runs/main_k8/r2_grasp_diagnostic/scripts"
export PYTHONDONTWRITEBYTECODE=1
[ -f "$RUN/diag/chunks.jsonl" ] || { echo "⛔ $RUN/diag/chunks.jsonl 없음 — ROLLOUT_DIAG=1 (run_trial.sh) 로 실행한 폴더가 아님"; exit 2; }
if pgrep -f "eval_ui.py --child|lerobot-rollout|lerobot-record|lerobot-teleoperate" >/dev/null; then
  echo "⛔ 실물 평가 · 녹화 프로세스가 돌고 있어요. 끝난 뒤 다시:"; pgrep -af "eval_ui.py --child|lerobot-rollout|lerobot-record|lerobot-teleoperate" | head -3; exit 2
fi
echo "== 1/4 기록 점검"
"$PY" "$PDS/p00b_verify_run.py" "$RUN" --expect_filter false | tail -25 || echo "(점검 종료 코드 $? — 위 FAIL 줄 확인)"
if [ "$NOREPLAY" != "--no-replay" ]; then
  if [ -f "$RUN/diag/replay/replay.npz" ]; then echo "== 2/4 replay 이미 있음 — 건너뜀"
  else echo "== 2/4 chunk 재현 + RTC 끔 재구성 (GPU)"; nice -n 19 "$PY" "$PDS/p05_replay_check.py" "$RUN/diag" | tail -5; fi
else echo "== 2/4 replay 건너뜀 (--no-replay)"; fi
echo "== 3/4 r2_analyze"
nice -n 19 "$PY" "$R2S/r2_analyze.py" "$RUN" --out-root "$S/reports"
echo "== 4/4 자동 지표"
nice -n 19 "$PY" "$S/scripts/trial_auto.py" "$RUN"
echo
echo "다음: python3 $S/scripts/record_trial.py $RUN"
