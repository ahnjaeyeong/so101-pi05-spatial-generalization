"""eval_ab_child.py 의 전송 경로 검증 (로봇·정책 없음).
A: 같은 RTC 출력 → lerobot 원래 core.send_next_action 과 보낸 명령·기록이 완전히 같아야 한다.
B: 같은 출력 → ArmFilter(검증된 필터) 를 직접 건 값과 같아야 한다.
훅: _estimate_rtc_delay · ActionQueue.merge 는 원래 함수와 같은 값.  보호 정지: 이후 전송 0, 판 끝 요청.
실행: EVAL_AB_STUDY=<mock study> PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python test_eval_ab_path.py
"""

import os
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
SS = Path.home() / "so101_runs/redbox_all/eval/speed_scaling"
run_dir = Path(tempfile.mkdtemp(dir=HERE)); (run_dir / "ctrl").mkdir()
os.environ["EVAL_AB_RUN_DIR"] = str(run_dir)
STUDY = Path(os.environ["EVAL_AB_STUDY"])
sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))

import lerobot.rollout.inference.rtc as rtc_mod  # noqa: E402
import lerobot.rollout.strategies.core as core_mod  # noqa: E402
import lerobot.rollout.strategies.episodic as episodic_mod  # noqa: E402
import lerobot.scripts.lerobot_rollout as lr  # noqa: E402
from lerobot.policies.rtc import ActionQueue  # noqa: E402
from lerobot.policies.rtc.configuration_rtc import RTCConfig  # noqa: E402
from lerobot.utils.action_interpolator import ActionInterpolator  # noqa: E402

ORIG_SEND, ORIG_EST, ORIG_MERGE = core_mod.send_next_action, rtc_mod._estimate_rtc_delay, ActionQueue.merge
import eval_ab_child as C  # noqa: E402
from arm_filter import ArmFilter  # noqa: E402

KEYS = C.KEYS
z = np.load(SS / "runs/run_rtc_h20_exp_s5.npz", allow_pickle=True)
cmds = z["rollout_rtcfilt|cmds"].astype(float); obs_t = z["rollout_rtcfilt|obs_t"].astype(int)
S_ = np.load(SS / "runs/src_rollout_rtcfilt.npz")["state"]; states = S_[np.minimum(obs_t, len(S_) - 1)]
stream = [None if np.isnan(c).any() else c for c in cmds]
res = {}


def check(n, c, d=""):
    res[n] = bool(c); print(("PASS " if c else "FAIL ") + n + (f" — {d}" if d else ""))


def run(send_fn, events=None):
    class Engine:
        def __init__(self): self.i = 0
        action_queue = None
        def get_action(self, f):
            a = stream[self.i] if self.i < len(stream) else None; self.i += 1
            return None if a is None else torch.tensor(a, dtype=torch.float32)
    sent = []
    ctx = types.SimpleNamespace(policy=types.SimpleNamespace(inference=Engine()),
                                data=types.SimpleNamespace(dataset_features={}, ordered_action_keys=KEYS),
                                processors=types.SimpleNamespace(robot_action_processor=lambda t: {k: float(v) for k, v in t[0].items()}),
                                hardware=types.SimpleNamespace(robot_wrapper=types.SimpleNamespace(send_action=lambda d: (sent.append([d[k] for k in KEYS]), d)[1])),
                                runtime=types.SimpleNamespace(shutdown_event=types.SimpleNamespace(is_set=lambda: False)))
    interp = ActionInterpolator(1); interp.reset(); rec = []
    for t in range(len(stream)):
        obs = {k: float(states[t, i]) for i, k in enumerate(KEYS)}
        d = send_fn({}, obs, ctx, interp, None)
        rec.append(None if d is None else [d[k] for k in KEYS])
    return np.array(sent), rec


class FakeRobot:
    def get_observation(self):
        o = {k: float(v) for k, v in zip(KEYS, states[0])}
        o["front"] = o["wrist"] = np.zeros((480, 640, 3), np.uint8)
        return o


A_off, A_off_rec = run(ORIG_SEND)
C.install(lr)
child_send = core_mod.send_next_action
check("install replaced send_next_action in core & episodic", child_send is not ORIG_SEND and episodic_mod.send_next_action is child_send)

