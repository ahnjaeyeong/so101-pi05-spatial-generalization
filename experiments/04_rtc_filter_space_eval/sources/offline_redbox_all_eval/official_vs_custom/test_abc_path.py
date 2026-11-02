"""A = lerobot 원래 send_next_action, B = rollout_logged 경로(필터 없음), C = rollout_logged 경로(필터) 를 같은 엔진 출력으로 비교.
엔진 출력 = P0 RTC 시뮬레이터(실제 lerobot ActionQueue·guided RTC·정책)가 실제 실패 rollout(132729) 관측으로 만든 틱별 action
(speed_scaling/runs/run_rtc_h20_exp_s5.npz, 지연 ×1.75 = 실제 0.36 s 수준). 큐가 빈 틱은 None.
추가: 바꿔 끼운 RTC 훅(_estimate_rtc_delay, ActionQueue.merge) 이 기본 동작과 같은 값을 내는지 무작위 입력으로 비교.
로봇·정책 없음. 실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python test_abc_path.py
"""

import importlib.util
import os
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
EVAL = Path.home() / "so101_runs/main/redbox_all/eval"
SS = Path.home() / "so101_runs/redbox_all/eval/speed_scaling"
sys.path.insert(0, str(EVAL))
KEYS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]

import lerobot.rollout.inference.rtc as rtc_mod  # noqa: E402
import lerobot.rollout.strategies.core as core_mod  # noqa: E402
from lerobot.policies.rtc import ActionQueue  # noqa: E402
from lerobot.policies.rtc.configuration_rtc import RTCConfig  # noqa: E402
from lerobot.utils.action_interpolator import ActionInterpolator  # noqa: E402

ORIG_SEND = core_mod.send_next_action
ORIG_EST = rtc_mod._estimate_rtc_delay
ORIG_MERGE = ActionQueue.merge

z = np.load(SS / "runs/run_rtc_h20_exp_s5.npz", allow_pickle=True)
cmds = z["rollout_rtcfilt|cmds"].astype(float)
obs_t = z["rollout_rtcfilt|obs_t"].astype(int)
S = np.load(SS / "runs/src_rollout_rtcfilt.npz")["state"]
states = S[np.minimum(obs_t, len(S) - 1)]
# 시뮬레이터는 큐가 빈 틱에 직전 명령을 기록했다 → 같은 값 연속 + merge 전 = None 으로 복원은 불가하므로, 시작 NaN 만 None
stream = [None if np.isnan(c).any() else c for c in cmds]


def run(send_fn):
    class Engine:
        def __init__(self): self.i = 0
        def get_action(self, obs_frame):
            a = stream[self.i] if self.i < len(stream) else None
            self.i += 1
            return None if a is None else torch.tensor(a, dtype=torch.float32)
    sent, rec = [], []
    ctx = types.SimpleNamespace(policy=types.SimpleNamespace(inference=Engine()),
                                data=types.SimpleNamespace(dataset_features={}, ordered_action_keys=KEYS),
                                processors=types.SimpleNamespace(robot_action_processor=lambda t: {k: float(v) for k, v in t[0].items()}),
                                hardware=types.SimpleNamespace(robot_wrapper=types.SimpleNamespace(send_action=lambda d: sent.append([d[k] for k in KEYS]))),
                                runtime=types.SimpleNamespace(cfg=types.SimpleNamespace(inference=types.SimpleNamespace(rtc=types.SimpleNamespace(execution_horizon=20))),
                                                              shutdown_event=types.SimpleNamespace(set=lambda: None, is_set=lambda: False)))
    interp = ActionInterpolator(1); interp.reset()
    for t in range(len(stream)):
        obs = {k: float(states[t, i]) for i, k in enumerate(KEYS)}
        d = send_fn({}, obs, ctx, interp, None)
        rec.append(None if d is None else [d[k] for k in KEYS])
    return np.array(sent), rec


