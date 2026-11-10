#!/home/user/so101-env/bin/python
"""SG50 판 단계 확인 (dataset 읽기만). 사용자 진행 (2026-11-06 예비2): Pan 정렬 → 손목으로 큐브 찾기 → 그리퍼 열기 →
팔 뻗어 내려가기 · 맞추기 → 닫기 → 상자. 예비1 은 '팔 뻗은 뒤 열기' 였음 — 두 방식을 '열린 단계' 로 구분해 보여 준다.

팔로워 관절값 (observation.state) 과 리더 그리퍼 명령 (action) 으로 단계 시각을 찾는다. 자동 성공 판정 · 학습 제외는 하지 않음.

  ~/so101-env/bin/python sg_phase.py --session practice/sg50_pilot [--episodes 0,2] [--no-images]
  → <세션>/qa/sg_phase.md · sg_phase.csv · sg_phase_ep###.jpg (front 위 · wrist 아래: Pan 정렬 끝 · 열기 전 멈춤 · 열림 · 닫기 시작)

정의 (30 fps, 각도 °):
  움직임 = 0.2 s 사이 변화 / 0.2 s > MOVE_DPS (lift · elbow · wrist_flex 중 최대 = 팔, pan 따로)
  큰 팔 뻗기 시작 = shoulder_lift 가 시작값보다 REACH_LIFT 넘게 올라간 첫 프레임 (손목 숙이기 · 작은 lift 조정은 '찾기')
  Pan 정렬 = 큰 팔 뻗기 전 pan 움직임
  열림 = 리더 그리퍼 명령이 시작값 + OPEN_MIN 을 처음 넘은 프레임. 열림 횟수 = 명령이 (시작값 + 최고값)/2 를 아래→위로 넘은 횟수
         (보통 2 = 큐브 집기 전 1 + 상자에 놓기 1, 더 많으면 다시 열림)
  열린 단계 = '찾기 (큰 팔 뻗기 전)' 또는 '팔 뻗은 뒤'
  닫기 시작 = 열림 뒤 명령이 그때까지 최고값의 70 % 아래로 처음 내려간 프레임
  맞추기 양 = 큰 팔 뻗기 시작 → 닫기 시작 사이 pan · wrist_roll 움직임 길이 합 (°)
"""

import csv
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

MOVE_DPS = 15.0
OPEN_MIN = 8.0
REACH_LIFT = 20.0
WIN = 6  # 0.2 s
J = ["pan", "lift", "elbow", "wflex", "wroll", "grip"]
FIELDS = ["episode_index", "cube_position", "status", "length_s", "pan_moved_deg", "pan_align_start_s", "pan_align_end_s",
          "reach_start_s", "arm_stop_s", "still_before_open_s", "open_s", "open_stage", "close_s", "open_to_close_s", "arm_change_open_to_close_deg",
          "pan_change_open_to_close_deg", "adjust_pan_path_deg", "adjust_wroll_path_deg", "open_events", "wrist_cube_at_open", "wrist_cube_u_at_open", "wrist_cube_v_at_open",
          "wrist_cube_area_at_open", "flags", "order_text"]


def _speed(x, fps):
    v = np.zeros_like(x)
    v[WIN:] = np.abs(x[WIN:] - x[:-WIN]) * fps / WIN
    return v


