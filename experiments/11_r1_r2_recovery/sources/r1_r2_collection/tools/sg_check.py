#!/home/user/so101-env/bin/python
"""SG50 회차 판별 확인 (dataset 읽기만) — 2026-11-06 예비3 1회차 확인과 같은 항목 · 같은 기준.

  ~/so101-env/bin/python sg_check.py --session practice/sg50_pilot3 [--episodes 8-15]
  → <세션>/qa/check_ep{A}-{B}.md · .json, 화면에 표

항목 (판마다): 길이 · 그리퍼 열린 단계 · 열림 횟수 · 열림→닫기 s · 닫기 때 앞뒤 기울기 (수평계 보정 뒤, sg_viewer.tilt_zero) ·
닫기 자리 (활성 target ref) 4 항목 · 하강 앞뒤 길 (FK) · 다시 올라감 · 맞추기 wrist_roll · 최대거리 여유 (sg50.known_regions.reach) ·
놓은 자리 오차 (front 첫 프레임) · 끝 front 큐브 상자 안 · 시작/끝 S0 차.
튐 표시 (참고, 자동 제외 아님): FLAG 기준 아래.
"""

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

FLAG = {"end_dev_deg": 12.0, "tilt_deg": 8.0, "target_ok_max": 2, "reach_to_close_s": 18.0, "descent_path_cm": 18.0, "rerise_cm": 3.5}


