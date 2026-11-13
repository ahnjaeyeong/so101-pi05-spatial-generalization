#!/home/user/so101-env/bin/python
"""2026-11-09 접근 유형 · 정답조건 화면 시험 (로봇 · 카메라 없음, 읽기만).

1 계획: sg50_approach 40줄에 approach_mix 대로 유형 배정 · 같은 유형 3 연속 없음 · 기존 그룹 (sg50_pilot3) 은 빈칸 · 순서 그대로.
2 방향 부호: 손목 화면에서 큐브가 들어오는 쪽 (B 위 · C 아래 · D+ 왼쪽 · D- 오른쪽).
3 실제 예비3 닫기 (사람 40편, 닫기 3 프레임 전 손목 + 같은 프레임 관절값): 정답조건 네 가지 각각 · 모두 맞는 비율 (참고값, 기준 아님).
4 유지 시간: 다 맞은 상태를 0.6 s 이어 poll → 고리 다 참 (frac ≥ 1), 하나 틀리면 0 으로.
5 화면 그림: 유형마다 접근 중 (닫기 5 s 전) · 닫기 직전 장면 → screenshots/sg50_approach/*.png (Tk 창에 넣는 그림과 같은 그림).

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_approach.py
"""

import glob
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
P3 = os.path.expanduser("~/so101_runs/practice/sg50_pilot3")
CFG = os.path.join(ROOT, "config", "sg50.yaml")
os.environ["R12_CONFIG"] = CFG
OUT = os.path.join(ROOT, "screenshots", "sg50_approach")
NAMES = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True)


class P3Data:
    def __init__(self):
        import pandas as pd

        self.info = json.load(open(f"{P3}/dataset/meta/info.json"))
        self.em = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{P3}/dataset/meta/episodes/*/*.parquet"))])
        self.d = pd.concat([pd.read_parquet(p, columns=["observation.state", "action", "episode_index", "frame_index"])
                            for p in sorted(glob.glob(f"{P3}/dataset/data/*/*.parquet"))])

    def ep(self, ep):
        e = self.d[self.d.episode_index == ep].sort_values("frame_index")
        return np.stack(e["observation.state"].values).astype(float), np.stack(e["action"].values).astype(float)

    def frames(self, ep, idxs, cam):
        import av

        er = self.em[self.em.episode_index == ep].iloc[0]
        k = f"observation.images.{cam}"
        p = f"{P3}/dataset/" + self.info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]),
                                                               file_index=int(er[f"videos/{k}/file_index"]))
        t0 = float(er[f"videos/{k}/from_timestamp"])
        want = {int(i): None for i in idxs}
        c = av.open(p)
        s = c.streams.video[0]
        c.seek(int((t0 + min(want) / 30.0 - 1.0) / float(s.time_base)), stream=s, backward=True)
        for f in c.decode(s):
            fi = int(round((float(f.pts * s.time_base) - t0) * 30))
            if fi in want and want[fi] is None:
                want[fi] = f.to_ndarray(format="rgb24")
            if fi > max(want):
                break
        c.close()
        return want


