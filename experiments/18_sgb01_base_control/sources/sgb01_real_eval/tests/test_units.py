"""CPU 단위 시험 (로봇 · 카메라 · GPU 없음): Pan 반전 · Wrist 재획득 규칙, record_trial 추가 전용 기록, run_trial 게이트.
출력 PASS/FAIL 줄, 마지막 ALL_PASS / SOME_FAIL. 임시 폴더만 쓴다 (실제 results/ 는 건드리지 않음).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

S_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S_DIR / "scripts"))
import trial_auto as TA  # noqa: E402

ok = True


def chk(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}", flush=True)


# U1 Pan 반전
s0, pe = 0.0, -35.0
mono = np.linspace(0, -36, 200)
r = TA.pan_reversals(mono, s0, pe)
chk("U1a_monotonic_no_reversal", r["n_reversals"] == 0, r["n_reversals"])
over = np.concatenate([np.linspace(0, -48, 100), np.linspace(-48, -32, 30), np.linspace(-32, -109, 200)])  # B1 모양
r = TA.pan_reversals(over, s0, pe)
chk("U1b_B1_shape_one_reversal", r["n_reversals"] == 1 and abs(r["events"][0]["back_deg"] - 16) < 0.5 and r["pan_min"] == -109,
    f"{r['n_reversals']} back={r['events'][0].get('back_deg') if r['events'] else None} past={r['max_past_target_deg']:.1f}")
noise = np.linspace(0, -36, 300) + 2.0 * np.sin(np.arange(300) / 3)
chk("U1c_small_wiggle_ignored", TA.pan_reversals(noise, s0, pe)["n_reversals"] == 0)
early = np.concatenate([np.linspace(0, -3, 20), np.linspace(-3, 6, 20), np.linspace(6, -35, 100)])  # 5° 진행 전 흔들림
chk("U1d_reversal_needs_min_travel", TA.pan_reversals(early, s0, pe)["n_reversals"] == 0)
chk("U1e_no_pe", TA.pan_reversals(mono, s0, None) is None)
pos = np.concatenate([np.linspace(0, 45, 100), np.linspace(45, 30, 50)])
r = TA.pan_reversals(pos, 0.0, 33.0)
chk("U1f_positive_direction", r["direction_to_target"] == "+" and r["n_reversals"] == 1, r["direction_to_target"])

# U2 Wrist 재획득 (표본 간격 STEP=3 frame, 30 fps)
idx = list(range(0, 300, 3))
vis = [True] * 20 + [False] * 15 + [True] * 65    # 15 표본 = 1.5 s 놓침 → 재획득
lost, reacq, seen = TA.wrist_segments(idx, vis)
chk("U2a_lost_then_reacquired", reacq and len(lost) == 1 and lost[0]["reacquired_i"] is not None, lost)
vis = [True] * 20 + [False] * 80
lost, reacq, seen = TA.wrist_segments(idx, vis)
chk("U2b_lost_no_reacquire", not reacq and len(lost) == 1 and lost[0]["reacquired_i"] is None, lost)
vis = [True] * 20 + [False] * 5 + [True] * 75     # 0.5 s 가림 = 놓침 아님
lost, reacq, seen = TA.wrist_segments(idx, vis)
chk("U2c_short_gap_not_lost", not lost, lost)
vis = [False] * 100
lost, reacq, seen = TA.wrist_segments(idx, vis)
chk("U2d_never_seen", not lost and not seen, (lost, seen))

# U3 record_trial: 추가 전용 · 중복 거부 · amend
tmp = Path(tempfile.mkdtemp(prefix="pilot_units_"))
try:
    run = tmp / "eval/rollouts/20261105_120000_1k_t01_ft_k3_0"
    run.mkdir(parents=True)
    rep = tmp / "reports" / run.name
    rep.mkdir(parents=True)
    auto = {"run_id": run.name, "manifest": {"trial": 1, "model": "ft", "model_name": "rft01_001000", "model_sha256": "620c", "code_sha256": {"a": "b"},
                                              "so101_boxpick_git": {"head": "490a5da"}, "plan_row": {"condition": "K3 0°", "label": "K3_0", "pair": "P1", "phase": "2"},
                                              "rerun_reason": None},
            "eval_ui": {"verdict": "P", "seconds": "20.1"}, "n_frames": 600, "start_joints": {"shoulder_pan": 1.0}, "cube": {"cube_x": -8.5},
            "paths": {"videos": ["dataset/videos/observation.images.front/x.mp4", "dataset/videos/observation.images.wrist/x.mp4"], "dataset": "d", "filter_log": "f"},
            "plan_check": ["놓인 곳 …"], "plan_check_warn": [], "safety_stops": [], "fault_events": [], "console_flags": {"ctrl_c": False},
            "auto": {"first_close_T4": "grasp", "n_closes": 1, "n_empty_before_first_grasp": 0, "pan_pre_first_close": {"n_reversals": 0},
                     "pan_whole": {"n_reversals": 0, "max_past_target_deg": 1.0, "pan_min": 0.0, "pan_max": 33.0}, "wrist": {"lost_segments": [], "reacquired": False}}}
    (rep / "trial_auto.json").write_text(json.dumps(auto))
    out = tmp / "results/trials.csv"
    ans = "first_grasp=y,empty_grasp=n,pan_reversal=n,wrist_reacquire=na,final_success=y,intervention=none,intervention_reason=,memo=test"
    cmd = [sys.executable, str(S_DIR / "scripts/record_trial.py"), str(run), "--out", str(out), "--reports-root", str(tmp / "reports"), "--answers", ans]
    r1 = subprocess.run(cmd, capture_output=True, text=True)
    r2 = subprocess.run(cmd, capture_output=True, text=True)
    r3 = subprocess.run(cmd + ["--amend", "오타"], capture_output=True, text=True)
    rows = out.read_text().splitlines()
    chk("U3a_first_write", r1.returncode == 0 and len(rows) >= 2, r1.stderr[-200:])
    chk("U3b_duplicate_refused", r2.returncode != 0 and "이미 기록됨" in (r2.stderr + r2.stdout), (r2.stderr + r2.stdout)[-120:])
    chk("U3c_amend_appends_revision2", r3.returncode == 0 and len(out.read_text().splitlines()) == 3 and ",2," in out.read_text().splitlines()[2],
        out.read_text().splitlines()[-1][:80])
    bad = subprocess.run(cmd[:-1] + [ans.replace("first_grasp=y", "first_grasp=maybe")] + ["--amend", "x"], capture_output=True, text=True)
    chk("U3d_invalid_answer_refused", bad.returncode != 0)

    # U4 run_trial 게이트 (GATE_ONLY=1, PILOT_DIR = 임시 사본; eval_ui · 로봇 없음)
    P = tmp / "pilot"
    (P / "logs").mkdir(parents=True)
    shutil.copytree(S_DIR / "config", P / "config")
    shutil.copy(S_DIR / "logs/c01_verify_models.json", P / "logs/c01_verify_models.json")
    (P / "results").mkdir()

    def gate(n, extra=None):
        env = dict(os.environ, PILOT_DIR=str(P), GATE_ONLY="1", **(extra or {}))
        r = subprocess.run([str(S_DIR / "scripts/run_trial.sh"), str(n)], capture_output=True, text=True, env=env)
        return [ln for ln in r.stdout.splitlines() if "게이트:" in ln][0] if "게이트:" in r.stdout else r.stdout + r.stderr

    g = gate(1)
    chk("U4a_trial1_open", "게이트: OK" in g, g)
    g = gate(2)
    chk("U4b_trial2_needs_trial1_and_go", "시행 1 결과" in g and "Phase 2" in g, g[:200])
    shutil.copy(out, P / "results/trials.csv")
    g = gate(2)
    chk("U4c_trial2_needs_go_only", "Phase 2" in g and "시행 1 결과" not in g, g[:200])
    (P / "results/phase2_go.txt").write_text("GO test")
    g = gate(2)
    chk("U4d_trial2_open_after_go", "게이트: OK" in g, g)
    g = gate(1)
    chk("U4e_recorded_trial_needs_rerun", "이미 기록됨" in g, g[:160])
    g = gate(1, {"RERUN": "test"})
    chk("U4f_rerun_reason_opens", "게이트: OK" in g, g)
    t = (P / "results/trials.csv").read_text().replace(",none,", ",r2_safety_stop,")
    (P / "results/trials.csv").write_text(t)
    g = gate(2)
    chk("U4g_intervention_needs_ack", "안전 개입" in g, g[:200])
    (P / "results/ack_trial01.txt").write_text("ACK")
    chk("U4h_ack_opens", "게이트: OK" in gate(2))
    (P / "results/STOP").write_text("STOP test")
    chk("U4i_stop_blocks", "STOP" in gate(2))
    c = json.loads((P / "logs/c01_verify_models.json").read_text())
    c["checks"]["M5_normalizer_values_identical"]["pass"] = False
    (P / "logs/c01_verify_models.json").write_text(json.dumps(c))
    (P / "results/STOP").unlink()
    chk("U4j_model_check_fail_blocks", "M5" in gate(2))
    c["checks"]["M5_normalizer_values_identical"]["pass"] = True
    (P / "logs/c01_verify_models.json").write_text(json.dumps(c))
    # U5 (v2) 직전 run 의 끝 상태 게이트
    run_id = "20261105_120000_1k_t01_ft_k3_0"
    (P / "results/run_ledger.csv").write_text("trial,model,model_name,model_sha256,tag,run,launched,ended,eval_ui_exit,rerun_reason,manifest\n"
                                              f"1,ft,rft01_001000,620c,t01_ft_k3_0,{run_id},a,b,0,\"\",m.json\n")
    rd = P / "eval/rollouts" / run_id
    rd.mkdir(parents=True)
    g = gate(2)
    chk("U5a_missing_end_state_blocks", "end_state.json 없음" in g, g[:160])
    (rd / "end_state.json").write_text(json.dumps({"max_abs_diff_deg": 41.0, "torque_left_on": True}))
    g = gate(2)
    chk("U5b_far_from_start_blocks", "41.0" in g and "safe_home" in g, g[:200])
    (P / "results/home_logs").mkdir(parents=True)
    (P / f"results/home_logs/{run_id}_x.json").write_text(json.dumps({"move": {"ok": False}}))
    chk("U5c_failed_home_still_blocks", "safe_home" in gate(2))
    (P / f"results/home_logs/{run_id}_y.json").write_text(json.dumps({"move": {"ok": True}}))
    chk("U5d_successful_home_opens", "게이트: OK" in gate(2), gate(2))
    for f in (P / "results/home_logs").glob("*"):
        f.unlink()
    env = dict(os.environ)
    rg = subprocess.run(["bash", "-c", f"sed 's#^S=.*results$#S={P}/results#' {S_DIR}/scripts/gate.sh > {tmp}/gate_t.sh && bash {tmp}/gate_t.sh rest '손으로 둠'"],
                        capture_output=True, text=True)
    chk("U5e_gate_rest_writes_for_last_run", (P / f"results/rest_{run_id}.txt").exists() and "게이트: OK" in gate(2), rg.stdout + rg.stderr)
    (rd / "end_state.json").write_text(json.dumps({"max_abs_diff_deg": 1.2, "torque_left_on": True}))
    (P / f"results/rest_{run_id}.txt").unlink()
    chk("U5f_near_start_opens", "게이트: OK" in gate(2))
    r = subprocess.run([str(S_DIR / "scripts/run_trial.sh"), "2"], capture_output=True, text=True, env=dict(os.environ, PILOT_DIR=str(P)))
    chk("U4k_pilot_dir_without_gate_only_refused", r.returncode != 0 and "시험용" in r.stdout, r.stdout[-120:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("ALL_PASS" if ok else "SOME_FAIL")
sys.exit(0 if ok else 1)
