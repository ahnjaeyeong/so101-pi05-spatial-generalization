#!/home/user/so101-env/bin/python
"""회복 시연 (config/r12_recovery.yaml, 11-04) 시험 — 로봇 · 녹화 없음.

A. 설정: 그룹 pilot12_rc 12 판 (F1 4 · F2 4 · F3 L2 R2) · 그리퍼 시작 (F1 열림 · F2/F3 닫힘) · visual_guide · 기존 설정 · 파일럿 12편 그대로
B. 그림: 옆에서 본 그림 (F1 비스듬 · F2 위) · 앞에서 본 그림 (F3 좌우) · 실제 실패 장면 파일
C. 시작 검사 (근사, 막지 않음): 그리퍼 시작 상태 · 손목 시작 영역
D. QA: F1 = 열린 채 접근 (Q3) · F2/F3 = 먼저 다시 열기 (Q4) · 시작부터 닫힌 그리퍼는 닫힘 사건이 아님
E. 영상 창 (DISPLAY, 숨김): 제목 · 닫힌 채 시작 → '먼저 그리퍼를 여세요' · 연 뒤 일반 안내 · F11 실제 실패 영상 (열지 않고 기록) · ③ 실제 장면 · 창 키는 녹화로 안 넘김

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_recovery.py
"""

import os
import subprocess
import sys
import tempfile
import time
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COLL, "tools"))
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
CFG = os.path.join(COLL, "config", "r12_recovery.yaml")
os.environ["R12_CONFIG"] = CFG
os.environ["R12_NO_OPEN"] = "1"
import r12_common as rc  # noqa: E402
import r12_schematic as SC  # noqa: E402

OK = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
    OK.append(bool(cond))


