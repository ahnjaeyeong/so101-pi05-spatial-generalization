"""p04 diag_log 오프라인 검증 장치 (GPU). 로봇·카메라에 연결하지 않는다.

안전 장치 (mock-hardware 사고 2026-10-19 재발 방지):
  1) FeetechMotorsBus.connect · OpenCVCamera.connect 를 시작 전에 막는다 (부르면 RuntimeError).
  2) SOFollower 는 __init__ 없이 만들고 (__new__) bus · cameras 를 FakeBus · FakeCam 으로 넣는다. 장치 경로를 쓰지 않는다.
  3) 첫 호출 전에 bus · 카메라가 Fake 인지 assert. 아니면 바로 중단.
흐름: 실물 eval 과 같은 RTCInferenceEngine (d2 020000, RTC guided EXP h20, steps 5, queue_threshold 30, fps 30) 에
  기록된 실물 판 (AV1 디코드 영상 + state 를 시작값으로) 을 30 Hz 로 넣고, 꺼낸 action 을 그대로 SOFollower.send_action
  (진짜 함수, clamp 8° 포함) 으로 FakeBus 에 쓴다. FakeBus 는 Present 를 Goal 쪽으로 1차 지연 (틱당 30%) 으로 움직인다.
  --diag on 이면 diag_log.install 을 건다 (ROLLOUT_DIAG 경로와 같은 함수). off 와 on 을 같은 조건으로 비교한다.
출력: --out 폴더 (diag 켰으면 diag/), harness_<tag>.json (RTC 지연·틱 루프 시간·starved 수)
사용: nice -n 19 env PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python p04_harness.py --diag on --ticks 450 --out <dir>
"""
import argparse
import json
import sys
import threading
import time
import types
from pathlib import Path

import numpy as np

D2 = Path.home() / "so101_runs/main_k8/d2"
sys.path.insert(0, str(D2 / "eval"))
sys.path.insert(0, str(D2 / "diag_grasp_bias"))
J = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CKPT = D2 / "train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"


def block_hardware():
    from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
    from lerobot.motors.feetech import FeetechMotorsBus

    def nope(*a, **k):
        raise RuntimeError("hardware connect blocked in p04_harness")

    FeetechMotorsBus.connect = nope
    OpenCVCamera.connect = nope


class FakeBus:
    is_connected = True

    def __init__(self, init):
        self.motors = {j: None for j in J}
        self.present = dict(init)
        self.goal = dict(init)
        self.writes = 0

    def sync_read(self, what, num_retry=0):
        assert what == "Present_Position"
        return dict(self.present)

    def sync_write(self, what, vals):
        assert what == "Goal_Position"
        self.goal.update(vals)
        self.writes += 1

    def step(self):
        for j in J:
            self.present[j] += 0.3 * (self.goal[j] - self.present[j])


