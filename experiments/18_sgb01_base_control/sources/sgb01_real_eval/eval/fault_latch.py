"""정책 추론 오류 래치 — rft01 실물 파일럿 평가 경로 (eval_ui + episodic + RTC) 용 (2026-11-05).

왜: lerobot 0.6.2 RTC 엔진 (rollout/inference/rtc.py) 은 추론 예외가 나면 "RTC inference error (k/10)" 를 로그하고
    0.5 s 쉬고 최대 10 번 다시 시도한다. 그동안 주 루프는 queue 에 남은 action (최대 chunk 50 step ≈ 1.7 s) 을 계속 로봇에 보낸다.
    10 번 실패하면 "Fatal error in RTC thread" → shutdown. r2_safety 는 pan · 지나침 · 추종 정지 규칙만 보고 추론 오류는 보지 않는다.
    HIL adapter 의 A10 래치 (main_k8/hil_dagger) 는 dagger 전략 전용이라 이 평가 경로에는 걸려 있지 않다.

동작 (HIL A10 과 같은 원칙, episodic 평가용으로 다시 씀 — hil_dagger 코드는 import 하지 않음):
  1. RTC 로거 ERROR 줄 "RTC inference error" 또는 "Fatal error in RTC thread" 가 처음 나오는 순간 (RTC 스레드 안)
     → 래치 설정 + engine.pause() (RTC 스레드 재시도 멈춤, Event 라 락 없음).
     주 루프 틱마다 engine.failed 도 본다.
  2. 래치 뒤 정책 루프의 send_action 은 모두 차단한다 (로봇에 보내지 않고 현재 위치를 돌려줌).
  3. 래치 뒤 첫 get_observation (주 루프, 매 틱 부름 — queue 가 비어 send_action 이 안 불려도 처리됨) 에서 한 번:
     engine.reset() (queue 비움 + epoch 증가 → 진행 중 chunk 버림), 팔 5 관절 Goal := 현재 위치, 그리퍼 := 마지막 정책 명령
     (쥔 큐브를 놓지 않게; 없으면 현재 위치) 를 한 번 보낸다 (max_relative_target 8° clamp 거침),
     r2_safety 상태 stopped=True (그 판 남은 정책 명령 차단), events['exit_early']=True (판 종료).
  4. 기록: <실행 폴더>/fault_latch.csv + r2_safety.csv 에 event=FAULT 행, 콘솔 WARNING "FAULT_LATCH ...".

정책 루프 밖 (eval_ui 처음 자세 복귀 · lerobot 종료 처리) 의 명령은 건드리지 않는다.
통신 (서보 bus · 카메라) 오류는 lerobot 에서 예외로 정책 루프가 끝나므로 이후 정책 명령이 나가지 않는다 — 이 모듈 대상 아님.

옵션: --fault_latch=stop|warn|off (기본 stop; warn = 기록만). rollout_logged.py (이 폴더 shim) 가 sys.argv 에서 뺀다.
"""

import csv
import logging
import os
import threading
import time

log = logging.getLogger("lerobot.fault_latch")
LAST_STATE = None
FIELDS = ["wall", "perf", "event", "kind", "thread", "episode", "tick", "msg", "qsize_before", "qsize_after", "hold", "since_fault_s"]


def pop_options(argv):
    mode, rest = "stop", [argv[0]] if argv else []
    for a in argv[1:]:
        if a.startswith("--fault_latch"):
            k, _, v = a[2:].partition("=")
            if k != "fault_latch" or v not in ("stop", "warn", "off"):
                raise SystemExit(f"--fault_latch=stop|warn|off (받은 값 {a})")
            mode = v
        else:
            rest.append(a)
    return {"mode": mode}, rest


class _Log:
    def __init__(self, path):
        self.lock = threading.Lock()
        new = not os.path.exists(path)
        self.fh = open(path, "a", newline="")
        self.w = csv.DictWriter(self.fh, fieldnames=FIELDS)
        if new:
            self.w.writeheader()
        self.fh.flush()

    def row(self, **kw):
        with self.lock:
            self.w.writerow({"wall": f"{time.time():.4f}", "perf": f"{time.perf_counter():.5f}", **kw})
            self.fh.flush()


