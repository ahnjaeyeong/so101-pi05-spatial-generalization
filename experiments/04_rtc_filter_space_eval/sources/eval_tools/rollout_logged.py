"""lerobot-rollout 을 그대로 실행하면서 DEBUG 로그 파일을 하나 더 남긴다 (venv 는 건드리지 않음).

- RTC 추론마다의 지연·큐 길이 ("RTC inference latency=…", DEBUG)
- max_relative_target 제한 경고 ("Relative goal position magnitude had to be clamped", WARNING)
를 ms 단위 시각과 함께 ROLLOUT_DEBUG_LOG 경로에 기록한다. 인자는 lerobot-rollout 과 같다.

주의: --interactive=true 는 실행 중 WARNING 이하를 전부 끄므로 이 파일에도 안 남는다.

추가 옵션 (2026-10-19, lerobot-rollout 에 넘기기 전에 여기서 빼서 처리 — 기본값이면 lerobot 경로를 바꾸지 않음)
  --arm_filter=true|false          팔 5관절 EMA + 관절별 속도 제한 (기본 false). 그리퍼는 손대지 않음. 자세한 규칙은 arm_filter.py
  --arm_filter.alpha=0.5           EMA α
  --arm_filter.init=state          에피소드 시작 첫 프레임 기준: state(실제 관절 상태, 기본) | first_action(P0 검증용)
  --rollout_guard=off|warn|stop    RTC 지연·큐 비움·추종 정지 감시 (기본 off). stop 은 lerobot 표준 종료 경로로 끝냄
  --rollout_guard.starve_ticks=15  --rollout_guard.stale_ticks=30  --rollout_guard.stall_ticks=20  --rollout_guard.horizon_count=10
  --rollout_guard.startup_ticks=150  (에피소드 첫 명령까지 허용 틱 — 첫 chunk 콜드 스타트 0.7–0.8 s 를 starve 와 따로 셈)
  --exec_speed=0.8                 실행 속도 배율 (기본 1.0 = 기존과 같음, 0.3–1.0, RTC 전용). 30 Hz 유지, RTC 큐 안 재생 위치를 틱마다
                                   0.8 action 씩 전진시켜 인접 두 action 을 보간 (팔·그리퍼 같이). RTC 지연 추정도 action 단위(×0.8)로 환산.
                                   근거: ~/so101_runs/redbox_all/eval/speed_scaling/report.md
  셋 중 하나라도 켜지면 틱마다 필터 전·후 action·실제 상태를 ROLLOUT_FILTER_LOG (기본: ROLLOUT_DEBUG_LOG 옆 filter_log.csv) 에 남긴다.
  필터를 켜면 dataset 의 action 열은 '필터 후(= 보낸 명령, clamp 전)' 값이 된다. 필터 전 값은 filter_log.csv 의 raw_*.
"""

import contextlib
import logging
import os
import sys
from pathlib import Path

import lerobot.scripts.lerobot_rollout as lr

_orig_init_logging = lr.init_logging


def _init_logging(*args, **kwargs):
    _orig_init_logging(*args, **kwargs)
    path = os.environ.get("ROLLOUT_DEBUG_LOG")
    if not path:
        return
    h = logging.FileHandler(path)
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))
    h.addFilter(lambda r: r.name.startswith("lerobot") or r.levelno >= logging.WARNING)
    logging.getLogger().addHandler(h)
    logging.getLogger("lerobot.rollout_logged").info("debug log: %s · argv: %s", path, " ".join(sys.argv[1:]))
    if _OPTS["active"]:
        logging.getLogger("lerobot.rollout_logged").info("arm_filter/guard options: %s", _OPTS)


lr.init_logging = _init_logging


