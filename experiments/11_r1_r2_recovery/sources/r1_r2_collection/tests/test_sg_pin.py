#!/home/user/so101-env/bin/python
"""2026-11-12 sg_pin (새 절차: 숄더팬 → 그리퍼 → 첫 맞춤 → 손목 수직 → 다시 맞춤 → 회전 → 내려가 집기) 시험 (로봇 · 카메라 없음, 읽기만).

1 계획: 96 줄 = K 8 × 각도 4 + 영역 8 × K#p# 8 (영역마다 각도 2 판씩) · 첫 맞춤 방향 4 가지 각 24 · 각도 × 방향 각 6 ·
  같은 영역 연달아 없음 · 같은 각도 / 방향 3 연속 없음 · 노란 자리 화면 안 · 기존 그룹 (sg50_rot) 계획은 저장된 것과 같음.
2 절차 단계 [합성 상태]: 가짜 화면 (큐브 윤곽 · 기울기 · 높이를 정해 넣음) 으로 단계가
  숄더팬 → 그리퍼 → 첫 맞춤 → 수직 → 다시 맞춤 → 회전 → 내려가기 → 유지 → 닫기 순서로만 나아가고 되돌아가지 않는지, 0° 큐브는 회전을 건너뛰는지.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_pin.py
"""
import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
CFG = os.path.join(ROOT, "config", "sg50.yaml")
os.environ["R12_CONFIG"] = CFG
RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True)


def cube_det(ref, u, v, size=1.0, rot=0.0):
    """닫기 자리 목표 윤곽을 (u, v) 로 옮기고 size 배 · rot° 돌린 검출 결과 [합성]."""
    W, H = 640.0, 480.0
    th = math.radians(rot)
    hull = []
    for x, y in ref["hull"]:
        dx, dy = (x - ref["u"]) * W * size, (y - ref["v"]) * H * size
        hull.append([u * W + dx * math.cos(th) - dy * math.sin(th), v * H + dx * math.sin(th) + dy * math.cos(th)])
    return {"status": "detected", "cube": {"u": u, "v": v, "area_px": ref["area_px"] * size * size, "hull": hull, "touches_edge": False}, "sticker": None}


