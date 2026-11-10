"""HIL 수집 진입점 — 설치된 lerobot 0.6.2 의 `lerobot-rollout --strategy.type=dagger` 를 그대로 실행하고 얇은 adapter 만 끼운다.

lerobot 파일 · d2 파일은 수정하지 않는다 (런타임 패치만). 상태기계 · 정책 정지 · RTC 큐 처리 · 리더 동기화 · 교정 녹화는 공식 코드 그대로.

추가하는 것 (모두 `--hil.*` 옵션, lerobot 에 넘기기 전에 여기서 뺀다):
  A1  d2/eval/rollout_logged.py 를 그대로 불러 `--arm_filter` · `--rollout_guard` · filter_log 를 쓰고, 그 함수를 dagger 모듈에도 건다.
      (rollout_logged 는 core/episodic/base/highlight 만 패치 — dagger 는 `from .core import send_next_action` 로 따로 묶여 있다.)
      팔 필터 기본값은 rollout_logged 기본 그대로 OFF (2026-11-04 사용자 결정). run_hil.sh 는 `--rollout_guard=warn` 만 켜서
      filter_log (정책 구간 매 틱 state · 명령, 필터 꺼짐 → out = raw) 를 남긴다. 필터를 켜려면 사용자가 `--arm_filter=true` 를 직접 준다.
  A2  hil_events.jsonl (데이터셋 옆): 단계 전환 (시각 · 전/후 단계 · 저장된 episode 수 · 진행 중 교정의 frame 수 ·
      follower 현재 자세 · leader 현재 자세 · 마지막 정책 명령 · RTC 큐 길이 · reset epoch), 표시 키, 세션 끝 상태.
  A3  표시 키 (녹화 동작은 바꾸지 않음, 기록만): m = 복구 완료, 1/2/3 = 이번 개입 유형 R1 / R2 / R2-O,
      g / h = 첫 파지 성공 / 실패, b / f = 최종 작업 성공 (상자 안) / 실패, r = 원위치 구간 (학습 변환에서 뺌).
  A4  정지 직전 기록: 정책 구간의 최근 --hil.pre_s 초 (state · 마지막 명령 · 1/4 크기 front/wrist 영상, 10 Hz) 를
      정지 순간 snapshots/pause_NNN.npz 로 저장. (교정만 녹화하는 공식 기본 모드는 정책 구간을 남기지 않음)
  A5  Space debounce: 전환(리더 이동 ~2 s) 도중 또는 전환이 끝난 뒤 --hil.debounce_s 초 안의 pause_resume 요청을 버리고 기록 · 경고.
      (공식 코드는 Space 두 번 → 리더 이동이 끝나자마자 정책 재개)
  A6  키 입력은 터미널에서만 (--hil.keyboard=terminal, 기본): DISPLAY 를 지워 pynput 전역 키 후킹을 쓰지 않게 한다.
  A7  교정 끝 (Tab) 에 리더 토크를 다시 켜기 전, 리더 Goal 레지스터 := 리더 현재 위치 (--hil.leader_goal_sync=true, 기본).
  A8  교정 구간만 follower max_relative_target 바꾸기 (--hil.correction_max_relative_target=keep 기본 = 공식과 같음).
      d2 · R1 · RC 녹화는 None (clamp 없음), 정책 평가는 8. none 이면 CORRECTING 동안만 None, 끝나면 원래 값으로 되돌림.
  A9  PAUSED 로 시작 (--hil.start_paused=true, 기본): 공식 코드는 모델 로딩이 끝나면 바로 정책이 움직인다.
      시작 시 리더를 follower 현재 자세로 2 s 동안 맞추고 (공식 teleop_smooth_move_to, 리더 토크 on) PAUSED 에서 기다린다 → Space 로 정책 시작.
  A10 정책 오류 래치 (2026-11-04 최우선): RTC 추론 오류가 처음 로그되는 순간 (lerobot.rollout.inference.rtc 의
      "RTC inference error" / "Fatal error in RTC thread", 또는 engine.failed)
      → RTC 스레드 즉시 멈춤 (policy_active clear, 락 없이) → 다음 틱부터 정책 명령 0
      → 주 루프에서 한 번: engine.pause · engine.reset (큐 비움 + epoch 증가 → 진행 중 chunk 버림) · interpolator.reset
      → follower 팔 5 관절 Goal := 현재 위치 (보낸 명령의 남은 이동을 덮어씀), 그리퍼는 마지막 명령 유지
      → PAUSED 로 강제 전환 (리더는 그 자세로 정렬), 이후 Space 로 정책 재개 불가 (교정 Tab · 종료 Esc 만 가능).
      공식 동작: 오류 뒤에도 큐에 남은 action 을 계속 보내고 0.5 s 간격 10 번 재시도 뒤 종료.
  A11 종료 처리: lerobot 의 자동 시작 자세 복귀를 쓰지 않는다 (Esc · 정상 종료 · 모든 오류).
      종료 시 follower 는 마지막 Goal 을 토크로 유지한 채 터미널에서 사용자가 고른다:
        home    = 시작 자세로 3 s 이동 뒤 토크 끄기 (follower 통신 오류가 있었으면 선택 불가)
        release = 지금 자세에서 토크 끄기 (follower · 리더를 손으로 받친 뒤)
        hold    = 토크 켠 채 종료 (Enter 만 · 입력 없음 · Ctrl+C 도 hold). 이후 처리는 사용자가 따로.
      터미널이 아니면 (시험) HIL_TEST_END_CHOICE 환경 변수, 없으면 hold.
  A12 화면 상태 전달 (tap, 2026-11-04 UI): --hil.tap=<dir> 이면 별도 스레드가 --hil.tap_hz (기본 10) 로
      <dir>/state.json (사실값만: phase · 대기 키 · 전환 · 리더 토크 · RTC 스레드 · 마지막 정책 명령 시각 · 표시 키 · 오류 · 종료 메뉴)
      과 <dir>/wrist.npy · front.npy (마지막 관측을 1/2 로 줄인 것) 를 원자적으로 쓴다. 화면 (tools/hil_viewer.py) 은 이것만 읽는다.
      제어 · 녹화 코드는 바꾸지 않는다: 리더 토크 함수 · 전환 함수는 원래 함수를 그대로 부르고 기록만 덧붙인다.
      tap 오류 5 번 연속이면 tap 만 멈추고 (tap_disabled 기록) 제어는 그대로. --hil.tap_log=<jsonl> 이면 시험용으로 매 기록을 덧붙인다.

옵션: --hil.events=<path> (기본: --dataset.root 옆 hil_events.jsonl) --hil.pre_s=3 --hil.debounce_s=0.8 --hil.keyboard=terminal|default
     --hil.leader_goal_sync=true|false  --hil.correction_max_relative_target=keep|none|<deg>  --hil.start_paused=true|false
"""

