"""네모 그림 (개념도) 그리기 — 수집자 모드 가이드 (2026-11-03). Tk 없이 PIL 만 써서 시험 · 문서용 PNG 로도 뽑을 수 있다.

그림 언어 (모든 시나리오 공통, 09/10 문서 §도식 규칙):
  큐브 = 빨간 네모 (실선 = 지금 상대 위치) · 그리퍼 손가락 = 회색 막대 2 개 (벌어짐 = 열림, 가까움 = 닫힘)
  참고 목표 위치 = 초록 점선 네모 · 화면 속 위치 변화 = 파란 화살표 · 하면 안 됨 = 빨간 X · 올바른 예 = 초록 체크
  화면 끝 잘림 = 잘린 쪽 빨간 띠 · 이전 위치 = 흐린 점선 네모 (ghost)

좌표: 손목 카메라 화면처럼 그린다 (손가락이 화면 아래에서 위로, 큐브가 위쪽 = 손가락 끝보다 앞). u 오른쪽 + · v 아래 + (0–1).
이것은 개념도다: 위치 · 크기는 실제 측정값이 아니고, 화살표는 화면 속 큐브의 위치 변화이지 로봇 관절의 이동 방향이 아니다.

장면 (scene) = dict (설정 yaml 의 visual_guide 에 그대로 적는다):
  grip:    open | closed | grasp           (grasp = 손가락이 큐브 양옆에 붙음)
  cube:    [u, v] 큐브 중심 (없으면 큐브 안 그림)
  ghost:   [u, v] 이전 위치 (흐린 점선)
  target:  true  → 참고 목표 위치 (초록 점선)
  arrow:   true (큐브 → 목표) | [[u0, v0], [u1, v1]]
  mark:    x | check
  cut:     bottom | top | left | right     (큐브가 그 쪽 화면 경계에서 잘림 — 빨간 띠)
  inset:   다른 장면 (작게, 오른쪽 위 — 예: 잘못된 예)
  tag:     그림 왼쪽 위 작은 글 (기본 '개념도')
"""

import math

FONT_FILE = "/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf"

SCREEN = (214, 218, 224)      # 손목 화면 바탕 (밝은 회색 — 실제 영상처럼)
FRAME = (75, 85, 99)
FINGER, FINGER_EDGE, FINGER_TIP = (120, 126, 136), (55, 60, 70), (160, 166, 176)
CUBE, CUBE_EDGE = (220, 38, 38), (127, 29, 29)
TARGET = (22, 163, 74)
ARROW = (37, 99, 235)
XMARK = (220, 38, 38)
CHECK = (22, 163, 74)
GHOST = (220, 38, 38)

# 그림 기본 기하 (화면 비율 4:3) — 실제 손목 영상에 맞춤 (11-03: d2 '다 열림' 프레임 16 장 평균에서 손가락 끝
# 왼쪽 u≈0.07 v≈0.72 · 오른쪽 u≈0.63 v≈0.66, 닫기 영역 u 0.255–0.432 · v 0.633–0.78). 실시간 손목 영상과 나란히 놓고 비교할 수 있게.
FINGER_W = 0.13
FINGER_TIP_V = 0.67
FINGER_X_OPEN = (0.07, 0.63)
FINGER_X_CLOSED = (0.27, 0.42)
CUBE_S = 0.32                 # 큐브 한 변 (화면 높이 비율, v 0.7 기준 — 멀수록 (v 작을수록) 작게 그림)
TARGET_UV = (0.344, 0.707)    # 닫기 영역 가운데
ZONE = (0.255, 0.432, 0.633, 0.78)


def cube_size(v):
    """원근: 화면 위쪽 (멀리) 일수록 작게. v 0.7 → CUBE_S."""
    return CUBE_S * (0.55 + 0.65 * v) / (0.55 + 0.65 * 0.7)


def _font(px):
    from PIL import ImageFont

    try:
        return ImageFont.truetype(FONT_FILE, max(8, int(px)))
    except OSError:
        return ImageFont.load_default()


