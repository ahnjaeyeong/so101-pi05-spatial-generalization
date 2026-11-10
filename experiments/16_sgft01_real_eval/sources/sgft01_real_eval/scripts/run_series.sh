#!/usr/bin/env bash
# rft01 실물 파일럿 — 남은 시행을 이어서 (사용자가 터미널에서 직접 실행). ※ 정책이 팔을 움직이고, 판 사이에 팔이 시작 자세로 돌아간다.
#
# 사용:  ~/so101_runs/main_k8/sgft01_real_eval/scripts/run_series.sh
#
# v3 (11-05 사용자 요청): 모델을 한 번 올리고 그 모델의 남은 시행을 한 세션에서 이어서. 판마다 P/F → (→) → 다음 판.
#   판 사이 · 세션 끝에 팔이 시작 자세로 자동 복귀 (end_hold E5: safe_home 점검 + 15°/s, Ctrl+C = 그 자리 정지).
#   순서: 남은 시행을 모델별로 묶어 첫 남은 시행의 모델부터 (예: BL 3·6·7 → FT 4·5·8). 모델 로딩은 모델당 1 회.
#   0) 직전 run 의 팔이 시작 자세에서 > 5° 떨어져 있으면 먼저 safe_home.py --auto 로 복귀 (점검 PASS 일 때만).
#   판정 기록 · go · ack 질문 없음 (eval_ui 의 P/F 만). 분석 · 기록은 끝난 뒤 Claude 가.
#   멈춤: Ctrl+C · Esc (사용자 종료) · 예외 · 복귀 점검 실패 · 진행 없음. 다시 같은 명령이면 남은 시행부터.
#   fault (추론 오류) 로 세션이 끝나면 (E5 가 복귀한 뒤) 남은 시행으로 새 세션을 띄워 계속.
set -uo pipefail
S=$HOME/so101_runs/main_k8/sgft01_real_eval
RT=$S/scripts/run_trial.sh; SH=$S/scripts/safe_home.py; SHPY=$HOME/so101-env/bin/python
if [ "${SERIES_TEST:-0}" = 1 ]; then   # 시험용 (tests/test_series.sh): 임시 폴더 + 가짜 명령. 로봇 없음.
  S=${PILOT_DIR:?}; RT=${SERIES_RT:?}; SH=${SERIES_SH:?}; SHPY=python3
fi
LED=$S/results/run_ledger.csv
trap 'echo; echo "중단됨 (Ctrl+C) — 팔은 그 자리에서 토크 유지. 확인 후 다시 run_series.sh"; exit 130' INT

py() { python3 - "$S" "$@"; }
info() { py "$1" <<'EOF'
import csv, sys
r = [r for r in csv.DictReader(open(sys.argv[1] + "/config/pilot_plan.csv", newline="")) if r["trial"] == sys.argv[2]]
print(f"{'FT sgft01 010000' if r[0]['model'] == 'ft' else 'BL d2 020000'} · {r[0]['condition']} · 각도 {r[0]['angle_text']}" if r else "계획에 없음")
EOF
}
# 남은 시행 (ledger 에 run 이 없는 2–16, 11-05 시행 9–16 = Unknown U2 · U7 · U8 · U1 추가) 중 첫 시행의 모델과 그 모델의 남은 시행들: "bl 3 6 7"
pending() { py <<'EOF'
import csv, os, sys
S = sys.argv[1]
L = S + "/results/run_ledger.csv"
ran = {int(r["trial"]) for r in csv.DictReader(open(L, newline="")) if r.get("run") not in ("", "none")} if os.path.exists(L) else set()
plan = [r for r in csv.DictReader(open(S + "/config/pilot_plan.csv", newline="")) if int(r["trial"]) >= 1 and int(r["trial"]) not in ran]
if plan:
    m = plan[0]["model"]
    print(m, " ".join(r["trial"] for r in plan if r["model"] == m))
EOF
}
mkplan() {  # $1 = 이름, 나머지 = 시행 번호 → config/series/<이름>.csv (계획 행 그대로, 그 순서로). 경로 출력
  local out=$S/config/series/$1.csv; shift
  mkdir -p "$S/config/series"
  python3 - "$S/config/pilot_plan.csv" "$out" "$@" <<'EOF'
import csv, sys
src, out, *ts = sys.argv[1:]
rows = {r["trial"]: r for r in csv.DictReader(open(src, newline=""))}
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(next(iter(rows.values())).keys()))
    w.writeheader()
    for t in ts:
        w.writerow(rows[t])
