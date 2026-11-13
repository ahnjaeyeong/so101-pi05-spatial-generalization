"""종료 처리 — 자동 원위치 복귀 없음 · 제자리 유지 · 토크 유지 (rft01 실물 파일럿, 2026-11-05 v2).

왜: lerobot 0.6.2 episodic 은 판 사이 (reset · 다시 찍기) 와 종료 (_teardown_hardware: 정상 종료 · 예외 · Ctrl+C 모두) 에
    return_to_initial_position 으로 팔을 시작 자세로 옮기고, eval_ui 는 이것을 30°/s 보간 + 4 s 추가 추종으로 바꿔 둔다.
    이 이동은 정책 루프 밖이라 r2_safety · fault_latch 검사를 받지 않는다. 이어서 disconnect 가 토크를 끄면 팔이 자기 무게로 내려온다.

이 모듈이 바꾸는 것 (rollout_logged.py shim 이 install, 다른 파일은 수정하지 않음):
  E1 EpisodicStrategy.return_to_initial_position := 차단 (아무 명령도 보내지 않고 False, end_hold.csv 에 auto_return_blocked 기록).
     eval_ui 는 RolloutStrategy (기반 클래스) 에 보강 함수를 넣는다 → 하위 클래스 속성이 먼저 잡히므로 eval_ui 보강도 불리지 않는다.
     (run_trial.sh 는 공식 옵션 --return_to_initial_position=false · --strategy.reset_to_initial_position=false 도 같이 준다.)
  E2 정책 루프가 어떤 이유로 끝나든 (판 시간 · → · r2_safety 정지 · fault_latch · 예외 · Ctrl+C) finally 에서 한 번:
     팔 5 관절 Goal := 지금 Present (이미 보낸 ≤ 8° 남은 이동을 덮어씀). 그리퍼는 쓰지 않는다 (쥔 큐브를 놓지 않음).
  E3 다시 찍기 (← = rerecord) 는 이 파일럿에서 '버리고 끝내기' 로 바꾼다 (stop_recording). 원래는 reset 단계 → 복귀 → 같은 프로세스에서
     정책 재시작인데, 복귀가 없으면 다른 자세에서 다시 시작하게 되므로. 다시 하려면 run_trial.sh 를 RERUN 으로 새로 실행.
  E4 EpisodicStrategy._teardown_hardware := 엔진 정지 → (가능하면) 한 번 더 제자리 유지 → 상태 기록 → bus.disconnect(disable_torque=False)
     · 카메라 disconnect. **토크는 켠 채로 남는다** (서보는 마지막 Goal = 멈춘 자리를 계속 유지). 복귀 · 토크 끄기는 scripts/safe_home.py (사용자 명시 실행).
  기록: <run>/end_hold.csv (이벤트) · <run>/end_state.json (끝난 이유 · 시작 자세 · 끝 자세 · 차이 · 토크 상태 · 차단한 복귀 호출 수)

E5 (11-05 v3, END_HOLD_HOME=1 — run_series.sh 가 한 모델의 여러 시행을 한 프로세스에서 돌릴 때만):
  판 사이 (lerobot reset 단계의 return_to_initial_position) 와 종료 (E4) 에서, 끝난 이유가 HOMEABLE 이면
  scripts/safe_home.py 의 checks() · move() 를 그대로 써서 시작 자세로 천천히 (15°/s) 옮긴다. 점검 (토크 · 걸림 · pan · 범위 ·
  목표가 접은 자세 · 끝 자세 일치 · 이동량) 이 하나라도 실패하면 움직이지 않고 그 판에서 세션을 끝낸다 (stop_recording, 토크 유지).
  Ctrl+C (shutdown_event) 는 이동 중에도 즉시 Goal := Present.
  HOMEABLE: episode_end_or_user_next · r2_safety_stop · fault_latch · engine_failed_shutdown · user_rerecord.
  Ctrl+C · 사용자 종료 · 예외로 끝나면 움직이지 않는다 (v2 와 같음).
  fault_latch 는 프로세스 안에서 풀리지 않으므로 복귀 뒤 세션을 끝낸다 (run_series.sh 가 남은 시행을 새로 띄움).
  v3.1: 판 사이 복귀가 도착하면 그리퍼도 시작 값으로 (30/s). 팔 복귀가 실패 · Ctrl+C 면 그리퍼는 쓰지 않는다.
  이 모드에서 ← (다시 찍기) 는 lerobot 기본 동작 (복귀 → 같은 판 다시) 으로 둔다 (E3 끔).

주의 (코드로 해결 안 됨): 다음 lerobot connect (다음 시행) 는 SOFollower.configure() 에서 잠깐 토크를 끈다 → 팔이 시작 자세가 아니면 내려온다.
  run_trial.sh 게이트가 앞 시행 end_state.json 을 보고 막는다 (safe_home.py 또는 gate.sh rest).
"""

