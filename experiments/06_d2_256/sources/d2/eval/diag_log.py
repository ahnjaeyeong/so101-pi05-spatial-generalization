"""pan 추론 진단용 추가 기록 (2026-10-29, pan_inference_diagnostic). 기본 꺼짐.

켜는 법: 환경변수 ROLLOUT_DIAG=1 + rollout_logged 옵션 하나 이상 켬 (d2 표준 --arm_filter=true).
  rollout_logged.install() 끝에서 diag_log.install(st) 를 부른다. ROLLOUT_DIAG 가 없으면 이 파일은 import 도 되지 않는다.
기록 위치: ROLLOUT_DIAG_DIR, 없으면 filter_log.csv (ROLLOUT_FILTER_LOG / ROLLOUT_DEBUG_LOG) 옆 diag/

원칙: 제어 경로의 값은 바꾸지 않는다. 감싼 함수는 원래 함수를 같은 인자로 부르고 결과를 그대로 돌려준다.
  감싸는 쪽에서 하는 일은 참조 보관·시각 기록·작은 dict 만들기뿐이다. 텐서 GPU→CPU 복사, PNG 인코딩, 파일 쓰기는
  별도 writer 스레드에서 한다. writer 큐가 가득 차면 기록을 버리고 (제어 루프를 막지 않음) 버린 수를 summary 에 남긴다.

기록 (chunk = RTC 추론 한 번):
  chunks.jsonl         chunk 마다 한 줄: chunk_id, episode, tick(merge 때), 관측 tick·시각, 카메라 프레임 시각,
                       추론 시작·끝, merge 시각, inference_delay(정책에 넘긴 값), real_delay, idx_before, idx_diff,
                       적용 delay(= 50 − queue 길이), qsize 전후, 관측 state
  chunks/c#####.npz    original (50,6) 정규화 · processed (50,6) ° · noise (50,32) · prefix (정책에 넘긴 prev_chunk_left_over, 정규화)
                       · leftover_processed (merge 직전 queue 에 남아 있던 앞 chunk 의 action, °)
  obs/c#####_front.png, obs/c#####_wrist.png   그 추론이 실제로 받은 영상 (RGB→PNG 무손실)
  ticks.csv            send_action 마다 한 줄: 시각, episode, tick, 꺼낸 action 의 chunk_id·chunk 안 index,
                       goal_in_*(clamp 전 = 필터 뒤) · sent_*(clamp 뒤 실제 Goal_Position) · present_*(clamp 에 쓴 Present_Position),
                       관측 시각·카메라 프레임 나이, send 시간
  manifest.json        실행 인자·환경·설정·코드 sha256 (시작 때), summary.json (끝날 때: 개수, 버린 수, 감싸기 비용 분포)
"""

import atexit
import dataclasses
import functools
import hashlib
import json
import logging
import os
import queue
import sys
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np

log = logging.getLogger("lerobot.diag_log")
JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
_QMAX = 4000


def _sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


class _Writer(threading.Thread):
    def __init__(self, root):
        super().__init__(daemon=True, name="DiagWriter")
        self.root = Path(root)
        (self.root / "chunks").mkdir(parents=True, exist_ok=True)
        (self.root / "obs").mkdir(exist_ok=True)
        self.q = queue.Queue(maxsize=_QMAX)
        self.dropped = {"tick": 0, "chunk": 0}
        self.written = {"tick": 0, "chunk": 0}
        self.cost = {"write_chunk_ms": []}
        self._ticks = open(self.root / "ticks.csv", "w", buffering=1 << 16)
        cols = (["wall", "perf", "episode", "tick", "pop_chunk", "pop_idx", "obs_perf", "obs_tick", "front_age_ms", "wrist_age_ms",
                 "front_ts", "wrist_ts", "send_ms"] + [f"goal_in_{j}" for j in JOINTS] + [f"sent_{j}" for j in JOINTS]
                + [f"present_{j}" for j in JOINTS])
        self._ticks.write(",".join(cols) + "\n")
        self._chunks = open(self.root / "chunks.jsonl", "w", buffering=1)
        self._stop_ev = threading.Event()

    def put(self, kind, item):
        try:
            self.q.put_nowait((kind, item))
        except queue.Full:
            self.dropped[kind] += 1

    def run(self):
        while not (self._stop_ev.is_set() and self.q.empty()):
            try:
                kind, item = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                if kind == "tick":
                    self._ticks.write(item + "\n")
                    self.written["tick"] += 1
                else:
                    self._write_chunk(item)
                    self.written["chunk"] += 1
            except Exception as e:  # 기록 실패는 제어에 영향 없게 로그만
                log.warning("diag write failed: %s", e)

    def _write_chunk(self, it):
        import cv2
        import torch
        t0 = time.perf_counter()
        cid = it["meta"]["chunk_id"]
        arr = {}
        for k in ("original", "processed", "noise", "prefix", "leftover_processed"):
            v = it.get(k)
            if v is None:
                continue
            if isinstance(v, torch.Tensor):
                v = v.detach().to("cpu", torch.float32).numpy()
            arr[k] = np.asarray(v, np.float32).squeeze()
        np.savez_compressed(self.root / "chunks" / f"c{cid:05d}.npz", **arr)
        for cam in ("front", "wrist"):
            img = it.get(cam)
            if img is not None:
                cv2.imwrite(str(self.root / "obs" / f"c{cid:05d}_{cam}.png"), cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR),
                            [cv2.IMWRITE_PNG_COMPRESSION, 3])
        self._chunks.write(json.dumps(it["meta"]) + "\n")
        self.cost["write_chunk_ms"].append((time.perf_counter() - t0) * 1e3)

    def close(self):
        self._stop_ev.set()
        self.join(timeout=30)
        self._ticks.close()
        self._chunks.close()


