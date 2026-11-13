#!/usr/bin/env bash
# run_series.sh v3 시험 (로봇 · 카메라 · GPU 없음). 임시 폴더 + 가짜 run_trial / safe_home.
# 가짜 run_trial 도 게이트는 진짜 run_trial.sh (PILOT_DIR + GATE_ONLY=1 + BATCH=1 + SERIES_*) 를 쓴다. PASS/FAIL 줄, 마지막 ALL_PASS / SOME_FAIL.
# 세션 k 번째의 결과는 SESS<k>="ended=<ended_by> saved=<판 수|all> diff=<°>" 로 정한다 (기본 정상 · 전부 저장 · 1°).
set -u
S=$HOME/so101_runs/main_k8/sgp01_real_eval
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

T1=20261105_111427_1k_t01_ft_k3_0; T2=20261105_130203_20k_t02_bl_k3_0
setup() {  # 지금 상태: 시행 1 (가까이 끝, 기록됨) · 시행 2 (167° 떨어져 끝, 복귀 안 됨). go 없음.
  P=$T/p_$1; rm -rf "$P"; mkdir -p "$P/results" "$P/logs" "$P/eval/rollouts/$T1" "$P/eval/rollouts/$T2"
  cp -r "$S/config" "$P/config"; rm -rf "$P/config/series"; cp "$S/logs/c01_verify_models.json" "$P/logs/"
  echo '{"ended_by":"episode_end_or_user_next","max_abs_diff_deg":4.57,"torque_left_on":true}' > "$P/eval/rollouts/$T1/end_state.json"
  echo '{"ended_by":"episode_end_or_user_next","max_abs_diff_deg":166.95,"torque_left_on":true}' > "$P/eval/rollouts/$T2/end_state.json"
  printf "trial,run_id,intervention,intervention_reason\n1,$T1,none,\n" > "$P/results/trials.csv"
  { echo "trial,model,model_name,model_sha256,tag,run,launched,ended,eval_ui_exit,rerun_reason,manifest"
    echo "1,ft,x,x,t01,$T1,a,b,0,\"\",m.json"; echo "2,bl,x,x,t02,$T2,a,b,0,\"\",m.json"; } > "$P/results/run_ledger.csv"
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
ran() { tail -n +2 "$P/results/run_ledger.csv" | cut -d, -f1 | sort -n | uniq | tr '\n' ' '; }

# S1 (시행 1–2 상태) → t02 자동 복귀 → BL 남은 전부 (3 6 7 13–16) → FT 남은 전부 (4 5 8–12). 계획 16 행, 모델당 1 세션.
setup s1; series
chk S1_home_t02_then_sessions "[ \$(rc) = 0 ] && [ \$(cnt RT) = 2 ] && head -1 $P/calls.log | grep -q 'SH $T2 auto ok' && grep -q 'RT 1 trials=\[3 6 7 13 14 15 16\] plan=3 6 7 13 14 15 16' $P/calls.log && grep -q 'RT 2 trials=\[4 5 8 9 10 11 12\] plan=4 5 8 9 10 11 12' $P/calls.log && [ \"\$(ran)\" = '1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 ' ]" "$(log)"
# S2 BL 세션이 fault 로 1 판 뒤 끝남 (E5 가 복귀 → diff 1°) → 남은 시행을 새 세션으로 (FT · BL 6 7 13–16)
setup s2; series SESS1="ended=fault_latch saved=1"
chk S2_fault_resumes_new_session "[ \$(rc) = 0 ] && [ \$(cnt RT) = 3 ] && grep -q 'RT 3 trials=\[6 7 13 14 15 16\] plan=6 7 13 14 15 16' $P/calls.log && grep -q 'trials=\[4 5 8 9 10 11 12\]' $P/calls.log && [ \"\$(ran)\" = '1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 ' ]" "$(log)"
# S3 Ctrl+C 로 1 판 뒤, 멀리 끝남 → 움직이지 않고 멈춤
setup s3; series SESS1="ended=shutdown_signal saved=1 diff=40"
chk S3_ctrl_c_far_stops_no_move "[ \$(rc) = 2 ] && [ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 1 ] && grep -q 'shutdown_signal' $P/out.txt" "$(log)"
# S3b 다시 실행해도 그 run 은 자동으로 안 움직이고 시행도 안 돌림
series
chk S3b_rerun_still_stopped "[ \$(rc) = 2 ] && [ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 1 ]" "$(log)"
# S3c 손으로 두고 gate.sh rest → 남은 시행 이어서
echo REST > "$P/results/rest_20261105_150001_1k_series1.txt"; series
chk S3c_rest_then_resume "[ \$(rc) = 0 ] && grep -q 'trials=\[6 7 13 14 15 16\]' $P/calls.log && [ \"\$(ran)\" = '1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 ' ]" "$(log)"
# S4 Ctrl+C 로 끝났지만 팔이 시작 자세 근처 (판 사이에 누름) → 움직임 없이 멈춤
setup s4; series SESS1="ended=shutdown_signal saved=2 diff=1"
chk S4_ctrl_c_near_stops "[ \$(rc) = 2 ] && [ \$(cnt RT) = 1 ] && [ \$(cnt SH) = 1 ] && grep -q '다 못 끝냈어요' $P/out.txt" "$(log)"
# S5 Esc (user_quit) 로 2 판 뒤 → 멈춤
setup s5; series SESS1="ended=user_quit saved=2 diff=1"
chk S5_user_quit_stops "[ \$(rc) = 2 ] && [ \$(cnt RT) = 1 ] && [ \"\$(ran)\" = '1 2 3 6 ' ]" "$(log)"
# S6 저장 0 판 → 멈춤
setup s6; series SESS1="saved=0"
chk S6_zero_saved_stops "[ \$(rc) = 2 ] && [ \$(cnt RT) = 1 ] && grep -q '저장된 판이 없어요' $P/out.txt" "$(log)"
# S7 STOP 파일 → 게이트 BLOCK → 시행 0
setup s7; echo "STOP x" > "$P/results/STOP"; series
chk S7_stop_blocks "[ \$(rc) = 2 ] && [ \$(cnt RT) = 0 ] && [ \$(cnt GATEBLOCK) = 1 ]" "$(log)"
# S8 모델 검증 FAIL → 막힘
setup s8; python3 -c "import json;p='$P/logs/c01_verify_models.json';c=json.load(open(p));c['checks']['M5_normalizer_values_identical']['pass']=False;json.dump(c,open(p,'w'))"
series
chk S8_model_check_blocks "[ \$(rc) = 2 ] && [ \$(cnt RT) = 0 ] && grep -q 'M5' $P/out.txt"
# S9 t02 복귀 실패 → 시행 없이 멈춤
setup s9; series HOME_FAIL="$T2"
chk S9_initial_home_fail_stops "[ \$(rc) = 2 ] && [ \$(cnt RT) = 0 ] && grep -q '복귀 못 함' $P/out.txt"
# S10 run_trial.sh SERIES_TRIALS 검증: 모델 섞임 · 첫 시행 불일치 · BATCH 없음 → 거부
setup s10; PL=$P/config/x.csv; cp "$S/config/pilot_plan.csv" "$PL"
o1=$(env PILOT_DIR="$P" GATE_ONLY=1 BATCH=1 SERIES_TRIALS="3 4" SERIES_PLAN="$PL" "$S/scripts/run_trial.sh" 3 2>&1)
o2=$(env PILOT_DIR="$P" GATE_ONLY=1 BATCH=1 SERIES_TRIALS="6 7" SERIES_PLAN="$PL" "$S/scripts/run_trial.sh" 3 2>&1)
o3=$(env PILOT_DIR="$P" GATE_ONLY=1 SERIES_TRIALS="3 6" SERIES_PLAN="$PL" "$S/scripts/run_trial.sh" 3 2>&1)
chk S10_series_trials_validated "echo \"$o1\" | grep -q '맞지 않음' && echo \"$o2\" | grep -q '맞지 않음' && echo \"$o3\" | grep -q 'run_series.sh 에서만'" "$o1 / $o2 / $o3"
# S11 BATCH 게이트는 끝 자세 검사를 유지 (t02 167° 복귀 기록 없음 → 막힘)
g=$(env PILOT_DIR="$P" GATE_ONLY=1 BATCH=1 SERIES_TRIALS="3 6 7" SERIES_PLAN="$PL" "$S/scripts/run_trial.sh" 3 | grep '게이트:')
chk S11_batch_gate_keeps_end_state "echo \"$g\" | grep -q '166.95'" "$g"
# S12 run_trial.sh 단독 규칙 그대로 (시행 2 기록 · go 요구)
g=$(env PILOT_DIR="$P" GATE_ONLY=1 "$S/scripts/run_trial.sh" 3 | grep '게이트:')
chk S12_non_batch_rules_unchanged "echo \"$g\" | grep -q '시행 2 결과' && echo \"$g\" | grep -q 'Phase 2'" "$g"
# S14 지금 상태 그대로 (시행 1–7 끝, 시행 8 세션은 로딩 중 Ctrl+C = trial 0 · end_state 없음) → rest 기록 없으면 멈춤, 있으면 FT (8 9 10 11 12) → BL (13–16)
setup s14; T67=20261105_134136_20k_t06_07_bl_series; T8=20261105_134711_1k_t08_ft_series; mkdir -p "$P/eval/rollouts/$T67" "$P/eval/rollouts/$T8"
echo '{"ended_by":"episode_end_or_user_next","max_abs_diff_deg":1.14,"torque_left_on":true}' > "$P/eval/rollouts/$T67/end_state.json"
for t in 3 4 5; do echo "$t,x,x,x,tag,20261105_13000${t}_x_t0$t,a,b,0,\"\",m.json" >> "$P/results/run_ledger.csv"; mkdir -p "$P/eval/rollouts/20261105_13000${t}_x_t0$t"; echo '{"ended_by":"episode_end_or_user_next","max_abs_diff_deg":4,"torque_left_on":true}' > "$P/eval/rollouts/20261105_13000${t}_x_t0$t/end_state.json"; done
echo "6,bl,x,x,tag,$T67,a,b,0,\"\",m.json" >> "$P/results/run_ledger.csv"; echo "7,bl,x,x,tag,$T67,a,b,0,\"\",m.json" >> "$P/results/run_ledger.csv"
echo "0,ft,x,x,tag,$T8,a,b,0,\"\",m.json" >> "$P/results/run_ledger.csv"
echo '{"move":{"ok":true}}' > /dev/null; mkdir -p "$P/results/home_logs"; echo '{"move":{"ok":true}}' > "$P/results/home_logs/${T2}_x.json"
series
chk S14a_aborted_session_needs_rest "[ \$(rc) = 2 ] && [ \$(cnt RT) = 0 ] && grep -q 'end_state.json 없음' $P/out.txt" "$(log)"
echo REST > "$P/results/rest_$T8.txt"; series
chk S14b_after_rest_ft_then_bl "[ \$(rc) = 0 ] && grep -q 'RT 1 trials=\[8 9 10 11 12\] plan=8 9 10 11 12' $P/calls.log && grep -q 'RT 2 trials=\[13 14 15 16\] plan=13 14 15 16' $P/calls.log" "$(log)"
# S13 다 끝났으면 아무것도 안 돌림
setup s13; series; series
chk S13_all_done_nothing "[ \$(rc) = 0 ] && grep -q '모두 run 이 있어요' $P/out.txt && [ \$(cnt RT) = 2 ]"
echo; [ $ok = 1 ] && echo ALL_PASS || echo SOME_FAIL
exit $((1 - ok))
