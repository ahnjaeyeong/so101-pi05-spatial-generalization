#!/home/user/so101-env/bin/python
"""SG 접근 유형 · 정답조건 판 뒤 검사 (읽기만 — dataset · 계획은 바꾸지 않음). 2026-11-09.

판마다 (sg_phase '닫기 시작' = ci):
  실제 접근 유형 — FK 그리퍼 끝을 닫기 위치 기준 (바깥 = 밑동 → 닫기 위치 방향, 옆 + = 팬 + 쪽 = 로봇 오른쪽, 높이) 으로 나눔.
    k* = 닫기 전 10 s 안에서 닫기 위치와 수평 거리 ≥ 1 cm 였던 마지막 프레임.
    k* 의 높이 > 1.5 cm (아직 위) 또는 k* 없음 → A (위에서) · 아니면 수평 성분이 큰 쪽: 바깥 < 0 → B (안쪽에서) · > 0 → C (바깥에서) · 옆 > 0 → D+ · < 0 → D-.
    잡는 높이 근처 (닫기 높이 + 1 cm 안) 에 온 뒤 바깥으로 ≥ 0.8 cm 지나갔다 돌아왔으면 E.
  정답조건 (sg50.end_condition) — 닫기 3 프레임 전 손목 + 관절값: u · v · 크기 · 높이, 닫기 직전 네 가지가 모두 맞은 채 이어진 시간 (s).
  지나침 — 닫기 전 10 s 안 바깥으로 닫기 위치를 넘은 최대 거리 (cm).
  노란 프레임 (계획 줄에 wp_u 가 있을 때) — 그리퍼 연 뒤부터 닫기까지 손목 영상 (3 프레임마다) 에서 큐브가 노란 프레임 허용 안에 들어온 첫 시각,
    그때 큐브가 주황 닫기 자리 기준 어느 화면 방향에 있었나 (°, 0 = 오른쪽 · 90 = 아래) ↔ 계획 방향 (±45° 안이면 같음).
→ 화면 표 · <세션>/qa/approach_check.csv · approach_check.md

  ~/so101-env/bin/python sg_approach_check.py --session practice/sg50_approach [--episodes 0,3,5]
"""
import argparse
import csv
import glob
import json
import os
import math
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

J5 = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")


def tips(q):
    import sg_fk

    p, _ = sg_fk.fk(np.atleast_2d(q)[:, :5])
    return p * 100.0


def decomp(pc, P):
    """닫기 위치 pc (cm, FK 원점 = 밑동) 기준 (바깥, 옆 (팬 + 쪽), 높이)."""
    r = pc[:2] / max(np.linalg.norm(pc[:2]), 1e-6)
    t = np.array([r[1], -r[0]])            # 팬 + = FK y − 쪽 (팬 +20° → 끝 y −5 cm)
    d = P - pc
    return np.c_[d[:, :2] @ r, d[:, :2] @ t, d[:, 2]]


