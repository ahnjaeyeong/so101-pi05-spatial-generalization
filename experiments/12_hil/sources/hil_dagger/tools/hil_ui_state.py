"""HIL 수집자 화면 — 상태 판정 (순수 함수, 표시 전용). 2026-11-04.

입력 = adapter tap 이 /dev/shm 에 쓰는 사실값 (raw dict, hil_dagger_entry.py `_tap_snapshot`). 이 모듈은 아무것도 제어하지 않는다.
derive(raw, now) → 화면 상태 하나 + 설명 + 지금 의미 있는 키 + 단계 + 경고 + 결과 칸.

원칙:
  - 실제 제어 상태(공식 DAgger phase · 전환 진행 · 리더 토크 · RTC 스레드 · 정지 뒤 정책 명령)를 우선한다.
  - 정보가 오래됐거나 (stale_s 넘게) 서로 맞지 않으면 'UNCERTAIN' / 'UNKNOWN' 으로 표시하고 조작을 유도하지 않는다.
  - '사람 제어 준비 완료' 는 아래가 모두 참일 때만: phase=paused · 전환 끝 · 직전 전환 = 정책→정지 · RTC 스레드 꺼짐 ·
    정지 시작 뒤 정책 명령 0 · 리더 토크 켜짐(정렬 끝, 위치 유지).
  - 키 설명은 설치된 lerobot 0.6.2 dagger.py `_DAGGER_TRANSITIONS` 와 adapter 규칙 (A5 debounce · A10 재개 차단) 그대로.
"""

from __future__ import annotations

STALE_S = 1.0
SETTLE_S = 0.3  # 리더 정렬 이동이 끝난 뒤 이만큼 지나야 '사람 제어 준비 완료' (마지막 목표 명령 뒤 서보가 멈출 시간)

# 상태 코드 → (제목, 한 문장, 색, 아이콘 글자)
STATES = {
    "UNKNOWN": ("상태 확인 불가", "제어 프로그램 상태를 받지 못하고 있습니다. 로봇을 조작하지 말고 터미널을 확인하세요.", "#6b7280", "?"),
    "UNCERTAIN": ("제어권 미확인", "정책이 완전히 멈췄는지 아직 확인되지 않았습니다. 리더를 잡지 말고 기다리세요.", "#6b7280", "?"),
    "STARTING": ("시작 중 · 리더 정렬", "프로그램이 시작되는 중입니다. 리더가 follower 자세로 움직일 수 있으니 손을 대지 마세요.", "#d97706", "!"),
    "POLICY_WAIT": ("정책 대기", "정책은 멈춰 있습니다. 큐브를 놓고 리더를 받친 뒤 Space 로 정책을 시작하세요.", "#2563eb", "‖"),
    "POLICY_RUNNING": ("정책 실행 중", "로봇을 관찰하다가 잘못된 접근이 보이면 Space 로 정지를 요청하세요.", "#16a34a", "▶"),
    "STOP_REQUESTED": ("정지 요청됨", "정지 요청이 들어갔습니다. 정책이 멈추고 리더가 움직이기 시작합니다. 손을 대지 마세요.", "#d97706", "■"),
    "STOP_CONFIRMING": ("정지 확인 중", "정책을 멈추는 중입니다. 곧 리더가 움직입니다. 손을 대지 마세요.", "#d97706", "■"),
    "LEADER_ALIGNING": ("리더 자동 정렬 중", "리더가 움직입니다 (약 2 초). 손을 대지 말고 정렬 완료 상태를 확인하세요.", "#dc2626", "!"),
    "TRANSITION": ("제어권 전환 중", "전환을 처리하는 중입니다. 잠시 기다리세요.", "#d97706", "…"),
    "HUMAN_READY": ("사람 제어 준비 완료", "정책 정지와 리더 정렬이 확인됐습니다. 리더를 손으로 잡은 다음 Tab 으로 교정을 시작하세요.", "#7c3aed", "손"),
    "CORRECTING": ("사람 교정 중 · 녹화 중", "지금 전문가 동작이 기록되고 있습니다. 복구 후 큐브를 집어 상자에 넣으세요.", "#dc2626", "●"),
    "RESULT": ("결과 확인", "방금 교정이 저장됐습니다. 기록된 결과를 확인하고, 원위치(Tab → r) 후 다음 판을 준비하세요.", "#0891b2", "@check"),
    "FAULT_LOCKED": ("오류로 잠김", "정책 추론 오류로 정책 명령을 끊었습니다. 정책은 이 세션에서 다시 시작되지 않습니다.", "#b91c1c", "@x"),
    "STOPPING": ("종료 처리 중", "정책을 멈추고 데이터를 정리하는 중입니다. 곧 터미널에 종료 선택이 나옵니다. 팔은 토크로 위치를 유지합니다.", "#4b5563", "■"),
    "END_MENU": ("종료 선택", "자동 원위치 복귀는 없습니다. 터미널에서 home / release / hold 중 하나를 입력하세요.", "#4b5563", "끝"),
    "ENDED": ("세션 종료됨", "제어 프로그램이 끝났습니다.", "#374151", "■"),
}