from __future__ import annotations

import collections
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

_logger = logging.getLogger("hil_dagger")
D2_EVAL = Path.home() / "so101_runs/main_k8/d2/eval"

HIL_DEFAULTS = {"events": "", "pre_s": 3.0, "debounce_s": 0.8, "keyboard": "terminal", "leader_goal_sync": True, "correction_max_relative_target": "keep", "start_paused": True, "tap": "", "tap_hz": 10.0, "tap_log": ""}


def _pop_hil(argv):
    opts = dict(HIL_DEFAULTS)
    rest = []
    for a in argv:
        if a.startswith("--hil."):
            k, _, v = a[len("--hil."):].partition("=")
            if k not in opts:
                raise SystemExit(f"unknown option --hil.{k}")
            opts[k] = (v.lower() in ("1", "true", "yes")) if isinstance(HIL_DEFAULTS[k], bool) else type(HIL_DEFAULTS[k])(v)
        else:
            rest.append(a)
    return opts, rest


def _arg(argv, name):
    for a in argv:
        if a.startswith(f"--{name}="):
            return a.split("=", 1)[1]
    return None


class EventLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "a", buffering=1)
        self.t0 = time.perf_counter()
        self.lock = threading.Lock()

    def write(self, kind, **kw):
        now = time.perf_counter()
        rec = {"t": round(now - self.t0, 4), "perf": now, "wall": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, **kw}
        with self.lock:
            self.f.write(json.dumps(rec, ensure_ascii=False, default=float) + "\n")
        return rec


