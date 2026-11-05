"""r12 영상 창의 시각 시연 가이드 부분 (2026-11-03). 시나리오에 guide_stages 가 있을 때만 켜진다 (지금: 파일럿 R2-P).

화면 (r12_viewer.Viewer 위에 덧붙임 — 기존 창 · 키는 그대로):
  - 단계 띠: guide_stages 마다 칸 (이름 · d2 참고 손목 썸네일 · 참고 그리퍼 기록값). 현재 = 주황 · 다음 = 파랑 테두리 · 지난 = 흐림.
      F5 / F6 = 이전 / 다음 단계 (수동) · 칸 클릭 = 그 단계 · F7 = 자동 추정으로 (보조) · F8 = 다음 참고 시연 후보.
  - 참고 칸 (카메라 오른쪽): 고른 d2 사람 성공 시연의 현재 단계 손목 · front 영상 + 관절 · 그리퍼 기록값 + 일치 정도 (불확실성).
  - 손목 실시간 오버레이: 지금 큐브 (경계 잘림 = 빨강) · 참고 큐브 (현재 단계, 하늘색 점선) · 다음 단계 참고 큐브 중심 (분홍 ○) ·
      닫기 영역 (참고, 흰 점선 — '닫아도 됨' 판정 없음) · 지금 그리퍼 / 참고 그리퍼. 화면 → 로봇 이동 방향 화살표 없음.
  - 가운데 칸: 참고 궤적 (그리퍼 명령 · 팔로워 그리퍼, Lift — 단계 키프레임 세로선) + 관절 표 (지금 · 참고 현재 · 참고 다음).
  - 결과 단계: 녹화 뒤 검토 표시 (첫 닫힘 빈 파지 의심 · 파지 전 닫힘 횟수 · 첫 닫힘 때 큐브 잘림) — 수집 UI 가 ui.json 'review' 로 줌.
"""

import os
import time

import r12_common as rc
import r12_guide as G

BG, PANEL, FG, DIM = "#111827", "#1f2937", "#f3f4f6", "#9ca3af"
CUR, NXT, DONE_C = "#f59e0b", "#3b82f6", "#374151"
C_REF, C_NEXT, C_NOW, C_CUT = (56, 189, 248), (244, 114, 182), (250, 204, 21), (239, 68, 68)
THUMB = (120, 90)