def _dashed_rect(d, box, col, width, dash):
    x0, y0, x1, y1 = box
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = max(abs(bx - ax), abs(by - ay), 1)
        n = max(2, int(L // dash))
        for k in range(0, n, 2):
            d.line([(ax + (bx - ax) * k / n, ay + (by - ay) * k / n), (ax + (bx - ax) * (k + 1) / n, ay + (by - ay) * (k + 1) / n)],
                   fill=col, width=width)


def _arrow(d, p0, p1, col, width):
    d.line([p0, p1], fill=col, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L = width * 3.6
    pts = [p1, (p1[0] - L * math.cos(ang - 0.5), p1[1] - L * math.sin(ang - 0.5)),
           (p1[0] - L * math.cos(ang + 0.5), p1[1] - L * math.sin(ang + 0.5))]
    d.polygon(pts, fill=col)


def _x(d, cx, cy, r, col, width):
    d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=col, width=width)
    d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=col, width=width)


def _check(d, cx, cy, r, col, width):
    d.line([(cx - r, cy), (cx - r * 0.25, cy + r * 0.7), (cx + r, cy - r * 0.8)], fill=col, width=width, joint="curve")


def _draw(d, scene, ox, oy, W, H, base_w):
    """scene 을 (ox, oy) 에서 W×H 크기로. base_w = 선 굵기 기준."""
    lw = max(2, int(base_w / 70))
    d.rectangle([ox, oy, ox + W, oy + H], fill=SCREEN)
    S = cube_size((scene.get("cube") or TARGET_UV)[1]) * H

    def P(u, v):
        return ox + u * W, oy + v * H

    grip = scene.get("grip", "open")
    cube = scene.get("cube")
    # 손가락 x
    if grip == "grasp" and cube:
        cx = P(*cube)[0] - ox
        fx = ((cx - S / 2 - FINGER_W * W / 2 + lw) / W, (cx + S / 2 + FINGER_W * W / 2 - lw) / W)
    elif grip == "closed":
        fx = FINGER_X_CLOSED
    else:
        fx = FINGER_X_OPEN
    if scene.get("target"):
        St = cube_size(TARGET_UV[1]) * H
        tx, ty = P(*TARGET_UV)
        _dashed_rect(d, (tx - St / 2, ty - St / 2, tx + St / 2, ty + St / 2), TARGET, lw + 1, max(6, St / 6))
    if scene.get("ghost"):
        gx, gy = P(*scene["ghost"])
        Sg = cube_size(scene["ghost"][1]) * H
        _dashed_rect(d, (gx - Sg / 2, gy - Sg / 2, gx + Sg / 2, gy + Sg / 2), GHOST, max(1, lw - 1), max(5, Sg / 8))
    # 큐브는 손가락보다 뒤 (손가락이 화면 앞쪽에 있음 — 실제 손목 영상처럼)
    if cube:
        cx, cy = P(*cube)
        d.rectangle([cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2], fill=CUBE, outline=CUBE_EDGE, width=lw)
    # 점선 영역은 큐브 위에 (가려지지 않게), 손가락 아래에
    if scene.get("region"):  # 시작 영역 (주황 점선) — 실시간 손목 화면의 주황 점선과 같은 자리
        u0, u1, v0, v1 = scene["region"]
        _dashed_rect(d, (ox + u0 * W, oy + v0 * H, ox + u1 * W, oy + v1 * H), (234, 88, 12), lw + 1, max(6, W / 40))
    if scene.get("zone"):  # 참고 위치 = 닫기 영역 (초록 점선) — 실시간 손목 화면의 초록 점선과 같은 자리
        u0, u1, v0, v1 = scene["zone"] if isinstance(scene["zone"], (list, tuple)) else ZONE
        _dashed_rect(d, (ox + u0 * W, oy + v0 * H, ox + u1 * W, oy + v1 * H), TARGET, lw + 1, max(6, W / 40))
    for x in fx:
        fw = FINGER_W * W
        xc = ox + x * W
        y0 = oy + FINGER_TIP_V * H
        d.rounded_rectangle([xc - fw / 2, y0, xc + fw / 2, oy + H + fw], radius=fw * 0.35, fill=FINGER, outline=FINGER_EDGE,
                            width=max(1, lw - 1))
        d.rounded_rectangle([xc - fw / 2 + fw * 0.15, y0 + fw * 0.15, xc + fw / 2 - fw * 0.15, y0 + fw * 0.75], radius=fw * 0.2,
                            fill=FINGER_TIP)
    arrow = scene.get("arrow")
    if arrow and cube:
        if arrow is True:
            p0, p1 = P(*cube), P(*TARGET_UV)
        else:
            p0, p1 = P(*arrow[0]), P(*arrow[1])
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if L > S * 0.2:
            # 큐브 중심 → 목표 중심 (흰 테두리를 둘러 큐브 위에서도 보이게)
            k0 = min(0.3, (S * 0.2) / L)
            a0 = (p0[0] + (p1[0] - p0[0]) * k0, p0[1] + (p1[1] - p0[1]) * k0)
            _arrow(d, a0, p1, (255, 255, 255), lw + 6)
            _arrow(d, a0, p1, ARROW, lw + 2)
    cut = scene.get("cut")
    if cut:
        band = max(4, int(H / 22))
        box = {"bottom": (ox, oy + H - band, ox + W, oy + H), "top": (ox, oy, ox + W, oy + band),
               "left": (ox, oy, ox + band, oy + H), "right": (ox + W - band, oy, ox + W, oy + H)}[cut]
        d.rectangle(box, fill=XMARK)
    mark = scene.get("mark")
    r = H * 0.11
    if mark == "x":
        _x(d, ox + W - r * 1.5, oy + r * 1.5, r, XMARK, lw + 3)
    elif mark == "check":
        _check(d, ox + W - r * 1.6, oy + r * 1.5, r, CHECK, lw + 3)
    d.rectangle([ox, oy, ox + W, oy + H], outline=FRAME, width=max(1, lw - 1))


def render(scene, size, ss=2):
    """scene → PIL RGB 이미지 (size = (w, h)). ss 배로 그린 뒤 줄여 매끄럽게."""
    from PIL import Image, ImageDraw

    w, h = int(size[0]), int(size[1])
    W, H = w * ss, h * ss
    im = Image.new("RGB", (W, H), SCREEN)
    d = ImageDraw.Draw(im)
    _draw(d, scene or {}, 0, 0, W - 1, H - 1, W)
    ins = (scene or {}).get("inset")
    if ins:  # 작은 그림 (따로 그려 붙임 — 손가락이 칸 밖으로 넘치지 않게)
        iw, ih = int(W * 0.46), int(H * 0.46)
        ix, iy = W - iw - int(W * 0.02), int(H * 0.02)
        d.rectangle([ix - 4, iy - 4, ix + iw + 4, iy + ih + 4], fill=(255, 255, 255))
        im.paste(render({**ins, "tag": ""}, (iw, ih), ss=1), (ix, iy))
        lab = ins.get("label")
        if lab:
            f = _font(ih * 0.16)
            tw = d.textlength(lab, font=f)
            d.rectangle([ix, iy, ix + tw + 10, iy + ih * 0.21], fill=(255, 255, 255))
            d.text((ix + 5, iy + ih * 0.01), lab, fill=XMARK, font=f)
    tag = (scene or {}).get("tag", "개념도")
    if tag:
        th = min(H * 0.085, 22 * ss)
        f = _font(th)
        tw = d.textlength(tag, font=f)
        d.rectangle([2, 2, 2 + tw + 10, 2 + th * 1.3], fill=(31, 41, 55))
        d.text((7, 3), tag, fill=(229, 231, 235), font=f)
    return im.resize((w, h), Image.LANCZOS)


def render_side(spec, size, ss=2):
    """옆에서 (또는 앞에서) 본 개념도 (배치 방법 칸). 큐브 2.5 cm · 탁자 · 손가락 · 초록 점선 = 닫는 위치 (참고).
    spec:
      view: side (기본) | front
      side — tip: [x, z] cm (x = 큐브 앞면에서 큐브 쪽 +, z = 탁자 위 높이) · angle_deg (손가락 기울기, 90 = 수직으로 내려감)
             (옛 키 gap_cm: tip = [-gap, 1.1] · angle 38)
      front — offset_cm (손가락 사이 중심이 큐브 가운데에서 옆으로, + = 그림 오른쪽) · tip_z (손가락 끝 높이 cm)
      grip: open | closed (앞에서 본 그림만 손가락 사이 간격으로 보임) · label (그림 아래 글) · tag"""
    from PIL import Image, ImageDraw

    w, h = int(size[0]), int(size[1])
    W, H = w * ss, h * ss
    im = Image.new("RGB", (W, H), (241, 243, 246))
    d = ImageDraw.Draw(im)
    lw = max(2, int(W / 160))
    px = min(W / 16.0, H * 0.8 / 7.0)  # 1 cm
    ty = H * 0.88                      # 탁자 면
    d.rectangle([0, ty, W, H], fill=(203, 213, 225))
    cs = 2.5 * px
    view = spec.get("view", "side")
    fw = px * 0.9
    f2 = _font(H * 0.06)

    def bar(tip, ang_deg, col, outline, dash=False, length=None):
        a = math.radians(ang_deg)
        tx, ty_ = tip
        L = length or min(W * 0.40, (ty_ - px * 1.8) / max(math.sin(a), 0.2))  # 손목 덩어리가 그림 안에
        bx, by = tx - L * math.cos(a), ty_ - L * math.sin(a)
        nx, ny = math.sin(a) * fw / 2, -math.cos(a) * fw / 2
        poly = [(bx + nx, by + ny), (tx + nx, ty_ + ny), (tx - nx, ty_ - ny), (bx - nx, by - ny)]
        if dash:
            for a_, b_ in zip(poly, poly[1:] + poly[:1]):
                n = 14
                for k in range(0, n, 2):
                    d.line([(a_[0] + (b_[0] - a_[0]) * k / n, a_[1] + (b_[1] - a_[1]) * k / n),
                            (a_[0] + (b_[0] - a_[0]) * (k + 1) / n, a_[1] + (b_[1] - a_[1]) * (k + 1) / n)], fill=outline, width=lw)
        else:
            d.polygon(poly, fill=col, outline=outline)
        return bx, by

    if view == "front":
        cx0 = W / 2 - cs / 2
        d.rectangle([cx0, ty - cs, cx0 + cs, ty], fill=CUBE, outline=CUBE_EDGE, width=lw)
        for sgn in (-1, 1):  # 참고: 큐브 양옆에 열린 손가락 (초록 점선)
            bar((W / 2 + sgn * (cs / 2 + fw * 0.7), ty - 1.0 * px), 90, None, TARGET, dash=True, length=H * 0.6)
        off = float(spec.get("offset_cm", 2.5)) * px
        gap = (cs / 2 + fw * 0.7) if spec.get("grip", "closed") == "open" else fw * 0.55
        tz = ty - float(spec.get("tip_z", 1.2)) * px
        for sgn in (-1, 1):
            bar((W / 2 + off + sgn * gap, tz), 90, FINGER, FINGER_EDGE, length=H * 0.6)
        d.rounded_rectangle([W / 2 + off - gap - fw, tz - H * 0.6 - px, W / 2 + off + gap + fw, tz - H * 0.6 + px * 0.3], radius=px * 0.3,
                            fill=(75, 85, 99))
        if abs(off) > px * 0.3:  # 어긋난 거리 화살표 (손가락 사이 중심 ↔ 큐브 가운데)
            y = ty - cs - px * 0.8
            _arrow(d, (W / 2 + off * 0.5, y), (W / 2 + lw, y), ARROW, lw + 1)
            _arrow(d, (W / 2 + off * 0.5, y), (W / 2 + off - lw, y), ARROW, lw + 1)
        tag = spec.get("tag", "개념도 · 로봇 뒤에서 봄")
    else:
        cx0 = W * 0.55
        d.rectangle([cx0, ty - cs, cx0 + cs, ty], fill=CUBE, outline=CUBE_EDGE, width=lw)
        P = lambda x, z: (cx0 + x * px, ty - z * px)  # noqa: E731
        bar(P(1.25, 1.0), 90, None, TARGET, dash=True)  # 참고: 큐브 바로 위에서 수직으로 내려와 닫는 위치
        if "tip" in spec:
            tip, ang = spec["tip"], float(spec.get("angle_deg", 38))
        else:
            tip, ang = [-float(spec.get("gap_cm", 2.0)), 1.1], 38.0
        bx, by = bar(P(*tip), ang, FINGER, FINGER_EDGE)
        d.rounded_rectangle([bx - px * 1.2, by - px * 1.2, bx + px * 1.2, by + px * 0.4], radius=px * 0.3, fill=(75, 85, 99))
        gx = tip[0]
        if "tip" not in spec and gx < -0.05:  # 옛 그림: 거리 화살표
            y = ty - 1.1 * px + px * 0.9
            t0x = cx0 + gx * px
            _arrow(d, (t0x + (cx0 - t0x) * 0.5, y), (cx0 - lw, y), ARROW, lw + 1)
            _arrow(d, (t0x + (cx0 - t0x) * 0.5, y), (t0x + lw, y), ARROW, lw + 1)
        tag = spec.get("tag", "개념도 · 옆에서 본 거리")
    lab = spec.get("label", "")
    if lab:
        f = _font(H * 0.075)
        tw = d.textlength(lab, font=f)
        tx = min(max(W / 2 - tw / 2, 6), W - tw - 6)
        d.rectangle([tx - 4, ty + H * 0.005, tx + tw + 4, ty + H * 0.005 + H * 0.09], fill=(255, 255, 255))
        d.text((tx, ty + H * 0.005), lab, fill=(30, 64, 175), font=f)
    gl = "초록 점선 = 닫는 위치 (참고)"
    d.text((W - d.textlength(gl, font=f2) - 10, H * 0.03), gl, fill=TARGET, font=f2)
    tw = d.textlength(tag, font=f2)
    d.rectangle([2, 2, 2 + tw + 10, 2 + H * 0.085], fill=(31, 41, 55))
    d.text((7, 3), tag, fill=(229, 231, 235), font=f2)
    return im.resize((w, h), Image.LANCZOS)


def legend(size):
    """그림 언어 범례 (한 장). 문서 · 화면 위 작은 범례."""
    from PIL import Image, ImageDraw

    w, h = size
    ss = 2
    W, H = w * ss, h * ss
    im = Image.new("RGB", (W, H), (17, 24, 39))
    d = ImageDraw.Draw(im)
    f = _font(H / 9)
    items = [("cube", "큐브"), ("finger", "그리퍼 손가락"), ("target", "참고 목표 위치"), ("arrow", "화면 속 위치 변화"),
             ("x", "하면 안 됨"), ("check", "올바른 예"), ("cut", "화면 끝 잘림")]
    cols = 2
    rows = math.ceil(len(items) / cols)
    cw, rh = W / cols, H / rows
    for i, (k, t) in enumerate(items):
        x0, y0 = (i % cols) * cw + 8, (i // cols) * rh + rh * 0.15
        s = rh * 0.6
        if k == "cube":
            d.rectangle([x0, y0, x0 + s, y0 + s], fill=CUBE, outline=CUBE_EDGE, width=2)
        elif k == "finger":
            for dx in (0, s * 0.6):
                d.rounded_rectangle([x0 + dx, y0, x0 + dx + s * 0.3, y0 + s], radius=4, fill=FINGER, outline=FINGER_EDGE)
        elif k == "target":
            _dashed_rect(d, (x0, y0, x0 + s, y0 + s), TARGET, 3, 6)
        elif k == "arrow":
            _arrow(d, (x0, y0 + s / 2), (x0 + s * 1.2, y0 + s / 2), ARROW, 4)
        elif k == "x":
            _x(d, x0 + s / 2, y0 + s / 2, s * 0.4, XMARK, 5)
        elif k == "check":
            _check(d, x0 + s / 2, y0 + s / 2, s * 0.45, CHECK, 5)
        elif k == "cut":
            d.rectangle([x0, y0 + s * 0.7, x0 + s * 1.2, y0 + s], fill=XMARK)
        d.text((x0 + s * 1.4, y0 + s * 0.05), t, fill=(229, 231, 235), font=f)
    return im.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- 지금 손목 화면 → 실패 그림 고르기 (자동 · 보조)
OBS_KEYS = ("ahead", "side", "edge", "in_zone")
OBS_KO = {"ahead": "앞쪽에 있음", "side": "옆으로 벗어남", "edge": "화면 끝에 걸림", "in_zone": "손가락 사이에 보임 (2D)", None: "큐브 위치 확인 필요"}


def observe(w, zone, fresh=True, margin=0.03):
    """손목 검출 w (r12_common.vision()['wrist']) → (key | None, certain, 근거 글). 2D 화면 관계만 — 물리 깊이 · 접촉은 모름.
    key: ahead (손가락 끝보다 앞 = 화면 위쪽) · side (손가락 사이 밖, 좌우) · edge (화면 경계에서 잘림) · in_zone (참고 위치 안)
    certain=False 이면 화면은 빨강/초록 대신 '큐브 위치 확인 필요' 를 보인다 (경계 근처 · 검출 없음 · 오래된 영상)."""
    if not fresh:
        return None, False, "손목 영상이 갱신되지 않음"
    if not w or not w.get("detected"):
        return None, False, "손목 화면에서 큐브 검출 안 됨"
    z = zone or {"u": [0.255, 0.432], "v": [0.633, 0.78], "area_min": 0.08}
    u, v = (w["dx"] + 1) / 2, (w["dy"] + 1) / 2
    if w.get("touches_edge"):
        x, y, bw, bh = w.get("bbox", (0, 0, 0, 0))
        side = [nm for nm, c in (("위", y <= 2), ("아래", y + bh >= 478), ("왼쪽", x <= 2), ("오른쪽", x + bw >= 638)) if c]
        return "edge", True, f"큐브가 화면 {'·'.join(side) or '경계'} 에서 잘림 (깊이 · 접촉은 직접 확인)"
    if v < z["v"][0] - margin:
        return "ahead", True, f"큐브가 참고 위치보다 화면 위쪽 (v {v:.2f})"
    if u < z["u"][0] - margin or u > z["u"][1] + margin:
        return "side", True, f"큐브가 참고 위치 {'왼쪽' if u < z['u'][0] else '오른쪽'} 밖 (u {u:.2f})"
    if v > z["v"][1] + margin:
        return None, False, f"큐브가 참고 위치보다 아래 (v {v:.2f}) — 직접 확인"
    inside = z["u"][0] <= u <= z["u"][1] and z["v"][0] <= v <= z["v"][1]
    if inside:
        return "in_zone", True, f"큐브가 참고 위치 안 (u {u:.2f} v {v:.2f}, 2D)"
    return None, False, f"참고 위치 경계 근처 (u {u:.2f} v {v:.2f})"


CLOSE_STATES = {
    "A": ("아직 닫지 마세요", (220, 38, 38)),
    "B": ("직접 확인하세요", (217, 119, 6)),
    "C": ("사용자가 확인했습니다", (37, 99, 235)),
    "U": ("큐브 위치 확인 필요", (107, 114, 128)),
    "CLOSED": ("그리퍼 닫힘", (75, 85, 99)),
    "O": ("먼저 그리퍼를 여세요", (217, 119, 6)),
}


def close_state(obs_key, certain, user_ok, grip_open):
    """그리퍼 닫힘 안내 (작업 지시 §7). 반환 (코드, 짧은 글, 설명). 자동으로 '닫아도 됨' 을 보증하지 않는다.
    A = 아직 닫지 마세요 (앞쪽 · 옆 · 잘림) · B = 직접 확인하세요 (2D 로는 손가락 사이, 깊이 · 접촉 모름) ·
    C = 사용자 확인 (사람이 F10 으로 표시, 자동 추론 아님) · U = 확인 필요 (검출 불확실) · CLOSED = 그리퍼 이미 닫힘."""
    if grip_open is False:
        return "CLOSED", CLOSE_STATES["CLOSED"][0], "그리퍼가 닫혀 있어요 — 큐브를 쥐었는지 화면으로 확인"
    if user_ok:
        return "C", CLOSE_STATES["C"][0], "사람이 확인한 표시예요 (자동 판정 아님) — 한 번 닫기"
    if obs_key in ("ahead", "side", "edge"):
        why = {"ahead": "큐브가 손가락 끝보다 앞", "side": "큐브가 손가락 사이 밖", "edge": "큐브가 화면 끝에 걸림"}[obs_key]
        return "A", CLOSE_STATES["A"][0], why + " — 그리퍼를 연 채 고치기"
    if obs_key == "in_zone":
        return "B", CLOSE_STATES["B"][0], "화면에서는 손가락 사이 — 깊이 · 접촉은 직접 보고 확인 (F10 = 확인함)"
    return "U", CLOSE_STATES["U"][0], "자동으로 판단하지 않아요 — 영상을 보고 판단"