def check(sess, eps=None):
    import glob

    import av
    import pandas as pd

    import sg_fk
    import sg_phase
    import sg_plan as sp
    import sg_sticker as ss
    import sg_viewer as sv

    cfg = rc.load_config(os.environ.get("R12_CONFIG") or os.path.join(rc.ROOT, "config", "sg50.yaml"))
    s50 = cfg["sg50"]
    sd = rc.session_dir(sess)
    plan = {int(r["episode_index"]): r for r in rc.read_plan(sd)}
    df = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{sd}/dataset/data/*/*.parquet"))])
    info = json.load(open(f"{sd}/dataset/meta/info.json"))
    em = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(f"{sd}/dataset/meta/episodes/*/*.parquet"))])
    ref = next((r for r in ss.active_refs() if r.get("kind") == "target"), None)
    P = ss.load_params()
    reach = (s50.get("known_regions") or {}).get("reach")
    S0 = np.array(list(s50["start_poses"][s50.get("fixed_pose", "S0")]["joints"].values())[:5], float)
    g = rc.group_for_session(cfg, sess)[1] or {}
    tmax = float(g.get("episode_time_s", 60))

    def frame(ep, cam, fi):
        er = em[em.episode_index == ep].iloc[0]
        k = f"observation.images.{cam}"
        p = f"{sd}/dataset/" + info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]), file_index=int(er[f"videos/{k}/file_index"]))
        t0 = float(er[f"videos/{k}/from_timestamp"])
        c = av.open(p)
        out = None
        try:
            for f in c.decode(video=0):
                if int(round((float(f.pts * f.time_base) - t0) * 30)) >= fi:
                    out = f.to_ndarray(format="rgb24")
                    break
        finally:
            c.close()
        return out

    rows = []
    for ep in sorted(int(e) for e in df.episode_index.unique()):
        if eps is not None and ep not in eps:
            continue
        e = df[df.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values)
        n = len(st)
        r = sg_phase.analyze(st, ac, 30)
        idx = r.get("_idx") or {}
        ci = idx.get("close")
        pr = plan.get(ep, {})
        x = {"ep": ep, "pos": pr.get("position", ""), "status": pr.get("status", ""), "retake_of": pr.get("retake_of", ""), "len_s": round(n / 30, 1),
             "open_stage": r.get("open_stage"), "open_events": r.get("open_events"), "open_to_close_s": r.get("open_to_close_s"), "flags": list(r["flags"])}
        if ci is not None:
            x["tilt"] = round(sg_fk.tool_tilt(st[ci, :5])[0] - sv.tilt_zero(s50, st[ci, 0]), 1)
            if ref:
                c = ss.target_compare(ss.detect(frame(ep, "wrist", ci), P), ref)
                if c:
                    x["target"] = {"ok": int(sum(c["ok"].values())), "du": c["du"], "dv": c["dv"], "size": c["size"], "dangle": c["dangle"]}
            rm = np.where(st[:, 1] - st[0, 1] > 20)[0]
            if len(rm) and rm[0] < ci:
                ri = int(rm[0])
                p, _ = sg_fk.fk(st[:, :5])
                p = p * 100
                k0 = ri + int(np.argmax(p[ri:ci + 1, 2]))
                D = p[k0:ci + 1]
                x["descent_path_cm"] = round(float(np.sum(np.abs(np.diff(np.hypot(D[:, 0], D[:, 1]))))), 1)
                x["rerise_cm"] = round(float(np.sum(np.clip(np.diff(D[:, 2]), 0, None))), 1)
            x["adjust_wroll"] = r.get("adjust_wroll_path_deg")
        if reach and pr.get("position"):
            rr, pan = sp.reach_fk(reach, *rc.known_xy(cfg, pr["position"]))
            x["reach_margin_cm"] = round(reach["max_r_cm"] + reach.get("side_cm", 0) * math.sin(math.radians(pan)) - rr, 1)
        f0 = (rc.vision(frame(ep, "front", 0), None, cfg).get("front") or {})
        if f0.get("detected") and pr.get("position"):
            px, py = rc.known_xy(cfg, pr["position"])
            x["place_err_cm"] = round(math.hypot(f0["xy_cm"][0] - px, f0["xy_cm"][1] - py), 1)
        fl = (rc.vision(frame(ep, "front", n - 1), None, cfg).get("front") or {})
        x["end_in_box"] = bool(fl.get("detected") and fl["xy_cm"][0] > 0)
        x["box_check"] = "front 끝" if x["end_in_box"] else ""
        if not x["end_in_box"]:  # 상자 안쪽 깊이 떨어지면 front 화면 아래 밖 → 놓은 뒤 0.5 s 손목 화면: 큐브 + 상자 바닥 (갈색) 으로 확인
            a_ = ac[:, 5]
            rel = None
            if ci is not None:  # 놓기 = 닫기 시작 뒤 그리퍼 명령이 그때까지 최소보다 10 넘게 다시 벌어진 첫 프레임 (잡을 때 명령이 '열림' 기준 위에 머물러도 찾음)
                lo = float(a_[ci])
                for k_ in range(ci, n):
                    lo = min(lo, float(a_[k_]))
                    if a_[k_] > lo + 10:
                        rel = k_
                        break
            if rel is not None:
                w = frame(ep, "wrist", min(rel + 15, n - 1))
                if w is not None:
                    import cv2

                    hsv = cv2.cvtColor(w, cv2.COLOR_RGB2HSV)
                    brown = float(((hsv[..., 0] >= 5) & (hsv[..., 0] <= 25) & (hsv[..., 1] >= 50) & (hsv[..., 2] >= 80)).mean())
                    cube = ss.detect(w, P).get("cube")
                    if cube and brown > 0.25:
                        x["end_in_box"], x["box_check"] = True, f"손목 (놓고 0.5 s, 상자 바닥 {brown:.0%})"
        x["start_dev"] = round(float(np.abs(st[0, :5] - S0).max()), 1)
        x["end_dev"] = round(float(np.abs(st[-1, :5] - S0).max()), 1)
        # 튐 표시
        why = []
        tt_ = float(s50.get("tilt_target_deg", 0.0))
        if x.get("tilt") is not None and abs(x["tilt"] - tt_) > FLAG["tilt_deg"]:
            why.append(f"기울기 {x['tilt']:+.1f}° (목표 {tt_:+g}°)")
        if x.get("target") and x["target"]["ok"] <= FLAG["target_ok_max"]:
            why.append(f"닫기 자리 {x['target']['ok']}/4")
        if (r.get("reach_to_close_s") or 0) > FLAG["reach_to_close_s"]:  # 2026-11-06: 그리퍼를 팬 정렬 직후 열므로 열림→닫기 대신 큰 팔 뻗기→닫기
            why.append(f"큰 팔 뻗기→닫기 {r['reach_to_close_s']} s")
        if (x.get("descent_path_cm") or 0) > FLAG["descent_path_cm"] or (x.get("rerise_cm") or 0) > FLAG["rerise_cm"]:
            why.append(f"하강 흔들림 ({x.get('descent_path_cm')} cm, 다시 올라감 {x.get('rerise_cm')})")
        if x["open_stage"] != "찾기 (큰 팔 뻗기 전)" or not 1 <= (x["open_events"] or 0) <= 2:  # 놓을 때 작게 열면 1 번으로 셈
            why.append(f"그리퍼 ({x['open_stage']}, 열림 {x['open_events']} 번)")
        if not x["end_in_box"]:
            why.append("상자 안 큐브 확인 못 함 (front 끝 · 손목 놓은 뒤)")
        if x["len_s"] >= tmax - 0.5:
            why.append("판 시간 상한")
        if x["end_dev"] > FLAG["end_dev_deg"]:
            j = ["pan", "lift", "elbow", "wflex", "wroll"][int(np.argmax(np.abs(st[-1, :5] - S0)))]
            why.append(f"끝 자세 S0 와 {x['end_dev']}° ({j})")
        if ci is None:
            why.append("닫기 없음")
        x["why"] = why
        rows.append(x)
    return rows


