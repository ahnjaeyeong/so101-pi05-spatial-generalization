"""HIL 수집자 화면 — 그리기 (PIL 만, Tk 없음). 화면 전체를 이미지 한 장으로 합성한다 → 미리보기 · 스크린샷 · 실시간 창이 같은 그림.

그림 언어는 R1/R2 수집 도구 (r1_r2_collection/tools/r12_schematic.py) 를 그대로 가져다 쓴다 (수정 없이 import):
  큐브 = 빨간 네모 · 그리퍼 손가락 = 회색 막대 (벌어짐 = 열림) · 참고 목표 = 초록 점선 · 화면 속 위치 변화 = 파란 화살표
  하면 안 됨 = 빨간 X · 올바른 예 = 초록 체크. 손목 영상 좌표: 로봇 좌우 = 화면 위아래 (v), 멀고 가까움 = 화면 좌우 (u).
그림은 개념도다: 화살표는 화면 속 큐브의 상대 위치 변화이지 관절 이동 방향이 아니다.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

R12_TOOLS = Path.home() / "so101_runs/main_k8/r1_r2_collection/tools"
if str(R12_TOOLS) not in sys.path:
    sys.path.insert(0, str(R12_TOOLS))
import r12_schematic as SC  # noqa: E402  (수정 없이 재사용)

W, H = 1400, 940
BG, PANEL, PANEL2, FG, DIM = (17, 24, 39), (31, 41, 55), (24, 32, 46), (243, 244, 246), (156, 163, 175)
AMBER, BLUE, RED, GREEN, VIOLET, GRAY = (245, 158, 11), (59, 130, 246), (239, 68, 68), (34, 197, 94), (139, 92, 246), (75, 85, 99)
FONT_B = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"
FONT_R = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"
FONT_M = "/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf"
_FONTS = {}


def font(px, kind="r"):
    key = (kind, int(px))
    if key not in _FONTS:
        f = {"b": FONT_B, "r": FONT_R, "m": FONT_M}[kind]
        try:
            _FONTS[key] = ImageFont.truetype(f, int(px))
        except OSError:
            _FONTS[key] = ImageFont.load_default()
    return _FONTS[key]


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def wrap(d, text, f, width):
    out, line = [], ""
    for word in str(text).split(" "):
        t = (line + " " + word).strip()
        if d.textlength(t, font=f) <= width or not line:
            line = t
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def text_block(d, xy, text, f, fill, width, gap=4, max_lines=None):
    x, y = xy
    lines = wrap(d, text, f, width)
    if max_lines:
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += f.size + gap
    return y


# ---------------- 교정 가이드 (네모 그림 4 칸) ----------------
# 손목 화면 좌표 (r12_schematic 과 같음). TARGET = 닫기 영역 가운데.
T = SC.TARGET_UV
GUIDES = {
    "R1": [
        ("① 큐브를 지나침", {"grip": "open", "cube": [0.35, 0.17], "cut": "top", "mark": "x", "tag": "개념도"}),
        ("② 상대 위치 되맞추기", {"grip": "open", "cube": [0.35, 0.3], "ghost": [0.35, 0.12], "target": True, "arrow": True, "tag": "개념도"}),
        ("③ 큐브 재정렬 (열린 채)", {"grip": "open", "cube": list(T), "zone": True, "tag": "개념도"}),
        ("④ 파지 완료 → 상자", {"grip": "grasp", "cube": list(T), "mark": "check", "tag": "개념도"}),
    ],
    "R2": [
        ("① 앞이나 옆에 있음", {"grip": "open", "cube": [0.36, 0.33], "mark": "x", "tag": "개념도"}),
        ("② 열린 채 정렬", {"grip": "open", "cube": [0.36, 0.38], "target": True, "arrow": True, "tag": "개념도"}),
        ("③ 파지 직전 위치 확인", {"grip": "open", "cube": list(T), "zone": True, "tag": "개념도"}),
        ("④ 첫 닫힘으로 파지 → 상자", {"grip": "grasp", "cube": list(T), "mark": "check", "tag": "개념도"}),
    ],
    "R2-O": [
        ("① 닫힌 채 빈 파지", {"grip": "closed", "cube": [0.62, 0.42], "mark": "x", "tag": "개념도"}),
        ("② 그리퍼 다시 열기", {"grip": "open", "cube": [0.62, 0.42], "tag": "개념도"}),
        ("③ 다시 정렬", {"grip": "open", "cube": [0.6, 0.45], "target": True, "arrow": True, "tag": "개념도"}),
        ("④ 정상 파지 → 상자", {"grip": "grasp", "cube": list(T), "mark": "check", "tag": "개념도"}),
    ],
}
_SC_CACHE = {}


def scene_img(scene, size):
    key = (repr(sorted(scene.items())), size)
    if key not in _SC_CACHE:
        _SC_CACHE[key] = SC.render(scene, size)
    return _SC_CACHE[key]


def guide_step(code, marks):
    """교정 중 지금 강조할 그림 칸 (0–3). 표시 키로만 정함 (자동 판정 없음)."""
    marks = marks or []
    if "first_grasp_ok" in marks or "final_success" in marks:
        return 3
    if "recovery_done" in marks:
        return 2
    return 1 if code == "CORRECTING" else 0


# ---------------- 합성 영상 (미리보기) ----------------
def synth_wrist(scene, size):
    """합성 손목 영상: 개념도 표시 (X · 체크 · 화살표 · 목표 · 영역 · 이전 위치) 를 빼고 큐브 · 손가락만."""
    plain = {k: v for k, v in scene.items() if k in ("grip", "cube", "cut")}
    plain["tag"] = ""
    return scene_img(plain, size).copy()


def synth_front(state_code, size):
    """위에서 본 탁자 (합성). 상자 · 로봇 · 큐브 · 팔 — 개념도."""
    w, h = size
    im = Image.new("RGB", size, (205, 199, 189))
    d = ImageDraw.Draw(im)
    d.rectangle([w * 0.33, h * 0.68, w * 0.67, h * 0.98], fill=(166, 124, 82), outline=(110, 80, 50), width=3)  # 상자
    base = (w * 0.5, h * 0.12)
    d.ellipse([base[0] - 22, base[1] - 22, base[0] + 22, base[1] + 22], fill=(40, 40, 40))
    cube = (w * 0.38, h * 0.45)
    d.rectangle([cube[0] - 12, cube[1] - 12, cube[0] + 12, cube[1] + 12], fill=(220, 38, 38), outline=(127, 29, 29), width=2)
    tip = {"POLICY_RUNNING": (w * 0.6, h * 0.45), "STOP_REQUESTED": (w * 0.62, h * 0.45)}.get(state_code, (w * 0.56, h * 0.43))
    d.line([base, tip], fill=(30, 30, 30), width=12)
    d.ellipse([tip[0] - 9, tip[1] - 9, tip[0] + 9, tip[1] + 9], fill=(90, 90, 90))
    return im


# ---------------- 칸 그리기 ----------------
def cam_panel(im, d, box, frame, title, mode_label, note=None):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(10, 10, 10))
    if frame is not None:
        fw, fh = x1 - x0, y1 - y0 - 30
        if isinstance(frame, Image.Image):
            fr = frame
        else:
            fr = Image.fromarray(frame)
        r = min(fw / fr.width, fh / fr.height)
        fr = fr.resize((max(1, int(fr.width * r)), max(1, int(fr.height * r))), Image.BILINEAR)
        im.paste(fr, (x0 + (fw - fr.width) // 2, y0 + 30 + (fh - fr.height) // 2))
    else:
        d.text((x0 + 20, (y0 + y1) // 2), "영상 없음", font=font(22), fill=DIM)
    if frame is not None and mode_label in ("PREVIEW", "SIMULATION"):  # 영상 안에도 표시
        tag = "PREVIEW · 합성 영상" if mode_label == "PREVIEW" else "SIMULATION · 가짜 장치"
        f_ = font(20, "m")
        tw = d.textlength(tag, font=f_)
        d.rectangle([x0 + 8, y1 - 34, x0 + 20 + tw, y1 - 6], fill=(153, 27, 27))
        d.text((x0 + 14, y1 - 32), tag, font=f_, fill=(255, 255, 255))
    band = RED if mode_label in ("PREVIEW", "SIMULATION") else (31, 41, 55)
    d.rectangle([x0, y0, x1, y0 + 30], fill=band)
    d.text((x0 + 8, y0 + 3), f"{title}  ·  {mode_label}" + (f"  ·  {note}" if note else ""), font=font(19, "m"), fill=(255, 255, 255))


def card(d, box, title, fill=PANEL, title_col=FG):
    d.rounded_rectangle(box, radius=10, fill=fill)
    d.text((box[0] + 14, box[1] + 8), title, font=font(21, "b"), fill=title_col)
    return box[1] + 40


def status_rows(d, x, y, w, ui, raw):
    """제어 상태 사실 (tap 값 그대로) — 정책 · 리더 · 녹화."""
    raw = raw or {}
    if ui["code"] in ("UNKNOWN", "ENDED"):
        for k in ("정책 명령", "리더", "사람 제어", "녹화"):
            d.text((x, y), k, font=font(16), fill=DIM)
            d.text((x + 96, y), "확인 불가 (상태 갱신 안 됨)" if ui["code"] == "UNKNOWN" else "세션 끝", font=font(16), fill=DIM)
            y += 26
        return y
    rows = []
    pa = raw.get("policy_active")
    ph = raw.get("phase")
    if raw.get("fault"):
        rows.append(("정책 명령", "차단됨 (오류 잠김)", RED))
    elif ph == "autonomous" and not raw.get("in_transition"):
        rows.append(("정책 명령", "보내는 중", GREEN))
    elif pa is False and not raw.get("policy_since_pause"):
        rows.append(("정책 명령", "멈춤 (확인됨)", FG))
    elif pa is None:
        rows.append(("정책 명령", "확인 불가", DIM))
    else:
        rows.append(("정책 명령", "멈추는 중 / 미확인", AMBER))
    lt = raw.get("leader_torque")
    if raw.get("in_transition") and raw.get("transition") == ["autonomous", "paused"] and lt:
        rows.append(("리더", f"토크로 움직이는 중 ({raw.get('transition_age') or 0:.1f}/2 s)", RED))
    elif lt is True:
        rows.append(("리더", "토크 켜짐 · 제자리 유지", AMBER))
    elif lt is False:
        rows.append(("리더", "토크 꺼짐 · 손으로 잡기", AMBER if ph != "correcting" else GREEN))
    else:
        rows.append(("리더", "확인 불가", DIM))
    rows.append(("사람 제어", "가능" if ui["human_control_ok"] else "불가", GREEN if ui["human_control_ok"] else DIM))
    rows.append(("녹화", f"● 녹화 중 · {ui.get('frames') or 0} frame" if ui["recording"] else "○ 녹화 안 함", RED if ui["recording"] else DIM))
    rows.append(("저장된 교정", f"{ui.get('episodes_saved') if ui.get('episodes_saved') is not None else '-'} 판", FG))
    for k, v, c in rows:
        d.text((x, y), k, font=font(16), fill=DIM)
        y2 = text_block(d, (x + 96, y), v, font(16), c, w - 100, gap=1, max_lines=2)
        y = max(y + 26, y2 + 4)
    return y


def guide_panel(im, d, box, ui, raw):
    x0, y0, x1, y1 = box
    code = ui["code"]
    typ = ui.get("type")
    marks = (raw or {}).get("marks_current") or []
    if code in ("CORRECTING", "HUMAN_READY", "FAULT_LOCKED") and typ in GUIDES:
        y = card(d, box, f"교정 가이드 — {typ}", title_col=AMBER)
        y = text_block(d, (x0 + 14, y - 2), SC_TITLE(typ), font(23, "b"), FG, x1 - x0 - 28, gap=2, max_lines=2) + 6
        cur = guide_step(code, marks)
        _grid(im, d, x0 + 12, y, x1 - x0 - 24, y1 - y - 34, GUIDES[typ], cur)
        d.text((x0 + 14, y1 - 28), "개념도 · 화살표 = 화면 속 큐브 위치 변화 (관절 이동 방향 아님)", font=font(15), fill=DIM)
        return
    if code in ("CORRECTING", "HUMAN_READY", "FAULT_LOCKED"):
        y = card(d, box, "교정 가이드 — 유형을 고르세요", title_col=AMBER)
        msg = "교정을 시작하면 바로 1 / 2 / 3 으로 유형 표시" if code != "CORRECTING" else "지금 1 / 2 / 3 으로 유형을 표시하세요 (그림이 바뀝니다)"
        d.text((x0 + 14, y), msg, font=font(20), fill=FG)
        y += 34
        _type_rows(im, d, x0 + 12, y, x1 - x0 - 24, y1 - y - 10)
        return
    if code in ("POLICY_RUNNING", "STOP_REQUESTED", "POLICY_WAIT"):
        y = card(d, box, "이런 모습이 보이면 Space 로 정지" if code != "POLICY_WAIT" else "정지 대상 실패 모습 (참고)", title_col=AMBER)
        _type_rows(im, d, x0 + 12, y, x1 - x0 - 24, y1 - y - 10, first_only=True)
        return
    if code in ("RESULT",) or (code in ("STOPPING", "ENDED") and ui.get("last_result")):
        result_panel(d, box, ui)
        return
    if code == "END_MENU":
        end_panel(d, box, ui)
        return
    if code in ("LEADER_ALIGNING", "STOP_CONFIRMING", "STARTING"):
        y = card(d, box, "리더가 스스로 움직입니다", fill=(69, 10, 10), title_col=(254, 202, 202))
        y = text_block(d, (x0 + 18, y + 6), "정지하면 리더가 토크로 follower 의 마지막 명령 자세까지 약 2 초 동안 움직입니다.", font(24, "b"), FG, x1 - x0 - 36)
        y = text_block(d, (x0 + 18, y + 14), "• 리더에서 손 · 손가락을 뗀 채 기다리세요 (끼임).", font(21), FG, x1 - x0 - 36)
        y = text_block(d, (x0 + 18, y + 6), "• 정렬이 끝나면 위쪽 상태가 '사람 제어 준비 완료' 로 바뀝니다. 그 전에는 Tab 을 누르지 마세요.", font(21), FG, x1 - x0 - 36)
        text_block(d, (x0 + 18, y + 6), "• 리더 정렬 힘 · 속도는 실물에서 확인되지 않았습니다.", font(19), (252, 165, 165), x1 - x0 - 36)
        return
    if code in ("UNKNOWN", "UNCERTAIN", "TRANSITION"):
        y = card(d, box, "조작하지 마세요", fill=(55, 65, 81))
        text_block(d, (x0 + 18, y + 6), ui.get("reason") or "상태를 확인하는 중", font(24, "b"), FG, x1 - x0 - 36)
        return
    card(d, box, "")


def SC_TITLE(typ):
    from hil_ui_state import TYPE_TITLES

    return TYPE_TITLES[typ]


def _grid(im, d, x, y, w, h, panels, cur):
    cw, chh = (w - 12) // 2, (h - 12) // 2
    ih = chh - 28
    iw = int(ih * 4 / 3)
    if iw > cw:
        iw, ih = cw, int(cw * 3 / 4)
    for i, (lab, scene) in enumerate(panels):
        cx, cy = x + (i % 2) * (cw + 12), y + (i // 2) * (chh + 12)
        col = AMBER if i == cur else (BLUE if i == cur + 1 else GRAY)
        d.rounded_rectangle([cx - 3, cy - 3, cx + iw + 3, cy + ih + 3], radius=6, outline=col, width=4 if i in (cur, cur + 1) else 2)
        im.paste(scene_img(scene, (iw, ih)), (cx, cy))
        pre = "▶ " if i == cur else ("▷ " if i == cur + 1 else "")
        f_ = font(16, "b" if i == cur else "r")
        t_ = pre + lab
        while d.textlength(t_, font=f_) > cw and len(t_) > 4:
            t_ = t_[:-2] + "…"
        d.text((cx, cy + ih + 5), t_, font=f_, fill=col if i in (cur, cur + 1) else DIM)


def _type_rows(im, d, x, y, w, h, first_only=False):
    rows = [("1  R1  pan 지나침", "R1"), ("2  R2  접근 · 정렬 부족", "R2"), ("3  R2-O  빈 파지", "R2-O")]
    rh = (h - 10) // 3
    ih = rh - 12
    iw = int(ih * 4 / 3)
    for i, (lab, t) in enumerate(rows):
        yy = y + i * rh
        im.paste(scene_img(GUIDES[t][0][1], (iw, ih)), (x, yy))
        d.text((x + iw + 14, yy + 6), lab, font=font(22, "b"), fill=FG)
        from hil_ui_state import TYPE_TITLES

        text_block(d, (x + iw + 14, yy + 38), TYPE_TITLES[t], font(18), DIM, w - iw - 20, max_lines=2)


def result_panel(d, box, ui):
    x0, y0, x1, y1 = box
    r = ui.get("last_result") or {}
    y = card(d, box, f"방금 저장된 교정 — episode {r.get('episode', '-')}", title_col=(103, 232, 249))

    def yn(v, ok="예", bad="아니오"):
        if v is None:
            return ("검토 필요 (표시 없음)", AMBER)
        return (ok, GREEN) if v in (True, "ok", "success") else (bad, RED)

    rows = [("교정 유형", (r.get("type") or "검토 필요 (1/2/3 없음)", FG if r.get("type") else AMBER)),
            ("복구 완료 (m)", yn(r.get("recovery_done"))),
            ("첫 파지 (g/h)", yn(r.get("first_grasp"), "성공", "실패")),
            ("상자 넣기 (b/f)", yn(r.get("final"), "성공", "실패")),
            ("미완성 교정", ("예 — 교정 도중 종료", RED) if r.get("ended_during_correction") else ("아니오", FG)),
            ("원위치 구간 (r)", ("예", AMBER) if r.get("reset") else ("아니오", FG)),
            ("frame", (str(r.get("frames")), FG))]
    for k, (v, c) in rows:
        d.text((x0 + 18, y), k, font=font(20), fill=DIM)
        d.text((x0 + 200, y), v, font=font(20, "b"), fill=c)
        y += 31
    tr = r.get("training", "검토 필요")
    col = RED if tr.startswith("제외") else (GREEN if tr.startswith("변환 포함") else AMBER)
    y = text_block(d, (x0 + 18, y + 6), "학습 데이터: " + tr, font(20, "b"), col, x1 - x0 - 36)
    text_block(d, (x0 + 18, y + 8), "표시 키는 저장 전에 눌러야 이 판에 들어갑니다. 지금 누르면 다음 교정 판에 기록됩니다. 실패한 정책 구간은 녹화되지 않습니다 (교정 구간만 저장).",
               font(16), DIM, x1 - x0 - 36)


def end_panel(d, box, ui):
    x0, y0, x1, y1 = box
    y = card(d, box, "종료 선택 — 터미널 '선택 >' 에 입력", title_col=(229, 231, 235))
    y = text_block(d, (x0 + 18, y), "자동 원위치 복귀는 없습니다. 지금 팔은 마지막 목표 자세를 토크로 유지합니다.", font(20, "b"), AMBER, x1 - x0 - 36)
    for o, (eff, risk) in (ui.get("end_options") or {}).items():
        d.text((x0 + 18, y + 8), o, font=font(26, "m"), fill=FG)
        yy = text_block(d, (x0 + 140, y + 10), eff, font(19, "b"), FG, x1 - x0 - 160)
        y = text_block(d, (x0 + 140, yy), risk, font(17), (252, 165, 165), x1 - x0 - 160) + 4
    for u in ui.get("end_unavailable") or []:
        y = text_block(d, (x0 + 18, y + 8), f"선택 불가: {u}", font(18), DIM, x1 - x0 - 36)


def keys_panel(d, box, ui):
    x0, y0, x1, y1 = box
    y = card(d, box, "지금 쓸 수 있는 키 (터미널 창에서 — 이 창은 키를 받지 않음)")
    colors = {"ok": (GREEN, (20, 83, 45)), "warn": (AMBER, (120, 53, 15)), "blocked": (GRAY, (31, 41, 55)), "mark": (BLUE, (30, 58, 138))}
    cols = 2 if len(ui["keys"]) > 4 else 1
    cw = (x1 - x0 - 30) // cols
    for i, k in enumerate(ui["keys"]):
        cx = x0 + 14 + (i % cols) * cw
        cy = y + (i // cols) * 46
        fg, bgc = colors[k["kind"]]
        kw = max(64, int(d.textlength(k["key"], font=font(22, "m"))) + 22)
        d.rounded_rectangle([cx, cy, cx + kw, cy + 34], radius=7, fill=bgc, outline=fg, width=2)
        d.text((cx + 11, cy + 4), k["key"], font=font(22, "m"), fill=(255, 255, 255) if k["kind"] != "blocked" else DIM)
        strike = k["kind"] == "blocked"
        tx = cx + kw + 10
        lines = wrap(d, k["meaning"], font(16), cw - kw - 22)[:2]
        for j, ln in enumerate(lines):
            d.text((tx, cy + 0 + j * 18 + (8 if len(lines) == 1 else 0)), ln, font=font(16), fill=DIM if strike else FG)


def warn_panel(d, box, ui):
    x0, y0, x1, y1 = box
    y = card(d, box, "안전 · 주의")
    col = {"danger": (254, 202, 202), "warn": (253, 230, 138), "info": DIM}
    dot = {"danger": RED, "warn": AMBER, "info": GRAY}
    for kind, msg in ui["warnings"]:
        if y > y1 - 24:
            break
        d.ellipse([x0 + 16, y + 6, x0 + 26, y + 16], fill=dot[kind])
        y = text_block(d, (x0 + 34, y), msg, font(17 if kind == "info" else 18, "r"), col[kind], x1 - x0 - 50, max_lines=3) + 4


def steps_bar(d, y, ui):
    from hil_ui_state import STEPS

    n = len(STEPS)
    bw = (W - 20 - (n - 1) * 6) // n
    cur = ui.get("step")
    for i, s in enumerate(STEPS):
        x = 10 + i * (bw + 6)
        if cur is None:
            fill, fg, out = PANEL2, DIM, GRAY
        elif i < cur:
            fill, fg, out = (30, 41, 59), DIM, GRAY
        elif i == cur:
            fill, fg, out = (120, 53, 15), (255, 255, 255), AMBER
        elif i == cur + 1:
            fill, fg, out = PANEL2, (191, 219, 254), BLUE
        else:
            fill, fg, out = PANEL2, DIM, GRAY
        d.rounded_rectangle([x, y, x + bw, y + 44], radius=8, fill=fill, outline=out, width=3 if cur is not None and i in (cur, cur + 1) else 1)
        if cur is not None and i < cur:  # 끝난 단계: 작은 체크 (폰트에 ✓ 없음 → 선으로)
            d.line([(x + 9, y + 22), (x + 15, y + 29), (x + 25, y + 14)], fill=GREEN, width=3)
            label = s
        else:
            label = ("▶ " if i == cur else f"{i + 1} ") + s + ("  다음" if cur is not None and i == cur + 1 else "")
        d.text((x + 32 if cur is not None and i < cur else x + 10, y + 10), label, font=font(18, "b" if i == cur else "r"), fill=fg)


def render(ui, raw, frames, mode_label, focus_warn=False, now_label=""):
    """ui = hil_ui_state.derive(...) · raw = tap 사실값 · frames = {'wrist': arr|PIL|None, 'front': ...}."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    col = hexrgb(ui["color"])
    # 상단 상태 띠
    d.rectangle([0, 0, W, 128], fill=col)
    d.rounded_rectangle([18, 16, 114, 112], radius=16, fill=(255, 255, 255))
    ic = ui["icon"]
    if ic == "@check":
        d.line([(38, 66), (58, 90), (96, 38)], fill=col, width=12, joint="curve")
    elif ic == "@x":
        d.line([(40, 38), (92, 90)], fill=col, width=12)
        d.line([(92, 38), (40, 90)], fill=col, width=12)
    else:
        f_ic = font(60 if len(ic) == 1 and ord(ic) > 0x3000 else 64, "b")
        d.text((66 - d.textlength(ic, font=f_ic) / 2, 26 if ord(ic[0]) > 0x3000 else 22), ic, font=f_ic, fill=col)
    d.text((134, 10), ui["title"], font=font(56, "b"), fill=(255, 255, 255))
    text_block(d, (136, 76), ui["sentence"], font(23, "r"), (255, 255, 255), W - 136 - 330, gap=2, max_lines=2)
    # 오른쪽: 모드 · 녹화 · 사람 제어
    mx = W - 312
    mcol = (255, 255, 255) if mode_label == "LIVE" else (254, 226, 226)
    d.rounded_rectangle([mx, 12, W - 14, 46], radius=8, fill=(0, 0, 0) if mode_label == "LIVE" else (153, 27, 27))
    sub = {"PREVIEW": "  · 실물 명령 없음", "SIMULATION": " · 가짜 장치"}.get(mode_label, "  · 실물 연결")
    d.text((mx + 12, 15), mode_label + sub, font=font(22, "m"), fill=mcol)
    rec = ui["recording"]
    d.rounded_rectangle([mx, 52, W - 14, 86], radius=8, fill=(220, 38, 38) if rec else (31, 41, 55))
    d.text((mx + 12, 55), "● 녹화 중 (전문가 시연)" if rec else "○ 녹화 안 함", font=font(22, "b"), fill=(255, 255, 255))
    hc = ui["human_control_ok"]
    d.rounded_rectangle([mx, 92, W - 14, 122], radius=8, fill=(21, 128, 61) if hc else (55, 65, 81))
    d.text((mx + 12, 94), "사람 제어: 가능" if hc else "사람 제어: 불가 (손대지 않기)", font=font(20, "b"), fill=(255, 255, 255))
    # 단계
    steps_bar(d, 138, ui)
    # 가운데
    top = 192
    cam_panel(im, d, (10, top, 600, top + 476), frames.get("wrist"), "WRIST 카메라", mode_label)
    cam_panel(im, d, (610, top, 940, top + 250), frames.get("front"), "FRONT", mode_label)
    sy = card(d, (610, top + 258, 940, top + 476), "제어 상태 (실제 값)")
    status_rows(d, 622, sy - 4, 310, ui, raw)
    guide_panel(im, d, (950, top, W - 10, top + 476), ui, raw)
    # 아래
    keys_panel(d, (10, top + 486, 820, H - 30), ui)
    warn_panel(d, (830, top + 486, W - 10, H - 30), ui)
    foot = f"{now_label}" + (f"  ·  사유: {ui['reason']}" if ui.get("reason") else "")
    d.text((12, H - 26), foot, font=font(16), fill=DIM)
    if focus_warn:
        d.rectangle([0, H // 2 - 60, W, H // 2 + 60], fill=(185, 28, 28))
        msg = "이 창에서는 키가 동작하지 않습니다 — 터미널 창을 클릭한 뒤 키를 누르세요"
        f = font(34, "b")
        d.text((W / 2 - d.textlength(msg, font=f) / 2, H // 2 - 22), msg, font=f, fill=(255, 255, 255))
    return im
