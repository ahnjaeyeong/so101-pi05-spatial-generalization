"""(11-05) 배치 창 키 → eval_ui 시험 (로봇 · 카메라 · GPU 없음, 창 없음).

K1 viewer.key_bytes → eval_ui.tokens: → next · ← redo · Esc quit · Enter enter · p/P/ㅔ P · f/F/ㄹ F · Ctrl+C ctrl_c · 그 밖 None
K2 eval_ui.run_child 를 진짜로 돌린다 (가짜 자식 = MARK 줄을 찍고 받은 키 바이트를 기록하는 작은 python, stdin 은 pty).
   viewer.send_key 로 FIFO 에 키를 넣어 터미널 키와 같은 처리인지 본다:
   READY 에서 → → 자식이 'n' 받음 · REC 중 P → 상태 파일 verdict P · RESET 에서 판정 없이 → 는 거부 (자식에게 안 감, 안내 note)
   · F 로 바꾼 뒤 → → 'n' · 상태 파일에 단계 · 판 번호 · 안내 · verdicts · 끝나면 FIFO · 상태 파일 삭제
K3 viewer.compose(ui=…) 가 창 없이 그려짐 (PNG) · 계획 목록에 판정 표시 · 키 도움말 줄
PASS/FAIL 줄, 마지막 ALL_PASS / SOME_FAIL.
"""
import json
import os
import pty
import subprocess
import sys
import tempfile
import time
from pathlib import Path

S_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/r2_grasp_diagnostic/scripts"))
import eval_ui as EU  # noqa: E402
import r2_place_viewer as V  # noqa: E402

ok = True


def chk(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}", flush=True)


# ---- K1
cases = [("Right", False, "", ["next"]), ("Left", False, "", ["redo"]), ("Escape", False, "", ["quit"]), ("Return", False, "", ["enter"]),
         ("p", False, "p", ["P"]), ("P", False, "P", ["P"]), ("Hangul_E", False, "ㅔ", ["P"]), ("f", False, "f", ["F"]), ("F", False, "F", ["F"]),
         ("Hangul_Rieul", False, "ㄹ", ["F"]), ("c", True, "", ["ctrl_c"])]
bad = []
for ks, ctrl, ch, want in cases:
    b = V.key_bytes(ks, ctrl, ch)
    got = EU.tokens(b) if b is not None else None
    if got != want:
        bad.append((ks, ctrl, ch, got, want))
none_ok = all(V.key_bytes(k, False, c) is None for k, c in (("a", "a"), ("space", " "), ("Up", ""), ("n", "n"), ("q", "q"))) and V.key_bytes("p", True) is None
chk("K1_key_mapping_same_as_terminal", not bad and none_ok, f"bad={bad} others_none={none_ok}")

# ---- K2 run_child + FIFO
td = Path(tempfile.mkdtemp(prefix="uikeys_"))
child = td / "fake_child.py"
child.write_text(r'''
import os, sys, time, tty
tty.setraw(0)
M = "[eval_ui]"
log = open(sys.argv[1], "a")
def got(timeout):
    t = time.time()
    while time.time() - t < timeout:
        import select
        r, _, _ = select.select([0], [], [], 0.1)
        if r:
            b = os.read(0, 64)
            log.write(repr(b) + "\n"); log.flush()
            return b
    return b""
print(M, "READY 0", flush=True)
b = got(20)                          # → (FIFO) 기다림
print(M, "START 0", flush=True)
time.sleep(float(sys.argv[2]))       # 판 실행 중 (P 를 받음 — 부모만 처리, 자식에겐 안 옴)
print("Reset the environment", flush=True)
b2 = got(20)                         # RESET 에서 → (판정 뒤)
print(M, "SAVED 0 300", flush=True)
time.sleep(0.5)
''')
harness = td / "harness.py"
harness.write_text(r'''
import os, sys, json
sys.path.insert(0, os.path.expanduser("~/so101_boxpick/scripts"))
import eval_ui as EU
class R:
    def write_results(self, ui):
        pass
ui = EU.UI(R())
ui.state_path = sys.argv[1]
st = EU.run_child([sys.executable, sys.argv[3], sys.argv[4], "6"], dict(os.environ), sys.argv[5], ui, key_fifo=sys.argv[2])
json.dump({"status": st, "verdict": ui.verdict, "saved": ui.saved}, open(sys.argv[6], "w"))
''')
fifo, state, glog, clog, res = f"/dev/shm/eval_ui_keys_test_{os.getpid()}", f"/dev/shm/eval_ui_state_test_{os.getpid()}.json", td / "got.log", td / "console.log", td / "res.json"
master, slave = pty.openpty()
pr = subprocess.Popen([sys.executable, str(harness), state, fifo, str(child), str(glog), str(clog), str(res)], stdin=slave, stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))


