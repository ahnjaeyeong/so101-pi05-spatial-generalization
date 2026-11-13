#!/usr/bin/env bash
# rft01 실물 파일럿 — 시행 1 개 실행 (사용자가 터미널에서 직접). ※ 팔에 토크가 걸리고, '준비' 에서 → 를 누르면 정책이 팔을 움직인다.
#
# 사용:  ~/so101_runs/main_k8/sgp01_real_eval/scripts/run_trial.sh <시행 번호 1–16>
#        CHECK=1 …/run_trial.sh <번호>    옵션 · 체크포인트 · 게이트만 확인 (eval_ui --check, 팔 · 카메라 연결 없음, 기록 안 남김)
#        RERUN="이유" …/run_trial.sh <번호>   이미 기록된 시행을 새 run ID 로 다시 (이전 결과는 그대로 둠)
#
# 하는 일 (기존 체계 재사용 — eval_ui.py · R2 세션 shim · r2_safety · d2 rollout_logged 는 수정하지 않는다):
#   1) config/pilot_plan.csv 에서 시행 행 (모델 · 큐브 자리 · 각도) 을 읽는다.
#   2) 게이트: logs/c01_verify_models.json 의 M1–M6 PASS · 앞 시행이 모두 results/trials.csv 에 기록됨 ·
#      시행 2 이후는 results/phase2_go.txt (scripts/gate.sh go) · 안전 개입이 있었던 시행은 results/ack_trialNN.txt 필요.
#   3) model.safetensors SHA-256 을 다시 계산해 config/models.env 와 비교 (다르면 실행 안 함).
#   4) 실행 manifest (모델 · SHA · 코드 파일 SHA-256 · git HEAD · 시행 조건) → results/manifests/
#   5) eval_ui 실행 (d2 표준 실물 평가와 같은 추론 옵션 + r2_safety stop + fault_latch stop, 판 1 개, 판 최대 60 s)
#   6) 끝나면 run 폴더에 trial_manifest.json 복사, results/run_ledger.csv 에 한 줄.
set -uo pipefail
S=$HOME/so101_runs/main_k8/sgp01_real_eval
# 시험용: PILOT_DIR (다른 폴더의 config · logs · results 로 게이트만 확인). GATE_ONLY=1 = 게이트 출력 뒤 끝 (eval_ui 안 띄움)
if [ -n "${PILOT_DIR:-}" ]; then
  [ "${GATE_ONLY:-0}" = 1 ] || [ "${CHECK:-0}" = 1 ] || { echo "⛔ PILOT_DIR 는 GATE_ONLY=1 또는 CHECK=1 과만 (시험용)"; exit 2; }
  S=$PILOT_DIR
fi
N=${1:?"시행 번호 (1–20) 를 주세요"}
[[ "$N" =~ ^([1-9]|1[0-9]|2[0-6])$ ]] || { echo "시행 번호는 1–26: $N"; exit 2; }
NN=$(printf %02d "$N")
source "$S/config/models.env"
CHECK=${CHECK:-0}
RERUN=${RERUN:-}
BATCH=${BATCH:-0}   # run_series.sh 연속 진행: 판정 기록 · go · ack 요구 생략 (STOP · 모델 검증 · 끝 자세 · SHA 는 그대로)

