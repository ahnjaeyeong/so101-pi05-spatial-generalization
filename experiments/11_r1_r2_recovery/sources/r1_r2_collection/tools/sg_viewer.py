#!/home/user/so101-env/bin/python
"""SG50 수집 화면 — 녹화 프로세스가 /dev/shm 에 쓰는 영상 · 상태를 읽어 보여 주기만 한다 (로봇 · 카메라를 열지 않음).

r12_collect.py record/preview 가 설정 viewer: sg 일 때 r12_viewer.py 대신 연다. 공유 파일은 r12 와 같다:
  frames.u8 (front · wrist 원본 프레임, 녹화 루프가 2 틱마다 씀) · status.json (녹화 프로세스) · ui.json (터미널 화면).
화면 = 한 장의 그림 (PIL) 을 창 크기에 맞춰 매번 다시 그림 → 창 크기를 바꿔도 좌표 · 표시가 맞는다.
  - 원본 프레임 배열은 바꾸지 않는다. 표시용 복사본 (축소 그림) 위에만 박스 · 점 · 글씨를 그린다.
  - 스티커 검출 (sg_sticker.detect) 은 이 화면 프로세스에서만 돈다 → 녹화 루프 · dataset 에 영향 없음.
  - 영상이 멈추거나 (새 프레임 없음 0.5 s) 같은 프레임이 반복되면 빨간 띠로 알리고 검출 표시를 끈다.
  - 스티커가 안 보이면 '미검출' — 이전 위치를 이어 그리지 않는다.
창 키: F3 검출 표시 켜기/끄기 (끄면 검출 계산도 멈춤) · F2 정렬 참고 표시 켜기/끄기. 나머지 키는 녹화 키로 넘김 (r12 와 같은 keys.in).

  ~/so101-env/bin/python sg_viewer.py --live /dev/shm/r12_live_<run> [--scale 1.0]
  ~/so101-env/bin/python sg_viewer.py --live DIR --render OUT.png --size 1400x860   # 창 없이 한 장 (시험 · 화면 예시)
"""

import argparse
import collections
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402
import sg_sticker as sgs  # noqa: E402

TITLE = "SO-101 SG50 수집 화면"
FONT_FILE = "/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf"
BG, PANEL, FG, DIM = (17, 24, 39), (31, 41, 55), (243, 244, 246), (156, 163, 175)
OK, WARN, BAD, INFO = (34, 197, 94), (245, 158, 11), (239, 68, 68), (96, 165, 250)
C_HULL, C_STK, C_REF, C_PLAN = (34, 197, 94), (34, 211, 238), (232, 121, 249), (255, 255, 255)
C_CROSS = (250, 204, 21)  # 큐브 중심 십자 (노란 점선, 2026-11-06 사용자: 회색은 잘 안 보임 — 주황은 닫기 자리 목표)
C_OPEN_ALERT = (255, 140, 0)
OPEN_ALERT_GRIP, OPEN_ALERT_LIFT = 8.0, 20.0  # 그리퍼 '열림' = 시작 + 8 · 큰 팔 뻗기 = lift 시작 + 20 (sg_phase 와 같은 값)
OPEN_ALERT_PAN, OPEN_ALERT_STILL_S, OPEN_ALERT_FIND = 5.0, 0.5, 8.0  # 팬 정렬 끝 = 시작 ± 5° 넘게 움직인 뒤 0.5 s 멈춤 · 찾기 시작 = lift/wflex ± 8°
C_TGT_GUIDE, C_GUIDE_OK = (249, 115, 22), (22, 163, 74)  # 닫기 자리 목표 (주황) · 네 가지 다 맞음 (초록)
STATE = {"START": ("시작 준비", (107, 114, 128)), "SETUP": ("준비 — 녹화 안 함", (180, 83, 9)),
         "RESET": ("판 끝 · 다음 판 준비 — 녹화 안 함", (75, 85, 99)), "REC": ("● 녹화 중", (220, 38, 38)),
         "SAVING": ("저장 중 — 리더 팔 그대로", (29, 78, 216)), "FINAL": ("마무리 저장", (29, 78, 216)),
         "DONE": ("녹화 종료", (21, 128, 61)), "WAIT": ("다음 판 시작 대기", (75, 85, 99)),
         "CAMPREVIEW": ("카메라 미리보기", (55, 65, 81))}
C_TGT = (220, 38, 38)   # 놓을 위치 (빨간 큐브 색)
MAP_FRAC = 0.92 
        # 위에서 본 그림 폭 / 카메라 칸 폭
# 위에서 본 그림 범위 (탁자 C 좌표 cm): 세로 = x (위 로봇 → 아래 상자), 가로 = y (왼쪽 = 로봇 오른쪽 −y, 오른쪽 = 로봇 왼쪽 +y; front 화면과 같음)
MAP_X, MAP_Y = (-36.0, 14.0), (-16.0, 38.0)
STK_COL = {"detected": OK, "uncertain": WARN, "none": BAD, "no_cube": DIM}
STALE_S = 0.5          # 새 프레임이 이 시간 넘게 없으면 '영상 멈춤'
STATUS_STALE_S = 2.0   # status.json 이 이 시간 넘게 안 바뀌면 '상태 갱신 없음'
REPEAT_N = 6           # 새 순번인데 같은 손목 프레임이 연속 이만큼 → '프레임 반복'

_fonts = {}


def font(size):
    from PIL import ImageFont

    size = max(9, int(size))
    if size not in _fonts:
        try:
            _fonts[size] = ImageFont.truetype(FONT_FILE, size)
        except OSError:
            _fonts[size] = ImageFont.load_default()
    return _fonts[size]


def _tw(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def label(d, xy, text, f, fg=FG, bg=(0, 0, 0), pad=3):
    x, y = xy
    w, h = _tw(d, text, f)
    d.rectangle([x - pad, y - pad, x + w + pad, y + h + pad + 2], fill=bg)
    d.text((x, y), text, font=f, fill=fg)
    return w + 2 * pad, h + 2 * pad


def dashed_poly(d, pts, col, width=2, dash=8):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(np.hypot(x1 - x0, y1 - y0) / dash))
        for k in range(0, n, 2):
            a, b = k / n, min(1, (k + 1) / n)
            d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=col, width=width)


