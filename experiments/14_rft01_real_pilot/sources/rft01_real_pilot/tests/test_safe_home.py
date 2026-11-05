"""safe_home.py 시험 (CPU, 하드웨어 없음): 가짜 bus 객체로 session() · move() 를 그대로 부른다. 실제 포트는 열지 않는다.
PASS/FAIL 줄, 마지막 ALL_PASS / SOME_FAIL.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

S_DIR = Path(__file__).resolve().parents[1]
os.environ["SAFE_HOME_NO_REEXEC"] = "1"
sys.path.insert(0, str(S_DIR / "scripts"))
import safe_home as SH  # noqa: E402

ARM, ALL = SH.ARM, SH.ALL
REST = {"shoulder_pan": 4.3, "shoulder_lift": -101.0, "elbow_flex": 95.8, "wrist_flex": 66.6, "wrist_roll": 3.9, "gripper": 0.8}
END = {"shoulder_pan": -33.0, "shoulder_lift": -20.0, "elbow_flex": 30.0, "wrist_flex": 70.0, "wrist_roll": 5.0, "gripper": 12.0}
LIM = {"shoulder_pan": (-110.2, 110.2), "shoulder_lift": (-103.7, 103.7), "elbow_flex": (-96.7, 96.7), "wrist_flex": (-102.1, 102.1),
       "wrist_roll": (-180, 180), "gripper": (0, 100)}
ok = True


def chk(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}", flush=True)


class Bus:
    def __init__(self, present, torque=1, blocked=None):
        self.present, self.goal = dict(present), dict(present)
        self.torque = {j: torque for j in ALL}
        self.writes, self.disabled, self.blocked = [], 0, blocked or {}

    def sync_read(self, name, normalize=True):
        return dict({"Present_Position": self.present, "Goal_Position": self.goal, "Torque_Enable": self.torque}[name])

    def sync_write(self, name, vals):
        assert name == "Goal_Position"
        self.writes.append(dict(vals))
        self.goal.update(vals)

    def step(self):
        for j in ALL:
            if j in self.blocked:
                self.present[j] = self.blocked[j]
            elif self.torque[j]:
                self.present[j] += 0.5 * (self.goal[j] - self.present[j])

    def disable_torque(self):
        self.disabled += 1
        self.torque = {j: 0 for j in ALL}


def es(end=END):
    return {"initial_position": {f"{j}.pos": v for j, v in REST.items()}, "end_present_arm": {j: end[j] for j in ARM}}


def run(bus, answers, end_state=None, mode="home", others="", interrupt=None):
    it = iter(answers)
    return SH.session(bus, end_state or es(), mode, inp=lambda p: next(it, ""), sleep=lambda s: bus.step(), interrupt=interrupt, limits=LIM, others=others)


b = Bus(END)
L = run(b, ["no"])
chk("SH1_no_home_word_no_move", not b.writes and b.disabled == 0 and L["choice"] == "no", f"writes={len(b.writes)}")
b = Bus(END)
b.torque["elbow_flex"] = 0
L = run(b, ["home"])
chk("SH2_torque_off_refused", not b.writes and L["choice"] == "refused_checks", [c["name"] for c in L["checks"] if not c["pass"]])
b = Bus(END)
b.goal["shoulder_lift"] += 6
L = run(b, ["home"])
chk("SH3_goal_gap_refused", not b.writes and L["choice"] == "refused_checks", [c["name"] for c in L["checks"] if not c["pass"]])
moved = dict(END, shoulder_pan=END["shoulder_pan"] + 8)
b = Bus(moved)
L = run(b, ["home"])
chk("SH4_moved_since_end_refused", not b.writes and any(c["name"] == "H6_matches_end_state" and not c["pass"] for c in L["checks"]))
p102 = dict(END, shoulder_pan=102.0)
b = Bus(p102)
L = run(b, ["home"], end_state=es(p102))
chk("SH5_pan_over_100_refused", not b.writes and any(c["name"] == "H4_pan_and_limits" and not c["pass"] for c in L["checks"]))
bad_t = es()
bad_t["initial_position"]["shoulder_lift.pos"] = -40.0
b = Bus(END)
L = run(b, ["home"], end_state=bad_t)
chk("SH6_target_not_rest_refused", not b.writes and any(c["name"] == "H5_target_is_rest" and not c["pass"] for c in L["checks"]))
b = Bus(END)
L = run(b, ["home"], others="1234 python3 scripts/eval_ui.py --child")
chk("SH7_other_process_refused", not b.writes and any(c["name"] == "H1_no_other_process" and not c["pass"] for c in L["checks"]))
b = Bus(END)
L = run(b, ["home", ""])
R = L["move"] or {}
fin = R.get("final") or {}
chk("SH8_home_arrives_slow_no_gripper_torque_kept",
    R.get("ok") and max(abs(fin[j] - REST[j]) for j in ARM) <= 3.0 and R["max_step_deg"] <= SH.SPEED / SH.FPS + 1e-6
    and all("gripper" not in w for w in b.writes) and b.disabled == 0 and not L["released"],
    f"reason={R.get('reason')} ticks={R.get('ticks')} planned={R.get('duration_planned_s'):.1f}s max_step={R.get('max_step_deg'):.3f} writes={len(b.writes)}")
b = Bus(END)
L = run(b, ["home", "release"])
chk("SH9_release_after_home_only_if_typed", L["released"] and b.disabled == 1)
b = Bus(END, blocked={"elbow_flex": END["elbow_flex"]})
L = run(b, ["home"])
R = L["move"] or {}
last = b.writes[-1] if b.writes else {}
chk("SH10_stall_halts_and_holds", not R.get("ok") and str(R.get("reason", "")).startswith("tracking_elbow_flex") and R.get("halt_hold")
    and abs(last.get("elbow_flex", 1e9) - b.present["elbow_flex"]) < 1e-6 and b.disabled == 0,
    f"reason={R.get('reason')} ticks={R.get('ticks')} last write elbow={last.get('elbow_flex')}")
b = Bus(END)
L = run(b, ["home"], interrupt=lambda k: k == 10)
R = L["move"] or {}
last = b.writes[-1] if b.writes else {}
chk("SH11_ctrl_c_halts_and_holds", R.get("reason") == "ctrl_c" and R.get("ticks") == 10 and all(abs(last[j] - b.present[j]) < 1e-6 for j in ARM),
    f"reason={R.get('reason')} ticks={R.get('ticks')}")
b = Bus(END)
L = run(b, ["release", "no"], mode="release")
chk("SH12a_release_not_rest_needs_support_word", b.disabled == 0 and not b.writes)
b = Bus(END)
L = run(b, ["release", "받쳤음"], mode="release")
chk("SH12b_release_with_support_word", b.disabled == 1 and not b.writes)
b = Bus(REST)
L = run(b, ["release"], mode="release", end_state=es(REST))
chk("SH12c_release_at_rest_single_word", b.disabled == 1 and not b.writes)

# SH16 (11-05) --auto: 점검 PASS → 입력 없이 이동 · 토크 유지 / 점검 FAIL → 이동 없음. H7 은 167° 이동 허용 (t02 끝 자세)
far = {"shoulder_pan": 32.3, "shoulder_lift": 65.9, "elbow_flex": -62.7, "wrist_flex": 92.4, "wrist_roll": -46.3, "gripper": 10.0}
b = Bus(far)
L = SH.session(b, es(far), "home", inp=SH.auto_inp, sleep=lambda s: b.step(), limits=LIM)
chk("SH16a_auto_moves_far_keeps_torque", (L["move"] or {}).get("ok") and b.disabled == 0 and not L["released"]
    and all(c["pass"] for c in L["checks"]), [c["name"] for c in L["checks"] if not c["pass"]])
b = Bus(END)
b.torque["wrist_flex"] = 0
L = SH.session(b, es(), "home", inp=SH.auto_inp, sleep=lambda s: b.step(), limits=LIM)
chk("SH16b_auto_refuses_on_failed_check", not b.writes and L["choice"] == "refused_checks")
b = Bus(END)
L = SH.session(b, es(), "home", inp=SH.auto_inp, sleep=lambda s: b.step(), limits=LIM, others="999 python3 scripts/eval_ui.py --child")
chk("SH16c_auto_refuses_other_process", not b.writes)

with tempfile.TemporaryDirectory() as td:
    run_dir = Path(td) / "20261105_000000_1k_t01_ft_k3_0"
    run_dir.mkdir()
    (run_dir / "end_state.json").write_text(json.dumps({**es(), "ended_by": "episode_end_or_user_next", "max_abs_diff_deg": 81.0, "torque_left_on": True}))
    r = subprocess.run([str(Path.home() / "so101-env/bin/python"), str(S_DIR / "scripts/safe_home.py"), "--run", str(run_dir), "--check"],
                       capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    chk("SH13_check_mode_no_hardware", r.returncode == 0 and "CHECK_ONLY" in r.stdout and not list((S_DIR / "results/home_logs").glob(f"{run_dir.name}_*"))
        if (S_DIR / "results/home_logs").exists() else r.returncode == 0 and "CHECK_ONLY" in r.stdout, r.stdout[-160:] + r.stderr[-200:])
    r = subprocess.run([str(Path.home() / "so101-env/bin/python"), str(S_DIR / "scripts/safe_home.py"), "--run", str(Path(td) / "missing")],
                       capture_output=True, text=True)
    chk("SH14_no_end_state_refuses_before_connect", r.returncode != 0 and "end_state.json 없음" in (r.stdout + r.stderr))

src = (S_DIR / "scripts/safe_home.py").read_text()
code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#") and '"""' not in ln)
body = src.split('"""', 2)[2]
connects = re.findall(r"[\w\.]+\.connect\(", body)
chk("SH15_never_robot_connect_or_configure", connects == ["bus.connect("] and "configure(" not in body.replace("configure() 는 부르지 않음", ""),
    f"connect calls={connects}")
print("ALL_PASS" if ok else "SOME_FAIL")
sys.exit(0 if ok else 1)
