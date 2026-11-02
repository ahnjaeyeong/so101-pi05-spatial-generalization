#!/home/user/so101-env/bin/python
"""바탕화면 스크린샷용: xterm 안에서 실행된다 (xterm -e ...). 실제 r12_collect.py preview 를 pty 로 띄워 출력을 이 xterm 에
그대로 보여 주고, 정해 둔 키를 보내며, 정해 둔 순간에 X 화면(xwd -root)에서 xterm + 영상 창 영역을 잘라 PNG 로 저장한다.
로봇·카메라는 쓰지 않는다 (preview). 키는 자동으로 보낸다 (사람이 누르는 바이트와 같음).

  xterm -geometry 140x58+1310+40 -fa NanumGothicCoding -fs 11 -e ~/so101-env/bin/python tests/shot_session.py OUTDIR
"""

import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, HERE)
sys.path.insert(0, TOOLS)
from pty_driver import ESC, RIGHT, Driver  # noqa: E402
from r12_viewer import xwd_png  # noqa: E402

VENV = os.path.expanduser("~/so101-env/bin/python")
OUT = sys.argv[1]
LOG = open(os.path.join(OUT, "shot_session.log"), "a")
GEOM = "+0+60"


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


def win_geom(wid):
    o = subprocess.run(["xwininfo", "-id", str(wid)], capture_output=True, text=True).stdout
    g = {}
    for k, key in (("Absolute upper-left X", "x"), ("Absolute upper-left Y", "y"), ("Width", "w"), ("Height", "h")):
        for ln in o.splitlines():
            if ln.strip().startswith(k + ":"):
                g[key] = int(ln.split(":")[1])
    return g


def viewer_geom(live):
    for ln in subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout.splitlines():
        if "R1·R2" in ln or "R1\\302\\267R2" in ln or "SO-101 R1" in ln:
            wid = ln.split()[0]
            g = win_geom(wid)
            if g.get("w", 0) > 600:
                return g
    return None


def viewer_wid():
    for ln in subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout.splitlines():
        if "SO-101 R1" in ln:
            return ln.split()[0]
    return None


def snap(path, live):
    """영상 창은 영상 창 프로세스가 자기 창(winfo_id)을, 이 xterm 은 여기서 WINDOWID 를 xwd -id 로 찍어 나란히 붙인다.
    창마다 따로 찍으므로 다른 창·바탕화면은 담기지 않는다."""
    from PIL import Image
    from r12_viewer import xwd_window

    done = os.path.join(live, "snap_done.json")
    if os.path.exists(done):
        os.unlink(done)
    vpath = path[:-4] + "_viewer_only.png"
    with open(os.path.join(live, ".req"), "w") as f:
        json.dump({"path": vpath}, f)
    os.replace(os.path.join(live, ".req"), os.path.join(live, "snap_request.json"))
    end = time.time() + 10
    while time.time() < end and not os.path.exists(done):
        time.sleep(0.1)
    with open(done) as f:
        log("viewer", f.read())
    term = xwd_window(int(os.environ["WINDOWID"]))
    view = Image.open(vpath)
    gap = 8
    out = Image.new("RGB", (view.size[0] + gap + term.size[0], max(view.size[1], term.size[1])), (40, 40, 40))
    out.paste(view, (0, 0))
    out.paste(term, (view.size[0] + gap, 0))
    out.save(path)
    os.unlink(vpath)
    import numpy as np
    log("snap", path, out.size, "term mean", float(np.asarray(term).mean()))
def latest_live():
    ds = sorted(glob.glob("/dev/shm/r12_live_*_preview"), key=os.path.getmtime)
    return ds[-1] if ds else None


def session(typ, steps):
    root = os.path.join(OUT, f"preview_{typ}_{time.strftime('%H%M%S')}")
    cmd = [VENV, os.path.join(TOOLS, "r12_collect.py"), "preview", "--type", typ, "--episodes", "3", "--root", root,
           "--viewer-geometry", GEOM, "--scale", "0.85"]
    d = Driver(cmd, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), relay=True,
               cols=int(os.environ.get("COLUMNS", "140")), rows=int(os.environ.get("LINES", "58")))
    try:
        steps(d)
    except Exception as e:
        log("error", typ, repr(e))
        d.key(b"\x03")
    d.finish(60)
    return root


def r2(d):
    # R2 = 준비 단계에서 큐브 근처 국소 오차 자세 (손목 화면 주황 시작 영역), Pan 목표 없음
    d.wait(r"준비 — 녹화 안 함 · episode 0", 90)
    d.sleep(5)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI_R2.png"), latest_live())
    d.key(ESC)
    d.sleep(6)


def r1(d):
    # 4차 지시서 R1: 계획 앞 3판 = B2 · B1 · A. B 준비 화면 → 녹화 → 결과 → (B1 짧게) → A 준비 화면 → 안전 확인 화면
    d.wait(r"준비 — 녹화 안 함 · episode 0", 90)
    d.sleep(4)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI_R1B.png"), latest_live())
    d.wait_safe(90)
    d.key(RIGHT)
    d.wait(r"안전 확인: 탁자", 10)
    d.sleep(0.6)
    d.key(RIGHT)
    d.wait(r"녹화 중 — episode 0", 15)
    d.sleep(4.0)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI_Recording.png"), latest_live())
    d.key(RIGHT)
    d.wait(r"R1 복구 \(대략\)", 15)
    d.wait(r"결과 입력 — 녹화 안 함", 15)
    d.sleep(1)
    d.key(b"4")
    d.sleep(0.5)
    d.key(b"m")
    d.key("지나친 쪽에서 되돌아와 접근, 파지는 놓침".encode())
    d.key(b"\r")
    d.sleep(2.0)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI.png"), latest_live())
    d.key(RIGHT)
    d.wait(r"준비 — 녹화 안 함 · episode 1", 30)
    d.sleep(1.5)
    d.wait_safe(90)
    d.key(RIGHT)
    d.wait(r"안전 확인: 탁자", 10)
    d.sleep(0.6)
    d.key(RIGHT)
    d.wait(r"녹화 중 — episode 1", 15)
    d.sleep(2.0)
    d.key(RIGHT)
    d.wait(r"결과 입력 — 녹화 안 함", 15)
    d.sleep(0.5)
    d.key(b"1")
    d.sleep(0.5)
    d.key(RIGHT)
    d.wait(r"준비 — 녹화 안 함 · episode 2", 30)
    d.sleep(4)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI_R1A.png"), latest_live())
    d.wait_safe(90)
    d.key(RIGHT)
    d.wait(r"안전 확인: 탁자", 10)
    d.sleep(1.2)
    snap(os.path.join(OUT, "SO101_R1_R2_Collection_UI_R1.png"), latest_live())
    d.sleep(10.5)  # 안전 확인 시간(10 s) 이 지나 녹화 안 함
    d.key(ESC)
    d.wait(r"종료|Exiting", 40)
    d.sleep(5)


if __name__ == "__main__":
    which = sys.argv[2] if len(sys.argv) > 2 else "both"
    try:
        if which in ("both", "r2"):
            session("R2", r2)
        if which in ("both", "r1"):
            session("R1", r1)
        log("done")
    except Exception as e:
        log("fatal", repr(e))
    time.sleep(1)
