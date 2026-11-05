#!/usr/bin/env python3
"""시행 결과 입력 → results/trials.csv 에 한 줄 추가 (덮어쓰지 않음). 로봇 · 카메라 연결 없음, 표준 라이브러리만.

사용 (사용자, 터미널):  python3 ~/so101_runs/main_k8/rft01_real_pilot/scripts/record_trial.py <run 폴더>
  - reports/<run>/trial_auto.json (post_trial.sh) 의 [기록] · [자동 후보] 값을 먼저 보여 준다.
  - 사용자 판정 칸은 기본값 없이 묻는다 (자동 후보를 그대로 쓰지 않는다): y = 예 · n = 아니오 · u = 판단 못함 · na = 해당 없음
  - 같은 run 을 다시 입력하려면 --amend "이유" (새 revision 줄을 더함, 이전 줄은 남김)
비대화 (시험용): --answers first_grasp=y,empty_grasp=n,pan_reversal=n,wrist_reacquire=na,final_success=y,intervention=none,intervention_reason=,memo=...
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

S_DIR = Path(__file__).resolve().parents[1]
OUT = S_DIR / "results/trials.csv"
YN = {"y", "n", "u"}
YNA = {"y", "n", "u", "na"}
INTERVENTIONS = ["none", "r2_safety_stop", "fault_latch", "user_key_end_early", "ctrl_c", "power_off", "hand_contact", "other"]
QUESTIONS = [  # (칸, 질문, 허용값)
    ("first_grasp", "첫 파지 성공? (첫 닫힘에서 큐브를 쥐었나)", YN),
    ("empty_grasp", "빈 파지 (큐브 없이 닫힘) 가 한 번이라도 있었나?", YN),
    ("pan_reversal", "Pan 방향 반전 (목표 쪽으로 가다 / 지나친 뒤 되돌아옴) 이 있었나?", YNA),
    ("wrist_reacquire", "Wrist 영상에서 큐브를 놓친 뒤 다시 잡았나? (놓친 적 없으면 na)", YNA),
    ("final_success", "최종 작업 성공? (큐브를 상자에 넣음)", YN),
]
FIELDS = ["trial", "run_id", "revision", "amend_reason", "rerun_reason", "recorded_at", "model", "model_name", "model_sha256", "code_sha256_digest",
          "boxpick_git_head", "condition", "plan_label", "pair", "phase",
          "cube_x", "cube_y", "cube_yaw_deg", "angle_class", "coord_status", "plan_check", "plan_check_warn",
          "start_pan", "start_lift", "start_elbow", "start_wrist_flex", "start_wrist_roll", "start_gripper",
          "video_front", "video_wrist", "dataset", "filter_log", "eval_ui_verdict", "seconds", "frames",
          "auto_first_close", "auto_n_closes", "auto_empty_before_grasp", "auto_pan_rev_pre_close", "auto_pan_rev_whole", "auto_pan_max_past_target",
          "auto_pan_min", "auto_pan_max", "auto_wrist_lost_segments", "auto_wrist_reacquired",
          "safety_stops", "fault_events", "console_ctrl_c", "end_ended_by", "end_max_diff_from_start_deg", "end_torque_left_on", "auto_return_blocked_calls",
          "first_grasp", "empty_grasp", "pan_reversal", "wrist_reacquire", "final_success", "intervention", "intervention_reason", "memo"]


def ask(prompt, allowed=None, free=False):
    while True:
        try:
            a = input(prompt).strip()
        except EOFError:
            raise SystemExit("입력이 끊겼어요 — 저장하지 않았어요.")
        if free:
            return a.replace("\n", " ")
        if a.lower() in allowed:
            return a.lower()
        print(f"   허용: {' / '.join(sorted(allowed))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--amend", default="")
    ap.add_argument("--answers", default="")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--reports-root", default=str(S_DIR / "reports"), help="시험용")
    a = ap.parse_args()
    run = Path(a.run).resolve()
    out = Path(a.out)
    auto_p = Path(a.reports_root) / run.name / "trial_auto.json"
    if not auto_p.exists():
        raise SystemExit(f"⛔ {auto_p} 없음 — 먼저 scripts/post_trial.sh {run}")
    A = json.loads(auto_p.read_text())
    m = A.get("manifest") or {}
    if not m:
        raise SystemExit("⛔ trial_manifest.json 이 없는 run (run_trial.sh 로 실행한 run 만 기록)")
    prev = list(csv.DictReader(open(out, newline=""))) if out.exists() else []
    same = [r for r in prev if r["run_id"] == run.name]
    if same and not a.amend:
        raise SystemExit(f"⛔ {run.name} 은 이미 기록됨 (revision {same[-1]['revision']}). 고치려면 --amend \"이유\"")
    au = A.get("auto") or {}
    pr, pw, wr = au.get("pan_pre_first_close") or {}, au.get("pan_whole") or {}, au.get("wrist") or {}
    sj = A.get("start_joints") or {}
    cube = A.get("cube") or {}
    vids = A["paths"]["videos"]
    print(f"\n── 시행 {m['trial']} · {m['model_name']} · {(m.get('plan_row') or {}).get('condition')} · run {run.name}")
    print(f"  시작 사진 [기록]: {A['plan_check'][0] if A['plan_check'] else '없음'}")
    print(f"  eval_ui P/F [기록]: {(A.get('eval_ui') or {}).get('verdict')}  · {(A.get('eval_ui') or {}).get('seconds')} s")
    print(f"  [자동 후보] 첫 닫힘 {au.get('first_close_T4')} · 닫힘 {au.get('n_closes')} 회 · 첫 파지 전 빈 닫힘 {au.get('n_empty_before_first_grasp')}")
    print(f"  [자동 후보] Pan 반전 첫 닫힘 전 {pr.get('n_reversals')} · 전체 {pw.get('n_reversals')} · 목표 지나침 최대 {pw.get('max_past_target_deg')}°"
          f" · pan {pw.get('pan_min')} … {pw.get('pan_max')}")
    print(f"  [자동 후보] Wrist 놓침 {len(wr.get('lost_segments') or [])} 구간 · 재획득 {wr.get('reacquired')}")
    print(f"  [기록] r2_safety STOP {len(A['safety_stops'])} {[s['rule'] for s in A['safety_stops']]} · FAULT {len(A['fault_events'])} · console {A['console_flags']}")
    print("  (자동 후보는 참고용. 아래는 직접 본 것으로 답하세요.)\n")
    given = dict(kv.split("=", 1) for kv in a.answers.split(",") if "=" in kv) if a.answers else None
    ans = {}
    for k, q, allowed in QUESTIONS:
        if given is not None:
            v = given.get(k, "")
            if v not in allowed:
                raise SystemExit(f"--answers {k}={v} 허용값 {sorted(allowed)}")
            ans[k] = v
        else:
            ans[k] = ask(f"  {q} [{'/'.join(sorted(allowed))}]: ", allowed)
    auto_iv = "r2_safety_stop" if A["safety_stops"] else ("fault_latch" if A["fault_events"] else ("ctrl_c" if A["console_flags"].get("ctrl_c") else None))
    if given is not None:
        ans["intervention"] = given.get("intervention", "")
        if ans["intervention"] not in INTERVENTIONS:
            raise SystemExit(f"intervention 허용값 {INTERVENTIONS}")
        ans["intervention_reason"] = given.get("intervention_reason", "")
        ans["memo"] = given.get("memo", "")
    else:
        print(f"  중단 · 안전 개입 종류: {' / '.join(INTERVENTIONS)}" + (f"   (기록에서 찾은 것: {auto_iv})" if auto_iv else ""))
        ans["intervention"] = ask("  중단 · 안전 개입: ", set(INTERVENTIONS))
        ans["intervention_reason"] = ask("  이유 (없으면 Enter): ", free=True) if ans["intervention"] != "none" else ""
        ans["memo"] = ask("  메모 (없으면 Enter): ", free=True)
    if auto_iv and ans["intervention"] == "none":
        print(f"  ⚠ 기록에는 {auto_iv} 가 있는데 'none' 으로 입력했어요 — 그대로 저장합니다 (두 값 모두 남음).")
    code = m.get("code_sha256") or {}
    row = {"trial": m["trial"], "run_id": run.name, "revision": (int(same[-1]["revision"]) + 1) if same else 1, "amend_reason": a.amend,
           "rerun_reason": m.get("rerun_reason") or "", "recorded_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "model": m["model"], "model_name": m["model_name"], "model_sha256": m["model_sha256"],
           "code_sha256_digest": hashlib.sha256(json.dumps(code, sort_keys=True).encode()).hexdigest()[:16],
           "boxpick_git_head": (m.get("so101_boxpick_git") or {}).get("head"), "condition": (m.get("plan_row") or {}).get("condition"),
           "plan_label": (m.get("plan_row") or {}).get("label"), "pair": (m.get("plan_row") or {}).get("pair"), "phase": (m.get("plan_row") or {}).get("phase"),
           **{k: cube.get(k) for k in ("cube_x", "cube_y", "cube_yaw_deg", "angle_class", "coord_status")},
           "plan_check": (A["plan_check"] or [""])[0], "plan_check_warn": "; ".join(A["plan_check_warn"]),
           "start_pan": sj.get("shoulder_pan"), "start_lift": sj.get("shoulder_lift"), "start_elbow": sj.get("elbow_flex"),
           "start_wrist_flex": sj.get("wrist_flex"), "start_wrist_roll": sj.get("wrist_roll"), "start_gripper": sj.get("gripper"),
           "video_front": next((v for v in vids if "front" in v), ""), "video_wrist": next((v for v in vids if "wrist" in v), ""),
           "dataset": A["paths"]["dataset"], "filter_log": A["paths"]["filter_log"], "eval_ui_verdict": (A.get("eval_ui") or {}).get("verdict"),
           "seconds": (A.get("eval_ui") or {}).get("seconds"), "frames": A.get("n_frames"),
           "auto_first_close": au.get("first_close_T4"), "auto_n_closes": au.get("n_closes"), "auto_empty_before_grasp": au.get("n_empty_before_first_grasp"),
           "auto_pan_rev_pre_close": pr.get("n_reversals"), "auto_pan_rev_whole": pw.get("n_reversals"),
           "auto_pan_max_past_target": None if pw.get("max_past_target_deg") is None else round(pw["max_past_target_deg"], 1),
           "auto_pan_min": None if pw.get("pan_min") is None else round(pw["pan_min"], 1),
           "auto_pan_max": None if pw.get("pan_max") is None else round(pw["pan_max"], 1),
           "auto_wrist_lost_segments": len(wr.get("lost_segments") or []) if wr else None, "auto_wrist_reacquired": wr.get("reacquired") if wr else None,
           "safety_stops": "; ".join(f"{s['rule']}@{s['tick']}" for s in A["safety_stops"]), "fault_events": "; ".join(f"{f['event']}:{f['kind']}" for f in A["fault_events"]),
           "console_ctrl_c": A["console_flags"].get("ctrl_c"),
           "end_ended_by": (A.get("end_state") or {}).get("ended_by"), "end_max_diff_from_start_deg": (A.get("end_state") or {}).get("max_abs_diff_deg"),
           "end_torque_left_on": (A.get("end_state") or {}).get("torque_left_on"),
           "auto_return_blocked_calls": (A.get("end_state") or {}).get("auto_return_blocked_calls"), **ans}
    new = not out.exists()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"\n저장: {out} (시행 {row['trial']}, revision {row['revision']})")
    es = A.get("end_state") or {}
    if es.get("max_abs_diff_deg") is None or es["max_abs_diff_deg"] > 5:
        print(f"팔이 시작 자세에서 {es.get('max_abs_diff_deg')}° 떨어진 자리에서 토크 유지 중 (자동 복귀 없음). 다음 시행 전에:")
        print(f"  python3 {S_DIR}/scripts/safe_home.py --run {run}     (또는 손으로 옮긴 뒤 gate.sh rest \"메모\")")
    if int(m["trial"]) == 1 and not (out.parent / "phase2_go.txt").exists():
        print("시행 1 (Phase 2) 확인 뒤 이상이 없으면: ~/so101_runs/main_k8/rft01_real_pilot/scripts/gate.sh go \"확인 메모\"  · 문제가 있으면: gate.sh stop \"이유\"")
    if ans["intervention"] != "none":
        print(f"안전 개입이 있었어요 — 다음 시행 전에 확인: gate.sh ack {m['trial']} \"메모\"  또는  gate.sh stop \"이유\"")


if __name__ == "__main__":
    sys.exit(main())