def draw_wrist(img, det, ref, s, show_det=True, show_ref=True, stale=False, text=True, tilt=None, alert=False):
    """손목 표시 복사본. img = 이미 s 배로 줄인 PIL 그림 (원본 프레임 배열과 별개). det 좌표는 원본 px → × s."""
    from PIL import ImageDraw

    im = img.copy()
    d = ImageDraw.Draw(im)
    W, H = im.size
    f = font(max(11, W / 36))
    refs = ref if isinstance(ref, list) else ([ref] if ref else [])
    for ri, ref in enumerate(refs if show_ref else []):
        cx, cy = ref["u"] * W, ref["v"] * H
        if ref.get("kind") == "target":  # 닫기 자리 목표 윤곽 (주황 굵은 점선) — 안내는 아래 _draw_target_guide
            dashed_poly(d, [(x * W, y * H) for x, y in ref["hull"]], C_TGT_GUIDE, max(2, int(W / 210)), dash=10)
            continue
        if ref.get("kind") == "cross":  # 큐브 중심 십자: 화면 끝에서 끝까지 가로 · 세로 주황 점선 (판정 아님)
            wl = max(2, int(W / 300))  # 노란 점선 (흰 탁자 위에서 보이게 조금 굵게)
            dashed_poly(d, [(0, cy), (W, cy)], C_CROSS, wl, dash=10)
            dashed_poly(d, [(cx, 0), (cx, H)], C_CROSS, wl, dash=10)
            d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], outline=C_CROSS, width=2)
            if text:
                fr_ = font(max(10, W / 48))
                label(d, (min(cx + 8, W - _tw(d, "큐브 십자 (판정 아님)", fr_)[0] - 8), 6), "큐브 십자 (판정 아님)", fr_, C_CROSS)
            continue
        if ref.get("kind") == "box":
            hw, hh = ref["half_u"] * W, ref["half_v"] * H
            dashed_poly(d, [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)], C_REF, 2)
        else:
            r = ref.get("r", 0.04) * W
            pts = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40, endpoint=False)]
            dashed_poly(d, pts, C_REF, 2, dash=5)
        d.line([(cx - 6, cy), (cx + 6, cy)], fill=C_REF, width=2)
        d.line([(cx, cy - 6), (cx, cy + 6)], fill=C_REF, width=2)
        fr_ = font(max(10, W / 48))
        rr = (ref["half_v"] * H if ref.get("kind") == "box" else ref.get("r", 0.04) * W) + 6
        if text:
            txt_ = f"참고 {ref.get('name') or ref['version']} (판정 아님)"
            tw_ = _tw(d, txt_, fr_)[0]
            step = _tw(d, txt_, fr_)[1] + 8  # 참조가 여럿이면 글을 겹치지 않게 아래/위로 한 줄씩
            label(d, (max(4, min(cx - tw_ / 2, W - tw_ - 8)), cy + rr + ri * step if cy < H * 0.75 else cy - rr - 24 - ri * step), txt_, fr_, C_REF)
    tref = next((r for r in refs if r.get("kind") == "target"), None) if show_ref else None
    if tilt is not None:
        _draw_level(d, W, H, tilt)
    if alert and int(time.time() * 3) % 2 == 0:  # 그리퍼 열기 알림 (2026-11-06 사용자): 손목 칸 전체 주황 + '그리퍼를 열어주세요' 깜빡임
        from PIL import Image as _I

        ov = _I.new("RGB", im.size, C_OPEN_ALERT)
        im.paste(_I.blend(im, ov, 0.45))
        d = ImageDraw.Draw(im)
        bw = max(6, int(W / 60))
        d.rectangle([bw // 2, bw // 2, W - 1 - bw // 2, H - 1 - bw // 2], outline=C_OPEN_ALERT, width=bw)
        msg = "그리퍼를 열어주세요"
        fb = font(max(18, W / 11))
        tw, th = _tw(d, msg, fb)
        while tw > W * 0.92 and fb.size > 14:
            fb = font(fb.size - 2)
            tw, th = _tw(d, msg, fb)
        tx, ty = (W - tw) / 2, (H - th) / 2
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            d.text((tx + ox, ty + oy), msg, font=fb, fill=(40, 20, 0))
        d.text((tx, ty), msg, font=fb, fill=(255, 255, 255))
    if stale:
        label(d, (8, H - 30), "오래된 프레임 — 검출 표시 안 함", f, (255, 255, 255), (127, 29, 29))
        if tref:
            _target_band(d, W, H, "영상 멈춤 — 안내 없음", DIM, text)
        return im
    if not show_det:
        if text:
            label(d, (8, H - 30), "검출 표시 꺼짐 (F3)", f, DIM)
        return im
    if det is None:
        return im
    if det.get("cube"):
        pts = [(x * s, y * s) for x, y in det["cube"]["hull"]]
        if len(pts) >= 2:
            d.line(pts + pts[:1], fill=C_HULL, width=2)
        if show_ref and any(r.get("kind") == "cross" for r in refs):  # 십자와 맞춰 볼 지금 큐브 중심
            x, y = det["cube"]["px"][0] * s, det["cube"]["px"][1] * s
            d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 0, 0), fill=C_HULL, width=1)
    stv = det["status"]
    col = STK_COL[stv]
    if det.get("sticker"):
        st = det["sticker"]
        pts = [(x * s, y * s) for x, y in st["contour"]]
        if len(pts) >= 2:
            d.line(pts + pts[:1], fill=col, width=3)
        x, y = st["px"][0] * s, st["px"][1] * s
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 0, 0), fill=col, width=1)
        d.line([(x - 14, y), (x + 14, y)], fill=col, width=2)
        d.line([(x, y - 14), (x, y + 14)], fill=col, width=2)
        if text:
            txt = f"({st['u']:.3f}, {st['v']:.3f})"
            label(d, (min(x + 12, W - _tw(d, txt, f)[0] - 8), max(4, y - 30)), txt, f, col)
    if tref:
        _draw_target_guide(d, W, H, s, det, tref, text)
    elif text:
        head = {"detected": "스티커 검출", "uncertain": "스티커 불확실", "none": "스티커 미검출", "no_cube": "큐브 없음"}[stv]
        label(d, (8, 8), head + (f" — {det['reason']}" if det.get("reason") and stv != "detected" else ""), f, col)
    return im


def _target_band(d, W, H, msg, col, text=True):
    """위 색 띠. text=False (기본 화면) 면 글 없이 색만 (2026-11-06 사용자: 글자 지움)."""
    bh = max(18, int(H / 13)) if text else max(8, int(H / 40))
    d.rectangle([0, 0, W, bh], fill=col)
    if not text:
        return bh
    d.text((8, (bh - font(max(11, bh * 0.62)).size) / 2), msg, font=font(max(11, bh * 0.62)), fill=(255, 255, 255))
    return bh


def _draw_level(d, W, H, tilt):
    """그리퍼 수평계 (옆에서 본 그림, 글 없음): 왼쪽 회색 = 로봇 쪽, 노란 점선 = 목표 각도 (sg50.tilt_target_deg, 0 = 지면과 수직),
    막대 = 지금 그리퍼 (실제 각도, ±70° 에서 멈춤). tilt = (앞뒤 °, 허용 °[, 목표 °]) — + = 손끝이 로봇에서 먼 쪽. |앞뒤 − 목표| ≤ 허용 이면 초록. 판정 아님."""
    fwd, tol = tilt[0], tilt[1]
    tgt = tilt[2] if len(tilt) > 2 else 0.0
    ok = abs(fwd - tgt) <= tol
    pw = max(64, int(W / 6))
    x0, y0 = W - pw - 6, max(14, int(H / 13)) + 6
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + pw], radius=8, fill=(17, 24, 39), outline=(75, 85, 99), width=1)
    cx, top, bot = x0 + pw * 0.36, y0 + pw * 0.12, y0 + pw * 0.88
    d.pieslice([x0 + 3, bot - pw * 0.13, x0 + pw * 0.22, bot + pw * 0.13], 180, 360, fill=(107, 114, 128))  # 로봇 (왼쪽)
    L = (bot - top) * 0.92

    def tip(deg):
        a = math.radians(max(-70.0, min(70.0, deg)))
        return a, cx + L * math.sin(a), top + L * math.cos(a)  # 위 (손목) 고정, 아래 (손끝) 가 기울어짐: + = 오른쪽 (로봇에서 멀리)
    _, gx, gy = tip(tgt)
    dashed_poly(d, [(cx, top), (gx, gy)], C_CROSS, 2, dash=4)
    a, tx, ty = tip(fwd)
    col = C_GUIDE_OK if ok else C_TGT_GUIDE
    d.line([(cx, top), (tx, ty)], fill=col, width=max(3, int(pw / 12)))
    for sgn in (-1, 1):  # 손가락 두 개
        d.line([(tx, ty), (tx + sgn * pw * 0.08 * math.cos(a), ty - sgn * pw * 0.08 * math.sin(a))], fill=col, width=3)
    d.ellipse([cx - 3, top - 3, cx + 3, top + 3], fill=(229, 231, 235))


def tilt_zero(s50, pan):
    """수평계 0 점 (°): sg50.tilt_zero {c0, c1} 가 있으면 c0 + c1·sin(pan), 없으면 tilt_zero_deg (2026-11-06 사용자 수직 3 자세로 맞춤)."""
    z = s50.get("tilt_zero")
    if z and pan is not None:
        return float(z.get("c0", 0.0)) + float(z.get("c1", 0.0)) * math.sin(math.radians(float(pan)))
    return float(s50.get("tilt_zero_deg", 0.0))


