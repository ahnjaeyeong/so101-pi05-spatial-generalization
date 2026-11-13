#!/home/user/so101-env/bin/python
"""2026-11-09 sg50_rot (큐브 각도 · 계획 시작 자세 · 손목 절차 안내) 시험 (로봇 · 카메라 없음, 읽기만).

1 계획: 80 줄 · 각도 0/L30/R30/45 각 20 · 자리마다 두 판 다른 각도 · 같은 각도 3 연속 없음 · 같은 영역 연달아 없음 ·
  시작 팬 |팬| ≤ abs_max · 팔 접힘 fold_mix 비율 · 시작 관절 = start_folds 값 (녹화값) · 기존 그룹 (sg50_pilot3) 순서 · 칸 그대로.
2 준비 단계 안내: 실제 예비3 첫 프레임 (S0) ↔ 계획 시작 자세 → '시작 자세를 맞추세요' · 관절값을 계획 값으로 바꾼 [합성] 상태 → '맞음'.
3 녹화 중 절차: 예비3 ep 한 판을 닫기까지 재생 (관절값 · 손목 영상 실제), 계획 줄 = 그 판 자리 + 각도 L30 · 시작 자세 (표시용) →
  단계가 ① 숄더팬 (이미 맞으면 건너뜀) → ② 그리퍼 → ③ 각도 → 노란 프레임 (그 판 큐브가 실제로 지나간 자리) → 주황 프레임 순서로만 나아가는지.
4 화면 그림: 단계마다 · 준비 단계 → screenshots/sg50_rot/*.png.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_rot.py
"""
import collections
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
CFG = os.path.join(ROOT, "config", "sg50.yaml")
os.environ["R12_CONFIG"] = CFG
OUT = os.path.join(ROOT, "screenshots", "sg50_rot")
P3 = os.path.expanduser("~/so101_runs/practice/sg50_pilot3")
NAMES = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
RES = []


def on_phase():
    """깜빡임 (초당 1.5 번) 이 켜진 순간에 그림을 찍음."""
    while int(time.time() * 3) % 2:
        time.sleep(0.02)


def check(name, ok, detail=""):
    RES.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True)


