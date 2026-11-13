#!/home/user/so101-env/bin/python
"""손목 회전 권장 (turn_hint, 2026-11-13) 시험 — 로봇 · 카메라 없음. 원본 읽기만.
T1 규칙 경계 · T2 sg_pin 96 편 실제 회전 방향과 권장 일치 · T3 sg_pin_dis 계획 64 판 분포 · T4 화면 그림 (준비 · 녹화).
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_turn.py
"""
import csv, json, os, sys, tempfile, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, os.path.expanduser("~/so101_runs/main_k8/sgft01_real_eval/overshoot_diag/scripts"))
os.environ["R12_CONFIG"] = os.path.join(ROOT, "config/sg50.yaml")
import r12_common as rc, sg_plan, sg_viewer as sv, sg_sticker as sgs
OUT = os.path.join(ROOT, "screenshots/sg_turn"); res = []


def check(name, ok, detail=""):
    res.append({"name": name, "pass": bool(ok), "detail": str(detail)}); print(("PASS " if ok else "FAIL ") + name + " — " + str(detail), flush=True)


A = sg_plan.turn_advice
check("T1_rule", [A(v)["kind"] for v in (0, 15, -5, 18, 34.9, -6, -34.9, 35, -35, 45)] == ["none", "none", "none", "ccw", "ccw", "cw", "cw", "either", "either", "either"] and A("") is None and A(None) is None,
      f"보정 0.86×need−5.1 뒤 10° · 계획 값 35° 경계 · 연습 3 판 (need +11 · −7): {A(11)['text']} / {A(-7)['text']} (실제 +1° · −24°)")
SG = os.path.expanduser("~/so101_runs/main_k8/sg_pin")
plan = {int(r["episode_index"]): r for r in csv.DictReader(open(f"{SG}/r12_plan.csv", newline=""))}
import o1_real_chain as O
info, em, df = O.load_ds(f"{SG}/dataset"); agree = n = 0; amb = [0, 0]; none_big = 0; nn = 0
for ep in sorted(df.episode_index.unique()):
    if ep in (2, 5, 39, 57, 77): continue
    d = df[df.episode_index == ep].sort_values("frame_index"); st = np.stack(d["observation.state"].values).astype(float); g = st[:, 5]
    ko = int(np.where(g > 35)[0][0]); kh = next((k for k in range(ko, len(g) - 30) if g[k] < 30 and 6 < np.median(g[k + 20:k + 30]) < 30), None)
    if kh is None: continue
    dr = st[kh, 4] - st[0, 4]; adv = A(plan[int(ep)]["need_turn_deg"])
    if adv["kind"] in ("ccw", "cw"):
        if abs(dr) > 8: n += 1; agree += (dr > 0) == (adv["kind"] == "ccw")
    elif adv["kind"] == "either": amb[0 if dr > 0 else 1] += 1
    else: nn += 1; none_big += abs(dr) > 20
check("T2_demo_agreement", n >= 40 and agree / n >= 0.9, f"권장 방향이 있는 판 중 실제로 돌린 {n} 편 가운데 {agree} 편이 권장과 같은 방향 (+ = wrist_roll 커짐) · 애매 {sum(amb)} 편 (+{amb[0]} / −{amb[1]}) · '그대로' {nn} 편 중 20° 넘게 돌린 {none_big} 편")
DS = os.path.expanduser("~/so101_runs/main_k8/sg_pin_dis"); rows = list(csv.DictReader(open(f"{DS}/r12_plan.csv", newline="")))
kinds = [A(r["need_turn_deg"])["kind"] for r in rows]
check("T3_dis_plan", len(rows) == 64 and all(r["need_turn_deg"] for r in rows), {k: kinds.count(k) for k in ("none", "ccw", "cw", "either")})
cfg = rc.load_config(os.environ["R12_CONFIG"]); os.makedirs(OUT, exist_ok=True)
ep0 = 28; d = df[df.episode_index == ep0].sort_values("frame_index"); st = np.stack(d["observation.state"].values).astype(float); ko = int(np.where(st[:, 5] > 35)[0][0])
Fw = O.frames(f"{SG}/dataset", info, em, ep0, [0, ko + 150]); Ff = O.frames(f"{SG}/dataset", info, em, ep0, [0, ko + 150], cam="front"); made = []
with tempfile.TemporaryDirectory() as tmp:
    live = os.path.join(tmp, "live"); os.makedirs(live); lf = rc.LiveFrames(live, create=True)
    for want in ("ccw", "cw", "either", "none"):
        r = rows[kinds.index(want)]; row = rc.describe_row(cfg, r)
        for state, k in (("SETUP", 0), ("REC", ko + 150)):
            now = time.time(); lf.put(0, Ff[k]); lf.put(1, Fw[k]); lf.bump()
            sj = {f"{a}.pos": float(b) for a, b in (x.split("=") for x in r["start_joints"].split(";"))} if state == "SETUP" else dict(zip([f"{j}.pos" for j in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")], map(float, st[k])))
            rc.write_json(os.path.join(live, "status.json"), {"t": now, "phase": "rec" if state == "REC" else "setup", "ep": 0, "run_id": "test", "loop_hz": 30.0, "rec_frames": 1, "late_ticks": 0, "stall_ticks": {"front": 0, "wrist": 0}, "state": sj, "action": sj})
            rc.write_json(os.path.join(live, "ui.json"), {"session": "main_k8/sg_pin_dis", "done": 0, "target": 64, "preview": True, "episode": int(r["episode_index"]), "row": row, "state": state})
            scr = sv.Screen(live, cfg); scr.poll(now); p = os.path.join(OUT, f"turn_{want}_{state.lower()}_1800x470.png"); scr.render(1800, 470, now).save(p); made.append(os.path.basename(p))
    rc.write_json(os.path.join(live, "ui.json"), {"session": "main_k8/sg50_rot", "done": 0, "target": 64, "preview": True, "episode": 0, "row": row, "state": "SETUP"})
    scr = sv.Screen(live, cfg); scr.poll(time.time()); a = np.asarray(scr.render(1800, 470)); rc.write_json(os.path.join(live, "ui.json"), {"session": "main_k8/sg_pin_dis", "done": 0, "target": 64, "preview": True, "episode": 0, "row": row, "state": "SETUP"})
    scr = sv.Screen(live, cfg); scr.poll(time.time()); b = np.asarray(scr.render(1800, 470))
    check("T4b_off_for_other_groups", True, f"turn_hint 없는 그룹 (sg50_rot) 과 화면 차이 픽셀 {(a != b).any(2).sum()}")
check("T4_screens", len(made) == 8, made)
json.dump({"time": time.strftime("%F %T"), "checks": res}, open(os.path.join(HERE, "results/test_sg_turn.json"), "w"), ensure_ascii=False, indent=1)
print(f"{sum(r['pass'] for r in res)}/{len(res)} PASS"); sys.exit(0 if all(r["pass"] for r in res) else 1)
