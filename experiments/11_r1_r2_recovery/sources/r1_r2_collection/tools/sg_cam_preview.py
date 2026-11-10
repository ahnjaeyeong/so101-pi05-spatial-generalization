#!/home/user/so101-env/bin/python
"""카메라만 미리보기 (로봇 · 리더 연결 없음, 토크 없음, 녹화 없음) — 스티커 검출 화면 확인용.

front · wrist 카메라를 d2 녹화와 같은 형식 (640×480 · MJPG · 30 fps) 으로 열어 r12 와 같은 공유 폴더 (/dev/shm) 에 쓰고
sg_viewer.py 를 띄운다. 카메라 노출 · 화이트밸런스 등 v4l2 값은 바꾸지 않는다 (형식만 정함).
lerobot-record · teleoperate · eval 등이 카메라를 쓰고 있으면 시작하지 않는다 (r12_common.robot_conflicts, 읽기만).

  ~/so101-env/bin/python sg_cam_preview.py [--scale 0.9]          # 실제 카메라 (사용자가 실행)
  ~/so101-env/bin/python sg_cam_preview.py --session practice/sg50_pilot   # + 계획 놓을 위치 표시, 영상 창 ← → 로 판 넘김
  ~/so101-env/bin/python sg_cam_preview.py --source VIDEO.mp4      # 시험: 영상 파일 (front|wrist 1280×480 review 영상 또는 손목 영상 하나)
끝내기: Ctrl+C (또는 영상 창 닫기).
"""

import argparse
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

VENV_PY = os.path.expanduser("~/so101-env/bin/python")
CAMS = {"front": "/dev/cam_front", "wrist": "/dev/cam_wrist"}


def open_cam(path):
    import cv2

    c = cv2.VideoCapture(path, cv2.CAP_V4L2)
    c.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    c.set(cv2.CAP_PROP_FPS, 30)
    if not c.isOpened():
        raise SystemExit(f"카메라를 못 열었어요: {path}")
    return c