EOF
  echo "$out"
}
last_run() { [ -f "$LED" ] && tail -n +2 "$LED" | awk -F, '$6!="none" && $6!=""{r=$6} END{print r}'; }
ended_by() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('ended_by'))" "$S/eval/rollouts/$1/end_state.json" 2>/dev/null; }
# 끝 상태 판정: near / homed / home / stop:<이유>
end_action() { py "$1" <<'EOF'
import glob, json, os, sys
S, run = sys.argv[1], sys.argv[2]
p = f"{S}/eval/rollouts/{run}/end_state.json"
if os.path.exists(f"{S}/results/rest_{run}.txt"):
    print("homed"); sys.exit()
for h in glob.glob(f"{S}/results/home_logs/{run}_*.json"):
    try:
        if (json.load(open(h)).get("move") or {}).get("ok"):
            print("homed"); sys.exit()
    except Exception:
        pass
if not os.path.exists(p):
    print("stop:end_state.json 없음 (끝 상태 모름)"); sys.exit()
e = json.load(open(p))
by, md = str(e.get("ended_by")), e.get("max_abs_diff_deg")
print(f"   끝 상태: {by} · 시작 자세와 최대 {md}° · 토크 {e.get('torque_left_on')}", file=sys.stderr)
if md is not None and md <= 5.0:
    print("near"); sys.exit()
if by in ("shutdown_signal", "user_quit") or by.startswith("exception"):
    print(f"stop:{by} 로 끝남 — 자동으로 움직이지 않음"); sys.exit()
print("home")
EOF
}
home_after() {  # $1 = run id. 실패면 멈춤
  local R=$1 A
  A=$(end_action "$R")
  case "$A" in
    near|homed) return 0 ;;
    home)
      echo "── 시작 자세로 복귀 (safe_home --auto, 15°/s, 점검 실패 시 안 움직임 · Ctrl+C = 그 자리 정지)"
      if PYTHONDONTWRITEBYTECODE=1 "$SHPY" "$SH" --run "$S/eval/rollouts/$R" --auto; then return 0; fi
      echo "⛔ 복귀 못 함 (점검 실패 또는 도중 정지) — 팔은 그 자리에서 토크 유지. 위 출력 확인."
      echo "   팔을 직접 처리 (safe_home.py --run eval/rollouts/$R  또는 손으로 + gate.sh rest \"메모\") 뒤 다시 run_series.sh"
      exit 2 ;;
    *)
      echo "⛔ ${A#stop:}. 팔을 확인하고 (safe_home.py --run eval/rollouts/$R  또는 손으로 + gate.sh rest \"메모\") 다시 run_series.sh"
      exit 2 ;;
  esac
}

R=$(last_run)
[ -n "$R" ] && { echo "직전 run: $R"; home_after "$R"; }
P=$(pending)
[ -n "$P" ] || { echo "계획의 시행 (2–16) 모두 run 이 있어요. 분석을 요청하세요."; exit 0; }
echo "남은 시행을 모델별 세션으로 진행합니다 (모델당 로딩 1 회). 판마다 P/F → (→). 멈추려면 Ctrl+C."
while [ -n "$P" ]; do
  read -r MODEL TRIALS <<< "$P"
  echo
  echo "════════ ${MODEL^^} 세션 — 시행 $TRIALS"
  for t in $TRIALS; do echo "   시행 $t: $(info "$t")"; done
  PLANF=$(mkplan "$(date +%Y%m%d_%H%M%S)_${MODEL}" $TRIALS)
  BATCH=1 SERIES_TRIALS="$TRIALS" SERIES_PLAN="$PLANF" "$RT" "${TRIALS%% *}"
  R=$(last_run)
  NEWP=$(pending)
  if [ "$NEWP" = "$P" ]; then
    echo "⛔ 이 세션에서 저장된 판이 없어요 (게이트 BLOCK · 시작 전 취소 · 오류). 위 출력 확인."
    [ -n "$R" ] && home_after "$R"
    exit 2
  fi
  home_after "$R"   # E5 가 이미 복귀했으면 near. Ctrl+C · 종료 · 예외로 멀리 끝났으면 여기서 멈춤
  # 이 세션의 시행이 남았는데 fault 로 끝난 게 아니면 (Esc · Ctrl+C · 복귀 점검 실패 등) 멈춤
  LEFT=$(for t in $TRIALS; do tail -n +2 "$LED" | awk -F, -v t="$t" '$1==t && $6!="none" && $6!=""{f=1} END{exit !f}' || printf '%s ' "$t"; done)
  if [ -n "$LEFT" ]; then
    BY=$(ended_by "$R")
    case "$BY" in
      fault_latch|engine_failed_shutdown) echo "   추론 오류로 세션이 끝났어요 — 남은 시행 $LEFT 은 새 세션으로." ;;
      *) echo "⛔ 세션이 시행을 다 못 끝냈어요 (끝난 이유 $BY). 남은 시행: $LEFT. 확인 후 다시 run_series.sh"; exit 2 ;;
    esac
  fi
  P=$NEWP
done
echo
echo "════════ 계획 시행 모두 끝. Claude 에게 분석을 요청하세요 (post_trial · 자동 지표 · 비교는 Claude 가 돌림)."