def _pop_options(argv):
    """--arm_filter* / --rollout_guard* 를 argv 에서 빼서 dict 로."""
    opts = {"arm_filter": False, "alpha": 0.5, "init": "state", "guard": "off",
            "starve_ticks": 15, "stale_ticks": 30, "stall_ticks": 20, "horizon_count": 10, "startup_ticks": 150, "exec_speed": 1.0}
    rest = [argv[0]]
    for a in argv[1:]:
        if a.startswith("--exec_speed="):
            opts["exec_speed"] = float(a.split("=", 1)[1])
        elif a.startswith("--arm_filter") or a.startswith("--rollout_guard"):
            key, _, val = a[2:].partition("=")
            if key == "arm_filter":
                opts["arm_filter"] = val.lower() in ("1", "true", "yes", "on")
            elif key == "arm_filter.alpha":
                opts["alpha"] = float(val)
            elif key == "arm_filter.init":
                opts["init"] = val
            elif key == "rollout_guard":
                opts["guard"] = val
            elif key.startswith("rollout_guard."):
                opts[key.split(".", 1)[1]] = int(val)
            else:
                raise SystemExit(f"unknown option {a}")
        else:
            rest.append(a)
    opts["active"] = opts["arm_filter"] or opts["guard"] != "off" or opts["exec_speed"] < 1.0
    if opts["exec_speed"] < 1.0 and "--inference.type=rtc" not in rest:
        raise SystemExit("--exec_speed < 1 은 --inference.type=rtc 와 함께만 쓸 수 있습니다")
    return opts, rest


_OPTS, _ARGV = _pop_options(sys.argv)