def install(hil, argv):
    import numpy as np

    import lerobot.rollout.strategies.core as core_mod
    import lerobot.rollout.strategies.dagger as dagger_mod

    if hil["keyboard"] == "terminal":
        os.environ.pop("DISPLAY", None)
        os.environ.pop("WAYLAND_DISPLAY", None)

    # A1 — rollout_logged 가 core 를 패치했으면 그 함수, 아니면 lerobot 원래 함수. A10 래치 검사를 앞에 붙여 dagger 에 건다.
    _base_send = core_mod.send_next_action

    root = _arg(argv, "dataset.root")
    ev_path = hil["events"] or (str(Path(root).parent / "hil_events.jsonl") if root else "hil_events.jsonl")
    log = EventLog(ev_path)
    snap_dir = Path(ev_path).parent / "snapshots"
    st = {"strategy": None, "ctx": None, "last_obs": None, "last_cmd": None, "in_transition": False, "t_last_transition": -1e9,
          "ring": collections.deque(), "pause_n": 0, "tick": 0, "fault": None, "fault_handled": False, "fault_hold": None,
          "follower_io_error": None,
          # A12 화면용 기록 (읽기 전용 사실값)
          "session": "setup", "leader_torque": None, "transition": None, "transition_t0": None, "last_transition": None,
          "last_policy_send_t": None, "pause_t": None, "marks_current": [], "last_saved": None, "end_menu": None, "end_choice": None,
          "tap_stats": []}

    def _jpos(d):
        return None if d is None else {k: round(float(v), 3) for k, v in d.items() if k.endswith(".pos")}

    def _buffer_size(ds):
        w = getattr(ds, "writer", None)
        b = getattr(w, "episode_buffer", None) if w is not None else getattr(ds, "episode_buffer", None)
        return None if not b else int(b.get("size", 0))

    def _snapshot_fields():
        s, ctx = st["strategy"], st["ctx"]
        out = {}
        if ctx is None or s is None:
            return out
        ds = ctx.data.dataset
        out["episodes_saved"] = None if ds is None else int(ds.num_episodes)
        out["frames_in_current"] = None if ds is None else _buffer_size(ds)
        out["follower"] = _jpos(st["last_obs"])
        out["last_cmd"] = _jpos(st["last_cmd"])
        try:
            tel = ctx.hardware.teleop
            out["leader"] = _jpos(tel.get_action()) if tel is not None else None
        except Exception as e:  # 기록 실패는 동작에 영향 주지 않음
            out["leader"] = f"read_error: {e}"
        eng = s._engine
        q = getattr(eng, "action_queue", None)
        out["rtc_qsize"] = None if q is None else int(q.qsize())
        out["epoch"] = getattr(eng, "_reset_epoch", None)
        return out

    # A10 — 정책 오류 래치
    import lerobot.rollout.inference.rtc as rtc_mod

    def _latch(kind, msg):
        if st["fault"] is not None:
            return
        st["fault"] = {"kind": kind, "t": time.perf_counter(), "msg": str(msg)[:300]}
        s_ = st["strategy"]
        eng = None if s_ is None else s_._engine
        if eng is not None and hasattr(eng, "_policy_active"):
            eng._policy_active.clear()  # RTC 스레드 재시도 멈춤 (Event, 락 없음 — 오류 지점이 락 안이어도 교착 없음)
        log.write("policy_fault", fault_kind=kind, msg=str(msg)[:300], thread=threading.current_thread().name)
        _logger.error("HIL: 정책 오류 — 정책 명령 차단, RTC 큐 무효화, 정지로 전환합니다 (%s)", kind)

    class _FaultHandler(logging.Handler):
        def emit(self, rec):
            if rec.levelno >= logging.ERROR:
                m = rec.getMessage()
                if m.startswith("RTC inference error") or m.startswith("Fatal error in RTC thread"):
                    _latch("inference_error", m)

    rtc_mod.logger.addHandler(_FaultHandler(level=logging.ERROR))

    def _handle_fault(ctx, interpolator):
        """주 루프에서 한 번: 큐 · 지연 action 무효화, 남은 이동 덮어쓰기, PAUSED 강제."""
        st["fault_handled"] = True
        eng = ctx.policy.inference
        q = getattr(eng, "action_queue", None)
        q_before = None if q is None else int(q.qsize())
        ep_before = getattr(eng, "_reset_epoch", None)
        eng.pause()
        eng.reset()
        interpolator.reset()
        keys = list(ctx.data.ordered_action_keys)
        obs, last = st["last_obs"] or {}, st["last_cmd"] or {}
        hold = {}
        for k in keys:
            if k.startswith("gripper"):
                hold[k] = float(last.get(k, obs.get(k)))
            else:
                hold[k] = float(obs.get(k, last.get(k)))
        st["fault_hold"] = hold
        ctx.hardware.robot_wrapper.send_action(hold)
        ev = st["strategy"]._events
        with ev._lock:
            if ev._phase.value == "autonomous":
                ev._pending_transition = "pause_resume"
        q_after = None if q is None else int(q.qsize())
        st["fault"].update(handled=True, rtc_qsize_before=q_before, rtc_qsize_after=q_after)
        log.write("policy_fault_handled", rtc_qsize_before=q_before, rtc_qsize_after=q_after, epoch_before=ep_before,
                  epoch_after=getattr(eng, "_reset_epoch", None), hold=_jpos(hold),
                  since_fault_s=round(time.perf_counter() - st["fault"]["t"], 4))

    def guarded_send(obs_processed, obs_raw, ctx, interpolator, timer=None):
        eng = ctx.policy.inference
        if st["fault"] is None and getattr(eng, "failed", False):
            _latch("engine_failed", getattr(eng, "failure_traceback", "") or "")
        if st["fault"] is not None:
            if not st["fault_handled"]:
                _handle_fault(ctx, interpolator)
            return None
        out = _base_send(obs_processed, obs_raw, ctx, interpolator, timer)
        if out is not None:
            st["last_policy_send_t"] = time.perf_counter()
        return out

    dagger_mod.send_next_action = guarded_send

    # 관측 · 명령 캐시 (ThreadSafeRobot 수준; 동작 변경 없음)
    from lerobot.rollout.robot_wrapper import ThreadSafeRobot

    _orig_obs, _orig_send = ThreadSafeRobot.get_observation, ThreadSafeRobot.send_action

    def get_observation(self):
        try:
            obs = _orig_obs(self)
        except Exception as e:
            if st["follower_io_error"] is None:
                st["follower_io_error"] = f"get_observation: {type(e).__name__}: {e}"
                log.write("follower_io_error", op="get_observation", error=str(e)[:300])
            raise
        st["last_obs"] = obs
        return obs

    def send_action(self, action):
        # A10: 정책 오류 뒤 PAUSED 유지 명령은 '마지막 정책 명령' 대신 오류 순간의 hold 목표 (팔 = 현재 위치)
        s_ = st["strategy"]
        if st["fault_hold"] is not None and s_ is not None and s_._events.phase.value == "paused":
            action = dict(st["fault_hold"])
        try:
            out = _orig_send(self, action)
        except Exception as e:
            if st["follower_io_error"] is None:
                st["follower_io_error"] = f"send_action: {type(e).__name__}: {e}"
                log.write("follower_io_error", op="send_action", error=str(e)[:300])
            raise
        st["last_cmd"] = action if isinstance(action, dict) else st["last_cmd"]
        return out

    ThreadSafeRobot.get_observation = get_observation
    ThreadSafeRobot.send_action = send_action

    # A4 — 정책 구간 ring (정책 관측 처리 시점, 3 틱마다 = 10 Hz)
    S = dagger_mod.DAggerStrategy
    _orig_proc = S._process_observation_and_notify
    pre_s = float(hil["pre_s"])

    def _proc(self, processors, obs_raw):
        out = _orig_proc(self, processors, obs_raw)
        st["tick"] += 1
        if pre_s > 0 and st["tick"] % 3 == 0:
            item = {"t": time.perf_counter() - log.t0, "state": np.array([obs_raw.get(k, np.nan) for k in _keys()], np.float32),
                    "cmd": np.array([(st["last_cmd"] or {}).get(k, np.nan) for k in _keys()], np.float32)}
            for cam in ("front", "wrist"):
                img = obs_raw.get(cam)
                if img is not None:
                    item[cam] = np.ascontiguousarray(img[::4, ::4])
            st["ring"].append(item)
            while st["ring"] and item["t"] - st["ring"][0]["t"] > pre_s:
                st["ring"].popleft()
        return out

    S._process_observation_and_notify = _proc

    def _keys():
        ctx = st["ctx"]
        return list(ctx.data.ordered_action_keys) if ctx is not None else []

    def _dump_ring():
        if not st["ring"]:
            return None
        snap_dir.mkdir(parents=True, exist_ok=True)
        st["pause_n"] += 1
        p = snap_dir / f"pause_{st['pause_n']:03d}.npz"
        items = list(st["ring"])
        arrs = {"t": np.array([i["t"] for i in items]), "state": np.stack([i["state"] for i in items]),
                "cmd": np.stack([i["cmd"] for i in items]), "keys": np.array(_keys())}
        for cam in ("front", "wrist"):
            if all(cam in i for i in items):
                arrs[cam] = np.stack([i[cam] for i in items])
        np.savez_compressed(p, **arrs)
        st["ring"].clear()
        return str(p)

    # A8 — 교정 구간 clamp
    cmrt = str(hil["correction_max_relative_target"]).lower()

    def _set_clamp(phase_value):
        if cmrt == "keep" or st["ctx"] is None:
            return
        cfg = st["ctx"].hardware.robot_wrapper.inner.config
        if "orig_mrt" not in st:
            st["orig_mrt"] = cfg.max_relative_target
        want = (None if cmrt == "none" else float(cmrt)) if phase_value == "correcting" else st["orig_mrt"]
        if cfg.max_relative_target != want:
            cfg.max_relative_target = want
            log.write("clamp", phase=phase_value, max_relative_target=want)

    # A2/A5 — 전환 기록 · debounce
    _orig_apply = S._apply_transition

    def _apply(self, old_phase, new_phase, *a, **k):
        st["transition"], st["transition_t0"] = [old_phase.value, new_phase.value], time.perf_counter()
        if old_phase.value == "autonomous" and new_phase.value == "paused":
            st["pause_t"] = st["transition_t0"]
        st["in_transition"] = True
        before = _snapshot_fields()
        snap = _dump_ring() if (old_phase.value == "autonomous" and new_phase.value == "paused") else None
        t_a = time.perf_counter()
        # A7 — 교정 끝 (CORRECTING→PAUSED) 에서 리더 토크를 켜기 전에 Goal := 현재 위치 (토크 꺼진 상태에서 쓰기).
        #      공식 코드는 enable_torque 만 부른다 → Goal 레지스터에 정지 때 send_feedback 값이 남아 있으면 리더가 그 자세로 되돌아간다.
        if hil["leader_goal_sync"] and old_phase.value == "correcting" and new_phase.value == "paused":
            try:
                from lerobot.common.control_utils import teleop_supports_feedback

                tel = st["ctx"].hardware.teleop
                if tel is not None and teleop_supports_feedback(tel):
                    pos = tel.get_action()
                    tel.send_feedback(pos)
                    log.write("leader_goal_sync", leader=_jpos(pos))
            except Exception as e:
                log.write("leader_goal_sync_error", error=str(e))
        if st["fault_hold"] is not None and old_phase.value == "autonomous" and new_phase.value == "paused" and len(a) >= 5:
            a = list(a)
            a[4] = dict(st["fault_hold"])  # prev_action: 리더를 오류 hold 목표로 정렬
        if old_phase.value == "paused" and new_phase.value == "correcting":
            st["fault_hold"] = None  # 사람 제어 시작 → hold 덮어쓰기 끝
        try:
            return _orig_apply(self, old_phase, new_phase, *a, **k)
        finally:
            _set_clamp(new_phase.value)
            after_leader = None
            try:
                tel = st["ctx"].hardware.teleop if st["ctx"] is not None else None
                after_leader = _jpos(tel.get_action()) if tel is not None else None
            except Exception as e:
                after_leader = f"read_error: {e}"
            log.write("transition", old=old_phase.value, new=new_phase.value, blocking_s=round(time.perf_counter() - t_a, 3),
                      pre_pause_snapshot=snap, leader_after=after_leader, **before)
            if old_phase.value == "correcting" and new_phase.value == "paused":
                # 저장 직전 (공식 루프는 이 전환 뒤 save_episode) — 이 판의 표시 키를 화면용으로 묶는다 (QA 와 같은 귀속: 저장 전 표시)
                st["last_saved"] = {"episode": before.get("episodes_saved"), "frames": before.get("frames_in_current"),
                                    "marks": list(st["marks_current"]), "ended_during_correction": False}
                st["marks_current"] = []
            st["last_transition"] = [old_phase.value, new_phase.value]
            st["transition_end_t"] = time.perf_counter()
            st["t_last_transition"] = time.perf_counter()
            st["in_transition"] = False

    S._apply_transition = _apply

    E = dagger_mod.DAggerEvents
    _orig_req = E.request_transition
    _orig_reset = E.reset

    def ev_reset(self):
        _orig_reset(self)
        if hil["start_paused"]:
            with self._lock:
                self._phase = dagger_mod.DAggerPhase.PAUSED

    E.reset = ev_reset
    deb = float(hil["debounce_s"])

    def request_transition(self, event):
        if event == "pause_resume" and st["fault"] is not None:
            log.write("key_dropped", event=event, phase=self.phase.value, reason="policy_fault_latched")
            _logger.warning("HIL: 정책 오류 뒤에는 정책을 재개하지 않습니다 (Tab 교정 · Esc 종료만)")
            return
        dt = time.perf_counter() - st["t_last_transition"]
        # pause_resume 만 막는다: 전환(리더 이동 ~2 s) 도중 또는 끝난 뒤 debounce_s 안. correction(Tab) 은 공식 동작 그대로.
        if event == "pause_resume" and (st["in_transition"] or dt < deb):
            log.write("key_dropped", event=event, phase=self.phase.value, in_transition=st["in_transition"],
                      since_last_transition_s=round(dt, 3), pending=self._pending_transition)
            _logger.warning("HIL: Space 무시됨 (전환 중이거나 직후 %.1f s) — 다시 누르세요", deb)
            return
        log.write("key", event=event, phase=self.phase.value)
        _orig_req(self, event)

    E.request_transition = request_transition

    # A3 — 표시 키: 공식 dispatch 앞에 끼운다
    _orig_ckl = dagger_mod.create_key_listener
    marks = {"m": "recovery_done", "1": "type_R1", "2": "type_R2", "3": "type_R2O", "g": "first_grasp_ok", "h": "first_grasp_fail",
             "b": "final_success", "f": "final_fail", "r": "reset_segment"}

    def create_key_listener(dispatch, **kw):
        def wrapped(name):
            if name in marks:
                s = st["strategy"]
                log.write("mark", mark=marks[name], phase=None if s is None else s._events.phase.value, **_snapshot_fields())
                st["marks_current"].append(marks[name])
                return
            if name == "esc":
                s = st["strategy"]
                log.write("key", event="esc", phase=None if s is None else s._events.phase.value)
            dispatch(name)

        kw["controls_help"] = kw.get("controls_help", "") + ", m=복구 완료, 1/2/3=R1/R2/R2-O, g/h=첫 파지 성공/실패, b/f=최종 성공/실패, r=원위치 구간"
        return _orig_ckl(wrapped, **kw)

    dagger_mod.create_key_listener = create_key_listener

    _orig_setup, _orig_teardown = S.setup, S.teardown

    def setup(self, ctx):
        st["strategy"], st["ctx"] = self, ctx
        log.write("session_start", argv=argv, hil=hil, keyboard_backend="terminal-only" if hil["keyboard"] == "terminal" else "default")
        tel_ = ctx.hardware.teleop
        if tel_ is not None and hasattr(tel_, "enable_torque") and hasattr(tel_, "disable_torque"):
            # A12: 리더 토크 상태 기록 (원래 함수를 그대로 부름). SOLeader.connect → configure 에서 이미 토크 꺼짐.
            st["leader_torque"] = False
            _en, _dis = tel_.enable_torque, tel_.disable_torque

            def enable_torque(*a_, **k_):
                r_ = _en(*a_, **k_)
                st["leader_torque"] = True
                return r_

            def disable_torque(*a_, **k_):
                st["leader_torque"] = False
                return _dis(*a_, **k_)

            tel_.enable_torque, tel_.disable_torque = enable_torque, disable_torque
        _start_tap()
        out = _orig_setup(self, ctx)
        if hil["start_paused"]:
            from lerobot.common.control_utils import teleop_smooth_move_to, teleop_supports_feedback

            tel = ctx.hardware.teleop
            obs = ctx.hardware.robot_wrapper.get_observation()
            target = {k: float(v) for k, v in obs.items() if k.endswith(".pos")}
            if tel is not None and teleop_supports_feedback(tel):
                teleop_smooth_move_to(tel, target)  # 리더 토크 on, follower 현재 자세로
            log.write("start_paused", follower=_jpos(target), leader=_jpos(tel.get_action()) if tel is not None else None)
            _logger.warning("HIL: 정지(PAUSED) 상태로 시작 — 큐브를 놓고 Space 를 누르면 정책이 움직입니다")
        st["session"] = "running"
        return out

    def teardown(self, ctx):
        st["session"] = "teardown"
        f = _snapshot_fields()
        if self._events.phase.value == "correcting":
            st["last_saved"] = {"episode": (f.get("episodes_saved") or 1) - 1, "frames": st.get("tap_frames_last"),
                                "marks": list(st["marks_current"]), "ended_during_correction": True}
        log.write("session_end", phase_at_end=self._events.phase.value,
                  ended_during_correction=self._events.phase.value == "correcting", **f)
        _set_clamp("teardown")
        try:
            return _orig_teardown(self, ctx)
        finally:
            st["session"] = "ended"
            _stop_tap()

    S.setup, S.teardown = setup, teardown

    # A11 — 종료: 자동 복귀 없음, 사용자가 home / release / hold 선택
    def _end_choice(follower_ok):
        opts = ["home", "release", "hold"] if follower_ok else ["release", "hold"]
        st["end_menu"] = {"options": opts, "follower_ok": follower_ok}
        try:
            c = _end_choice_inner(follower_ok, opts)
        finally:
            st["end_menu"] = None
        st["end_choice"] = c[0]
        return c

    def _end_choice_inner(follower_ok, opts):
        if not sys.stdin.isatty():
            c = os.environ.get("HIL_TEST_END_CHOICE", "hold").strip().lower()
            return (c if c in opts else "hold"), "env" if "HIL_TEST_END_CHOICE" in os.environ else "non_tty_default"
        print("\n=== 세션 종료: follower 는 마지막 목표 자세를 토크로 유지 중 (새 명령 없음) ===", flush=True)
        if follower_ok:
            print("  home    = 시작 자세로 3 초 동안 이동한 뒤 토크 끄기 (경로에 손·물체가 없는지 먼저 확인)")
        else:
            print(f"  (home 선택 불가: follower 통신 오류 — {st['follower_io_error']})")
        print("  release = 지금 자세에서 토크 끄기 (follower · 리더를 손으로 받친 뒤)")
        print("  hold    = 토크 켠 채 프로그램 종료 (Enter 만 눌러도 hold)", flush=True)
        while True:
            try:
                c = input("선택 > ").strip().lower() or "hold"
            except (EOFError, KeyboardInterrupt, SystemExit):
                return "hold", "interrupted"
            if c in opts:
                return c, "tty"
            print(f"  {opts} 중 하나를 입력하세요")

    def _teardown_hardware(self, hw, return_to_initial_position=True):
        if self._engine is not None:
            self._engine.stop()
        robot = hw.robot_wrapper.inner
        follower_ok = st["follower_io_error"] is None
        choice, src = _end_choice(follower_ok)
        log.write("end_choice", choice=choice, source=src, follower_ok=follower_ok, options=["home", "release", "hold"] if follower_ok else ["release", "hold"],
                  lerobot_return_flag_ignored=bool(return_to_initial_position),
                  fault=None if st["fault"] is None else st["fault"]["kind"])
        if robot.is_connected:
            try:
                if choice == "home" and follower_ok and hw.initial_position:
                    ok = self.return_to_initial_position(hw)
                    log.write("home_done", ok=bool(ok))
                robot.config.disable_torque_on_disconnect = choice != "hold"
                robot.disconnect()
                log.write("follower_disconnected", torque_off=choice != "hold")
            except Exception as e:
                log.write("follower_disconnect_error", error=str(e)[:300])
                _logger.error("HIL: follower 연결 해제 실패 (%s) — 토크 상태를 알 수 없음, 전원으로 정지하세요", e)
        tel = hw.teleop
        if tel is not None and tel.is_connected:
            try:
                if choice == "hold":
                    tel.bus.disconnect(disable_torque=False)
                else:
                    tel.disconnect()
                log.write("leader_disconnected", torque_off=choice != "hold")
            except Exception as e:
                log.write("leader_disconnect_error", error=str(e)[:300])

    S._teardown_hardware = _teardown_hardware

    # A12 — tap (화면용 사실값 · 영상). 제어 루프와 다른 스레드, 읽기만.
    def _tap_snapshot():
        now = time.perf_counter()
        s_, ctx = st["strategy"], st["ctx"]
        ev = None if s_ is None else s_._events
        eng = None if s_ is None else s_._engine
        ds = None if ctx is None else ctx.data.dataset
        lp, pt = st["last_policy_send_t"], st["pause_t"]
        fr = None if ds is None else _buffer_size(ds)
        st["tap_frames_last"] = fr if fr else st.get("tap_frames_last")
        marks_ = list(st["marks_current"])
        typ = next((m[5:].replace("R2O", "R2-O") for m in reversed(marks_) if m.startswith("type_")), None)
        f = st["fault"]
        cfg = None if ctx is None else ctx.hardware.robot_wrapper.inner.config
        return {
            "t": now, "wall": time.strftime("%H:%M:%S"), "session": st["session"],
            "phase": None if ev is None else ev._phase.value, "pending": None if ev is None else ev._pending_transition,
            "in_transition": bool(st["in_transition"]), "transition": st["transition"], "last_transition": st["last_transition"],
            "transition_age": None if st["transition_t0"] is None else round(now - st["transition_t0"], 3),
            "since_transition_end": None if st.get("transition_end_t") is None else round(now - st["transition_end_t"], 3),
            "leader_torque": st["leader_torque"],
            "policy_active": None if eng is None or not hasattr(eng, "_policy_active") else bool(eng._policy_active.is_set()),
            "last_policy_send_age": None if lp is None else round(now - lp, 3),
            "policy_since_pause": bool(lp is not None and pt is not None and lp > pt),
            "fault": None if f is None else {k: f.get(k) for k in ("kind", "msg", "handled", "rtc_qsize_before", "rtc_qsize_after")},
            "follower_io_error": st["follower_io_error"],
            "episodes_saved": None if ds is None else int(ds.num_episodes), "frames_in_current": fr,
            "marks_current": marks_, "type_current": typ, "last_saved": st["last_saved"],
            "end_menu": st["end_menu"], "end_choice": st["end_choice"],
            "clamp_deg": None if cfg is None else cfg.max_relative_target,
            "start_paused": bool(hil["start_paused"]),
            # 장치 경로가 /nonexistent (가짜 장치 시험) 이면 화면에 SIMULATION 표시
            "sim": bool(cfg is not None and str(getattr(cfg, "port", "")).startswith("/nonexistent")),
        }

    def _atomic_write(path, data_bytes):
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as fh:
            fh.write(data_bytes)
        os.replace(tmp, path)

    def _tap_loop():
        d = Path(hil["tap"])
        d.mkdir(parents=True, exist_ok=True)
        period = 1.0 / max(1.0, float(hil["tap_hz"]))
        logf = open(hil["tap_log"], "a", buffering=1) if hil["tap_log"] else None
        fail_at = int(os.environ.get("HIL_TAP_TEST_FAIL_AT", "0") or 0)  # 시험 전용 (tap 오류 격리 확인)
        fails, n, last_obs_id = 0, 0, None
        import io

        while not st["tap_stop"].is_set():
            t0 = time.perf_counter()
            try:
                n += 1
                if fail_at and n >= fail_at:
                    raise RuntimeError("tap test fault")
                snap = _tap_snapshot()
                _atomic_write(d / "state.json", json.dumps(snap, ensure_ascii=False, default=str).encode())
                obs = st["last_obs"]
                if obs is not None and id(obs) != last_obs_id:
                    last_obs_id = id(obs)
                    for cam in ("wrist", "front"):
                        img = obs.get(cam)
                        if img is not None:
                            small = np.ascontiguousarray(img[::2, ::2]) if img.shape[0] >= 240 else np.ascontiguousarray(img)
                            buf = io.BytesIO()
                            np.save(buf, small)
                            _atomic_write(d / f"{cam}.npy", buf.getvalue())
                if logf is not None:
                    logf.write(json.dumps(snap, ensure_ascii=False, default=str) + "\n")
                fails = 0
            except Exception as e:  # tap 오류는 제어에 전달하지 않는다
                fails += 1
                if fails >= 5:
                    log.write("tap_disabled", error=str(e)[:200], iterations=n)
                    _logger.warning("HIL: 화면 상태 전달(tap) 을 멈춤 (%s) — 제어는 계속됩니다", e)
                    break
            dt = time.perf_counter() - t0
            if len(st["tap_stats"]) < 100000:
                st["tap_stats"].append(dt)
            st["tap_stop"].wait(max(0.0, period - dt))
        if logf is not None:
            logf.close()

    def _start_tap():
        if not hil["tap"] or st.get("tap_thread") is not None:
            return
        st["tap_stop"] = threading.Event()
        st["tap_thread"] = threading.Thread(target=_tap_loop, name="hil-tap", daemon=True)
        st["tap_thread"].start()
        log.write("tap_start", dir=hil["tap"], hz=hil["tap_hz"])

    def _stop_tap():
        th = st.get("tap_thread")
        if th is None:
            return
        try:  # 마지막 상태 (ended) 한 번 더 쓴 뒤 멈춤 (시험 기록에도)
            Path(hil["tap"]).mkdir(parents=True, exist_ok=True)
            fin = json.dumps(_tap_snapshot(), ensure_ascii=False, default=str)
            _atomic_write(Path(hil["tap"]) / "state.json", fin.encode())
            if hil["tap_log"] and th.is_alive():
                with open(hil["tap_log"], "a") as fh:
                    fh.write(fin + "\n")
        except Exception:
            pass
        st["tap_stop"].set()
        th.join(timeout=1.0)
        a_ = np.array(st["tap_stats"]) * 1000 if st["tap_stats"] else np.zeros(1)
        log.write("tap_stats", n=int(len(st["tap_stats"])), mean_ms=round(float(a_.mean()), 3),
                  p99_ms=round(float(np.percentile(a_, 99)), 3), max_ms=round(float(a_.max()), 3))

    def mark(name):
        """시험 · 외부 입력용: 표시 키와 같은 처리."""
        if name in marks:
            s = st["strategy"]
            log.write("mark", mark=marks[name], phase=None if s is None else s._events.phase.value, **_snapshot_fields())
            st["marks_current"].append(marks[name])

    st["mark"] = mark
    st["log"] = log
    return st


def main():
    hil, rest = _pop_hil(sys.argv)
    sys.argv = rest
    sys.path.insert(0, str(D2_EVAL))
    import rollout_logged as rl  # import 시 --arm_filter 등 자기 옵션을 sys.argv 에서 뺀다

    rl_state = rl.install(rl._OPTS) if rl._OPTS["active"] else None
    sys.argv = rl._ARGV
    st = install(hil, list(sys.argv))
    st["log"].write("rollout_logged", active=bool(rl_state), opts={k: v for k, v in rl._OPTS.items()})
    try:
        rl.lr.main()
    finally:
        if rl_state is not None and rl_state["log"] is not None:
            rl_state["log"].close()


if __name__ == "__main__":
    main()
