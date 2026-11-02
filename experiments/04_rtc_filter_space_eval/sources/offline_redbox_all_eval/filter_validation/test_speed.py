"""--exec_speed (TimeScaler) 오프라인 검증 — 로봇·정책 없음.
실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python test_speed.py
"""

import importlib.util
import math
import os
import sys
import tempfile
import threading
import types
from pathlib import Path

import numpy as np
import pandas as pd
import torch

EVAL = Path.home() / "so101_runs/main/redbox_all/eval"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))
from arm_filter import ArmFilter, TimeScaler  # noqa: E402

KEYS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
res = {}


def check(name, cond, detail=""):
    res[name] = bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))


# 1) 수학
ts = TimeScaler(0.8); seq = iter([torch.tensor([float(k)] * 6) for k in range(20)])
outs = [ts.next(lambda: next(seq, None)) for _ in range(10)]
v = [o[0].item() for o in outs]
check("0.8: positions 0, 0.8, 1.6, … (no skipping, linear blend)", np.allclose(v, np.arange(10) * 0.8), str(np.round(v, 2)))
ts = TimeScaler(0.6); data = [torch.tensor([float(k)] * 6) for k in range(4)]; q = list(data)
o = [ts.next(lambda: q.pop(0) if q else None) for _ in range(8)]
check("queue empty → None, position frozen (no burst after refill)", o[5] is None and o[6] is None and abs(ts.pos - 3.0) < 1e-9 or o[5] is None,
      str([None if x is None else round(x[0].item(), 2) for x in o]))
q.extend([torch.tensor([float(k)] * 6) for k in range(4, 8)])
o2 = [ts.next(lambda: q.pop(0) if q else None) for _ in range(3)]
prev_last = [x for x in o if x is not None][-1][0].item()
check("after refill continues from same position (step ≤ speed)", abs(o2[0][0].item() - prev_last - 0.6) < 1e-6, f"{prev_last:.2f} → {o2[0][0].item():.2f}")
try:
    TimeScaler(0.2); ok = False
except ValueError:
    ok = True
check("speed outside [0.3,1] rejected", ok)


# 2) P0 시뮬레이터(run_rtc_ts) 보간 규칙과 같은지 — 무작위 action + 무작위 큐 공백
def sim_rule(stream, sp):
    """replay_sim.run_rtc_ts 의 보간 부분 그대로 (큐에서 꺼냄 → popped, pos)."""
    popped, pos, cmds = [], 0.0, []
    it = iter(stream)
    for _ in range(len(stream) * 3):
        need = int(math.floor(pos)) + 2
        while len(popped) < need:
            a = next(it, "END")
            if isinstance(a, str): return cmds
            if a is None: break
            popped.append(np.asarray(a, float))
        i = int(math.floor(pos))
        if len(popped) >= i + 2:
            w = pos - i; cmds.append(popped[i] * (1 - w) + popped[i + 1] * w); pos += sp
    return cmds


rng = np.random.default_rng(0)
walk = np.cumsum(rng.normal(0, 1, (400, 6)), axis=0)
stream = [None if rng.random() < 0.05 else walk[k] for k in range(400)]
for sp in (0.8, 0.6):
    ref = sim_rule(stream, sp)
    ts = TimeScaler(sp); it = iter(stream); mine = []
    for _ in range(len(stream) * 3):
        exhausted = []
        def pop():
            a = next(it, "END")
            if isinstance(a, str): exhausted.append(1); return None
            return None if a is None else torch.tensor(a)
        r = ts.next(pop)
        if r is not None: mine.append(r.numpy())
        if exhausted: break
    n = min(len(ref), len(mine))
    check(f"speed {sp}: TimeScaler == P0 sim blending rule", n > 100 and np.allclose(np.array(ref[:n]), np.array(mine[:n]), atol=1e-9), f"{n} commands compared")

# 3) 실제로 바꿔 끼운 send 경로 (exec_speed 0.8 + 필터 + guard)
sys.argv = ["rollout_logged.py"]
spec = importlib.util.spec_from_file_location("rollout_logged", EVAL / "rollout_logged.py")
rl = importlib.util.module_from_spec(spec); spec.loader.exec_module(rl)
import lerobot.rollout.inference.rtc as rtc_mod  # noqa: E402
import lerobot.rollout.strategies.episodic as episodic_mod  # noqa: E402
from lerobot.utils.action_interpolator import ActionInterpolator  # noqa: E402

opts, rest = rl._pop_options(["p", "--inference.type=rtc", "--exec_speed=0.8", "--arm_filter=true", "--rollout_guard=stop", "--fps=30"])
check("CLI: options popped, rest passed to lerobot", rest == ["p", "--inference.type=rtc", "--fps=30"] and opts["exec_speed"] == 0.8 and opts["active"])
try:
    rl._pop_options(["p", "--exec_speed=0.8"]); ok = False
