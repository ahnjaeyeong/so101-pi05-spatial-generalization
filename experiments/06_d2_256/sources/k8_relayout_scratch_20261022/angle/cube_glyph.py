"""회전 큐브 Top View 를 터미널 글자로 그리기 (미리보기 전용, record_ui 는 안 고침).
좌표: 로봇 = 화면 아래, 정면(상자) = 위. 각도 θ: 로봇에 가장 가까운 면의 모서리와 X축(가로)의 예각.
방향: L = 위에서 볼 때 반시계(↺, 왼쪽으로 돌림), R = 시계(↻). 0°·45° 는 방향 없음 (45° 는 좌우 같은 모양)."""
import math, unicodedata

# 256색 (배너 seg 의 배경/글자 코드로 바로 씀)
RGB256 = {"red": 160, "orange": 208, "yellow": 220, "blue": 26, "green": 34}
NEAR = 16        # 로봇 쪽 면 강조선 = 검정
EDGE = 244       # 나머지 테두리 = 회색 (흰 바탕에서 노랑도 보이게)
COLOR_KO = {"red": "빨강", "yellow": "노랑", "orange": "주황", "blue": "파랑", "green": "초록"}


def signed(angle, side):
    """L30 → +30 (반시계), R30 → −30. 0° 는 그대로, 45° 는 좌우가 같은 모양이라 +45."""
    a = abs(float(angle))
    return a if a == 45 or (side or "").upper() == "L" else -a


def raster(color, angle, side, w=16, h=16, band=1.5, outline=False, ss=4):
    """픽셀 격자 [[256색 코드 또는 None(바탕)]] (h 줄 × w 칸). 픽셀마다 ss×ss 점을 찍어 반 넘게 덮이면 칠한다.
    band: 로봇 쪽 면 강조선 두께(px). outline: 테두리만 (점자용)."""
    th = math.radians(signed(angle, side))
    hs = min(w, h) / math.sqrt(2) * 0.97 / 2            # 반 변 — 45° 로 돌려도 칸 안
    c, sn = math.cos(-th), math.sin(-th)
    a45 = abs(float(angle)) == 45
    out = []
    for py in range(h):
        row = []
        for px in range(w):
            inside = near = edge = 0
            for i in range(ss):
                for j in range(ss):
                    u, v = px + (i + .5) / ss - w / 2, -(py + (j + .5) / ss - h / 2)
                    lx, ly = u * c - v * sn, u * sn + v * c
                    m = max(abs(lx), abs(ly))
                    if m > hs:
                        continue
                    inside += 1
                    nb = ly <= -hs + band or (a45 and lx <= -hs + band)   # 45°: 아래 두 면 (꼭짓점이 로봇 쪽)
                    near += nb
                    edge += (hs - m) < band
            n = ss * ss
            if inside < n / 2:
                row.append(None)
            elif near >= inside / 2:
                row.append(NEAR)
            elif outline and edge < inside / 2:
                row.append(None)
            else:
                row.append(RGB256[color])
        out.append(row)
    return out


def halfblock_segs(pix, bg=None):
    """픽셀 2줄 → 글자 1줄. 위·아래 둘 다 칠하면 ▀(글자색 = 위, 배경 = 아래), 하나만이면 ▀/▄ + 배너 바탕 그대로."""
    rows = []
    for y in range(0, len(pix), 2):
        segs = []
        for t, b in zip(pix[y], pix[y + 1]):
            if t is None and b is None:
                segs.append((" ", None, None))
            elif b is None:
                segs.append(("▀", None, f"38;5;{t}"))
            elif t is None:
                segs.append(("▄", None, f"38;5;{b}"))
            else:
                segs.append(("▀", f"48;5;{b}", f"38;5;{t}"))
        rows.append(segs)
    return rows


def braille_segs(color, angle, side, cols=12, rows=6):
    """점자 글자(칸마다 2×4 점)로 테두리만. 칸마다 글자색 1개 → 로봇 쪽 면이 있는 칸은 검정, 나머지는 큐브 색."""
    pix = raster(color, angle, side, cols * 2, rows * 4, band=1.6, outline=True, ss=3)
    out = []
    for r in range(rows):
        segs = []
        for cc in range(cols):
            bits, near = 0, False
            for dy, dx, bit in ((0, 0, 0), (1, 0, 1), (2, 0, 2), (0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 0, 6), (3, 1, 7)):
                p = pix[r * 4 + dy][cc * 2 + dx]
                if p is not None:
                    bits |= 1 << bit
                    near = near or p == NEAR
            segs.append((chr(0x2800 + bits) if bits else " ", None, f"38;5;{NEAR if near else RGB256[color]}"))
        out.append(segs)
    return out


def angle_text(angle, side):
    a = int(abs(float(angle)))
    if a in (0, 45) or not side:
        return f"{a}°" + (" (꼭짓점이 로봇 쪽)" if a == 45 else "")
    return f"↺ 왼쪽 {a}°" if side.upper() == "L" else f"↻ 오른쪽 {a}°"