ROW=$(python3 - "$S/config/pilot_plan.csv" "$N" <<'EOF'
import csv, sys
for r in csv.DictReader(open(sys.argv[1], newline="")):
    if r["trial"] == sys.argv[2]:
        print(r["model"], r["label"], r["phase"], r["pair"], r["condition"].replace(" ", "_"), sep="|")
EOF
)
IFS='|' read -r MODEL LABEL PHASE PAIR COND <<< "$ROW"
[ -n "$MODEL" ] || { echo "계획에 시행 $N 없음"; exit 2; }
if [ "$MODEL" = ft ]; then CKPT=$FT_CKPT; WANT=$FT_SHA; MNAME=$FT_NAME; else CKPT=$BL_CKPT; WANT=$BL_SHA; MNAME=$BL_NAME; fi
TAG="t${NN}_${MODEL}_$(echo "$LABEL" | tr 'A-Z' 'a-z')"
# v3 (11-05) 연속 세션: SERIES_TRIALS="3 6 7" (같은 모델) + SERIES_PLAN=<그 시행들만 담은 계획 csv> — run_series.sh 가 준다.
#   모델을 한 번 올리고 판 N 개. 판 사이 · 끝에 end_hold E5 (END_HOLD_HOME=1) 가 safe_home 점검 + 15°/s 로 시작 자세 복귀.
NEP=1; PLANF=$S/config/pilot_plan.csv; PSTART=$N; RESET_FLAG=false
if [ -n "${SERIES_TRIALS:-}" ]; then
  [ "$BATCH" = 1 ] && [ -f "${SERIES_PLAN:-}" ] || { echo "⛔ SERIES_TRIALS 는 run_series.sh 에서만 (BATCH=1 · SERIES_PLAN 필요)"; exit 2; }
  python3 - "$S/config/pilot_plan.csv" "$MODEL" "$N" $SERIES_TRIALS <<'EOF2' || exit 2
import csv, sys
plan, model, first, *ts = sys.argv[1:]
rows = {r["trial"]: r for r in csv.DictReader(open(plan, newline=""))}
bad = [t for t in ts if t not in rows or rows[t]["model"] != model]
if bad or ts[0] != first:
    sys.exit(f"⛔ SERIES_TRIALS 가 계획과 맞지 않음 (모델 {model}, 첫 시행 {first}): {bad or ts}")
EOF2
  NEP=$(echo $SERIES_TRIALS | wc -w); PLANF=$SERIES_PLAN; PSTART=1; RESET_FLAG=true
  TAG="t$(for t in $SERIES_TRIALS; do printf %02d_ "$t"; done)${MODEL}_series"
  export END_HOLD_HOME=1
  echo "── 연속 세션: 시행 $SERIES_TRIALS ($NEP 판, 모델 1 회 로딩) · 판 사이 자동 복귀 (E5)"
fi
echo "── 시행 $N / $(tail -n +2 "$S/config/pilot_plan.csv" | wc -l) · 모델 $MNAME ($MODEL) · $COND · 쌍 $PAIR · Phase $PHASE · tag $TAG"