def _arrow(d, p0, p1, col, width):
    d.line([p0, p1], fill=col, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L = 6 + 2.5 * width
    for da in (2.6, -2.6):
        d.line([p1, (p1[0] + L * math.cos(ang + da), p1[1] + L * math.sin(ang + da))], fill=col, width=width)


def _draw_target_guide(d, W, H, s, det, ref, text=True):
    """닫기 자리 목표 안내 (화면 복사본에만): 위 띠 (주황 = 아직 · 초록 = 네 가지 다 허용 안) + 항목 칩 + 화면 화살표.
    판정 · 자동 동작 아님 — 닫는 때는 사람이 정함."""
    import sg_sticker as sgs

    c = sgs.target_compare(det, ref) if det else None
    if c is None:
        _target_band(d, W, H, "닫기 자리 안내 — 큐브 안 보임", DIM, text)
        return
    bh = _target_band(d, W, H, "닫기 자리 맞음 (참고)" if c["all"] else "닫기 자리까지 (참고)", C_GUIDE_OK if c["all"] else C_TGT_GUIDE, text)
    cu, cv = det["cube"]["u"] * W, det["cube"]["v"] * H
    tu, tv = ref["u"] * W, ref["v"] * H
    wln = max(2, int(W / 180))
    d.ellipse([cu - 5, cv - 5, cu + 5, cv + 5], fill=C_GUIDE_OK if c["all"] else (255, 255, 255), outline=(0, 0, 0))
    d.ellipse([tu - 6, tv - 6, tu + 6, tv + 6], outline=C_TGT_GUIDE, width=2)
    if not (c["ok"]["u"] and c["ok"]["v"]) and math.hypot(tu - cu, tv - cv) > 8:
        _arrow(d, (cu, cv), (tu, tv), C_TGT_GUIDE, wln)
    if not c["ok"]["angle"]:  # 돌려야 할 쪽으로 호 (작은 각도도 보이게 3배, 최소 25°)
        R = 0.32 * math.sqrt(det["cube"]["area_px"]) * s
        span = math.copysign(max(25.0, 3 * abs(c["dangle"])), c["dangle"])
        a0 = -90.0
        pts = [(cu + R * math.cos(math.radians(a0 + span * k / 12)), cv + R * math.sin(math.radians(a0 + span * k / 12))) for k in range(13)]
        d.line(pts, fill=C_TGT_GUIDE, width=wln)
        _arrow(d, pts[-2], pts[-1], C_TGT_GUIDE, wln)
    if not text:  # 기본 화면: 윤곽 · 화살표 · 색 띠만
        return
    fs = font(max(11, W / 34))
    px_u, px_v = abs(c["du"]) * 640, abs(c["dv"]) * 480
    items = [("좌우", c["ok"]["u"], ("큐브를 화면 왼쪽으로 " if c["du"] > 0 else "큐브를 화면 오른쪽으로 ") + f"{px_u:.0f}px"),
             ("앞뒤", c["ok"]["v"], ("큐브를 화면 위로 " if c["dv"] > 0 else "큐브를 화면 아래로 ") + f"{px_v:.0f}px"),
             ("높이", c["ok"]["size"], ("가까이 " if c["size"] < 1 else "멀리 ") + f"(크기 {c['size'] * 100:.0f}%)"),
             ("회전", c["ok"]["angle"], ("화면 시계 방향 " if c["dangle"] > 0 else "화면 반시계 방향 ") + f"{abs(c['dangle']):.0f}°")]
    y = bh + 4
    for name, ok, txt in items:
        t = f"{name} 맞음" if ok else f"{name}: {txt}"
        label(d, (6, y), t, fs, C_GUIDE_OK if ok else (255, 255, 255), (17, 24, 39))
        y += _tw(d, t, fs)[1] + 9
    if c["edge"]:
        label(d, (6, y), "큐브가 화면 끝에 걸림 — 크기 · 회전 값 불확실", fs, WARN, (17, 24, 39))


class Health:
    """영상 · 상태 신선도 (화면 프로세스 기준 시각)."""

    def __init__(self):
        self.seq = -1
        self.seq_t = None
        self.sig = None
        self.repeat = 0
        self.status_t = None
        self.status_seen = None

    def on_frames(self, seq, wrist, now):
        new = seq != self.seq and seq > 0
        if new:
            self.seq, self.seq_t = seq, now
            sig = wrist[::53, ::47].tobytes()
            self.repeat = self.repeat + 1 if sig == self.sig else 0
            self.sig = sig
        return new

    def on_status(self, st, now):
        t = st.get("t")
        if t is not None and t != self.status_seen:
            self.status_seen, self.status_t = t, now

    def problems(self, phase, now):
        out = []
        active = phase in ("setup", "rec", "after_rec", "connect", "camera_preview")
        if self.seq_t is None:
            out.append("영상 없음 (녹화 프로세스가 아직 카메라를 열지 않음)" if active or phase is None else "영상 없음")
        elif now - self.seq_t > STALE_S and active:
            out.append(f"영상 멈춤 — 새 프레임 {now - self.seq_t:.1f} s 없음")
        if self.repeat >= REPEAT_N:
            out.append(f"손목 프레임 반복 {self.repeat}회 (카메라 멈춤 의심)")
        if self.status_t is not None and now - self.status_t > STATUS_STALE_S and active:
            out.append(f"녹화 상태 갱신 없음 {now - self.status_t:.1f} s")
        return out

    def stale(self, now):
        return self.seq_t is None or now - self.seq_t > STALE_S or self.repeat >= REPEAT_N


def pose_lines(cfg, row, state):
    """시작 자세 목표 ↔ 지금 (팔로워). [(글, 색)]."""
    if not row or not cfg.get("sg50"):
        return []
    import sg_plan

    sc = cfg["scenarios"].get(row.get("scenario_id", ""), {})
    q = sc.get("pose", "")
    p = cfg["sg50"]["start_poses"].get(q)
    if not p:
        return []
    dev = sg_plan.pose_dev(cfg, q, state)
    out = [(f"시작 자세 {q} {p['name']}" + ("" if p.get("status") in ("confirmed_in_d2", "user_fixed") else " (후보)")
            + (f" — {p['pending']}" if p.get("pending") else ""), FG)]
    parts = []
    for j, t in p["joints"].items():
        if j in dev:
            now, _, dv, ok = dev[j]
            parts.append((f"{rc.SHORT[j]} {now:+.0f}/{t:+.0f}", OK if ok else WARN))
        else:
            parts.append((f"{rc.SHORT[j]} ?/{t:+.0f}", DIM))
    out.append(parts)
    return out


class Screen:
    """live 폴더 → 화면 그림 (PIL). Tk 없이도 쓴다 (--render · 시험)."""

    def __init__(self, live, cfg=None):
        self.live = live
        self.cfg = cfg or rc.load_config(os.environ.get("R12_CONFIG"))
        self.H = rc.front_H(self.cfg)
        self.P = sgs.load_params()
        self.frames = None
        self.front = self.wrist = None
        self.health = Health()
        self.det = None
        self.det_seq = -1
        self.show_det, self.show_ref, self.show_map = True, True, True
        self.debug = False  # F5: 좌표 · 검출 수치 디버그 화면
        self.tilt = None  # (앞뒤 °, 옆 °, 전체 °) — 팔로워 관절값 FK (녹화 · 준비 때만, 카메라 미리보기는 없음)
        self.ref = sgs.active_ref()
        self.ref_t = 0
        self.vis, self.vis_t = {}, 0
        self.rec_t0, self._last_state = None, None
        self.st, self.ui = {}, {}
        self.perf = {"render": collections.deque(maxlen=300), "detect": collections.deque(maxlen=300), "new_frames": 0,
                     "detect_runs": 0, "t0": time.time()}

    def _open_alert(self, stt, stv, now=None):
        """그리퍼 열기 알림 (2026-11-06 사용자 순서: 숄더팬 → 그리퍼 열기 → 찾기 → 이동). 녹화 중 그리퍼를 한 번도 안 열었는데
        (a) 숄더팬이 녹화 시작보다 OPEN_ALERT_PAN° 넘게 움직였다가 OPEN_ALERT_STILL_S 동안 멈춤 (팬 정렬 끝), 또는
        (b) lift · wrist_flex 가 시작보다 OPEN_ALERT_FIND° 넘게 바뀜 (찾기 · 이동 시작 — 팬을 거의 안 돌리는 정면 자리), 또는
        (c) lift 가 시작보다 OPEN_ALERT_LIFT° 넘음 (큰 팔 뻗기) 이면 켜짐. 그리퍼를 열면 그 판에서는 꺼짐.
        판정 · 자동 동작 아님 — 손목 칸에 '그리퍼를 열어주세요' 깜빡임. 판마다 (ep · 녹화 시작 시각) 새로. 관절값 없으면 (미리보기) 안 함."""
        now = time.time() if now is None else now
        if stt != "REC" or not stv or self.tilt is None:
            self._oa_key = None
            return False
        try:
            grip, lift = float(stv["gripper.pos"]), float(stv["shoulder_lift.pos"])
            pan, wflex = float(stv["shoulder_pan.pos"]), float(stv["wrist_flex.pos"])
        except (KeyError, TypeError, ValueError):
            return False
        key = (self.ui.get("episode"), self.rec_t0)
        if key != getattr(self, "_oa_key", None):
            self._oa_key, self._oa_opened = key, False
            self._oa0 = {"lift": lift, "grip": grip, "pan": pan, "wflex": wflex}
            self._oa_pan = collections.deque()
        if grip > self._oa0["grip"] + OPEN_ALERT_GRIP:
            self._oa_opened = True
        if self._oa_opened:
            return False
        self._oa_pan.append((now, pan))
        while self._oa_pan and now - self._oa_pan[0][0] > OPEN_ALERT_STILL_S:
            self._oa_pan.popleft()
        span = now - self._oa_pan[0][0] if self._oa_pan else 0.0
        pans = [v for _, v in self._oa_pan]
        pan_done = abs(pan - self._oa0["pan"]) > OPEN_ALERT_PAN and span >= OPEN_ALERT_STILL_S * 0.8 and (max(pans) - min(pans)) < 1.5
        find = max(abs(lift - self._oa0["lift"]), abs(wflex - self._oa0["wflex"])) > OPEN_ALERT_FIND
        return bool(pan_done or find or lift - self._oa0["lift"] > OPEN_ALERT_LIFT)

    def level(self):
        """수평계 값 (앞뒤 − 0 점, 허용) 또는 None. 설정 sg50.tilt_zero_deg · tilt_tol_deg."""
        if not self.tilt or not self.show_ref:
            return None
        s50 = self.cfg.get("sg50") or {}
        return (self.tilt[0] - tilt_zero(s50, (self.st.get("state") or {}).get("shoulder_pan.pos")), float(s50.get("tilt_tol_deg", 3.0)),
                float(s50.get("tilt_target_deg", 0.0)))

    def poll(self, now=None):
        now = time.time() if now is None else now
        self.st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
        self.ui = rc.read_json(os.path.join(self.live, "ui.json"), {}) or {}
        self.health.on_status(self.st, now)
        self.tilt = None
        stv = self.st.get("state")
        if stv and self.health.status_t is not None and now - self.health.status_t <= 2.0:  # 팔로워 관절값이 새로울 때만
            try:
                import sg_fk

                self.tilt = sg_fk.tool_tilt(stv)
            except Exception:  # URDF 없음 등 — 수평계만 안 보임
                self.tilt = None
        stt = self.ui.get("state")
        if stt == "REC" and getattr(self, "_last_state", None) != "REC":
            self.rec_t0 = now
        elif stt != "REC":
            self.rec_t0 = None
        self.open_alert = self._open_alert(stt, stv, now)
        self._last_state = stt
        if self.frames is None and os.path.exists(os.path.join(self.live, "frames.u8")):
            try:
                self.frames = rc.LiveFrames(self.live, create=False)
            except (OSError, ValueError):
                self.frames = None
        if self.frames is not None:
            seq, f, w = self.frames.get()  # np.array 복사본 — 공유 메모리 원본은 그대로
            if self.health.on_frames(seq, w, now):
                self.front, self.wrist = f, w
                self.perf["new_frames"] += 1
        if now - self.ref_t > 2.0:  # 참조 · 검출 설정 파일 바뀌면 반영 (sg_sticker.py set-ref / use-ref, config/sg_sticker.json)
            self.refs = sgs.active_refs()
            self.ref, self.ref_t = (self.refs[0] if self.refs else None), now
            try:
                m = os.path.getmtime(sgs.PARAMS_PATH)
            except OSError:
                m = None
            if m != getattr(self, "params_mtime", "unset"):
                if getattr(self, "params_mtime", "unset") != "unset":
                    self.P = sgs.load_params()
                    self.det_seq = -1
                self.params_mtime = m
        if self.wrist is not None and self.show_det and self.health.seq != self.det_seq and not self.health.stale(now):
            t0 = time.perf_counter()
            try:
                self.det = sgs.detect(self.wrist, self.P)
            except Exception as e:  # 검출 오류로 화면이 멈추면 안 됨
                self.det = {"status": "none", "reason": f"검출 오류 {e!r}", "cube": None, "sticker": None, "candidates": [],
                            "img_size": [640, 480], "version": self.P["_version"]}
            self.perf["detect"].append((time.perf_counter() - t0) * 1000)
            self.perf["detect_runs"] += 1
            self.det_seq = self.health.seq
        if self.front is not None and now - self.vis_t > 0.3 and not self.health.stale(now):
            row = self.ui.get("row") or {}
            try:
                self.vis = rc.vision(self.front, None, self.cfg, row.get("position"))
            except Exception as e:
                self.vis = {"error": repr(e)}
            self.vis_t = now

    def render(self, W, H, now=None):
        if not self.debug:
            return self.render_clean(W, H, now)
        return self.render_debug(W, H, now)

    def cam_tiles(self, pw, ph, row, stale, text):
        """front · wrist 표시용 복사본 (원본 배열은 그대로)."""
        from PIL import Image

        out = []
        for cam, img in (("Front", self.front), ("Wrist", self.wrist)):
            if img is None:
                out.append((cam, None))
                continue
            s = pw / img.shape[1]
            small = Image.fromarray(img).resize((pw, ph), Image.BILINEAR)
            if cam == "Front":
                small = self.draw_front(small, s, row, stale)
            else:
                small = draw_wrist(small, self.det, getattr(self, "refs", None) or self.ref, s, self.show_det, self.show_ref, stale, text=text,
                                   tilt=None if stale else self.level(), alert=bool(getattr(self, "open_alert", False)) and not stale)
            out.append((cam, small))
        return out

    def render_clean(self, W, H, now=None):
        """기본 화면 = 그림 세 장만 (위에서 본 탁자 | Front | Wrist). 좌표 · 검출 수치는 디버그 화면 (F5)."""
        from PIL import Image, ImageDraw

        now = time.time() if now is None else now
        t0 = time.perf_counter()
        W, H = max(int(W), 480), max(int(H), 360)
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        u = max(0.6, min(W / 1800, H / 470))  # 기본 화면 = 넓고 낮은 창 기준
        pad = int(8 * u)
        y = pad
        probs = self.health.problems(self.st.get("phase"), now)  # 영상 멈춤 · 반복은 기본 화면에도 (안전 표시)
        if probs:
            d.rectangle([0, 0, W, int(30 * u)], fill=(127, 29, 29))
            d.text((pad, int(5 * u)), " · ".join(probs), font=font(17 * u), fill=(255, 255, 255))
            y = int(30 * u) + pad
        n = 3 if self.show_map else 2  # 위 그림 · Front · Wrist 를 같은 크기 (4:3) 로 한 줄
        avail = H - y - pad
        pw = int((W - (n + 1) * pad) / n)
        if pw * 0.75 > avail:
            pw = int(avail / 0.75)
        ph = int(pw * 0.75)
        stale = self.health.stale(now)
        row = self.ui.get("row") or {}
        x0 = (W - (n * pw + (n - 1) * pad)) // 2
        top = y + max(0, (avail - ph) // 2)
        if self.show_map:
            im.paste(self.draw_map(pw, ph, max(0.55, pw / 470), text=False), (x0, top))
            x0 += pw + pad
        spots = [(x0, top), (x0 + pw + pad, top)]
        for (x, top), (cam, tile) in zip(spots, self.cam_tiles(pw, ph, row, stale, text=False)):
            if tile is None:
                d.rectangle([x, top, x + pw, top + ph], fill=(0, 0, 0))
                d.text((x + pad, top + pad), f"{cam} 영상 없음", font=font(16 * u), fill=DIM)
            else:
                im.paste(tile, (x, top))
        if self.ui.get("state") == "REC":  # 녹화 중 = 화면 테두리 빨강
            d.rectangle([0, 0, W - 1, H - 1], outline=(220, 38, 38), width=max(3, int(5 * u)))
        self.perf["render"].append((time.perf_counter() - t0) * 1000)
        return im

    def render_debug(self, W, H, now=None):
        from PIL import Image, ImageDraw

        now = time.time() if now is None else now
        t0 = time.perf_counter()
        W, H = max(int(W), 480), max(int(H), 360)
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        ui, st = self.ui, self.st
        u = max(0.6, min(W / 1400, H / 860))  # 글씨 크기 기준
        fb, fm, fs = font(26 * u), font(17 * u), font(14 * u)
        pad = int(8 * u)
        # ---- 머리 띠: 상태 · run · episode · 진행
        state = ui.get("state") or "START"
        name, col = STATE.get(state, (state, (75, 85, 99)))
        hh = int(46 * u)
        d.rectangle([0, 0, W, hh], fill=col)
        ep = ui.get("episode")
        run = st.get("run_id") or "?"
        sess = ui.get("session") or ""
        txt = name + (f"   ep {ep}" if ep is not None else "")
        d.text((pad, int(8 * u)), txt, font=fb, fill=(255, 255, 255))
        right = f"run {run} · {sess} · 완료 {ui.get('done', '?')}/{ui.get('target', '?')}" + (" · PREVIEW" if ui.get("preview") else "")
        room = W - _tw(d, txt, fb)[0] - 4 * pad  # 왼쪽 제목과 겹치지 않게: 글씨를 줄이고 그래도 길면 앞을 자름
        fr_ = fm
        for k_ in (17, 15, 13, 11):
            fr_ = font(k_ * u)
            if _tw(d, right, fr_)[0] <= room:
                break
        while _tw(d, right, fr_)[0] > room and len(right) > 8:
            right = "…" + right[len(right) // 8 + 1:]
        d.text((W - _tw(d, right, fr_)[0] - pad, int(14 * u)), right, font=fr_, fill=(255, 255, 255))
        # ---- 조건 줄
        row = ui.get("row") or {}
        y = hh + pad
        s50 = self.cfg.get("sg50") or {}
        import sg_plan

        pos = row.get("position", "-")
        posd = (s50.get("positions") or {}).get(pos, {})
        conf = "" if posd.get("confirmed", True) else " (미확정 좌표)"
        cond = (f"큐브 {pos}{conf} ({row.get('cube_xy_cm', '-')} cm) · 회전 {row.get('angle', '-')} (로봇 좌우축 기준) · "
                f"{row.get('label', row.get('scenario_id', '-'))} · 스티커 {sg_plan.sticker_text(self.cfg) if s50 else '-'}")
        d.text((pad, y), cond, font=fm, fill=FG)
        y += int(26 * u)
        probs = self.health.problems(st.get("phase"), now)
        if probs:
            d.rectangle([0, y, W, y + int(28 * u)], fill=(127, 29, 29))
            d.text((pad, y + int(4 * u)), " · ".join(probs), font=fm, fill=(255, 255, 255))
            y += int(30 * u)
        # ---- 영상 두 칸 (4:3)
        bottom_h = int(150 * u)
        avail_h = H - y - bottom_h - pad
        mf = MAP_FRAC if self.show_map else 0.0  # 위에서 본 놓을 위치 그림 폭 / 카메라 폭
        pw = int((W - (4 if mf else 3) * pad) / (2 + mf))
        ph = int(pw * 0.75)
        if ph > avail_h - int(22 * u):
            ph = max(120, avail_h - int(22 * u))
            pw = int(ph / 0.75)
        mw = int(pw * mf)
        x0 = (W - (2 * pw + pad + (mw + pad if mw else 0))) // 2
        stale = self.health.stale(now)
        if mw:  # 왼쪽 칸 전체 높이 (아래 글은 카메라 아래로)
            d.text((x0, y), "위에서 본 탁자 (로봇 아래 · 상자 위)", font=fs, fill=DIM)
            im.paste(self.draw_map(mw, H - y - int(20 * u) - int(26 * u), u), (x0, y + int(20 * u)))
            x0 += mw + pad
        for k, (cam, img) in enumerate((("Front", self.front), ("Wrist", self.wrist))):
            x = x0 + k * (pw + pad)
            d.text((x, y), f"{cam} 카메라" + ("" if img is not None else " — 영상 없음"), font=fs, fill=DIM)
            yy = y + int(20 * u)
            if img is None:
                d.rectangle([x, yy, x + pw, yy + ph], fill=(0, 0, 0))
                continue
            s = pw / img.shape[1]
            small = Image.fromarray(img).resize((pw, ph), Image.BILINEAR)  # 표시용 복사본
            if cam == "Front":
                small = self.draw_front(small, s, row, stale)
            else:
                small = draw_wrist(small, self.det, getattr(self, "refs", None) or self.ref, s, self.show_det, self.show_ref, stale,
                                   tilt=None if stale else self.level(), alert=bool(getattr(self, "open_alert", False)) and not stale)
            im.paste(small, (x, yy))
        y = y + int(20 * u) + ph + pad
        # ---- 아래: 스티커 수치 · 시작 자세 · 상태 (카메라 칸 아래)
        self.draw_bottom(d, x0, y, W, H, u, row, stale)
        ms = (time.perf_counter() - t0) * 1000
        self.perf["render"].append(ms)
        return im

    def draw_map(self, mw, mh, u, text=True):
        """위에서 본 탁자 그림 (로봇이 위에서 아래(남쪽)를 봄 = front 카메라와 같은 방향). 단계마다 바뀜:
        준비 = 놓을 위치 · 녹화 중 = 빨강 · 저장 중 = 파랑 · 결과 입력 = 다음 위치 · 끝 = 초록."""
        from PIL import Image, ImageDraw

        im = Image.new("RGB", (mw, mh), (24, 32, 46))
        d = ImageDraw.Draw(im)
        ui = self.ui
        state = ui.get("state") or "START"
        row = ui.get("row") or {}
        ep = ui.get("episode")
        hb = int((56 if text else 44) * u)  # 위 띠 (기본 화면은 낮게)
        fb, fs_, fxs = font((22 if text else 19) * u), font((14 if text else 12.5) * u), font(11.5 * u)
        if state == "REC":
            col, t1, t2 = (220, 38, 38), f"● 녹화 중 · ep {ep}", "→ = 녹화 끝 · ← = 버리기"
        elif state in ("SAVING", "FINAL"):
            col, t1, t2 = (29, 78, 216), "저장 중…", "리더 팔을 그대로 두세요"
        elif state == "RESET":
            col, t1, t2 = ((75, 85, 99), "결과 입력 1 · 2 · 3", f"→ = 저장 → 다음 ep {ep} 위치 (아래)") if self.cfg.get("result_entry", True) else \
                ((75, 85, 99), "판 끝 — 녹화 안 함", f"→ = 저장 · ← = 버리기 · 다음 ep {ep} 위치 (아래)")
        elif state == "DONE":
            col, t1, t2 = (21, 128, 61), "녹화 종료", ""
        elif state == "CAMPREVIEW":
            col, t1, t2 = (180, 83, 9), f"놓을 위치 · ep {ep if ep is not None else '-'}", "카메라 미리보기 — ← → 계획 판 넘기기 (녹화 아님)"
        else:
            col, t1, t2 = (180, 83, 9), f"놓을 위치 · ep {ep if ep is not None else '-'}", "큐브를 놓고 시작 자세 → (녹화 시작)"
        d.rectangle([0, 0, mw, hb], fill=col)
        d.text((8, int(4 * u)), t1, font=fb, fill=(255, 255, 255))
        d.text((8, int((32 if text else 26) * u)), t2, font=fs_, fill=(255, 255, 255))
        # 탁자 → 그림 좌표
        top, bot = hb + int(6 * u), mh - int((175 if text else 50) * u)  # 아래 글 자리 (기본 화면은 두 줄만)
        sx = (mw - 16) / (MAP_Y[1] - MAP_Y[0])
        sy = (bot - top) / (MAP_X[1] - MAP_X[0])
        sc = min(sx, sy)
        ox = (mw - sc * (MAP_Y[1] - MAP_Y[0])) / 2
        oy = top

        def T(x, y):  # 로봇 아래 (남) · 상자 위 (북), 로봇이 위를 봄 → 로봇 왼쪽 (+y) = 그림 왼쪽 (front 화면을 180° 돌린 방향)
            return ox + (MAP_Y[1] - y) * sc, oy + (MAP_X[1] - x) * sc

        def R(x, y, h):  # 탁자 위 정사각형 (축 정렬) → 그림 사각형 [x0, y0, x1, y1]
            (ax, ay), (bx_, by_) = T(x - h, y - h), T(x + h, y + h)
            return [min(ax, bx_), min(ay, by_), max(ax, bx_), max(ay, by_)]

        x0_, y0_ = T(MAP_X[1], MAP_Y[1])
        x1_, y1_ = T(MAP_X[0], MAP_Y[0])
        d.rectangle([x0_, y0_, x1_, y1_], fill=(55, 65, 81))  # 탁자
        base = self.cfg.get("_base", {})
        hz = ((base.get("workspace") or {}).get("hard_zones_cm") or [])
        for z in hz:
            pts = [T(a, b) for a, b in z["polygon"]]
            dashed_poly(d, pts, (96, 165, 250), 1, dash=5)
            lx = min(p[0] for p in pts)
            ly = min(p[1] for p in pts)
            d.text((lx + 3, ly + 3), "어려운 영역", font=fxs, fill=(147, 197, 253))
        bx = base.get("box") or {}
        if bx.get("center_cm"):
            (bcx, bcy), (bsx, bsy) = bx["center_cm"], bx.get("inner_size_cm", [12, 22.5])
            (ax, ay), (bx2, by2) = T(bcx - bsx / 2, bcy - bsy / 2), T(bcx + bsx / 2, bcy + bsy / 2)
            d.rectangle([min(ax, bx2), min(ay, by2), max(ax, bx2), max(ay, by2)], outline=(180, 120, 60), width=3, fill=(92, 64, 40))
            cxb, cyb = T(bcx, bcy)
            d.text((cxb - 14 * u, cyb - 8 * u), "상자", font=fs_, fill=(253, 230, 138))
        rb = (base.get("robot") or {}).get("base_xy_cm", [-31, 11])
        rx, ry = T(*rb)
        rr = 3.5 * sc
        d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=(17, 24, 39), outline=(156, 163, 175), width=2)
        d.polygon([(rx - rr * 0.6, ry - rr * 0.6), (rx + rr * 0.6, ry - rr * 0.6), (rx, ry - rr * 1.7)], fill=(156, 163, 175))  # 로봇 정면 = 위 (북쪽, 상자 쪽)
        d.text((rx + rr + 4, ry - 8 * u), "로봇", font=fs_, fill=(209, 213, 219))
        d.text((x0_ + 4, y1_ - 18 * u), "← 로봇 왼쪽", font=fxs, fill=(209, 213, 219))
        t_r = "로봇 오른쪽 →"
        d.text((x1_ - _tw(d, t_r, fxs)[0] - 4, y1_ - 18 * u), t_r, font=fxs, fill=(209, 213, 219))
        s50 = self.cfg.get("sg50") or {}
        for nm, (ex, ey) in ((s50.get("eval_reserved") or {}).get("points") or {}).items():  # 평가 전용 자리
            px_, py_ = T(ex, ey)
            k_ = 0.9 * sc
            d.line([(px_ - k_, py_ - k_), (px_ + k_, py_ + k_)], fill=(127, 29, 29), width=2)
            d.line([(px_ - k_, py_ + k_), (px_ + k_, py_ - k_)], fill=(127, 29, 29), width=2)
        h = 1.25
        for nm, pd in (s50.get("positions") or {}).items():  # 수집 자리
            try:
                x_, y_ = rc.known_xy(self.cfg, nm)
            except KeyError:
                continue
            r4 = R(x_, y_, h)
            a_, b_ = (r4[0], r4[1]), (r4[2], r4[3])
            if pd.get("confirmed", True):
                d.rectangle(r4, outline=(156, 163, 175), width=1)
            else:
                dashed_poly(d, [a_, (b_[0], a_[1]), b_, (a_[0], b_[1])], (156, 163, 175), 1, dash=3)
            d.text((b_[0] + 2, a_[1] - 2), nm, font=fxs, fill=(156, 163, 175))
        pos = row.get("position")
        if pos:
            try:
                x_, y_ = rc.known_xy(self.cfg, pos)
                cx_, cy_ = T(x_, y_)
                tc = (220, 38, 38) if state != "REC" else (248, 113, 113)
                r_ = 3.2 * sc
                d.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], outline=(255, 255, 255), width=2)
                d.rectangle(R(x_, y_, h), fill=tc, outline=(255, 255, 255), width=2)  # 0° = 면이 로봇 좌우축과 나란함 → 그림에서 축 정렬
                tx = cx_ + r_ + 4 if cx_ < mw * 0.6 else cx_ - r_ - 4 - _tw(d, pos, fb)[0]
                d.text((tx, cy_ - 12 * u), pos, font=fb, fill=(255, 255, 255))
                fr = (self.vis or {}).get("front") or {}
                if fr.get("detected") and state != "REC" and not self.health.stale(time.time()):
                    gx, gy = T(*fr["xy_cm"])
                    d.line([(gx, gy), (cx_, cy_)], fill=OK, width=1)
                    d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=OK)
            except KeyError:
                pass
        tb = oy + sc * (MAP_X[1] - MAP_X[0]) + int(8 * u)  # 탁자 그림 바로 아래
        if state in ("REC", "SAVING", "FINAL"):  # 단계 덮개: 녹화 중 = 빨강, 저장 중 = 파랑
            ov = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            oc = (220, 38, 38, 110) if state == "REC" else (29, 78, 216, 120)
            od.rectangle([x0_, y0_, x1_, y1_], fill=oc)
            im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
            d = ImageDraw.Draw(im)
            big = font((40 if text else 30) * u)
            msg = "● 녹화 중" if state == "REC" else "저장 중…"
            tw, th = _tw(d, msg, big)
            mx, my = (x0_ + x1_) / 2, (y0_ + y1_) / 2
            d.text((mx - tw / 2, my - th - 6), msg, font=big, fill=(255, 255, 255))
            sub = (f"{time.time() - self.rec_t0:4.1f} s" if state == "REC" and self.rec_t0 else "다음 위치는 저장 뒤")
            tw2, _ = _tw(d, sub, fb)
            d.text((mx - tw2 / 2, my + 8), sub, font=fb, fill=(255, 255, 255))
        # 아래 글 (탁자 그림 바로 아래)
        q = (self.cfg.get("scenarios", {}).get(row.get("scenario_id", ""), {}) or {}).get("pose", "")
        pn = ((s50.get("start_poses") or {}).get(q) or {}).get("name", "")
        if q == "FREE":
            q, pn = "자유", "(직접 정함)"
        fl = font(19 * u)
        if not text:  # 기본 화면 (4:3 칸): 위치 · 시작 자세 한 줄 + 진행 한 줄
            conf = (s50.get("positions") or {}).get(pos, {}).get("confirmed", True) if pos else True
            lead = "다음 " if state == "RESET" else ""
            line = (f"{lead}{pos} · 0° · 시작 자세 {q} {pn}" + ("" if conf else " · 미확정 좌표")) if pos else "계획 없음"
            d.text((8, mh - int(44 * u)), line, font=fs_, fill=FG if conf else WARN)
            prog = f"완료 {ui.get('done', '?')}/{ui.get('target', '?')} · run {(self.st.get('run_id') or '?')}" + (" · PREVIEW" if ui.get("preview") else "")
            d.text((8, mh - int(20 * u)), prog + " · F5 디버그", font=fxs, fill=DIM)
            if state == "REC":
                d.rectangle([0, 0, mw - 1, mh - 1], outline=(220, 38, 38), width=4)
            return im
        if pos:
            conf = (s50.get("positions") or {}).get(pos, {}).get("confirmed", True)
            lead = "다음 위치 " if state == "RESET" else ""
            d.text((8, tb), f"{lead}{pos}" + (f" ({row.get('cube_xy_cm', '')} cm)" if text else "") + " · 회전 0°", font=fl, fill=FG)
            if not conf:
                d.text((8, tb + int(26 * u)), "미확정 좌표 — front 의 빨간 원에 놓고 확인", font=fs_, fill=WARN)
            d.text((8, tb + int(48 * u)), f"시작 자세 {q} {pn}" if q else "", font=fl, fill=FG)
        else:
            d.text((8, tb), "계획 없음 (카메라 미리보기는 --session 으로 계획 표시)", font=fs_, fill=DIM)
        ly = tb + int(80 * u)
        for t_ in ("□ 수집 자리 (점선 = 미확정 좌표)", "빨간 x = 평가 자리 (놓지 않음)", "초록 점 = front 에서 본 큐브"):
            d.text((8, ly), t_, font=fxs, fill=DIM)
            ly += int(17 * u)
        prog = f"완료 {ui.get('done', '?')}/{ui.get('target', '?')} · run {(self.st.get('run_id') or '?')}" + (" · PREVIEW" if ui.get("preview") else "")
        d.text((8, mh - int(18 * u)), prog + "   F5 디버그", font=fxs, fill=DIM)
        if state == "REC":  # 녹화 중 = 빨간 테두리
            d.rectangle([0, 0, mw - 1, mh - 1], outline=(220, 38, 38), width=4)
        return im

    def draw_front(self, img, s, row, stale):
        from PIL import ImageDraw

        im = img.copy()
        d = ImageDraw.Draw(im)
        f = font(max(11, im.size[0] / 40))
        pos = row.get("position")
        if pos:
            try:
                x, y = rc.known_xy(self.cfg, pos)
                h = 1.25  # 2.5 cm 큐브 반
                corners = [rc.cm_to_px(self.H, (x + a, y + b)) for a, b in ((-h, -h), (-h, h), (h, h), (h, -h))]
                pts = [(px * s, py * s) for px, py in corners]
                cx, cy = rc.cm_to_px(self.H, (x, y))
                cx, cy = cx * s, cy * s
                rec = (self.ui.get("state") in ("REC", "SAVING", "FINAL"))
                if rec:  # 녹화 중에는 가늘게 (영상 가리지 않게)
                    dashed_poly(d, pts, C_PLAN, 1, dash=4)
                else:
                    r_ = max(18, 2.2 * max(abs(pts[0][0] - pts[2][0]), abs(pts[0][1] - pts[2][1])))
                    d.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], outline=C_TGT, width=3)
                    for (x1, y1, x2, y2) in ((cx - r_ - 14, cy, cx - r_ + 4, cy), (cx + r_ - 4, cy, cx + r_ + 14, cy),
                                             (cx, cy - r_ - 14, cx, cy - r_ + 4), (cx, cy + r_ - 4, cx, cy + r_ + 14)):
                        d.line([(x1, y1), (x2, y2)], fill=C_TGT, width=3)
                    d.polygon(pts, outline=(255, 255, 255))
                    dashed_poly(d, pts, C_TGT, 2, dash=4)
                    label(d, (min(cx + r_ + 8, im.size[0] - 150), cy - 14), f"여기 놓기 {pos} · 0°", f, (255, 255, 255), C_TGT)
            except Exception:
                pass
        fr = (self.vis or {}).get("front") or {}
        if fr.get("detected") and not stale:
            cx, cy = fr["px"]
            d.ellipse([cx * s - 4, cy * s - 4, cx * s + 4, cy * s + 4], fill=OK)
            dist = fr.get("dist_planned_cm")
            col = OK if dist is not None and dist <= 2.0 else WARN
            if self.debug:
                label(d, (8, im.size[1] - 30), f"front 큐브 ({fr['xy_cm'][0]:.1f}, {fr['xy_cm'][1]:.1f}) cm" +
                      (f" · 목표까지 {dist:.1f} cm" if dist is not None else ""), f, col)
        return im

    def draw_bottom(self, d, x, y, W, H, u, row, stale):
        fm, fs = font(16 * u), font(13 * u)
        lh = int(22 * u)
        det = self.det if (self.show_det and not stale) else None
        if stale:
            d.text((x, y), "스티커: 영상이 오래되어 표시 안 함", font=fm, fill=BAD)
        elif not self.show_det:
            d.text((x, y), "스티커: 검출 표시 꺼짐 (F3)", font=fm, fill=DIM)
        elif det is None:
            d.text((x, y), "스티커: 아직 검출 안 함", font=fm, fill=DIM)
        else:
            stv = det["status"]
            if det.get("sticker"):
                stk = det["sticker"]
                t = (f"스티커 {sgs.STATUS_KO[stv]}: u {stk['u']:.3f} · v {stk['v']:.3f} (원본 손목 640×480 기준 0–1, 원점 왼쪽 위) · "
                     f"px ({stk['px'][0]:.0f}, {stk['px'][1]:.0f}) · 큐브 안 ({stk['in_cube'][0]:.2f}, {stk['in_cube'][1]:.2f})")
            else:
                t = f"스티커 {sgs.STATUS_KO[stv]}" + (f" — {det['reason']}" if det.get("reason") else "")
            d.text((x, y), t, font=fm, fill=STK_COL[stv])
            if stv == "uncertain" and det.get("reason"):
                y += lh
                d.text((x, y), f"  불확실 이유: {det['reason']}", font=fs, fill=WARN)
        y += lh
        refs = getattr(self, "refs", None) or ([self.ref] if self.ref else [])
        if refs and self.show_ref:
            for k, ref in enumerate(refs):
                if k:
                    y += lh
                nm = f"{ref.get('name') or ''} {ref['version']}".strip()
                c = sgs.ref_compare(det, ref) if det else None
                if ref.get("kind") == "target":
                    t = sgs.target_compare(det, ref) if det else None
                    if t:
                        n_ok = sum(t["ok"].values())
                        d.text((x, y), f"닫기 자리 목표 {nm}: 큐브 du {t['du']:+.3f} · dv {t['dv']:+.3f} · 크기 {t['size'] * 100:.0f}% · 회전 {t['dangle']:+.1f}° · "
                               f"허용 안 {n_ok}/4 (판정 아님)", font=fs, fill=C_GUIDE_OK if t["all"] else C_TGT_GUIDE)
                    else:
                        d.text((x, y), f"닫기 자리 목표 {nm}: 큐브 검출 없음", font=fs, fill=DIM)
                    continue
                if ref.get("kind") == "cross":
                    if c:
                        d.text((x, y), f"큐브 십자 {nm} (u {ref['u']:.3f}, v {ref['v']:.3f}): 큐브 중심 du {c['du']:+.3f} · dv {c['dv']:+.3f} · "
                               + ("십자 근처 (±0.03)" if c["inside"] else "십자 밖") + (f" · 큐브 크기 비 {c['size_ratio']:.2f}" if c.get("size_ratio") else "")
                               + " (판정 아님)", font=fs, fill=C_CROSS)
                    else:
                        d.text((x, y), f"큐브 십자 {nm} (u {ref['u']:.3f}, v {ref['v']:.3f}): 큐브 검출 없음", font=fs, fill=DIM)
                    continue
                if c:
                    t = (f"정렬 참고 {nm} (u {ref['u']:.3f}, v {ref['v']:.3f}): du {c['du']:+.3f} · dv {c['dv']:+.3f} · " + ("참고 영역 안" if c["inside"] else "참고 영역 밖")
                         + (f" · 큐브 크기 비 {c['size_ratio']:.2f}" if c.get("size_ratio") else ""))
                    warn = c.get("size_ratio") and not 0.8 <= c["size_ratio"] <= 1.25
                    d.text((x, y), t + ("  — 참조 때와 거리 · 높이가 달라 참고 약함" if warn else ""), font=fs, fill=WARN if warn else C_REF)
                else:
                    d.text((x, y), f"정렬 참고 {nm} (u {ref['u']:.3f}, v {ref['v']:.3f}): 스티커 검출이 없어 비교 안 함 (자동 판정 아님)", font=fs, fill=DIM)
        else:
            d.text((x, y), "정렬 참고: 없음 (예비 시연 확인 뒤 sg_sticker.py set-ref 로 설정)" if not self.ref else "정렬 참고 표시 꺼짐 (F2)",
                   font=fs, fill=DIM)
        y += lh
        lv = self.level()
        if getattr(self, "open_alert", False):
            d.text((x, y), "그리퍼 열기 알림: 숄더팬 정렬 · 찾기 · 이동을 그리퍼를 안 연 채 시작함 (참고, 자동 동작 없음)", font=fs, fill=C_OPEN_ALERT)
            y += lh
        if self.tilt:
            d.text((x, y), f"그리퍼 기울기 (수평계): 보정 뒤 앞뒤 {lv[0]:+.1f}° (+ = 손끝 로봇에서 멀리, 0 = 지면과 수직) · FK 계산 {self.tilt[0]:+.1f}° · "
                   f"목표 {lv[2]:+g}° ± {lv[1]:g}° (참고, FK 계산값)" if lv else f"그리퍼 기울기: 앞뒤 {self.tilt[0]:+.1f}°", font=fs,
                   fill=C_GUIDE_OK if lv and abs(lv[0] - lv[2]) <= lv[1] else C_TGT_GUIDE)
            y += lh
        lines = pose_lines(self.cfg, row, self.st.get("state"))
        if lines:
            d.text((x, y), lines[0][0] + "   (팔로워 지금 / 목표, 녹화를 막지 않음)", font=fs, fill=FG)
            y += lh
            xx = x
            for t, col in lines[1]:
                d.text((xx, y), t, font=fs, fill=col)
                xx += _tw(d, t, fs)[0] + int(14 * u)
            y += lh
        hz = self.st.get("loop_hz")
        age = (time.time() - self.health.seq_t) if self.health.seq_t else None
        dm = np.median(self.perf["detect"]) if self.perf["detect"] else None
        foot = (f"녹화 루프 {hz} Hz · 프레임 나이 {age:.2f} s" if age is not None else f"녹화 루프 {hz} Hz · 프레임 없음") + \
               f" · 녹화 프레임 {self.st.get('rec_frames', '-')} · 늦은 틱 {self.st.get('late_ticks', '-')} · 카메라 반복 " + \
               (" ".join(f"{k} {v}" for k, v in self.st["stall_ticks"].items()) if isinstance(self.st.get("stall_ticks"), dict) else "-") + \
               (f" · 검출 {dm:.0f} ms" if dm is not None else "") + f" · {self.P['_version']} · 창 키 F3 검출 · F2 참고 · F4 위 그림 · F5 기본 화면"
        d.text((x, H - int(22 * u)), foot, font=font(12 * u), fill=DIM)

    def perf_summary(self):
        r, dt = list(self.perf["render"]), list(self.perf["detect"])
        q = lambda a, p: round(float(np.percentile(a, p)), 2) if a else None  # noqa: E731
        return {"t": time.time(), "show_det": self.show_det, "render_ms_p50": q(r, 50), "render_ms_p95": q(r, 95),
                "detect_ms_p50": q(dt, 50), "detect_ms_p95": q(dt, 95), "new_frames": self.perf["new_frames"],
                "detect_runs": self.perf["detect_runs"], "elapsed_s": round(time.time() - self.perf["t0"], 1)}


