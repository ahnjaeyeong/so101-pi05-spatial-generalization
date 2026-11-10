#!/home/user/so101-env/bin/python
"""스티커 검출 · 표시 시험 (로봇 · 카메라 없음). 실제 d2 손목 영상 프레임 (스티커 없음) + [합성] 흰 사각형을 붙인 프레임.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_sticker.py [--out DIR] [--n-neg 600]

확인
  N1 실제 프레임 (스티커 없음) 에서 '검출 · 불확실' 0 (거짓 검출)
  P1 [합성] 큐브 윗면 안 흰 사각형 → 검출, 중심 오차 ≤ 2 px
  P2 [합성] 작은 밝은 반사 줄 (분홍빛 흰색) → 검출 아님
  P3 [합성] 손가락 끝 모양 회색-흰 띠가 바깥에서 들어와 스티커 반을 덮음 → 검출 아님 (불확실 · 미검출)
  P4 [합성] 스티커가 영상 가장자리에 걸림 → 불확실
  P5 [합성] 큐브가 화면 밖 (영상 이동) → 큐브 없음 · 스티커 없음
  P6 [합성] 같은 크기 스티커 둘 → 불확실
  P7 원본 배열 불변 (detect · draw_wrist 전후 해시 같음)
  P8 표시 크기 320 · 640 · 1100 · 1700 폭에서 표시 점 위치 = (u·W, v·H) ±1 px
  P9 영상 멈춤 (새 순번 없음 0.6 s) · 같은 프레임 반복 → stale, 표시에 스티커 점 없음
  P10 이전 프레임에서 검출됐어도 지금 프레임에 스티커가 없으면 '미검출' (위치를 이어 쓰지 않음)
"""

import glob
import hashlib
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)
import sg_sticker as sgs  # noqa: E402
import sg_viewer as sgv  # noqa: E402

D2_WRIST = sorted(glob.glob(os.path.expanduser("~/so101_runs/main_k8/d2/dataset/videos/observation.images.wrist/chunk-000/*.mp4")))
P = sgs.load_params(None)  # 기본값 (설정 파일 없이)
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
N_NEG = int(sys.argv[sys.argv.index("--n-neg") + 1]) if "--n-neg" in sys.argv else 600
results = []


def ok(name):
    results.append(name)
    print(f"  ✓ {name}", flush=True)


def frames(every, limit):
    import av

    n = 0
    for vp in D2_WRIST:
        c = av.open(vp)
        try:
            for i, f in enumerate(c.decode(video=0)):
                if i % every:
                    continue
                yield vp, i, f.to_ndarray(format="rgb24")
                n += 1
                if n >= limit:
                    return
        finally:
            c.close()


def sticker_spot(img, side):
    """빨강 마스크 안에 side×side 정사각형이 통째로 들어가는 자리 중 큐브 중심에 가장 가까운 곳 (윗면 · 옆면 상관없음)."""
    import cv2

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    red = sgs._hsv_mask(hsv, P["red_hsv"])
    ins = cv2.erode(red, np.ones((side + 6, side + 6), np.uint8))
    ys, xs = np.nonzero(ins)
    if len(xs) == 0:
        return None
    m = cv2.moments(red, binaryImage=True)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    k = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    return int(xs[k]), int(ys[k])


def paste_sticker(img, c, side, col=(236, 236, 230), rot=0.0):
    """[합성] 흰 사각형 (가장자리 1 px 흐림 · 잡음). 반환 새 배열 + 실제 중심."""
    import cv2

    out = img.copy()
    m = np.zeros(img.shape[:2], np.uint8)
    box = cv2.boxPoints(((c[0], c[1]), (side, side), rot)).astype(np.int32)
    cv2.fillConvexPoly(m, box, 255)
    m = cv2.GaussianBlur(m, (3, 3), 0).astype(np.float32)[..., None] / 255
    rng = np.random.default_rng(int(c[0] * 7 + c[1]))
    white = np.clip(np.array(col, np.float32) + rng.normal(0, 4, img.shape), 0, 255)
    out = (out * (1 - m) + white * m).astype(np.uint8)
    return out


