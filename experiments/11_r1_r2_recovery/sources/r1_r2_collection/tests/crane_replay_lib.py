"""test_sg_rot 용: 실제 녹화 한 판을 sg50_rot_pilot7 (crane_step) 그룹 화면으로 재생해 절차 단계가 바뀌는 시각 · 이름을 돌려줌 (읽기만)."""
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
NAMES = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]


def replay(cfg, P, sess, ep, group_session="practice/sg50_rot_pilot7"):
    import r12_common as rc
    import sg_phase
    import sg_viewer as sv
    import test_sg_approach as T

    old = T.P3
    T.P3 = os.path.expanduser(f"~/so101_runs/practice/{sess}")
    D = T.P3Data()
    st, ac = D.ep(ep)
    ci = sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    row = rc.describe_row(cfg, {int(r["episode_index"]): r for r in rc.read_plan(T.P3)}[ep])
    seq = list(range(0, ci + 1, 3))
    W = {}
    F = D.frames(ep, [0], "front")
    for k0 in range(0, len(seq), 60):
        W.update(D.frames(ep, seq[k0:k0 + 60], "wrist"))
    T.P3 = old
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        live = os.path.join(tmp, "live")
        os.makedirs(live)
        lf = rc.LiveFrames(live, create=True)
        scr = sv.Screen(live, cfg)
        scr.P = P
        tt = time.time()
        for k in seq:
            lf.put(0, F[0]), lf.put(1, W[k]), lf.bump()
            s_ = dict(zip(NAMES, [float(x) for x in st[k]]))
            rc.write_json(os.path.join(live, "status.json"), {"t": tt, "phase": "rec", "ep": 0, "run_id": "t", "loop_hz": 30, "rec_frames": 1, "late_ticks": 0,
                                                              "stall_ticks": {"front": 0, "wrist": 0}, "state": s_, "action": s_})
            rc.write_json(os.path.join(live, "ui.json"), {"session": group_session, "done": 0, "target": 3, "preview": True, "state": "REC", "episode": 0, "row": row})
            scr.poll(tt)
            pr = scr.proc
            nm = (pr.get("name") or pr["title"]) if pr else None
            if not out or out[-1][1] != nm:
                out.append((round(k / 30, 1), nm))
            tt += 0.1
    return out, ci / 30


def replay_hold(cfg, P, sess, ep, hold_at_s, hold_s, group_session):
    """replay 와 같되 hold_at_s 에 가장 가까운 프레임을 hold_s 동안 반복 (사람이 그 자리에서 멈춘 것처럼) — 절차의 대기 단계 확인용 [합성: 같은 프레임 반복]."""
    import r12_common as rc
    import sg_phase
    import sg_viewer as sv
    import test_sg_approach as T

    old = T.P3
    T.P3 = os.path.expanduser(f"~/so101_runs/practice/{sess}")
    D = T.P3Data()
    st, ac = D.ep(ep)
    ci = sg_phase.analyze(st, ac, 30)["_idx"]["close"]
    r0 = dict({int(r["episode_index"]): r for r in rc.read_plan(T.P3)}[ep])
    r0.update(wp_dir="", wp_u="", wp_v="", wp_size="")
    row = rc.describe_row(cfg, r0)
    seq = list(range(0, ci + 1, 3))
    kh = min(seq, key=lambda k: abs(k - hold_at_s * 30))
    i = seq.index(kh)
    seq = seq[:i] + [kh] * int(hold_s / 0.1) + seq[i:]
    W = {}
    F = D.frames(ep, [0], "front")
    uniq = sorted(set(seq))
    for k0 in range(0, len(uniq), 60):
        W.update(D.frames(ep, uniq[k0:k0 + 60], "wrist"))
    T.P3 = old
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        live = os.path.join(tmp, "live")
        os.makedirs(live)
        lf = rc.LiveFrames(live, create=True)
        scr = sv.Screen(live, cfg)
        scr.P = P
        tt = time.time()
        for k in seq:
            lf.put(0, F[0]), lf.put(1, W[k]), lf.bump()
            s_ = dict(zip(NAMES, [float(x) for x in st[k]]))
            rc.write_json(os.path.join(live, "status.json"), {"t": tt, "phase": "rec", "ep": 0, "run_id": "t", "loop_hz": 30, "rec_frames": 1, "late_ticks": 0,
                                                              "stall_ticks": {"front": 0, "wrist": 0}, "state": s_, "action": s_})
            rc.write_json(os.path.join(live, "ui.json"), {"session": group_session, "done": 0, "target": 3, "preview": True, "state": "REC", "episode": 0, "row": row})
            scr.poll(tt)
            pr = scr.proc
            nm = (pr.get("name") or pr["title"]) if pr else None
            if not out or out[-1][1] != nm:
                out.append((round(k / 30, 1), nm))
            tt += 0.1
    return out, ci / 30