def analyze(st, ac, fps):
    """st, ac: (n, 6). 반환 dict (시각 = 초, 없으면 None)."""
    n = len(st)
    t = np.arange(n) / fps
    a = ac[:, 5]
    g0 = float(np.median(a[: min(10, n)]))
    arm_v = np.max(np.stack([_speed(st[:, j], fps) for j in (1, 2, 3)]), 0)
    pan_v = _speed(st[:, 0], fps)
    out = {"length_s": round(t[-1], 2), "flags": []}
    op = np.where(a > g0 + OPEN_MIN)[0]
    if not len(op):
        out["flags"].append("그리퍼 열림 없음")
        return out
    oi = int(op[0])
    # 열림 횟수 (반값 위로 넘기)
    half = g0 + (a.max() - g0) / 2
    above = a > half
    out["open_events"] = int(np.sum(above[1:] & ~above[:-1]) + int(above[0]))
    # 닫기 시작
    ci = None
    run = a[oi]
    for k in range(oi, n):
        run = max(run, a[k])
        if a[k] < 0.7 * run and run > g0 + OPEN_MIN:
            ci = k
            break
    end = ci if ci is not None else n - 1
    # 큰 팔 뻗기 — shoulder_lift 가 시작값보다 REACH_LIFT 넘게 올라간 첫 프레임 (닫기 전까지에서)
    rm = np.where(st[: end + 1, 1] - st[0, 1] > REACH_LIFT)[0]
    ri = int(rm[0]) if len(rm) else None
    out["reach_start_s"] = round(t[ri], 2) if ri is not None else None
    # Pan 정렬 = 큰 팔 뻗기 전 (없으면 닫기 전) pan 움직임
    pw = ri if ri is not None else end
    pan_moved = float(np.max(np.abs(st[: pw + 1, 0] - st[0, 0])))
    out["pan_moved_deg"] = round(pan_moved, 1)
    pm = np.where(pan_v[: pw + 1] > MOVE_DPS)[0]
    if pan_moved > 5 and len(pm):
        out["pan_align_start_s"], out["pan_align_end_s"] = round(t[pm[0]], 2), round(t[pm[-1]], 2)
    am = np.where(np.maximum(arm_v, pan_v)[: oi + 1] > MOVE_DPS)[0]
    si = int(am[-1]) if len(am) else None
    out["arm_stop_s"] = round(t[si], 2) if si is not None else None
    out["still_before_open_s"] = round(t[oi] - t[si], 2) if si is not None else None
    out["open_s"] = round(t[oi], 2)
    out["open_stage"] = "찾기 (큰 팔 뻗기 전)" if (ri is None or oi < ri) else "팔 뻗은 뒤"
    out["close_s"] = round(t[ci], 2) if ci is not None else None
    if ci is not None:
        out["open_to_close_s"] = round(t[ci] - t[oi], 2)
        seg = st[oi: ci + 1]
        out["arm_change_open_to_close_deg"] = round(float(np.max(np.abs(seg[:, 1:4] - seg[0, 1:4]))), 1)
        out["pan_change_open_to_close_deg"] = round(float(np.max(np.abs(seg[:, 0] - seg[0, 0]))), 1)
        if ri is not None and ri < ci:
            adj = st[ri: ci + 1]
            out["adjust_pan_path_deg"] = round(float(np.sum(np.abs(np.diff(adj[:, 0])))), 1)
            out["adjust_wroll_path_deg"] = round(float(np.sum(np.abs(np.diff(adj[:, 4])))), 1)
    # 표시 (판정 아님)
    f = out["flags"]
    # 2026-11-06 사용자 순서 (숄더팬 → 그리퍼 열기 → 찾기 → 이동): 팬 미세 조정 중 · 큐브가 손목에 보이기 전 여는 것은 정상 → 표시 안 함
    if arm_v[oi] > MOVE_DPS:
        f.append("팔이 움직이는 중에 열림")
    if ci is None:
        f.append("닫기 없음")
    if ci is not None and ri is not None and ri < ci:
        out["reach_to_close_s"] = round(t[ci] - t[ri], 2)
    if out["open_events"] > 2:
        f.append(f"다시 열림 (열림 {out['open_events']} 번, 보통 2)")
    idx = {"pan_end": int(pm[-1]) if (pan_moved > 5 and len(pm)) else None, "stop": si, "open": oi, "close": ci}
    out["_idx"] = idx
    return out


