#!/home/user/so101-env/bin/python
"""편향 구간 표시 영상 (읽기만 — dataset · review 영상은 바꾸지 않음). 2026-11-10 사용자 "동영상 처리를 해서 어느구간이 편향적으로 되어있는지".

판마다 review 영상 (front | wrist, 1280×480, dataset 프레임과 1:1) 위에:
  위 띠  — 시각 · 단계 (그리퍼 열기 전 / 열림~닫기 / 닫은 뒤) · 바깥 cm · 높이 cm (닫은 순간 그리퍼 끝 기준, FK) · 손목 dv (주황 닫기 자리 기준)
           색: 빨강 = 카메라 쪽으로 샘 (열림~닫기, 바깥 > out_thr, 높이 ≤ low_cm) · 주황 = 높은 곳에서 카메라 쪽 (높이 > low_cm) · 초록 = 닫기 1 s 전부터 · 회색 = 그 밖
  아래   — 판 전체 바깥 거리 곡선 (가운데 선 = 0 = 닫은 자리, 위 = 카메라 쪽), 색 구간, 지금 위치 세로선, 열림 · 닫기 표시
바깥 = 로봇 밑동 → 닫은 자리 방향 (지금 손목 카메라가 달린 쪽), 높이 + = 위.
→ <out>/episode_NNN_bias.mp4 · bias_segments.md (구간 표)

  ~/so101-env/bin/python sg_bias_video.py --session practice/sg50_rot_pilot4 [--episodes 0,2] [--out DIR] [--out-thr 0.3] [--low-cm 2.0]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

FONT = "/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf"
RED, ORANGE, GREEN, GRAY = (220, 38, 38), (234, 120, 20), (22, 163, 74), (75, 85, 99)


def segments(mask, fps):
    out, start = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            out.append((start, i - 1))
            start = None
    return [(a, b) for a, b in out if (b - a + 1) >= max(3, int(0.1 * fps))]   # 0.1 s 미만은 버림


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--episodes")
    ap.add_argument("--out")
    ap.add_argument("--out-thr", type=float, default=0.3)
    ap.add_argument("--low-cm", type=float, default=2.0)
    a = ap.parse_args(argv)
    import av
    import pandas as pd
    from PIL import Image, ImageDraw, ImageFont

    import sg_approach_check as X
    import sg_phase
    import sg_sticker as sgs

    sd = rc.session_dir(a.session)
    out = a.out or os.path.join(sd, "qa", "bias_videos")
    os.makedirs(out, exist_ok=True)
    df = pd.concat([pd.read_parquet(p, columns=["observation.state", "action", "episode_index", "frame_index"])
                    for p in sorted(glob.glob(f"{sd}/dataset/data/*/*.parquet"))])
    plan = {int(r["episode_index"]): r for r in rc.read_plan(sd)}
    tref = next((r for r in sgs.active_refs() if r.get("kind") == "target"), None)
    P = sgs.load_params()
    eps = sorted(df.episode_index.unique()) if not a.episodes else [int(x) for x in a.episodes.split(",")]
    fb, fs = ImageFont.truetype(FONT, 22), ImageFont.truetype(FONT, 15)
    md = [f"# {a.session} — 편향 구간 (읽기만, `tools/sg_bias_video.py`)", "",
          f"- 바깥 = 닫은 순간 그리퍼 끝 기준 로봇에서 먼 쪽 (지금 손목 카메라 쪽), FK. 빨강 = 그리퍼 열림~닫기 · 바깥 > {a.out_thr} cm · 높이 ≤ {a.low_cm} cm,"
          f" 주황 = 같은데 높이 > {a.low_cm} cm. 0.1 s 미만 구간은 뺌.", ""]
    summary = {}
    for ep in eps:
        e = df[df.episode_index == ep].sort_values("frame_index")
        st = np.stack(e["observation.state"].values).astype(float)
        ac = np.stack(e["action"].values).astype(float)
        idx = sg_phase.analyze(st, ac, 30)["_idx"]
        o, ci = int(idx["open"]), int(idx["close"])
        Pt = X.tips(st)
        D = X.decomp(Pt[ci], Pt)
        n = len(st)
        live = np.zeros(n, bool)
        live[o:ci] = True
        red = live & (D[:, 0] > a.out_thr) & (D[:, 2] <= a.low_cm)
        ora = live & (D[:, 0] > a.out_thr) & (D[:, 2] > a.low_cm)
        seg_r, seg_o = segments(red, 30), segments(ora, 30)
        vin = os.path.join(sd, "review_videos", f"episode_{ep:03d}.mp4")
        vout = os.path.join(out, f"episode_{ep:03d}_bias.mp4")
        cin = av.open(vin)
        sin = cin.streams.video[0]
        W0, H0 = sin.width, sin.height
        TOP, BOT = 64, 150
        cout = av.open(vout, "w")
        so = cout.add_stream("libx264", rate=30)
        so.width, so.height, so.pix_fmt = W0, H0 + TOP + BOT, "yuv420p"
        so.options = {"crf": "23", "preset": "veryfast"}
        # 아래 그래프 바탕 (한 번 그림)
        gx0, gx1, gy0, gy1 = 60, W0 - 20, 18, BOT - 28
        lim = 3.0   # ±3 cm 로 고정 (멀리서 다가오는 구간은 끝에 붙음) — 1 cm 안팎 차이가 보이게
        X_ = lambda i: gx0 + (gx1 - gx0) * i / max(1, n - 1)  # noqa: E731
        Y_ = lambda v: (gy0 + gy1) / 2 - (gy1 - gy0) / 2 * max(-1, min(1, v / lim))  # noqa: E731
        base = Image.new("RGB", (W0, BOT), (17, 24, 39))
        bd = ImageDraw.Draw(base)
        for (s_, e_), col in [(x, RED) for x in seg_r] + [(x, ORANGE) for x in seg_o]:
            bd.rectangle([X_(s_), gy0, X_(e_), gy1], fill=tuple(int(c * 0.45) for c in col))
        bd.line([(gx0, Y_(0)), (gx1, Y_(0))], fill=(156, 163, 175), width=1)
        bd.line([(gx0, Y_(a.out_thr)), (gx1, Y_(a.out_thr))], fill=(120, 60, 60), width=1)
        pts = [(X_(i), Y_(D[i, 0])) for i in range(n)]
        bd.line(pts[:o + 1], fill=(107, 114, 128), width=2)
        bd.line(pts[o:ci + 1], fill=(229, 231, 235), width=2)
        bd.line(pts[ci:], fill=(107, 114, 128), width=2)
        for i, t_ in ((o, "열림"), (ci, "닫기")):
            bd.line([(X_(i), gy0 - 4), (X_(i), gy1 + 4)], fill=(250, 204, 21), width=2)
            bd.text((X_(i) + 3, gy0 - 2), t_, font=fs, fill=(250, 204, 21))
        bd.text((6, gy0 - 4), f"+{lim:.0f}", font=fs, fill=(209, 213, 219))
        bd.text((6, Y_(0) - 8), " 0", font=fs, fill=(209, 213, 219))
        bd.text((6, gy1 - 14), f"-{lim:.0f}", font=fs, fill=(209, 213, 219))
        bd.text((gx0, BOT - 22), "바깥 cm (위 = 카메라 쪽, 0 = 닫은 자리) · 빨강 = 낮은 곳에서 카메라 쪽 · 주황 = 높은 곳에서 카메라 쪽", font=fs, fill=(209, 213, 219))
        dv_last = None
        for i, fr in enumerate(cin.decode(sin)):
            if i >= n:
                break
            img = fr.to_image()
            if o <= i <= ci and i % 3 == 0:
                c = sgs.target_compare(sgs.detect(np.asarray(img)[:, W0 // 2:], P), tref)
                dv_last = None if c is None else c["dv"]
            canvas = Image.new("RGB", (W0, H0 + TOP + BOT), (17, 24, 39))
            canvas.paste(img, (0, TOP))
            cd = ImageDraw.Draw(canvas)
            if red[i]:
                col, lab = RED, "카메라 쪽으로 샘 (낮은 곳)"
            elif ora[i]:
                col, lab = ORANGE, "높은 곳에서 카메라 쪽"
            elif ci - 30 <= i <= ci:
                col, lab = GREEN, "닫기 직전"
            else:
                col, lab = GRAY, ("그리퍼 열기 전" if i < o else ("닫은 뒤" if i > ci else "정상"))
            cd.rectangle([0, 0, W0, TOP], fill=col)
            ph = "열기 전" if i < o else ("닫은 뒤" if i > ci else "열림~닫기")
            txt = f"{i / 30:5.1f} s · {ph} · {lab}"
            cd.text((10, 6), txt, font=fb, fill=(255, 255, 255))
            sub = f"바깥 {D[i, 0]:+.2f} cm · 높이 {D[i, 2]:+.2f} cm (닫은 순간 기준)" + (f" · 손목 dv {dv_last:+.3f}" if (o <= i <= ci and dv_last is not None) else "")
            cd.text((10, 36), sub, font=fs, fill=(255, 255, 255))
            if col in (RED, ORANGE):
                cd.rectangle([W0 // 2, TOP, W0 - 1, TOP + H0 - 1], outline=col, width=6)
            g = base.copy()
            gd = ImageDraw.Draw(g)
            gd.line([(X_(i), gy0 - 6), (X_(i), gy1 + 6)], fill=(56, 189, 248), width=2)
            gd.ellipse([X_(i) - 4, Y_(D[i, 0]) - 4, X_(i) + 4, Y_(D[i, 0]) + 4], fill=(56, 189, 248))
            canvas.paste(g, (0, TOP + H0))
            for pkt in so.encode(av.VideoFrame.from_image(canvas)):
                cout.mux(pkt)
        for pkt in so.encode():
            cout.mux(pkt)
        cout.close()
        cin.close()
        pr = plan.get(ep) or {}
        lines = [f"## episode {ep} — {pr.get('position', '')} · 각도 {pr.get('angle', '')} · 노랑 {pr.get('wp_dir', '')}° · 열림 {o / 30:.1f} s · 닫기 {ci / 30:.1f} s",
                 f"- 영상: `{os.path.relpath(vout, sd)}`"]
        if not seg_r and not seg_o:
            lines.append("- 편향 구간 없음")
        for (s_, e_), kind in sorted([(x, "빨강 낮은 곳에서 카메라 쪽") for x in seg_r] + [(x, "주황 높은 곳에서 카메라 쪽") for x in seg_o]):
            mx = int(np.argmax(D[s_:e_ + 1, 0])) + s_
            lines.append(f"- {s_ / 30:5.1f}–{e_ / 30:5.1f} s ({(e_ - s_ + 1) / 30:.1f} s) {kind}: 최대 바깥 {D[mx, 0]:+.2f} cm (그때 높이 {D[mx, 2]:+.2f} cm, 닫기 {(ci - mx) / 30:.1f} s 전)")
        md += lines + [""]
        summary[int(ep)] = {"red": [(s_ / 30, e_ / 30) for s_, e_ in seg_r], "orange": [(s_ / 30, e_ / 30) for s_, e_ in seg_o]}
        print("\n".join(lines), flush=True)
    open(os.path.join(out, "bias_segments.md"), "w").write("\n".join(md) + "\n")
    json.dump(summary, open(os.path.join(out, "bias_segments.json"), "w"), ensure_ascii=False, indent=1)
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
