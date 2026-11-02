"""arm_filter.py · rollout_logged.py 오프라인 검증 (로봇·정책 없음).

1) 단위 시험      : ArmFilter / RolloutGuard 규칙
2) P0 일치 시험   : 새 ArmFilter(init=first_action) 를 P0 재생 명령 흐름에 걸어 P0 analyze_runs 의 ema50vc_arm 과 비교
3) 연결 시험      : rollout_logged.install() 로 바꿔 끼운 실제 send 경로를 가짜 ctx(엔진·로봇)로 돌림
                    → 보낸 값 = ArmFilter 직접 계산, dataset action = 보낸 값, 로그의 raw/out, 에피소드 reset, 감시 stop, RTC merge 훅
실행: PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python test_filter.py
"""

import glob
import importlib.util
import json
import sys
import tempfile
import threading
import types
from pathlib import Path

import numpy as np
import torch

EVAL = Path.home() / "so101_runs/main/redbox_all/eval"
P0 = Path.home() / "so101_runs/redbox_all/eval/p0_offline_replay"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))
from arm_filter import VMAX_TELEOP_P995, ArmFilter, RolloutGuard  # noqa: E402

KEYS = ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]
results = {}


def check(name, cond, detail=""):
    results[name] = {"pass": bool(cond), "detail": detail}
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))


# ---------------- 1) 단위 시험 ----------------
f = ArmFilter(KEYS, enabled=False)
x = np.array([1, 2, 3, 4, 5, 60.0])
check("disabled = identity", np.array_equal(f.step(x, x)[0], x))

f = ArmFilter(KEYS, init="first_action")
f.step(np.zeros(6))
y, info = f.step(np.array([1, 1, 1, 1, 1, 50.0]))
check("EMA α0.5 small step", np.allclose(y[:5], 0.5) and y[5] == 50.0, f"arm {y[:5]} grip {y[5]}")
y, info = f.step(np.array([9, 9, 9, 9, 9, 0.0]))  # ema = 0.5*9+0.5*0.5 = 4.75 → clip by vmax
exp = 0.5 + np.clip(4.75 - 0.5, -np.array(list(VMAX_TELEOP_P995.values())), np.array(list(VMAX_TELEOP_P995.values())))
check("velocity limit per joint", np.allclose(y[:5], exp) and info["vclip"].any(), f"{y[:5].round(3)} vs {exp.round(3)}")
check("gripper never filtered", y[5] == 0.0)
y, info = f.step(np.array([40, 0, 0, 0, 0, 0.0]))  # |40 - ema 4.75| > 10 → EMA 통과(reset), 속도 제한은 유지
check("ema reset passes x but velocity limit still applies", info["ema_reset"][0] and abs(y[0] - (exp[0] + VMAX_TELEOP_P995["shoulder_pan"])) < 1e-9, f"pan {y[0]:.3f}")

f = ArmFilter(KEYS, init="state")
state = np.array([0, -98, 96, 78, 90, 1.0])
y, info = f.step(np.array([10, -60, 60, 78, 90, 30.0]), state)
check("init=state: first command rate-limited from actual state", info["init"] == "state" and np.allclose(y[:5], state[:5] + np.clip(np.array([10, 38, -36, 0, 0]) * 0.5, -np.array(list(VMAX_TELEOP_P995.values())), np.array(list(VMAX_TELEOP_P995.values())))) and y[5] == 30.0, f"{y.round(2)}")
f.reset()
y, info = f.step(np.array([10, -60, 60, 78, 90, 30.0]), None)
check("reset → no state → first action passes", info["init"] == "first_action" and np.allclose(y, [10, -60, 60, 78, 90, 30]))
check("multiplier scales vmax", np.allclose(ArmFilter(KEYS, multiplier=2).vmax, np.array(list(VMAX_TELEOP_P995.values())) / 2))