def main():
    import r12_common as rc
    import sg_fk
    import sg_phase
    import sg_plan as sp
    import sg_sticker as sgs
    import sg_viewer as sv

    cfg = rc.load_config(CFG)
    s50 = cfg["sg50"]
    ec = s50["end_condition"]
    # 1 계획
    rows = sp.make_rows(cfg, "sg50_approach")
    cnt = {}
    for r in rows:
        cnt[r["approach_type"]] = cnt.get(r["approach_type"], 0) + 1
    mix = rc.group_of(cfg, "sg50_approach")["approach_mix"]
    check("plan_counts", cnt == sp.approach_counts(mix, len(rows)) and len(rows) == 40, f"{dict(sorted(cnt.items()))}")
    t = [r["approach_type"] for r in rows]
    check("plan_no_3_in_row", sum(a == b == c for a, b, c in zip(t, t[1:], t[2:])) == 0)
    old = sp.make_rows(cfg, "sg50_pilot3")
    cur = rc.read_plan(P3)
    same = [r["position"] for r in old] == [r["position"] for r in cur[: len(old)]] if cur else True
    check("old_group_unchanged", all(not r["approach_type"] for r in old) and same, f"pilot3 순서 같음 {same}")
    check("counts_sum", all(sum(sp.approach_counts(mix, n).values()) == n for n in (7, 40, 48, 53)))
    # 2 방향 부호
    A = s50["approach"]
    exp = {"B": (0, -1), "C": (0, 1), "D+": (-1, 0), "D-": (1, 0), "E": (0, -1)}
    got = {k: tuple(round(x) for x in sv.wrist_from_dir(A[k])) for k in exp}
    check("wrist_dir_signs", got == exp and sv.wrist_from_dir(A["A"]) is None, f"{got}")
    # 3 실제 사람 닫기
    D = P3Data()
    tref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    P = sgs.load_params()
    okc = {"u": 0, "v": 0, "size": 0, "height": 0, "all": 0}
    n = 0
    scenes = {}
    for ep in range(3, 43):
        st, ac = D.ep(ep)
        ci = sg_phase.analyze(st, ac, 30)["_idx"]["close"]
        k = ci - 3
        w = D.frames(ep, [k], "wrist")[k]
        if w is None:
            continue
        q = st[k, :5]
        z = float(sg_fk.fk(q[None])[0][0][2] * 100)
        e = sv.end_check(sgs.detect(w, P), tref, ec, z)
        n += 1
        for kk in ("u", "v", "size", "height"):
            okc[kk] += e["ok"][kk]
        okc["all"] += e["all"]
        if ep in (12, 20, 30) and e["all"]:
            scenes.setdefault("close", (ep, ci))
    frac = {k: round(v / max(n, 1), 2) for k, v in okc.items()}
    check("human_close_end_condition_measured", n >= 35, f"n {n} · 맞는 비율 {frac} (참고값)")
    # 4 · 5 화면
    os.makedirs(OUT, exist_ok=True)
    ep, ci = scenes.get("close") or (12, sg_phase.analyze(*D.ep(12), 30)["_idx"]["close"])
    st, _ = D.ep(ep)
    ks = [ci - 150, ci - 3]
    fr = D.frames(ep, ks, "front")
    wr = D.frames(ep, ks, "wrist")
    with tempfile.TemporaryDirectory() as tmp:
        live = os.path.join(tmp, "live")
        os.makedirs(live)
        lf = rc.LiveFrames(live, create=True)

        def put(k, ui, now):
            lf.put(0, fr[k]), lf.put(1, wr[k]), lf.bump()
            stt = dict(zip(NAMES, [float(x) for x in st[k]]))
            rc.write_json(os.path.join(live, "status.json"), {"t": now, "phase": "rec", "ep": ui["episode"], "run_id": "test", "loop_hz": 30.0,
                                                              "rec_frames": 100, "late_ticks": 0, "stall_ticks": {"front": 0, "wrist": 0},
                                                              "state": stt, "action": stt})
            rc.write_json(os.path.join(live, "ui.json"), ui)

        rows_ = rows
        made = []
        for typ in ("A", "B", "C", "D+", "D-", "E"):
            r = next(x for x in rows_ if x["approach_type"] == typ)
            row = rc.describe_row(cfg, r)
            row["approach_type"] = typ
            ui = {"session": "practice/sg50_approach", "done": 3, "target": 40, "preview": True, "state": "REC", "episode": int(r["episode_index"]), "row": row}
            scr = sv.Screen(live, cfg)
            scr.P = P
            t0 = time.time()
            put(ks[0], ui, t0)
            scr.poll(t0)
            fn = f"approach_{typ.replace('+', 'p').replace('-', 'm')}_approaching_1800x470.png"
            scr.render(1800, 470, t0).save(os.path.join(OUT, fn))
            made.append(fn)
        # 닫기 직전: 유지 시간 고리
        scr = sv.Screen(live, cfg)
        scr.P = P
        r = next(x for x in rows_ if x["approach_type"] == "B")
        row = rc.describe_row(cfg, r)
        row["approach_type"] = "B"
        ui = {"session": "practice/sg50_approach", "done": 3, "target": 40, "preview": True, "state": "REC", "episode": int(r["episode_index"]), "row": row}
        t0 = time.time()
        put(ks[1], ui, t0)
        scr.poll(t0)
        e0 = scr.endc
        scr.render(1800, 470, t0).save(os.path.join(OUT, "approach_close_hold_start_1800x470.png"))
        lf.bump()
        hs = float(ec.get("hold_s", 0.5)) + 0.1
        rc.write_json(os.path.join(live, "status.json"), {**rc.read_json(os.path.join(live, "status.json"), {}), "t": t0 + hs})
        scr.poll(t0 + hs)
        e1 = scr.endc
        scr.render(1800, 470, t0 + hs).save(os.path.join(OUT, "approach_close_hold_full_1800x470.png"))
        scr.debug = True
        scr.render(1400, 860, t0 + hs).save(os.path.join(OUT, "approach_close_debug_1400x860.png"))
        made += ["approach_close_hold_start_1800x470.png", "approach_close_hold_full_1800x470.png", "approach_close_debug_1400x860.png"]
        check("hold_ring_fills", e0 is not None and e1 is not None and e0["e"]["all"] and e1["frac"] >= 1.0,
              f"ep {ep} 닫기 3 프레임 전 · 처음 {e0 and round(e0['frac'], 2)} → {hs:.1f} s 뒤 {e1 and round(e1['frac'], 2)} · dz {e1 and e1['e']['dz']}")
        # 하나 틀리면 0
        bad = dict(ec, height_cm=ec["height_cm"] + 2.0)
        scr.cfg = dict(cfg, sg50=dict(s50, end_condition=bad))
        scr.poll(t0 + 0.7)
        check("hold_resets_when_off", scr.endc is not None and not scr.endc["e"]["all"] and scr.endc["frac"] == 0.0)
        # 접근 유형 없는 줄 (기존 그룹) = 정답조건 표시 안 함
        row0 = dict(row)
        row0["approach_type"] = ""
        scr.cfg = cfg
        rc.write_json(os.path.join(live, "ui.json"), {**ui, "row": row0})
        scr.poll(t0 + 0.8)
        check("no_end_condition_for_old_groups", scr.endc is None)
    check("screenshots", all(os.path.exists(os.path.join(OUT, f)) for f in made), f"{len(made)} 장 → {OUT}")
    n_ok = sum(ok for _, ok, _ in RES)
    print(f"\n{n_ok}/{len(RES)} PASS")
    json.dump({"results": RES, "human_close_frac": frac, "scene": {"ep": int(ep), "close": int(ci)}},
              open(os.path.join(ROOT, "tests", "results", "test_sg_approach.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return 0 if n_ok == len(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
