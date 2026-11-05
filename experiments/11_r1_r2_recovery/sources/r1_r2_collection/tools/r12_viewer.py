#!/home/user/so101-env/bin/python
"""R1/R2 수집 화면 (Tk 창) — 녹화 프로세스가 /dev/shm 에 쓰는 프레임·상태를 읽어 보여 주기만 한다.

장치(로봇·카메라)를 열지 않는다. 녹화 키(→ ← Esc 1 2 3 0 m …)는 live/keys.in 으로 수집 UI 에 넘긴다 (터미널과 같은 검사). 창 전용 키: F2 격자 · F3 검출 표시.
화면 모드 (2026-11-03): 시나리오에 visual_guide 가 있으면 기본 = 수집자 모드 (네모 그림 가이드, r12_viewer_collector.py),
  F4 = 디버그 모드 (이전 화면: 관절 · d2 참고 · 궤적) ↔ 수집자 모드. 녹화 상태 줄 · 안전 경고 띠는 두 모드 모두 항상 보임.
  ~/so101-env/bin/python r12_viewer.py --live /dev/shm/r12_live_<tag> [--scale 0.9]
공유 파일: frames.u8 (front·wrist), status.json (녹화 프로세스), ui.json (터미널 화면) → 여기서 vision.json 을 쓴다.
스냅샷: live 폴더에 snap_request.json {"path": ...} 을 두면 이 창을 xwd -id 로 찍어 PNG 로 저장 (실제 화면 내용, 다른 창 없음).
"""

import argparse
import json
import math
import os
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r12_common as rc
from r12_viewer_collector import CollectorUI  # noqa: E402
from r12_viewer_guide import GuideUI  # noqa: E402

TITLE = "SO-101 R1·R2 수집 화면"
MAP_W, MAP_H = 440, 280
C_PLAN, C_START, C_VIA, C_NOW = "#22c55e", "#f97316", "#60a5fa", "#22d3ee"
TYPE_BG = {"R1": "#6d28d9", "R2": "#0f766e", "R1C": "#9d174d"}
STATE_KO = {"START": ("시작 준비", "#6b7280"), "SETUP": ("준비 — 녹화 안 함", "#b45309"), "RESET": ("결과 입력 · 다음 판 준비 — 녹화 안 함", "#4b5563"),
            "REC": ("● 녹화 중", "#dc2626"), "SAVING": ("저장 중 — 리더 팔 그대로", "#1d4ed8"), "FINAL": ("마무리 저장", "#1d4ed8"),
            "DONE": ("녹화 종료", "#15803d"), "WAIT": ("다음 판 시작 대기", "#4b5563")}
BG, PANEL, FG, DIM = "#111827", "#1f2937", "#f3f4f6", "#9ca3af"
OK, WARN, BAD = "#22c55e", "#f59e0b", "#ef4444"
FONT_FILE = "/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf"  # 영상 위 한글 글씨 (PIL 기본 글꼴은 한글 없음)


def pil_font(size):
    from PIL import ImageFont

    try:
        return ImageFont.truetype(FONT_FILE, size)
    except OSError:
        return ImageFont.load_default()


def xwd_window(wid):
    """xwd -id <창> (그 창 하나만, 실제 X 서버 화면 내용) → PIL 이미지. 다른 창·바탕화면은 담기지 않는다.
    (GNOME 합성 화면에서는 xwd -root 가 창 내용을 검게 찍어서 창마다 찍는다.)"""
    import numpy as np
    from PIL import Image

    raw = subprocess.run(["xwd", "-id", str(wid), "-silent"], capture_output=True, check=True).stdout
    hs = struct.unpack(">I", raw[:4])[0]
    h = struct.unpack(">25I", raw[:100])
    w_, h_, byte_order, bpp, bpl, ncolors = h[4], h[5], h[7], h[11], h[12], h[19]
    off = hs + ncolors * 12
    if bpp not in (24, 32):
        raise RuntimeError(f"xwd bits_per_pixel {bpp} 미지원")
    k = bpp // 8
    a = np.frombuffer(raw[off:off + bpl * h_], np.uint8).reshape(h_, bpl)[:, :w_ * k].reshape(h_, w_, k)
    rgb = a[..., [2, 1, 0]] if byte_order == 0 else a[..., [k - 3, k - 2, k - 1]]
    return Image.fromarray(np.ascontiguousarray(rgb))