class FileSource:
    def __init__(self, path):
        import av

        self.path = path
        self.av = av
        self._open()

    def _open(self):
        self.c = self.av.open(self.path)
        self.it = self.c.decode(video=0)

    def read(self):
        try:
            f = next(self.it).to_ndarray(format="rgb24")
        except StopIteration:
            self.c.close()
            self._open()
            f = next(self.it).to_ndarray(format="rgb24")
        if f.shape[1] == 1280:  # review 영상 = front | wrist
            return f[:, :640].copy(), f[:, 640:].copy()
        return f, f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scale", default="0.9")
    ap.add_argument("--source", help="시험용 영상 파일 (카메라 대신)")
    ap.add_argument("--seconds", type=float, default=0, help="시험용: 이 시간 뒤 끝냄 (0 = Ctrl+C 까지)")
    ap.add_argument("--no-viewer", action="store_true")
    ap.add_argument("--session", help="계획 표시 (예: practice/sg50_pilot) — 영상 창에서 ← → 로 계획 판을 넘김 (녹화 아님)")
    ap.add_argument("--episode", type=int, help="처음 보여 줄 계획 판 (기본 = 아직 안 찍은 첫 판)")
    a = ap.parse_args()
    import cv2

    if not a.source:
        conf = rc.robot_conflicts(exclude_pids=(os.getpid(),))
        conf = [c for c in conf if any(d in c["devices"] for d in CAMS.values()) or c["name"]]
        if conf:
            print("카메라 · 로봇을 쓰는 다른 프로세스가 있어요 — 미리보기를 열지 않았어요:")
            for c in conf[:6]:
                print(f"  pid {c['pid']}: {c['cmd']}")
            return 1
        miss = [p for p in CAMS.values() if not os.path.exists(p)]
        if miss:
            print(f"카메라 장치가 없어요: {', '.join(miss)}")
            return 1
    run = time.strftime("%Y%m%d_%H%M%S")
    live = rc.live_dir_for(f"campreview_{run}")
    fr = rc.LiveFrames(live, create=True)
    cfgp = os.path.join(rc.ROOT, "config", "sg50.yaml")
    ui = {"state": "CAMPREVIEW", "episode": None, "row": None, "session": "카메라 미리보기 (녹화 안 함 · 로봇 연결 없음)", "done": "-", "target": "-",
          "preview": bool(a.source)}
    plan, cfg = [], None
    if a.session:  # 계획 판을 화면에 (놓을 위치 그림 · front 빨간 원). 녹화 · 기록은 하지 않음
        cfg = rc.load_config(cfgp)
        plan = rc.read_plan(rc.session_dir(a.session))
        cur = a.episode if a.episode is not None else next((i for i, r in enumerate(plan) if r["status"] == rc.PLANNED), 0)
        done = sum(r["status"] == rc.RECORDED for r in plan)
        ui.update(session=f"{a.session} · 카메라 미리보기 (녹화 안 함) · ← → 계획 판 넘기기", done=done, target=len(plan))

    def show(i):
        ui.update(episode=i, row=rc.describe_row(cfg, plan[i]))
        rc.write_json(os.path.join(live, "ui.json"), ui)

    if plan:
        show(cur)
    rc.write_json(os.path.join(live, "ui.json"), ui)
    keys_p, keys_off = os.path.join(live, "keys.in"), 0
    viewer = None
    if not a.no_viewer and os.environ.get("DISPLAY"):
        viewer = subprocess.Popen([VENV_PY, os.path.join(HERE, "sg_viewer.py"), "--live", live, "--scale", a.scale],
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", R12_CONFIG=cfgp))
    if a.source:
        src = FileSource(a.source)
        caps = None
    else:
        caps = {k: open_cam(p) for k, p in CAMS.items()}
    stop = {"v": False}
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__("v", True))
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("v", True))
    print(f"[sg] 카메라 미리보기 {live} — 로봇 연결 없음 · 녹화 안 함. 끝내기 Ctrl+C", flush=True)
    t_end = time.time() + a.seconds if a.seconds else None
    n = 0
    t0 = time.time()
    try:
        while not stop["v"] and (t_end is None or time.time() < t_end):
            if viewer is not None and viewer.poll() is not None:
                break
            if caps is None:
                f, w = src.read()
                time.sleep(1 / 30)
            else:
                ok1, fb = caps["front"].read()
                ok2, wb = caps["wrist"].read()
                if not (ok1 and ok2):
                    time.sleep(0.05)
                    continue
                f, w = cv2.cvtColor(fb, cv2.COLOR_BGR2RGB), cv2.cvtColor(wb, cv2.COLOR_BGR2RGB)
            n += 1
            if plan and n % 5 == 0 and os.path.exists(keys_p):  # 영상 창의 ← → (sg_viewer 가 keys.in 에 씀)
                with open(keys_p, "rb") as kf:
                    kf.seek(keys_off)
                    new = kf.read()
                    keys_off += len(new)
                for ln in new.decode(errors="ignore").split():
                    if ln == b"\x1b[C".hex():
                        cur = min(cur + 1, len(plan) - 1)
                        show(cur)
                    elif ln == b"\x1b[D".hex():
                        cur = max(cur - 1, 0)
                        show(cur)
            if n % 2 == 0:  # 녹화 탭과 같이 2 장마다
                fr.put(0, f), fr.put(1, w), fr.bump()
            if n % 3 == 0:
                rc.write_json(os.path.join(live, "status.json"), {"t": time.time(), "phase": "camera_preview", "ep": None, "run_id": f"campreview_{run}",
                                                                  "loop_hz": round(n / max(time.time() - t0, 1e-6), 1), "rec_frames": 0,
                                                                  "late_ticks": 0, "stall_ticks": {}, "state": None})
    finally:
        if caps:
            for c in caps.values():
                c.release()
        if viewer is not None and viewer.poll() is None:
            viewer.terminate()
        print(f"[sg] 끝 — {n} 장 읽음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