def st():
    try:
        return json.load(open(state))
    except Exception:
        return {}


def wait(pred, timeout=15):
    t = time.time()
    while time.time() - t < timeout:
        s = st()
        if pred(s):
            return s
        time.sleep(0.05)
    return st()


steps = {}
s = wait(lambda s: s.get("state") == EU.READY)
steps["ready"] = s.get("state")
steps["send_next"] = V.send_key(fifo, V.key_bytes("Right"))
s = wait(lambda s: s.get("state") == EU.REC)
steps["rec"] = (s.get("state"), s.get("episode"))
V.send_key(fifo, V.key_bytes("Hangul_E", False, "ㅔ"))  # P
s = wait(lambda s: s.get("verdict") == "P")
steps["verdict_P"] = s.get("verdict")
s = wait(lambda s: s.get("state") == EU.RESET)
V.send_key(fifo, V.key_bytes("f", False, "f"))  # F 로 바꿈
s = wait(lambda s: s.get("verdict") == "F")
steps["verdict_F"] = s.get("verdict")
steps["banner"] = s.get("banner")
V.send_key(fifo, V.key_bytes("Right"))
s = wait(lambda s: s.get("saved") == [0])
steps["saved"] = s.get("saved")
pr.wait(timeout=30)
os.close(master)
os.close(slave)
got = glog.read_text().splitlines() if glog.exists() else []
R = json.load(open(res)) if res.exists() else {}
chk("K2a_ready_next_from_window", steps["send_next"][0] and got[:1] == ["b'n'"], f"{steps['ready']} send={steps['send_next']} child got={got}")
chk("K2b_P_then_F_recorded_in_eval_ui", steps["verdict_P"] == "P" and steps["verdict_F"] == "F" and R.get("verdict") == {"0": "F"} or R.get("verdict") == {0: "F"},
    f"steps={steps} final verdict={R.get('verdict')}")
chk("K2c_child_got_only_next_bytes", got == ["b'n'", "b'n'"], f"child got={got}")
chk("K2d_state_and_fifo_removed", not os.path.exists(state + ".tmp") and R.get("status") == 0, f"status={R.get('status')}")
# K2e: RESET 에서 판정 없이 → 는 거부 (eval_ui on_keys 규칙) — UI 만으로 확인
ui = EU.UI(type("R", (), {"write_results": lambda self, u: None})())
ui.state_path = str(td / "st2.json")
ui.out = lambda s: None
ui.episode, ui.state = 1, EU.RESET
sent = ui.on_keys(V.key_bytes("Right"))
s2 = json.load(open(ui.state_path))
chk("K2e_next_without_verdict_refused", sent == b"" and "P(성공)" in (s2.get("note") or ""), f"sent={sent!r} note={s2.get('note')}")
sent = ui.on_keys(V.key_bytes("c", True))
chk("K2f_ctrl_c_from_window_forwarded", sent == b"\x03" and ui.interrupted, f"sent={sent!r}")

# ---- K3 compose
from PIL import Image  # noqa: E402
plan = [{"ep": "8", "label": "K1_L30", "known": "known", "group": "K", "x_cm": "-8.5", "y_cm": "26.5", "angle_code": "L30", "angle_deg": "30", "angle_text": "L30", "ref_K": "K1", "from_ref": ""},
        {"ep": "9", "label": "U2_L30", "known": "unknown", "group": "U", "x_cm": "-8.5", "y_cm": "-7.0", "angle_code": "L30", "angle_deg": "30", "angle_text": "L30", "ref_K": "K3", "from_ref": "오른쪽 3.5 cm"}]
stj = {"phase": "RESET", "plan": plan, "current": plan[0], "current_n": 0, "next_if_saved": plan[1], "next_n": 1}
uij = {"state": "RESET", "episode": 0, "verdict": "P", "verdicts": {"0": "P"}, "banner": ["↺ 초기화 — ep 0 판정 성공", "다음 판 →"], "note": ""}
try:
    im = V.compose(None, None, stj, None, ui=uij, keyinfo="P 보냄")
    p = td / "viewer.png"
    im.save(p)
    good = isinstance(im, Image.Image) and im.size[1] == V.H_FRONT + 150 + V.N_LINES * 26 + 10
    chk("K3_compose_with_ui_state", good, f"size={im.size} png={p}")
except Exception as e:
    chk("K3_compose_with_ui_state", False, f"{type(e).__name__}: {e}")
print("ALL_PASS" if ok else "SOME_FAIL")
sys.exit(0 if ok else 1)