STEPS = ["정책 실행", "실패 징후 확인", "정지 요청", "안전 정지 확인", "리더 동기화", "인간 교정", "작업 완료", "결과 판정"]

TYPE_TITLES = {
    "R1": "큐브를 지나쳤습니다. 다시 맞춰 잡으세요.",
    "R2": "아직 잡을 위치가 아닙니다. 열린 채 정렬하세요.",
    "R2-O": "잡지 못했습니다. 다시 열고 맞춰 잡으세요.",
}

END_OPTIONS = {
    "home": ("시작 자세로 3 초 동안 이동한 뒤 토크 끄기", "팔이 움직입니다 — 경로에 손 · 물체가 없는지 먼저 확인"),
    "release": ("지금 자세에서 토크 끄기", "follower · 리더가 떨어질 수 있음 — 두 팔을 손으로 받친 뒤 입력"),
    "hold": ("토크 켠 채 프로그램 종료 (Enter 만 눌러도 hold)", "다음 연결 때 lerobot 이 토크를 끄므로 팔이 떨어질 수 있음 — 다음 연결 전에 받치기 · 발열 미검증"),
}


def _k(key, meaning, kind="ok"):
    """kind: ok (지금 쓸 키) · warn (주의해서) · blocked (눌러도 무시됨) · mark (기록용 표시 키)."""
    return {"key": key, "meaning": meaning, "kind": kind}


def result_from_marks(marks, frames=None, ended_during_correction=False):
    """교정 한 판의 표시 키 → 결과 칸. hil_qa.py 와 같은 규칙 (기본값 = 검토 필요, 자동 성공 없음)."""
    d = {"type": None, "recovery_done": None, "first_grasp": None, "final": None, "reset": False}
    for m in marks or []:
        if m.startswith("type_"):
            d["type"] = m[5:].replace("R2O", "R2-O")
        elif m in ("recovery_done", "recovery_end"):
            d["recovery_done"] = True
        elif m in ("first_grasp_ok", "first_grasp_fail") and d["first_grasp"] is None:
            d["first_grasp"] = "ok" if m.endswith("ok") else "fail"
        elif m in ("final_success", "final_fail"):
            d["final"] = "success" if m == "final_success" else "fail"
        elif m == "reset_segment":
            d["reset"] = True
    why = []
    if d["reset"]:
        why.append("원위치 구간(r)")
    if ended_during_correction:
        why.append("교정 도중 세션 종료")
    if d["final"] == "fail":
        why.append("최종 실패(f)")
    elif d["final"] is None and not d["reset"]:
        why.append("최종 결과 미입력")
    if frames is not None and frames < 15:
        why.append("15 frame 미만")
    d["ended_during_correction"] = bool(ended_during_correction)
    d["frames"] = frames
    d["exclusion"] = why
    if why:
        d["training"] = "제외 — " + " · ".join(why)
    elif d["type"] is None or d["recovery_done"] is None or d["first_grasp"] is None:
        d["training"] = "검토 필요 (유형 · 복구 · 첫 파지 표시 빠짐)"
    else:
        d["training"] = "변환 포함 조건 충족 (QA 확인 전)"
    return d


