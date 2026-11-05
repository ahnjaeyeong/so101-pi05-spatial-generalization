"""r12 영상 창 — 수집자 모드 (Collector Mode, 2026-11-03). 시나리오에 visual_guide 가 있을 때 기본 화면 (지금: 파일럿 R2-P).

화면 (위 → 아래):
  머리: 큰 제목 (예: 'R2-P | 아직 큐브를 잡을 위치가 아닙니다') · 짧은 설명 · 작은 보조 정보 (유형 · 계획 큐브 자리 · 계획 각도 · episode — 계획과 측정을 따로 적음)
  (기존) 녹화 상태 줄 · 안전 경고 띠 — 두 모드 모두 항상 보임
  가운데 3 칸:
    왼쪽  = 시연 순서 네모 그림 (① 시작 → ② 맞추기 → ③ 확인 → ④ 한 번 닫기; 지금 = 주황 · 다음 = 파랑). 클릭 = 그 단계 (수동)
    가운데 = 실시간 Wrist 영상 (가장 큼, 최소 표시: 단계 · 그리퍼 · 큐브 관찰) + 아래 Front 영상 (보조) · 그리퍼 닫힘 안내 칸
    오른쪽 = '아직 닫지 마세요' 실패 그림 3 (앞쪽에 있음 · 옆으로 벗어남 · 화면 끝에 걸림) + 목표 (참고) 그림. 지금 화면과 비슷한 그림을 강조.
            클릭 = 수동 선택 (자동보다 우선)
  아래 띠: 지금 · 다음 · 이후 할 일 (크게) · 하지 말 것 · 녹화 시간 · 결과 입력 상태 · 핵심 키

창 전용 키 (녹화로 넘기지 않음): F4 수집자/디버그 · F5/F6 단계 · F7 자동 단계 · F9 관찰 그림 바꾸기 (자동 → 앞쪽 → 옆 → 화면 끝 → 손가락 사이 → 자동)
  · F10 '정렬 확인함' 표시 켜기/끄기 (자동 판정 아님 — 사람 확인 표시).
그림은 개념도다: 화면 속 위치 관계만 보이고 로봇 관절 이동 방향을 지시하지 않는다. UI 는 그리퍼를 열거나 닫지 않는다.
"""

import json
import os
import time

import r12_common as rc
import r12_schematic as SC

BG, PANEL, FG, DIM = "#111827", "#1f2937", "#f3f4f6", "#9ca3af"
CUR, NXT, DONE_C = "#f59e0b", "#3b82f6", "#374151"
RED, GREEN, AMBER, BLUE = "#ef4444", "#22c55e", "#f59e0b", "#3b82f6"
CARD_KEYS = ("start", "approach", "preclose", "close")
OBS_CYCLE = (None, "ahead", "side", "edge", "in_zone")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def visual_guide(cfg, sid):
    return (cfg["scenarios"].get(sid) or {}).get("visual_guide") if sid else None


