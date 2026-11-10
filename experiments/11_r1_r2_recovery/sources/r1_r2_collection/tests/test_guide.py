#!/home/user/so101-env/bin/python
"""시각 시연 가이드 시험 (로봇 · 녹화 없음, 저장된 영상 · d2 색인 읽기만).

A. d2 참고 색인: 256 편 · 키프레임 순서 · 기록값 범위 · 파일 존재
B. 참고 시연 고르기: K 자리 · 같은 각도 → '높음', 먼 자리 → '낮음' (불확실성 표시), 성공 시연만
C. 단계 자동 추정 (보조): 준비 → 시작 · 접근 · 닫힘 직전 (닫기 영역 안) · 파지 · 완료 · 빈 파지 뒤 다시 엶 → 접근
D. 녹화 뒤 검토 표시: 실물 R2-P ep0 · ep1 (11-03, 첫 닫힘 빈 파지 뒤 재파지) → 빈 파지 의심 · 실패한 닫힘 · ep0 잘림. 정상 파지 → 경고 없음
E. 설정: R2-P 두 시나리오에만 guide_stages (R1 · R2-O 는 아직 없음 → 가이드 꺼짐, 기존 화면)
F. 영상 창 (DISPLAY 있을 때): 실제 Viewer 를 저장 영상으로 띄워 F5/F6 수동 단계 · 클릭 · F7 자동 · F8 후보 · 손목 오버레이 그리기 오류 없음

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_guide.py
"""

import glob
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(COLL, "tools"))
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
CFG = os.path.join(COLL, "config", "r12_pilot12.yaml")
os.environ["R12_CONFIG"] = CFG
import r12_common as rc  # noqa: E402
import r12_guide as G  # noqa: E402

OK = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
    OK.append(bool(cond))