def xwd_png(path, wids, gap=8, bg=(40, 40, 40)):
    """창 여러 개를 각각 찍어 왼쪽부터 나란히 붙여 PNG 로. 반환 (전체 크기, [창마다 크기])."""
    from PIL import Image

    ims = [xwd_window(w) for w in wids]
    W = sum(i.size[0] for i in ims) + gap * (len(ims) - 1)
    H = max(i.size[1] for i in ims)
    out = Image.new("RGB", (W, H), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.size[0] + gap
    out.save(path)
    return out.size, [i.size for i in ims]


class Viewer:
    def __init__(self, live, scale):
        import tkinter as tk
        from PIL import ImageTk  # noqa: F401

        self.tk = tk
        self.live = live
        self.cfg = rc.load_config(os.environ.get("R12_CONFIG"))
        self.H = rc.front_H(self.cfg)
        self.W, self.Hh = int(640 * scale), int(480 * scale)
        self.W0, self._grow_n = self.W, 0  # 요청 크기 (줄인 뒤 다시 키울 때 상한)
        self.frames = None
        self.seq = -1
        self.imgs = (None, None)
        self.vis = {}
        self.vis_t = 0
        self.show_grid, self.show_det = True, True
        self.last_frame_t = None
        self.pf = pil_font(18)
        self.pf_big = pil_font(30)
        self.zone = rc.wrist_zone()
        self.replay_t0 = None
        self.mode = "collector"  # visual_guide 있는 시나리오의 기본 화면 (F4 = debug)
        self.layout = None
        self.step_info = ("", FG, [])
        self.refresh_times = []  # (모드, 한 번 그리기 s) — 성능 측정 (perf.json 으로 남김)

        root = self.root = tk.Tk()
        root.title(TITLE)
        root.configure(bg=BG)
        fam = "NanumGothicCoding"
        self.f_top = (fam, 15, "bold")
        self.f = (fam, 11)
        self.f_b = (fam, 11, "bold")
        self.f_s = (fam, 10)

        self.big = tk.Label(root, font=(fam, 30, "bold"), bg=BG, fg="white", anchor="w", padx=12, pady=4)
        self.big.pack(fill="x")  # 시나리오 큰 글씨 (예: R2 · PAN 정렬 불량 (왼쪽))
        self.step = tk.Label(root, font=(fam, 17, "bold"), bg=BG, fg=FG, anchor="w", padx=12, pady=2)
        self.step.pack(fill="x")  # 지금 할 일
        self.guide = GuideUI(self)  # 시각 시연 가이드 (시나리오에 guide_stages 가 있을 때만 보임)
        self.st = {}
        self.top = tk.Label(root, font=(fam, 12, "bold"), bg=BG, fg=FG, anchor="w", justify="left", padx=10, pady=3)
        self.top.pack(fill="x")
        self.banner = tk.Label(root, font=self.f_b, bg="#7f1d1d", fg="white", anchor="w", justify="left", padx=10,
                               wraplength=int(self.W * 2.4))  # 긴 안내가 창 폭을 늘려 화면이 줄어드는 것 방지
        self.banner.pack(fill="x")
        mid = self.mid = tk.Frame(root, bg=BG)
        mid.pack()
        self.cam = []
        for name in ("Front 카메라", "Wrist 카메라"):
            fr = tk.Frame(mid, bg=BG, padx=4, pady=2)
            fr.pack(side="left")
            tl = tk.Label(fr, font=self.f_b, bg=BG, fg=FG, anchor="w", text=name)
            tl.pack(fill="x")
            from PIL import Image as _I, ImageTk as _IT
            if not hasattr(self, "_blank"):  # 그림 없는 Label 의 width/height 는 글자 수 단위 → 빈 그림으로 픽셀 크기 고정
                self._blank = _IT.PhotoImage(_I.new("RGB", (self.W, self.Hh), (0, 0, 0)))
            il = tk.Label(fr, bg="black", image=self._blank, compound="center", width=self.W, height=self.Hh)
            il.pack()
            cap = tk.Label(fr, font=self.f_s, bg=BG, fg=DIM, anchor="w", justify="left")
            cap.pack(fill="x")
            self.cam.append((tl, il, cap))
        self.guide.build_ref(mid)
        bot = self.bot = tk.Frame(root, bg=BG)
        bot.pack(fill="both", expand=True, padx=4, pady=4)
        self.panels = []
        for i, title in enumerate(("시나리오 · 시작 조건", "녹화 상태 · 관절", "조작 키 · 저장 결과")):
            fr = tk.Frame(bot, bg=PANEL, padx=8, pady=6, highlightthickness=1, highlightbackground="#374151")
            fr.grid(row=0, column=i, sticky="nsew", padx=3)
            bot.columnconfigure(i, weight=1, uniform="p")
            tk.Label(fr, text=title, font=self.f_b, bg=PANEL, fg="#93c5fd", anchor="w").pack(fill="x")
            if i == 0:
                self.map = tk.Canvas(fr, width=MAP_W, height=MAP_H, bg="#0b1220", highlightthickness=0)
                self.map.pack()
            if i == 1:
                self.guide.build_plot(fr)
            t = tk.Text(fr, font=self.f_s, bg=PANEL, fg=FG, height=10 if i == 0 else 23, width=44, bd=0, highlightthickness=0, wrap="word")
            t.pack(fill="both", expand=True)
            for tag, col in (("ok", OK), ("warn", WARN), ("bad", BAD), ("dim", DIM), ("h", "#fde68a"), ("big", FG)):
                t.tag_configure(tag, foreground=col)
            t.tag_configure("big", font=self.f_b)
            t.tag_configure("pan_ok", font=(fam, 14, "bold"), foreground=OK)
            t.tag_configure("pan_warn", font=(fam, 14, "bold"), foreground=WARN)
            self.panels.append(t)
        self.coll = CollectorUI(self)  # 수집자 모드 (visual_guide 있을 때만 보임)
        self.relayout(False)
        root.bind("<Key>", self.on_key)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.after(100, self.refresh)

    # ---- 입력
    KEYMAP = {"Right": b"\x1b[C", "Left": b"\x1b[D", "Escape": b"\x1b", "Return": b"\r", "KP_Enter": b"\r", "BackSpace": b"\x7f"}

    def on_key(self, e):
        if e.keysym == "F4":  # 수집자 ↔ 디버그 (창 전용)
            self.mode = "debug" if self.mode == "collector" else "collector"
            return
        c = getattr(self, "coll", None)
        if c is not None and c.on_key(e.keysym):  # F9 관찰 그림 · F10 정렬 확인함 (수집자 모드, 녹화로 넘기지 않음)
            return
        g = getattr(self, "guide", None)
        if g is not None and g.on_key(e.keysym):  # F5/F6 단계 · F7 자동 · F8 참고 후보 (가이드 켜졌을 때, 녹화로 넘기지 않음)
            return
        if e.keysym in ("F4", "F9", "F10", "F11", "F12"):  # 창 전용 키 — 녹화로 넘기지 않음
            return
        if e.keysym == "F2":
            self.show_grid = not self.show_grid
            return
        if e.keysym == "F3":
            self.show_det = not self.show_det
            return
        data = self.KEYMAP.get(e.keysym) or (e.char.encode() if e.char and e.char.isprintable() else b"")
        if data:  # 녹화 키를 수집 UI 로 넘김 (터미널 키와 같은 검사를 거침)
            with open(os.path.join(self.live, "keys.in"), "ab") as f:
                f.write(data.hex().encode() + b"\n")

    # ---- 데이터
    def load(self):
        st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
        ui = rc.read_json(os.path.join(self.live, "ui.json"), {}) or {}
        if self.frames is None and os.path.exists(os.path.join(self.live, "frames.u8")):
            try:
                self.frames = rc.LiveFrames(self.live, create=False)
            except (OSError, ValueError):
                self.frames = None
        if self.frames is not None:
            seq, f, w = self.frames.get()
            if seq != self.seq and seq > 0:
                self.seq = seq
                self.imgs = (f, w)
                self.last_frame_t = time.time()
        self.pan_calib = float(ui.get("pan_calib") or 0.0)
        return st, ui

    def update_vision(self, ui):
        if self.imgs[0] is None or time.time() - self.vis_t < 0.2:
            return
        row = ui.get("row") or {}
        try:
            self.vis = rc.vision(self.imgs[0], self.imgs[1], self.cfg, row.get("position"))
            if row.get("position") and row.get("angle_raw") not in (None, ""):
                self.vis["angle"] = rc.measure_angle(self.imgs[0], self.cfg, row["position"], row["angle_raw"])
        except Exception as e:  # 검출 오류로 화면이 멈추면 안 됨
            self.vis = {"error": repr(e)}
        self.vis_t = time.time()
        self.vis["t"] = self.vis_t
        self.vis["seq"] = self.seq
        rc.write_json(os.path.join(self.live, "vision.json"), self.vis)

    # ---- 그리기
    def replay_frames(self, ui):
        """p 키 '이전 판 다시 보기': 녹화 프로세스가 남긴 축소 영상 (live/last_episode.npy, 10 틱마다 1장) 의 지금 장면. 없으면 None."""
        if not ui.get("replay"):
            self.replay_t0 = None
            return None
        try:
            import numpy as np

            p_ = os.path.join(self.live, "last_episode.npy")
            if getattr(self, "replay_mtime", None) != os.path.getmtime(p_):
                self.replay_arr, self.replay_mtime = np.load(p_), os.path.getmtime(p_)
                self.replay_meta = rc.read_json(os.path.join(self.live, "last_episode.json"), {}) or {}
        except (OSError, ValueError):
            return None
        if self.replay_t0 is None:
            self.replay_t0 = time.time()
        n = len(self.replay_arr)
        k = min(int((time.time() - self.replay_t0) * 3), n - 1)  # 3 장/s = 녹화 속도 (30 fps 의 10 틱마다)
        return k, n, self.replay_arr[k]

    def draw_cams(self, ui):
        from PIL import Image, ImageDraw, ImageTk

        row = ui.get("row") or {}
        rp = self.replay_frames(ui)
        if rp is not None:
            k, n, pair = rp
            meta = self.replay_meta
            for i in range(2):
                tl, il, cap = self.cam[i]
                im = Image.fromarray(pair[i]).resize((self.W, self.Hh))
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, im.size[0], 30], fill=(30, 64, 175))
                d.text((8, 4), f"이전 판 episode {meta.get('ep')} 다시 보기 · {k / 3:4.1f}s / {n / 3:.1f}s (축소 영상)", fill=(255, 255, 255), font=self.pf)
                ph = ImageTk.PhotoImage(im)
                il.configure(image=ph, text="")
                il.image = ph
                cap.configure(text=f"녹화 {meta.get('frames')} 프레임 · 평균 {meta.get('loop_hz_mean')} Hz · 늦은 틱 {meta.get('late_ticks')} · "
                                   f"카메라 반복 {meta.get('stall_ticks')}", fg=DIM)
            return
        for i, img in enumerate(self.imgs):
            tl, il, cap = self.cam[i]
            if img is None:
                il.configure(text="영상 없음 — 녹화 프로세스가 아직 카메라를 열지 않았어요", fg=FG, font=self.f, compound="center")
                continue
            im = Image.fromarray(img)
            d = ImageDraw.Draw(im)
            v = self.vis.get("front" if i == 0 else "wrist", {}) if self.show_det else {}
            if i == 0:
                if row.get("position"):
                    self.front_overlay(d, row, ui)
                if v.get("detected"):
                    cx, cy = v["px"]
                    d.rectangle([cx - 12, cy - 12, cx + 12, cy + 12], outline=(34, 197, 94), width=2)
            elif self.guide.active:  # 가이드: 참고 큐브 · 다음 단계 · 잘림 · 그리퍼 (닫기 영역은 참고만, 방향 화살표 없음)
                w, h = im.size
                if self.show_grid:
                    for k in (1, 2, 3):
                        d.line([(w * k / 4, 0), (w * k / 4, h)], fill=(70, 70, 70))
                        d.line([(0, h * k / 4), (w, h * k / 4)], fill=(70, 70, 70))
                reg = row.get("wrist_start_region")
                if reg and ui.get("state") in ("SETUP", "WAIT", "START") and self.guide.cur == 0:
                    from r12_viewer_guide import dashed_rect
                    dashed_rect(d, reg["u"][0] * w, reg["v"][0] * h, reg["u"][1] * w, reg["v"][1] * h, (249, 115, 22), 3)
                    d.text((reg["u"][0] * w + 3, reg["v"][0] * h - 24), "시작 영역 (대략)", fill=(249, 115, 22), font=self.pf)
                self.guide.wrist_overlay(d, w, h, self.vis.get("wrist", {}) if self.show_det else {}, self.st, self.zone, True)
            else:
                w, h = im.size
                if self.show_grid:
                    for k in (1, 2, 3):
                        d.line([(w * k / 4, 0), (w * k / 4, h)], fill=(70, 70, 70))
                        d.line([(0, h * k / 4), (w, h * k / 4)], fill=(70, 70, 70))
                z = self.zone
                vv = self.vis.get("wrist", {})
                ok, hint = rc.zone_status(vv, z)
                reg = row.get("wrist_start_region")
                aim = None  # 화살표가 가리킬 곳 (기본 = 닫기 영역 가운데)
                if reg and ui.get("state") in ("SETUP", "RESET", "WAIT", "START") and row.get("local_alignment_type") != "near_aligned":
                    # R2 준비: 시작(오차) 영역 — 주황 점선. 준비 단계 안내는 닫기 대신 이 영역 기준
                    rin = rc.in_region(vv, reg)
                    rx0, rx1, ry0, ry1 = reg["u"][0] * w, reg["u"][1] * w, reg["v"][0] * h, reg["v"][1] * h
                    rcol = (34, 197, 94) if rin else (249, 115, 22)
                    for a_, b_ in (((rx0, ry0), (rx1, ry0)), ((rx1, ry0), (rx1, ry1)), ((rx1, ry1), (rx0, ry1)), ((rx0, ry1), (rx0, ry0))):
                        for t in range(0, 10, 2):
                            d.line([(a_[0] + (b_[0] - a_[0]) * t / 10, a_[1] + (b_[1] - a_[1]) * t / 10),
                                    (a_[0] + (b_[0] - a_[0]) * (t + 1) / 10, a_[1] + (b_[1] - a_[1]) * (t + 1) / 10)], fill=rcol, width=4)
                    lab = "시작 영역 (" + rc.LOCAL_KO.get(row.get("local_alignment_type"), "") + ")"
                    ly = ry0 - 28 if ry0 > 30 else ry1 + 2  # 영역 위에 (닫기 영역 글씨와 안 겹치게)
                    d.rectangle([rx0, ly, rx0 + d.textlength(lab, font=self.pf) + 8, ly + 26], fill=(15, 15, 15))
                    d.text((rx0 + 4, ly + 1), lab, fill=rcol, font=self.pf)
                    aim = ((rx0 + rx1) / 2, (ry0 + ry1) / 2)
                    ok, hint = bool(rin), ("✓ 시작 영역 → 누르기" if rin else "큐브를 주황 시작 영역으로" if rin is False else "큐브 안 보임")
                if z:  # 닫기 영역 = d2 사람 시연에서 닫기 시작한 순간의 큐브 중심 (주 덩어리 p10–p90)
                    zx0, zx1, zy0, zy1 = z["u"][0] * w, z["u"][1] * w, z["v"][0] * h, z["v"][1] * h
                    zc = (34, 197, 94) if ok else (250, 250, 250)
                    for a_, b_ in (((zx0, zy0), (zx1, zy0)), ((zx1, zy0), (zx1, zy1)), ((zx1, zy1), (zx0, zy1)), ((zx0, zy1), (zx0, zy0))):
                        n = 12
                        for t in range(0, n, 2):
                            d.line([(a_[0] + (b_[0] - a_[0]) * t / n, a_[1] + (b_[1] - a_[1]) * t / n),
                                    (a_[0] + (b_[0] - a_[0]) * (t + 1) / n, a_[1] + (b_[1] - a_[1]) * (t + 1) / n)], fill=zc, width=3)
                    d.rectangle([zx0, zy0 - 26, zx0 + d.textlength("닫기 영역", font=self.pf) + 8, zy0 - 2], fill=(15, 15, 15))
                    d.text((zx0 + 4, zy0 - 25), "닫기 영역", fill=zc, font=self.pf)
                if v.get("detected"):
                    x, y, bw, bh = v["bbox"]
                    col = (34, 197, 94) if ok else (245, 158, 11)
                    d.rectangle([x, y, x + bw, y + bh], outline=col, width=3)
                    if z and not ok:  # 큐브 중심 → 영역 가운데 화살표 (화면에서 큐브가 가야 할 쪽)
                        tx, ty = aim or ((zx0 + zx1) / 2, (zy0 + zy1) / 2)
                        d.line([(v["cx"], v["cy"]), (tx, ty)], fill=(250, 204, 21), width=4)
                        import math as _m
                        ang = _m.atan2(ty - v["cy"], tx - v["cx"])
                        for sgn in (1, -1):
                            d.line([(tx, ty), (tx - 18 * _m.cos(ang + sgn * 0.45), ty - 18 * _m.sin(ang + sgn * 0.45))], fill=(250, 204, 21), width=4)
                if z and self.show_det:
                    hint = hint.replace("✓ ", "")  # 큰 글꼴에 ✓ 글자가 없음 — 초록 글씨로 구분
                    fnt = self.pf_big if d.textlength(hint, font=self.pf_big) < w - 30 else self.pf
                    tw = d.textlength(hint, font=fnt)
                    d.rectangle([w / 2 - tw / 2 - 10, h - 48, w / 2 + tw / 2 + 10, h - 6], fill=(15, 15, 15))
                    d.text((w / 2 - tw / 2, h - 46), hint, fill=(34, 197, 94) if ok else (250, 204, 21), font=fnt)
            if ui.get("preview"):
                d.rectangle([0, 0, im.size[0], 26], fill=(127, 29, 29))
                d.text((6, 3), "PREVIEW · " + ui.get("preview_frames", "기존 녹화 영상") + " · 녹화 안 함", fill=(255, 255, 255), font=self.pf)
            im = im.resize((self.W, self.Hh))
            ph = ImageTk.PhotoImage(im)
            il.configure(image=ph, text="")
            il.image = ph
            if i == 0:
                if v.get("detected"):
                    x, y = v["xy_cm"]
                    t = f"빨강 검출 · 탁자 좌표 ({x:+.1f}, {y:+.1f}) cm (front H, ±0.5 cm)"
                    if "dist_planned_cm" in v:
                        t += f" · 계획 {row.get('position')} 와 {v['dist_planned_cm']:.1f} cm"
                else:
                    t = "빨강 검출 안 됨 (로봇에 가려졌거나 화면 밖) — 위치 unknown"
            else:
                if v.get("detected"):
                    side = "왼쪽" if v["dx"] < -0.1 else "오른쪽" if v["dx"] > 0.1 else "가운데"
                    ud = "위" if v["dy"] < -0.1 else "아래" if v["dy"] > 0.1 else "가운데"
                    t = (f"큐브: 화면 {side}·{ud} (dx {v['dx']:+.2f}, dy {v['dy']:+.2f}) · 넓이 {v['area_px']} px"
                         + (" · ⚠ 화면 가장자리" if v.get("touches_edge") else ""))
                else:
                    t = "큐브 안 보임" + (" (이 시나리오는 가장자리/안 보여도 됨)" if row.get("wrist_expect") == "edge_or_absent" else " ⚠")
            age = time.time() - self.last_frame_t if self.last_frame_t else None
            cap.configure(text=t + (f"   · 화면 갱신 {age:.1f}s 전" if age is not None else ""),
                          fg=WARN if (age is not None and age > 1.0) else DIM)

    def geo(self, row, pan_now):
        """지도·front 공통: 탁자 위 점들 (cm). 반환 dict 또는 None."""
        if not row or not row.get("position") or row.get("pan_target_deg") in (None, ""):
            return None
        cfg, pos = self.cfg, row["position"]
        rK = rc.k_radius(cfg, pos)
        g = {"base": rc.base_xy(cfg), "cube": rc.known_xy(cfg, pos),
             "start": tuple(float(v) for v in row["start_xy_cm"].split(",")) if row.get("start_xy_cm") and not row.get("wrist_start_region") else None,
             "via": rc.known_xy(cfg, pos) if row.get("via") else None, "rK": rK}
        sp = rc.setup_path(cfg, row) if row.get("setup_from") else None
        if sp:  # 준비 단계 출발 쪽 (B1 = 큐브 방향, B2 = 큐브 반대쪽) 과 출발 → 멈출 곳 경로
            g["from"], g["path"] = sp["from"], sp["path"]
        # 로봇선 (지금 pan): K 기준 pan(d2 중앙값) 에서 큐브를 향하게 + 세션 보정(c 키). 보정 없이는 실제와 4–8° 다를 수 있음 (11-02 연습)
        if pan_now is not None:
            g["now"] = rc.polar_xy(cfg, rc.pan_phi(cfg, pos, pan_now - getattr(self, "pan_calib", 0.0)), rK + 6)
        return g

    def front_overlay(self, d, row, ui):
        """front 영상 위 (탁자 면, H 보정): 계획 ■ · 시작 ✕ · 경유 ○ · 정답·목표·지금 방향선."""
        st = rc.read_json(os.path.join(self.live, "status.json"), {}) or {}
        g = self.geo(row, (st.get("state") or {}).get("shoulder_pan.pos"))
        if not g:
            return
        P = lambda xy: rc.cm_to_px(self.H, xy)  # noqa: E731
        hexrgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # noqa: E731
        b = P(g["base"])
        d.line([b, P(g["cube"])], fill=hexrgb(C_PLAN), width=2)
        if g.get("from"):  # 준비 출발선 (파란 점선) + 출발 → 멈출 곳 경로 (흰 점선 화살표) — 둘 다 녹화 안 함
            fx, fy = P(g["from"])
            for t in range(0, 20, 2):
                a_ = (b[0] + (fx - b[0]) * t / 20, b[1] + (fy - b[1]) * t / 20)
                b_ = (b[0] + (fx - b[0]) * (t + 1) / 20, b[1] + (fy - b[1]) * (t + 1) / 20)
                d.line([a_, b_], fill=(15, 15, 15), width=7)
                d.line([a_, b_], fill=hexrgb(C_VIA), width=4)
            pts = [P(q) for q in g["path"]]
            for i, (a_, b_) in enumerate(zip(pts, pts[1:])):
                if i % 2 == 0:
                    d.line([a_, b_], fill=(240, 240, 240), width=3)
            import math as _m
            (ax, ay), (bx_, by_) = pts[-2], pts[-1]
            an = _m.atan2(by_ - ay, bx_ - ax)
            for sgn in (2.6, -2.6):
                d.line([bx_, by_, bx_ + 14 * _m.cos(an + sgn), by_ + 14 * _m.sin(an + sgn)], fill=(240, 240, 240), width=3)
        if g["start"]:  # 밑동 → 시작/멈출 곳 방향선 (11-02 사용자: 시작선처럼 기계에서 그 지점까지)
            d.line([b, P(g["start"])], fill=(15, 15, 15), width=7)
            d.line([b, P(g["start"])], fill=hexrgb(C_START), width=4)
        if "now" in g:
            d.line([b, P(g["now"])], fill=(15, 15, 15), width=7)
            d.line([b, P(g["now"])], fill=hexrgb(C_NOW), width=4)
        cx, cy = P(g["cube"])
        sxy = P(g["start"]) if g["start"] else None

        def tag(x, y, text, col, away):  # 어두운 바탕 글씨, away = 피할 점 반대쪽에 둠
            text = text.replace("↺", "왼").replace("↻", "오")  # 영상 위 글꼴에 회전 화살표 글자가 없음
            w_ = d.textlength(text, font=self.pf)
            right = away is None or away[0] <= x
            tx = x + 16 if right else x - 16 - w_
            tx = min(max(tx, 4), d.im.size[0] - w_ - 6)  # 영상 안에
            ty = y - 12 + (14 if away is not None and away[1] < y else -14 if away is not None else 0)
            d.rectangle([tx - 3, ty - 2, tx + w_ + 3, ty + 22], fill=(15, 15, 15))
            d.text((tx, ty), text, fill=col, font=self.pf)

        if row.get("angle_raw") not in (None, ""):  # 목표 각도로 돌린 큐브 윤곽 (흰 점선) — 이 모양에 맞춰 놓기
            cs = [P(c) for c in rc.cube_corners(self.cfg, row["position"], row["angle_raw"], half=1.6)]
            for a_, b_ in zip(cs, cs[1:] + cs[:1]):
                for t in range(0, 8, 2):
                    d.line([(a_[0] + (b_[0] - a_[0]) * t / 8, a_[1] + (b_[1] - a_[1]) * t / 8),
                            (a_[0] + (b_[0] - a_[0]) * (t + 1) / 8, a_[1] + (b_[1] - a_[1]) * (t + 1) / 8)], fill=(255, 255, 255), width=2)
        else:
            d.rectangle([cx - 11, cy - 11, cx + 11, cy + 11], outline=hexrgb(C_PLAN), width=3)
        ang = self.vis.get("angle") or {}
        tag(cx, cy, f"계획 {row['position']} {row.get('angle', '')}" + (f" · 지금 {rc._cube_angle().label(ang['meas'])} {'✓' if ang.get('ok') else '✗'}"
                                                                       if ang.get("meas") is not None else ""), hexrgb(C_PLAN), sxy)
        if g["via"]:
            d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=hexrgb(C_VIA), width=2)
        if g["start"]:
            sx, sy = P(g["start"])
            d.line([sx - 11, sy - 11, sx + 11, sy + 11], fill=hexrgb(C_START), width=4)
            d.line([sx - 11, sy + 11, sx + 11, sy - 11], fill=hexrgb(C_START), width=4)
        if g["start"]:
            if row.get("error_in_rec"):  # ✕ → 큐브 되돌아가는 화살표
                d.line([sx, sy, cx, cy], fill=(229, 231, 235), width=2)
                import math as _m
                a_ = _m.atan2(cy - sy, cx - sx)
                for s_ in (2.6, -2.6):
                    d.line([cx - 14 * _m.cos(a_), cy - 14 * _m.sin(a_), cx - 14 * _m.cos(a_) - 10 * _m.cos(a_ + s_), cy - 14 * _m.sin(a_) - 10 * _m.sin(a_ + s_)],
                           fill=(229, 231, 235), width=2)
            tag(sx, sy, row.get("x_label") or "시작(오답)", hexrgb(C_START), (cx, cy))
        if g.get("from"):
            fx, fy = P(g["from"])
            tag(fx, fy, "출발 (준비)", hexrgb(C_VIA), (cx, cy))
        if "now" in g:
            nx, ny = P(g["now"])
            tag(nx, ny, "로봇", hexrgb(C_NOW), (cx, cy))

    def draw_map(self, row, st):
        """위에서 본 지도 — 위 = 상자, 아래 = 로봇, 왼쪽 = 로봇 왼쪽 (배너 격자와 같은 방향)."""
        c = self.map
        c.delete("all")
        cfg = self.cfg
        X0, X1, Y0, Y1 = -36.0, 14.5, -11.0, 33.0  # 보이는 범위 (cm): x 로봇→상자, y 오른쪽→왼쪽
        sc = min((MAP_H - 30) / (X1 - X0), (MAP_W - 150) / (Y1 - Y0))
        ox, oy = 8, 22

        def T(xy):
            x, y = xy
            return ox + (Y1 - y) * sc, oy + (X1 - x) * sc

        c.create_text(6, 4, anchor="nw", fill=DIM, font=("NanumGothicCoding", 9),
                      text="위에서 본 탁자 · 위 = 상자 · 왼쪽 = 로봇 왼쪽")
        bx, by = cfg["_base"]["box"]["center_cm"]
        iw, ih = cfg["_base"]["box"]["inner_size_cm"]
        (a, b_), (e, f) = T((bx + iw / 2, by + ih / 2)), T((bx - iw / 2, by - ih / 2))
        c.create_rectangle(a, b_, e, f, outline="#a16207", width=2)
        c.create_text((a + e) / 2, (b_ + f) / 2, text="상자", fill="#a16207", font=("NanumGothicCoding", 10, "bold"))
        for k in cfg["positions"]:
            px, py = T(rc.known_xy(cfg, k))
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#4b5563", outline="")
            c.create_text(px, py + 10, text=k, fill="#6b7280", font=("NanumGothicCoding", 8))
        for k in (cfg.get("free_points") or {}):  # 자유 점 (탁자 표시 없음)
            px, py = T(rc.known_xy(cfg, k))
            c.create_oval(px - 3, py - 3, px + 3, py + 3, outline="#6b7280")
            c.create_text(px, py + 10, text=k, fill="#4b5563", font=("NanumGothicCoding", 8))
        base = T(rc.base_xy(cfg))
        c.create_oval(base[0] - 9, base[1] - 9, base[0] + 9, base[1] + 9, fill="#374151", outline="#9ca3af")
        c.create_text(base[0], base[1] + 16, text="로봇", fill="#9ca3af", font=("NanumGothicCoding", 9))
        pan_now = (st.get("state") or {}).get("shoulder_pan.pos")
        g = self.geo(row, pan_now)
        lx = ox + (Y1 - Y0) * sc + 14
        if not g:
            c.create_text(lx, 40, anchor="nw", fill=DIM, text="계획 줄 없음", font=("NanumGothicCoding", 10))
            return
        cube, start = T(g["cube"]), T(g["start"]) if g["start"] else None
        c.create_line(*base, *cube, fill=C_PLAN, dash=(4, 3), width=2)
        if g.get("from"):  # 준비 출발선 + 경로 (녹화 안 함)
            c.create_line(*base, *T(g["from"]), fill=C_VIA, width=2, dash=(5, 3))
            c.create_line(*[v for q in g["path"] for v in T(q)], fill="#e5e7eb", width=2, dash=(3, 3), arrow="last", smooth=True)
        if start:
            c.create_line(*base, *start, fill=C_START, width=3)
        if "now" in g:
            c.create_line(*base, *T(g["now"]), fill=C_NOW, width=3, arrow="last")
        if g["via"]:
            c.create_oval(cube[0] - 13, cube[1] - 13, cube[0] + 13, cube[1] + 13, outline=C_VIA, width=2)
        if row.get("angle_raw") not in (None, ""):
            pts = [T(c_) for c_ in rc.cube_corners(cfg, row["position"], row["angle_raw"], half=1.8)]
            c.create_polygon(*[v for p_ in pts for v in p_], fill=C_PLAN, outline="white")
            # 로봇 쪽 면 = 화면 아래쪽 변 (d2 각도 그림과 같이 검은 선)
            near = sorted(zip(pts, pts[1:] + pts[:1]), key=lambda e: -((e[0][1] + e[1][1]) / 2))[0]
            c.create_line(*near[0], *near[1], fill="black", width=3)
        else:
            c.create_rectangle(cube[0] - 7, cube[1] - 7, cube[0] + 7, cube[1] + 7, fill=C_PLAN, outline="white")
        if start:
            c.create_line(start[0] - 8, start[1] - 8, start[0] + 8, start[1] + 8, fill=C_START, width=4)
            c.create_line(start[0] - 8, start[1] + 8, start[0] + 8, start[1] - 8, fill=C_START, width=4)
        if start:
            if abs(start[0] - cube[0]) + abs(start[1] - cube[1]) > 6 and not g.get("from"):
                c.create_line(*start, *cube, fill="#e5e7eb", dash=(2, 3), arrow="last")
        f9, f10b = ("NanumGothicCoding", 9), ("NanumGothicCoding", 10, "bold")
        items = [(C_PLAN, "■ 계획 위치", f"큐브 {row['position']} · 각도 {row.get('angle', '')}")]
        if row.get("error_in_rec"):
            side = {"left": "왼쪽", "right": "오른쪽"}.get(row.get("pan_error_direction"), "")
            items.append((C_START, f"✕ {row.get('x_label')} (녹화 중)", f"Pan 오차 {side} {row.get('nominal_pan_error_deg', '')}° · 주황 선 끝"))
        elif row.get("r1_setup"):
            side = {"left": "왼쪽", "right": "오른쪽"}.get(row.get("pan_error_direction"), "")
            stg = "/".join(rc.STAGE_SHORT.get(x, x) for x in (row.get("approach_stage_expected") or "").split("|") if x) or rc.POSE_KO.get(row.get("start_pose_type"), "")
            items.append((C_START, f"✕ {row.get('x_label', '시작 Pan')}", f"{side} {row.get('nominal_pan_error_deg', '')}° → {float(row['pan_target_deg']):+.0f}° · {stg}"))
        elif g["start"]:
            items.append((C_START, "✕ 시작 위치 (오답)", f"Pan {float(row['pan_target_deg']):+.1f}° · 높이 {row.get('start_height', '')}"))
        else:  # R2: 국소 오차 — 손목 화면 기준
            items.append((C_START, "R2 국소 오차 (손목 화면)", f"{rc.LOCAL_KO.get(row.get('local_alignment_type'), '')} · 주황 시작 영역 → 초록 닫기 영역"))
        if row.get("via"):
            items.append((C_VIA, "○ 경유 위치", row["via"]))
        if g.get("from"):
            items.insert(1, (C_VIA, "┈ 출발 (준비, 녹화 안 함)", {"cube": "큐브 방향에서 → 주황으로 벗어남", "rest": "쉬는 자세 Pan 에서 → 주황으로 돌림"}
                             .get(row.get("setup_from"), "반대쪽에서 → 큐브 지나 주황에서 멈춤")))
        items.append((C_NOW, "→ 로봇 (지금 Pan)", ("" if pan_now is None else f"{pan_now:+.1f}°") +
                      f" · 보정 {getattr(self, 'pan_calib', 0.0):+.1f}° (c)"))
        y = 30
        for col, head, sub in items:
            c.create_text(lx, y, anchor="nw", fill=col, text=head, font=f10b)
            c.create_text(lx + 4, y + 15, anchor="nw", fill=FG, text=sub, font=f9, width=MAP_W - lx - 6)
            y += 44

    def put(self, t, parts):
        t.configure(state="normal")
        t.delete("1.0", "end")
        for s, tag in parts:
            t.insert("end", s, tag)
        t.configure(state="disabled")

    # ---- 화면 배치 (모드 · 가이드에 따라 루트 프레임 순서)
    def relayout(self, coll_on):
        want = ("collector",) if coll_on else ("debug", self.guide.active)
        if want == self.layout:
            return
        self.layout = want
        allw = [self.big, self.step, self.guide.strip, self.top, self.banner, self.mid, self.bot, *self.coll.widgets()]
        for w in allw:
            w.pack_forget()
        if coll_on:
            seq = [(self.coll.header, {"fill": "x"}), (self.top, {"fill": "x"}), (self.banner, {"fill": "x"}),
                   (self.coll.main, {}), (self.coll.bottom, {"fill": "x", "padx": 4, "pady": 4})]
        else:
            seq = [(self.big, {"fill": "x"}), (self.step, {"fill": "x"})] + \
                  ([(self.guide.strip, {"fill": "x", "pady": (0, 2)})] if self.guide.active else []) + \
                  [(self.top, {"fill": "x"}), (self.banner, {"fill": "x"}), (self.mid, {}),
                   (self.bot, {"fill": "both", "expand": True, "padx": 4, "pady": 4})]
        for w, kw in seq:
            w.pack(**kw)
        self.coll.shown = coll_on
        if hasattr(self, "_fit"):
            self.root.after(200, self._fit)

    def refresh(self):
        try:
            t0 = time.perf_counter()
            st, ui = self.load()
            self.st = st
            self.update_vision(ui)
            self.guide.update(st, ui)
            coll_on = self.mode == "collector" and self.coll.available(ui) and self.guide.active
            self.relayout(coll_on)
            if coll_on:
                self.coll.update(st, ui)
                self.coll.draw_cams(ui)
                self.draw_text(st, ui, panels=False)
                self.coll.draw(st, ui)
            else:
                self.draw_cams(ui)
                self.draw_text(st, ui)
                self.guide.draw(st, ui)
            self.refresh_times.append((self.layout[0], time.perf_counter() - t0))
            del self.refresh_times[:-300]
            if len(self.refresh_times) % 60 == 0:  # 성능 기록 (화면만 · 녹화 프로세스와 별개)
                import statistics as _s
                out = {"t": time.time(), "scale": round(self.W / 640, 3), "size": [self.root.winfo_width(), self.root.winfo_height()]}
                for m in ("collector", "debug"):
                    xs = sorted(x for k, x in self.refresh_times if k == m)
                    if xs:
                        out[m] = {"n": len(xs), "median_ms": round(_s.median(xs) * 1000, 1), "p95_ms": round(xs[int(0.95 * (len(xs) - 1))] * 1000, 1)}
                rc.write_json(os.path.join(self.live, "viewer_perf.json"), out)
            self.snap_check()
            self.cmd_check()
        except Exception as e:
            self.banner.configure(text=f"화면 오류: {e!r}", bg="#7f1d1d")
        self.root.after(66, self.refresh)

    def draw_text(self, st, ui, panels=True):
        state = ui.get("state", "START")
        name, col = STATE_KO.get(state, (state, "#4b5563"))
        tgt, done = ui.get("target", 0), ui.get("done", 0)
        bar = "█" * int(20 * done / tgt) + "░" * (20 - int(20 * done / tgt)) if tgt else ""
        ep = ui.get("episode")
        el = ui.get("elapsed")
        tm = f"  {el:4.0f}s / {ui.get('episode_time', 0):.0f}s" if state == "REC" and el is not None else ""
        self.top.configure(text=f"{ui.get('session', '세션 ?')}  ·  episode {ep if ep is not None else '-'}"
                                f"  ·  진행 {done}/{tgt} {bar}  ·  {name}{tm}", bg=col)
        row = ui.get("row") or {}
        self.big.configure(text=row.get("label") or ui.get("type", ""), bg=TYPE_BG.get(row.get("scenario_id", "").split("-")[0], "#374151"))
        pan_now = ((st.get("state") or {}).get("shoulder_pan.pos")) if st else None
        _, ptxt, pok = (rc.pan_guide(self.cfg, row, None if pan_now is None else pan_now - self.pan_calib)
                        if row and row.get("pan_text") and not row.get("r1_setup") else (None, "", False))  # R1 은 아래 시나리오 조건 · R2 는 Pan 목표 없음
        ang = self.vis.get("angle") or {}
        ang_bad = ang.get("meas") is not None and not ang.get("ok")
        # 11-02 사용자: 값보다 대략 위치·방법이 중요 → 각도·Pan·위치는 참고 표시, 막는 것은 안전 검사 BLOCK 뿐
        blk = rc.blocking([tuple(c) for c in (st.get("checks") or [])]) if st else []
        if state in ("SETUP", "WAIT", "START"):
            if blk:
                stp, scol = "✗ 안전 조건으로 → 막힘 — " + blk[0][2], BAD
            elif row.get("r1_setup") and ui.get("safety_ask"):
                stp, scol = "안전 확인: 탁자·상자 닿지 않음 · 케이블 · 관절 끝 밀지 않음 · 그리퍼 열림 → 맞으면 → 한 번 더", WARN
            elif row.get("r1_setup"):
                stp, scol = {"R1-FOLD-OVER": "① 준비 (녹화 안 함): 팔 접은 채 큐브 방향을 지나쳐 주황 쪽(대략)에서 멈춤 → → 두 번 · Pan 한계 근처 금지",
                             "R1-A": "① 준비 (녹화 안 함): 팔 거의 접은 채 Pan 을 주황 쪽으로 → → 두 번 (조건 ⚠ 여도 녹화됨)",
                             "R1-B1": "① 준비 (녹화 안 함): 팔을 펴며 Pan 을 주황 쪽(멀어짐)으로 움직여 멈춤 → → 두 번",
                             "R1-B2": "① 준비 (녹화 안 함): 반대쪽에서 와서 초록 선을 지나 주황 쪽에서 멈춤 → → 두 번",
                             "R1-B3": "① 준비 (녹화 안 함): 편 팔로 주황 쪽 — 손목 화면에 큐브 없게 (front 는 보임) → → 두 번",
                             }.get(row.get("scenario_id"), "① 준비 (녹화 안 함): 주황 선 쪽 오차 자세 → → 두 번"), OK
            elif row.get("error_in_rec"):
                stp, scol = "① 준비: 큐브 각도만 맞추고, 팔은 쉬는 자세 그대로 →", OK
            elif row.get("gripper_start") == "closed":
                stp, scol = "① 준비 (녹화 안 함): 그리퍼 닫은 채 큐브 앞 파지 높이 근처 (큐브에 닿지 않게) · 팔 정지 → (빈 파지 동작 금지)", OK
            elif row.get("wrist_start_region"):
                stp, scol = "① 준비 (녹화 안 함): 그리퍼 열고 큐브 근처 — 손목 화면 주황 영역에 큐브 → (대략)", OK
            else:
                stp, scol = "① 준비: 큐브 각도·주황 ✕·Pan 대략 맞으면 → (✓ 는 참고 · 키는 이 창에서도 됨)", OK
        elif state == "RESET" and row.get("r1_setup"):
            stp, scol = "③ 결과 1·2·3·4 · p 다시 보기 → = 저장 → 준비 단계에서 다음 판 오차 자세 (s/d/k/x 로 바꿈)", OK
        elif state == "RESET":
            stp, scol = "③ 결과 1·2·3 · p 다시 보기 → = 저장 → 준비 단계에서 다음 판 자세", OK
        elif state == "REC" and row.get("error_in_rec"):
            mk = ui.get("marks") or []
            stp, scol = (("② 재정렬 표시 ✓ — 큐브 가운데로 → 파지 → 상자 → 쉬는 자세", OK) if mk else
                         (f"② 녹화 중: 큐브 쪽으로 → 주황 선 ({row.get('x_label')}) 에서 Space", "#fca5a5"))
        elif state == "REC" and row.get("scenario_id") == "R1-FOLD-OVER":
            stp, scol = "② 녹화 중: 화면을 보고 Pan 을 큐브 쪽으로 되돌림 → 재정렬 → 팔 펴며 접근 · 파지 → 상자 → 쉬는 자세", "#fca5a5"
        elif state == "REC" and row.get("gripper_start") == "closed":
            stp, scol = "② 녹화 중: 먼저 그리퍼를 충분히 열기 (약 30) → 연 채 접근 · 정렬 → 한 번 닫기 → 상자 → 쉬는 자세", "#fca5a5"
        elif state == "REC" and row.get("gripper_start") == "open":
            stp, scol = "② 녹화 중: 그리퍼를 연 채 접근 깊이 · 높이 · 정렬 보정 → 손가락 사이에서 한 번 닫기 → 상자 → 쉬는 자세", "#fca5a5"
        elif state == "REC" and row.get("r1_setup"):
            stp, scol = ("② 녹화 중: " + ("Pan 방향을 바로 반대로 (초록 선 쪽)" if row.get("scenario_id") == "R1-B1" else
                                          "왔던 쪽으로 되돌아 초록 선" if row.get("scenario_id") == "R1-B2" else
                                          "큐브 쪽으로 돌려 손목 화면에서 다시 찾기" if row.get("scenario_id") == "R1-B3" else
                                          "Pan 을 초록 선(큐브)으로 되돌리기") + " → 접근·파지 → 상자 → 쉬는 자세", "#fca5a5")
        elif state == "REC" and row.get("wrist_start_region"):
            stp, scol = "② 녹화 중: 큐브가 초록 닫기 영역에 오게 고친 뒤 한 번 닫기 → 상자 → 쉬는 자세", "#fca5a5"
        elif state == "REC":
            stp, scol = "② 녹화 중: " + (row.get("pace", "") or row.get("demo", "") or "시연"), "#fca5a5"
        elif state in ("SAVING", "FINAL"):
            stp, scol = "저장 중 — 리더 팔을 그대로 두세요", "#93c5fd"
        else:
            stp, scol = name, FG
        self.step.configure(text=stp, fg=scol)
        self.step_info = (stp, scol, blk)
        msgs = []
        if ui.get("preview"):
            msgs.append("PREVIEW · 로봇·카메라 연결 없음 · dataset 쓰지 않음 · 영상·관절값 = 기존 녹화 재생 (큐브 위치는 계획과 무관)")
        age = time.time() - st.get("t", 0) if st else None
        if not st or age is None or age > 2.0:
            msgs.append("녹화 프로세스 상태가 갱신되지 않아요 (연결 중이거나 멈춤)" if state not in ("DONE",) else "녹화 종료")
        if st.get("tap_error"):
            msgs.append(f"화면 탭 오류: {st['tap_error']} (녹화는 계속)")
        gd = (st or {}).get("guard") or {}
        if gd.get("hold"):
            msgs.append(f"⛔ 명령 보호: 팔로워 고정 중 ({gd.get('hold_reason', '')}) — 리더를 팔로워 자세 쪽으로 천천히 맞추면 풀림")
        if gd.get("rec_invalid") and state in ("REC", "RESET", "SETUP"):
            msgs.append(f"⛔ 무효 시연 ({gd['rec_invalid']}) — 이 판은 자동으로 버려요")
        rv = [f for f in (ui.get("review") or []) if f[0] == "warn"]
        if rv and state in ("RESET", "SAVING"):  # 녹화 뒤 검토 표시 (자동 · 보조) — 결과 확인 화면
            msgs.append("⚠ 방금 판 검토: " + " · ".join(f[2] for f in rv) + " — 영상 확인 · 의도와 다르면 ← 로 버리기")
        self.banner.configure(text="   ".join(msgs) if msgs else "", bg="#7f1d1d" if msgs else BG)
        if not panels:  # 수집자 모드: 상태 줄 · 안전 띠까지만 (아래 칸은 수집자 화면이 그림)
            return
        self.draw_map(row, st)

        # 왼쪽: 지도 아래 — Pan 안내 + 시작 자세 검사
        p = []
        judging = state in ("SETUP", "RESET", "START", "WAIT")
        if row:
            if ptxt:
                p.append((ptxt + "\n", ("pan_ok" if pok else "pan_warn") if judging else "dim"))
            ang = self.vis.get("angle")
            if ang:
                p.append((ang["text"] + "\n", ("pan_ok" if ang.get("ok") else "pan_warn") if judging else "dim"))
            if row.get("retake_of"):
                p.append((f"재촬영 (episode {row['retake_of']} 대신)\n", "warn"))
        else:
            p.append(("계획 줄 없음\n", "dim"))
        checks = st.get("checks") or []
        blk_ = [c for c in checks if c[0] == "BLOCK"]
        p.append(("안전 조건 — ✗ 이면 → 막힘\n" if judging else "안전 조건 — 녹화·저장 중 판정 안 함\n", "h"))
        if st.get("state") is None:
            p.append(("  ✗ 관절값 없음\n", "bad"))
        elif not blk_:
            p.append(("  ✓ 통과 (Pan |95°|·한계 10° · 리더−팔로워 25° · 관절값)\n", "ok"))
        for _, _, m in blk_:
            p.append(("  ✗ " + m + "\n", "bad" if judging else "dim"))
        r1s = bool(row.get("r1_setup") and st.get("state"))
        if r1s:  # R1 시나리오 조건: 경고만 (녹화됨, 값 기록) — 안 맞으면 s/d/k/x 로 재분류
            p.append(("시나리오 조건 — 달라도 녹화됨 (◇ = 다름, s/d/k/x)\n", "h"))
            for ok_, _, t in rc.scenario_checks(self.cfg, row, st.get("state"), self.vis, self.pan_calib):
                p.append((f"  {'✓' if ok_ else '◇' if ok_ is False else '·'} {t}\n", ("ok" if ok_ else "warn" if ok_ is False else "dim") if judging else "dim"))
        if row.get("pilot_variant") and st.get("state"):  # 파일럿 12편: 시작 조건 · 실패 상태와 비슷함 (근사, 막지 않음)
            ps = rc.pilot_start_checks(self.cfg, row, st.get("state"), self.vis, self.pan_calib)
            sim = ps["similarity"]
            p.append((f"시작 조건 [{row['pilot_variant']}]" + (f" · 실패 상태와 비슷함 {sim['matched']}/{sim['total']} (근사)" if sim["total"] else "")
                      + " — 달라도 녹화됨\n", "h"))
            # R1 은 위 '시나리오 조건' 이 단계 · 손목 · front · Pan 을 이미 보여 줌 → 여기서는 복구 방향만
            for ok_, k_, t in [i for i in ps["items"] if not r1s or i[1] == "pan"]:
                p.append((f"  {'✓' if ok_ else '◇' if ok_ is False else '·'} {t}\n", ("ok" if ok_ else "warn" if ok_ is False else "dim") if judging else "dim"))
        closed_ok = row.get("gripper_start") == "closed"
        wrn = [c for c in checks if c[0] != "BLOCK" and not (closed_ok and c[1] == "gripper_closed")]
        if wrn:
            p.append(("참고 (막지 않음): " + " · ".join(m.split(" — ")[0] for _, _, m in wrn) + "\n", "dim"))
        w = self.vis.get("wrist", {})
        exp = row.get("wrist_expect", "visible")
        if self.vis and not r1s and not row.get("pilot_variant"):  # 파일럿 R2 는 위 '시작 조건' 에 손목 u/v · front 가 있음
            if w.get("detected"):
                p.append((f"  ✓ 손목 화면 큐브 검출 (dx {w['dx']:+.2f}, dy {w['dy']:+.2f})\n", "ok"))
            else:
                p.append(("  · 손목 화면 큐브 안 보임 (허용)\n" if exp == "edge_or_absent" else "  ⚠ 손목 화면 큐브 안 보임\n",
                          "dim" if exp == "edge_or_absent" else "warn"))
            fr = self.vis.get("front", {})
            if fr.get("detected") and "dist_planned_cm" in fr:
                ok = fr["dist_planned_cm"] <= 4.0  # 대략 (11-02, 2.0 에서)
                p.append((f"  {'✓' if ok else '⚠'} front 큐브 ↔ 계획 {row.get('position')} {fr['dist_planned_cm']:.1f} cm\n", "ok" if ok else "warn"))
        if not row.get("pilot_variant"):
            p.append(("  · 물리적 접근 깊이는 측정 안 함 (unknown) · FK 위치 안 씀\n", "dim"))
        self.put(self.panels[0], p)

        # 가운데: 녹화 상태 + 관절
        p = [(f"{name}\n", "big")]
        if row.get("pilot_variant"):  # 파일럿: 준비 중 · 녹화 중 · 저장 완료 · 무효 시연
            inv = ui.get("invalid_recent") or []
            rs = ("녹화 중" if state == "REC" else "저장 중" if state in ("SAVING", "FINAL") else "준비 중" if state in ("SETUP", "WAIT", "START", "RESET")
                  else name)
            p.append((f"녹화 상태: {rs}", "warn" if state == "REC" else None))
            if ui.get("last_saved_ep") is not None:
                p.append((f" · 저장 완료 ep{ui['last_saved_ep']}", "ok"))
            if inv:
                p.append((f" · 무효 시연 ep{inv[-1].get('ep')} ({inv[-1].get('reason')})", "bad"))
            p.append(("\n", None))
            if gd.get("enabled"):
                p.append((f"명령 보호 켜짐 · 리더−팔로워 {gd.get('gap') if gd.get('gap') is not None else '-'}°"
                          + (" · 팔로워 고정 중" if gd.get("hold") else "") + (" · Pan 명령 제한 중" if gd.get("pan_cap") else "") + "\n",
                          "bad" if gd.get("hold") or gd.get("pan_cap") else "dim"))
        if state == "REC":
            p.append((f"경과 {el or 0:.1f}s / {ui.get('episode_time', 0):.0f}s\n", None))
        fps = st.get("fps") or 30
        hz = st.get("loop_hz") or 0
        p += [("기록 프레임 ", "dim"), (f"{st.get('rec_frames', 0)}", "big"), (f"   (state·action 같은 수, 틱마다 1줄)\n", "dim"),
              ("제어 주기 ", "dim"), (f"{hz:5.1f} Hz", "ok" if hz >= fps * 0.95 else "warn"), (f" / 목표 {fps}\n", "dim")]
        late = st.get("late_ticks", 0)
        stall = st.get("stall_ticks") or {}
        p.append((f"늦은 틱(>{1.5 / fps * 1000:.0f} ms) {late}  ", "warn" if late else "dim"))
        p.append((f"카메라 같은 프레임 반복 front {stall.get('front', 0)} · wrist {stall.get('wrist', 0)}\n",
                  "warn" if sum(stall.values() if stall else [0]) else "dim"))
        p.append((f"이번 실행 저장 {ui.get('run_saved', 0)}편 · {ui.get('save_note', '')}\n", None))
        s, a = st.get("state") or {}, st.get("action") or {}
        if self.guide.active:
            p += self.guide.joint_rows(st)
        else:
            p.append(("\n관절      팔로워   리더    차이\n", "h"))
        for j in ([] if self.guide.active else rc.JOINTS):
            k = f"{j}.pos"
            if k in s:
                dv = a.get(k, s[k]) - s[k]
                p.append((f"{rc.SHORT[j]:6s} {s[k]:8.1f} {a.get(k, float('nan')):7.1f} {dv:+7.1f}\n", "warn" if abs(dv) > 6 and j != "gripper" else None))
        if not s:
            p.append(("  (관절값 없음)\n", "dim"))
        p.append(("단위: 관절 ° (use_degrees) · 그리퍼 0–100 (d2 와 같음)\n", "dim"))
        self.put(self.panels[1], p)

        # 오른쪽: 키 + 결과 + 시나리오 집계
        p = [("터미널이나 이 창 (클릭해서 선택) 에서 누르세요\n", "warn")]
        for k, d in ui.get("keys", []):
            p += [(f" {k:7s}", "h"), (f" {d}\n", None)]
        rv = ui.get("review") or []
        if rv and state in ("RESET", "SAVING"):
            p.append(("\n방금 판 자동 검토 (보조 · 영상으로 확인):\n", "h"))
            for lv, _, t in rv:
                p.append((f" {'⚠' if lv == 'warn' else '·'} {t}\n", "bad" if lv == "warn" else "dim"))
        lab = ui.get("label")
        if lab is not None:
            p.append(("\n방금 판 결과: ", "h"))
            p.append((lab or "아직 입력 안 함", "ok" if lab else "warn"))
            p.append(("\n", None))
        if ui.get("memo_mode"):
            p.append((f"메모 입력 중: {ui.get('memo_text', '')}▏ (Enter 끝 · Esc 취소)\n", "warn"))
        res = ui.get("results", [])
        if res:
            p.append(("\n최근 저장\n", "h"))
            for r in res[-5:]:
                p.append((f" ep{r['ep']:<3} {r['scenario']:<9} {r['label']}\n", None))
        prog = ui.get("program") or []
        cnt = ui.get("counts", {})
        if prog:  # 48편 파일럿 전체 (R1 16 + R2 32), 이번 세션 시나리오는 굵게
            tot_d, tot_t = sum(x[2] for x in prog), sum(x[3] for x in prog)
            p.append((f"\n파일럿 전체 {tot_d}/{tot_t} 편\n", "h"))
            for typ in ("R1", "R2"):
                part = [x for x in prog if x[0] == typ]
                p.append((f" {typ} {sum(x[2] for x in part)}/{sum(x[3] for x in part)}\n", "h"))
                for _, sid, d, t in part:
                    p.append((f"  {sid:<10} {d:>2}/{t:<2} " + "■" * d + "□" * max(0, t - d) + "\n",
                              "ok" if d >= t else ("big" if sid in cnt else "dim")))
        elif cnt:
            p.append(("\n시나리오별 저장/목표\n", "h"))
            for sid, (d, t) in cnt.items():
                p.append((f" {sid:<9} {d:>2}/{t:<2} " + "■" * d + "□" * max(0, t - d) + "\n", "ok" if d >= t else None))
        for m in ui.get("messages", [])[-3:]:
            p.append(("\n" + m, "warn"))
        self.put(self.panels[2], p)

    def cmd_check(self):
        """시험 · 화면 찍기용: live 폴더의 viewer_cmd.json {"keys": ["F6", "F9", ...]} = 창 키를 누른 것처럼 (창 전용 키만, 한 번 읽고 지움)."""
        p_ = os.path.join(self.live, "viewer_cmd.json")
        req = rc.read_json(p_)
        if not req:
            return
        os.unlink(p_)
        import types

        for k in req.get("keys", []):
            if k in ("F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11"):
                self.on_key(types.SimpleNamespace(keysym=k, char=""))

    def snap_check(self):
        req_p = os.path.join(self.live, "snap_request.json")
        req = rc.read_json(req_p)
        if not req:
            return
        os.unlink(req_p)
        # 찍기 전에 이 창을 맨 위로 (다른 창이 겹치면 xwd 에 그 창 내용이 담김 — 11-03 확인) → 찍은 뒤 원래대로
        try:
            self.root.attributes("-topmost", True)
            self.root.lift()
        except Exception:
            pass
        self.root.update_idletasks()
        self.root.update()
        time.sleep(0.4)
        self.root.update()
        try:
            size = xwd_png(req["path"], [self.root.winfo_id()] + list(req.get("extra_windows", [])))
            rc.write_json(os.path.join(self.live, "snap_done.json"), {"path": req["path"], "size": size, "t": time.time()})
        except Exception as e:
            rc.write_json(os.path.join(self.live, "snap_done.json"), {"error": repr(e)})
        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass

    def screen_size(self):
        """화면 크기 (R12_SCREEN=WxH 로 바꿔 작은 화면 시험)."""
        e = os.environ.get("R12_SCREEN", "")
        if "x" in e:
            w, h = e.lower().split("x")
            return int(w), int(h)
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def shrink_collector(self, f):
        """수집자 화면 전체 (영상 · 그림 · 글씨 폭) 를 f 배로 다시 만듦. 수동 선택 상태는 그대로."""
        old = self.coll
        self.W, self.Hh = int(self.W * f), int(self.Hh * f)
        for w in old.widgets():
            w.destroy()
        self.coll = CollectorUI(self)
        self.coll.manual_obs, self.coll.user_ok, self.coll.ep_key = old.manual_obs, old.user_ok, old.ep_key
        self.coll.sid, self.coll.vg = old.sid, old.vg
        self.banner.configure(wraplength=int(self.W * 2.4))
        self.layout = None
        self.relayout(True)

    def fit_window(self):
        """창 관리자가 큰 창을 최대화해도 필요한 크기로 되돌림. 수집자 화면이 화면보다 크면 영상 · 그림을 함께 줄임 (잘리지 않게)."""
        pos = getattr(self, "_pos", "")
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        sw, sh = self.screen_size()
        if self.coll.shown and (w > sw * 0.98 or h > sh * 0.93):
            self._grow_n = 0
            f = max(min(sw * 0.98 / w, sh * 0.93 / h) * 0.97, 640 * 0.35 / self.W)  # 글씨 최소 크기 때문에 조금 더 줄임 · 영상 폭 224 px 아래로는 안 줄임
            if f < 0.995:
                self.fit_log("shrink", w, h, sw, sh, f)
                self.shrink_collector(f)
                self.root.after(150, self.fit_window)
                return
        elif self.coll.shown and self.W < self.W0 * 0.97:
            # 시작 때 잠깐 큰 내용 때문에 줄었으면, 지금 크기로 맞는지 보고 요청 크기까지 다시 키움 (두 번 연속 맞을 때만)
            g = min(min(sw * 0.98 / w, sh * 0.93 / h) * 0.97, self.W0 / self.W)
            self._grow_n = self._grow_n + 1 if g > 1.05 else 0
            if self._grow_n >= 2:
                self._grow_n = 0
                self.fit_log("grow", w, h, sw, sh, g)
                self.shrink_collector(g)
                self.root.after(150, self.fit_window)
                return
        if self.root.state() == "zoomed":
            self.root.state("normal")
        try:
            self.root.wm_attributes("-zoomed", False)
        except Exception:
            pass
        self.root.geometry(f"{w}x{h}" + (pos[pos.index("+"):] if "+" in pos else ""))

    def fit_log(self, what, w, h, sw, sh, f):
        """창 크기 조정 기록 (viewer_fit.log): 원인 확인용 — 요청 폭/높이가 큰 위젯 3 개."""
        try:
            kids = []
            def walk(x, depth=0):
                for c in x.winfo_children():
                    if not c.winfo_ismapped():
                        continue
                    t = ""
                    try:
                        t = str(c.cget("text"))[:60]
                    except Exception:
                        pass
                    kids.append((c.winfo_reqwidth(), c.winfo_reqheight(), str(c), t))
                    if depth < 6:
                        walk(c, depth + 1)
            walk(self.root)
            top = sorted(kids, reverse=True)[:3] + sorted(kids, key=lambda k: -k[1])[:3]
            with open(os.path.join(self.live, "viewer_fit.log"), "a") as fh:
                fh.write(json.dumps({"t": time.time(), "what": what, "req": [w, h], "screen": [sw, sh], "f": round(f, 3),
                                     "scale": round(self.W / 640, 3), "widest_tallest": top}, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def grow_tick(self):
        """줄어든 수집자 화면이면 1.5 s 마다 다시 맞춰 봄 (두 번 연속 맞으면 요청 크기까지 키움)."""
        try:
            if self.coll.shown and self.W < self.W0 * 0.97:
                self.fit_window()
        finally:
            self.root.after(1500, self.grow_tick)

    def run(self):
        geo = rc.read_json(os.path.join(self.live, "viewer_geometry.json"))
        self._pos = geo["geometry"] if geo else ""
        self._fit = self.fit_window
        self.root.after(300, self.fit_window)
        self.root.after(1500, self.fit_window)
        self.root.after(2000, self.grow_tick)
        rc.write_json(os.path.join(self.live, "viewer_ready.json"), {"pid": os.getpid(), "t": time.time()})
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", required=True)
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    if not os.environ.get("DISPLAY"):
        print("DISPLAY 가 없어 화면 창을 열 수 없어요 (터미널 배너만으로 진행).", file=sys.stderr)
        return 3
    Viewer(a.live, a.scale).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
