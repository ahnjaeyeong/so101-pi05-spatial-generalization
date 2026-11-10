#!/usr/bin/env bash
# sgft01 계획 (8 판 · ft 만 · 1 번부터) 으로 run_series.sh 시험 (로봇 · 카메라 · GPU 없음). 임시 폴더 + 가짜 run_trial / safe_home.
# 가짜 run_trial 도 게이트는 진짜 run_trial.sh (PILOT_DIR + GATE_ONLY=1 + BATCH=1 + SERIES_*) 를 쓴다. PASS/FAIL 줄, 마지막 ALL_PASS / SOME_FAIL.
# 세션 k 번째의 결과는 SESS<k>="ended=<ended_by> saved=<판 수|all> diff=<°>" 로 정한다 (기본 정상 · 전부 저장 · 1°).
set -u
S=$HOME/so101_runs/main_k8/sgft01_real_eval
T=$(mktemp -d /tmp/claude-2001/-home-user/440db4fb-0474-4b93-bd85-3fc6175c60a4/scratchpad/series_XXXX 2>/dev/null || mktemp -d)
trap 'rm -rf "$T"' EXIT
ok=1
chk() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1 ${3:-}"; ok=0; fi; }

mkdir -p "$T/stub"
cat > "$T/stub/rt.sh" <<'EOF'
#!/usr/bin/env bash
N=$1
G=$(env PILOT_DIR="$PILOT_DIR" GATE_ONLY=1 BATCH="${BATCH:-0}" SERIES_TRIALS="${SERIES_TRIALS:-}" SERIES_PLAN="${SERIES_PLAN:-}" "$REAL_RT" "$N" 2>&1)
echo "$G"
[[ "$G" == *"게이트: OK"* ]] || { echo "GATEBLOCK $N" >> "$PILOT_DIR/calls.log"; exit 0; }
K=$(( $(grep -c '^RT' "$PILOT_DIR/calls.log") + 1 ))
echo "RT $K trials=[$SERIES_TRIALS] plan=$(tail -n +2 "$SERIES_PLAN" | cut -d, -f16 | tr '\n' ' ')" >> "$PILOT_DIR/calls.log"
V=SESS$K; CFG=${!V:-}
BY=$(echo "$CFG" | grep -o 'ended=[^ ]*' | cut -d= -f2); BY=${BY:-episode_end_or_user_next}
SV=$(echo "$CFG" | grep -o 'saved=[^ ]*' | cut -d= -f2); NT=$(echo $SERIES_TRIALS | wc -w); [ -z "$SV" ] || [ "$SV" = all ] && SV=$NT
D=$(echo "$CFG" | grep -o 'diff=[^ ]*' | cut -d= -f2); D=${D:-1.0}
RUN=20261105_15000${K}_1k_series$K
mkdir -p "$PILOT_DIR/eval/rollouts/$RUN"
echo "{\"ended_by\":\"$BY\",\"max_abs_diff_deg\":$D,\"torque_left_on\":true}" > "$PILOT_DIR/eval/rollouts/$RUN/end_state.json"
LT=$(echo $SERIES_TRIALS | cut -d' ' -f1-$((SV > 0 ? SV : 1))); [ "$SV" -gt 0 ] || LT=0
for t in $LT; do echo "$t,x,x,x,tag,$RUN,a,b,0,\"\",m.json" >> "$PILOT_DIR/results/run_ledger.csv"; done
EOF
cat > "$T/stub/sh.py" <<'EOF'
import json, os, sys
a = sys.argv; run = os.path.basename(a[a.index("--run") + 1]); P = os.environ["PILOT_DIR"]
okm = run not in os.environ.get("HOME_FAIL", "").split()
os.makedirs(f"{P}/results/home_logs", exist_ok=True)
json.dump({"move": {"ok": okm}}, open(f"{P}/results/home_logs/{run}_{len(os.listdir(P + '/results/home_logs'))}.json", "w"))
open(f"{P}/calls.log", "a").write(f"SH {run} {'auto' if '--auto' in a else 'manual'} {'ok' if okm else 'fail'}\n")
sys.exit(0 if okm else 3)
EOF
chmod +x "$T/stub/"*

