#!/usr/bin/env bash
# rft01 실물 파일럿 진행 게이트 (사용자가 직접 판단해서 실행). 파일만 만든다 — 로봇 · 카메라 연결 없음.
#   gate.sh go  "메모"      시행 1 (Phase 2) 결과를 보고 비정상 Pan · 그리퍼 · 종료 기능 문제가 없을 때 → results/phase2_go.txt (시행 2–8 허용)
#   gate.sh ack <N> "메모"  시행 N 의 안전 개입 · 중단 기록을 확인했고 계속해도 될 때 → results/ack_trialNN.txt
#   gate.sh rest "메모"     직전 run 뒤 팔을 쉬는 자세에 두었음 (safe_home.py 대신 손으로) → results/rest_<run>.txt
#   gate.sh stop "이유"     파일럿 중단 → results/STOP (있으면 run_trial.sh 가 실행하지 않음. 풀려면 파일을 직접 옮긴다)
#   gate.sh status          현재 상태 출력
set -euo pipefail
S=$HOME/so101_runs/main_k8/sgft01_real_eval/results
mkdir -p "$S"
now=$(date '+%Y-%m-%d %H:%M:%S')
case "${1:-status}" in
  go)
    grep -q '^1,' "$S/trials.csv" 2>/dev/null || { echo "⛔ 시행 1 이 results/trials.csv 에 없음 (record_trial.py 먼저)"; exit 2; }
    [ -e "$S/phase2_go.txt" ] && { echo "이미 있음: $(cat "$S/phase2_go.txt")"; exit 0; }
    echo "$now GO ${2:?메모를 주세요}" > "$S/phase2_go.txt"; echo "기록: $S/phase2_go.txt" ;;
  ack)
    N=$(printf %02d "${2:?시행 번호}"); f="$S/ack_trial$N.txt"
    [ -e "$f" ] && { echo "이미 있음: $(cat "$f")"; exit 0; }
    echo "$now ACK ${3:?메모를 주세요}" > "$f"; echo "기록: $f" ;;
  rest)
    # v2: 직전 run 뒤 팔이 쉬는 자세에 있음을 사용자가 직접 확인 (safe_home.py 를 안 썼거나 실패했을 때, 손으로 옮긴 뒤)
    R=$(tail -n +2 "$S/run_ledger.csv" 2>/dev/null | awk -F, '$6!="none"{r=$6} END{print r}')
    [ -n "$R" ] || { echo "run_ledger.csv 에 run 없음"; exit 2; }
    echo "$now REST ${2:?메모를 주세요 (예: 손으로 쉬는 자세에 둠, 토크 꺼짐)}" > "$S/rest_$R.txt"; echo "기록: $S/rest_$R.txt" ;;
  stop)
    echo "$now STOP ${2:?이유를 주세요}" >> "$S/STOP"; echo "기록: $S/STOP" ;;
  status)
    echo "trials.csv: $( [ -f "$S/trials.csv" ] && tail -n +2 "$S/trials.csv" | cut -d, -f1 | sort -n | tr '\n' ' ' || echo 없음)"
    for f in phase2_go.txt STOP; do [ -e "$S/$f" ] && echo "$f: $(cat "$S/$f")" || echo "$f: 없음"; done
    ls "$S"/ack_trial*.txt 2>/dev/null || true ;;
  *) echo "사용: gate.sh go|ack|rest|stop|status"; exit 2 ;;
esac