import csv
import functools
import inspect
import json
import logging
import os
import sys
import threading
import time
import traceback

log = logging.getLogger("lerobot.end_hold")
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
LAST_STATE = None
FIELDS = ["wall", "perf", "event", "detail"]


class _Log:
    def __init__(self, path):
        self.lock = threading.Lock()
        new = not os.path.exists(path)
        self.fh = open(path, "a", newline="")
        self.w = csv.DictWriter(self.fh, fieldnames=FIELDS)
        if new:
            self.w.writeheader()
        self.fh.flush()

    def row(self, event, detail=""):
        with self.lock:
            self.w.writerow({"wall": f"{time.time():.4f}", "perf": f"{time.perf_counter():.5f}", "event": event, "detail": str(detail)[:500]})
            self.fh.flush()


def install(r2_state=None, fl_state=None):
    global LAST_STATE
    from lerobot.rollout.strategies.episodic import EpisodicStrategy

    run_dir = os.environ.get("EVAL_UI_RUN_DIR") or os.path.dirname(os.environ.get("ROLLOUT_FILTER_LOG", "./x"))
    E = {"log": _Log(os.path.join(run_dir, "end_hold.csv")), "run_dir": run_dir, "blocked_returns": [], "holds": [], "ended_by": None,
         "exception": None, "events": None, "robot": None, "initial_position": None, "rerecord_to_stop": 0, "teardown": None}
    LAST_STATE = E
    E["home_mode"] = os.environ.get("END_HOLD_HOME") == "1"
    E["homes"] = []
    E["ctx"] = None
    if E["home_mode"]:
        import importlib.util
        os.environ["SAFE_HOME_NO_REEXEC"] = "1"
        sp = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "scripts", "safe_home.py")
        spec = importlib.util.spec_from_file_location("pilot_safe_home", sp)
        E["SH"] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(E["SH"])
        E["log"].row("install", f"E5 home between/at end via {sp}")
        print("[end_hold] E5 home mode: 판 사이 · 종료 때 safe_home 점검 + 15°/s 복귀 (Ctrl+C · 사용자 종료 · 예외 뒤에는 안 움직임)", flush=True)
    E["log"].row("install", "E1 return blocked · E2 end hold · E3 rerecord→stop · E4 teardown hold (torque on)")
    print("[end_hold] installed (auto-return blocked, torque kept on at exit)", flush=True)

    # E1
    def blocked_return(hw=None, duration_s=3.0, fps=50, *a, **k):
        if E["home_mode"] and hw is not None:
            return safe_return(hw, "between_episodes")
        caller = "".join(traceback.format_stack(limit=4)[:-1]).replace("\n", " | ")[-300:]
        E["blocked_returns"].append({"perf": time.perf_counter(), "caller": caller})
        E["log"].row("auto_return_blocked", caller)
        log.warning("END_HOLD 자동 원위치 복귀 차단 (명령 0) — 복귀는 scripts/safe_home.py 로")
        return False

    EpisodicStrategy.return_to_initial_position = staticmethod(blocked_return)

    def hold_here(robot_wrapper, why):
        """팔 5 관절 Goal := Present. 그리퍼는 건드리지 않음. 반환 hold dict 또는 None."""
        try:
            inner = getattr(robot_wrapper, "inner", robot_wrapper)
            bus = inner.bus
            lock = getattr(robot_wrapper, "_lock", None)
            ctx_ = lock if lock is not None else _Null()
            with ctx_:
                pres = bus.sync_read("Present_Position")
                hold = {j: float(pres[j]) for j in ARM if j in pres}
                bus.sync_write("Goal_Position", hold)
            E["holds"].append({"perf": time.perf_counter(), "why": why, "hold": hold})
            E["log"].row("hold", f"{why} " + " ".join(f"{j}={v:.2f}" for j, v in hold.items()))
            return hold
        except Exception as e:  # 유지 명령 실패 — 기록만 (서보는 마지막 Goal 유지)
            E["log"].row("hold_failed", f"{why} {type(e).__name__}: {e}")
            log.error("END_HOLD 제자리 유지 명령 실패 (%s): %s", why, e)
            return None

    def safe_return(hw, where):
        """E5: safe_home 의 점검 · 이동을 프로세스 안에서. 반환 True = 도착."""
        SH = E["SH"]
        why = E["ended_by"] or "unknown"
        rec = {"perf": time.perf_counter(), "where": where, "ended_by": why, "ok": False}
        E["homes"].append(rec)
        events = E["events"]
        sd = getattr(getattr(E["ctx"], "runtime", None), "shutdown_event", None)
        if sd is not None and sd.is_set():
            why = "shutdown_signal"  # Ctrl+C 뒤 (판 사이 · 복귀 도중 포함) 에는 움직이지 않음
            rec["ended_by"] = why
        if why not in HOMEABLE:
            rec["result"] = "not_homeable"
            E["log"].row("home_skip", f"{where} ended_by={why} — 움직이지 않음")
            log.warning("END_HOLD 복귀 안 함 (%s 로 끝남)", why)
            if events is not None:
                events["stop_recording"] = True
            return False
        robot_w = hw.robot_wrapper
        inner = getattr(robot_w, "inner", robot_w)
        bus = _LockedBus(inner.bus, getattr(robot_w, "_lock", None))
        init = dict(hw.initial_position or {})
        target = {j: float(init[f"{j}.pos"]) for j in ARM if f"{j}.pos" in init} if init else None
        try:
            pres = bus.sync_read("Present_Position")
            goal = bus.sync_read("Goal_Position")
            torque = bus.sync_read("Torque_Enable", normalize=False)
            limits = None
            try:
                cal = inner.calibration
                lo = inner.bus._normalize({cal[j].id: cal[j].range_min for j in cal})
                hi = inner.bus._normalize({cal[j].id: cal[j].range_max for j in cal})
                limits = {j: (min(lo[cal[j].id], hi[cal[j].id]), max(lo[cal[j].id], hi[cal[j].id])) for j in cal}
            except Exception:
                limits = None
            last_hold = (E["holds"][-1]["hold"] if E["holds"] else None) or {j: float(pres[j]) for j in ARM}
            es = {"initial_position": init, "end_present_arm": last_hold}
            C = SH.checks(pres, goal, torque, limits, es, target)
            rec["checks"] = [{"name": n, "pass": ok_, "detail": d[:200]} for n, ok_, d in C]
            bad = [n for n, ok_, _ in C if not ok_]
            if bad or target is None:
                rec["result"] = f"refused {bad}"
                E["log"].row("home_refused", f"{where} {bad}")
                log.error("END_HOLD 복귀 점검 실패 %s — 움직이지 않고 세션 종료 (토크 유지)", bad)
                print(f"[end_hold] 복귀 점검 실패 {bad} — 움직이지 않음. 세션을 끝냅니다 (팔은 그 자리, 토크 유지).", flush=True)
                if events is not None:
                    events["stop_recording"] = True
                return False
            dist = max(abs(target[j] - float(pres[j])) for j in ARM)
            print(f"[end_hold] 시작 자세로 복귀 {dist:.0f}° · {SH.SPEED:.0f}°/s (~{dist / SH.SPEED:.1f} s). 멈추려면 Ctrl+C", flush=True)
            E["log"].row("home_start", f"{where} dist={dist:.1f}")
            R = SH.move(bus, {j: float(pres[j]) for j in ARM}, target, interrupt=(lambda k: sd is not None and sd.is_set()))
            rec.update(move={k: v for k, v in R.items() if k != "final"}, final=R.get("final"))
            rec["ok"] = bool(R.get("ok"))
            E["log"].row("home_end", f"{where} {R.get('reason')} ticks={R.get('ticks')} max_err={R.get('max_err', 0):.1f}")
            if not R.get("ok"):
                log.error("END_HOLD 복귀 도중 멈춤 (%s) — 그 자리 유지, 세션 종료", R.get("reason"))
                print(f"[end_hold] 복귀 도중 멈춤 ({R.get('reason')}) — 그 자리 유지 (토크 켬), 세션 종료.", flush=True)
                if events is not None:
                    events["stop_recording"] = True
                return False
            print("[end_hold] 복귀 완료.", flush=True)
            if where in ("between_episodes", "teardown"):  # v3.2 (11-13): 세션 끝에서도 닫음 — 열린 채 끝난 세션 뒤 다음 세션이 열린 그리퍼로 시작한 일. v3.1 (11-05): 그리퍼도 시작 값으로 (다음 판 시작 조건을 같게). 팔 도착 뒤에만, 천천히
                rec["gripper"] = gripper_return(bus, init, sd)
            if R.get("final"):  # 다음 복귀 점검 (H6 끝 자세 일치) 의 기준 = 도착 자세
                E["holds"].append({"perf": time.perf_counter(), "why": "homed_" + where, "hold": dict(R["final"])})
            if why == "fault_latch" and events is not None:
                events["stop_recording"] = True  # 프로세스 안에서 fault 는 풀리지 않음 → 세션 종료, run_series 가 새로 띄움
                print("[end_hold] 추론 오류 뒤라 이 세션은 여기서 끝냅니다 (P/F 고른 뒤 →).", flush=True)
            return True
        except Exception as e:
            rec["result"] = f"error {type(e).__name__}: {e}"[:300]
            E["log"].row("home_error", rec["result"])
            log.error("END_HOLD 복귀 오류: %s", e)
            if events is not None:
                events["stop_recording"] = True
            return False

    def gripper_return(bus, init, sd):
        """그리퍼 Goal 을 지금 값 → 시작 값으로 GRIP_SPEED 로 보간 (팔 관절은 쓰지 않음). Ctrl+C 면 그 자리."""
        try:
            g0 = float(bus.sync_read("Present_Position")["gripper"])
            gt = float(init.get("gripper.pos", g0))
            if gt > GRIP_OPEN_MAX:  # v3.2 (11-13): 세션이 열린 그리퍼로 시작했어도 복귀 목표는 닫힌 값
                gt = GRIP_REST
            if abs(gt - g0) <= 2.0:
                return {"moved": False, "from": g0, "to": gt}
            n = max(1, int(abs(gt - g0) / (GRIP_SPEED / 30.0)))
            for k in range(1, n + 1):
                if sd is not None and sd.is_set():
                    p_ = float(bus.sync_read("Present_Position")["gripper"])
                    bus.sync_write("Goal_Position", {"gripper": p_})
                    return {"moved": False, "from": g0, "to": gt, "stopped": "ctrl_c", "at": p_}
                bus.sync_write("Goal_Position", {"gripper": g0 + (gt - g0) * k / n})
                time.sleep(1 / 30.0)
            time.sleep(0.3)
            g1 = float(bus.sync_read("Present_Position")["gripper"])
            E["log"].row("gripper_home", f"{g0:.1f} -> {gt:.1f} (now {g1:.1f})")
            print(f"[end_hold] 그리퍼 {g0:.1f} → {gt:.1f} (지금 {g1:.1f})", flush=True)
            return {"moved": True, "from": g0, "to": gt, "final": g1, "steps": n}
        except Exception as e:
            E["log"].row("gripper_home_error", f"{type(e).__name__}: {e}")
            return {"moved": False, "error": f"{type(e).__name__}: {e}"[:200]}

    # E2 · E3
    orig_loop = EpisodicStrategy._policy_loop
    sig = inspect.signature(orig_loop)

    @functools.wraps(orig_loop)
    def policy_loop(self, *a, **k):
        args = sig.bind(self, *a, **k).arguments
        robot, events, ctx = args.get("robot"), args.get("events"), args.get("ctx")
        E["robot"], E["events"], E["ctx"] = robot, events, ctx
        exc = None
        try:
            return orig_loop(self, *a, **k)
        except BaseException as ex:  # KeyboardInterrupt 포함 — 기록 후 그대로 올림
            exc = ex
            raise
        finally:
            why = ("exception:" + type(exc).__name__) if exc is not None else _why(events, r2_state, fl_state, ctx)
            E["ended_by"] = why
            if exc is not None:
                E["exception"] = f"{type(exc).__name__}: {exc}"[:300]
            hold_here(robot, "policy_loop_end " + why)
            if events is not None and events.get("rerecord_episode") and not E["home_mode"]:
                events["stop_recording"] = True  # E3: 복귀 · 재시작 없이 버리고 끝내기
                E["rerecord_to_stop"] += 1
                E["log"].row("rerecord_to_stop", "← 다시 찍기 → 이 판 버리고 실행 종료 (복귀 없음). 다시: RERUN=… run_trial.sh")
                log.warning("END_HOLD ← 다시 찍기 = 이 판 버리고 종료 (복귀 없음). 다시 하려면 RERUN=\"이유\" run_trial.sh <N>")

    EpisodicStrategy._policy_loop = policy_loop

    # E4
    def teardown_hardware(self, hw, return_to_initial_position=True):
        T = {"lerobot_return_flag": bool(return_to_initial_position), "steps": []}
        E["teardown"] = T
        try:
            if self._engine is not None:
                self._engine.stop()
                T["steps"].append("engine_stopped")
        except Exception as e:
            T["steps"].append(f"engine_stop_error {e}")
        E["initial_position"] = dict(hw.initial_position) if getattr(hw, "initial_position", None) else None
        robot_w = hw.robot_wrapper
        inner = getattr(robot_w, "inner", robot_w)
        present, bus_ok = None, False
        try:
            if inner.bus.is_connected:
                h = hold_here(robot_w, "teardown")
                present = h
                bus_ok = h is not None
        except Exception as e:
            T["steps"].append(f"bus_check_error {e}")
        if E["home_mode"] and bus_ok and E["ended_by"] in HOMEABLE:
            if safe_return(hw, "teardown"):
                try:
                    p_ = inner.bus.sync_read("Present_Position")
                    present = {j: float(p_[j]) for j in ARM}
                    T["steps"].append("homed_at_teardown")
                except Exception as e:
                    T["steps"].append(f"read_after_home_error {e}")
        end_grip = None
        try:
            if inner.bus.is_connected:
                end_grip = float(inner.bus.sync_read("Present_Position")["gripper"])  # v3.2: 끝 그리퍼 값 (다음 세션 게이트용, 읽기만)
        except Exception as e:
            T["steps"].append(f"gripper_read_error {e}")
        kept = False
        try:
            inner.config.disable_torque_on_disconnect = False
            if inner.bus.is_connected:
                inner.bus.disconnect(disable_torque=False)  # 토크 유지
                kept = True
                T["steps"].append("bus_disconnected_torque_kept")
        except Exception as e:
            T["steps"].append(f"bus_disconnect_error {type(e).__name__}: {e}")
        for name, cam in getattr(inner, "cameras", {}).items():
            try:
                cam.disconnect()
            except Exception as e:
                T["steps"].append(f"cam_{name}_disconnect_error {e}")
        tel = getattr(hw, "teleop", None)
        if tel is not None and getattr(tel, "is_connected", False):
            try:
                tel.bus.disconnect(disable_torque=False)
            except Exception as e:
                T["steps"].append(f"teleop_disconnect_error {e}")
        init = E["initial_position"] or {}
        diff = {j: round(present[j] - init[f"{j}.pos"], 2) for j in ARM if present and f"{j}.pos" in init and j in present}
        st = {"run": os.path.basename(os.path.normpath(run_dir)), "ended_by": E["ended_by"] or "no_policy_loop", "exception": E["exception"],
              "initial_position": init, "end_present_arm": present, "end_gripper": end_grip, "diff_from_initial_deg": diff,
              "max_abs_diff_deg": max((abs(v) for v in diff.values()), default=None), "bus_ok_at_teardown": bus_ok,
              "torque_left_on": True if (kept and bus_ok) else "unknown", "auto_return_blocked_calls": len(E["blocked_returns"]),
              "rerecord_to_stop": E["rerecord_to_stop"], "holds": len(E["holds"]),
              "home_mode": E["home_mode"], "homes": E["homes"], "teardown_steps": T["steps"],
              "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        try:
            p = os.path.join(run_dir, "end_state.json")
            with open(p, "w") as fh:
                json.dump(st, fh, indent=1, ensure_ascii=False, default=float)
        except Exception as e:
            log.error("END_HOLD end_state.json 쓰기 실패: %s", e)
        E["end_state"] = st
        E["log"].row("teardown", json.dumps({k: st[k] for k in ("ended_by", "max_abs_diff_deg", "bus_ok_at_teardown", "torque_left_on",
                                                                  "auto_return_blocked_calls")}, ensure_ascii=False, default=float))
        if E["home_mode"]:
            msg = (f"END_HOLD 종료 (E5): 복귀 {sum(1 for h in E['homes'] if h.get('ok'))}/{len(E['homes'])} 회 성공 · "
                   f"시작 자세와 최대 {st['max_abs_diff_deg']}° · 토크 유지")
        else:
            msg = (f"END_HOLD 종료: 자동 복귀 없음 · 팔은 지금 자리에서 토크 유지 (시작 자세와 최대 {st['max_abs_diff_deg']}°). "
                   f"복귀 · 토크 끄기는 사용자가: python3 ~/so101_runs/main_k8/sgp01_real_eval/scripts/safe_home.py --run {run_dir}")
        log.warning(msg)
        print("[end_hold] " + msg, flush=True)
        if not bus_ok:
            log.error("END_HOLD 팔 통신 상태 불명 — 토크 · 자세를 알 수 없음. 팔을 받치고 전원으로 정지하세요")

    EpisodicStrategy._teardown_hardware = teardown_hardware
    return E


GRIP_REST, GRIP_OPEN_MAX = 3.0, 10.0  # v3.2 (11-13): 쉬는 자세의 그리퍼 값 · 이보다 크면 "열림"
GRIP_SPEED = 30.0  # 그리퍼 복귀 속도 (단위/s, 0–100 범위)
HOMEABLE = {"episode_end_or_user_next", "r2_safety_stop", "fault_latch", "engine_failed_shutdown", "user_rerecord"}


class _LockedBus:
    """safe_home.move() 용: bus 호출마다 ThreadSafeRobot 의 lock 을 잡는다."""

    def __init__(self, bus, lock):
        self.bus, self.lock = bus, lock if lock is not None else _Null()

    def sync_read(self, *a, **k):
        with self.lock:
            return self.bus.sync_read(*a, **k)

    def sync_write(self, *a, **k):
        with self.lock:
            return self.bus.sync_write(*a, **k)


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _why(events, r2, fl, ctx=None):
    """끝난 이유. lerobot 은 첫 Ctrl+C (SIGINT) 를 ProcessSignalHandler 로 받아 shutdown_event 만 세운다 (예외 없음, 두 번째는 sys.exit(1))."""
    if fl and fl.get("fault"):
        return "fault_latch"
    if r2 and r2.get("stopped"):
        return "r2_safety_stop"
    eng = getattr(getattr(ctx, "policy", None), "inference", None)
    if eng is not None and getattr(eng, "failed", False):
        return "engine_failed_shutdown"
    sd = getattr(getattr(ctx, "runtime", None), "shutdown_event", None)
    if sd is not None and sd.is_set():
        return "shutdown_signal"  # Ctrl+C (eval_ui → pty \x03 → SIGINT) · SIGTERM · SIGHUP
    if events is not None:
        if events.get("rerecord_episode"):
            return "user_rerecord"
        if events.get("stop_recording"):
            return "user_quit"
    return "episode_end_or_user_next"