def main():
    import cv2

    # ---------------- N1 거짓 검출
    t0 = time.time()
    cnt, pos_frames = {}, []
    for vp, i, img in frames(13, N_NEG):
        d = sgs.detect(img, P)
        cnt[d["status"]] = cnt.get(d["status"], 0) + 1
        if d["status"] in ("detected", "uncertain"):
            print("    거짓 검출:", os.path.basename(vp), i, d["status"], d["reason"])
        c = d.get("cube")
        if d["status"] == "none" and c and c["area_px"] > 3000 and not c["touches_edge"] and len(pos_frames) < 24:
            pos_frames.append((os.path.basename(vp), i, img))
    fp = cnt.get("detected", 0) + cnt.get("uncertain", 0)
    assert fp == 0, cnt
    ok(f"N1 실제 d2 손목 {sum(cnt.values())} 프레임 (스티커 없음) 거짓 검출 0 — {cnt} ({time.time() - t0:.0f} s)")
    assert len(pos_frames) >= 12, len(pos_frames)

    # ---------------- P1 합성 스티커
    errs, misses, used = [], [], 0
    shots = []
    for name, i, img in pos_frames:
        area = sgs.detect(img, P)["cube"]["area_px"]
        side = max(8, int(0.28 * np.sqrt(area)))
        c = sticker_spot(img, side)
        if c is None:
            continue
        used += 1
        im2 = paste_sticker(img, c, side, rot=float((used * 17) % 45))
        d = sgs.detect(im2, P)
        if d["status"] != "detected":
            misses.append((name, i, d["status"], d["reason"]))
            continue
        errs.append(float(np.hypot(d["sticker"]["px"][0] - c[0], d["sticker"]["px"][1] - c[1])))
        if len(shots) < 4:
            shots.append((im2, d))
    assert used >= 10 and not misses and max(errs) <= 2.0, (used, misses, errs)
    ok(f"P1 [합성] 큐브 안 흰 사각형 {used}장 모두 검출 · 중심 오차 최대 {max(errs):.2f} px (중앙 {np.median(errs):.2f})")

    base_name, base_i, base = pos_frames[0]
    area = sgs.detect(base, P)["cube"]["area_px"]
    side = max(8, int(0.28 * np.sqrt(area)))
    c = sticker_spot(base, side)
    stk = paste_sticker(base, c, side)

    # ---------------- P2 반사 줄
    glare = base.copy()
    gx, gy = c
    cv2.line(glare, (gx - 9, gy - 2), (gx + 9, gy + 1), (255, 228, 232), 2)
    d = sgs.detect(glare, P)
    assert d["status"] != "detected", d["status"]
    ok(f"P2 [합성] 반사 줄 → {sgs.STATUS_KO[d['status']]} ({d['reason']})")

    # ---------------- P3 손가락 끝이 바깥에서 들어와 반을 덮음
    occ = stk.copy()
    h, w = occ.shape[:2]
    poly = np.array([[gx, gy - side], [gx + side // 2, gy - side], [gx + side // 2 + 20, h - 1], [gx - 10, h - 1]], np.int32)
    cv2.fillConvexPoly(occ, poly, (205, 205, 200))
    d = sgs.detect(occ, P)
    assert d["status"] in ("uncertain", "none"), (d["status"], d["reason"])
    ok(f"P3 [합성] 손가락 모양 회색-흰 띠가 반을 덮음 → {sgs.STATUS_KO[d['status']]} ({d['reason']})")

    # ---------------- P4 가장자리에 걸림: 스티커 중심이 영상 왼쪽 끝에 오게 이동
    M = np.float32([[1, 0, -(gx - 2)], [0, 1, 0]])
    edge = cv2.warpAffine(stk, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    d = sgs.detect(edge, P)
    assert d["status"] != "detected", (d["status"], d["reason"])
    ok(f"P4 [합성] 스티커가 영상 가장자리에 걸림 → {sgs.STATUS_KO[d['status']]} ({d['reason'] or '-'})")

    # ---------------- P5 큐브가 화면 밖
    M = np.float32([[1, 0, w], [0, 1, 0]])
    gone = cv2.warpAffine(stk, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    d = sgs.detect(gone, P)
    assert d["status"] == "no_cube" and d["sticker"] is None, d["status"]
    ok("P5 [합성] 큐브가 화면 밖 → 큐브 없음 · 스티커 없음")

    # ---------------- P6 둘
    big = None
    for name, i, img in pos_frames:
        a = sgs.detect(img, P)["cube"]["area_px"]
        if big is None or a > big[0]:
            big = (a, img)
    a, img = big
    s2 = max(8, int(0.2 * np.sqrt(a)))
    import cv2 as _c

    hsv = _c.cvtColor(img, _c.COLOR_RGB2HSV)
    red = sgs._hsv_mask(hsv, P["red_hsv"])
    ins = _c.erode(red, np.ones((s2 + 6, s2 + 6), np.uint8))
    ys, xs = np.nonzero(ins)
    i1 = int(np.argmin(xs))
    i2 = int(np.argmax(xs))
    assert xs[i2] - xs[i1] > 2 * s2, "두 자리 없음"
    two = paste_sticker(paste_sticker(img, (int(xs[i1]), int(ys[i1])), s2), (int(xs[i2]), int(ys[i2])), s2)
    d = sgs.detect(two, P)
    assert d["status"] == "uncertain" and "후보" in d["reason"], (d["status"], d["reason"])
    ok(f"P6 [합성] 같은 크기 스티커 둘 → 불확실 ({d['reason']})")

    # ---------------- P7 원본 불변
    h0 = hashlib.sha256(stk.tobytes()).hexdigest()
    d = sgs.detect(stk, P)
    from PIL import Image

    pil = Image.fromarray(stk)
    _ = sgv.draw_wrist(pil.resize((800, 600)), d, None, 800 / 640)
    _ = sgv.draw_wrist(pil, d, {"version": "ref-test", "kind": "box", "u": 0.5, "v": 0.5, "half_u": 0.05, "half_v": 0.05}, 1.0)
    assert hashlib.sha256(stk.tobytes()).hexdigest() == h0
    assert hashlib.sha256(np.array(pil).tobytes()).hexdigest() == h0
    ok("P7 detect · draw_wrist 전후 원본 프레임 배열 해시 같음 (표시는 복사본에만)")

    # ---------------- P8 크기 바꿔도 표시 위치
    for W in (320, 640, 1100, 1700):
        H = int(W * 0.75)
        s = W / 640
        im = sgv.draw_wrist(Image.fromarray(stk).resize((W, H)), d, None, s)
        x, y = d["sticker"]["u"] * W, d["sticker"]["v"] * H
        px = np.array(im)[int(round(y)), int(round(x))]
        assert tuple(int(v) for v in px) == sgv.OK, (W, px)
        assert abs(d["sticker"]["px"][0] * s - x) <= 1 and abs(d["sticker"]["px"][1] * s - y) <= 1
    ok("P8 표시 폭 320 · 640 · 1100 · 1700: 스티커 점 = (u·W, v·H) 자리, 색 = 검출 색")

    # ---------------- P9 멈춤 · 반복
    hlt = sgv.Health()
    now = 1000.0
    assert hlt.on_frames(1, stk, now)
    assert not hlt.stale(now + 0.2)
    assert hlt.stale(now + 0.6) and any("영상 멈춤" in p for p in hlt.problems("rec", now + 0.6))
    hlt2 = sgv.Health()
    for k in range(1, 9):
        hlt2.on_frames(k, stk, now + k * 0.066)
    assert hlt2.repeat >= sgv.REPEAT_N and hlt2.stale(now + 0.6) and any("반복" in p for p in hlt2.problems("rec", now + 0.6))
    im = sgv.draw_wrist(Image.fromarray(stk), d, None, 1.0, stale=True)
    x, y = d["sticker"]["px"]
    assert tuple(int(v) for v in np.array(im)[int(y), int(x)]) != sgv.OK
    ok("P9 새 프레임 0.6 s 없음 → '영상 멈춤' · 같은 프레임 반복 → stale · 표시에 스티커 점 없음")

    # ---------------- P10 이어 쓰지 않음 (Screen 이 프레임마다 새로 검출)
    import json
    import tempfile

    sys.path.insert(0, TOOLS)
    import r12_common as rc

    with tempfile.TemporaryDirectory() as live:
        fr = rc.LiveFrames(live, create=True)
        rc.write_json(os.path.join(live, "status.json"), {"t": time.time(), "phase": "rec"})
        rc.write_json(os.path.join(live, "ui.json"), {"state": "REC"})
        cfg = rc.load_config(os.path.join(os.path.dirname(HERE), "config", "sg50.yaml"))
        scr = sgv.Screen(live, cfg)
        scr.P = P
        fr.put(0, stk), fr.put(1, stk), fr.bump()
        scr.poll()
        assert scr.det["status"] == "detected"
        fr.put(1, gone), fr.bump()
        scr.poll()
        assert scr.det["status"] == "no_cube" and scr.det["sticker"] is None
        fr.put(1, base), fr.bump()
        scr.poll()
        assert scr.det["status"] == "none" and scr.det["sticker"] is None
        im = scr.render(1100, 680)
        del fr
    ok("P10 검출 → 큐브 사라짐 → 스티커 없음: 상태가 프레임마다 바뀜 (이전 위치 안 씀)")

    if OUT:
        os.makedirs(OUT, exist_ok=True)
        cases = [("P1_synth", stk), ("P2_glare", glare), ("P3_finger", occ), ("P4_edge", edge), ("P6_two", two), ("N_real", base)]
        tiles = []
        for nm, arr in cases:
            dd = sgs.detect(arr, P)
            t = sgv.draw_wrist(Image.fromarray(arr), dd, None, 1.0)
            from PIL import ImageDraw

            ImageDraw.Draw(t).text((8, 448), nm + (" [합성]" if nm[0] == "P" else " [실제 d2 프레임]"), font=sgv.font(18), fill=(255, 255, 0))
            tiles.append(t)
        sheet = Image.new("RGB", (640 * 3, 480 * 2))
        for k, t in enumerate(tiles):
            sheet.paste(t, ((k % 3) * 640, (k // 3) * 480))
        sheet.save(os.path.join(OUT, "sticker_cases.png"))
        json.dump({"base_frame": [base_name, base_i]}, open(os.path.join(OUT, "sticker_cases.json"), "w"))
    print(f"PASS {len(results)} 항목")
    return 0


if __name__ == "__main__":
    sys.exit(main())