class App:
    KEYMAP = {"Right": b"\x1b[C", "Left": b"\x1b[D", "Escape": b"\x1b", "Return": b"\r", "KP_Enter": b"\r", "BackSpace": b"\x7f"}

    def __init__(self, live, scale):
        import tkinter as tk

        self.tk = tk
        self.live = live
        self.scr = Screen(live)
        root = self.root = tk.Tk()
        root.title(TITLE)
        root.configure(bg="#111827")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w = min(int(1920 * scale), int(sw * 0.98))  # 기본 화면 = 같은 크기 4:3 세 칸 한 줄 → 넓고 낮은 창
        h = min(int((w - 32) / 3 * 0.75) + 24, int(sh * 0.92))
        geo = rc.read_json(os.path.join(live, "viewer_geometry.json"))
        root.geometry(geo["geometry"] if geo else f"{w}x{h}")
        self.lab = tk.Label(root, bg="#111827", bd=0)
        self.lab.pack(fill="both", expand=True)
        self.size = (w, h)
        root.bind("<Configure>", self.on_resize)
        root.bind("<Key>", self.on_key)
        self.last_perf = time.time()
        root.after(50, self.tick)

    def on_resize(self, e):
        if e.widget is self.root:
            self.size = (e.width, e.height)

    def on_key(self, e):
        if e.keysym == "F3":
            self.scr.show_det = not self.scr.show_det
            if not self.scr.show_det:
                self.scr.det = None
            return
        if e.keysym == "F2":
            self.scr.show_ref = not self.scr.show_ref
            return
        if e.keysym == "F4":
            self.scr.show_map = not self.scr.show_map
            return
        if e.keysym == "F5":
            self.scr.debug = not self.scr.debug
            return
        if e.keysym.startswith("F") and e.keysym[1:].isdigit():
            return
        data = self.KEYMAP.get(e.keysym) or (e.char.encode() if e.char and e.char.isprintable() else b"")
        if data:  # 녹화 키 → 수집 UI (터미널 키와 같은 검사, r12 viewer 와 같은 길)
            with open(os.path.join(self.live, "keys.in"), "ab") as f:
                f.write(data.hex().encode() + b"\n")

    def cmd_check(self):
        """시험용: live/viewer_cmd.json {"keys": ["F3"]} = 창 키 (한 번 읽고 지움)."""
        p = os.path.join(self.live, "viewer_cmd.json")
        req = rc.read_json(p)
        if not req:
            return
        os.unlink(p)
        import types

        for k in req.get("keys", []):
            if k in ("F2", "F3", "F4", "F5"):
                self.on_key(types.SimpleNamespace(keysym=k, char=""))

    def tick(self):
        from PIL import ImageTk

        t_start = time.time()
        try:
            self.cmd_check()
            self.scr.poll()
            w, h = self.size
            im = self.scr.render(max(w, 480), max(h, 360))
            self.photo = ImageTk.PhotoImage(im)
            self.lab.configure(image=self.photo)
            if time.time() - self.last_perf > 5:
                rc.write_json(os.path.join(self.live, "viewer_perf.json"), {**self.scr.perf_summary(), "window": [w, h]})
                self.last_perf = time.time()
        except Exception as e:  # 화면 오류로 녹화가 영향받지 않게 — 기록만
            with open(os.path.join(self.live, "viewer.log"), "a") as f:
                f.write(f"{time.strftime('%H:%M:%S')} tick error {e!r}\n")
        self.root.after(max(5, int(66 - (time.time() - t_start) * 1000)), self.tick)  # 약 15 장/s (공유 프레임이 15 장/s)

    def run(self):
        rc.write_json(os.path.join(self.live, "viewer_ready.json"), {"pid": os.getpid(), "t": time.time(), "viewer": "sg"})
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", required=True)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--render", help="창 없이 한 장 그려 PNG 로 (시험 · 화면 예시)")
    ap.add_argument("--size", default="1400x860")
    ap.add_argument("--no-det", action="store_true")
    ap.add_argument("--debug", action="store_true", help="좌표 · 검출 수치 디버그 화면으로 시작 (창에서 F5 로 바꿈)")
    ap.add_argument("--bench", type=float, help="창 없이 N 초 동안 Tk 화면과 같은 주기 (50 ms) 로 읽기 · 검출 · 그리기 → live/viewer_perf.json (시험용)")
    a = ap.parse_args()
    if a.bench:
        from PIL import Image  # noqa: F401

        scr = Screen(a.live)
        scr.show_det = not a.no_det
        scr.debug = a.debug
        w, h = (int(v) for v in a.size.lower().split("x"))
        end = time.time() + a.bench
        while time.time() < end:
            t0 = time.time()
            scr.poll()
            im = scr.render(w, h)
            im.tobytes()  # Tk PhotoImage 로 넘길 때의 복사 비용 대신
            time.sleep(max(0.0, 0.05 - (time.time() - t0)))
        out = {**scr.perf_summary(), "window": [w, h], "mode": "bench"}
        rc.write_json(os.path.join(a.live, "viewer_perf.json"), out)
        print(json.dumps(out, ensure_ascii=False))
        return 0
    if a.render:
        scr = Screen(a.live)
        scr.show_det = not a.no_det
        scr.debug = a.debug
        scr.poll()
        w, h = (int(v) for v in a.size.lower().split("x"))
        scr.render(w, h).save(a.render)
        print(json.dumps(scr.perf_summary(), ensure_ascii=False))
        return 0
    if not os.environ.get("DISPLAY"):
        print("DISPLAY 가 없어 화면 창을 열 수 없어요 (터미널 배너만으로 진행).", file=sys.stderr)
        return 3
    app = App(a.live, a.scale)
    app.scr.debug = a.debug
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