def install(opts, r2_state):
    """r2_safety.install 뒤에 부른다 (r2_safety 의 send_action · get_observation 을 한 겹 더 감싼다)."""
    global LAST_STATE
    from lerobot.rollout.robot_wrapper import ThreadSafeRobot
    import lerobot.rollout.inference.rtc as rtc_mod

    run_dir = os.environ.get("EVAL_UI_RUN_DIR") or os.path.dirname(os.environ.get("ROLLOUT_FILTER_LOG", "./x"))
    F = {"opts": opts, "fault": None, "handled": False, "n_blocked": 0, "last_cmd": None, "n_rtc_errors": 0,
         "log": _Log(os.path.join(run_dir, "fault_latch.csv")), "r2": r2_state, "records": []}
    LAST_STATE = F
    F["log"].row(event="install", kind=opts["mode"], thread=threading.current_thread().name, episode="", tick="", msg="", qsize_before="",
                 qsize_after="", hold="", since_fault_s="")
    print(f"[fault_latch] installed {opts}", flush=True)
    log.info("fault_latch installed: %s", opts)
    if opts["mode"] == "off":
        return F
    S = r2_state  # in_policy · stopped · ctx · events · episode · tick · log (r2_safety install 이 채움)

    def engine():
        ctx = S.get("ctx")
        return getattr(getattr(ctx, "policy", None), "inference", None)

    def latch(kind, msg):
        if F["fault"] is not None:
            return
        F["fault"] = {"kind": kind, "t": time.perf_counter(), "msg": str(msg)[:300], "episode": S.get("episode"), "tick": S.get("tick")}
        eng = engine()
        if opts["mode"] == "stop" and eng is not None:
            try:
                eng.pause()  # _policy_active.clear() — 재시도 멈춤
            except Exception:
                pass
        F["log"].row(event="FAULT", kind=kind, thread=threading.current_thread().name, episode=S.get("episode"), tick=S.get("tick"),
                     msg=str(msg)[:300], qsize_before="", qsize_after="", hold="", since_fault_s=0)
        F["records"].append(dict(F["fault"]))

    class _H(logging.Handler):
        def emit(self, rec):
            if rec.levelno >= logging.ERROR:
                m = rec.getMessage()
                if m.startswith("RTC inference error") or m.startswith("Fatal error in RTC thread"):
                    F["n_rtc_errors"] += 1
                    latch("inference_error", m)

    F["handler"] = _H(level=logging.ERROR)
    rtc_mod.logger.addHandler(F["handler"])

    inner_obs = ThreadSafeRobot.get_observation
    inner_send = ThreadSafeRobot.send_action

    def handle(robot, obs):
        """주 루프에서 한 번: queue 무효화 · 유지 명령 · 판 종료."""
        F["handled"] = True
        eng = engine()
        q = getattr(eng, "action_queue", None)
        qb = q.qsize() if q is not None else ""
        if eng is not None:
            eng.pause()
            eng.reset()
        qa = q.qsize() if q is not None else ""
        hold = {}
        for k, v in obs.items():
            if k.endswith(".pos"):
                hold[k] = float(v)
        last = F["last_cmd"] or {}
        if "gripper.pos" in last:
            hold["gripper.pos"] = float(last["gripper.pos"])
        if S.get("stopped"):  # r2_safety 가 이미 정지 (유지 명령 보냄) → 다시 보내지 않음
            held = None
        else:  # 유지 명령은 r2_safety 를 거쳐 보낸다 (규칙 검사 · 기록 동일). 보낸 뒤 바로 차단 상태로
            held = inner_send(robot, hold)
            S["stopped"] = True
        if S.get("events") is not None:
            S["events"]["exit_early"] = True
        dt = time.perf_counter() - F["fault"]["t"]
        F["fault"].update(handled=True, qsize_before=qb, qsize_after=qa, hold=hold, held=held, since_fault_s=dt, perf_handled=time.perf_counter())
        F["records"][-1] = dict(F["fault"])
        F["log"].row(event="FAULT_HANDLED", kind=F["fault"]["kind"], thread=threading.current_thread().name, episode=S.get("episode"),
                     tick=S.get("tick"), msg="hold+pause+reset_queue+exit_early", qsize_before=qb, qsize_after=qa,
                     hold=" ".join(f"{k.removesuffix('.pos')}={v:.2f}" for k, v in hold.items()), since_fault_s=f"{dt:.4f}")
        try:
            S["log"].row(episode=S.get("episode"), tick=S.get("tick"), event="FAULT", rule=F["fault"]["kind"], detail=F["fault"]["msg"][:200],
                         cmd_pan="", present_pan=hold.get("shoulder_pan.pos"), qsize_before=qb, qsize_after=qa,
                         action="hold+pause+reset_queue+exit_early")
        except Exception:
            pass
        log.warning("FAULT_LATCH %s ep=%s tick=%s queue %s→%s — 정책 명령 차단, 판 종료 (%s)", F["fault"]["kind"], S.get("episode"), S.get("tick"),
                    qb, qa, F["fault"]["msg"][:160])

    def get_observation(self, *a, **k):
        obs = inner_obs(self, *a, **k)
        if S.get("in_policy"):
            eng = engine()
            if F["fault"] is None and eng is not None and getattr(eng, "failed", False):
                latch("engine_failed", getattr(eng, "failure_traceback", "") or "engine.failed")
            if F["fault"] is not None and not F["handled"] and opts["mode"] == "stop":
                handle(self, obs)
        return obs

    def send_action(self, action, *a, **k):
        if S.get("in_policy") and F["fault"] is not None and opts["mode"] == "stop":
            F["n_blocked"] += 1
            obs = S.get("last_obs") or {}
            return {key: float(v) for key, v in obs.items() if key.endswith(".pos")}
        out = inner_send(self, action, *a, **k)
        if S.get("in_policy") and not S.get("stopped"):
            F["last_cmd"] = dict(action)
        return out

    ThreadSafeRobot.get_observation = get_observation
    ThreadSafeRobot.send_action = send_action
    return F