def order_text(r):
    p = (f"Pan 정렬 {r['pan_align_start_s']}–{r['pan_align_end_s']} s ({r['pan_moved_deg']}°)" if r.get("pan_align_end_s") is not None
         else f"Pan 정렬 거의 없음 ({r.get('pan_moved_deg')}°)")
    return (f"{p} → 멈춤 {r.get('still_before_open_s')} s → 그리퍼 열림 {r.get('open_s')} s [{r.get('open_stage')}] → "
            f"큰 팔 뻗기 {r.get('reach_start_s')} s → 닫기 시작 {r.get('close_s')} s (열림→닫기 {r.get('open_to_close_s')} s, "
            f"맞추기 pan {r.get('adjust_pan_path_deg')}° · wrist_roll {r.get('adjust_wroll_path_deg')}°)")


def _frames(sess_dir, info, er, cam, idxs):
    import av

    k = f"observation.images.{cam}"
    p = os.path.join(sess_dir, "dataset", info["video_path"].format(video_key=k, chunk_index=int(er[f"videos/{k}/chunk_index"]),
                                                                    file_index=int(er[f"videos/{k}/file_index"])))
    t0 = float(er[f"videos/{k}/from_timestamp"])
    fps = info["fps"]
    want = sorted(set(i for i in idxs if i is not None))
    out = {}
    c = av.open(p)
    try:
        s = c.streams.video[0]
        c.seek(max(0, int((t0 + want[0] / fps - 1.0) / float(s.time_base))), stream=s, backward=True)
        for fr in c.decode(s):
            fi = int(round((float(fr.pts * s.time_base) - t0) * fps))
            if fi in want and fi not in out:
                out[fi] = fr.to_ndarray(format="rgb24")
            if fi > want[-1]:
                break
    finally:
        c.close()
    return out