# ---- 게이트 (읽기만)
GATE=$(python3 - "$S" "$N" "$CHECK" "$RERUN" "$BATCH" <<'EOF'
import csv, json, os, sys
S, n, check, rerun = sys.argv[1], int(sys.argv[2]), sys.argv[3] == "1", sys.argv[4]
batch = len(sys.argv) > 5 and sys.argv[5] == "1"
bad = []
try:
    c = json.load(open(f"{S}/logs/c01_verify_models.json"))["checks"]
    miss = [k for k in ("M1_sha256", "M2_000500_preserved", "M3_config_diff_train_keys_only", "M4_processor_json_identical",
                        "M5_normalizer_values_identical", "M6_tokenizer_same_output") if not c.get(k, {}).get("pass")]
    if miss:
        bad.append(f"체크포인트 검증 FAIL: {miss}")
except Exception as e:
    bad.append(f"logs/c01_verify_models.json 을 못 읽음 ({e}) — scripts/c01_verify_models.py 먼저")
rows = list(csv.DictReader(open(f"{S}/results/trials.csv", newline=""))) if os.path.exists(f"{S}/results/trials.csv") else []
rows = list({r["run_id"]: r for r in rows}.values())  # run 마다 마지막 revision 만
done = {int(r["trial"]) for r in rows}
for k in range(1, n):
    if k not in done and not batch:
        bad.append(f"시행 {k} 결과가 results/trials.csv 에 없음 (scripts/record_trial.py 먼저)")
if n >= 2 and not batch and not os.path.exists(f"{S}/results/phase2_go.txt"):
    bad.append("Phase 2 (시행 1) 확인 기록 없음 — 시행 1 을 보고 이상이 없으면: scripts/gate.sh go \"확인 메모\"")
if os.path.exists(f"{S}/results/STOP"):
    bad.append("results/STOP 이 있음 (파일럿 중단 상태) — 내용 확인: " + open(f"{S}/results/STOP").read().strip()[:200])
for r in rows:
    k = int(r["trial"])
    if not batch and k < n and r.get("intervention", "none") not in ("none", "") and not os.path.exists(f"{S}/results/ack_trial{k:02d}.txt"):
        bad.append(f"시행 {k} 에 안전 개입 기록 ({r.get('intervention')}: {r.get('intervention_reason', '')}) — 확인 후 scripts/gate.sh ack {k} \"메모\"")
# v2 (11-05): 마지막으로 팔에 연결한 run 의 끝 상태 — 자동 복귀가 없으므로 팔이 시작 자세가 아닐 수 있다.
#   다음 connect (configure) 는 토크를 잠깐 끈다 → 시작 자세가 아니면 팔이 내려옴. safe_home.py 도착 기록 또는 gate.sh rest 필요.
led = list(csv.DictReader(open(f"{S}/results/run_ledger.csv", newline=""))) if os.path.exists(f"{S}/results/run_ledger.csv") else []
led = [r for r in led if r.get("run") not in ("", "none")]
if led:
    last = led[-1]["run"]
    es_p = f"{S}/eval/rollouts/{last}/end_state.json"
    rest_ok = os.path.exists(f"{S}/results/rest_{last}.txt")
    homes = []
    import glob as _g
    for hp in sorted(_g.glob(f"{S}/results/home_logs/{last}_*.json")):
        try:
            h = json.load(open(hp))
            homes.append(bool((h.get("move") or {}).get("ok")))
        except Exception:
            pass
    if not os.path.exists(es_p):
        if not rest_ok:
            bad.append(f"직전 run {last} 에 end_state.json 없음 (끝 상태 모름) — 팔을 직접 확인해 쉬는 자세에 두고: scripts/gate.sh rest \"메모\"")
    else:
        es = json.load(open(es_p))
        md = es.get("max_abs_diff_deg")
        if (md is None or md > 5.0) and not any(homes) and not rest_ok:
            bad.append(f"직전 run {last} 이 시작 자세에서 {md}° 떨어져 끝남 (토크 {es.get('torque_left_on')}) — "
                       f"safe_home.py --run eval/rollouts/{last} 로 복귀하거나, 손으로 옮겼으면 scripts/gate.sh rest \"메모\"")
# v3.2 (11-13): 직전 run 이 그리퍼를 연 채 끝났으면 막음 — 열린 채 시작하면 학습에 없는 시작 상태 (11-13 14:01 세션).
if led:
    try:
        es_g = json.load(open(f"{S}/eval/rollouts/{led[-1]['run']}/end_state.json"))
        eg = es_g.get("end_gripper")
        if eg is None:   # 예전 기록: 끝 값 없음 → 마지막 복귀의 그리퍼 값, 없으면 시작 값
            hg = [h.get("gripper") for h in es_g.get("homes", []) if h.get("gripper")]
            eg = (hg[-1].get("final", hg[-1].get("from")) if hg and es_g.get("homes", [{}])[-1].get("gripper") else (es_g.get("initial_position") or {}).get("gripper.pos"))
        if eg is not None and float(eg) > 10.0 and not os.path.exists(f"{S}/results/gripper_closed_{led[-1]['run']}.txt"):
            bad.append(f"직전 run 이 그리퍼를 연 채 끝남 ({float(eg):.0f}) — 먼저: scripts/gripper_close.py")
    except Exception:
        pass
if n in done and not rerun and not batch:
    bad.append(f"시행 {n} 은 이미 기록됨 — 다시 하려면 RERUN=\"이유\" (이전 결과는 남음)")
if check:
    print("CHECK_ONLY " + (" / ".join(bad) if bad else "게이트 통과"))
else:
    print("BLOCK " + " / ".join(bad) if bad else "OK")
EOF
)
echo "  게이트: $GATE"
[ "${GATE_ONLY:-0}" = 1 ] && exit 0
if [ "$CHECK" != 1 ] && [ "$GATE" != OK ]; then echo "⛔ 실행하지 않았어요."; exit 2; fi

