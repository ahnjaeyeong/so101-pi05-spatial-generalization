#!/usr/bin/env python3
"""HIL 수집자 화면 (Collector Mode). 표시 전용 — 로봇 · 리더 · 정책에 아무 명령도 보내지 않고, 키를 터미널로 넘기지 않는다.

사용:
  python3 hil_viewer.py --tap /dev/shm/hil_<tag>         실시간 (adapter A12 tap 을 읽기만). 장치 경로가 /nonexistent 면 SIMULATION 표시
  python3 hil_viewer.py --preview [상태이름]               미리보기 (합성 영상, PREVIEW 표시). ← / → 로 상태 넘기기 (이 창 안에서만)
  python3 hil_viewer.py --snap-all <dir>                   미리보기 상태를 모두 PNG 로 (창 없음)
  python3 hil_viewer.py --tap <dir> --headless --snap-dir <dir> [--seconds N]
                                                            창 없이 tap 을 읽고 그리기 (시험 · 성능 측정 · 상태가 바뀔 때 PNG)

키: 실시간 모드에서 이 창은 키를 받지 않는다 (키 바인딩 없음). 이 창에 포커스가 오면 '터미널을 클릭하세요' 띠를 그린다.
창이 닫히거나 이 프로그램이 죽어도 제어 프로그램은 영향을 받지 않는다 (별도 프로세스, tap 은 쓰기만).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hil_ui_render as R  # noqa: E402
import hil_ui_state as U  # noqa: E402


class TapReader:
    def __init__(self, d):
        self.d = Path(d)
        self.raw = None
        self.frames = {"wrist": None, "front": None}
        self.mt = {}

    def poll(self):
        p = self.d / "state.json"
        try:
            self.raw = json.loads(p.read_text())
        except Exception:
            pass  # 없거나 쓰는 중 → 이전 값 유지 (오래되면 derive 가 UNKNOWN)
        for cam in ("wrist", "front"):
            f = self.d / f"{cam}.npy"
            try:
                m = f.stat().st_mtime_ns
                if self.mt.get(cam) != m:
                    self.frames[cam] = np.load(f)
                    self.mt[cam] = m
            except Exception:
                pass
        return self.raw, self.frames


def mode_of(raw):
    if raw and raw.get("sim"):
        return "SIMULATION"
    return "LIVE"


def frame_live(raw, now, reader, focus_warn=False):
    raw, frames = reader.poll()
    ui = U.derive(raw, time.perf_counter() if raw is None else now(raw))
    age = None if not raw else time.perf_counter() - raw["t"]
    label = time.strftime("%H:%M:%S") + (f"  ·  상태 갱신 {age:.2f} s 전" if age is not None else "  ·  상태 없음")
    return R.render(ui, raw, frames, mode_of(raw), focus_warn=focus_warn, now_label=label), ui


def _now(raw):
    # tap 의 t 는 adapter 프로세스의 perf_counter (같은 기계에서 같은 시계: CLOCK_MONOTONIC)
    return time.perf_counter()


def render_preview(name):
    import hil_ui_preview as P

    now = time.perf_counter()
    raw, scene = P.raw_for(name, now)
    ui = U.derive(raw, now)
    frames = P.frames_for(scene, ui["code"])
    return R.render(ui, raw, frames, "PREVIEW", now_label=f"PREVIEW {name}  ·  합성 영상 · 가짜 상태값 · 로봇 명령 없음"), ui


def snap_all(out):
    import hil_ui_preview as P

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, _, _ in P.STATES:
        im, ui = render_preview(name)
        # 문서용: 128 색으로 줄여 저장 (UI 그림은 색이 적어 차이 거의 없음, 파일 ~1/3)
        im.convert("RGB").quantize(colors=128, dither=0).save(out / f"preview_{name}.png", optimize=True)
        rows.append((name, ui["code"], ui["title"]))
        print(f"{name}: {ui['code']} · {ui['title']}")
    return rows


def headless(tap, snap_dir, seconds, hz):
    reader = TapReader(tap)
    snap_dir = Path(snap_dir) if snap_dir else None
    if snap_dir:
        snap_dir.mkdir(parents=True, exist_ok=True)
    t_end = time.time() + seconds
    last_code, times, seen, log = None, [], {}, []
    while time.time() < t_end:
        t0 = time.perf_counter()
        im, ui = frame_live(None, _now, reader)
        dt = time.perf_counter() - t0
        times.append(dt)
        code = ui["code"] + (("_" + ui["type"]) if ui.get("type") and ui["code"] == "CORRECTING" else "")
        if code != last_code:
            log.append({"t": time.time(), "code": code})
            if snap_dir is not None and code not in seen:
                seen[code] = {"n": len(seen) + 1, "t": time.time(), "stable": False}
                im.save(snap_dir / f"live_{seen[code]['n']:02d}_{code}.png", optimize=True)
            last_code = code
        elif snap_dir is not None and code in seen and not seen[code]["stable"] and time.time() - log[-1]["t"] >= 1.0:
            # 같은 상태가 1 s 이어진 화면도 한 장 (첫 순간과 안정된 순간이 다를 수 있음 — 예: 오류 감지 직후 vs 처리 뒤)
            seen[code]["stable"] = True
            im.save(snap_dir / f"live_{seen[code]['n']:02d}_{code}_stable.png", optimize=True)
        if reader.raw and reader.raw.get("session") == "ended":
            break
        time.sleep(max(0.0, 1.0 / hz - dt))
    a = np.array(times) * 1000 if times else np.zeros(1)
    stats = {"frames": len(times), "render_mean_ms": round(float(a.mean()), 2), "render_p99_ms": round(float(np.percentile(a, 99)), 2),
             "render_max_ms": round(float(a.max()), 2), "codes": [x["code"] for x in log]}
    if snap_dir is not None:
        (snap_dir / "viewer_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))
    print(json.dumps(stats, ensure_ascii=False))


def gui(tap=None, preview=None, hz=10.0, smoke=0.0):
    """smoke > 0: 창을 띄우지 않고 (withdraw) smoke 초 동안 갱신만 한 뒤 바인딩 목록을 출력하고 끝 (시험용)."""
    import tkinter as tk

    from PIL import ImageTk

    import hil_ui_preview as P

    root = tk.Tk()
    root.title("HIL 수집자 화면 — " + ("PREVIEW" if preview else "실시간 (표시 전용)"))
    root.configure(bg="#111827")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    scale = min(1.0, (sw * 0.98) / R.W, (sh * 0.92) / R.H)
    size = (int(R.W * scale), int(R.H * scale))
    lab = tk.Label(root, bg="#111827", takefocus=0)
    lab.pack()
    state = {"focus": False, "i": 0, "photo": None}
    names = [n for n, _, _ in P.STATES]
    if preview:
        state["i"] = names.index(preview) if preview in names else 0

        def step(k):
            state["i"] = (state["i"] + k) % len(names)

        # 미리보기 전용 (로봇과 무관): 상태 넘기기
        root.bind("<Right>", lambda e: step(1))
        root.bind("<Left>", lambda e: step(-1))
    else:
        # 실시간: 키 바인딩 없음. 포커스만 감지해 경고 띠를 그린다.
        root.bind("<FocusIn>", lambda e: state.__setitem__("focus", True))
        root.bind("<FocusOut>", lambda e: state.__setitem__("focus", False))
    reader = TapReader(tap) if tap else None

    def tick():
        try:
            if preview:
                im, _ = render_preview(names[state["i"]])
            else:
                im, _ = frame_live(None, _now, reader, focus_warn=state["focus"])
            if scale < 1.0:
                im = im.resize(size)
            state["photo"] = ImageTk.PhotoImage(im)
            lab.configure(image=state["photo"])
        except Exception as e:  # 그리기 오류는 창 안에서만
            print("viewer render error:", e, file=sys.stderr)
        root.after(int(1000 / hz), tick)

    tick()
    if smoke:
        root.withdraw()
        root.after(int(smoke * 1000), root.quit)
        root.mainloop()
        print(json.dumps({"bindings": sorted(root.bind()), "mode": "preview" if preview else "live", "photo": state["photo"] is not None}))
        root.destroy()
        return
    root.mainloop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tap")
    ap.add_argument("--preview", nargs="?", const="01_policy_wait")
    ap.add_argument("--snap-all")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--snap-dir")
    ap.add_argument("--seconds", type=float, default=600)
    ap.add_argument("--hz", type=float, default=10.0)
    ap.add_argument("--smoke", type=float, default=0.0)
    a = ap.parse_args()
    if a.snap_all:
        snap_all(a.snap_all)
    elif a.headless:
        headless(a.tap, a.snap_dir, a.seconds, a.hz)
    elif a.preview or a.tap:
        gui(tap=a.tap, preview=a.preview, hz=a.hz, smoke=a.smoke)
    else:
        ap.error("--tap 또는 --preview 또는 --snap-all")


if __name__ == "__main__":
    main()