def _pcts(x):
    x = np.asarray(x, float)
    if not len(x):
        return None
    return {"n": int(len(x)), "p50": float(np.percentile(x, 50)), "p99": float(np.percentile(x, 99)), "max": float(x.max())}


def install(st, opts=None):
    """rollout_logged.install() 의 상태 dict st (episode · tick · ctx) 와 옵션 opts 를 받아 기록 감싸기를 건다."""
    import torch
    import lerobot.robots.so_follower.so_follower as sof_mod
    import lerobot.rollout.inference.rtc as rtc_mod
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy, PI05Pytorch
    from lerobot.policies.rtc import ActionQueue

    root = os.environ.get("ROLLOUT_DIAG_DIR") or str(
        Path(os.environ.get("ROLLOUT_FILTER_LOG") or os.environ.get("ROLLOUT_DEBUG_LOG", "rollout_debug.log")).with_name("diag"))
    W = _Writer(root)
    W.start()
    d = {"cid": -1, "offset": 0, "last_pop": (-1, -1), "last_obs": None, "obs_pairs": deque(maxlen=16), "present": None,
         "cost": {"ctl_us": [], "rtc_us": []}, "manifest_cfg": False, "lock": threading.Lock()}
    tls = threading.local()
    errs = {}

    def _err(where, e):
        """감싸기 안 기록 코드의 예외는 삼킨다 (제어·추론 흐름을 바꾸지 않게). 처음 한 번만 경고."""
        errs[where] = errs.get(where, 0) + 1
        if errs[where] == 1:
            log.warning("diag_log %s error (ignored): %r", where, e)
    t_wall0, t_perf0 = time.time(), time.perf_counter()

    def wall_of(perf):
        return t_wall0 + (perf - t_perf0)

    here = Path(__file__).resolve().parent
    import lerobot
    lp = Path(lerobot.__file__).resolve().parent
    manifest = {
        "started": time.strftime("%Y-%m-%d %H:%M:%S"), "argv": sys.argv, "root": root,
        "env": {k: v for k, v in os.environ.items() if k.startswith(("ROLLOUT_", "EVAL_UI_", "CUDA", "PYTORCH"))},
        "code_sha256": {str(p): _sha(p) for p in [here / "rollout_logged.py", here / "arm_filter.py", here / "diag_log.py",
                                                   lp / "rollout/inference/rtc.py", lp / "policies/rtc/action_queue.py",
                                                   lp / "policies/rtc/modeling_rtc.py", lp / "policies/pi05/modeling_pi05.py",
                                                   lp / "robots/so_follower/so_follower.py", lp / "robots/utils.py",
                                                   lp / "rollout/strategies/core.py", lp / "rollout/strategies/episodic.py"]},
        "rollout_logged_opts": opts,
        "lerobot_version": getattr(lerobot, "__version__", None), "torch": torch.__version__, "python": sys.version,
    }
    (Path(root) / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))

    def _cfg_once():
        """첫 send 때 ctx 의 설정을 manifest 에 덧붙인다 (그 전엔 ctx 가 없다)."""
        if d["manifest_cfg"] or st.get("ctx") is None:
            return
        d["manifest_cfg"] = True
        try:
            cfg = st["ctx"].runtime.cfg
            pol = st["ctx"].policy
            pc = getattr(getattr(pol, "policy", None), "config", None)
            extra = {"rollout_cfg": repr(cfg)[:20000],
                     "policy_cfg": {k: repr(getattr(pc, k, None)) for k in ("num_inference_steps", "chunk_size", "n_action_steps",
                                                                             "rtc_config", "max_action_dim")} if pc is not None else None}
            m = json.loads((Path(root) / "manifest.json").read_text())
            m.update(extra)
            (Path(root) / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False))
        except Exception as e:
            log.warning("diag manifest cfg failed: %s", e)

    in_rtc = lambda: threading.current_thread().name == "RTCInference"  # noqa: E731

    # ---- 관측 (control thread): get_observation → 시각·카메라 프레임 시각
    _orig_get_obs = sof_mod.SOFollower.get_observation

    @functools.wraps(_orig_get_obs)
    def get_observation(self, *a, **k):
        p0 = time.perf_counter()
        obs = _orig_get_obs(self, *a, **k)
        t0 = time.perf_counter()
        try:
            cams = {n: getattr(c, "latest_timestamp", None) for n, c in getattr(self, "cameras", {}).items()}
            d["last_obs"] = {"perf": p0, "tick": st.get("tick"), "episode": st.get("episode"), "cam_ts": cams}
        except Exception as e:
            _err("get_obs", e)
        d["cost"]["ctl_us"].append((time.perf_counter() - t0) * 1e6)
        return obs

    sof_mod.SOFollower.get_observation = get_observation

    _orig_notify = rtc_mod.RTCInferenceEngine.notify_observation

    @functools.wraps(_orig_notify)
    def notify_observation(self, obs):
        d["obs_pairs"].append((obs, d["last_obs"]))
        return _orig_notify(self, obs)

    rtc_mod.RTCInferenceEngine.notify_observation = notify_observation

    # ---- RTC thread: 어느 관측으로 추론했는지 (build_dataset_frame 은 _rtc_loop 안에서 관측 하나당 한 번)
    _orig_bdf = rtc_mod.build_dataset_frame

    @functools.wraps(_orig_bdf)
    def build_dataset_frame(ds_features, values, prefix):
        obs = values
        if in_rtc():
            t0 = time.perf_counter()
            try:
                meta = next((m for o, m in reversed(list(d["obs_pairs"])) if o is obs), None)
                tls.pend = {"t_build": t0, "obs": obs, "obs_meta": meta}
            except Exception as e:
                _err("bdf", e)
            d["cost"]["rtc_us"].append((time.perf_counter() - t0) * 1e6)
        return _orig_bdf(ds_features, values, prefix)

    rtc_mod.build_dataset_frame = build_dataset_frame

    _orig_noise = PI05Pytorch.sample_noise

    @functools.wraps(_orig_noise)
    def sample_noise(self, shape, device):
        n = _orig_noise(self, shape, device)
        p = getattr(tls, "pend", None) if in_rtc() else None
        if p is not None:
            try:
                p["noise"] = n.clone()
            except Exception as e:
                _err("noise", e)
        return n

    PI05Pytorch.sample_noise = sample_noise

    _orig_pred = PI05Policy.predict_action_chunk

    @functools.wraps(_orig_pred)
    def predict_action_chunk(self, batch, **kw):
        p = getattr(tls, "pend", None) if in_rtc() else None
        if p is not None:
            try:
                p["t_pred0"] = time.perf_counter()
                p["inference_delay"] = kw.get("inference_delay")
                pc = kw.get("prev_chunk_left_over")
                p["prefix"] = None if pc is None else pc.clone()
                p["execution_horizon"] = kw.get("execution_horizon")
            except Exception as e:
                _err("pred", e)
        out = _orig_pred(self, batch, **kw)
        if p is not None:
            p["t_pred1"] = time.perf_counter()
        return out

    PI05Policy.predict_action_chunk = predict_action_chunk

    # ---- merge (RTC thread, obs_lock 안): 참조·작은 값만 잡고 바로 원래 merge
    _orig_merge = ActionQueue.merge

    @functools.wraps(_orig_merge)
    def merge(self, original_actions, processed_actions, real_delay, action_index_before_inference=None, **kw):
        t0 = time.perf_counter()
        last_index, qsize = self.last_index, self.qsize()
        left = None if self.queue is None else self.queue[self.last_index:]  # 새 텐서 (slice 는 view 지만 queue 는 merge 에서 교체만 됨)
        r = _orig_merge(self, original_actions, processed_actions, real_delay, action_index_before_inference, **kw)
        t1 = time.perf_counter()
        try:
            _after_merge(self, original_actions, processed_actions, real_delay, action_index_before_inference, t0, t1, last_index, qsize, left)
        except Exception as e:
            _err("merge", e)
        d["cost"]["rtc_us"].append((time.perf_counter() - t1) * 1e6)
        return r

    def _after_merge(self, original_actions, processed_actions, real_delay, action_index_before_inference, t0, t1, last_index, qsize, left):
        n_q = 0 if self.queue is None else len(self.queue)
        applied = int(len(processed_actions) - n_q)
        with d["lock"]:
            d["cid"] += 1
            d["offset"] = applied
            cid = d["cid"]
        p = getattr(tls, "pend", None) or {}
        tls.pend = None
        om = p.get("obs_meta") or {}
        obs = p.get("obs") or {}
        state = [float(obs.get(f"{j}.pos", float("nan"))) for j in JOINTS] if isinstance(obs, dict) else None
        meta = {"chunk_id": cid, "episode": st.get("episode"), "tick_at_merge": st.get("tick"),
                "obs_tick": om.get("tick"), "obs_episode": om.get("episode"),
                "obs_perf": om.get("perf"), "obs_wall": wall_of(om["perf"]) if om.get("perf") else None,
                "cam_ts": om.get("cam_ts"), "t_build": p.get("t_build"), "t_pred0": p.get("t_pred0"), "t_pred1": p.get("t_pred1"),
                "t_merge": t0, "wall_merge": wall_of(t0), "inference_delay": p.get("inference_delay"),
                "execution_horizon": p.get("execution_horizon"), "real_delay": int(real_delay),
                "idx_before": action_index_before_inference, "last_index_at_merge": last_index,
                "idx_diff": None if action_index_before_inference is None else max(0, last_index - action_index_before_inference),
                "applied_delay": applied, "qsize_before": qsize, "qsize_after": n_q, "obs_state": state,
                "has_noise": "noise" in p, "has_prefix": p.get("prefix") is not None, "merge_us": (t1 - t0) * 1e6}
        W.put("chunk", {"meta": meta, "original": original_actions, "processed": processed_actions, "noise": p.get("noise"),
                        "prefix": p.get("prefix"), "leftover_processed": left,
                        "front": obs.get("front") if isinstance(obs, dict) else None,
                        "wrist": obs.get("wrist") if isinstance(obs, dict) else None})

    ActionQueue.merge = merge

    # ---- 꺼낸 action 의 chunk·index (control thread)
    _orig_get = ActionQueue.get_with_task

    @functools.wraps(_orig_get)
    def get_with_task(self):
        with d["lock"]:
            cid, off = d["cid"], d["offset"]
        li = self.last_index
        r = _orig_get(self)
        if r is not None:
            d["last_pop"] = (cid, off + li)
        return r

    ActionQueue.get_with_task = get_with_task

    # ---- clamp 에 쓴 Present_Position, 실제 Goal_Position (control thread)
    _orig_safe = sof_mod.ensure_safe_goal_position

    def ensure_safe_goal_position(goal_present_pos, max_relative_target):
        d["present"] = {k: v[1] for k, v in goal_present_pos.items()}
        return _orig_safe(goal_present_pos, max_relative_target)

    sof_mod.ensure_safe_goal_position = ensure_safe_goal_position

    _orig_send = sof_mod.SOFollower.send_action

    @functools.wraps(_orig_send)
    def send_action(self, action):
        d["present"] = None
        p0 = time.perf_counter()
        sent = _orig_send(self, action)
        p1 = time.perf_counter()
        try:
            _after_send(action, sent, p0, p1)
        except Exception as e:
            _err("send", e)
        d["last_pop"] = (-1, -1)
        d["cost"]["ctl_us"].append((time.perf_counter() - p1) * 1e6)
        return sent

    def _after_send(action, sent, p0, p1):
        _cfg_once()
        om = d["last_obs"] or {}
        cts = om.get("cam_ts") or {}
        f = lambda v: "" if v is None else f"{v:.4f}"  # noqa: E731
        pr = d["present"] or {}
        row = ([f"{wall_of(p0):.4f}", f"{p0:.5f}", str(st.get("episode")), str(st.get("tick")), str(d["last_pop"][0]), str(d["last_pop"][1]),
                f(om.get("perf")), str(om.get("tick")),
                f((om["perf"] - cts["front"]) * 1e3) if om.get("perf") and cts.get("front") else "",
                f((om["perf"] - cts["wrist"]) * 1e3) if om.get("perf") and cts.get("wrist") else "",
                f(cts.get("front")), f(cts.get("wrist")), f"{(p1 - p0) * 1e3:.2f}"]
               + [f(action.get(f"{j}.pos")) for j in JOINTS] + [f(sent.get(f"{j}.pos")) for j in JOINTS]
               + [f(pr.get(j)) for j in JOINTS])
        W.put("tick", ",".join(row))

    sof_mod.SOFollower.send_action = send_action

    def close():
        W.close()
        summ = {"ended": time.strftime("%Y-%m-%d %H:%M:%S"), "written": W.written, "dropped": W.dropped,
                "ctl_wrapper_us": _pcts(d["cost"]["ctl_us"]), "rtc_wrapper_us": _pcts(d["cost"]["rtc_us"]),
                "writer_chunk_ms": _pcts(W.cost["write_chunk_ms"]), "n_chunks": d["cid"] + 1, "wrapper_errors": errs}
        (Path(root) / "summary.json").write_text(json.dumps(summ, indent=1))

    atexit.register(close)
    log.info("diag_log on: %s", root)
    return {"root": root, "close": close, "state": d, "writer": W}