class FakeCam:
    is_connected = True
    use_rgb = True
    height, width = 480, 640

    def __init__(self):
        self.frame, self.latest_timestamp = None, None

    def set(self, img):
        self.frame, self.latest_timestamp = img, time.perf_counter()

    def read_latest(self, max_age_ms=500):
        return self.frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag", choices=["on", "off"], required=True)
    ap.add_argument("--ticks", type=int, default=450)
    ap.add_argument("--run", default="20261026_140246_20k_t1_try3_filt")
    ap.add_argument("--ep", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    block_hardware()

    import common as C
    import torch
    from lerobot.configs import RTCAttentionSchedule
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    from lerobot.policies.rtc.configuration_rtc import RTCConfig
    from lerobot.robots.so_follower.so_follower import SOFollower
    from lerobot.rollout.inference.rtc import RTCInferenceEngine
    from lerobot.rollout.robot_wrapper import ThreadSafeRobot

    # 기록된 판 (영상·state)
    ds = D2 / "eval/rollouts" / args.run / "dataset"
    s, _ = C.load_parquet(ds)[args.ep]
    n = min(args.ticks, len(s))
    cache = {}
    F = C.frames(ds, args.ep, "front", 0, n - 1, cache)
    Wr = C.frames(ds, args.ep, "wrist", 0, n - 1, cache)

    # 가짜 팔 (__init__ 안 씀)
    rob = SOFollower.__new__(SOFollower)
    rob.config = types.SimpleNamespace(max_relative_target=8.0, num_read_retries=0, id="harness")
    rob.id, rob.robot_type = "harness", "so_follower"
    rob.bus = FakeBus({j: float(s[0, k]) for k, j in enumerate(J)})
    rob.cameras = {"front": FakeCam(), "wrist": FakeCam()}
    assert isinstance(rob.bus, FakeBus) and all(isinstance(c, FakeCam) for c in rob.cameras.values()), "not fake — abort"
    tsr = ThreadSafeRobot(rob)

    st = {"episode": 0, "tick": 0, "ctx": None}
    diag = None
    if args.diag == "on":
        import os
        os.environ["ROLLOUT_DIAG_DIR"] = str(out / "diag")
        import diag_log
        diag = diag_log.install(st, {"harness": True})

    policy = PI05Policy.from_pretrained(str(CKPT)).to("cuda").eval()
    policy.config.num_inference_steps = 5
    policy.config.rtc_config = RTCConfig(enabled=True, mode="guided", prefix_attention_schedule=RTCAttentionSchedule.EXP,
                                         max_guidance_weight=10.0, execution_horizon=20)
    policy.init_rtc_processor()
    pre, post = make_pre_post_processors(policy.config, pretrained_path=str(CKPT),
                                         preprocessor_overrides={"device_processor": {"device": "cuda"}})
    feats = {"observation.state": {"dtype": "float32", "shape": (6,), "names": [f"{j}.pos" for j in J]},
             "observation.images.front": {"dtype": "video", "shape": (480, 640, 3), "names": ["height", "width", "channels"]},
             "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3), "names": ["height", "width", "channels"]}}
    eng = RTCInferenceEngine(policy=policy, preprocessor=pre, postprocessor=post, robot_wrapper=tsr, rtc_config=policy.config.rtc_config,
                             dataset_features=feats, task=TASK, fps=30, device="cuda", rtc_queue_threshold=30)
    import logging
    lat = []

    class H(logging.Handler):
        def emit(self, r):
            m = r.getMessage()
            if m.startswith("RTC inference latency="):
                lat.append(float(m.split("=")[1].split("s")[0]))

    lg = logging.getLogger("lerobot.rollout.inference.rtc")
    lg.setLevel(logging.DEBUG)
    lg.addHandler(H())
    eng.start()
    eng.reset()
    eng.resume()
    body, starved, sent_n = [], 0, 0
    t_next = time.perf_counter()
    for t in range(n):
        st["tick"] = t
        rob.cameras["front"].set(F[t])
        rob.cameras["wrist"].set(Wr[t])
        b0 = time.perf_counter()
        obs = tsr.get_observation()
        eng.notify_observation(obs)
        a = eng.get_action(None)
        if a is None:
            starved += 1
        else:
            tsr.send_action({f"{j}.pos": float(a[k]) for k, j in enumerate(J)})
            sent_n += 1
        body.append((time.perf_counter() - b0) * 1e3)
        rob.bus.step()
        t_next += 1 / 30
        dt = t_next - time.perf_counter()
        if dt > 0:
            time.sleep(dt)
    eng.pause()
    eng.stop()
    if diag is not None:
        diag["close"]()
    res = {"diag": args.diag, "ticks": n, "sent": sent_n, "starved": starved, "bus_writes": rob.bus.writes,
           "rtc_latency_s": {"n": len(lat), "p50": float(np.median(lat)) if lat else None, "max": float(max(lat)) if lat else None,
                             "all": lat},
           "loop_body_ms": {"p50": float(np.median(body)), "p99": float(np.percentile(body, 99)), "max": float(max(body))}}
    (out / f"harness_{args.diag}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "rtc_latency_s"} | {"lat_p50": res["rtc_latency_s"]["p50"]}, indent=1))


if __name__ == "__main__":
    main()