def derive(raw, now, stale_s=STALE_S):
    """raw (tap 사실값) → 화면 상태 dict. raw 가 None 이면 UNKNOWN."""
    if not raw:
        return _out("UNKNOWN", raw, reason="tap 없음")
    age = now - float(raw.get("t", 0))
    if raw.get("session") == "ended":
        return _out("ENDED", raw)
    if age > stale_s:
        return _out("UNKNOWN", raw, reason=f"상태가 {age:.1f} s 동안 갱신되지 않음")
    if raw.get("end_menu"):
        return _out("END_MENU", raw)
    if raw.get("session") == "teardown":
        return _out("STOPPING", raw)
    phase = raw.get("phase")
    fault = raw.get("fault")
    tr = raw.get("transition") if raw.get("in_transition") else None
    if raw.get("session") == "setup":
        return _out("STARTING", raw)
    if tr:
        if tr == ["autonomous", "paused"]:
            return _out("LEADER_ALIGNING" if raw.get("leader_torque") else "STOP_CONFIRMING", raw)
        return _out("TRANSITION", raw)
    if phase == "correcting":
        return _out("CORRECTING", raw)
    if fault:
        return _out("FAULT_LOCKED", raw)
    if phase == "autonomous":
        if raw.get("pending") == "pause_resume":
            return _out("STOP_REQUESTED", raw)
        return _out("POLICY_RUNNING", raw)
    if phase == "paused":
        last = raw.get("last_transition")
        if last == ["autonomous", "paused"]:
            # 모두 '확인된' 값이어야 함: RTC 스레드 꺼짐 = False (None = 모름 → 불가), 정지 뒤 정책 명령 없음, 리더 토크 켜짐 (정렬 끝)
            ok = raw.get("policy_active") is False and raw.get("policy_since_pause") is False and raw.get("leader_torque") is True
            settle = raw.get("since_transition_end")
            if ok and (settle is None or settle < SETTLE_S):
                return _out("LEADER_ALIGNING", raw, reason=f"정렬 이동 끝 — 멈춤 확인 중 ({settle or 0:.1f}/{SETTLE_S} s)")
            if ok:
                return _out("HUMAN_READY", raw)
            why = []
            if raw.get("policy_active") is not False:
                why.append("RTC 추론 스레드가 아직 켜져 있음" if raw.get("policy_active") else "RTC 추론 스레드 상태 모름")
            if raw.get("policy_since_pause") is not False:
                why.append("정지 뒤 정책 명령이 기록됨" if raw.get("policy_since_pause") else "정지 뒤 정책 명령 여부 모름")
            if raw.get("leader_torque") is not True:
                why.append("리더 정렬 · 토크 상태 미확인")
            return _out("UNCERTAIN", raw, reason=" · ".join(why))
        if last == ["correcting", "paused"]:
            ls = raw.get("last_saved") or {}
            if ls.get("reset"):
                return _out("POLICY_WAIT", raw)
            return _out("RESULT", raw)
        return _out("POLICY_WAIT", raw)
    return _out("UNCERTAIN", raw, reason=f"알 수 없는 phase {phase!r}")


