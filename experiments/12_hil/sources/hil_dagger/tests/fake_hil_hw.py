"""가짜 SO-101 follower + 가짜 SO-101 leader + stub π0.5 (시험 전용, 2026-11-04).

실물 차단 (memory: mock-hardware-isolation):
  1) FeetechMotorsBus.connect · OpenCVCamera.connect 를 막는다 (부르면 RuntimeError).
  2) follower/leader 는 SOFollower.__new__ / SOLeader.__new__ 로 만들고 (진짜 __init__ 안 부름 → 진짜 bus·camera 객체 없음)
     bus · cameras 를 가짜로 넣는다.
  3) port · camera 경로가 /nonexistent/hil_fake_* 가 아니면 거부. connect 직전 assert (가짜 클래스인지).
  4) GPU 차단: CUDA_VISIBLE_DEVICES="" 는 호출 쪽에서 설정. stub 정책은 torch 텐서만 CPU 에서 만든다 (모델 가중치 로드 없음).
  5) 키보드: DISPLAY/WAYLAND_DISPLAY 를 지운 뒤 stdin 이 TTY 가 아니면 lerobot 키 리스너는 None → 사용자 키 입력이 시험에 들어오지 않음.

lerobot 의 SOFollower.get_observation / send_action (max_relative_target clamp 포함), SOLeader.get_action / send_feedback /
enable_torque / disable_torque, RTCInferenceEngine, ActionQueue, DAggerStrategy 는 설치된 0.6.2 코드를 그대로 쓴다.
"""

from __future__ import annotations

import sys
import threading
import time
import types

import numpy as np
import torch

J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
FOLLOWER_PORT = "/nonexistent/hil_fake_follower"
LEADER_PORT = "/nonexistent/hil_fake_leader"
FAKE_CAMS = ("/nonexistent/hil_fake_front", "/nonexistent/hil_fake_wrist")
REST = {"shoulder_pan": 2.0, "shoulder_lift": -100.0, "elbow_flex": 95.0, "wrist_flex": 66.0, "wrist_roll": 0.0, "gripper": 1.0}
PAN_LIMIT = 109.0
TICK_HZ = 30.0
FOLLOW_GAIN = 0.3  # Present 가 Goal 쪽으로 틱당 30 % (r2 fake 와 같음)

REC = {"follower_writes": [], "leader_events": [], "engine_events": [], "chunks": [], "leader_reads": [], "policy_fail_t": [],
       "t0": time.perf_counter()}
HOLD = {"strategy": None, "engine": None, "robot": None, "leader": None, "leader_bus": None, "follower_bus": None}


def now():
    return time.perf_counter() - REC["t0"]


def _phase():
    s = HOLD["strategy"]
    return None if s is None else s._events.phase.value


def _origin():
    """쓰기 호출 출처: policy(send_next_action) / slide / home / teleop / hold / other."""
    f = sys._getframe(2)
    names = []
    while f is not None and len(names) < 40:
        names.append(f.f_code.co_name)
        f = f.f_back
    if "send_next_action" in names:
        return "policy"
    if "_handle_fault" in names:
        return "fault_hold"
    if "follower_smooth_move_to" in names:
        return "slide"
    if "return_to_initial_position" in names:
        return "home"
    ph = _phase()
    if ph == "correcting":
        return "teleop"
    if ph == "paused":
        return "hold"
    return "other:" + ">".join(names[:4])