stops = []
g = RolloutGuard(mode="stop", starve_ticks=15, on_stop=lambda k, m: stops.append(k))
g.on_command(np.zeros(6), np.zeros(6), np.arange(5))  # 에피소드 첫 명령 이후의 starve 규칙
for _ in range(14): g.on_starved()
check("guard starve: not before 15", stops == [])
g.on_starved()
check("guard starve: stop at 15 (once)", stops == ["starve"])
g.on_starved(); check("guard stop only once", stops == ["starve"])
g = RolloutGuard(mode="stop", stall_ticks=20, on_stop=lambda k, m: stops.append(k)); stops.clear()
arm = np.arange(5); s = np.zeros(6)
for t in range(25): g.on_command(np.array([20, 0, 0, 0, 0, 0.0]), s, arm)
check("guard stall: |cmd-state|>8 & not moving 20 ticks → stop", stops == ["stall"])
# 2026-10-19 실물 첫 시도 재현: 시작 대기 22틱(콜드 스타트 0.72 s) + 첫 merge real_delay 22 → 중단하면 안 됨
stops.clear(); g = RolloutGuard(mode="stop", starve_ticks=15, stale_ticks=30, startup_ticks=150, on_stop=lambda k, m: stops.append(k))
for _ in range(22): g.on_starved()
g.on_merge(22, 0, 0); g.on_merge(40, 0, 0)  # 첫 명령 전 merge 는 지연이 커도 stale 아님
check("startup wait (cold start 22 ticks) does not stop", stops == [] and g.events == [])
g.on_command(np.zeros(6), np.zeros(6), np.arange(5))
for _ in range(15): g.on_starved()
check("after first command, 15 starved ticks → stop", stops == ["starve"])
stops.clear(); g = RolloutGuard(mode="stop", startup_ticks=150, on_stop=lambda k, m: stops.append(k))
for _ in range(149): g.on_starved()
check("startup: not before 150 ticks", stops == [])
g.on_starved(); check("startup: stop at 150 ticks (5 s) without any action", stops == ["startup"])
g = RolloutGuard(mode="warn", stale_ticks=30, horizon=20, horizon_count=10)
g.on_command(np.zeros(6), np.zeros(6), np.arange(5)); g.on_merge(35, 30, 0)
for _ in range(10): g.on_delay_estimate(24)
check("guard stale & horizon events recorded (warn mode)", [e[1] for e in g.events] == ["stale", "horizon"])

# ---------------- 2) P0 일치 시험 ----------------
spec = importlib.util.spec_from_file_location("p0a", P0 / "analyze_runs.py")
sys.argv = ["x", str(P0 / "runs_lat1.55")]
p0a = importlib.util.module_from_spec(spec); spec.loader.exec_module(p0a)
maxdiff_arm, maxdiff_grip_raw, n_rows, grip_p0_clipped = 0.0, 0.0, 0, 0
for fz in sorted(glob.glob(str(P0 / "runs_lat1.55/run_*.npz"))):
    z = np.load(fz, allow_pickle=True)
    for sn in sorted({k.split("|")[0] for k in z.files}):
        c = z[f"{sn}|cmds"].astype(float)
        ref = p0a.FILTERS["ema50vc_arm"](c)
        valid = ~np.isnan(c).any(1)
        af = ArmFilter(KEYS, init="first_action")
        mine = np.full_like(c, np.nan)
        for t in np.where(valid)[0]:
            mine[t] = af.step(c[t])[0]
        maxdiff_arm = max(maxdiff_arm, float(np.nanmax(np.abs(mine[valid, :5] - ref[valid, :5]))))
        maxdiff_grip_raw = max(maxdiff_grip_raw, float(np.nanmax(np.abs(mine[valid, 5] - c[valid, 5]))))
        grip_p0_clipped += int((np.abs(ref[valid, 5] - c[valid, 5]) > 1e-6).sum())
        n_rows += int(valid.sum())
check("P0 equivalence: arm joints identical to P0 ema50vc_arm", maxdiff_arm < 1e-5, f"max |Δ| {maxdiff_arm:.2e}° over {n_rows} ticks")
check("gripper = raw (P0 variant velocity-clipped gripper)", maxdiff_grip_raw == 0.0, f"P0 clipped gripper on {grip_p0_clipped}/{n_rows} ticks ({100 * grip_p0_clipped / n_rows:.2f}%) — intended difference")

# ---------------- 3) 연결 시험 (실제 바꿔 끼운 send 경로) ----------------
sys.argv = ["rollout_logged.py"]
spec = importlib.util.spec_from_file_location("rollout_logged", EVAL / "rollout_logged.py")
rl = importlib.util.module_from_spec(spec); spec.loader.exec_module(rl)
import lerobot.rollout.inference.rtc as rtc_mod  # noqa: E402
import lerobot.rollout.strategies.core as core_mod  # noqa: E402
import lerobot.rollout.strategies.episodic as episodic_mod  # noqa: E402
from lerobot.policies.rtc import ActionQueue  # noqa: E402
from lerobot.policies.rtc.configuration_rtc import RTCConfig  # noqa: E402
from lerobot.utils.action_interpolator import ActionInterpolator  # noqa: E402