def main():
    cfg = rc.load_config(CFG)
    print("A. 설정")
    plan = rc.make_plan(cfg, "pilot12_rc")
    cnt = {}
    for p in plan:
        cnt[p["scenario_id"]] = cnt.get(p["scenario_id"], 0) + 1
    check("pilot12_rc 12 판 = F1 4 · F2 4 · F3-L 2 · F3-R 2", cnt == {"RC-F1": 4, "RC-F2": 4, "RC-F3-L": 2, "RC-F3-R": 2}, str(cnt))
    rows = {p["scenario_id"]: rc.describe_row(cfg, p) for p in plan}
    gs = {k: r.get("gripper_start") for k, r in rows.items()}
    check("그리퍼 시작: F1 열림 · F2 · F3 닫힘 (사용자 결정)", gs == {"RC-F1": "open", "RC-F2": "closed", "RC-F3-L": "closed", "RC-F3-R": "closed"}, str(gs))
    check("pilot_variant RC-F1 · RC-F2 · RC-F3", {k: r.get("pilot_variant") for k, r in rows.items()} ==
          {"RC-F1": "RC-F1", "RC-F2": "RC-F2", "RC-F3-L": "RC-F3", "RC-F3-R": "RC-F3"})
    vg_ok = all(cfg["scenarios"][s]["visual_guide"].get(k) for s in cnt for k in ("category", "case", "setup_steps", "side", "setup_target", "rec_target", "stages", "ref_video"))
    check("visual_guide 키 (분류 · 배치 순서 · 옆/앞 그림 · 목표 · 단계 · 실패 영상)", vg_ok)
    check("다른 시험 계획과 같은 seed → 같은 계획", rc.make_plan(cfg, "pilot12_rc") == plan)
    out = subprocess.run(["git", "-C", COLL, "diff", "--quiet", "HEAD", "--", "config/r12_scenarios.yaml", "config/r12_pilot12.yaml"])
    check("기존 r12_scenarios.yaml · r12_pilot12.yaml 안 바뀜 (git)", out.returncode == 0)
    p12 = rc.load_config(os.path.join(COLL, "config", "r12_pilot12.yaml"))
    check("파일럿 12편 설정에는 회복 시나리오 없음", not any(k.startswith("RC-") for k in p12["scenarios"]) and set(p12["groups"]) == {"pilot12_r1", "pilot12_r2p", "pilot12_r2o"})

    print("B. 그림")
    sides = {s: SC.render_side(cfg["scenarios"][s]["visual_guide"]["side"], (512, 192)) for s in cnt}
    check("옆/앞에서 본 그림 4 종 그려짐", all(i.size == (512, 192) for i in sides.values()))
    a = np.asarray(sides["RC-F3-L"]).astype(int)
    b = np.asarray(sides["RC-F3-R"]).astype(int)
    check("F3 왼쪽 · 오른쪽 앞에서 본 그림이 다름 (좌우 반대)", np.abs(a - b).mean() > 3)
    for s in ("RC-F1", "RC-F3-R"):
        ti = cfg["scenarios"][s]["visual_guide"].get("setup_target_image") or {}
        pth = os.path.join(COLL, ti.get("path", ""))
        check(f"{s}: 실제 실패 장면 파일 ({'있음' if os.path.exists(pth) else '없음 → 개념도'})", True, ti.get("path", ""))

    print("C. 시작 검사 (근사)")
    names = [f"{j}.pos" for j in rc.JOINTS]

    def st(g):
        return dict(zip(names, [10.0, 20.0, 0.0, 70.0, 0.0, g]))

    def vis(u, v):
        return {"wrist": {"detected": True, "dx": 2 * u - 1, "dy": 2 * v - 1, "area_px": 9000, "touches_edge": False, "bbox": (0, 0, 10, 10)},
                "front": {"detected": True, "dist_planned_cm": 1.0, "xy_cm": [0, 0], "px": [0, 0]}}

    f2 = rc.pilot_start_checks(cfg, rows["RC-F2"], st(1.0), vis(0.34, 0.72))
    f2o = rc.pilot_start_checks(cfg, rows["RC-F2"], st(30.0), vis(0.34, 0.72))
    f1 = rc.pilot_start_checks(cfg, rows["RC-F1"], st(30.0), vis(0.34, 0.66))
    f3 = rc.pilot_start_checks(cfg, rows["RC-F3-R"], st(1.0), vis(0.34, 0.50))   # 큐브가 손가락 끝 위 = F3-L 쪽
    f3r = rc.pilot_start_checks(cfg, rows["RC-F3-R"], st(1.0), vis(0.54, 0.85))  # RC ep3 시작 (사용자 확인: 큐브가 로봇 왼쪽)
    f3l = rc.pilot_start_checks(cfg, rows["RC-F3-L"], st(1.0), vis(0.34, 0.50))
    sim = lambda r: (r["similarity"]["matched"], r["similarity"]["total"])  # noqa: E731
    check("F2 닫힘 · 영역 안 → 3/3 · F2 열림 → 그리퍼 항목 ✗", sim(f2) == (3, 3) and sim(f2o) == (2, 3), f"{sim(f2)} {sim(f2o)}")
    check("F1 열림 · 영역 안 → 3/3", sim(f1) == (3, 3), str(f1["similarity"]["items"]))
    check("F3-R: 큐브가 손가락 위 → 영역 ✗ (근사 · 녹화는 막지 않음)", sim(f3) == (2, 3), str(f3["similarity"]["items"]))
    check("F3-R: RC ep3 시작 (u .54 · v .85, 큐브 로봇 왼쪽) → 3/3", sim(f3r) == (3, 3), str(f3r["similarity"]["items"]))
    check("F3-L: 큐브가 손가락 끝 위 → 3/3", sim(f3l) == (3, 3), str(f3l["similarity"]["items"]))
    gsc = {s: cfg["scenarios"][s]["visual_guide"]["setup_target"]["cube"][1] for s in ("RC-F3-L", "RC-F3-R")}
    check("F3 손목 목표 그림: 로봇 좌우 빗김 = 화면 위/아래 (L 위 · R 아래)", gsc["RC-F3-L"] < 0.6 < gsc["RC-F3-R"], str(gsc))

    print("D. QA (파일럿 QA · 합성 기록)")
    import r12_qa

    n = 300
    S = np.zeros((n, 6))
    A = np.zeros((n, 6))
    S[:, 1] = np.linspace(20, 40, n)
    # F2: 닫힘 1 → 1.0 s 에 30 까지 엶 (팔 정지) → 4 s 에 닫아 쥠 (팔로워 12)
    A[:, 5] = 1.0
    A[30:120, 5] = 30.0
    A[120:, 5] = 2.0
    S[:, 5] = A[:, 5]
    S[120:, 5] = 12.0
    S[:30, 1] = 20.0
    ev = rc.close_events(A[:, 5])
    check("시작부터 닫힌 그리퍼는 닫힘 사건이 아님 (닫힘 1 번 = 연 뒤 닫기)", len(ev) == 1 and ev[0][0] >= 115, str([e[0] for e in ev]))
    v_ = vis(0.34, 0.72)
    q2 = r12_qa._pilot_one(cfg, plan[[p["scenario_id"] for p in plan].index("RC-F2")], S, A, 30, v_, None, {"first_grasp_success": True, "final_success": True}, True)
    check("F2 QA: Q4 (먼저 다시 열기 ≥ 25) ok · Q3 해당 없음 · Q5 첫 닫힘에 쥠", q2["q4"] == "ok" and q2["q3"] == "na" and q2["q5"] == "ok",
          f"q4 {q2['q4']} {q2['q4_detail']} · q5 {q2['q5']}")
    A1 = A.copy()
    A1[:120, 5] = 30.0
    S1 = S.copy()
    S1[:120, 5] = 30.0
    q1 = r12_qa._pilot_one(cfg, plan[[p["scenario_id"] for p in plan].index("RC-F1")], S1, A1, 30, vis(0.34, 0.66), None,
                           {"first_grasp_success": True, "final_success": True}, True)
    check("F1 QA: Q3 (열린 채 접근) ok · Q4 해당 없음", q1["q3"] == "ok" and q1["q4"] == "na", f"q3 {q1['q3']} {q1['q3_detail']}")

    print("E. 영상 창 (실제 Viewer, 숨김)")
    if not os.environ.get("DISPLAY"):
        print("  · DISPLAY 없음 — 건너뜀")
    else:
        import r12_viewer as V

        live = tempfile.mkdtemp(prefix="r12_recovery_test_")
        fr = rc.LiveFrames(live, create=True)
        img = np.full((480, 640, 3), 200, np.uint8)
        img[300:400, 180:280] = (210, 25, 30)
        fr.put(0, img)
        fr.put(1, img)
        last = {"g": 1.0}

        def status():
            rc.write_json(os.path.join(live, "status.json"), {"t": time.time() + 3600, "state": st(last["g"]), "action": st(last["g"]),
                                                               "checks": [], "guard": {"enabled": True, "gap": 0.5}})

        def ui(state, sid, aid=None):
            rc.write_json(os.path.join(live, "ui.json"), {"state": state, "episode": 0, "row": rows[sid], "keys": [], "results": [], "program": [],
                                                           "rec_aid": aid, "elapsed": 1.0, "episode_time": 45})

        status()
        ui("SETUP", "RC-F2")
        v = V.Viewer(live, 0.8)
        v.root.withdraw()

        def frame(k=1):
            for _ in range(k):
                status()
                time.sleep(0.002)
                fr.bump()
                v.vis_t = 0
                v.refresh()
            return "화면 오류" not in v.banner.cget("text")

        c = v.coll
        good = frame()
        check("F2 준비: 수집자 화면 · 제목 'RC-F2 | 이른 닫힘 회복 — …'", good and v.layout == ("collector",) and c.title.cget("text").startswith("RC-F2 | 이른 닫힘 회복"),
              c.title.cget("text"))
        check("F2 닫힌 채 → 닫기 안내 '먼저 그리퍼를 여세요'", c.close[0] == "O" and "먼저 그리퍼를" in c.c_big.cget("text"), c.c_big.cget("text"))
        check("F2 ① 옆에서 본 그림 · 배치 순서 · ③ 개념도 (실제 장면 없음)", c.p1_img.cget("image") and "1.5–2.5 cm" in c.p1_txt.cget("text")
              and c.p3_title.cget("text").startswith("③ 목표 손목 화면"))
        ui("REC", "RC-F2", "a1")
        frame(2)
        check("녹화 중 아직 안 엶 → 계속 '먼저 그리퍼를 여세요'", c.close[0] == "O")
        last["g"] = 30.0
        frame(2)
        last["g"] = 1.0
        frame(2)
        check("한 번 연 뒤 다시 닫힘 → 'O' 아님 (일반 안내: 그리퍼 닫힘)", c.close[0] == "CLOSED", str(c.close))
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F11", char=""))
        check("F11 → 실제 실패 영상 (F2 앵커, 열지 않고 기록)", (getattr(c, "ref_opened", "") or "").endswith("index.html#F2") or "영상 폴더가 없어요" in getattr(c, "ref_msg", ""),
              getattr(c, "ref_msg", ""))
        last["g"] = 30.0
        ui("SETUP", "RC-F1")
        frame()
        ti = cfg["scenarios"]["RC-F1"]["visual_guide"]["setup_target_image"]
        if os.path.exists(os.path.join(COLL, ti["path"])):
            check("F1 준비: ③ 실제 실패 장면 (16:08 ep4)", c.p3_title.cget("text").startswith("③ 실제 실패 장면") and "ep4" in c.p3_cap.cget("text"))
        check("F1 열림 → 'O' 아님", c.close[0] != "O")
        ui("SETUP", "RC-F3-L")
        frame()
        check("F3-L 준비: 제목 · 앞에서 본 그림", c.title.cget("text").startswith("RC-F3 | 정렬 오차 회복") and c.p1_img.cget("image"))
        check("창 키 (F11 포함) 는 녹화로 안 넘김 (keys.in 없음)", not os.path.exists(os.path.join(live, "keys.in")))
        v.root.destroy()
    print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)}")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