def classify(D, ci, fps=30):
    lo = max(0, ci - 10 * fps)
    hor = np.hypot(D[lo:ci, 0], D[lo:ci, 1])
    far = np.where(hor >= 1.0)[0]
    zc = 0.0
    near = np.where(D[lo:ci, 2] <= zc + 1.0)[0]
    over = 0.0
    if len(near):
        seg = D[lo + near[0]:ci, 0]
        over = float(seg.max()) if len(seg) else 0.0
    if not len(far):
        return "A", over, None
    k = lo + far[-1]
    if D[k, 2] > 1.5:
        typ = "A"
    elif abs(D[k, 0]) >= abs(D[k, 1]):
        typ = "B" if D[k, 0] < 0 else "C"
    else:
        typ = "D+" if D[k, 1] > 0 else "D-"
    if over >= 0.8 and typ in ("B", "A"):
        typ = "E"
    return typ, over, k


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--episodes")
    ap.add_argument("--out", help="결과 폴더 (기본 <세션>/qa)")
    a = ap.parse_args(argv)
    import av
    import pandas as pd

    import sg_phase
    import sg_sticker as sgs
    import sg_viewer as sv

    cfg = rc.load_config(os.environ.get("R12_CONFIG") or os.path.join(rc.ROOT, "config", "sg50.yaml"))
    s50 = cfg["sg50"]
    ec = s50.get("end_condition") or {}
    sd = rc.session_dir(a.session)
    plan = {int(r["episode_index"]): r for r in rc.read_plan(sd)}
    info = json.load(open(f"{sd}/dataset/meta/info.json"))
    em = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{sd}/dataset/meta/episodes/*/*.parquet"))])
    df = pd.concat([pd.read_parquet(p, columns=["observation.state", "action", "episode_index", "frame_index"])
                    for p in sorted(glob.glob(f"{sd}/dataset/data/*/*.parquet"))])
    tref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    P = sgs.load_params()
    eps = sorted(df.episode_index.unique()) if not a.episodes else [int(x) for x in a.episodes.split(",")]
    fps = int(info.get("fps", 30))

    def wrist_frames(ep, i0, i1):
        er = em[em.episode_index == ep].iloc[0]
        k = "observation.images.wrist"
        p = f"{sd}/dataset/" + info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]),
                                                          file_index=int(er[f"videos/{k}/file_index"]))
        t0 = float(er[f"videos/{k}/from_timestamp"])
        out = {}
        c = av.open(p)
        s = c.streams.video[0]
        c.seek(int((t0 + i0 / fps - 1.0) / float(s.time_base)), stream=s, backward=True)
        for f in c.decode(s):
            fi = int(round((float(f.pts * s.time_base) - t0) * fps))
            if i0 <= fi <= i1:
                out[fi] = f.to_ndarray(format="rgb24")
            if fi > i1:
                break
        c.close()
        return out

    rows = []
    for ep in eps:
        e = df[df.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        try:
            ci = sg_phase.analyze(st, ac, fps)["_idx"]["close"]
        except Exception as ex:  # 닫기 못 찾음
            rows.append(dict(episode=ep, planned=(plan.get(ep) or {}).get("approach_type", ""), actual="?", note=f"닫기 못 찾음 {ex!r}"))
            continue
        Pt = tips(st)
        D = decomp(Pt[ci], Pt)
        typ, over, k = classify(D, ci, fps)
        prow = plan.get(ep) or {}
        wp_res = {}
        wref = sv.waypoint_ref(cfg, prow, tref) if prow.get("wp_u") else None
        if wref is not None:
            try:
                o_ = sg_phase.analyze(st, ac, fps)["_idx"]["open"]
            except Exception:
                o_ = max(0, ci - 15 * fps)
            WW = wrist_frames(ep, o_, ci)
            hit = None
            for fi in range(o_, ci, 3):
                w = WW.get(fi)
                c_ = sgs.target_compare(sgs.detect(w, P), wref) if w is not None else None
                if c_ and c_["ok"]["u"] and c_["ok"]["v"] and c_["ok"]["size"]:
                    hit = fi
                    break
            if hit is not None:
                cc = sgs.target_compare(sgs.detect(WW[hit], P), tref)
                ang = math.degrees(math.atan2(cc["dv"] * 480.0, cc["du"] * 640.0)) % 360 if cc else None
                pd = float(prow["wp_dir"])
                ok_at = None   # 노랑 지난 뒤 처음으로 정답조건 네 가지가 다 맞은 때
                for fj in range(hit, ci, 3):
                    w2 = WW.get(fj)
                    r2 = sv.end_check(sgs.detect(w2, P), tref, ec, float(Pt[fj, 2])) if w2 is not None else None
                    if r2 and r2["all"]:
                        ok_at = fj
                        break
                wp_res = dict(wp_passed=True, wp_pass_s=round(hit / fps, 2), wp_before_close_s=round((ci - hit) / fps, 2),
                              wp_to_ok_s=None if ok_at is None else round((ok_at - hit) / fps, 2),
                              wp_dir_actual=None if ang is None else round(ang), wp_dir_planned=round(pd),
                              wp_dir_match=None if ang is None else ("O" if abs((ang - pd + 180) % 360 - 180) <= 45 else "X"))
            else:
                wp_res = dict(wp_passed=False, wp_dir_planned=round(float(prow["wp_dir"])))
        W = wrist_frames(ep, max(0, ci - 8 * fps), ci)   # 2026-11-10 멈춤 (유지) 은 최대 8 s 까지 잼 (이전 2 s 에서 잘림)
        okrun, hold = True, 0
        end_ok = None
        for fi in range(ci - 1, max(-1, ci - 8 * fps - 1), -1):
            w = W.get(fi)
            if w is None:
                break
            res = sv.end_check(sgs.detect(w, P), tref, ec, float(Pt[fi, 2]))
            if fi == ci - 3:
                end_ok = res
            if okrun and res and res["all"]:
                hold += 1
            else:
                okrun = False
            if not okrun and fi < ci - 3:
                break
        pl = (plan.get(ep) or {}).get("approach_type", "")
        r = dict(episode=ep, position=(plan.get(ep) or {}).get("position", ""), planned=pl, actual=typ,
                 match="" if not pl else ("O" if pl == typ else "X"), hold_s=round(hold / fps, 2),
                 end_all=None if end_ok is None else bool(end_ok["all"]),
                 end_u=None if not end_ok or not end_ok["c"] else end_ok["c"]["du"], end_v=None if not end_ok or not end_ok["c"] else end_ok["c"]["dv"],
                 end_size=None if not end_ok or not end_ok["c"] else end_ok["c"]["size"], end_dz_cm=None if not end_ok or end_ok["dz"] is None else round(end_ok["dz"], 2),
                 overshoot_out_cm=round(over, 2), entry_from_cm=None if k is None else ";".join(f"{x:+.2f}" for x in D[k]),
                 close_s=round(ci / fps, 2), note="", **wp_res)
        rows.append(r)
        print(f"ep {ep:3d} {r['position']:6s} 계획 {pl or '—':3s} 실제 {typ:3s} {r['match'] or ' '} · 유지 {r['hold_s']:.2f} s · 닫기 때 정답조건 "
              f"{'O' if r['end_all'] else 'X'} (du {r['end_u']} dv {r['end_v']} 크기 {r['end_size']} 높이 {r['end_dz_cm']}) · 지나침 {over:+.2f} cm"
              + ("" if not wp_res else (f" · 노랑 지남 {wp_res.get('wp_before_close_s')} s 전 → 주황 맞춤까지 {wp_res.get('wp_to_ok_s')} s · 방향 {wp_res.get('wp_dir_actual')}° (계획 {wp_res['wp_dir_planned']}°) {wp_res.get('wp_dir_match')}"
                                        if wp_res.get("wp_passed") else f" · 노랑 안 지남 (계획 {wp_res['wp_dir_planned']}°)")), flush=True)
    out = a.out or f"{sd}/qa"
    os.makedirs(out, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    for r in rows:
        for f_ in r:
            if f_ not in fields:
                fields.append(f_)
    with open(f"{out}/approach_check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    hold_s = float(ec.get("hold_s", 0.5))
    good = [r for r in rows if r.get("actual") != "?"]
    L = [f"# {a.session} — 접근 유형 · 정답조건 판 뒤 검사 ({len(good)}편, 읽기만)", "",
         f"- 정답조건: u · v ±{ec.get('tol_uv')} · 크기 ±{ec.get('tol_size')} · 높이 {ec.get('height_cm')} ± {ec.get('tol_height_cm')} cm · 유지 {hold_s} s",
         f"- 계획과 같은 유형: {sum(r['match'] == 'O' for r in good)}/{sum(bool(r['planned']) for r in good)}",
         f"- 닫기 때 정답조건 맞음: {sum(bool(r['end_all']) for r in good)}/{len(good)} · 유지 ≥ {hold_s} s: {sum(r['hold_s'] >= hold_s for r in good)}/{len(good)}",
         f"- 실제 유형: " + ", ".join(f"{t} {sum(r['actual'] == t for r in good)}" for t in ("A", "B", "C", "D+", "D-", "E")),
         (f"- 노란 프레임 지남: {sum(bool(r.get('wp_passed')) for r in good)}/{sum('wp_passed' in r for r in good)} · 방향 같음 {sum(r.get('wp_dir_match') == 'O' for r in good)}"
          if any("wp_passed" in r for r in good) else "- 노란 프레임: 계획 없음"), "",
         "| ep | 자리 | 계획 | 실제 | 같음 | 유지 s | 정답조건 | du | dv | 크기 | 높이 cm | 지나침 cm |", "|---:|---|---|---|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in good:
        L.append(f"| {r['episode']} | {r['position']} | {r['planned']} | {r['actual']} | {r['match']} | {r['hold_s']} | {'O' if r['end_all'] else 'X'} | "
                 f"{r['end_u']} | {r['end_v']} | {r['end_size']} | {r['end_dz_cm']} | {r['overshoot_out_cm']} |")
    open(f"{out}/approach_check.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[2:6]))
    print(f"→ {out}/approach_check.csv · approach_check.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