setup() {  # 새 세션: 실행 기록 없음
  P=$T/p_$1; rm -rf "$P"; mkdir -p "$P/results" "$P/logs" "$P/eval/rollouts"
  cp -r "$S/config" "$P/config"; rm -rf "$P/config/series"; cp "$S/logs/c01_verify_models.json" "$P/logs/"
  : > "$P/calls.log"
}
series() {
  env "$@" SERIES_TEST=1 PILOT_DIR="$P" REAL_RT="$S/scripts/run_trial.sh" SERIES_RT="$T/stub/rt.sh" SERIES_SH="$T/stub/sh.py" \
      bash "$S/scripts/run_series.sh" < /dev/null > "$P/out.txt" 2>&1
  echo $? > "$P/rc.txt"
}
cnt() { grep -c "^$1" "$P/calls.log"; }
rc() { cat "$P/rc.txt"; }
log() { tr '\n' ';' < "$P/calls.log"; }
ran() { tail -n +2 "$P/results/run_ledger.csv" 2>/dev/null | cut -d, -f1 | sort -n | uniq | tr '\n' ' '; }
mkledger() { echo "trial,model,model_name,model_sha256,tag,run,launched,ended,eval_ui_exit,rerun_reason,manifest" > "$P/results/run_ledger.csv"; }

# G1 처음부터: 한 세션에 1–8 (모델 1 회 로딩), 시작 전 복귀 없음
setup g1; mkledger; series
chk G1_fresh_all_8_one_session "[ \$(rc) = 0 ] && [ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 0 ] && grep -q 'RT 1 trials=\[1 2 3 4 5 6 7 8\] plan=1 2 3 4 5 6 7 8' $P/calls.log && [ \"\$(ran)\" = '1 2 3 4 5 6 7 8 ' ]" "$(log)"
# G2 3 판 뒤 추론 오류 (E5 복귀 diff 1°) → 남은 4–8 을 새 세션으로
setup g2; mkledger; series SESS1="ended=fault_latch saved=3"
chk G2_fault_resumes_remaining "[ \$(rc) = 0 ] && [ \$(cnt RT) = 2 ] && grep -q 'RT 2 trials=\[4 5 6 7 8\] plan=4 5 6 7 8' $P/calls.log && [ \"\$(ran)\" = '1 2 3 4 5 6 7 8 ' ]" "$(log)"
# G3 Ctrl+C 로 2 판 뒤 멀리 (40°) 끝남 → 움직이지 않고 멈춤, 다시 실행해도 멈춤
setup g3; mkledger; series SESS1="ended=shutdown_signal saved=2 diff=40"
chk G3_ctrl_c_far_stops_no_move "[ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 0 ] && [ \"\$(ran)\" = '1 2 ' ]" "$(log)"
series
chk G3b_rerun_still_stopped "[ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 0 ]" "$(log)"
# G4 다 끝남 → 아무것도 안 함
setup g4; mkledger; for t in 1 2 3 4 5 6 7 8; do echo "$t,ft,x,x,t,20261109_10000${t}_x,a,b,0,\"\",m.json" >> "$P/results/run_ledger.csv"; mkdir -p "$P/eval/rollouts/20261109_10000${t}_x"; echo '{"ended_by":"episode_end_or_user_next","max_abs_diff_deg":1.0,"torque_left_on":true}' > "$P/eval/rollouts/20261109_10000${t}_x/end_state.json"; done; series
chk G4_all_done_nothing "[ \$(cnt RT) = 0 ]" "$(log); $(tail -3 $P/out.txt | tr '\n' ' ')"
[ $ok = 1 ] && echo ALL_PASS || echo SOME_FAIL