def _keys(code, raw):
    fault = bool((raw or {}).get("fault"))
    if code in ("UNKNOWN", "UNCERTAIN", "STARTING", "TRANSITION", "STOPPING", "ENDED"):
        return [_k("—", "키를 누르지 마세요 (상태 확인 중)", "blocked")]
    if code == "POLICY_WAIT":
        return [_k("Space", "정책 시작 — 리더 토크가 꺼지므로 리더를 받친 뒤", "ok" if not fault else "blocked"),
                _k("Tab", "사람 녹화 시작 (원위치 · 정리용이면 r 표시) — 리더를 먼저 잡고", "warn"),
                _k("Esc", "세션 종료 → 종료 선택", "ok")]
    if code == "POLICY_RUNNING":
        return [_k("Space", "정지 요청 — 정책 멈춤 → 리더가 2 초 자동 정렬", "ok"),
                _k("Tab", "효과 없음 (정책 실행 중에는 무시됨)", "blocked"),
                _k("Esc", "세션 종료 (정책 멈춤 → 종료 선택)", "warn")]
    if code in ("STOP_REQUESTED", "STOP_CONFIRMING", "LEADER_ALIGNING"):
        return [_k("Space", "무시됨 (전환 중 · 직후 0.8 s)", "blocked"),
                _k("Tab", "누르지 마세요 — 정렬이 끝나는 즉시 리더 토크가 꺼집니다", "blocked"),
                _k("—", "리더에서 손을 떼고 기다리기", "warn")]
    if code == "HUMAN_READY":
        ks = [_k("Tab", "교정 시작 = 녹화 시작 · 리더 토크 꺼짐 (리더를 먼저 잡고 누르기)", "ok")]
        ks.append(_k("Space", "정책 재개 (권장 안 함 — 교정하거나 Esc)", "warn") if not fault else _k("Space", "무시됨 — 오류 뒤 재개 차단", "blocked"))
        ks.append(_k("Esc", "세션 종료 → 종료 선택", "ok"))
        return ks
    if code == "CORRECTING":
        return [_k("1 / 2 / 3", "유형 R1 / R2 / R2-O", "mark"), _k("m", "복구 완료", "mark"), _k("g / h", "첫 파지 성공 / 실패", "mark"),
                _k("b / f", "최종 (상자 안) 성공 / 실패", "mark"), _k("r", "원위치 구간 (학습 제외)", "mark"),
                _k("Tab", "교정 끝 = 저장 · 리더 토크 켜짐 (표시 키는 Tab 전에)", "ok"),
                _k("Space", "효과 없음 (교정 중에는 무시됨)", "blocked"),
                _k("Esc", "종료 — 이 교정은 미완성으로 저장 · 학습 제외", "warn")]
    if code == "RESULT":
        return [_k("Tab", "다음 녹화 (원위치면 바로 r) — 리더를 먼저 잡고", "ok"),
                _k("Space", "정책 재개 (권장 안 함: 원위치 뒤 새 판)" if not fault else "무시됨 — 오류 뒤 재개 차단", "warn" if not fault else "blocked"),
                _k("Esc", "세션 종료 → 종료 선택", "ok"),
                _k("표시 키", "지금 누르면 다음 교정 판에 기록됨", "blocked")]
    if code == "FAULT_LOCKED":
        return [_k("Space", "무시됨 — 오류 뒤 정책 재개 차단", "blocked"),
                _k("Tab", "사람 교정 · 원위치 녹화 가능 (리더를 먼저 잡고)", "warn"),
                _k("Esc", "세션 종료 → 종료 선택", "ok")]
    if code == "END_MENU":
        opts = (raw or {}).get("end_menu", {}).get("options", [])
        return [_k(o, END_OPTIONS[o][0], "warn") for o in opts] + [_k("(입력 위치)", "터미널 '선택 >' — 이 창이 아님", "warn")]
    return []


def _step(code, raw):
    """현재 단계 번호 (0 기반)와 끝난 단계 수."""
    marks = (raw or {}).get("marks_current") or []
    if code in ("POLICY_WAIT",):
        return 0
    if code == "POLICY_RUNNING":
        return 1
    if code == "STOP_REQUESTED":
        return 2
    if code in ("STOP_CONFIRMING", "TRANSITION"):
        return 3
    if code in ("LEADER_ALIGNING", "HUMAN_READY", "UNCERTAIN"):
        return 4
    if code == "CORRECTING":
        return 6 if any(m in ("final_success", "final_fail") for m in marks) else 5
    if code in ("RESULT", "END_MENU", "ENDED", "STOPPING"):
        return 7
    return None