res = {}
def check(n, c, d=""):
    res[n] = bool(c); print(("PASS " if c else "FAIL ") + n + (f" — {d}" if d else ""))


A_sent, A_rec = run(ORIG_SEND)

sys.argv = ["rollout_logged.py"]
spec = importlib.util.spec_from_file_location("rollout_logged", EVAL / "rollout_logged.py")
rl = importlib.util.module_from_spec(spec); spec.loader.exec_module(rl)
tmp = Path(tempfile.mkdtemp(dir=HERE))
os.environ["ROLLOUT_FILTER_LOG"] = str(tmp / "B.csv")
stB = rl.install({"arm_filter": False, "alpha": 0.5, "init": "state", "guard": "warn", "starve_ticks": 15, "stale_ticks": 30,
                  "stall_ticks": 20, "horizon_count": 10, "startup_ticks": 150, "exec_speed": 1.0, "active": True})
B_send = core_mod.send_next_action
B_sent, B_rec = run(B_send)
check("A == B: 보낸 명령 (필터 없음, 감시 warn, 로그 켬)", A_sent.shape == B_sent.shape and np.array_equal(A_sent, B_sent), f"{A_sent.shape}, max|Δ| {np.abs(A_sent - B_sent).max() if A_sent.shape == B_sent.shape else 'shape'}")
check("A == B: dataset 에 기록되는 action / starved 틱", all((a is None and b is None) or (a is not None and b is not None and np.array_equal(a, b)) for a, b in zip(A_rec, B_rec)))

# 훅 통과 확인 (exec_speed 1.0)
rng = np.random.default_rng(0); ok = True
for _ in range(2000):
    kw = dict(latency=float(rng.choice([0.0, rng.uniform(0, 1.5)])), time_per_step=1 / 30, mode=str(rng.choice(["guided", "trained"])),
              training_max_delay=int(rng.integers(0, 30)), has_previous_actions=bool(rng.integers(0, 2)))
    ok &= rtc_mod._estimate_rtc_delay(**kw) == ORIG_EST(**kw)
check("RTC delay-estimate hook == original (2000 random inputs)", ok)
ok = True
for _ in range(300):
    cfg = RTCConfig(enabled=bool(rng.integers(0, 2)), execution_horizon=20)
    q1, q2 = ActionQueue(cfg), ActionQueue(cfg)
    for q in (q1, q2): q.merge(torch.arange(50 * 6.).reshape(50, 6), torch.arange(50 * 6.).reshape(50, 6) + 1, 0, None)
    k = int(rng.integers(0, 50))
    for q in (q1, q2):
        for _ in range(k): q.get()
    new = torch.randn(50, 6); rd = int(rng.integers(0, 40)); ib = int(rng.integers(0, k + 1))
    q1.merge(new, new + 1, rd, ib)                 # 바꿔 끼운 merge
    ORIG_MERGE(q2, new, new + 1, rd, ib)           # 원래 merge
    ok &= torch.equal(q1.queue, q2.queue) and torch.equal(q1.original_queue, q2.original_queue) and q1.last_index == q2.last_index
check("ActionQueue.merge hook == original (300 random merges)", ok)

os.environ["ROLLOUT_FILTER_LOG"] = str(tmp / "C.csv")
stB["filter"].enabled = True; stB["filter"].reset()   # 같은 설치에서 필터만 켬 = C
C_sent, C_rec = run(B_send)
np.savez_compressed(HERE / "abc_streams.npz", A=A_sent, B=B_sent, C=C_sent, states=states, cmds=cmds)
d = np.abs(C_sent - B_sent)
print("B vs C |Δ| 평균 (°):", np.round(d.mean(0), 2), " p99:", np.round(np.percentile(d, 99, axis=0), 2), " 최대:", np.round(d.max(0), 2))
check("C: gripper == B (필터가 그리퍼를 건드리지 않음)", np.array_equal(C_sent[:, 5], B_sent[:, 5]))
print(f"\n{sum(res.values())}/{len(res)} passed")