def main():
    cfg = rc.load_config(CFG)
    print("A. d2 참고 색인")
    idx = G.load_index()
    E = idx["episodes"]
    check("256 편 · 모두 첫 닫힘에 쥠 (팔로워 바닥 ≥ 8)", len(E) == 256 and all(e["grasped"] for e in E))
    order = all(e["keys"]["k_open"]["frame"] <= e["keys"]["k_opened"]["frame"] <= e["keys"]["k_reach"]["frame"] <= e["keys"]["k_close"]["frame"]
                < e["keys"]["k_grasp"]["frame"] <= e["keys"]["k_done"]["frame"] for e in E)
    check("키프레임 순서 열기 ≤ 다 열림 ≤ 접근 멈춤 ≤ 닫기 시작 < 파지 ≤ 끝", order)
    g_open = np.median([e["keys"]["k_opened"]["state"][5] for e in E])
    g_grasp = np.median([e["keys"]["k_grasp"]["state"][5] for e in E])
    check("기록값: 다 열림 팔로워 그리퍼 중앙 25–40 · 파지 바닥 중앙 8–18", 25 <= g_open <= 40 and 8 <= g_grasp <= 18, f"{g_open:.1f} / {g_grasp:.1f}")
    miss = [e["ep"] for e in E for k in e["keys"] for c in rc.CAMS if not os.path.exists(G.ref_image_path(e, k, c))]
    check("키프레임 영상 파일 모두 있음", not miss, f"없음 {len(miss)}")
    check("참고 궤적 (닫기 시작 기준 시간 · 관절 6 · 리더 그리퍼)", G.ref_traj(E[0]["ep"]).shape[1] == 8)

    print("B. 참고 시연 고르기")
    r = G.select_refs(rc.known_xy(cfg, "K3"), "45", 5)
    check("K3 45° → 같은 각도 · 2 cm 안 · 일치 '높음'", r and r[0]["angle_same"] and r[0]["dist_cm"] <= 2 and r[0]["quality"] == "high",
          f"ep{r[0]['ep']} {r[0]['dist_cm']} cm")
    far = G.select_refs((0.0, 45.0), "0", 3)
    check("작업 범위 밖 자리 → 일치 '낮음' + 거리 표시", far and far[0]["quality"] == "low" and "cm" in far[0]["quality_text"], far[0]["quality_text"])
    check("후보 5 개 · 점수 순", len(r) == 5 and all(r[i]["score"] <= r[i + 1]["score"] for i in range(4)))

    print("C. 단계 자동 추정 (보조)")
    st = G.stages_of(cfg, "R2-P-AHEAD")
    keys = [s["key"] for s in st]
    name = lambda i: keys[i]  # noqa: E731
    vis_ahead = {"wrist": {"detected": True, "dx": -0.3, "dy": -0.1, "area_px": 9000, "touches_edge": False}}
    vis_zone = {"wrist": {"detected": True, "dx": -0.31, "dy": 0.42, "area_px": 30000, "touches_edge": False}}
    hold = [(30, 30, 10, 20)] * 5 + [(30, 30, 10, 26)] * 5
    check("준비 단계 → ① 시작", name(G.auto_stage(st, "SETUP", [], vis_ahead)[0]) == "start")
    check("녹화 · 팔 이동 · 큐브 앞 → ② 접근", name(G.auto_stage(st, "REC", hold, vis_ahead)[0]) == "approach")
    check("녹화 · 큐브가 닫기 영역 안 (2D) → ③ 닫힘 직전", name(G.auto_stage(st, "REC", hold, vis_zone)[0]) == "preclose")
    grasp = hold + [(30 - 3 * k, 30 - 2 * k, 10, 22) for k in range(9)] + [(3, 12, 10, 22)] * 10
    check("닫힘 · 팔로워 12 → ④ 한 번 닫기", name(G.auto_stage(st, "REC", grasp, vis_zone)[0]) == "close")
    moved = grasp + [(3, 12, 40, -30)] * 5
    check("파지 뒤 팔 크게 이동 → ⑤ 완료", name(G.auto_stage(st, "REC", moved, None)[0]) == "done")
    empty = hold + [(30 - 3 * k, 30 - 3 * k, 10, 22) for k in range(10)] + [(1, 1, 10, 22)] * 5 + [(30, 30, 10, 22)] * 5
    i, why = G.auto_stage(st, "REC", empty, vis_ahead)
    check("빈 파지 (바닥 ≤ 5) 뒤 다시 엶 → ② 접근 · '빈 파지 의심'", name(i) == "approach" and "빈 파지" in why, why)

    print("D. 녹화 뒤 검토 표시 (실물 R2-P 11-03 기록, 읽기만)")
    import pandas as pd
    import record_ui as ru

    ds = os.path.expanduser("~/so101_runs/main_k8/r12_pilot12_r2p/dataset")
    if os.path.isdir(ds):
        info = json.load(open(os.path.join(ds, "meta", "info.json")))
        _, eps, cams = ru.load_meta(ds)
        d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(ds, "data", "*", "*.parquet")))])
        flags = {}
        for _, er in eps.iterrows():
            e = int(er["episode_index"])
            g = d[d.episode_index == e].sort_values("frame_index")
            S, A = np.stack(g["observation.state"].values), np.stack(g["action"].values)
            wcam = next(c for c in cams if c.endswith(".wrist"))
            t0 = float(er[f"videos/{wcam}/from_timestamp"])
            th = [f[::4, ::4] for k, f in enumerate(ru.iter_frames(ru.video_path(ds, info, wcam, er), t0, t0 + len(g) / 30, 30)) if k % 10 == 0]
            flags[e] = {c for lv, c, _ in G.review_episode(A[:, 5], S[:, 5], th, cfg) if lv == "warn"}
        check("ep0: 첫 닫힘 빈 파지 의심 · 실패한 닫힘 1 · 첫 닫힘 때 잘림",
              {"empty_first_close", "closes_before_grasp", "cut_at_first_close"} <= flags.get(0, set()), str(flags.get(0)))
        check("ep1: 첫 닫힘 빈 파지 의심 · 실패한 닫힘", {"empty_first_close", "closes_before_grasp"} <= flags.get(1, set()), str(flags.get(1)))
    else:
        print("  · R2-P dataset 없음 — 건너뜀")
    g_ok = np.r_[np.full(20, 30.0), np.linspace(30, 2, 10), np.full(40, 2.0)]
    s_ok = np.r_[np.full(20, 30.0), np.linspace(30, 12.5, 10), np.full(40, 12.5)]
    check("정상 파지 (첫 닫힘 팔로워 12.5) → 경고 없음", not [f for f in G.review_episode(g_ok, s_ok) if f[0] == "warn"])

    print("E. 설정")
    with_g = [sid for sid, s in cfg["scenarios"].items() if s.get("guide_stages")]
    check("guide_stages = R2-P-AHEAD · R2-P-DEPTH 만 (R1 · R2-O 는 다음 단계)", sorted(with_g) == ["R2-P-AHEAD", "R2-P-DEPTH"], str(with_g))
    base = rc.load_config()
    check("기본 설정 (기존 세션) 에는 가이드 없음", not any(s.get("guide_stages") for s in base["scenarios"].values()))

    print("F. 영상 창 (실제 Viewer)")
    if not os.environ.get("DISPLAY"):
        print("  · DISPLAY 없음 — 건너뜀")
    else:
        import types

        import r12_viewer as V

        live = tempfile.mkdtemp(prefix="r12_guide_test_")
        fr = rc.LiveFrames(live, create=True)
        jpg = lambda k, c: __import__("cv2").cvtColor(__import__("cv2").resize(__import__("cv2").imread(G.ref_image_path(E[0], k, c)), (640, 480)),  # noqa: E731
                                                      __import__("cv2").COLOR_BGR2RGB)
        fr.put(0, jpg("k_reach", "front"))
        fr.put(1, jpg("k_reach", "wrist"))
        fr.bump()
        names = [f"{j}.pos" for j in rc.JOINTS]
        st_ = {"t": time.time() + 3600, "state": dict(zip(names, E[0]["keys"]["k_reach"]["state"])), "action": dict(zip(names, E[0]["keys"]["k_reach"]["state"])),
               "checks": [], "guard": {"enabled": True, "gap": 0.5}}
        rc.write_json(os.path.join(live, "status.json"), st_)
        plan = rc.make_plan(cfg, "pilot12_r2p")
        row = rc.describe_row(cfg, plan[0])
        rc.write_json(os.path.join(live, "ui.json"), {"state": "SETUP", "episode": 0, "row": row, "keys": [], "results": [], "program": []})
        v = V.Viewer(live, 0.6)
        v.root.withdraw()
        err = []

        def frame():
            try:
                st, ui = v.load()
                v.st = st
                v.update_vision(ui)
                v.guide.update(st, ui)
                v.draw_cams(ui)
                v.draw_text(st, ui)
                v.guide.draw(st, ui)
            except Exception as e:
                err.append(repr(e))

        frame()
        check("가이드 켜짐 · 단계 5 칸 · 참고 시연 고름", v.guide.active and len(v.guide.boxes) == 5 and v.guide.ref is not None, str(err[:1]))
        check("준비 단계 자동 = ① (수동 없음)", v.guide.cur == 0 and v.guide.manual is None)
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F6", char=""))
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F6", char=""))
        frame()
        check("F6 두 번 → ③ 수동 (자동 추정과 별개)", v.guide.cur == 2 and v.guide.manual == 2)
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F5", char=""))
        frame()
        check("F5 → ②", v.guide.cur == 1)
        v.guide.click(3)
        frame()
        check("단계 칸 클릭 → ④", v.guide.cur == 3)
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F7", char=""))
        frame()
        check("F7 → 자동 추정으로 돌아감 (①)", v.guide.manual is None and v.guide.cur == 0)
        ep0 = v.guide.ref["ep"]
        V.Viewer.on_key(v, types.SimpleNamespace(keysym="F8", char=""))
        frame()
        check("F8 → 다음 참고 후보", v.guide.ref["ep"] != ep0, f"ep{ep0} → ep{v.guide.ref['ep']}")
        check("F5–F8 은 녹화 키로 넘기지 않음 (keys.in 없음)", not os.path.exists(os.path.join(live, "keys.in")))
        rc.write_json(os.path.join(live, "ui.json"), {"state": "SETUP", "episode": 0, "row": rc.describe_row(cfg, rc.make_plan(cfg, "pilot12_r2o")[0]),
                                                       "keys": [], "results": [], "program": []})
        frame()
        check("R2-O (guide_stages 없음) → 가이드 꺼짐 · 기존 화면", not v.guide.active)
        check("그리기 오류 없음", not err, str(err[:2]))
        v.root.destroy()
    print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)}")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
