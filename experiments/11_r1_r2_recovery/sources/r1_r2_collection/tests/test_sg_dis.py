#!/home/user/so101-env/bin/python
"""2026-11-13 sg_pin_dis (방해물 조건 64판) 계획 시험 (로봇 · 카메라 없음, 읽기만).
  64 줄 = sg_pin 영역 무작위 자리 64 곳 · 각도 16 씩 · 같은 자리의 깨끗한 판과 다른 각도 · 방해물 개수 2–6 (13/13/13/13/12) ·
  가장 가까운 방해물 near / far 32 씩 · 방향 4 가지 14–18 · 색 4 가지 고르게 · 한 판에 같은 색 ≤ 2 · 큐브에서 ≥ 5 cm · 방해물끼리 ≥ 3.5 cm ·
  가장 가까운 것이 실제로 가장 가까움 (둘째와 ≥ 1.5 cm) · 놓을 수 있는 자리 · front 화면 그림이 오류 없이 그려짐 · 기존 그룹 (sg_pin) 계획은 그대로.
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_dis.py
"""
import collections, csv, json, math, os, sys, types
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools")); CFG = os.path.join(ROOT, "config", "sg50.yaml"); os.environ["R12_CONFIG"] = CFG
RES = []
def check(name, ok, detail=""):
    RES.append((name, bool(ok), detail)); print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True)
def main():
    import numpy as np
    from PIL import Image
    import r12_common as rc, sg_plan as sp, sg_viewer as sv
    cfg = rc.load_config(CFG); dc = cfg["sg50"]["distractors"]
    rows = sp.make_rows(cfg, "sg_pin_dis"); clean = {r["position"]: r["angle"] for r in sp.make_rows(cfg, "sg_pin")}
    check("rows_64_positions", len(rows) == 64 and len({r["position"] for r in rows}) == 64 and all(len(r["position"]) > 2 for r in rows))
    check("angles_16_each_differ_from_clean", collections.Counter(r["angle"] for r in rows) == {"0": 16, "L30": 16, "R30": 16, "45": 16} and all(r["angle"] != clean[r["position"]] for r in rows))
    D = [r["_dis"] for r in rows]
    check("counts", dict(collections.Counter(d["n"] for d in D)) == {2: 13, 3: 13, 4: 13, 5: 13, 6: 12}, str(dict(sorted(collections.Counter(d["n"] for d in D).items()))))
    dirs = collections.Counter(d["dir"] for d in D)
    check("near_far_dirs", collections.Counter(d["cls"] for d in D) == {"near": 32, "far": 32} and all(14 <= dirs[k] <= 18 for k in sp.DIS_DIRS), str(dict(dirs)))
    cols = collections.Counter(); ok_geo = True; worst = []
    for r in rows:
        cx, cy = (float(v) for v in r["cube_xy_cm"].split(",")); P = sp.parse_distractors(r["distractors"])
        ds = sorted(math.hypot(x - cx, y - cy) for _, x, y in P)
        lo, hi = dc["near_cm"] if r["_dis"]["cls"] == "near" else dc["far_cm"]
        ok = (len(P) == r["_dis"]["n"] and ds[0] >= float(dc["near_cm"][0]) - 1e-6 and lo - 1e-6 <= ds[0] <= hi + 0.3 and (len(ds) < 2 or ds[1] - ds[0] >= float(dc["gap_cm"]) - 1e-6)
              and all(math.hypot(a[1] - b[1], a[2] - b[2]) >= float(dc["min_between_cm"]) - 1e-6 for i, a in enumerate(P) for b in P[i + 1:])
              and all(sp.distractor_ok(cfg, x, y, dc) for _, x, y in P) and max(collections.Counter(c for c, _, _ in P).values()) <= int(dc["max_per_color"]))
        ok_geo &= ok
        if not ok: worst.append(r["position"])
        for c, _, _ in P: cols[c] += 1
    check("geometry", ok_geo, str(worst[:5]))
    check("colors_balanced", max(cols.values()) - min(cols.values()) <= 2 and set(cols) == set(dc["colors"]), str(dict(cols)))
    check("order", sum(a["position"][:2] == b["position"][:2] for a, b in zip(rows, rows[1:])) == 0 and sum(a["angle"] == b["angle"] == c["angle"] for a, b, c in zip(rows, rows[1:], rows[2:])) == 0)
    try:
        fake = types.SimpleNamespace(cfg=cfg, H=rc.front_H(cfg), ui={"state": "SETUP"}, vis={}, debug=False)
        im = sv.Screen.draw_front(fake, Image.new("RGB", (960, 720), (200, 200, 200)), 1.5, rc.describe_row(cfg, rows[0]), False)
        a = np.array(im); drew = int((np.abs(a.astype(int) - 200).sum(-1) > 60).sum())
        check("front_markers_drawn", drew > 500, f"{drew} px")
    except Exception as e:
        check("front_markers_drawn", False, repr(e))
    old = os.path.expanduser("~/so101_runs/main_k8/sg_pin/r12_plan.csv")
    if os.path.exists(old):
        o = [x for x in csv.DictReader(open(old)) if not x["retake_of"]]; n = sp.make_rows(cfg, "sg_pin")
        check("main_group_plan_unchanged", len(o) == len(n) and all((a["position"], a["angle"]) == (b["position"], b["angle"]) for a, b in zip(n, o)) and all(not r["distractors"] for r in n))
    json.dump({"pass": sum(ok for _, ok, _ in RES), "total": len(RES), "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in RES]}, open(os.path.join(HERE, "results", "test_sg_dis.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{sum(ok for _, ok, _ in RES)}/{len(RES)}"); return 0 if all(ok for _, ok, _ in RES) else 1
if __name__ == "__main__":
    sys.exit(main())