class FakeFollowerBus:
    is_calibrated = True

    def __init__(self, init):
        self.motors = {j: types.SimpleNamespace(id=i + 1) for i, j in enumerate(J)}
        self.present = dict(init)
        self.goal = dict(init)
        self.connected = False
        self.t_last = time.perf_counter()
        self.fail_writes = False
        self.lock = threading.Lock()

    @property
    def is_connected(self):
        return self.connected

    def connect(self, *a, **k):
        self.connected = True

    def disconnect(self, disable_torque=True, *a, **k):
        REC["follower_writes"].append({"t": now(), "kind": "disconnect", "torque_off": bool(disable_torque)})
        self.connected = False

    def _advance(self):
        t = time.perf_counter()
        n = int((t - self.t_last) * TICK_HZ)
        if n <= 0:
            return
        self.t_last += n / TICK_HZ
        for _ in range(min(n, 90)):
            for j in J:
                self.present[j] += FOLLOW_GAIN * (self.goal[j] - self.present[j])
            self.present["shoulder_pan"] = float(np.clip(self.present["shoulder_pan"], -PAN_LIMIT, PAN_LIMIT))

    def sync_read(self, what, num_retry=0):
        assert what == "Present_Position"
        with self.lock:
            self._advance()
            self.last_read = dict(self.present)
            return dict(self.present)

    def sync_write(self, what, vals):
        assert what == "Goal_Position"
        if self.fail_writes:
            raise ConnectionError("fake follower: injected write failure")
        with self.lock:
            self._advance()
            self.goal.update({k: float(v) for k, v in vals.items()})
            REC["follower_writes"].append({"t": now(), "kind": "write", "origin": _origin(), "phase": _phase(),
                                           "thread": threading.current_thread().name,
                                           "goal": dict(self.goal), "present": dict(self.present),
                                           "present_read": dict(getattr(self, "last_read", self.present)),
                                           "leader_torque": None if HOLD["leader_bus"] is None else HOLD["leader_bus"].torque,
                                           "mrt": None if HOLD["robot"] is None else HOLD["robot"].config.max_relative_target})


class FakeLeaderBus:
    """가짜 leader. torque 꺼짐 = 사람 손이 잡고 움직임 (hand_target 쪽으로 hand_speed °/s), 켜짐 = Goal 쪽으로 이동.

    goal_on_enable: 'stale' = 토크를 켜도 Goal 레지스터는 마지막 send_feedback 값 그대로 (그 위치로 되돌아감),
                    'present' = 토크를 켜는 순간 Goal := Present. 실제 STS3215 동작은 이 시험으로 알 수 없음 (실물 미검증).
    """

    is_calibrated = True

    def __init__(self, init, goal_on_enable="stale"):
        self.motors = {j: types.SimpleNamespace(id=i + 1) for i, j in enumerate(J)}
        self.present = dict(init)
        self.goal = dict(init)
        self.torque = False
        self.connected = False
        self.goal_on_enable = goal_on_enable
        self.hand_target = None
        self.hand_speed = 40.0
        self.fail_reads = False
        self.t_last = time.perf_counter()
        self.lock = threading.Lock()

    @property
    def is_connected(self):
        return self.connected

    def connect(self, *a, **k):
        self.connected = True

    def disconnect(self, disable_torque=True, *a, **k):
        REC["leader_events"].append({"t": now(), "kind": "disconnect", "torque_off": bool(disable_torque), "phase": _phase()})
        if disable_torque:
            self.torque = False
        self.connected = False

    def _advance(self):
        t = time.perf_counter()
        n = int((t - self.t_last) * TICK_HZ)
        if n <= 0:
            return
        self.t_last += n / TICK_HZ
        for _ in range(min(n, 90)):
            if self.torque:
                for j in J:
                    self.present[j] += FOLLOW_GAIN * (self.goal[j] - self.present[j])
            elif self.hand_target is not None:
                step = self.hand_speed / TICK_HZ
                for j, v in self.hand_target.items():
                    d = v - self.present[j]
                    self.present[j] += float(np.clip(d, -step, step))

    def sync_read(self, what, num_retry=0):
        assert what == "Present_Position"
        if self.fail_reads:
            raise ConnectionError("fake leader: injected read failure")
        with self.lock:
            self._advance()
            REC["leader_reads"].append((now(), dict(self.present)))
            return dict(self.present)

    def sync_write(self, what, vals):
        assert what == "Goal_Position"
        with self.lock:
            self._advance()
            self.goal.update({k: float(v) for k, v in vals.items()})
            REC["leader_events"].append({"t": now(), "kind": "goal", "goal": dict(self.goal), "present": dict(self.present),
                                         "torque": self.torque, "phase": _phase()})

    def enable_torque(self, *a, **k):
        with self.lock:
            self._advance()
            if self.goal_on_enable == "present":
                self.goal = dict(self.present)
            self.torque = True
            REC["leader_events"].append({"t": now(), "kind": "torque_on", "goal": dict(self.goal), "present": dict(self.present),
                                         "phase": _phase()})

    def disable_torque(self, *a, **k):
        with self.lock:
            self._advance()
            self.torque = False
            REC["leader_events"].append({"t": now(), "kind": "torque_off", "present": dict(self.present), "phase": _phase()})

    def configure_motors(self, *a, **k):
        pass

    def write(self, *a, **k):
        pass