# ---- 체크포인트 SHA-256
[ -f "$CKPT/model.safetensors" ] || { echo "⛔ 체크포인트 없음: $CKPT"; exit 2; }
echo "  체크포인트 SHA-256 계산 중 (약 7 s)…"
GOT=$(sha256sum "$CKPT/model.safetensors" | cut -d' ' -f1)
if [ "$GOT" != "$WANT" ]; then echo "⛔ SHA-256 불일치: $GOT (기대 $WANT)"; exit 2; fi
echo "  SHA-256 OK ${GOT:0:8}…${GOT: -8}"

# 2026-11-13 추론 설정 시험 (사용자: "추론만 바꿔서 해보자"): QT = 새 계획을 요청하는 남은 명령 수 (기본 30 → 계획 50 스텝 중 약 20 스텝 실행 뒤 교체),
#   EH = RTC execution_horizon (기본 20). 예: QT=18 EH=15 → 계획을 약 33 스텝 (1.1 s) 실행한 뒤 교체. 기본값이 아니면 tag 에 _qt18eh15 가 붙는다.
QT=${QT:-30}; EH=${EH:-}
[[ "$QT" =~ ^[0-9]+$ ]] && [ "$QT" -ge 14 ] && [ "$QT" -le 40 ] || { echo "⛔ QT 는 14–40: $QT (추론 지연이 최대 13 틱이라 14 아래면 명령이 끊김)"; exit 2; }
EXTRA=(); [ -n "$EH" ] && EXTRA+=("--inference.rtc.execution_horizon=$EH")
{ [ "$QT" != 30 ] || [ -n "$EH" ]; } && TAG="${TAG}_qt${QT}${EH:+eh$EH}"
ARGS=(--session main_k8/sgp01_real_eval --ckpt "$CKPT" --task "$TASK" --tag "$TAG" --episodes "$NEP" --episode-time "$EPISODE_TIME_S"
      --inference.rtc.prefix_attention_schedule=EXP "--inference.queue_threshold=$QT" "${EXTRA[@]}"
      --arm_filter=false --rollout_guard=warn --r2_safety=stop --r2_safety.over_target_deg=0 "--r2_safety.plan=$PLANF" "--r2_safety.plan_start=$PSTART"
      --fault_latch=stop --return_to_initial_position=false "--strategy.reset_to_initial_position=$RESET_FLAG")
cd "$HOME/so101_boxpick"
if [ "$CHECK" = 1 ]; then
  ROLLOUT_DIAG=1 python3 scripts/eval_ui.py "${ARGS[@]}" --check
  exit $?
fi

STAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$S/results/manifests"
MAN="$S/results/manifests/trial${NN}_${STAMP}.json"
python3 - "$MAN" "$N" "$MODEL" "$MNAME" "$CKPT" "$GOT" "$TAG" "$RERUN" "$S" "${ARGS[@]}" <<'EOF'
import csv, hashlib, json, os, subprocess, sys, datetime
man, n, model, mname, ckpt, sha, tag, rerun, S, *args = sys.argv[1:]
H = os.path.expanduser("~")
files = [f"{H}/so101_boxpick/scripts/eval_ui.py", f"{S}/eval/rollout_logged.py", f"{S}/eval/fault_latch.py",
         f"{H}/so101_runs/main_k8/r2_grasp_diagnostic/eval/rollout_logged.py", f"{H}/so101_runs/main_k8/r2_grasp_diagnostic/eval/r2_safety.py",
         f"{H}/so101_runs/main_k8/r2_grasp_diagnostic/eval/r2_live.py", f"{H}/so101_runs/main_k8/r2_grasp_diagnostic/scripts/r2_place_viewer.py",
         f"{H}/so101_runs/main_k8/d2/eval/rollout_logged.py", f"{H}/so101_runs/main_k8/d2/eval/arm_filter.py", f"{H}/so101_runs/main_k8/d2/eval/diag_log.py",
         f"{H}/so101_runs/main_k8/d2/pan_inference_diagnostic/scripts/cube_coords.py", f"{S}/config/pilot_plan.csv", f"{S}/config/models.env",
         f"{S}/scripts/run_trial.sh", f"{S}/eval/end_hold.py", f"{S}/scripts/safe_home.py"]