orig_send = core_mod.send_next_action
tmp = Path(tempfile.mkdtemp(dir=OUT))
import os  # noqa: E402
os.environ["ROLLOUT_FILTER_LOG"] = str(tmp / "filter_log.csv")
opts = {"arm_filter": True, "alpha": 0.5, "init": "state", "guard": "stop", "starve_ticks": 15, "stale_ticks": 30,
        "stall_ticks": 20, "horizon_count": 10, "startup_ticks": 150, "active": True}
st = rl.install(opts)
check("install patched core & episodic send_next_action", core_mod.send_next_action is not orig_send and episodic_mod.send_next_action is core_mod.send_next_action)

z = np.load(P0 / "runs_lat1.55/run_rtc_h20_exp_s5.npz", allow_pickle=True)
src = np.load(P0 / "runs_lat1.55/src_rollout_20k_t1.npz")
cmds = z["rollout_20k_t1|cmds"].astype(float); obs_t = z["rollout_20k_t1|obs_t"].astype(int)
states = src["state"][np.minimum(obs_t, len(src["state"]) - 1)]


class Engine:
    def __init__(self, seq): self.seq, self.i = seq, 0
    def get_action(self, obs_frame):
        a = self.seq[self.i]; self.i += 1
        return None if np.isnan(a).any() else torch.tensor(a, dtype=torch.float32)


sent = []
ev = threading.Event()
ctx = types.SimpleNamespace(
    policy=types.SimpleNamespace(inference=Engine(cmds)),
    data=types.SimpleNamespace(dataset_features={}, ordered_action_keys=KEYS),
    processors=types.SimpleNamespace(robot_action_processor=lambda t: dict(t[0])),
    hardware=types.SimpleNamespace(robot_wrapper=types.SimpleNamespace(send_action=lambda d: sent.append([d[k] for k in KEYS]))),
    runtime=types.SimpleNamespace(cfg=types.SimpleNamespace(inference=types.SimpleNamespace(rtc=types.SimpleNamespace(execution_horizon=20))), shutdown_event=ev))
interp = ActionInterpolator(1)
interp.reset()  # 에피소드 시작
recorded = []
for t in range(len(cmds)):
    obs_raw = {k: float(states[t, i]) for i, k in enumerate(KEYS)}
    d = episodic_mod.send_next_action({}, obs_raw, ctx, interp, None)
    if d is not None: recorded.append([d[k] for k in KEYS])
sent_arr = np.array(sent); recorded = np.array(recorded)
ref_f = ArmFilter(KEYS, init="state"); ref = []
for t in range(len(cmds)):
    if np.isnan(cmds[t]).any(): continue
    ref.append(ref_f.step(cmds[t], states[t])[0])
ref = np.array(ref)
check("wired path: sent == ArmFilter(direct)", sent_arr.shape == ref.shape and np.allclose(sent_arr, ref, atol=1e-4), f"{sent_arr.shape} max|Δ| {np.abs(sent_arr - ref).max():.2e}")
check("wired path: dataset action == sent command", np.allclose(recorded, sent_arr))
check("wired path: gripper sent == raw", np.allclose(sent_arr[:, 5], cmds[~np.isnan(cmds).any(1), 5], atol=1e-4))
replay_events = [e[1] for e in st["guard"].events]
results["open-loop replay guard events (expected artefact: recorded state does not follow replayed commands)"] = {"pass": True, "detail": str(replay_events)}
print("INFO open-loop replay guard events:", replay_events)
ev.clear(); st["guard"].reset(); st["guard"].events.clear()

# 로그 내용
import pandas as pd  # noqa: E402
st["log"].f.flush()
L = pd.read_csv(tmp / "filter_log.csv")
cm = L[L.event == "cmd"]
check("log has raw & out per command tick", len(cm) == len(sent_arr) and np.allclose(cm[[f"out_{k[:-4]}" for k in KEYS]].to_numpy(), sent_arr, atol=1e-3)
      and np.allclose(cm[[f"raw_{k[:-4]}" for k in KEYS]].to_numpy(), cmds[~np.isnan(cmds).any(1)], atol=1e-3), f"{len(cm)} cmd rows, {int((L.event == 'starved').sum())} starved rows")