class FakeCam:
    is_connected = True
    use_rgb = True

    def __init__(self, h, w, seed):
        self.height, self.width = h, w
        rng = np.random.default_rng(seed)
        self.frames = [rng.integers(0, 255, (h, w, 3), dtype=np.uint8) for _ in range(8)]
        self.i = 0

    def connect(self, *a, **k):
        pass

    def disconnect(self, *a, **k):
        pass

    def read_latest(self, max_age_ms=500):
        self.i = (self.i + 1) % len(self.frames)
        return self.frames[self.i]


class StubPolicy(torch.nn.Module):
    """predict_action_chunk 만 있는 π0.5 대역. 가중치 없음, CPU 텐서만.

    chunk[k] = state + (k+1)·vel (pan 이 계속 + 쪽으로 가는 '지나침' 흉내), wrist_roll = chunk_id·0.01 (어느 chunk 의 action 인지 표시).
    추론 지연 latency_s 로 sleep (실측 RTC p50 0.31 s 흉내). 시작 시 engine 의 reset epoch 을 기록.
    """

    type = "pi05"
    name = "pi05"

    def __init__(self, config, latency_s=0.3, vel=None):
        super().__init__()
        self.config = config
        self.latency_s = latency_s
        self.vel = torch.tensor(vel or [0.3, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=torch.float32)
        self.cid = 0
        self.fail = False
        self.dummy = torch.nn.Parameter(torch.zeros(1), requires_grad=False)

    def supports_rtc(self):
        return True

    def reset(self):
        REC["engine_events"].append({"t": now(), "kind": "policy_reset"})

    def predict_action_chunk(self, batch, inference_delay=0, prev_chunk_left_over=None):
        if self.fail:
            REC["policy_fail_t"].append(now())
            raise RuntimeError("stub policy: injected inference failure")
        eng = HOLD["engine"]
        epoch = None if eng is None else eng._reset_epoch
        self.cid += 1
        cid = self.cid
        t_start = now()
        time.sleep(self.latency_s)
        state = batch["observation.state"].reshape(-1)[:6].float().cpu()
        n = 50
        k = torch.arange(1, n + 1, dtype=torch.float32).unsqueeze(1)
        chunk = state.unsqueeze(0) + k * self.vel.unsqueeze(0)
        chunk[:, 4] = cid * 0.01
        REC["chunks"].append({"cid": cid, "t_start": t_start, "t_end": now(), "epoch_start": epoch, "delay": int(inference_delay),
                              "phase_start": _phase()})
        return chunk.unsqueeze(0)


class _IdPipe:
    steps = []

    def __call__(self, x):
        return x

    def reset(self):
        pass


def install(goal_on_enable="stale", latency_s=0.3, cam_hw=(48, 64), leader_offset=None):
    """lerobot 생성 함수를 가짜로 바꾼다. 반환: HOLD."""
    import lerobot.rollout.context as ctx_mod
    import lerobot.rollout.inference.rtc as rtc_mod
    import lerobot.rollout.strategies.dagger as dagger_mod
    from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
    from lerobot.motors.feetech import FeetechMotorsBus
    from lerobot.robots.so_follower.so_follower import SOFollower
    from lerobot.teleoperators.so_leader.so_leader import SOLeader

    def _blocked(*_a, **_k):
        raise RuntimeError("hil fake: real hardware connect is blocked")

    FeetechMotorsBus.connect = _blocked
    OpenCVCamera.connect = _blocked

    def make_robot(cfg):
        if cfg.type not in ("so100_follower", "so101_follower"):
            raise RuntimeError(f"hil fake: unexpected robot type {cfg.type!r}")
        if cfg.port != FOLLOWER_PORT or any(str(c.index_or_path) not in FAKE_CAMS for c in cfg.cameras.values()):
            raise RuntimeError("hil fake: follower port/cameras are not /nonexistent placeholders — refusing")
        rob = SOFollower.__new__(SOFollower)
        rob.config = cfg
        rob.id = cfg.id
        rob.robot_type = "so_follower"
        rob.calibration = {}
        rob.bus = FakeFollowerBus(REST)
        h, w = cam_hw
        rob.cameras = {"front": FakeCam(h, w, 1), "wrist": FakeCam(h, w, 2)}

        def connect(calibrate=True):
            assert isinstance(rob.bus, FakeFollowerBus) and all(isinstance(c, FakeCam) for c in rob.cameras.values()), "NOT FAKE"
            rob.bus.connect()
            print("[hil fake] MOCK_OK follower FakeFollowerBus+FakeCam (no serial, no camera)", flush=True)

        rob.connect = connect
        HOLD["robot"] = rob
        HOLD["follower_bus"] = rob.bus
        return rob

    def make_teleop(cfg):
        if cfg.type not in ("so100_leader", "so101_leader"):
            raise RuntimeError(f"hil fake: unexpected teleop type {cfg.type!r}")
        if cfg.port != LEADER_PORT:
            raise RuntimeError("hil fake: leader port is not a /nonexistent placeholder — refusing")
        tel = SOLeader.__new__(SOLeader)
        tel.config = cfg
        tel.id = cfg.id
        tel.calibration = {}
        tel.bus = FakeLeaderBus({j: REST[j] + (leader_offset or {}).get(j, 0.0) for j in J}, goal_on_enable=goal_on_enable)

        def connect(calibrate=True):
            assert isinstance(tel.bus, FakeLeaderBus), "NOT FAKE"
            tel.bus.connect()
            tel.bus.torque = False  # SOLeader.configure() 와 같이 토크 끔
            print("[hil fake] MOCK_OK leader FakeLeaderBus (no serial)", flush=True)

        tel.connect = connect
        HOLD["leader"] = tel
        HOLD["leader_bus"] = tel.bus
        return tel

    def load_policy(policy_config):
        return StubPolicy(policy_config, latency_s=latency_s)

    def make_pp(**kw):
        return _IdPipe(), _IdPipe()

    ctx_mod.make_robot_from_config = make_robot
    ctx_mod.make_teleoperator_from_config = make_teleop
    ctx_mod._load_pretrained_policy = load_policy
    ctx_mod.make_pre_post_processors = make_pp
    ctx_mod.bind_relative_anchor = lambda *a, **k: None

    # 엔진 · 전략 포착 + 엔진 호출 기록
    E = rtc_mod.RTCInferenceEngine
    for meth in ("pause", "resume", "reset"):
        orig = getattr(E, meth)

        def wrap(self, _orig=orig, _m=meth):
            q = self._action_queue
            REC["engine_events"].append({"t": now(), "kind": _m, "qsize_before": None if q is None else q.qsize(),
                                         "epoch_before": self._reset_epoch, "phase": _phase()})
            return _orig(self)

        setattr(E, meth, wrap)

    S = dagger_mod.DAggerStrategy
    orig_setup = S.setup

    def setup(self, ctx):
        HOLD["strategy"] = self
        orig_setup(self, ctx)
        HOLD["engine"] = self._engine

    S.setup = setup
    return HOLD