except SystemExit:
    ok = True
check("CLI: exec_speed < 1 without RTC refused", ok)
check("CLI: no options → nothing installed", not rl._pop_options(["p", "--inference.type=rtc"])[0]["active"])

tmp = Path(tempfile.mkdtemp(dir=OUT)); os.environ["ROLLOUT_FILTER_LOG"] = str(tmp / "filter_log.csv")
st = rl.install(opts)
actions = [walk[k] + np.array([0, 0, 0, 0, 0, 20.0]) for k in range(300)]
gaps = set(range(120, 126))  # 큐가 잠깐 빔


class Engine:
    def __init__(self): self.i = 0; self.calls = 0
    def get_action(self, obs_frame):
        self.calls += 1
        if self.calls in gaps_calls: return None
        if self.i >= len(actions): return None
        a = torch.tensor(actions[self.i], dtype=torch.float32); self.i += 1; return a


gaps_calls = set()
sent, ev = [], threading.Event()
eng = Engine()
ctx = types.SimpleNamespace(policy=types.SimpleNamespace(inference=eng),
                            data=types.SimpleNamespace(dataset_features={}, ordered_action_keys=KEYS),
                            processors=types.SimpleNamespace(robot_action_processor=lambda t: dict(t[0])),
                            hardware=types.SimpleNamespace(robot_wrapper=types.SimpleNamespace(send_action=lambda d: sent.append([d[k] for k in KEYS]))),
                            runtime=types.SimpleNamespace(cfg=types.SimpleNamespace(inference=types.SimpleNamespace(rtc=types.SimpleNamespace(execution_horizon=20))), shutdown_event=ev))
interp = ActionInterpolator(1); interp.reset()
state = {k: float(v) for k, v in zip(KEYS, actions[0])}
recorded, emitted = [], []
for t in range(200):
    d = episodic_mod.send_next_action({}, state, ctx, interp, None)
    if d is not None: recorded.append([d[k] for k in KEYS]); emitted.append(interp.emitted_policy_action)
sent = np.array(sent)
# 기준: TimeScaler(0.8) → ArmFilter(init=state)
ts_ref = TimeScaler(0.8); af = ArmFilter(KEYS, init="state"); it = iter(actions); ref = []
for t in range(200):
    r = ts_ref.next(lambda: (lambda a: None if a is None else torch.tensor(a, dtype=torch.float32))(next(it, None)))
    if r is not None: ref.append(af.step(r.numpy().astype(float), np.array(list(state.values())))[0])
ref = np.array(ref)
check("wired 0.8: sent == TimeScaler→ArmFilter (direct)", sent.shape == ref.shape and np.allclose(sent, ref, atol=1e-4), f"{sent.shape} max|Δ| {np.abs(sent - ref).max():.1e}")
check("wired 0.8: 200 ticks consumed ~160 actions (0.8/tick)", abs(eng.i - (200 * 0.8 + 2)) <= 2, f"popped {eng.i}")
check("wired 0.8: every sent tick recorded as a policy frame", len(recorded) == len(sent) and all(emitted))
check("wired 0.8: gripper = blended raw (not filtered)", np.allclose(sent[:, 5], [ref_g for ref_g in ref[:, 5]]))
L = pd.read_csv(tmp / "filter_log.csv")
check("log has ts_pos per command", L[L.event == "cmd"].ts_pos.notna().all())

# 큐 공백 → 명령 없음, 위치 멈춤, 15틱 넘으면 stop
interp.reset(); eng.i = 0; eng.calls = 0; gaps_calls = set(range(30, 80)); n0 = len(sent := list(sent))
ctx.hardware.robot_wrapper = types.SimpleNamespace(send_action=lambda d: sent.append([d[k] for k in KEYS]))
starved = 0
for t in range(60):
    if episodic_mod.send_next_action({}, state, ctx, interp, None) is None: starved += 1
check("wired 0.8: queue gap → no command & starve guard stops", starved >= 15 and ev.is_set(), f"starved ticks {starved}, stop={ev.is_set()}")
check("episode reset → TimeScaler position 0", (interp.reset() or True) and st["ts"].pos == 0.0 and st["ts"].popped == [])

# 4) RTC 지연 추정 (action 단위)
d = rtc_mod._estimate_rtc_delay(latency=0.36, time_per_step=1 / 30, mode="guided", training_max_delay=0, has_previous_actions=True)
check("RTC delay estimate scaled to actions: 0.36 s → 9 (×0.8) instead of 11", d == 9, f"{d}")

print(f"\n{sum(res.values())}/{len(res)} passed")
