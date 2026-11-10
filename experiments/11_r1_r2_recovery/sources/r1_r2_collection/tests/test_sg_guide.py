#!/home/user/so101-env/bin/python
"""닫기 자리 안내 (ref kind target) 시험 — 예비2 dataset 프레임 읽기만, 로봇 · 카메라 없음.
  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_sg_guide.py"""
import hashlib
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sg_sticker as ss  # noqa: E402
import sg_viewer as sv  # noqa: E402
from PIL import Image  # noqa: E402

SD = os.path.expanduser("~/so101_runs/practice/sg50_pilot2")


def frame(ep, fi):
    for f, ts, img in ss.wrist_frames(SD, ep):
        if f == fi:
            return img


def main():
    res = []
    ref = next(r for r in ss.read_refs()["refs"].values() if r.get("kind") == "target")
    P = ss.load_params()
    img = frame(0, int(13.57 * 30) - 3)
    c = ss.target_compare(ss.detect(img, P), ref)
    assert c and c["all"], c
    res.append(f"예비2 ep0 닫기 직전 → 네 가지 모두 허용 안 (du {c['du']:+.3f} dv {c['dv']:+.3f} 크기 {c['size']:.2f} 회전 {c['dangle']:+.1f}°)")
    sh = np.roll(img, 40, axis=1)
    sh[:, :40] = img[:, :1]
    c2 = ss.target_compare(ss.detect(sh, P), ref)
    assert c2 and not c2["ok"]["u"] and c2["du"] > 0.04 and c2["ok"]["size"], c2
    res.append(f"영상을 오른쪽으로 40 px 밀면 → 좌우만 벗어남 (du {c2['du']:+.3f}), 안내 '큐브를 화면 왼쪽으로'")
    sm = np.array(Image.fromarray(img).resize((544, 408)).crop((-48, -36, 592, 444)))  # 85 % 축소 = 멀어짐
    c3 = ss.target_compare(ss.detect(sm, P), ref)
    assert c3 and c3["size"] < 0.95 and not c3["ok"]["size"], c3
    res.append(f"85 % 로 줄이면 → 높이 벗어남 (크기 {c3['size']:.2f}, '가까이')")
    rot = np.array(Image.fromarray(img).rotate(-8, center=(ref["u"] * 640, ref["v"] * 480), fillcolor=(200, 200, 200)))  # 화면 시계 방향 8°
    c4 = ss.target_compare(ss.detect(rot, P), ref)
    assert c4 and c4["dangle"] < -3, c4
    res.append(f"화면 시계 방향 8° 돌리면 → 회전 {c4['dangle']:+.1f}° (반시계로 돌리라는 안내)")
    assert ss.target_compare({"cube": None}, ref) is None
    h0 = hashlib.sha256(img.tobytes()).hexdigest()
    for W in (320, 640, 1100):
        s = W / 640
        im = sv.draw_wrist(Image.fromarray(img).resize((W, int(480 * s))), ss.detect(img, P), [{"version": "t", **ref}], s, text=False)
        assert im.size == (W, int(480 * s))
        px = np.array(im)[2, W - 5]
        assert px[1] > px[0], px  # 위 띠 초록
    stale = sv.draw_wrist(Image.fromarray(img), ss.detect(img, P), [{"version": "t", **ref}], 1.0, stale=True, text=False)
    assert tuple(np.array(stale)[2, 635]) != tuple(np.array(Image.fromarray(img))[2, 635])
    assert hashlib.sha256(img.tobytes()).hexdigest() == h0
    res.append("그리기 폭 320 · 640 · 1100: 맞으면 위 띠 초록 · 영상 멈춤이면 회색 띠 (안내 없음) · 원본 프레임 배열 그대로")
    import sg_fk

    f0 = sg_fk.tool_tilt([-4.3, -102.9, 95.3, 77.8, 92.9])
    f1 = sg_fk.tool_tilt({"shoulder_pan.pos": -4.3, "shoulder_lift.pos": -102.9, "elbow_flex.pos": 95.3, "wrist_flex.pos": 87.8, "wrist_roll.pos": 92.9})
    assert f0 and abs(f0[1]) < 3 and abs((f1[0] - f0[0]) + 10) < 1.5, (f0, f1)  # wrist_flex +10° → 앞뒤 −10° 쯤 (같은 평면)
    res.append(f"수평계 FK: S0 앞뒤 {f0[0]:+.1f}° · 옆 {f0[1]:+.1f}°, wrist_flex +10° 면 앞뒤 {f1[0] - f0[0]:+.1f}°")
    base = Image.fromarray(img)
    for fwd, want_green in ((0.5, True), (12.0, False), (-60.0, False)):
        im = np.array(sv.draw_wrist(base, None, [], 1.0, show_ref=False, tilt=(fwd, 3.0), text=False))
        pw = max(64, int(640 / 6))
        box = im[max(14, int(480 / 13)) + 6: max(14, int(480 / 13)) + 6 + pw, 640 - pw - 6: 640 - 6]
        g = ((box[..., 1] > 140) & (box[..., 0] < 60)).sum()
        o = ((box[..., 0] > 230) & (box[..., 1] > 90) & (box[..., 1] < 140)).sum()
        assert (g > 20) == want_green and (o > 20) == (not want_green), (fwd, g, o)
    assert np.array_equal(np.array(sv.draw_wrist(base, None, [], 1.0, show_ref=False, tilt=None, text=False)), img)
    res.append("수평계 그림: ±3° 안 초록 · 12° · −60° 주황 (막대가 칸 안) · 관절값 없으면 (카메라 미리보기) 안 그림")
    # 그리퍼 열기 알림 (합성 관절값): 안 열고 lift +25 → 켜짐, 연 뒤 → 꺼짐, 미리보기 (관절값 없음) → 없음
    import tempfile
    import time as _t

    import r12_common as rc

    live = tempfile.mkdtemp(prefix="sg_alert_", dir=os.environ.get("TMPDIR", "/tmp"))
    rc.LiveFrames(live, create=True)
    scr = sv.Screen(live)
    J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

    clock = [1000.0]

    def step(lift, grip, state="REC", ep=3, pan=-4.0, wflex=78.0, dt=0.1):
        clock[0] += dt
        rc.write_json(os.path.join(live, "status.json"), {"t": clock[0], "phase": "rec",
                                                          "state": dict(zip([j + ".pos" for j in J], [pan, lift, 95, wflex, 93, grip]))})
        rc.write_json(os.path.join(live, "ui.json"), {"state": state, "episode": ep})
        scr.poll(now=clock[0])
        return scr.open_alert
    # (a) 숄더팬 −4 → −60 으로 돌리고 멈춤 (그리퍼 안 엶) → 멈춘 지 0.5 s 뒤 켜짐 → 열면 꺼짐
    seq = [step(-103, 1, pan=-4)] + [step(-103, 1, pan=p_) for p_ in (-20, -40, -60)] + [step(-103, 1, pan=-60) for _ in range(6)]
    assert seq[:4] == [False] * 4 and seq[-1] is True, seq
    assert step(-103, 35, pan=-60) is False and step(-80, 12, pan=-60) is False, "연 뒤에는 안 켜짐"
    # (b) 정면 자리: 팬 그대로, 손목 숙임 (wrist_flex −10°) 로 찾기 시작 → 켜짐
    step(-103, 1, state="SETUP", ep=4)
    assert step(-103, 1, ep=4) is False and step(-103, 1, ep=4, wflex=74) is False and step(-103, 1, ep=4, wflex=68) is True
    # (c) 큰 팔 뻗기
    step(-103, 1, state="SETUP", ep=5)
    assert step(-103, 1, ep=5) is False and step(-78, 1, ep=5, wflex=78) is True
    rc.write_json(os.path.join(live, "status.json"), {"t": clock[0] + 1, "phase": "camera_preview", "state": None})
    rc.write_json(os.path.join(live, "ui.json"), {"state": "REC", "episode": 6})
    scr.poll(now=clock[0] + 1)
    assert scr.open_alert is False
    im_on = None
    import time as _tt
    while int(_tt.time() * 3) % 2:
        _tt.sleep(0.02)
    im_on = np.array(sv.draw_wrist(base, None, [], 1.0, show_ref=False, text=False, alert=True))
    assert im_on[100, 320, 0] > im_on[100, 320, 2] + 40, im_on[100, 320]  # 손목 칸 안쪽까지 주황 (글 위쪽)
    res.append("그리퍼 열기 알림: 숄더팬 돌리고 0.5 s 멈춤 · 손목 숙임 8° · 큰 팔 뻗기 때 (안 열었으면) 켜짐 → 열면 꺼짐 · 판마다 새로 · 관절값 없으면 안 켜짐 · 손목 칸 전체 주황")
    for r in res:
        print("  ✓", r)
    print(f"PASS {len(res)} 항목")
    return 0


if __name__ == "__main__":
    sys.exit(main())