class CollectorUI:
    def __init__(self, v):
        self.v = v
        self.vg = None
        self.sid = None
        self.shown = False
        self.manual_obs = None     # 수동 관찰 그림 (자동보다 우선) — None = 자동
        self.user_ok = False       # F10 '정렬 확인함' (사람 표시)
        self.obs = (None, False, "")
        self.close = ("U", "", "")
        self.ep_key = None
        self.cache = {}
        self.timing = []           # 그리기 시간 (s) — 성능 측정용
        self.s = v.W / 640.0
        self.build()

    # ---------------------------------------------------------------- 위젯
    def build(self):
        tk, v = self.v.tk, self.v
        fam = "NanumGothicCoding"
        s = self.s
        fz = lambda n: max(8, int(round(n * min(1.0, s / 0.8))))  # 0.8 배 이상은 그대로, 더 작은 창은 글씨도 줄임  # noqa: E731
        self.f_title = (fam, fz(26), "bold")
        self.f_sub = (fam, fz(16), "bold")
        self.f_info = (fam, fz(11))
        self.f_card = (fam, fz(13), "bold")
        self.f_txt = (fam, fz(11))
        self.f_now = (fam, fz(19), "bold")
        self.f_mid = (fam, fz(14), "bold")
        root = v.root
        # 머리
        self.header = tk.Frame(root, bg=BG)
        self.title = tk.Label(self.header, font=self.f_title, bg="#0f766e", fg="white", anchor="w", padx=12, pady=2)
        self.title.pack(fill="x")
        self.sub = tk.Label(self.header, font=self.f_sub, bg=BG, fg="#fde68a", anchor="w", padx=12)
        self.sub.pack(fill="x")
        self.info = tk.Label(self.header, font=self.f_info, bg=BG, fg=DIM, anchor="w", padx=12)
        self.info.pack(fill="x")
        # 1 줄: 3 칸 (같은 크기) — ① 배치/교정 방법 · ② 손목 실시간 · ③ 목표 손목 그림 (실시간과 같은 좌표)
        self.main = tk.Frame(root, bg=BG)
        W, H = self.v.W, self.v.Hh
        self.row1 = tk.Frame(self.main, bg=BG)
        self.row1.pack()
        self.p1 = tk.Frame(self.row1, bg=PANEL, padx=6, pady=4, highlightthickness=2, highlightbackground="#374151", width=W + 12, height=H + 30)
        self.p1.pack_propagate(False)
        self.p1.pack(side="left", padx=4, anchor="n")
        self.p1_title = tk.Label(self.p1, font=self.f_card, bg=PANEL, fg=CUR, anchor="w")
        self.p1_title.pack(fill="x")
        self.p1_img = tk.Label(self.p1, bg=PANEL)
        self.p1_img.pack()
        self.p1_txt = tk.Label(self.p1, font=self.f_mid, bg=PANEL, fg=FG, anchor="nw", justify="left", wraplength=W - 4)
        self.p1_txt.pack(fill="both", expand=True, pady=(4, 0))
        pw = tk.Frame(self.row1, bg=BG)
        pw.pack(side="left", padx=4, anchor="n")
        self.wt = tk.Label(pw, font=self.f_card, bg=BG, fg=FG, anchor="w", text="② 손목 카메라 (실시간)")
        self.wt.pack(fill="x")
        self.wimg = tk.Label(pw, bg="black")
        self.wimg.pack()
        p3 = tk.Frame(self.row1, bg=BG)
        p3.pack(side="left", padx=4, anchor="n")
        self.p3_title = tk.Label(p3, font=self.f_card, bg=BG, fg=GREEN, anchor="w")
        self.p3_title.pack(fill="x")
        self.p3_img = tk.Label(p3, bg="black")
        self.p3_img.pack()
        self.p3_cap = tk.Label(p3, font=self.f_txt, bg=BG, fg=FG, anchor="w", justify="left", wraplength=W)
        self.p3_cap.pack(fill="x")
        # 2 줄: 단계 그림 (작게) · Front · 닫기 안내 · 실패/목표 그림 (작게)
        self.row2 = tk.Frame(self.main, bg=BG)
        self.row2.pack(fill="x", pady=(6, 0))
        self.dw, self.dh = int(150 * s), int(112 * s)      # 단계 그림
        self.fw, self.fh = int(128 * s), int(96 * s)       # 실패 · 목표 그림
        self.compact = s < 0.6  # 작은 화면: 단계 띠 · 실패 그림 띠 · 부가 글 숨김 (1 줄 3 칸 · front · 닫기 안내 · 지금/다음 은 그대로)
        self.left = tk.Frame(self.row2, bg=BG)
        if not self.compact:
            self.left.pack(side="left", anchor="n", padx=4)
        self.lhead = tk.Label(self.left, font=self.f_txt, bg=BG, fg=DIM, anchor="w", justify="left", wraplength=4 * (self.dw + 14),
                              text="시연 순서 · 개념도 (손목 화면처럼) · 파란 화살표 = 화면 속 위치 변화 (로봇 이동 방향 아님)")
        if s >= 0.6:  # 작은 창에서는 그림 · 제목만
            self.lhead.pack(fill="x")
        crow = tk.Frame(self.left, bg=BG)
        crow.pack(anchor="w")
        self.cards = []
        for i, k in enumerate(CARD_KEYS):
            f = tk.Frame(crow, bg=PANEL, highlightthickness=3, highlightbackground=PANEL, padx=3, pady=2)
            f.pack(side="left", padx=2, anchor="n")
            t = tk.Label(f, font=self.v.f_b, bg=PANEL, fg=FG, anchor="w", justify="left", wraplength=self.dw)
            t.pack(fill="x")
            row = tk.Frame(f, bg=PANEL)
            row.pack()
            im = tk.Label(row, bg="black")
            im.pack()
            tx = tk.Label(row, font=self.f_txt, bg=PANEL)  # (카드 설명은 ① 칸에 크게 — 여기서는 안 씀)
            for w in (f, t, row, im):
                w.bind("<Button-1>", lambda e, i=i: self.click_stage(i))
            self.cards.append({"frame": f, "title": t, "row": row, "img": im, "text": tx, "key": k})
        self.done_line = tk.Label(self.left, font=self.f_card, bg=BG, fg=DIM, anchor="w", padx=4)
        self.done_line.pack(fill="x", pady=(2, 0))
        ff = tk.Frame(self.row2, bg=BG)
        ff.pack(side="left", anchor="n", padx=4)
        tk.Label(ff, font=self.v.f_s, bg=BG, fg=DIM, anchor="w", text="Front (보조 · 전체 위치)").pack(fill="x")
        self.fimg = tk.Label(ff, bg="black")
        self.fimg.pack()
        self.cbox = tk.Frame(self.row2, bg=PANEL, highlightthickness=3, highlightbackground=PANEL, padx=8, pady=4, width=int(280 * s))
        self.cbox.pack(side="left", fill="y", padx=4, anchor="n")
        tk.Label(self.cbox, font=self.v.f_s, bg=PANEL, fg=DIM, anchor="w", text="그리퍼 닫기 안내 (클릭 · F10 = 확인함)").pack(fill="x")
        self.c_big = tk.Label(self.cbox, font=self.f_mid, bg=PANEL, fg=FG, anchor="w", justify="left", wraplength=int(270 * s))
        self.c_big.pack(fill="x")
        self.c_why = tk.Label(self.cbox, font=self.f_txt, bg=PANEL, fg=FG, anchor="w", justify="left", wraplength=int(270 * s))
        self.c_why.pack(fill="x")
        gr = tk.Frame(self.cbox, bg=PANEL)
        gr.pack(fill="x", pady=(4, 0))
        self.g_img = tk.Label(gr, bg=PANEL)
        self.g_img.pack(side="left")
        self.g_txt = tk.Label(gr, font=self.f_card, bg=PANEL, fg=FG, anchor="w", justify="left", padx=6)
        self.g_txt.pack(side="left")
        self.c_obs = tk.Label(self.cbox, font=self.f_txt, bg=PANEL, fg=DIM, anchor="w", justify="left", wraplength=int(270 * s))
        if s >= 0.6:
            self.c_obs.pack(fill="x", pady=(4, 0))
        for w in (self.cbox, self.c_big, self.c_why):
            w.bind("<Button-1>", lambda e: self.toggle_ok())
        self.right = tk.Frame(self.row2, bg=BG)
        if not self.compact:
            self.right.pack(side="left", anchor="n", padx=4)
        self.rhead = tk.Label(self.right, font=self.v.f_b, bg=BG, fg=RED, anchor="w", text="✗ 이러면 아직 닫지 마세요 · ✓ 목표 (클릭 = 지금 화면 고르기)")
        self.rhead.pack(fill="x")
        frow = tk.Frame(self.right, bg=BG)
        frow.pack(anchor="w")
        self.thead = self.rhead
        self.fcards = []
        for i in range(4):
            f = tk.Frame(frow, bg=PANEL, highlightthickness=3, highlightbackground=RED if i < 3 else GREEN, padx=3, pady=2)
            f.pack(side="left", padx=2, anchor="n")
            nm = tk.Label(f, font=self.v.f_b, bg=PANEL, fg=FG, anchor="w")
            nm.pack(fill="x")
            im = tk.Label(f, bg="black")
            im.pack()
            tx = tk.Label(f, font=self.v.f_s, bg=PANEL, fg=DIM, anchor="nw", justify="left", wraplength=self.fw)
            tag = tk.Label(f, font=self.v.f_s, bg=PANEL, fg=AMBER, anchor="w", justify="left", wraplength=self.fw)
            tag.pack(fill="x")
            for w in (f, im, nm, tag):
                w.bind("<Button-1>", lambda e, i=i: self.click_obs(i))
            self.fcards.append({"frame": f, "img": im, "name": nm, "text": tx, "tag": tag})
        # 아래 띠
        self.bottom = tk.Frame(root, bg=PANEL, padx=10, pady=6, highlightthickness=1, highlightbackground="#374151")
        for c in range(3):
            self.bottom.columnconfigure(c, weight=(3, 2, 2)[c], uniform="b")
        b0 = tk.Frame(self.bottom, bg=PANEL)
        b0.grid(row=0, column=0, sticky="nsew")
        self.now = tk.Label(b0, font=self.f_now, bg=PANEL, fg=CUR, anchor="w", justify="left", wraplength=int(690 * s))
        self.now.pack(fill="x")
        self.nxt = tk.Label(b0, font=self.f_mid, bg=PANEL, fg="#93c5fd", anchor="w", justify="left", wraplength=int(690 * s))
        self.nxt.pack(fill="x")
        self.later = tk.Label(b0, font=self.f_txt, bg=PANEL, fg=DIM, anchor="w", justify="left", wraplength=int(690 * s))
        if not self.compact:
            self.later.pack(fill="x")
        b1 = tk.Frame(self.bottom, bg=PANEL)
        b1.grid(row=0, column=1, sticky="nsew", padx=8)
        self.dont = tk.Label(b1, font=self.f_mid, bg=PANEL, fg=RED, anchor="w", justify="left", wraplength=int(450 * s))
        self.dont.pack(fill="x")
        self.stage_src = tk.Label(b1, font=self.f_txt, bg=PANEL, fg=DIM, anchor="w", justify="left", wraplength=int(450 * s))
        if not self.compact:
            self.stage_src.pack(fill="x", pady=(4, 0))
        b2 = tk.Frame(self.bottom, bg=PANEL)
        b2.grid(row=0, column=2, sticky="nsew")
        self.rec = tk.Label(b2, font=self.f_mid, bg=PANEL, fg=FG, anchor="w", justify="left")
        self.rec.pack(fill="x")
        self.result = tk.Label(b2, font=self.f_txt, bg=PANEL, fg=FG, anchor="w", justify="left", wraplength=int(480 * s))
        self.result.pack(fill="x")
        self.keys = tk.Label(b2, font=self.v.f_s, bg=PANEL, fg=DIM, anchor="w", justify="left", wraplength=int(480 * s))
        if not self.compact:
            self.keys.pack(fill="x", pady=(2, 0))

    def widgets(self):
        """루트에 바로 붙는 프레임 (Viewer.relayout 이 순서대로 놓음)."""
        return self.header, self.main, self.bottom

    # ---------------------------------------------------------------- 입력
    def on_key(self, keysym):
        if not self.shown:
            return False
        if keysym == "F9":
            i = OBS_CYCLE.index(self.manual_obs) if self.manual_obs in OBS_CYCLE else 0
            self.manual_obs = OBS_CYCLE[(i + 1) % len(OBS_CYCLE)]
            if self.manual_obs in ("ahead", "side", "edge"):
                self.user_ok = False
            return True
        if keysym == "F10":
            self.toggle_ok()
            return True
        if keysym == "F11":
            self.open_ref_video()
            return True
        return False

    def open_ref_video(self):
        """설정 visual_guide.ref_video (수집 폴더 기준 경로, #앵커 가능) 를 기본 프로그램으로 연다. 녹화와 무관 (창 전용)."""
        ref = (self.vg or {}).get("ref_video")
        if not ref:
            self.ref_msg = "이 시나리오에는 실제 실패 영상이 없어요"
            return
        path, _, anchor = ref.partition("#")
        full = os.path.join(rc.ROOT, path)
        if not os.path.exists(full):
            self.ref_msg = f"영상 폴더가 없어요: {full}"
            return
        url = "file://" + full + (f"#{anchor}" if anchor else "")
        self.ref_msg = f"실제 실패 영상 열기: {url}"
        self.ref_opened = url
        if os.environ.get("R12_NO_OPEN"):  # 시험: 열지 않고 기록만
            return
        import subprocess

        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as e:
            self.ref_msg = f"영상 열기 실패: {e!r}"

    def toggle_ok(self):
        self.user_ok = not self.user_ok

    def click_stage(self, i):
        self.v.guide.click(i)

    def click_obs(self, i):
        keys = [f.get("key") for f in (self.vg or {}).get("failures", [])] + ["in_zone"]
        if i < len(keys):
            k = keys[i]
            self.manual_obs = None if self.manual_obs == k else k   # 같은 그림 다시 클릭 = 자동으로
            if self.manual_obs in ("ahead", "side", "edge"):
                self.user_ok = False

    # ---------------------------------------------------------------- 상태
    def available(self, ui):
        row = (ui or {}).get("row") or {}
        return bool(visual_guide(self.v.cfg, row.get("scenario_id")))

    def update(self, st, ui):
        row = ui.get("row") or {}
        sid = row.get("scenario_id")
        if sid != self.sid:
            self.sid, self.vg = sid, visual_guide(self.v.cfg, sid)
        # 새 판 (준비 → 녹화 시작 · 다른 episode) 이면 수동 관찰 · 확인 표시를 풂
        ek = (ui.get("episode"), ui.get("rec_aid") if ui.get("state") == "REC" else None)
        if ek != self.ep_key:
            if self.ep_key is not None:
                self.manual_obs, self.user_ok = None, False
            self.ep_key = ek
        vv = (self.v.vis or {}).get("wrist") or {}
        fresh = bool(self.v.vis) and time.time() - float(self.v.vis.get("t", 0)) < 1.0 and \
            self.v.last_frame_t is not None and time.time() - self.v.last_frame_t < 1.5
        auto = SC.observe(vv if self.v.show_det else {}, self.v.zone, fresh)
        self.auto_obs = auto
        if self.manual_obs is not None:
            self.obs = (self.manual_obs, True, "수동 선택 (F9 · 클릭 — 자동보다 우선)")
        else:
            self.obs = auto
        s = (st or {}).get("state") or {}
        g = s.get("gripper.pos")
        gmin = float(self.v.cfg["safety"].get("gripper_open_min", 15))
        self.grip_open = None if g is None else g >= gmin
        # 닫힌 그리퍼로 시작하는 판 (회복 F2 · F3): 이번 녹화에서 한 번도 열리지 않았으면 '먼저 그리퍼를 여세요'
        rk = (ui.get("episode"), ui.get("rec_aid"))
        if rk != getattr(self, "_open_key", None):
            self._open_key, self.opened_once = rk, False
        if self.grip_open:
            self.opened_once = True
        if row.get("gripper_start") == "closed" and self.grip_open is False and not self.opened_once and ui.get("state") in ("SETUP", "WAIT", "START", "REC"):
            self.close = ("O", SC.CLOSE_STATES["O"][0], "닫힌 채 시작하는 판 — 녹화 시작 뒤 먼저 그리퍼를 충분히 (약 30) 열기")
            return
        self.close = SC.close_state(self.obs[0] if self.obs[1] else None, self.obs[1], self.user_ok, self.grip_open)

    # ---------------------------------------------------------------- 그림 캐시
    def photo(self, key, scene, size):
        from PIL import ImageTk

        k = (key, json.dumps(scene, sort_keys=True, ensure_ascii=False), size)
        ph = self.cache.get(k)
        if ph is None:
            ph = self.cache[k] = ImageTk.PhotoImage(SC.render(scene, size))
        return ph

    # ---------------------------------------------------------------- 그리기
    def draw(self, st, ui):
        t0 = time.perf_counter()
        vg = self.vg or {}
        row = ui.get("row") or {}
        state = ui.get("state", "START")
        g = self.v.guide
        stages = g.stages or []
        keys = [x["key"] for x in stages]
        cur_key = keys[g.cur] if 0 <= g.cur < len(keys) else None
        # 머리
        typ = row.get("pilot_variant") or row.get("scenario_id", "").split("-")[0]
        if vg.get("category"):  # 제목 = 무엇을 교정하는 판인지 (분류) · 둘째 줄 = 지금 상태 + 할 일
            self.title.configure(text=f"{typ} | {vg['category']}" + (f" — {vg['case']}" if vg.get("case") else ""))
            self.sub.configure(text=" — ".join(x for x in (vg.get("title"), vg.get("subtitle")) if x))
        else:
            self.title.configure(text=f"{typ} | {vg.get('title', row.get('label', ''))}")
            self.sub.configure(text=vg.get("subtitle", ""))
        ang = (self.v.vis or {}).get("angle") or {}
        fr = (self.v.vis or {}).get("front") or {}
        meas = []
        if fr.get("detected") and "dist_planned_cm" in fr:
            meas.append(f"front 검출 ↔ 계획 자리 {fr['dist_planned_cm']:.1f} cm")
        if ang.get("meas") is not None:
            meas.append(f"측정 각도 {rc._cube_angle().label(ang['meas'])}")
        ep = ui.get("episode")
        self.info.configure(text=f"{vg.get('kind', '')} · 계획: {row.get('position', '-')} · 큐브 각도 {row.get('angle', '-')} · Episode {ep if ep is not None else '-'}"
                                 + ("   |   측정 (참고): " + " · ".join(meas) if meas else "   |   측정: 없음"))
        # 왼쪽 단계 그림
        stv = vg.get("stages") or {}
        for c in self.cards:
            k = c["key"]
            d = stv.get(k) or {}
            i = keys.index(k) if k in keys else -1
            if i == g.cur:
                bg, fg, hl, tag = CUR, "#111827", CUR, "지금 · "
            elif i == g.cur + 1:
                bg, fg, hl, tag = PANEL, FG, NXT, "다음 · "
            elif 0 <= i < g.cur:
                bg, fg, hl, tag = DONE_C, DIM, DONE_C, ""
            else:
                bg, fg, hl, tag = PANEL, DIM, PANEL, ""
            c["frame"].configure(bg=bg, highlightbackground=hl)
            for w in (c["title"], c["row"], c["text"]):
                w.configure(bg=bg)
            c["title"].configure(fg=fg, text=tag + d.get("title", k))
            c["text"].configure(fg=fg, text=d.get("text", ""))
            if d.get("scene"):
                c["img"].configure(image=self.photo("stage", d["scene"], (self.dw, self.dh)))
        dn = stv.get("done") or {}
        self.done_line.configure(text=("지금 · " if cur_key == "done" else "그 다음 · ") + dn.get("title", "⑤ 상자 → 쉬는 자세"),
                                 fg=CUR if cur_key == "done" else DIM)
        # 오른쪽 실패 · 목표 그림
        items = list(vg.get("failures") or [])[:3] + ([vg["target"]] if vg.get("target") else [])
        ok_, certain, why = self.obs
        for i, c in enumerate(self.fcards):
            if i >= len(items):
                c["frame"].pack_forget()
                continue
            it = items[i]
            sel = it.get("key") == ok_ and (certain or self.manual_obs is not None)
            base = RED if i < 3 else GREEN
            c["frame"].configure(highlightbackground=CUR if sel else base, highlightthickness=5 if sel else 2)
            c["img"].configure(image=self.photo("fail", it.get("scene") or {}, (self.fw, self.fh)))
            c["name"].configure(text=it.get("name", ""), fg=FG if sel or ok_ is None else DIM)
            c["text"].configure(text=it.get("text", ""))
            src = "수동 선택" if self.manual_obs is not None else "자동 추정 · 보조"
            c["tag"].configure(text=(f"◀ 지금 화면 ({src})" if i < 3 else f"◀ 화면상 비슷함 ({src}) — 깊이 · 접촉은 직접 확인") if sel else "",
                               wraplength=self.fw)
        self.draw_panels(row, state, stv, cur_key)
        # 닫힘 안내
        code, short, detail = self.close
        col = "#%02x%02x%02x" % SC.CLOSE_STATES.get(code, ("", (75, 85, 99)))[1]
        self.cbox.configure(highlightbackground=col)
        self.c_big.configure(text=short + (" (자동 판정 아님)" if code == "C" else ""), fg=col if code != "U" else FG)
        self.c_why.configure(text=detail)
        gk = None if self.grip_open is None else ("open" if self.grip_open else "closed")
        gv = ((st or {}).get("state") or {}).get("gripper.pos")
        if gk:
            self.g_img.configure(image=self.photo("grip", {"grip": gk, "tag": ""}, (int(64 * self.s), int(48 * self.s))))
        self.g_txt.configure(text=("그리퍼 열림" if gk == "open" else "그리퍼 닫힘" if gk == "closed" else "그리퍼 값 없음")
                             + ("" if gv is None or self.v.mode != "debug" else f" ({gv:.0f})"))
        self.c_obs.configure(text=f"손목 화면: {SC.OBS_KO.get(ok_ if certain else None)} — {why}")
        # 아래 띠: 지금 · 다음 · 이후 · 하지 말 것
        stp, scol, blk = getattr(self.v, "step_info", ("", FG, []))
        if state in ("SETUP", "WAIT", "START"):
            a = vg.get("setup") or {}
            now = ("✗ 안전 조건으로 → 막힘 — " + blk[0][2]) if blk else a.get("now", stp)
            self.now.configure(text="지금: " + now, fg=RED if blk else CUR)
            self.nxt.configure(text="다음: " + a.get("next", "→ 로 녹화 시작"))
            self.later.configure(text="이후: " + a.get("later", ""))
            self.dont.configure(text="✗ 하지 말 것: " + a.get("dont", ""))
        elif state == "RESET":
            self.now.configure(text="지금: 결과 입력 — 1 첫 파지 성공 · 2 재시도 후 성공 · 3 실패", fg=CUR)
            self.nxt.configure(text="다음: m 메모 · p 방금 판 다시 보기 (선택)")
            self.later.configure(text="이후: → 저장 → 준비 단계에서 다음 판 자세 (녹화 안 함)")
            self.dont.configure(text="✗ 하지 말 것: 리더 팔을 크게 움직이기 (다음 판 시작 자세)")
        elif state in ("SAVING", "FINAL"):
            self.now.configure(text="지금: 저장 중 — 리더 팔을 그대로 두세요", fg="#93c5fd")
            self.nxt.configure(text="")
            self.later.configure(text="")
            self.dont.configure(text="✗ 하지 말 것: 저장 중 리더 움직이기")
        else:
            d = stv.get(cur_key) or {}
            self.now.configure(text="지금: " + d.get("now", stp), fg=CUR)
            self.nxt.configure(text="다음: " + d.get("next", ""))
            self.later.configure(text="이후: " + d.get("later", ""))
            self.dont.configure(text="✗ 하지 말 것: " + d.get("dont", ""))
        src = "수동 선택 (F7 = 자동)" if g.manual is not None else "자동 추정 (보조)"
        self.stage_src.configure(text=f"단계: {src} — {getattr(g, 'auto_why', '')}\nF5/F6 · 그림 클릭 = 단계 바꾸기 · F9 · 오른쪽 그림 클릭 = 관찰 바꾸기")
        # 녹화 · 결과 · 키
        el = ui.get("elapsed")
        name = {"REC": "● 녹화 중", "SETUP": "준비 — 녹화 안 함", "RESET": "결과 입력 — 녹화 안 함", "SAVING": "저장 중",
                "WAIT": "다음 판 대기", "START": "시작 준비", "DONE": "녹화 종료", "FINAL": "마무리 저장"}.get(state, state)
        self.rec.configure(text=name + (f"  {el or 0:4.0f}s / {ui.get('episode_time', 0):.0f}s" if state == "REC" else ""),
                           fg=RED if state == "REC" else FG)
        res = []
        lab = ui.get("label")
        if lab is not None:
            res.append("결과: " + (lab or "아직 입력 안 함"))
        if ui.get("memo_mode"):
            res.append(f"메모 입력 중: {ui.get('memo_text', '')}▏")
        self.result.configure(text="\n".join(res), fg=FG)
        kk = ui.get("keys") or []
        keytxt = " · ".join(f"{k} {d_}" for k, d_ in kk[:6])
        self.keys.configure(text=keytxt + "\n창 키: F4 디버그 화면 · F10 정렬 확인함 · F11 실제 실패 영상 · F2 격자 · F3 검출")
        self.timing.append(time.perf_counter() - t0)
        del self.timing[:-300]

    def draw_panels(self, row, state, stv, cur_key):
        """1 줄 ① 칸 (배치 방법 / 지금 단계 교정 방법) · ③ 칸 (목표 손목 그림, 실시간 손목 영상과 같은 크기 · 좌표)."""
        from PIL import ImageTk

        vg = self.vg or {}
        W, H = self.v.W, self.v.Hh
        setup = state in ("SETUP", "WAIT", "START")
        reg = row.get("wrist_start_region")
        if setup:
            self.p1_title.configure(text="① 배치 방법 (녹화 안 함)")
            side = vg.get("side")
            k = ("side", json.dumps(side, sort_keys=True, ensure_ascii=False), (W, int(H * 0.5)))
            if side:
                if k not in self.cache:
                    self.cache[k] = ImageTk.PhotoImage(SC.render_side(side, (W, int(H * 0.5))))
                self.p1_img.configure(image=self.cache[k])
            steps = vg.get("setup_steps") or []
            self.p1_txt.configure(text="\n".join(f"{i + 1}. {t}" for i, t in enumerate(steps))
                                  + (f"\n{self.ref_msg}" if getattr(self, "ref_msg", "") else ""))
            tgt = dict(vg.get("setup_target") or {})
            if tgt.get("region") == "start":
                if reg:
                    tgt["region"] = list(reg["u"]) + list(reg["v"])
                else:
                    tgt.pop("region")
            self.p3_title.configure(text="③ 목표 손목 화면 — 이렇게 보이면 멈추고 →", fg=AMBER)
            ti = vg.get("setup_target_image") or {}
            ph = self.real_frame(ti, tgt.get("region") if isinstance(tgt.get("region"), list) else None, (W, H)) if ti else None
            if ph is not None:  # 실제 실패 장면 (개념도 대신)
                self.p3_img.configure(image=ph)
                self.p3_cap.configure(text=ti.get("caption", "실제 실패 장면") + "\n(주황 점선 = 시작 영역 · 실시간 손목 화면과 같은 자리)")
                self.p3_title.configure(text=f"③ {ti.get('label', '실제 실패 장면')} — 이렇게 보이면 멈추고 →")
                return
        else:
            d = stv.get(cur_key) or {}
            self.p1_title.configure(text=("① 지금 할 일 · " + d.get("title", "")) if state == "REC" else "① 결과 입력")
            if d.get("scene"):
                self.p1_img.configure(image=self.photo("stage", d["scene"], (int(H * 0.5 * 4 / 3), int(H * 0.5))))
            if state == "REC":
                self.p1_txt.configure(text=d.get("text", "") + ("\n\n지금: " + d["now"] if d.get("now") else ""))
            else:
                self.p1_txt.configure(text="1 첫 파지 성공 · 2 재시도 후 성공 · 3 실패 (선택)\n→ 저장 · ← 버리기")
            tgt = dict(vg.get("rec_target") or {})
            self.p3_title.configure(text="③ 목표 손목 화면 — 닫기 직전", fg=GREEN)
        cap = tgt.pop("caption", "")
        if tgt:
            self.p3_img.configure(image=self.photo("p3", tgt, (W, H)))
        self.p3_cap.configure(text=cap + "\n(개념도 · 실시간 손목 화면과 같은 자리에 그림 · 주황 점선 = 시작 영역 · 초록 점선 = 참고 위치)")

    def blank(self, size):
        """검은 빈 그림 (글자만 띄울 때 Label 크기를 픽셀로 두려고)."""
        from PIL import Image, ImageTk

        k = ("blank", tuple(size))
        if k not in self.cache:
            self.cache[k] = ImageTk.PhotoImage(Image.new("RGB", tuple(size), (0, 0, 0)))
        return self.cache[k]

    def real_frame(self, ti, region, size):
        """실제 실패 장면 프레임 (설정 setup_target_image: path · crop wrist|front) → PhotoImage (주황 시작 영역 점선). 파일 없으면 None."""
        from PIL import Image, ImageDraw, ImageTk
        from r12_viewer_guide import dashed_rect

        p = os.path.join(rc.ROOT, ti.get("path", ""))
        k = ("real", p, ti.get("crop"), ti.get("label"), tuple(region or ()), size)
        if k in self.cache:
            return self.cache[k]
        if not os.path.exists(p):
            return None
        im = Image.open(p).convert("RGB")
        if ti.get("crop") in ("wrist", "front") and im.size[0] >= 2 * im.size[1]:
            half = im.size[0] // 2
            im = im.crop((half, 0, im.size[0], im.size[1]) if ti["crop"] == "wrist" else (0, 0, half, im.size[1]))
        im = im.resize(size)
        d = ImageDraw.Draw(im)
        if region:
            u0, u1, v0, v1 = region
            dashed_rect(d, u0 * size[0], v0 * size[1], u1 * size[0], v1 * size[1], (249, 115, 22), 3)
        lab = ti.get("label", "실제 실패 장면")
        d.rectangle([4, 4, 14 + d.textlength(lab, font=self.v.pf), 32], fill=(127, 29, 29))
        d.text((9, 6), lab, fill=(255, 255, 255), font=self.v.pf)
        self.cache[k] = ImageTk.PhotoImage(im)
        return self.cache[k]

    # ---------------------------------------------------------------- 영상
    def draw_cams(self, ui):
        """Wrist (크게, 최소 표시) · Front (작게, 보조). Viewer.draw_cams 대신 불림."""
        from PIL import Image, ImageDraw, ImageTk

        t0 = time.perf_counter()
        v = self.v
        W, H = v.W, v.Hh
        rp = v.replay_frames(ui)
        if rp is not None:
            k, n, pair = rp
            for i, (lab_, size) in enumerate(((self.fimg, (W // 2, H // 2)), (self.wimg, (W, H)))):
                im = Image.fromarray(pair[i]).resize(size)
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, size[0], 28], fill=(30, 64, 175))
                d.text((8, 4), f"이전 판 다시 보기 {k / 3:4.1f}s / {n / 3:.1f}s", fill=(255, 255, 255), font=v.pf)
                ph = ImageTk.PhotoImage(im)
                lab_.configure(image=ph)
                lab_.image = ph
            return
        front, wrist = v.imgs
        if wrist is None:
            # 그림 없는 Label 의 width/height 는 글자 수 단위 → 빈 그림을 깔아 픽셀 크기로 (카메라 열기 전 창이 커져 최소 크기로 줄던 문제)
            self.wimg.configure(image=self.blank((W, H)), text="영상 없음 — 녹화 프로세스가 아직 카메라를 열지 않았어요", fg=FG, font=v.f,
                                compound="center", wraplength=W - 20, width=W, height=H)
        else:
            im = Image.fromarray(wrist)
            d = ImageDraw.Draw(im)
            self.wrist_overlay(d, im.size[0], im.size[1], ui)
            if ui.get("preview"):
                d.rectangle([0, 0, im.size[0], 26], fill=(127, 29, 29))
                d.text((6, 3), "PREVIEW · " + ui.get("preview_frames", "기존 녹화 영상") + " · 녹화 안 함", fill=(255, 255, 255), font=v.pf)
            ph = ImageTk.PhotoImage(im.resize((W, H)))
            self.wimg.configure(image=ph, text="", width=W, height=H)
            self.wimg.image = ph
        fsz = (W // 2, H // 2)
        if front is None:
            self.fimg.configure(image=self.blank(fsz), text="front 영상 없음", fg=FG, font=v.f_s, compound="center", width=fsz[0], height=fsz[1])
        else:
            im = Image.fromarray(front)
            d = ImageDraw.Draw(im)
            self.front_overlay(d, ui)
            if ui.get("preview"):
                d.rectangle([0, 0, im.size[0], 40], fill=(127, 29, 29))
                d.text((8, 4), "PREVIEW · 녹화 안 함", fill=(255, 255, 255), font=v.pf_big)
            ph = ImageTk.PhotoImage(im.resize(fsz))
            self.fimg.configure(image=ph, text="", width=fsz[0], height=fsz[1])
            self.fimg.image = ph
        self.timing_cam = time.perf_counter() - t0

    def wrist_overlay(self, d, w, h, ui):
        from r12_viewer_guide import dashed_rect

        v = self.v
        row = ui.get("row") or {}
        vv = (v.vis or {}).get("wrist") or {}
        z = v.zone
        f = v.pf
        if z:  # 참고 목표 위치 (d2 사람 닫기 시작 위치 분포 · 2D) — 초록 점선 · 판정 아님
            dashed_rect(d, z["u"][0] * w, z["v"][0] * h, z["u"][1] * w, z["v"][1] * h, (34, 197, 94), 3, 12)
        reg = row.get("wrist_start_region")
        if reg and ui.get("state") in ("SETUP", "WAIT", "START"):
            dashed_rect(d, reg["u"][0] * w, reg["v"][0] * h, reg["u"][1] * w, reg["v"][1] * h, (249, 115, 22), 3)
            d.text((reg["u"][0] * w + 3, reg["v"][0] * h - 24), "시작 영역 (대략)", fill=(249, 115, 22), font=f)
        key, certain, _ = self.obs
        if vv.get("detected") and v.show_det:
            x, y, bw, bh = vv["bbox"]
            col = (239, 68, 68) if (key == "edge" and certain) else (249, 115, 22) if (key in ("ahead", "side") and certain) else \
                (250, 204, 21) if key == "in_zone" else (229, 231, 235)
            d.rectangle([x, y, x + bw, y + bh], outline=col, width=4)
            cut = [nm for nm, c in (("위", y <= 2), ("아래", y + bh >= h - 2), ("왼쪽", x <= 2), ("오른쪽", x + bw >= w - 2)) if c]
            for nm in cut:
                box = {"위": [0, 0, w, 7], "아래": [0, h - 7, w, h], "왼쪽": [0, 0, 7, h], "오른쪽": [w - 7, 0, w, h]}[nm]
                d.rectangle(box, fill=(239, 68, 68))
        if z:  # 참고 위치 글씨는 큐브 상자 위에 (가려지지 않게)
            lab = "참고 위치 (2D)"
            lx, ly = z["u"][0] * w, z["v"][1] * h + 4
            d.rectangle([lx, ly, lx + d.textlength(lab, font=f) + 8, ly + 24], fill=(17, 24, 39))
            d.text((lx + 4, ly + 1), lab, fill=(74, 222, 128), font=f)
        # 위: 지금 단계 · 그리퍼
        g = v.guide
        stv = (self.vg or {}).get("stages") or {}
        keys = [x["key"] for x in (g.stages or [])]
        ck = keys[g.cur] if 0 <= g.cur < len(keys) else None
        top = "지금 " + ((stv.get(ck) or {}).get("title") or "-")
        gtxt = "그리퍼 열림" if self.grip_open else "그리퍼 닫힘" if self.grip_open is False else "그리퍼 ?"
        y0 = 30 if ui.get("preview") else 4
        tw = d.textlength(top, font=v.pf_big)
        d.rectangle([4, y0, 14 + tw, y0 + 38], fill=(17, 24, 39))
        d.text((9, y0 + 2), top, fill=hexrgb(CUR), font=v.pf_big)
        gw = d.textlength(gtxt, font=f)
        d.rectangle([w - gw - 16, y0, w - 4, y0 + 28], fill=(17, 24, 39))
        d.text((w - gw - 10, y0 + 3), gtxt, fill=(255, 255, 255), font=f)
        # 아래: 관찰 (자동/수동)
        obs = SC.OBS_KO.get(key if certain else None)
        src = "수동" if self.manual_obs is not None else "자동 · 보조"
        txt = f"큐브: {obs} ({src})"
        col = {"edge": (252, 165, 165), "ahead": (253, 186, 116), "side": (253, 186, 116), "in_zone": (253, 230, 138)}.get(key if certain else None,
                                                                                                                     (229, 231, 235))
        # 단계 줄 바로 아래 (화면 아래 가장자리는 잘린 큐브가 보이는 곳이라 비워 둠)
        fb = v.pf_big if d.textlength(txt, font=v.pf_big) < w - 30 else f
        tw = d.textlength(txt, font=fb)
        d.rectangle([4, y0 + 42, 14 + tw, y0 + 82], fill=(17, 24, 39))
        d.text((9, y0 + 44), txt, fill=col, font=fb)

    def front_overlay(self, d, ui):
        """Front (보조): 계획 큐브 윤곽 (흰 점선, '계획') · 빨강 검출 상자 (초록, '검출'). 글씨는 줄여 보여도 읽히게 크게."""
        v = self.v
        row = ui.get("row") or {}
        fb = v.pf_big
        if row.get("position") and row.get("angle_raw") not in (None, ""):
            try:
                cs = [rc.cm_to_px(v.H, c) for c in rc.cube_corners(v.cfg, row["position"], row["angle_raw"], half=1.6)]
                for a_, b_ in zip(cs, cs[1:] + cs[:1]):
                    for t in range(0, 8, 2):
                        d.line([(a_[0] + (b_[0] - a_[0]) * t / 8, a_[1] + (b_[1] - a_[1]) * t / 8),
                                (a_[0] + (b_[0] - a_[0]) * (t + 1) / 8, a_[1] + (b_[1] - a_[1]) * (t + 1) / 8)], fill=(255, 255, 255), width=4)
                cx = sum(p[0] for p in cs) / 4
                cy = max(p[1] for p in cs)
                lab = f"계획 {row['position']}"
                tw = d.textlength(lab, font=fb)
                tx = min(max(cx - tw / 2, 4), d.im.size[0] - tw - 8)
                d.rectangle([tx - 4, cy + 6, tx + tw + 4, cy + 44], fill=(15, 15, 15))
                d.text((tx, cy + 8), lab, fill=(255, 255, 255), font=fb)
            except Exception:  # 계획 자리 그리기 실패는 화면만 (기록 무관)
                pass
        fr = (v.vis or {}).get("front") or {}
        if fr.get("detected") and v.show_det:
            cx, cy = fr["px"]
            d.rectangle([cx - 18, cy - 18, cx + 18, cy + 18], outline=(34, 197, 94), width=4)