def install(opts):
    """lerobot 함수를 런타임에만 바꿔 끼운다 (설치된 lerobot 파일은 수정하지 않음)."""
    import lerobot.rollout.inference.rtc as rtc_mod
    import lerobot.rollout.strategies.base as base_mod
    import lerobot.rollout.strategies.core as core_mod
    import lerobot.rollout.strategies.episodic as episodic_mod
    import lerobot.rollout.strategies.highlight as highlight_mod
    from lerobot.policies.rtc import ActionQueue
    from lerobot.utils.action_interpolator import ActionInterpolator
    from lerobot.utils.constants import OBS_STR
    from lerobot.utils.feature_utils import build_dataset_frame

    from arm_filter import ArmFilter, FilterLog, RolloutGuard, TimeScaler

    st = {"filter": None, "guard": None, "log": None, "ctx": None, "episode": -1, "tick": 0,
          "ts": TimeScaler(opts.get("exec_speed", 1.0)) if opts.get("exec_speed", 1.0) < 1.0 else None}

    def _request_stop(kind, msg):
        ctx = st["ctx"]
        if ctx is not None:
            ctx.runtime.shutdown_event.set()

    def _lazy_init(ctx, interpolator):
        if st["filter"] is not None:
            return
        keys = list(ctx.data.ordered_action_keys)
        st["filter"] = ArmFilter(keys, alpha=opts["alpha"], init=opts["init"], multiplier=interpolator.multiplier,
                                 enabled=opts["arm_filter"])
        horizon = None
        inf_cfg = getattr(ctx.runtime.cfg, "inference", None)
        if getattr(inf_cfg, "rtc", None) is not None:
            horizon = int(inf_cfg.rtc.execution_horizon)
        st["guard"] = RolloutGuard(mode=opts["guard"], starve_ticks=opts["starve_ticks"], stale_ticks=opts["stale_ticks"],
                                   horizon=horizon, horizon_count=opts["horizon_count"], stall_ticks=opts["stall_ticks"],
                                   on_stop=_request_stop, startup_ticks=opts.get("startup_ticks", 150))
        path = os.environ.get("ROLLOUT_FILTER_LOG") or str(Path(os.environ.get("ROLLOUT_DEBUG_LOG", "rollout_debug.log")).with_name("filter_log.csv"))
        st["log"] = FilterLog(path, keys)
        logging.getLogger("lerobot.rollout_logged").info("arm_filter=%s guard=%s horizon=%s exec_speed=%s log=%s vmax/tick=%s",
                                                         opts["arm_filter"], opts["guard"], horizon, opts.get("exec_speed", 1.0), path,
                                                         st["filter"].vmax.round(2).tolist())

    def send_next_action(obs_processed, obs_raw, ctx, interpolator, timer=None):
        """core.send_next_action 과 같은 흐름 + 필터·감시·로그. 필터는 정책 action 을 꺼낸 직후, robot_action_processor·전송 전에 건다."""
        st["ctx"] = ctx
        _lazy_init(ctx, interpolator)
        engine = ctx.policy.inference
        features = ctx.data.dataset_features
        ordered_keys = ctx.data.ordered_action_keys
        section = timer.section if timer is not None else contextlib.nullcontext

        ts = st["ts"]
        if ts is not None:
            # 실행 속도 배율: RTC 큐에서 필요한 만큼만 꺼내 보간 → interpolator 에 한 개 넣고 바로 꺼냄 (녹화·관측 알림 흐름 유지)
            with section("infer"):
                obs_frame = build_dataset_frame(features, obs_processed, prefix=OBS_STR)
                pop = lambda: (lambda a: None if a is None else a.cpu())(engine.get_action(obs_frame))
                blended = ts.next(pop)
            if blended is not None:
                interpolator.add(blended)
        elif interpolator.needs_new_action():
            with section("infer"):
                obs_frame = build_dataset_frame(features, obs_processed, prefix=OBS_STR)
                action_tensor = engine.get_action(obs_frame)
            if action_tensor is not None:
                interpolator.add(action_tensor.cpu())

        interp = interpolator.get()
        state = [obs_raw.get(k, float("nan")) for k in ordered_keys]
        if interp is None:
            if timer is not None:
                timer.note_starved_tick()
            st["guard"].on_starved()
            st["log"].row(st["episode"], st["tick"], "starved", state=state)
            st["tick"] += 1
            return None

        if len(interp) != len(ordered_keys):
            raise ValueError(f"Interpolated tensor length ({len(interp)}) != action keys ({len(ordered_keys)})")
        raw = [interp[i].item() for i in range(len(ordered_keys))]
        out, info = st["filter"].step(raw, state)
        action_dict = {k: float(out[i]) for i, k in enumerate(ordered_keys)}
        with section("send"):
            processed = ctx.processors.robot_action_processor((action_dict, obs_raw))
            ctx.hardware.robot_wrapper.send_action(processed)
        st["guard"].on_command(out, state, st["filter"].arm_idx)
        st["log"].row(st["episode"], st["tick"], "cmd", raw=raw, out=out, state=state, info=info,
                      ts_pos="" if ts is None else f"{ts.pos:.3f}")
        st["tick"] += 1
        return action_dict

    for mod in (core_mod, episodic_mod, base_mod, highlight_mod):
        mod.send_next_action = send_next_action

    _orig_reset = ActionInterpolator.reset

    def _reset(self):
        _orig_reset(self)
        if st["filter"] is not None:
            st["filter"].reset()
            st["guard"].reset()
        if st["ts"] is not None:
            st["ts"].reset()
        st["episode"] += 1
        st["tick"] = 0

    ActionInterpolator.reset = _reset

    _orig_estimate = rtc_mod._estimate_rtc_delay

    def _estimate(**kw):
        if st["ts"] is not None and kw.get("latency"):
            kw = dict(kw, latency=kw["latency"] * st["ts"].speed)  # 지연을 action 단위로 (틱 × 속도)
        d = _orig_estimate(**kw)
        if st["guard"] is not None and kw.get("has_previous_actions"):
            st["guard"].on_delay_estimate(d)
        return d

    rtc_mod._estimate_rtc_delay = _estimate

    _orig_merge = ActionQueue.merge

    def _merge(self, original_actions, processed_actions, real_delay, action_index_before_inference=None, **kw):
        qsize_before = self.qsize()
        idx_diff = None if action_index_before_inference is None else max(0, self.get_action_index() - action_index_before_inference)
        if st["guard"] is not None and action_index_before_inference is not None:
            st["guard"].on_merge(int(real_delay), idx_diff, qsize_before)
        if st["log"] is not None:
            st["log"].row(st["episode"], st["tick"], f"merge real_delay={real_delay} idx_diff={idx_diff} qsize_before={qsize_before}")
        return _orig_merge(self, original_actions, processed_actions, real_delay, action_index_before_inference, **kw)

    ActionQueue.merge = _merge
    return st


if __name__ == "__main__":
    sys.argv = _ARGV
    _state = install(_OPTS) if _OPTS["active"] else None
    try:
        lr.main()
    finally:
        if _state is not None and _state["log"] is not None:
            _state["log"].close()