code = {f: hashlib.sha256(open(f, "rb").read()).hexdigest() if os.path.exists(f) else None for f in files}
g = lambda *c: subprocess.run(["git", "-C", f"{H}/so101_boxpick", *c], capture_output=True, text=True).stdout.strip()
plan = [r for r in csv.DictReader(open(f"{S}/config/pilot_plan.csv", newline="")) if r["trial"] == n][0]
try:
    lv = subprocess.run([f"{H}/so101-env/bin/python", "-c", "import lerobot;print(lerobot.__version__)"], capture_output=True, text=True,
                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")).stdout.strip()
except Exception:
    lv = None
json.dump({"trial": int(n), "model": model, "model_name": mname, "ckpt": ckpt, "model_sha256": sha, "tag": tag, "rerun_reason": rerun or None,
           "launched": datetime.datetime.now().isoformat(timespec="seconds"), "plan_row": plan, "eval_ui_args": args,
           "env": {"ROLLOUT_DIAG": "1"}, "code_sha256": code,
           "so101_boxpick_git": {"head": g("rev-parse", "HEAD"), "eval_ui_status": g("status", "--porcelain", "scripts/eval_ui.py") or "tracked-clean"},
           "lerobot_version": lv, "series_trials": os.environ.get("SERIES_TRIALS") or None, "series_plan": os.environ.get("SERIES_PLAN") or None,
           "end_hold_home": os.environ.get("END_HOLD_HOME") == "1"}, open(man, "w"), indent=1, ensure_ascii=False)
print("  manifest:", man)
EOF

T0=$(date +%s)
ROLLOUT_DIAG=1 python3 scripts/eval_ui.py "${ARGS[@]}"
RC=$?
RUN=$(ls -1dt "$S"/eval/rollouts/*_"$TAG" 2>/dev/null | head -1)
if [ -n "$RUN" ] && [ "$(stat -c %Y "$RUN")" -ge "$T0" ]; then
  cp -n "$MAN" "$RUN/trial_manifest.json"
else
  RUN=""
fi
[ -f "$S/results/run_ledger.csv" ] || echo "trial,model,model_name,model_sha256,tag,run,launched,ended,eval_ui_exit,rerun_reason,manifest" > "$S/results/run_ledger.csv"
LTRIALS=$N
if [ -n "${SERIES_TRIALS:-}" ]; then   # 저장된 판 수만큼 앞에서부터 시행 번호. 0 판이면 trial=0 (run 은 남김 — 끝 자세 게이트용)
  SAVED=$(python3 -c "import json,sys;print(int(json.load(open(sys.argv[1])).get('saved',0)))" "$RUN/results.json" 2>/dev/null || echo 0)
  LTRIALS=$(echo $SERIES_TRIALS | cut -d' ' -f1-"$((SAVED > 0 ? SAVED : 1))")
  [ "$SAVED" -gt 0 ] 2>/dev/null || LTRIALS=0
  echo "  연속 세션 저장 $SAVED 판 → 시행 $LTRIALS"
fi
for LT in $LTRIALS; do
  echo "$LT,$MODEL,$MNAME,$GOT,$TAG,$(basename "${RUN:-none}"),$STAMP,$(date +%Y%m%d_%H%M%S),$RC,\"${RERUN//\"/\'}\",$(basename "$MAN")" >> "$S/results/run_ledger.csv"
done
echo
echo "── 시행 $N 끝 (eval_ui 종료 코드 $RC) · run: ${RUN:-없음 (저장된 판 없음 또는 시작 전 취소)}"
if [ -n "$RUN" ]; then
  echo "다음 (로봇 연결 없음):"
  echo "  1) $S/scripts/post_trial.sh $RUN        # 기록 점검 · 재구성 (GPU 2–5 분) · 자동 지표"
  echo "  2) $S/scripts/record_trial.py $RUN       # 사용자 판정 입력 → results/trials.csv"
fi