def main(argv):
    import pandas as pd

    sess = argv[argv.index("--session") + 1]
    sess_dir = rc.session_dir(sess)
    only = [int(x) for x in argv[argv.index("--episodes") + 1].split(",")] if "--episodes" in argv else None
    with open(os.path.join(sess_dir, "dataset", "meta", "info.json")) as f:
        info = json.load(f)
    fps = info["fps"]
    df = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(sess_dir, "dataset", "data", "*", "*.parquet")))])
    em = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(sess_dir, "dataset", "meta", "episodes", "*", "*.parquet")))])
    plan = {int(r["episode_index"]): r for r in rc.read_plan(sess_dir)}
    import sg_sticker as ss

    P = ss.load_params()
    cross = next((r for r in ss.active_refs() if r.get("kind") == "cross"), None)
    qa = os.path.join(sess_dir, "qa")
    os.makedirs(qa, exist_ok=True)
    rows = []
    for ep in sorted(int(e) for e in df.episode_index.unique()):
        if only is not None and ep not in only:
            continue
        e = df[df.episode_index == ep].sort_values("frame_index")
        st, ac = np.stack(e["observation.state"].values), np.stack(e["action"].values)
        r = analyze(st, ac, fps)
        pr = plan.get(ep, {})
        r.update(episode_index=ep, cube_position=pr.get("position", ""), status=pr.get("status", ""))
        idx = r.pop("_idx", {})
        er = em[em.episode_index == ep].iloc[0]
        if idx.get("open") is not None:
            fr = {cam: _frames(sess_dir, info, er, cam, list(idx.values())) for cam in ("front", "wrist")}
            w = fr["wrist"].get(idx["open"])
            if w is not None:
                d = ss.detect(w, P)
                c = d.get("cube")
                r["wrist_cube_at_open"] = "보임" if c else "안 보임"
                if c:
                    r.update(wrist_cube_u_at_open=c["u"], wrist_cube_v_at_open=c["v"], wrist_cube_area_at_open=c["area_px"])
            if "--no-images" not in argv:
                _sheet(fr, idx, r, cross, os.path.join(qa, f"sg_phase_ep{ep:03d}.jpg"))
        r["order_text"] = order_text(r)
        r["flags"] = "; ".join(r["flags"])
        rows.append(r)
        print(f"ep{ep} {r['cube_position']} {r['status']}: {r['order_text']}" + (f"  ⚠ {r['flags']}" if r["flags"] else "  · 표시 없음"))
    with open(os.path.join(qa, "sg_phase.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    L = [f"# SG50 판 단계 확인 — {sess}", "",
         "- dataset 읽기만. 팔로워 관절값 · 리더 그리퍼 명령으로 단계 시각을 찾음 (정의는 tools/sg_phase.py 맨 위). 판정 · 제외 아님.",
         "- 확인할 것: 그리퍼가 '큐브 찾기' 단계 (Pan 정렬 · 손목으로 큐브를 본 뒤, 큰 팔 뻗기 전) 에서 열렸는지 = '열린 단계' 칸.", "",
         "| ep | 큐브 | 상태 | Pan 정렬 s | 멈춤 s | 열림 s | 열린 단계 | 큰 팔 뻗기 s | 닫기 s | 열림→닫기 s | 맞추기 pan° · roll° | 열림 때 손목 큐브 (u, v) | 열림 횟수 | 표시 |",
         "|---:|---|---|---|---:|---:|---|---:|---:|---:|---|---|---:|---|"]
    for r in rows:
        pa = f"{r.get('pan_align_start_s')}–{r.get('pan_align_end_s')} ({r.get('pan_moved_deg')}°)" if r.get("pan_align_end_s") is not None \
            else f"없음 ({r.get('pan_moved_deg')}°)"
        cube = (f"보임 ({r['wrist_cube_u_at_open']:.2f}, {r['wrist_cube_v_at_open']:.2f})" if r.get("wrist_cube_u_at_open") is not None
                else r.get("wrist_cube_at_open", ""))
        L.append(f"| {r['episode_index']} | {r['cube_position']} | {r['status']} | {pa} | {r.get('still_before_open_s')} | {r.get('open_s')} | "
                 f"{r.get('open_stage')} | {r.get('reach_start_s')} | {r.get('close_s')} | {r.get('open_to_close_s')} | "
                 f"{r.get('adjust_pan_path_deg')} · {r.get('adjust_wroll_path_deg')} | {cube} | {r.get('open_events')} | {r['flags'] or '—'} |")
    if cross:
        L += ["", f"- 손목 십자 (참고) {cross['version']} u {cross['u']:.3f} · v {cross['v']:.3f}."]
    L += ["", "- 그림 `sg_phase_ep###.jpg`: 왼쪽부터 Pan 정렬 끝 · 열기 전 멈춤 · 그리퍼 열림 · 닫기 시작 (위 front · 아래 wrist)."]
    with open(os.path.join(qa, "sg_phase.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"→ {os.path.join(qa, 'sg_phase.md')}")
    return 0


def _sheet(fr, idx, r, cross, path):
    from PIL import Image, ImageDraw, ImageFont

    W, H = 320, 240
    keys = [("pan_end", "Pan 정렬 끝"), ("stop", "열기 전 멈춤"), ("open", "그리퍼 열림"), ("close", "닫기 시작")]
    im = Image.new("RGB", (W * 4, H * 2 + 24), (17, 24, 39))
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf", 15)
    except OSError:
        fnt = None
    for i, (k, name) in enumerate(keys):
        fi = idx.get(k)
        d.text((i * W + 6, 4), f"ep{r['episode_index']} {name}" + (f" {fi / 30:.1f}s" if fi is not None else " (없음)"), fill=(250, 204, 21), font=fnt)
        for row, cam in enumerate(("front", "wrist")):
            a = fr[cam].get(fi) if fi is not None else None
            if a is None:
                continue
            t = Image.fromarray(a).resize((W, H))
            if cam == "wrist" and cross:
                dd = ImageDraw.Draw(t)
                cx, cy = cross["u"] * W, cross["v"] * H
                for x in range(0, W, 12):
                    dd.line([(x, cy), (x + 6, cy)], fill=(249, 115, 22), width=1)
                for y in range(0, H, 12):
                    dd.line([(cx, y), (cx, y + 6)], fill=(249, 115, 22), width=1)
            im.paste(t, (i * W, 24 + row * H))
    im.save(path, quality=85)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