def main():
    import r12_common as rc
    import sg_phase
    import sg_plan as sp
    import sg_sticker as sgs
    import sg_viewer as sv
    from test_sg_approach import P3Data

    cfg = rc.load_config(CFG)
    s50 = cfg["sg50"]
    g = rc.group_of(cfg, "sg50_rot")
    rows = sp.make_rows(cfg, "sg50_rot")
    ang = [r["angle"] for r in rows]
    check("plan_rows_angles", len(rows) == 80 and collections.Counter(ang) == {"0": 20, "L30": 20, "R30": 20, "45": 20}, f"{collections.Counter(ang)}")
    per = collections.defaultdict(list)
    for r in rows:
        per[r["position"]].append(r["angle"])
    check("plan_same_spot_diff_angle", all(len(v) == len(set(v)) == 2 for v in per.values()), f"자리 {len(per)}")
    check("plan_no_3_same_angle", sum(a == b == c for a, b, c in zip(ang, ang[1:], ang[2:])) == 0)
    check("plan_no_same_area_next", sum(a["position"][:2] == b["position"][:2] for a, b in zip(rows, rows[1:])) == 0)
    pans = [float(r["start_joints"].split(";")[0].split("=")[1]) for r in rows]
    check("plan_start_pan_limits", max(abs(p) for p in pans) <= float(s50["start_pan"]["abs_max"]), f"범위 {min(pans):+.1f}…{max(pans):+.1f}")
    diff = [abs(p - float(r["pan_target_deg"])) for p, r in zip(pans, rows)]
    check("plan_start_pan_far", np.median(diff) >= 30 and min(diff) >= 29.9, f"큐브 방향과 차 중앙 {np.median(diff):.0f}° · 최소 {min(diff):.0f}°")
    fc = collections.Counter(r["start_fold"] for r in rows)
    check("plan_folds", fc == sp.approach_counts(g["fold_mix"], 80), f"{dict(sorted(fc.items()))}")
    okj = all(all(abs(float(v) - s50["start_folds"][r["start_fold"]]["joints"][k]) < 1e-6 for k, v in (x.split("=") for x in r["start_joints"].split(";")) if k != "shoulder_pan")
              for r in rows)
    check("plan_fold_joints_from_config", okj)
    check("plan_scenario", all(r["scenario_id"] == "SG-PLAN" for r in rows))
    t45 = [abs(float(r["need_turn_deg"])) for r in rows if r["angle"] == "45"]
    check("plan_45_shorter_turn", max(t45) <= 45.0, f"45° 판 필요 회전 |최대| {max(t45):.1f}° (회전량이 적은 쪽)")
    wd = collections.Counter(r["wp_dir"] for r in rows)
    tref0 = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    fit = all(sp.waypoint_fit(tref0, s50["waypoint"], float(r["wp_u"]), float(r["wp_v"]), float(r["wp_size"])) for r in rows)
    wmix = s50["waypoint"].get("dir_mix")
    exp_w = sp.approach_counts({str(int(float(k))): v for k, v in wmix.items()}, 80) if wmix else None
    tw = [r["wp_dir"] for r in rows]
    dn = ["d" if sp._wp_band(x) == "down" else "u" for x in tw]
    runmax = max(len(x) for x in "".join(dn).replace("u", " ").split() + [""]) if dn else 0
    check("plan_waypoints", dict(wd) == exp_w and fit and sum(a == b for a, b in zip(tw, tw[1:])) == 0 and runmax <= 3
          and all(abs(tw[:40].count(k) - tw[40:].count(k)) <= 2 for k in exp_w),
          f"방향 {dict(wd)} (카메라 쪽 2 : 로봇 쪽 1) · 같은 방향 연달아 없음 · 카메라 쪽 연속 최대 {runmax} · 앞/뒤 절반 아래 {tw[:40].count('90')}/{tw[40:].count('90')} · 모두 화면 안 (아래 잘림 허용) · "
          f"크기 {min(float(r['wp_size']) for r in rows):.2f}–{max(float(r['wp_size']) for r in rows):.2f}")
    old = sp.make_rows(cfg, "sg50_pilot3")
    cur = rc.read_plan(P3)
    check("old_group_unchanged", [r["position"] for r in old] == [r["position"] for r in cur[:40]] and all(r["angle"] == "0" and not r["start_joints"] for r in old))

    # 2 · 3 화면
    D = P3Data()
    ep = 30   # 높은 곳 (크기 0.65) 에서 회전을 맞춘 장면이 있는 판 — 노란 프레임 단계를 실제 영상으로 보려고
    st, ac = D.ep(ep)
    idx = sg_phase.analyze(st, ac, 30)["_idx"]
    ci = idx["close"]
    p3row = {int(r["episode_index"]): r for r in cur}[ep]
    rrow = dict(next(r for r in rows if r["angle"] == "L30"))
    rrow.update(position=p3row["position"], cube_xy_cm=p3row["cube_xy_cm"], pan_target_deg=p3row["pan_target_deg"])
    seq = list(range(0, ci + 1, 3)) + [ci - 3, ci - 2, ci - 1]
    W = {}
    for k0 in range(0, len(seq), 60):
        chunk = seq[k0:k0 + 60]
        W.update({k: v for k, v in D.frames(ep, chunk, "wrist").items()})
    # 노란 프레임 = 이 판에서 큐브가 실제로 지나간 자리 (그리퍼 연 뒤, 회전 맞음 · 크기 < 0.9 · 화면 안) — 그래야 실제 영상으로 단계가 끝까지 감
    tref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    Pp = sgs.load_params()
    wpk = None
    for k in [x for x in seq if idx["open"] < x < ci - 30]:
        c = sgs.target_compare(sgs.detect(W[k], Pp), tref)
        if c and abs(c["dangle"]) <= 2 and c["size"] < 0.9 and not c["edge"] and (wpk is None or c["size"] < wpk[1]["size"]) and sp.waypoint_fit(tref, s50["waypoint"], tref["u"] + c["du"], tref["v"] + c["dv"], c["size"]):
            wpk = (k, c)
    if wpk:
        k, c = wpk
        rrow.update(wp_dir="test", wp_u=f"{tref['u'] + c['du']:.3f}", wp_v=f"{tref['v'] + c['dv']:.3f}", wp_size=f"{c['size']:.2f}")
    check("waypoint_from_replay", wpk is not None, f"노란 프레임 = ep{ep} 프레임 {wpk and wpk[0]} 큐브 (du {wpk and wpk[1]['du']} · dv {wpk and wpk[1]['dv']} · 크기 {wpk and wpk[1]['size']})")
    row = rc.describe_row(cfg, rrow)
    Fk = sorted(set([0, idx["open"], ci - 3]))
    F = D.frames(ep, Fk, "front")
    os.makedirs(OUT, exist_ok=True)
    P = sgs.load_params()
    made = []
    with tempfile.TemporaryDirectory() as tmp:
        live = os.path.join(tmp, "live")
        os.makedirs(live)
        lf = rc.LiveFrames(live, create=True)

        def put(fk, wk, state, ui, now):
            lf.put(0, F[min(Fk, key=lambda x: abs(x - fk))]), lf.put(1, W[wk]), lf.bump()
            rc.write_json(os.path.join(live, "status.json"), {"t": now, "phase": "rec" if ui["state"] == "REC" else "setup", "ep": 0, "run_id": "test",
                                                              "loop_hz": 30.0, "rec_frames": 1, "late_ticks": 0, "stall_ticks": {"front": 0, "wrist": 0},
                                                              "state": state, "action": state})
            rc.write_json(os.path.join(live, "ui.json"), ui)

        base = {"session": "main_k8/sg50_rot", "done": 0, "target": 80, "preview": True, "episode": 0, "row": row}
        scr = sv.Screen(live, cfg)
        scr.P = P
        t0 = time.time()
        s_real = dict(zip(NAMES, [float(x) for x in st[0]]))
        put(0, 0, s_real, {**base, "state": "SETUP"}, t0)
        scr.poll(t0)
        a = scr.start_ps
        on_phase()
        scr.render(1800, 470, t0).save(os.path.join(OUT, "rot_setup_mismatch_1800x470.png"))
        sj = {k: float(v) for k, v in (x.split("=") for x in rrow["start_joints"].split(";"))}
        s_plan = {f"{k}.pos": v for k, v in sj.items()}
        put(0, 0, s_plan, {**base, "state": "SETUP"}, t0 + 0.1)
        scr.poll(t0 + 0.1)
        b = scr.start_ps
        on_phase()
        scr.render(1800, 470, t0 + 0.1).save(os.path.join(OUT, "rot_setup_match_synthetic_1800x470.png"))
        made += ["rot_setup_mismatch_1800x470.png", "rot_setup_match_synthetic_1800x470.png"]
        check("setup_banner", a is not None and not a["all"] and b is not None and b["all"], f"S0 → '{a and a['sub']}' · 계획 값 [합성] → '{b and b['title']}'")
        # 녹화 중
        put(0, 0, s_real, {**base, "state": "REC"}, t0 + 0.2)
        scr.poll(t0 + 0.2)
        steps, shots = [], {}
        tt = t0 + 0.3
        for k in seq:
            stt = dict(zip(NAMES, [float(x) for x in st[k]]))
            put(k, k, stt, {**base, "state": "REC"}, tt)
            scr.poll(tt)
            pr = scr.proc
            steps.append(pr["step"] if pr else None)
            if pr and pr["step"] not in shots:
                shots[pr["step"]] = k
                fn = f"rot_rec_step{pr['step']}_1800x470.png"
                on_phase()
                scr.render(1800, 470, tt).save(os.path.join(OUT, fn))
                made.append(fn)
            tt += 0.1
        s_ = [x for x in steps if x is not None]
        first = [s_.index(i) if i in s_ else None for i in range(6)]
        k2 = next((i for i, x in enumerate(s_) if x >= 2), None)
        mono12 = k2 is not None and all(x >= 2 for x in s_[k2:])   # ②까지 지나면 ①②로 돌아가지 않음 (맞은 단계는 건너뜀)
        i3 = s_.index(3) if 3 in s_ else None
        after3 = s_[i3:] if i3 is not None else []
        check("rec_steps_order", s_ and s_[0] in (0, 1) and i3 is not None and 4 in after3 and mono12 and all(x >= 2 for x in after3),
              f"단계 처음 나온 프레임 순서 {first} · 마지막 {s_[-1]} · 나온 단계 {sorted(set(s_))} (예비3 ep{ep}, 큐브는 0° — 각도 · 노랑 단계는 실제 영상 기준)")
        scr.debug = True
        scr.render(1400, 860, tt).save(os.path.join(OUT, "rot_rec_debug_1400x860.png"))
        scr.debug = False
        # 화면 예시만 (판정 없음): 실제 계획 노란 프레임 (위 · 오른쪽 · 아래) — 준비 단계, 예비3 첫 손목 프레임
        for dd in ("270", "90"):
            pr_ = dict(next(r for r in rows if r["wp_dir"] == dd))
            pr_.update(position=p3row["position"], cube_xy_cm=p3row["cube_xy_cm"], pan_target_deg=p3row["pan_target_deg"])
            k_ = max(x for x in seq if x < ci - 30)
            put(k_, k_, dict(zip(NAMES, [float(x) for x in st[k_]])), {**base, "state": "SETUP", "row": rc.describe_row(cfg, pr_)}, tt + 1)
            scr2 = sv.Screen(live, cfg)
            scr2.P = P
            scr2.poll(tt + 1)
            while int(time.time() * 3) % 2 == 0:   # 깜빡임 꺼진 순간 (노란 점선이 잘 보이게)
                time.sleep(0.02)
            fn = f"rot_waypoint_dir{dd}_setup_1800x470.png"
            scr2.render(1800, 470, tt + 1).save(os.path.join(OUT, fn))
            made.append(fn)
        made.append("rot_rec_debug_1400x860.png")
    # 노랑 먼저 (2026-11-10 사용자 "노란색큐브만 먼저 띄워줄 수 있어?"): 노랑을 지나기 전 = 주황 윤곽 안 그림, 지난 뒤 = 그림
    from PIL import Image as _Im
    tref_y = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    wref_y = sv.waypoint_ref(cfg, next(r for r in rows if r["wp_dir"] == "270"), tref_y)
    blank = _Im.new("RGB", (640, 480), (128, 128, 128))
    cnt = lambda im, col: int((np.abs(np.asarray(im).astype(int) - np.array(col)).sum(2) == 0).sum())  # noqa: E731
    im_before = sv.draw_wrist(blank, None, [tref_y], 1.0, text=False, waypoint=wref_y)
    im_after = sv.draw_wrist(blank, None, [tref_y], 1.0, text=False, waypoint=None)
    ob, oa, yb = cnt(im_before, sv.C_TGT_GUIDE), cnt(im_after, sv.C_TGT_GUIDE), cnt(im_before, sv.C_CROSS)
    check("yellow_first", ob == 0 and oa > 100 and yb > 100, f"노랑 지나기 전 주황 픽셀 {ob} · 노랑 픽셀 {yb} / 지난 뒤 주황 픽셀 {oa}")
    # 크레인 단계 (2026-11-10, 그룹 crane_step): 실제 녹화 재생 — S0 시작 판은 그리퍼 연 뒤 '크레인' 이 나오고 각도보다 먼저, 크레인 시작 판은 크레인 안내 없이 통과
    import importlib.util
    spec = importlib.util.spec_from_file_location("crane_replay_t", os.path.join(HERE, "crane_replay_lib.py"))
    cr_ok, cr_detail = False, "녹화 없음"
    if os.path.isdir(os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot6/dataset")) and os.path.isdir(os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot4/dataset")):
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        o1, _ = m.replay(cfg, P, "sg50_rot_pilot6", 1)
        o2, _ = m.replay(cfg, P, "sg50_rot_pilot4", 2)
        n1 = [n for _, n in o1]
        n2 = [n for _, n in o2]
        cr_ok = ("crane" in n1 and "그리퍼를 여세요" in n1 and n1.index("그리퍼를 여세요") < n1.index("crane") < n1.index("각도를 맞추세요")
                 and "crane" not in n2)
        cr_detail = "S0 시작 (pilot6 ep1): " + " → ".join(f"{t}s {n}" for t, n in o1) + " | 크레인 시작 (pilot4 ep2): " + " → ".join(f"{t}s {n}" for t, n in o2[:4])
    check("crane_step", cr_ok, cr_detail)
    # 높이 보정 절차 (2026-11-10, 그룹 height_comp): 크레인으로 찍은 pilot7 ep2 재생 — 크레인 → 맞춤 (이 높이에서) → 내려가기 → 유지 → 닫으세요 순서
    hc_ok, hc_detail = False, "녹화 없음"
    if os.path.isdir(os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot7/dataset")):
        o3, _ = m.replay(cfg, P, "sg50_rot_pilot7", 2, group_session="practice/sg50_rot_pilot8")
        n3 = [n for _, n in o3]
        first = {k: n3.index(k) for k in ("crane", "align", "descend", "hold", "close") if k in n3}
        hc_ok = len(first) == 5 and first["crane"] < first["align"] < first["descend"] < first["hold"] < first["close"] and \
            "각도를 맞추세요" not in n3[first["descend"]:]   # 맞춤 통과 (내려가기 시작) 뒤에는 각도로 안 돌아감
        hc_detail = " → ".join(f"{t}s {n}" for t, n in o3)
    check("height_comp_procedure", hc_ok, hc_detail[:300])
    # 상단 프레임 절차 (2026-11-10, 그룹 hover): pilot7 ep2 재생 + 14.5 s (상단 프레임과 맞은 순간) 프레임을 1 s 반복 [합성 대기]
    hv_ok, hv_detail = False, "녹화 없음"
    if os.path.isdir(os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot7/dataset")):
        o4, _ = m.replay_hold(cfg, P, "sg50_rot_pilot7", 2, 14.5, 1.0, "practice/sg50_rot_pilot9")
        n4 = [n for _, n in o4]
        f4 = {k: n4.index(k) for k in ("hover_up", "hover_wait", "descend", "hold", "close") if k in n4}
        hv_ok = len(f4) == 5 and f4["hover_up"] < f4["hover_wait"] < f4["descend"] < f4["hold"] < f4["close"] and \
            not any(n in ("hover_up", "hover_align", "hover_wait") for n in n4[f4["descend"]:])
        hv_detail = " → ".join(f"{t}s {n}" for t, n in o4)
    check("hover_procedure", hv_ok, hv_detail[:300])
    check("screenshots", all(os.path.exists(os.path.join(OUT, f)) for f in made), f"{len(made)} 장 → {OUT}")
    # 회전 안내 방향 (2026-11-10 사용자 "각도 방향이 반대"): 실제 녹화 (sg50_rot_pilot2) 에서 손목회전 변화 ↔ 화면 큐브각 변화 기울기 부호와
    # 안내 글 ('손목을 반시계' = 손목회전 + 쪽) 이 맞는지. dangle > 0 → 화면 큐브각을 늘려야 함 → 손목회전 + (기울기 > 0 일 때) → '반시계'
    import test_sg_approach as TA
    old_p3 = TA.P3
    TA.P3 = os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot2")
    xs, ys = [], []
    if os.path.isdir(os.path.join(TA.P3, "dataset")):
        D2 = P3Data()
        tref2 = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
        for e2 in sorted(D2.d.episode_index.unique()):
            st2, ac2 = D2.ep(int(e2))
            ix = sg_phase.analyze(st2, ac2, 30)["_idx"]
            ks = list(range(ix["open"], ix["close"], 6))
            W2 = D2.frames(int(e2), ks, "wrist")
            R = []
            for k in ks:
                det = sgs.detect(W2[k], P) if W2.get(k) is not None else None
                c2 = sgs.target_compare(det, tref2) if det else None
                if c2 and not c2["edge"]:
                    R.append((st2[k, 4], sgs.cube_angle(det["cube"]["hull"])))
            R = np.array(R)
            if len(R) > 2:
                dw, da = np.diff(R[:, 0]), np.diff(R[:, 1])
                m = (np.abs(dw) > 1.0) & (np.abs(da) < 20)
                xs += list(dw[m])
                ys += list(da[m])
    TA.P3 = old_p3
    slope = float(np.polyfit(xs, ys, 1)[0]) if len(xs) > 5 else None
    # 지나침 경고 (2026-11-10): sg50_rot_pilot2 ep0 닫기 7.8 s 전 (잡는 높이 근처, 그리퍼가 닫은 자리보다 바깥 +1.9 cm · dv +0.11) 실제 손목 영상
    ov_detail = "녹화 없음"
    ov_ok = False
    TA.P3 = os.path.expanduser("~/so101_runs/practice/sg50_rot_pilot2")
    if os.path.isdir(os.path.join(TA.P3, "dataset")):
        D3 = P3Data()
        st3, ac3 = D3.ep(0)
        ci3 = sg_phase.analyze(st3, ac3, 30)["_idx"]["close"]
        k3 = ci3 - int(7.8 * 30)
        w3 = D3.frames(0, [k3], "wrist")[k3]
        tref3 = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
        c3 = sgs.target_compare(sgs.detect(w3, P), tref3)
        pl = {int(r["episode_index"]): r for r in rc.read_plan(TA.P3)}
        r_up = dict(pl[0])                      # 계획 노랑 위 (270°)
        r_dn = dict(r_up, wp_dir="90", wp_u=f"{tref3['u']:.3f}", wp_v=f"{tref3['v'] + 0.12:.3f}")   # 같은 장면, 노랑이 아래라면
        o_up = sv.overshoot_check(c3, tref3, sv.waypoint_ref(cfg, r_up, tref3), r_up["wp_dir"], cfg)
        o_dn = sv.overshoot_check(c3, tref3, sv.waypoint_ref(cfg, r_dn, tref3), r_dn["wp_dir"], cfg)
        # 지나감 (through): 노랑 오른쪽 (0°) 인데 큐브가 주황 왼쪽으로 30 px
        r_rt = dict(r_up, wp_dir="0", wp_u=f"{tref3['u'] + 0.15:.3f}", wp_v=f"{tref3['v']:.3f}")
        c_l = dict(c3, du=-30 / 640.0, dv=0.0)
        o_th = sv.overshoot_check(c_l, tref3, sv.waypoint_ref(cfg, r_rt, tref3), "0", cfg)
        c_ok = dict(c3, du=0.01, dv=0.01)
        o_none = sv.overshoot_check(c_ok, tref3, sv.waypoint_ref(cfg, r_up, tref3), "270", cfg)
        ov_ok = o_up == "camera" and o_dn is None and o_th == "through" and o_none is None
        ov_detail = f"실제 장면 dv {c3['dv']:+.3f}: 노랑 위 → {o_up} · 노랑 아래 → {o_dn} · 노랑 오른쪽 + 큐브 왼쪽 30 px → {o_th} · 거의 맞음 → {o_none}"
        from PIL import Image
        img = Image.fromarray(w3).resize((600, 450))
        b = {"title": "지나쳤어요", "sub": "로봇 쪽으로 당기세요 (큐브를 주황 위로)", "col": sv.BAD, "over": True}
        on_phase()
        sv.draw_wrist(img, sgs.detect(w3, P), [tref3], 600 / 640, text=False, banner=b).save(os.path.join(OUT, "rot_overshoot_warn_600x450.png"))
    TA.P3 = old_p3
    check("overshoot_warn", ov_ok, ov_detail)
    check("rotation_guide_direction", slope is not None and slope > 0 and "반시계" in sv.wrist_turn_text(+10) and "시계" in sv.wrist_turn_text(-10)
          and "반시계" not in sv.wrist_turn_text(-10),
          f"손목회전 +1° → 화면 큐브각 {slope if slope is None else round(slope, 2)}° (n {len(xs)}) · dangle +10 → '{sv.wrist_turn_text(10)}'")
    n = sum(ok for _, ok, _ in RES)
    print(f"\n{n}/{len(RES)} PASS")
    json.dump({"results": RES}, open(os.path.join(ROOT, "tests", "results", "test_sg_rot.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return 0 if n == len(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