# 에피소드 reset → 다음 첫 명령은 다시 실제 상태 기준
interp.reset()
ctx.policy.inference = Engine(np.array([[30, -60, 60, 70, 90, 20.0]] * 3))
obs_raw = {k: float(v) for k, v in zip(KEYS, [0, -98, 96, 78, 90, 1.0])}
d = episodic_mod.send_next_action({}, obs_raw, ctx, interp, None)
check("episode reset re-initialises from actual state", abs(d["shoulder_pan.pos"] - VMAX_TELEOP_P995["shoulder_pan"]) < 1e-6 and d["gripper.pos"] == 20.0, f"pan {d['shoulder_pan.pos']:.3f} grip {d['gripper.pos']}")

# 큐가 비면: 명령을 보내지 않고(로봇은 마지막 목표 유지), 첫 명령 이후 15틱째 stop 요청
interp.reset()
ctx.policy.inference = Engine(np.concatenate([np.full((22, 6), np.nan), [[0, -98, 96, 78, 90, 1.0]], np.full((40, 6), np.nan)]))
for t in range(22):
    episodic_mod.send_next_action({}, obs_raw, ctx, interp, None)
check("wired: episode-start wait of 22 ticks does not stop", not ev.is_set())
episodic_mod.send_next_action({}, obs_raw, ctx, interp, None)  # 첫 명령
n_sent0 = len(sent)
ctx.hardware.robot_wrapper = types.SimpleNamespace(send_action=lambda d: sent.append([d[k] for k in KEYS]))
for t in range(20):
    episodic_mod.send_next_action({}, obs_raw, ctx, interp, None)
check("starvation: no command sent, stop requested at tick 15", len(sent) == n_sent0 and ev.is_set(), f"sent during starvation {len(sent) - n_sent0}, shutdown_event={ev.is_set()}")

# RTC merge 훅 (실제 ActionQueue): 지연 35틱 merge → stale
ev.clear(); st["guard"].reset(); st["guard"].on_command(np.zeros(6), np.zeros(6), np.arange(5))
q = ActionQueue(RTCConfig(enabled=True, execution_horizon=20))
q.merge(torch.zeros(50, 6), torch.zeros(50, 6), 0, None)
for _ in range(35): q.get()
q.merge(torch.zeros(50, 6), torch.zeros(50, 6), 35, 0)
check("RTC merge hook: 35-tick chunk → stale stop", ev.is_set() and "stale" in [e[1] for e in st["guard"].events])
d = rtc_mod._estimate_rtc_delay(latency=0.8, time_per_step=1 / 30, mode="guided", training_max_delay=0, has_previous_actions=True)
check("RTC delay-estimate hook passes value through", d == 24)

# ---------------- 4) stall 감시 오경보: 실제 폐루프 데이터 ----------------
import pandas as pd  # noqa: E402,F811
def stall_trips(A, S):
    g = RolloutGuard(mode="warn", stall_ticks=20)
    for t in range(len(A)): g.on_command(A[t], S[t], np.arange(5))
    return [e[2] for e in g.events if e[1] == "stall"]
R = Path.home() / "so101_runs/main/redbox_all/eval/rollouts/20261019_091114_20k_t1_test1/dataset"
d = pd.concat(pd.read_parquet(f) for f in sorted(R.glob("data/*/*.parquet"))).sort_values("index")
trips = stall_trips(np.stack(d["action"]), np.stack(d["observation.state"]))
check("stall guard false alarms on real 20k rollout (closed loop, 2404 ticks)", len(trips) == 0, f"{len(trips)} trips {trips[:3]}")
tele = 0; frames = 0; detail = []
for fp in sorted(glob.glob(str(Path.home() / "so101_runs/main/redbox_all/dataset/data/*/*.parquet"))):
    dd = pd.read_parquet(fp, columns=["episode_index", "frame_index", "action", "observation.state"]).sort_values(["episode_index", "frame_index"])
    for e, gg in dd.groupby("episode_index"):
        tr = stall_trips(np.stack(gg["action"]), np.stack(gg["observation.state"])); frames += len(gg)
        if tr: tele += len(tr); detail.append((int(e), tr[0]))
check("stall guard on human teleop (384 eps, no clamp)", tele <= 5, f"{tele} trips in {frames} frames; first {detail[:3]}")

json.dump(results, open(OUT / "test_results.json", "w"), indent=1)
print(f"\n{sum(r['pass'] for r in results.values())}/{len(results)} passed")