def main(argv):
    sess = argv[argv.index("--session") + 1]
    eps = None
    if "--episodes" in argv:
        a, _, b = argv[argv.index("--episodes") + 1].partition("-")
        eps = set(range(int(a), int(b or a) + 1))
    rows = check(sess, eps)
    if not rows:
        print("판 없음")
        return 1
    tag = f"ep{rows[0]['ep']}-{rows[-1]['ep']}"
    L = [f"# 판별 확인 {sess} {tag}", "", "- dataset 읽기만 (`tools/sg_check.py`). 기울기 = 수평계 보정 뒤 (0 = 지면과 수직, + = 손끝이 로봇에서 멀리), 튐은 sg50.tilt_target_deg 와 차이. 닫기 자리 = 활성 target ref.",
         f"- 튐 기준 (참고): |기울기 − 목표| > {FLAG['tilt_deg']}° · 닫기 자리 ≤ {FLAG['target_ok_max']}/4 · 큰 팔 뻗기→닫기 > {FLAG['reach_to_close_s']} s · 하강 앞뒤 길 > {FLAG['descent_path_cm']} cm 또는 다시 올라감 > {FLAG['rerise_cm']} cm · 그리퍼 큰 팔 뻗기 뒤 엶 / 열림 0 또는 3 번 이상 · 끝 상자 안 못 봄 · 판 시간 상한 · 끝 자세 S0 와 > {FLAG['end_dev_deg']}°.", "",
         "| ep | 자리 | 재촬영 | 길이 s | 그리퍼 | 열림→닫기 s | 기울기 | 닫기 자리 (du, dv, 크기, 회전) | 하강 길 (다시 올라감) cm | 맞추기 roll° | 최대거리 여유 cm | 놓은 오차 cm | 끝 상자 | 시작/끝 S0° | 튐 |",
         "|---:|---|---|---:|---|---:|---:|---|---|---:|---:|---:|---|---|---|"]
    for x in rows:
        t = x.get("target") or {}
        tt = f"{t.get('ok')}/4 ({t.get('du'):+.3f}, {t.get('dv'):+.3f}, {t.get('size'):.2f}, {t.get('dangle'):+.1f})" if t else "-"
        L.append(f"| {x['ep']} | {x['pos']} | {('ep' + x['retake_of']) if x['retake_of'] else ''} | {x['len_s']} | {x['open_stage']} · {x['open_events']} | {x.get('open_to_close_s')} | "
                 f"{x.get('tilt', '-'):+} | {tt} | {x.get('descent_path_cm')} ({x.get('rerise_cm')}) | {x.get('adjust_wroll')} | {x.get('reach_margin_cm')} | {x.get('place_err_cm')} | "
                 f"{('안 (' + x['box_check'] + ')') if x['end_in_box'] else '못 봄'} | {x['start_dev']}/{x['end_dev']} | {'; '.join(x['why']) or '—'} |")
    out = os.path.join(rc.session_dir(sess), "qa", f"check_{tag}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(L) + "\n")
    with open(out[:-3] + ".json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1, default=str)
    print("\n".join(L[5:]))
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
