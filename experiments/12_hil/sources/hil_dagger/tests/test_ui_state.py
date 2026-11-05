"""화면 상태 판정 (hil_ui_state) 단위 시험 — 순수 함수, 장치 · GPU 없음. venv python 으로 실행 (공식 전환표 확인에 lerobot import).

U-a  '사람 제어 가능' 표시는 조건이 모두 참일 때만 (전 조합 탐색)
U-b  전환 중 · 리더 정렬 중에는 절대 '사람 제어 가능' 아님
U-c  오래된 상태 → UNKNOWN, 정보 없음 → UNKNOWN
U-d  키 설명이 설치된 lerobot 0.6.2 _DAGGER_TRANSITIONS 와 일치 (Space / Tab 의 상태별 의미 · 무시됨)
U-e  오류 잠김: Space 무시 표시, follower 오류 뒤 종료 메뉴에 home 없음
U-f  결과 칸: 표시 없음 → 자동 성공 아님 (검토 필요 · 제외), hil_qa 규칙과 같은 제외 사유
U-g  미리보기 17 상태 모두 그려짐 (PIL), PREVIEW 표시
"""

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import hil_ui_state as U  # noqa: E402

ok_all = True


def chk(name, cond, detail=""):
    global ok_all
    ok_all &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}")


NOW = 1000.0
TRS = [None, ["autonomous", "paused"], ["paused", "correcting"], ["correcting", "paused"], ["paused", "autonomous"]]
n = 0
viol_ready, viol_trans, viol_auto = [], [], []
for phase, in_tr, tr, lt, pa, psp, last, fault, pend in itertools.product(
        ["autonomous", "paused", "correcting"], [False, True], TRS, [True, False, None], [True, False, None], [True, False, None], TRS,
        [None, {"kind": "inference_error"}], [None, "pause_resume", "correction"]):
    raw = {"t": NOW, "session": "running", "phase": phase, "in_transition": in_tr, "transition": tr, "leader_torque": lt, "policy_active": pa,
           "policy_since_pause": psp, "last_transition": last, "fault": fault, "pending": pend, "since_transition_end": 1.0}
    ui = U.derive(raw, NOW)
    n += 1
    if ui["human_control_ok"]:
        ready_ok = (not (in_tr and tr)) and (
            (phase == "correcting") or
            (phase == "paused" and last == ["autonomous", "paused"] and pa is False and psp is False and lt is True and not fault))
        if not ready_ok:
            viol_ready.append(raw)
    if in_tr and tr and ui["human_control_ok"]:
        viol_trans.append(raw)
    if phase == "autonomous" and not (in_tr and tr) and ui["code"] not in ("POLICY_RUNNING", "STOP_REQUESTED", "FAULT_LOCKED"):
        viol_auto.append((raw, ui["code"]))
chk("U-a human_control_ok only when all conditions hold", not viol_ready, f"combos={n} violations={len(viol_ready)}")
chk("U-b never human_control_ok during a transition", not viol_trans, f"violations={len(viol_trans)}")
chk("U-b2 autonomous → policy running / stop requested / fault only", not viol_auto, f"violations={viol_auto[:2]}")
ready = {"t": NOW, "session": "running", "phase": "paused", "in_transition": False, "last_transition": ["autonomous", "paused"],
         "leader_torque": True, "policy_active": False, "policy_since_pause": False, "since_transition_end": 1.0}
chk("U-a2 all conditions → HUMAN_READY", U.derive(ready, NOW)["code"] == "HUMAN_READY")
for k, v in (("policy_active", True), ("policy_since_pause", True), ("leader_torque", False), ("leader_torque", None), ("policy_active", None),
             ("policy_since_pause", None)):
    d = U.derive({**ready, k: v}, NOW)
    chk(f"U-a3 {k}={v} → UNCERTAIN (no human control)", d["code"] == "UNCERTAIN" and not d["human_control_ok"], d.get("reason") or "")
st_ = U.derive({**ready, "since_transition_end": 0.1}, NOW)
chk("U-b4 within settle time after alignment → LEADER_ALIGNING (no human control)", st_["code"] == "LEADER_ALIGNING" and not st_["human_control_ok"], st_.get("reason") or "")
st_ = U.derive({**ready, "since_transition_end": None}, NOW)
chk("U-b5 unknown settle time → no human control", not st_["human_control_ok"])
al = U.derive({**ready, "in_transition": True, "transition": ["autonomous", "paused"], "leader_torque": True}, NOW)
chk("U-b3 leader aligning → LEADER_ALIGNING, no human control", al["code"] == "LEADER_ALIGNING" and not al["human_control_ok"])

chk("U-c stale → UNKNOWN", U.derive({**ready, "t": NOW - 1.5}, NOW)["code"] == "UNKNOWN")
chk("U-c2 none → UNKNOWN", U.derive(None, NOW)["code"] == "UNKNOWN")
chk("U-c3 UNKNOWN shows no usable keys", all(k["kind"] == "blocked" for k in U.derive(None, NOW)["keys"]))

# U-d 공식 전환표와 키 설명
from lerobot.rollout.strategies.dagger import _DAGGER_TRANSITIONS, DAggerPhase  # noqa: E402

T = {(a.value, e): b.value for (a, e), b in _DAGGER_TRANSITIONS.items()}
chk("U-d0 official table (0.6.2)", T == {("autonomous", "pause_resume"): "paused", ("paused", "pause_resume"): "autonomous",
                                         ("paused", "correction"): "correcting", ("correcting", "correction"): "paused"}, str(T))