def _warnings(code, raw):
    w = []
    raw = raw or {}
    if code in ("STOP_REQUESTED", "STOP_CONFIRMING", "LEADER_ALIGNING", "STARTING"):
        w.append(("danger", "리더가 토크로 약 2 초 동안 스스로 움직입니다 — 손 · 손가락을 떼세요 (끼임 위험, 실물 미검증)"))
    if code in ("HUMAN_READY", "FAULT_LOCKED", "RESULT"):
        w.append(("warn", "Tab 을 누르면 리더 토크가 꺼집니다 — 리더를 먼저 손으로 잡으세요 (떨어짐)"))
    if code == "POLICY_WAIT":
        w.append(("warn", "Space 로 정책을 시작하면 리더 토크가 꺼집니다 — 리더를 받쳐 두세요 (떨어짐)"))
    if code == "CORRECTING":
        w.append(("warn", "Tab(저장) 하면 리더 토크가 다시 켜져 그 자리에 고정됩니다 (Goal = 현재 위치로 맞춘 뒤)"))
        if raw.get("clamp_deg") is not None:
            w.append(("info", f"follower 명령은 present ±{raw['clamp_deg']:.0f}°/틱 으로 잘림 — 데이터에는 잘리기 전 리더 값이 저장됨 · 천천히"))
    if raw.get("fault"):
        f = raw["fault"]
        if f.get("handled"):
            q = f.get("rtc_qsize_before"), f.get("rtc_qsize_after")
            w.append(("danger", f"정책 오류 ({f.get('kind')}) — 정책 명령 차단 · RTC 큐 {q[0]} → {q[1]} 무효화 · 정책 재개 차단"))
        else:
            w.append(("danger", f"정책 오류 ({f.get('kind')}) — 정책 명령 차단됨 · RTC 큐 무효화 처리 중 (다음 제어 틱)"))
    if raw.get("follower_io_error"):
        w.append(("danger", f"follower 통신 오류 — {raw['follower_io_error'][:80]} · home 불가 · 필요하면 전원 차단"))
    if code in ("END_MENU", "ENDED", "STOPPING", "POLICY_RUNNING", "POLICY_WAIT", "RESULT", "FAULT_LOCKED"):
        w.append(("info", "자동 원위치 복귀 없음 — 종료 때 home / release / hold 를 직접 고름"))
    w.append(("info", "이 화면은 안전 장치가 아닙니다 · 키는 터미널 창에서 · 비상시 전원 차단"))
    return w


def _out(code, raw, reason=None):
    title, sentence, color, icon = STATES[code]
    raw = raw or {}
    d = {"code": code, "title": title, "sentence": sentence, "color": color, "icon": icon, "reason": reason,
         "recording": code == "CORRECTING", "keys": _keys(code, raw), "step": _step(code, raw), "warnings": _warnings(code, raw),
         "human_control_ok": code in ("HUMAN_READY", "CORRECTING"), "type": raw.get("type_current"),
         "frames": raw.get("frames_in_current"), "episodes_saved": raw.get("episodes_saved")}
    if code == "CORRECTING":
        d["current_result"] = result_from_marks(raw.get("marks_current"), frames=raw.get("frames_in_current"))
    ls = raw.get("last_saved")
    if ls:
        d["last_result"] = result_from_marks(ls.get("marks"), frames=ls.get("frames"), ended_during_correction=ls.get("ended_during_correction", False))
        d["last_result"]["episode"] = ls.get("episode")
    if code == "END_MENU":
        d["end_options"] = {o: END_OPTIONS[o] for o in raw.get("end_menu", {}).get("options", [])}
        d["end_unavailable"] = [] if "home" in raw.get("end_menu", {}).get("options", []) else ["home (follower 통신 오류)"]
    return d
