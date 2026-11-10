"""큐브 회전각 표시 미리보기 (preview-only: 화면 출력만, 로봇·카메라·파일·record_ui 안 건드림).
  python3 preview_angles.py            # 1) 0°·L30·R30·45° 비교  2) REC 배너  3) RESET 배너
  python3 preview_angles.py cubes|rec|reset"""
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
import record_ui as ru            # 배너 그리기(banner)만 빌려 씀 — 코드 변경 없음
from cube_glyph import raster, halfblock_segs, braille_segs, angle_text, COLOR_KO

WHITE = "48;5;231"
SAMPLES = [("red", 0, ""), ("red", 15, "L"), ("red", 30, "L"), ("red", 30, "R"), ("red", 45, "")]


def side_by_side(blocks, gap=4):
    """여러 그림(줄마다 seg 목록)을 가로로 붙인다."""
    n = max(len(b) for b in blocks)
    out = []
    for i in range(n):
        segs = []
        for j, b in enumerate(blocks):
            if j:
                segs.append((" " * gap, None, None))
            segs += b[i] if i < len(b) else [(" " * sum(len(t) for t, _, _ in b[0]), None, None)]
        out.append(segs)
    return out


def label_row(texts, width, gap=4):
    segs = []
    for j, t in enumerate(texts):
        if j:
            segs.append((" " * gap, None, None))
        pad = width - ru.disp_width(t)
        segs.append((" " * (pad // 2) + t + " " * (pad - pad // 2), None, None))
    return [segs]


def cubes(ui):
    labels = [angle_text(a, s) for _, a, s in SAMPLES]
    for name, fn, wcol in (("A. 반블록 ▀ 12×12 (색 채움 + 검정 선 = 로봇 쪽 면)", lambda c, a, s: halfblock_segs(raster(c, a, s, 12, 12)), 12),
                           ("A'. 반블록 ▀ 16×16 (더 크게)", lambda c, a, s: halfblock_segs(raster(c, a, s, 16, 16)), 16),
                           ("B. 점자 ⣿ 24×24 점 (테두리만)", lambda c, a, s: braille_segs(c, a, s, 12, 6), 12)):
        rows = side_by_side([fn(*x) for x in SAMPLES]) + label_row(labels, wcol)
        ui.banner(ru.REC, name, "↑ 정면(상자)      ↓ 로봇", rows)


def demo_layout():
    # (K, 색, 각도, 방향) — 미리보기용 예시 배치 (T3 Known 처럼 빨강 1 + 방해 3)
    return {"K1": ("red", 30, "L"), "K2": ("blue", 0, ""), "K5": ("orange", 45, ""), "K8": ("yellow", 15, "R")}


GRID = [["K1", "K2", "K3"], ["K4", "K5", "K6"], ["K7", None, "K8"]]   # 로봇에서 상자를 보는 방향 (위 = 상자 쪽)


def grid_rows(lay, bg=None, px=16):
    out = []
    for gr in GRID:
        blocks, labels = [], []
        for k in gr:
            if k and k in lay:
                c, a, s = lay[k]
                blocks.append(halfblock_segs(raster(c, a, s, px, px)))
                labels.append(f"{k} {COLOR_KO[c]} {angle_text(a, s).replace(' (꼭짓점이 로봇 쪽)', '')}")
            else:
                blocks.append([[(" " * px, None, None)] for _ in range(px // 2 - 1)] + [[((f"{k}()" if k else "").center(px), None, None)]])
                labels.append("")
        out += side_by_side(blocks, gap=6) + label_row(labels, px, gap=6) + [[("", None, None)]]
    return out[:-1]


def rec(ui):
    ui.episode = 0
    ui.banner(ru.REC, "▶ 녹화 시작 (1번째 / 64)", "episode 0 · 45초 · 끝나면 →  다시 ←  종료 Esc",
              [[(" 배치 T3K1-B2O5Y8 ", None, None)], [("4개 · 검정 선 = 로봇 쪽 면", None, None)], [("", None, None)]]
              + grid_rows(demo_layout(), WHITE))


def reset(ui):
    nxt = {"K6": ("red", 15, "L"), "K2": ("green", 30, "R"), "K3": ("blue", 0, "")}
    ui.banner(ru.RESET, "↺ 환경 초기화 — 준비되면 →", "30초 안에 준비 · 다시 녹화 ←  종료 Esc",
              [[(" 다음 판 (episode 1) — 배치 T3K6-G2B3 ", None, None)], [("3개 · 검정 선 = 로봇 쪽 면", None, None)], [("", None, None)]]
              + grid_rows(nxt, "100"))


if __name__ == "__main__":
    ui = ru.UI(["--dataset.num_episodes=64"], None)
    which = sys.argv[1:] or ["cubes", "rec", "reset"]
    for w in which:
        {"cubes": cubes, "rec": rec, "reset": reset}[w](ui)
    print()