C.S.begin({"trial": 9001, "condition": "A", "position": "K1", "dir": f"zz_pathtest_A_{run_dir.name}", "rep": 0}, 0, FakeRobot())
A_child, A_child_rec = run(child_send)
C.S.end("test")
check("A: child == official (sent commands)", A_off.shape == A_child.shape and np.array_equal(A_off, A_child), f"{A_child.shape}")
check("A: child == official (recorded actions & starved ticks)",
      all((x is None and y is None) or (x is not None and y is not None and np.array_equal(x, y)) for x, y in zip(A_off_rec, A_child_rec)))
tA = pd.read_csv(STUDY / "trials" / f"zz_pathtest_A_{run_dir.name}" / "ticks.csv")
cmdA = tA[tA.event == "cmd"]
check("A: ticks.csv cmd rows == sent, raw == cmd == sent", len(cmdA) == len(A_child)
      and np.allclose(cmdA[[f"raw_{j}" for j in C.JN]].to_numpy(), A_child, atol=1e-3)
      and np.allclose(cmdA[[f"cmd_{j}" for j in C.JN]].to_numpy(), A_child, atol=1e-3)
      and np.allclose(cmdA[[f"sent_{j}" for j in C.JN]].to_numpy(), A_child, atol=1e-3))

C.S.begin({"trial": 9002, "condition": "B", "position": "K1", "dir": f"zz_pathtest_B_{run_dir.name}", "rep": 0}, 1, FakeRobot())
B_child, _ = run(child_send)
C.S.end("test")
af = ArmFilter(KEYS, init="state"); ref = []
for t, a in enumerate(stream):
    if a is not None:
        ref.append(af.step(a, states[t])[0])
ref = np.array(ref)
check("B: child == ArmFilter(direct) on same stream", B_child.shape == ref.shape and np.allclose(B_child, ref, atol=1e-5), f"max|Δ| {np.abs(B_child - ref).max():.1e}")
check("B: gripper untouched", np.array_equal(B_child[:, 5], A_child[:, 5]))

rng = np.random.default_rng(1); ok = True
for _ in range(1000):
    kw = dict(latency=float(rng.uniform(0, 1.2)) * int(rng.integers(0, 2)), time_per_step=1 / 30, mode=str(rng.choice(["guided", "trained"])),
              training_max_delay=int(rng.integers(0, 30)), has_previous_actions=bool(rng.integers(0, 2)))
    ok &= rtc_mod._estimate_rtc_delay(**kw) == ORIG_EST(**kw)
check("hook: _estimate_rtc_delay == original (1000 random)", ok)
ok = True
for _ in range(200):
    cfg = RTCConfig(enabled=bool(rng.integers(0, 2)), execution_horizon=20); q1, q2 = ActionQueue(cfg), ActionQueue(cfg)
    for q in (q1, q2): ORIG_MERGE(q, torch.arange(300.).reshape(50, 6), torch.arange(300.).reshape(50, 6), 0, None)
    k = int(rng.integers(0, 50))
    for q in (q1, q2):
        for _ in range(k): q.get()
    new = torch.randn(50, 6); rd = int(rng.integers(0, 40)); ib = int(rng.integers(0, k + 1))
    q1.merge(new, new + 1, rd, ib); ORIG_MERGE(q2, new, new + 1, rd, ib)
    ok &= torch.equal(q1.queue, q2.queue) and q1.last_index == q2.last_index
check("hook: ActionQueue.merge == original (200 random)", ok)

# 보호 정지: guard 가 멈추면 그 뒤 전송 0, events exit_early
C.S.begin({"trial": 9003, "condition": "A", "position": "K2", "dir": f"zz_pathtest_P_{run_dir.name}", "rep": 0}, 2, FakeRobot())
C.S.events = {"exit_early": False}
sent_before = []
C.S.protect_stop("stall", "test stall")
P_child, P_rec = run(child_send)
C.S.end("test")
check("protect: no command sent after stop, exit_early requested", len(P_child) == 0 and all(r is None for r in P_rec) and C.S.events["exit_early"])
import shutil  # noqa: E402
for d in (STUDY / "trials").glob(f"zz_pathtest_*_{run_dir.name}"):
    shutil.rmtree(d)
print(f"\n{sum(res.values())}/{len(res)} passed")