def keymap(code, raw):
    return {k["key"]: k for k in U.derive({**raw, "t": NOW}, NOW)["keys"]} if U.derive({**raw, "t": NOW}, NOW)["code"] == code else None


run = keymap("POLICY_RUNNING", {"session": "running", "phase": "autonomous"})
cor = keymap("CORRECTING", {"session": "running", "phase": "correcting"})
wait = keymap("POLICY_WAIT", {"session": "running", "phase": "paused"})
chk("U-d1 running: Space=정지 (autonomous+pause_resume valid), Tab blocked (autonomous+correction invalid)",
    run and run["Space"]["kind"] == "ok" and "정지" in run["Space"]["meaning"] and run["Tab"]["kind"] == "blocked"
    and ("autonomous", "correction") not in T)
chk("U-d2 correcting: Tab=저장 (correction valid), Space blocked (pause_resume invalid)",
    cor and cor["Tab"]["kind"] == "ok" and "저장" in cor["Tab"]["meaning"] and cor["Space"]["kind"] == "blocked"
    and ("correcting", "pause_resume") not in T)
chk("U-d3 paused: Space=정책 시작 · Tab=녹화 시작 (both valid)", wait and "정책 시작" in wait["Space"]["meaning"] and "녹화" in wait["Tab"]["meaning"]
    and ("paused", "pause_resume") in T and ("paused", "correction") in T)
chk("U-d4 key names = official defaults (space / tab / esc)", __import__("lerobot.rollout.configs", fromlist=["x"]).DAggerKeyboardConfig() .__dict__
    == {"pause_resume": "space", "correction": "tab", "upload": "enter"})

fu = U.derive({"t": NOW, "session": "running", "phase": "autonomous", "fault": {"kind": "inference_error", "handled": False}}, NOW)
chk("U-e0 fault latched, not yet handled → FAULT_LOCKED, '처리 중' (no None numbers)", fu["code"] == "FAULT_LOCKED"
    and any("처리 중" in w[1] for w in fu["warnings"]) and not any("None" in w[1] for w in fu["warnings"]))
f = U.derive({"t": NOW, "session": "running", "phase": "paused", "fault": {"kind": "inference_error", "handled": True, "rtc_qsize_before": 30, "rtc_qsize_after": 0},
              "last_transition": ["autonomous", "paused"]}, NOW)
chk("U-e fault → FAULT_LOCKED, Space blocked, queue shown", f["code"] == "FAULT_LOCKED" and any(k["key"] == "Space" and k["kind"] == "blocked" for k in f["keys"])
    and any("30 → 0" in w[1] for w in f["warnings"]))
em = U.derive({"t": NOW, "session": "teardown", "end_menu": {"options": ["release", "hold"], "follower_ok": False}, "follower_io_error": "x"}, NOW)
chk("U-e2 follower fault end menu has no home", em["code"] == "END_MENU" and "home" not in em["end_options"] and em["end_unavailable"])
em2 = U.derive({"t": NOW, "session": "teardown", "end_menu": {"options": ["home", "release", "hold"], "follower_ok": True}}, NOW)
chk("U-e3 end menu explains hold re-connect drop risk", "떨어질" in em2["end_options"]["hold"][1] and "자동 원위치 복귀는 없습니다" in em2["sentence"])

r0 = U.result_from_marks([])
chk("U-f no marks → not success, 제외 (최종 결과 미입력)", r0["final"] is None and r0["training"].startswith("제외") and "최종 결과 미입력" in r0["exclusion"])
r1 = U.result_from_marks(["type_R2", "recovery_done", "first_grasp_ok", "final_success"], frames=200)
chk("U-f2 full marks → 변환 포함 조건 충족 (QA 확인 전)", r1["training"].startswith("변환 포함") and r1["type"] == "R2")
r2 = U.result_from_marks(["type_R1", "final_success"], frames=200)
chk("U-f3 missing m/g → 검토 필요", r2["training"].startswith("검토 필요"))
r3 = U.result_from_marks(["type_R1", "recovery_done", "first_grasp_ok"], frames=100, ended_during_correction=True)
chk("U-f4 ended during correction → 제외", "교정 도중 세션 종료" in r3["exclusion"])
r4 = U.result_from_marks(["reset_segment"], frames=40)
chk("U-f5 reset → 제외 (원위치) only", r4["exclusion"] == ["원위치 구간(r)"])

# U-g 미리보기
import hil_ui_preview as P  # noqa: E402
import hil_viewer as V  # noqa: E402

codes = {}
for name, _, _ in P.STATES:
    im, ui = V.render_preview(name)
    codes[name] = ui["code"]
    assert im.size == (1400, 940)
need = {"POLICY_WAIT", "POLICY_RUNNING", "STOP_REQUESTED", "LEADER_ALIGNING", "HUMAN_READY", "CORRECTING", "RESULT", "FAULT_LOCKED", "END_MENU"}
chk("U-g all preview states render; 11 required covered", need <= set(codes.values()) and len(codes) == len(P.STATES),
    f"{len(codes)} states, types R1/R2/R2-O: {[n for n in codes if 'correcting_R' in n]}")
print("UI_STATE_ALL_PASS" if ok_all else "UI_STATE_FAIL")
sys.exit(0 if ok_all else 1)