def dashed_rect(d, x0, y0, x1, y1, col, width=2, dash=8):
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = max(abs(bx - ax), abs(by - ay), 1)
        n = max(1, int(L // dash))
        for k in range(0, n, 2):
            d.line([(ax + (bx - ax) * k / n, ay + (by - ay) * k / n), (ax + (bx - ax) * (k + 1) / n, ay + (by - ay) * (k + 1) / n)], fill=col, width=width)


class GuideUI:
    def __init__(self, v):
        self.v = v
        tk = v.tk
        self.active = False
        self.strip = tk.Frame(v.root, bg=BG)
        self.strip_head = tk.Label(self.strip, font=v.f_s, bg=BG, fg=DIM, anchor="w", justify="left", width=22, wraplength=190)
        self.strip_head.pack(side="left", padx=(8, 4))
        self.boxes = []
        self.manual, self.cand_i = None, 0
        self.hist, self.hist_key, self.last_t = [], None, None
        self.stages, self.cands, self.ref, self.cur, self.auto_why = [], [], None, 0, ""
        self.match_src = ""
        self.photo = {}
        self.ref_col = None
        self.plot = None

    # ---- 위젯 (Viewer.__init__ 에서 부름, 켜질 때까지 숨김)
    def build_ref(self, mid):
        tk = self.v.tk
        fr = self.ref_col = tk.Frame(mid, bg=BG, padx=4, pady=2)
        self.ref_title = tk.Label(fr, font=self.v.f_b, bg=BG, fg="#7dd3fc", anchor="w", text="참고 · d2 사람 성공 시연")
        self.ref_title.pack(fill="x")
        self.ref_imgs = []
        for _ in range(2):
            il = tk.Label(fr, bg="black", width=self.v.W // 2, height=self.v.Hh // 2)
            il.pack()
            self.ref_imgs.append(il)
        self.ref_cap = tk.Label(fr, font=self.v.f_s, bg=BG, fg=DIM, anchor="w", justify="left", wraplength=self.v.W // 2)
        self.ref_cap.pack(fill="x")

    def build_plot(self, parent):
        self.plot = self.v.tk.Canvas(parent, width=420, height=150, bg="#0b1220", highlightthickness=0)

    # ---- 키 · 클릭
    def on_key(self, keysym):
        if not self.active:
            return False
        n = len(self.stages)
        if keysym == "F5":
            self.manual = max(0, (self.cur if self.manual is None else self.manual) - 1)
        elif keysym == "F6":
            self.manual = min(n - 1, (self.cur if self.manual is None else self.manual) + 1)
        elif keysym == "F7":
            self.manual = None
        elif keysym == "F8":
            self.cand_i += 1
        else:
            return False
        return True

    def click(self, i):
        self.manual = i

    # ---- 상태
    def update(self, st, ui):
        row = ui.get("row") or {}
        stages = G.stages_of(self.v.cfg, row.get("scenario_id", "")) if row else []
        if not stages:
            self.set_active(False)
            return
        if not self.active or [s["key"] for s in stages] != [s["key"] for s in self.stages]:
            self.stages = stages
            self.make_boxes()
        self.set_active(True)
        self.row = row
        # 참고 시연: 계획 자리 · 각도. front 검출이 계획에서 2 cm 넘게 떨어지면 검출 자리로
        xy = tuple(float(x) for x in str(row.get("cube_xy_cm", "0,0")).split(","))
        fr = (self.v.vis or {}).get("front") or {}
        self.match_src = f"계획 {row.get('position')} {rc.angle_label(row.get('angle_raw', ''))}"
        if fr.get("detected") and fr.get("dist_planned_cm", 0) > 2.0:
            xy = tuple(fr["xy_cm"])
            self.match_src = f"front 검출 자리 ({xy[0]:+.1f}, {xy[1]:+.1f}) cm · 각도 계획 {rc.angle_label(row.get('angle_raw', ''))}"
        key = (round(xy[0], 1), round(xy[1], 1), row.get("angle_raw"))
        if ui.get("state") not in ("SETUP", "WAIT", "START") and getattr(self, "_ckey", None) is not None \
                and getattr(self, "_crow", None) == (row.get("scenario_id"), ui.get("episode")):
            key = self._ckey  # 녹화 중 · 결과 단계: 참고 시연 고정 (큐브를 옮기면 front 검출 자리가 바뀌므로)
            self.match_src = getattr(self, "_csrc", self.match_src)
        self._crow, self._csrc = (row.get("scenario_id"), ui.get("episode")), self.match_src
        if getattr(self, "_ckey", None) != key:
            self._ckey, self.cands = key, G.select_refs(xy, row.get("angle_raw"), n=5)
        self.ref = self.cands[self.cand_i % len(self.cands)] if self.cands else None
        # 이번 녹화 기록 (자동 단계 추정용 · 녹화 값과 무관)
        state = ui.get("state", "")
        hk = (ui.get("episode"), ui.get("rec_aid"))
        if state == "REC":
            if hk != self.hist_key:
                self.hist, self.hist_key, self.manual = [], hk, None
            s, a = st.get("state") or {}, st.get("action") or {}
            if st.get("t") != self.last_t and "gripper.pos" in s:
                self.last_t = st.get("t")
                self.hist.append((a.get("gripper.pos", s["gripper.pos"]), s["gripper.pos"], s.get("shoulder_pan.pos", 0), s.get("shoulder_lift.pos", 0)))
        elif state == "SETUP" and self.hist_key is not None and hk[0] != self.hist_key[0]:
            self.hist, self.hist_key, self.manual = [], None, None
        auto, why = G.auto_stage(self.stages, state, self.hist, self.v.vis)
        self.auto, self.auto_why = self.stable_auto(state, auto, why)
        self.cur = self.manual if self.manual is not None else self.auto

    STABLE_N = 6  # 녹화 중 자동 단계는 같은 추정이 6 번 (약 0.4 s) 이어질 때만 바꿈

    def stable_auto(self, state, auto, why):
        """단계가 불확실할 때는 자동 전환하지 않는다 (작업 지시 §8). 준비 · 결과 단계로 바뀌는 것 (확실) 은 바로.
        녹화 중: 새 추정이 STABLE_N 번 이어져야 바꿈. 손목 검출에 기대는 '닫힘 직전' 추정은 검출이 확실할 때만
        (검출 없음 · 경계 잘림 · 1 s 넘은 영상이면 지금 단계 유지)."""
        prev = getattr(self, "_auto", None)
        if state != "REC" or prev is None or getattr(self, "_auto_state", None) != state:
            self._auto, self._auto_state, self._pend = (auto, why), state, None
            return auto, why
        if auto == prev[0]:
            self._auto, self._pend = (auto, why), None
            return auto, why
        keys = [s["key"] for s in self.stages]
        if 0 <= auto < len(keys) and keys[auto] == "preclose":
            w = (self.v.vis or {}).get("wrist") or {}
            fresh = time.time() - float((self.v.vis or {}).get("t", 0)) < 1.0
            if not (fresh and w.get("detected") and not w.get("touches_edge")):
                return prev[0], prev[1] + " (검출 불확실 — 자동 전환 안 함)"
        pend = self._pend if (self._pend and self._pend[0] == auto) else (auto, 0)
        self._pend = (auto, pend[1] + 1)
        if self._pend[1] >= self.STABLE_N:
            self._auto, self._pend = (auto, why), None
            return auto, why
        return prev[0], prev[1]

    def set_active(self, on):
        if on == self.active:
            return
        self.active = on
        if on:  # 단계 띠 (루트 프레임) 는 Viewer.relayout 이 모드에 따라 놓음
            self.ref_col.pack(side="left")
            self.plot.pack(before=self.v.panels[1], pady=(0, 4))
        else:
            self.ref_col.pack_forget()
            self.plot.pack_forget()

    def make_boxes(self):
        tk = self.v.tk
        for b in self.boxes:
            b["frame"].destroy()
        self.boxes = []
        for i, s in enumerate(self.stages):
            f = tk.Frame(self.strip, bg=PANEL, highlightthickness=3, highlightbackground=PANEL, padx=4, pady=2)
            f.pack(side="left", padx=3)
            t = tk.Label(f, font=self.v.f_b, bg=PANEL, fg=FG, anchor="w", text=s["label"])
            t.pack(fill="x")
            im = tk.Label(f, bg="black", width=THUMB[0], height=THUMB[1])
            im.pack()
            g = tk.Label(f, font=self.v.f_s, bg=PANEL, fg=DIM, anchor="w", justify="left", wraplength=THUMB[0] + 60)
            g.pack(fill="x")
            for w in (f, t, im, g):
                w.bind("<Button-1>", lambda e, k=i: self.click(k))
            self.boxes.append({"frame": f, "title": t, "img": im, "grip": g})

    # ---- 참고 값
    def key_of(self, i):
        if 0 <= i < len(self.stages):
            return self.stages[i].get("ref") or "none"
        return "none"

    def ref_key(self, i):
        k = self.key_of(i)
        if k == "none" or not self.ref:
            return None
        return (self.ref["entry"].get("keys") or {}).get(k)

    def grip_text(self, i):
        rk = self.ref_key(i)
        s = self.stages[i]
        if rk is None:
            return s.get("gripper", "") + ("\nd2 참고 없음" if self.key_of(i) == "none" else "")
        return (f"{s.get('gripper', '')}\n참고 리더 {rk['grip_cmd']:.0f} · 팔로워 {rk['state'][5]:.0f}"
                f" · 닫기 {rk['t_rel_close_s']:+.1f}s")

    def img(self, path, size, draw_bbox=None, label=None):
        from PIL import Image, ImageDraw, ImageTk

        if not path or not os.path.exists(path):
            im = Image.new("RGB", size, (40, 40, 40))
            ImageDraw.Draw(im).text((8, size[1] // 2 - 8), "d2 참고 없음", fill=(200, 200, 200), font=self.v.pf)
        else:
            im = Image.open(path).convert("RGB").resize(size)
            if draw_bbox:
                x, y, bw, bh = draw_bbox
                sx, sy = size[0] / 640, size[1] / 480
                ImageDraw.Draw(im).rectangle([x * sx, y * sy, (x + bw) * sx, (y + bh) * sy], outline=C_REF, width=2)
            if label:
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, size[0], 22], fill=(15, 23, 42))
                d.text((4, 1), label, fill=(186, 230, 253), font=self.v.pf)
        return ImageTk.PhotoImage(im)

    # ---- 그리기
    def draw(self, st, ui):
        if not self.active:
            return
        n = len(self.stages)
        mode = "수동 선택 (F7 = 자동)" if self.manual is not None else "자동 추정 (보조)"
        self.strip_head.configure(text=f"단계 · {mode}\n자동: {self.stages[self.auto]['label'] if self.auto < n else '-'}\n({self.auto_why})\n"
                                       "F5/F6 · 클릭 = 고르기")
        for i, b in enumerate(self.boxes):
            if i == self.cur:
                bg, fg, hl, tag = CUR, "#111827", CUR, "지금 · "
            elif i == self.cur + 1:
                bg, fg, hl, tag = PANEL, FG, NXT, "다음 · "
            elif i < self.cur:
                bg, fg, hl, tag = DONE_C, DIM, DONE_C, ""
            else:
                bg, fg, hl, tag = PANEL, DIM, PANEL, ""
            b["frame"].configure(bg=bg, highlightbackground=hl)
            b["title"].configure(bg=bg, fg=fg, text=tag + self.stages[i]["label"])
            b["grip"].configure(bg=bg, fg=fg if i in (self.cur, self.cur + 1) else DIM, text=self.grip_text(i))
            k = self.key_of(i)
            pk = ("strip", i, self.ref["ep"] if self.ref else None, k)
            if self.photo.get(("strip", i)) is None or self.photo[("strip", i)][0] != pk:
                path = G.ref_image_path(self.ref["entry"], k, "wrist") if (self.ref and k != "none") else None
                self.photo[("strip", i)] = (pk, self.img(path, THUMB))
            b["img"].configure(image=self.photo[("strip", i)][1])
        # 참고 칸
        if self.ref:
            e = self.ref["entry"]
            self.ref_title.configure(text=f"참고 · d2 사람 성공 ep{e['ep']:03d} ({e['group']}) · 후보 {self.cand_i % max(1, len(self.cands)) + 1}/{len(self.cands)} (F8)")
            k = self.key_of(self.cur)
            rk = self.ref_key(self.cur)
            lab = f"{self.stages[self.cur]['label']} · {G.KEY_KO.get(k, '')}" if rk else f"{self.stages[self.cur]['label']} · d2 참고 없음"
            size = (self.v.W // 2, self.v.Hh // 2)
            pk = ("ref", e["ep"], k)
            if self.photo.get("ref") is None or self.photo["ref"][0] != pk:
                self.photo["ref"] = (pk, [self.img(G.ref_image_path(e, k, "wrist") if rk else None, size,
                                                   (rk.get("wrist") or {}).get("bbox") if rk else None, lab + " · 손목"),
                                          self.img(G.ref_image_path(e, k, "front") if rk else None, size, None, "front")])
            for il, ph in zip(self.ref_imgs, self.photo["ref"][1]):
                il.configure(image=ph)
            js = (f"참고 관절 Lift {rk['state'][1]:+.0f} · Elbow {rk['state'][2]:+.0f} · Wflex {rk['state'][3]:+.0f} · Roll {rk['state'][4]:+.0f}\n"
                  f"참고 그리퍼 리더 {rk['grip_cmd']:.0f} · 팔로워 {rk['state'][5]:.0f} · 닫기 시작 기준 {rk['t_rel_close_s']:+.2f} s") if rk else \
                "이 단계는 d2 에 해당 상황이 없어 참고를 보여 주지 않음"
            self.ref_cap.configure(text=f"일치 {self.ref['quality_text']}\n기준: {self.match_src} → d2 ({e['cube_x']:+.1f}, {e['cube_y']:+.1f}) "
                                        f"{rc.angle_label(e.get('yaw_code', ''))}\n{js}",
                                   fg="#86efac" if self.ref["quality"] == "high" else "#fde68a" if self.ref["quality"] == "medium" else "#fca5a5")
        else:
            self.ref_title.configure(text="참고 · d2 색인 없음")
            self.ref_cap.configure(text="참고 색인이 없어요: ~/so101-env/bin/python tools/r12_guide.py build", fg="#fca5a5")
        self.draw_plot(st)

    def draw_plot(self, st):
        c = self.plot
        c.delete("all")
        W, H = int(c["width"]), int(c["height"])
        tr = G.ref_traj(self.ref["ep"]) if self.ref else None
        if tr is None or not len(tr):
            c.create_text(W // 2, H // 2, text="참고 궤적 없음", fill=DIM)
            return
        t = tr[:, 0]
        t0, t1 = float(t.min()), float(t.max())
        x = lambda tt: 36 + (tt - t0) / max(t1 - t0, 1e-6) * (W - 46)  # noqa: E731
        bands = [("그리퍼 (0–50)", 4, 74, [(tr[:, 7], "#fb923c", "리더 명령"), (tr[:, 6], "#4ade80", "팔로워")], (0.0, 50.0)),
                 ("Lift °", 82, H - 14, [(tr[:, 2], "#93c5fd", "")], (float(tr[:, 2].min()) - 2, float(tr[:, 2].max()) + 2))]
        for name, y0, y1, series, (lo, hi) in bands:
            yv = lambda v, y0=y0, y1=y1, lo=lo, hi=hi: y1 - (v - lo) / max(hi - lo, 1e-6) * (y1 - y0)  # noqa: E731
            c.create_rectangle(36, y0, W - 10, y1, outline="#1f2937")
            c.create_text(4, y0 + 2, text=name, fill=DIM, anchor="nw", font=("NanumGothicCoding", 8))
            for vals, col, lab in series:
                pts = [p for tt, vv in zip(t, vals) for p in (x(tt), yv(vv))]
                c.create_line(*pts, fill=col, width=2)
            if name.startswith("그리퍼"):
                s = (st or {}).get("state") or {}
                if "gripper.pos" in s:  # 지금 팔로워 그리퍼 (시간 맞춤 없음 — 높이만 비교)
                    yy = yv(min(50.0, max(0.0, s["gripper.pos"])))
                    c.create_line(36, yy, W - 10, yy, fill=FG, dash=(3, 3))
                    c.create_text(W - 12, yy - 6, text=f"지금 {s['gripper.pos']:.0f}", fill=FG, anchor="e", font=("NanumGothicCoding", 8))
        for i, s in enumerate(self.stages):
            rk = self.ref_key(i)
            if rk is None or not (t0 <= rk["t_rel_close_s"] <= t1):
                continue
            xx = x(rk["t_rel_close_s"])
            col = CUR if i == self.cur else NXT if i == self.cur + 1 else "#4b5563"
            c.create_line(xx, 2, xx, H - 12, fill=col, width=2 if i in (self.cur, self.cur + 1) else 1, dash=() if i == self.cur else (4, 3))
            c.create_text(xx, H - 2, text=str(i + 1), fill=col, anchor="s", font=("NanumGothicCoding", 8, "bold"))
        c.create_text(W - 10, 4, text=f"닫기 시작 기준 s ({t0:+.1f} … {t1:+.1f})", fill=DIM, anchor="ne", font=("NanumGothicCoding", 8))

    # ---- 손목 오버레이 (Viewer.draw_cams 가 guide 켜졌을 때 부름)
    def wrist_overlay(self, d, w, h, vv, st, zone, show_det):
        if zone:  # 닫기 영역 = 참고 (d2 사람 닫기 시작 위치 분포) — 판정 없음
            zx0, zx1, zy0, zy1 = zone["u"][0] * w, zone["u"][1] * w, zone["v"][0] * h, zone["v"][1] * h
            dashed_rect(d, zx0, zy0, zx1, zy1, (200, 200, 200), 2, 10)
            d.text((zx0 + 3, zy1 + 2), "닫기 영역 (참고)", fill=(200, 200, 200), font=self.v.pf)
        rk, nk = self.ref_key(self.cur), self.ref_key(self.cur + 1)
        if rk and rk.get("wrist"):
            x, y, bw, bh = rk["wrist"]["bbox"]
            dashed_rect(d, x, y, x + bw, y + bh, C_REF, 3)  # 참고 큐브 (현재 단계)
            d.text((x + 2, y - 22), f"참고 {self.cur + 1}", fill=C_REF, font=self.v.pf)
        if nk and nk.get("wrist"):
            cx, cy = nk["wrist"]["u"] * w, nk["wrist"]["v"] * h
            d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=C_NEXT, width=3)
            d.text((cx + 14, cy - 10), f"다음 {self.cur + 2}", fill=C_NEXT, font=self.v.pf)
        cut = []
        if vv.get("detected"):
            x, y, bw, bh = vv["bbox"]
            cut = [nm for nm, c in (("위", y <= 2), ("아래", y + bh >= h - 2), ("왼쪽", x <= 2), ("오른쪽", x + bw >= w - 2)) if c]
            d.rectangle([x, y, x + bw, y + bh], outline=C_CUT if cut else C_NOW, width=4)
            d.text((x + 2, y + bh + 2), "지금", fill=C_CUT if cut else C_NOW, font=self.v.pf)
            for nm in cut:  # 잘린 쪽 화면 가장자리 빨간 띠
                if nm == "위":
                    d.rectangle([0, 0, w, 6], fill=C_CUT)
                elif nm == "아래":
                    d.rectangle([0, h - 6, w, h], fill=C_CUT)
                elif nm == "왼쪽":
                    d.rectangle([0, 0, 6, h], fill=C_CUT)
                else:
                    d.rectangle([w - 6, 0, w, h], fill=C_CUT)
        s = (st or {}).get("state") or {}
        g = s.get("gripper.pos")
        gmin = float(self.v.cfg["safety"].get("gripper_open_min", 15))
        rel = rc.RELATION_KO.get(rc.wrist_relation(vv), "")
        lines = []
        if cut:
            lines.append((f"[잘림] 큐브가 화면 {'·'.join(cut)} 경계에서 잘림", C_CUT))
        lines.append((f"지금 큐브: {rel} (2D 화면)" if vv.get("detected") else "지금 큐브: 안 보임", C_NOW))
        if g is not None:
            lines.append((f"그리퍼 지금 {g:.0f} ({'열림' if g >= gmin else '닫힘'})"
                          + (f" · 참고 {self.cur + 1}: {rk['state'][5]:.0f}" if rk else "")
                          + (f" → 다음 {self.cur + 2}: {nk['state'][5]:.0f}" if nk else ""), (255, 255, 255)))
        if show_det:
            y0 = h - 8 - 26 * len(lines)
            wmax = max(d.textlength(t, font=self.v.pf) for t, _ in lines)
            d.rectangle([6, y0 - 4, 14 + wmax, h - 6], fill=(15, 15, 15))
            for k, (t, col) in enumerate(lines):
                d.text((10, y0 + 26 * k), t, fill=col, font=self.v.pf)

    # ---- 가운데 칸 관절 표
    def joint_rows(self, st):
        s, a = (st or {}).get("state") or {}, (st or {}).get("action") or {}
        rk, nk = self.ref_key(self.cur), self.ref_key(self.cur + 1)
        nxt = f"참고{self.cur + 2}(다음)" if self.cur + 1 < len(self.stages) else "(마지막 단계)"
        out = [(f"\n관절      팔로워   리더  참고{self.cur + 1:<2} {nxt}\n", "h")]
        for j, jn in enumerate(rc.JOINTS):
            k = f"{jn}.pos"
            if k not in s:
                continue
            r1 = f"{rk['state'][j]:6.1f}" if rk else "     -"
            r2 = f"{nk['state'][j]:6.1f}" if nk else "     -"
            out.append((f"{rc.SHORT[jn]:6s} {s[k]:8.1f} {a.get(k, float('nan')):6.1f} {r1} {r2}\n", None))
        out.append(("참고 = d2 사람 시연 기록값 (큐브 자리 · 각도만 맞춘 다른 판 — 자세는 판마다 다름)\n", "dim"))
        return out