def main():
    import r12_common as rc
    import sg_plan as sp
    import sg_sticker as sgs
    import sg_viewer as sv

    cfg = rc.load_config(CFG)
    s50 = cfg["sg50"]
    rows = sp.make_rows(cfg, "sg_pin_staged")
    K = [r for r in rows if len(r["position"]) == 2]
    R = [r for r in rows if len(r["position"]) > 2]
    check("plan_96", len(rows) == 96 and len(K) == 32 and len(R) == 64, f"{len(rows)} = K {len(K)} + 영역 {len(R)}")
    check("plan_K_all_angles", all(sorted(r["angle"] for r in K if r["position"] == k) == ["0", "45", "L30", "R30"] for k in {r["position"] for r in K}))
    check("plan_region_8_each", sorted(collections.Counter(r["position"][:2] for r in R).values()) == [8] * 8 and len({r["position"] for r in R}) == 64)
    check("plan_region_angle_2_each", set(collections.Counter((r["position"][:2], r["angle"]) for r in R).values()) == {2})
    check("plan_dirs", collections.Counter(r["wp_dir"] for r in rows) == {"0": 24, "90": 24, "180": 24, "270": 24}
          and set(collections.Counter((r["angle"], r["wp_dir"]) for r in rows).values()) == {6}, f"{dict(collections.Counter(r['wp_dir'] for r in rows))}")
    check("plan_order", sum(a["position"][:2] == b["position"][:2] for a, b in zip(rows, rows[1:])) == 0
          and sum(a["angle"] == b["angle"] == c["angle"] for a, b, c in zip(rows, rows[1:], rows[2:])) == 0
          and sum(a["wp_dir"] == b["wp_dir"] == c["wp_dir"] for a, b, c in zip(rows, rows[1:], rows[2:])) == 0)
    ref = next(r for r in sgs.active_refs() if r.get("kind") == "target")
    inside = all(all(0.02 <= x <= 0.98 and 0.02 <= y <= 0.98 for x, y in sv.pin_ref(cfg, r, ref, True)["hull"]) for r in rows)
    check("plan_entry_frames_inside", inside)
    check("plan_start_pan", all(abs(float(r["start_joints"].split(";")[0].split("=")[1])) <= s50["start_pan"]["abs_max"] for r in rows))
    old = os.path.expanduser("~/so101_runs/main_k8/sg50_rot/r12_plan.csv")
    if os.path.exists(old):
        o = list(csv.DictReader(open(old)))
        n = sp.make_rows(cfg, "sg50_rot")
        check("old_group_plan_unchanged", len(o) == len(n) and all((a["position"], a["angle"], a["wp_dir"]) == (b["position"], b["angle"], b["wp_dir"]) for a, b in zip(n, o)))  # 노란 자리 좌표 (wp_u) 는 활성 닫기 자리 목표에 따라 달라져서 뺌 (2026-11-12 ref-v8)

    # ---- 2 절차 단계 [합성 상태]
    ec, hv, pn = s50["end_condition"], s50["hover"], s50["pin"]
    hz = float(ec["height_cm"])
    aref = sv.pin_ref(cfg, {}, ref, False)

    class Scr:
        def __init__(self, row):
            self.cfg, self.ui, self.rec_t0, self._tref = cfg, {"row": row, "episode": 0, "session": "practice/sg_pin_staged"}, 1.0, ref
            self.det, self.tip_z, self.tilt_v, self.endc, self.wp, self._hold = None, hz + 6.0, 25.0, None, None, None

        def group_flag(self, k):
            return k in ("pin", "procedure_guide")

        def level(self):
            return (self.tilt_v, 3.0, 0.0)

        def step(self, now, pan, grip):
            e = sv.end_check(self.det, ref, ec, self.tip_z)
            self._hold = (self._hold or now) if (e and e["all"]) else None
            held = now - self._hold if self._hold else 0.0
            self.endc = {"e": e, "tol_h": float(ec["tol_height_cm"]), "frac": held / float(pn["hold_s"]), "held_s": held, "hold_s": float(pn["hold_s"])}
            return sv.procedure_state(self, self.ui["row"], {"shoulder_pan.pos": pan, "gripper.pos": grip}, now)

    def run(row, rot):
        s = Scr(row)
        tgt = float(row["pan_target_deg"])
        eu, ev, es = float(row["wp_u"]), float(row["wp_v"]), float(row["wp_size"])
        seq = []
        def go(now, pan, grip, det=None, tilt=None, z=None):
            if det is not None: s.det = det
            if tilt is not None: s.tilt_v = tilt
            if z is not None: s.tip_z = z
            p = s.step(now, pan, grip)
            seq.append((p.get("name") or {0: "pan", 1: "grip"}[p["step"]], p["step"], len(p["steps"]), s._wp_active))
            return p
        go(0.0, tgt + 20, 1.0, det=cube_det(ref, 0.5, 0.2, 0.6, rot))        # 숄더팬
        go(0.5, tgt + 1, 1.0)                                                 # 그리퍼
        go(1.0, tgt + 1, 30.0)                                                # 첫 맞춤 (큐브가 멀리)
        go(1.5, tgt + 1, 30.0, det=cube_det(ref, eu, ev, es, rot))            # 첫 맞춤 통과 → 수직 (기울기 25°)
        go(2.0, tgt + 1, 30.0, tilt=3.0)                                      # 수직 통과 → 다시 맞춤 (큐브는 아직 첫 자리, 높이 +6)
        go(2.5, tgt + 1, 30.0, det=cube_det(ref, aref["u"], aref["v"], float(hv["frame"]["size"]), rot), z=hz + float(hv["height_cm"]))   # 맞음, 기다리는 중
        go(3.0, tgt + 1, 30.0)                                                # wait_s 지남 → 회전 (rot ≠ 0) 또는 내려가기
        go(3.5, tgt + 1, 30.0, det=cube_det(ref, aref["u"], aref["v"], float(hv["frame"]["size"]), 0.0))   # 회전 맞음 → 내려가기
        go(4.0, tgt + 1, 30.0, det=cube_det(ref, ref["u"], ref["v"], 1.0, 0.0), z=hz)                      # 주황 · 높이 맞음 → 유지
        go(4.0 + float(pn["hold_s"]) + 0.1, tgt + 1, 30.0)                    # 유지 끝 → 닫으세요
        go(5.5, tgt + 1, 30.0, tilt=20.0)                                     # 뒤에 기울어져도 앞 단계로 안 돌아감
        return seq

    row = dict(rows[0])
    seq = run(row, 30.0)
    names = [x[0] for x in seq]
    want = ["pan", "grip", "pin_entry", "pin_vert", "pin_align", "pin_align", "pin_rot", "descend", "hold", "close", "close"]
    check("steps_rotated_cube", names == want, " → ".join(names))
    check("steps_monotonic", all(b[1] >= a[1] for a, b in zip(seq, seq[1:])) and all(x[2] == 8 for x in seq[2:]), str([x[1] for x in seq]))
    check("yellow_then_orange", [x[3] for x in seq[2:]] == [True, True, True, True, True, False, False, False, False], str([x[3] for x in seq[2:]]))
    seq0 = run(row, 0.0)
    names0 = [x[0] for x in seq0]
    check("steps_cube_0deg_skips_rotation", "pin_rot" not in names0 and names0[6] == "descend", " → ".join(names0))
    # 기존 그룹 (hover) 은 그대로 hover_state 로 감
    class ScrH(Scr):
        def group_flag(self, k):
            return k in ("hover", "procedure_guide")
    sh = ScrH(row)
    sh.det = cube_det(ref, 0.5, 0.2, 0.6)
    p = sh.step(0.0, float(row["pan_target_deg"]), 1.0)
    p = sh.step(0.5, float(row["pan_target_deg"]), 30.0)
    nat = sp.make_rows(cfg, "sg_pin")   # 본 수집: 같은 96 자리 · 각도, 계획 시작 자세 · 절차 안내 · 노란 상단 프레임 → 주황 (일부러 벗어난 자리 없음)
    check("main_group_natural", len(nat) == 96 and collections.Counter(r["angle"] for r in nat) == {"0": 24, "L30": 24, "R30": 24, "45": 24}
          and all(not r["wp_dir"] for r in nat) and {r["scenario_id"] for r in nat} == {"SG-PLAN"} and all(r["start_joints"] for r in nat)
          and rc.group_of(cfg, "sg_pin").get("procedure_guide") and rc.group_of(cfg, "sg_pin").get("hover") and not rc.group_of(cfg, "sg_pin").get("pin"),
          f"{len(nat)} · {sorted({r['scenario_id'] for r in nat})}")
    check("hover_group_unchanged", p.get("name") == "hover_up", str(p.get("name")))
    class ScrM(Scr):   # 본 수집 그룹: 노랑 (상단 프레임) 먼저 → 대기 0.3 s → 내려가기
        def group_flag(self, k):
            return k in ("hover", "procedure_guide")
        def group_get(self, k, d=None):
            return {"hover_wait_s": 0.3, "hold_s": 0.7}.get(k, d)
    sm = ScrM(row)
    tg = float(row["pan_target_deg"])
    sm.det, sm.tilt_v, sm.tip_z = cube_det(ref, aref["u"], aref["v"], float(hv["frame"]["size"])), 2.0, hz + float(hv["height_cm"])
    sm.wp = sv.hover_ref(cfg, ref)
    seqm = [sm.step(0.0, tg, 1.0).get("step"), sm.step(0.5, tg, 30.0).get("name"), sm.step(0.7, tg, 30.0).get("name"), sm.step(0.9, tg, 30.0).get("name")]
    check("main_group_yellow_first_wait_0.3s", seqm == [1, "hover_wait", "hover_wait", "descend"] , str(seqm))

    out = os.path.join(HERE, "results", "test_sg_pin.json")
    json.dump({"pass": sum(ok for _, ok, _ in RES), "total": len(RES), "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in RES]},
              open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{sum(ok for _, ok, _ in RES)}/{len(RES)} → {out}")
    return 0 if all(ok for _, ok, _ in RES) else 1


if __name__ == "__main__":
    sys.exit(main())
