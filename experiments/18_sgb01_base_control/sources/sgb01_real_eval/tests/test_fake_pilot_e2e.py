"""rft01 실물 파일럿 가짜 장치 시험 — eval_ui 자식 경로 (scripts/eval_ui.py child_main) 그대로, 이 세션 shim (R2 shim + fault_latch) 으로
lerobot-rollout (episodic, RTC, rft01 001000) 전체 루프를 돌린다 (GPU, 시나리오당 약 3–5 분).

실제 SO-101 · 카메라에 연결하지 않는다: R2 세션 tests/fake_robot.py 를 그대로 import (3 중 차단 — connect 함수 차단 · SOFollower.__new__ 가짜 bus/cam ·
/nonexistent 경로가 아니면 거부, connect 직전 MOCK_OK assert). memory: mock-hardware-isolation.
가짜 카메라 영상 = 기록 B1 판 (d2/eval/rollouts/20261029_170818 filt_off ds_ep 1, K1 큐브).

시나리오 (--scenario):
  fault      추론 오류 주입: PI05Policy.predict_action_chunk 가 --fail_after 번째 호출 뒤 계속 RuntimeError → fault_latch=stop
             F1 래치 (inference_error) · FAULT_HANDLED 기록, 처리까지 ≤ 0.2 s
             F2 오류 순간 이후 정책 루프에서 FakeBus 에 쓰인 Goal 이 모두 유지 명령 (오류 처리 순간 Present ± 0.5°, 그리퍼 제외) — 정책 명령 0 개
             F3 처리 순간 queue 비움 (qsize_after == 0)
             F4 판이 오류 처리 뒤 1 s 안에 끝남 (정책 루프 마지막 쓰기 시각)
             F5 RTC 재시도 멈춤: 'RTC inference error' 로그 ≤ 2 번 (공식 동작은 10 번 뒤 Fatal)
             F6 eval_ui 경로 예외 없음 · READY · START · SAVED 1 · r2_safety.csv · fault_latch.csv 에 FAULT 행
  fault_off  같은 주입, --fault_latch=off (대조: 공식 동작에서 첫 오류 뒤 정책 명령 수 · 시간을 잰다 — INFO. v2 공통 R 검사는 PASS/FAIL)
  normal_timeout  판 시간 (6 s) 으로 정상 종료      user_next  → 키 (exit_early) 로 종료
  ctrl_c     판 중 SIGINT (eval_ui 의 Ctrl+C 와 같음)      rerecord  ← 키 (rerecord) → v2: 버리고 종료
v2 공통 (모든 시나리오, 2026-11-05):
  R1 자동 원위치 복귀 명령 0: 정책 루프 마지막 쓰기 뒤 FakeBus 에 쓰인 Goal 이 모두 '제자리 유지' (Present ± 0.5°) 이고 시작 자세 쪽 이동 0, eval_ui HOMING 표시 0
  R2 end_state.json: 토크 유지 · bus 정상 · lerobot return flag False      R3 disconnect(disable_torque=False) 만      R4 정책 루프 끝 제자리 유지 명령 기록
v3 (11-05) 연속 세션 E5 (END_HOLD_HOME=1, 판 2 개, reset_to_initial_position=true — run_trial.sh SERIES 와 같음):
  series_home    판 2 개 정상 → H1 판 사이 · 종료 때 safe_home 점검 통과 후 복귀 (homes ok ≥ 2) · H2 복귀 쓰기 틱당 ≤ 0.5°+ε (15°/s)
                 H3 끝 자세가 시작 자세 3° 안 · H4 저장 2 판 · H5 토크 유지 (disconnect disable_torque=False)
  series_ctrl_c  첫 판 중 SIGINT → H6 복귀 이동 0 (정책 뒤 쓰기 모두 제자리 유지) · 저장 1 판 이하 · 토크 유지
  r2stop     오류 주입 없음, --r2_safety.pan_present_abs_max 낮춤 (기본 15) → r2_safety 정지가 이 shim 아래에서도 그대로 동작
             S1 STOP 기록 (pan_present_limit) · S2 queue 비움 · S3 STOP 뒤 정책 명령 0 · S4 fault_latch 오경보 0 · S5 eval_ui 경로 예외 없음
공통: T10a 진짜 FeetechMotorsBus/OpenCVCamera connect 차단 · T10b robot 이 FakeBus/FakeCam
출력: tests/_out/<scenario>_<시각>/ (가짜 run 폴더 + result.json), 마지막 줄 ALL_PASS / SOME_FAIL / INFO_DONE
사용: cd tests && PYTHONDONTWRITEBYTECODE=1 nice -n 19 ~/so101-env/bin/python test_fake_pilot_e2e.py --scenario fault
"""
import argparse
import contextlib
import datetime
import functools
import inspect
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np

S_DIR = Path(__file__).resolve().parents[1]
K8 = Path.home() / "so101_runs/main_k8"
R2 = K8 / "r2_grasp_diagnostic"
D2 = K8 / "d2"
CKPT = D2 / "recovery_ft/runs/rft01_d2rc16_W5_1k_s2001/checkpoints/001000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"
SRC_RUN = D2 / "eval/rollouts/20261029_170818_32_20000_20k_filt_off/dataset"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["fault", "fault_off", "r2stop", "normal_timeout", "user_next", "ctrl_c", "ctrl_c2", "rerecord", "series_home", "series_ctrl_c"], required=True)
    ap.add_argument("--fail_after", type=int, default=6, help="몇 번째 predict_action_chunk 호출 뒤부터 오류")
    ap.add_argument("--pan_thr", type=float, default=15.0)
    ap.add_argument("--episode_time", type=float, default=None, help="기본 20 s (normal_timeout 은 6 s)")
    ap.add_argument("--trigger_s", type=float, default=5.0, help="user_next · ctrl_c · rerecord 를 판 시작 몇 초 뒤에")
    ap.add_argument("--ckpt", default=str(CKPT))
    a = ap.parse_args()
    if a.episode_time is None:
        a.episode_time = 6.0 if a.scenario in ("normal_timeout", "series_home") else 20.0
    SERIES = a.scenario.startswith("series")
    if SERIES:
        os.environ["END_HOLD_HOME"] = "1"
    out = S_DIR / "tests/_out" / f"{a.scenario}_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    out.mkdir(parents=True)
    os.environ.update(ROLLOUT_DIAG="1", EVAL_UI_RUN_DIR=str(out), EVAL_UI_FILTER_DIR=str(S_DIR / "eval"), ROLLOUT_FILTER_LOG=str(out / "filter_log.csv"),
                      ROLLOUT_DEBUG_LOG=str(out / "debug.log"), HF_HUB_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
    sys.path.insert(0, str(R2 / "tests"))
    sys.path.insert(0, str(D2 / "diag_grasp_bias"))
    import common as C
    import fake_robot as FR

    cache = {}
    front = [np.ascontiguousarray(f) for f in C.frames(SRC_RUN, 1, "front", 0, 900, cache)]
    wrist = [np.ascontiguousarray(f) for f in C.frames(SRC_RUN, 1, "wrist", 0, 900, cache)]
    snapshot = {}
    holder = FR.install(front, wrist, snap=lambda: dict(snapshot))

    lerobot_args = ["--strategy.type=episodic", f"--policy.path={a.ckpt}", "--policy.num_inference_steps=5",
                    "--inference.type=rtc", "--inference.rtc.execution_horizon=20", "--inference.queue_threshold=30",
                    "--inference.rtc.prefix_attention_schedule=EXP",
                    "--robot.type=so101_follower", f"--robot.port={FR.FAKE_PORT}", "--robot.id=pilot_fake", "--robot.max_relative_target=8",
                    "--robot.cameras={ front: {type: opencv, index_or_path: %s, width: 640, height: 480, fps: 30}, "
                    "wrist: {type: opencv, index_or_path: %s, width: 640, height: 480, fps: 30} }" % FR.FAKE_CAMS,
                    "--dataset.repo_id=oxr/rollout_pilot_fake", f"--dataset.root={out / 'dataset'}", "--dataset.no_stamp=true",
                    f"--dataset.single_task={TASK}", f"--dataset.num_episodes={2 if SERIES else 1}", f"--dataset.episode_time_s={a.episode_time}",
                    "--dataset.reset_time_s=2", "--dataset.push_to_hub=false", "--fps=30", "--play_sounds=false", "--display_data=false",
                    "--arm_filter=false", "--rollout_guard=warn", "--r2_safety=stop", f"--r2_safety.plan={S_DIR / 'config/pilot_plan.csv'}",
                    "--r2_safety.plan_start=1", "--r2_safety.viewer=off", "--r2_safety.live=off",
                    "--fault_latch=" + ("off" if a.scenario == "fault_off" else "stop"),
                    "--return_to_initial_position=false", f"--strategy.reset_to_initial_position={'true' if SERIES else 'false'}"]  # run_trial.sh 와 같음
    if a.scenario == "r2stop":
        lerobot_args.append(f"--r2_safety.pan_present_abs_max={a.pan_thr}")

    sys.path.insert(0, str(Path.home() / "so101_boxpick/scripts"))
    import eval_ui
    sys.path.insert(0, str(R2 / "eval"))
    import r2_safety as RS0
    sys.path.insert(0, str(S_DIR / "eval"))
    import fault_latch as FL0
    import end_hold as EH0
    import lerobot.rollout.strategies.episodic as epi

    events = {"exit_early": True, "rerecord_episode": False, "stop_recording": False}  # READY 바로 통과
    epi.init_keyboard_listener = lambda: (None, events)
    orig_loop = epi.EpisodicStrategy._policy_loop

    trig = {"t": None, "kind": None}

    def fire():
        trig["t"] = time.perf_counter()
        if a.scenario == "user_next":  # → 키 = exit_early
            trig["kind"] = "exit_early"
            events["exit_early"] = True
        elif a.scenario == "rerecord":  # ← 키 = rerecord + exit_early
            trig["kind"] = "rerecord"
            events["rerecord_episode"] = True
            events["exit_early"] = True
        elif a.scenario in ("ctrl_c", "ctrl_c2", "series_ctrl_c"):  # eval_ui 가 pty 로 \x03 → 자식 SIGINT 와 같은 결과
            import signal
            trig["kind"] = "SIGINT×2 (0.05 s)" if a.scenario == "ctrl_c2" else "SIGINT"
            os.kill(os.getpid(), signal.SIGINT)
            if a.scenario == "ctrl_c2":  # 두 번째 Ctrl+C = lerobot sys.exit(1)
                time.sleep(0.05)
                os.kill(os.getpid(), signal.SIGINT)

    @functools.wraps(orig_loop)
    def loop(self, *aa, **kk):
        for c in holder["robot"].cameras.values():
            c.restart()
        trig.setdefault("loop_start", time.perf_counter())
        if a.scenario in ("user_next", "rerecord", "ctrl_c", "ctrl_c2", "series_ctrl_c") and trig["t"] is None:
            import threading as _th
            _th.Timer(a.trigger_s, fire).start()
        r_ = orig_loop(self, *aa, **kk)
        if a.scenario == "series_home" and not trig.get("grip_opened"):  # 첫 판 끝: 그리퍼를 연 채로 끝난 것처럼 (시행 6→7 상황)
            b_ = holder["robot"].bus
            b_.present["gripper"] = b_.goal["gripper"] = 30.0
            trig["grip_opened"] = True
        return r_

    epi.EpisodicStrategy._policy_loop = loop
    assert str(inspect.signature(epi.EpisodicStrategy._policy_loop)) == str(inspect.signature(orig_loop))

    # 오류 주입
    inj = {"calls": 0, "t_first_fail": None, "n_fail": 0}
    if a.scenario in ("fault", "fault_off"):
        from lerobot.policies.pi05.modeling_pi05 import PI05Policy
        orig_pac = PI05Policy.predict_action_chunk

        @functools.wraps(orig_pac)
        def pac(self, *aa, **kk):
            inj["calls"] += 1
            if inj["calls"] > a.fail_after:
                inj["n_fail"] += 1
                if inj["t_first_fail"] is None:
                    inj["t_first_fail"] = time.perf_counter()
                raise RuntimeError("injected test fault (test_fake_pilot_e2e)")
            return orig_pac(self, *aa, **kk)

        PI05Policy.predict_action_chunk = pac

    def snap_live():
        S = RS0.LAST_STATE or {}
        F = FL0.LAST_STATE or {}
        return {"in_policy": S.get("in_policy"), "stopped": S.get("stopped"), "episode": S.get("episode"),
                "fault": (F.get("fault") or {}).get("kind")}

    orig_read = FR.FakeBus.sync_read

    def sync_read(self, what, *aa, **kk):  # E5 점검이 Goal · Torque 도 읽는다
        if what == "Goal_Position":
            return dict(getattr(self, "goal", None) or self.present)
        if what == "Torque_Enable":
            return {j: 1 for j in FR.J}
        return orig_read(self, what)

    FR.FakeBus.sync_read = sync_read
    orig_write = FR.FakeBus.sync_write

    def sync_write(self, what, vals):
        snapshot.clear()
        snapshot.update(snap_live())
        return orig_write(self, what, vals)

    FR.FakeBus.sync_write = sync_write
    disc = []
    orig_disc = FR.FakeBus.disconnect

    def disconnect(self, *aa, **kk):  # 토크 끄기 여부 기록 (진짜 FeetechMotorsBus.disconnect(disable_torque=…) 와 같은 인자)
        disc.append({"args": aa, "kwargs": kk, "perf": time.perf_counter()})
        return orig_disc(self, *aa, **kk)

    FR.FakeBus.disconnect = disconnect

    from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
    from lerobot.motors.feetech import FeetechMotorsBus
    t10a = True
    for cls in (FeetechMotorsBus, OpenCVCamera):
        try:
            cls.connect(None)
            t10a = False
        except RuntimeError:
            pass
        except Exception:
            t10a = False

    rtc_logs = []

    class H(logging.Handler):
        def emit(self, r):
            m = r.getMessage()
            if m.startswith(("RTC inference error", "Fatal error in RTC thread", "FAULT_LATCH", "R2_SAFETY")):
                rtc_logs.append((time.perf_counter(), m[:160]))

    logging.getLogger().addHandler(H(level=logging.WARNING))
    buf, exc = io.StringIO(), None

    class Tee(io.TextIOBase):
        def write(self, x):
            buf.write(x)
            return sys.__stdout__.write(x)

    t0 = time.time()
    try:
        with contextlib.redirect_stdout(Tee()):
            eval_ui.child_main(lerobot_args)
    except BaseException as ex:  # noqa: BLE001 — SystemExit 포함 (fault_off 는 lerobot 이 오류로 끝날 수 있음)
        import traceback
        traceback.print_exc()
        exc = f"{type(ex).__name__}: {ex}"
    sys.stdout = sys.__stdout__
    dur = time.time() - t0
    S, F = RS0.LAST_STATE, FL0.LAST_STATE
    marks = [ln for ln in buf.getvalue().splitlines() if ln.startswith("[eval_ui]")]
    W = holder["robot"].bus.writes if holder["robot"] else []
    res, ok = {}, True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        res[name] = {"pass": bool(cond), "detail": detail}
        print(f"{'PASS' if cond else 'FAIL'} {name} {detail}", flush=True)

    def info(name, detail):
        res[name] = {"info": detail}
        print(f"INFO {name} {detail}", flush=True)

    J5 = FR.J[:5]
    _pol_t = [w[0] for w in W if w[3].get("in_policy")]
    t_pol1 = max(_pol_t, default=None)
    pol = [w for w in W if w[3].get("in_policy")]
    n_saved = sum(1 for m in marks if m.startswith("[eval_ui] SAVED"))
    chk("T10a_real_connect_blocked", t10a)
    chk("T10b_mock_ok", holder["robot"] is not None and isinstance(holder["robot"].bus, FR.FakeBus) and holder["connect_calls"] >= 1,
        f"connect_calls={holder['connect_calls']}")
    n_err = sum(1 for _, m in rtc_logs if m.startswith("RTC inference error"))
    n_fatal = sum(1 for _, m in rtc_logs if m.startswith("Fatal error in RTC thread"))

    if a.scenario == "fault":
        f = (F or {}).get("fault") or {}
        chk("F1_latched_and_handled", f.get("kind") == "inference_error" and f.get("handled") and f.get("since_fault_s", 9) <= 0.2,
            f"fault={ {k: f.get(k) for k in ('kind', 'episode', 'tick', 'since_fault_s', 'qsize_before', 'qsize_after')} } calls={inj['calls']} fail_after={a.fail_after}")
        tf = f.get("t", float("inf"))
        hold = f.get("hold") or {}
        after = [w for w in pol if w[0] >= tf]
        bad = [(round(w[0] - tf, 3), round(max(abs(w[1][j] - hold.get(f"{j}.pos", w[1][j])) for j in J5), 2)) for w in after
               if max(abs(w[1][j] - hold.get(f"{j}.pos", w[1][j])) for j in J5) > 0.5]
        chk("F2_no_policy_cmd_after_fault", hold and len(after) >= 1 and not bad,
            f"policy-loop writes after fault={len(after)} non_hold={bad[:5]} policy writes before fault={sum(1 for w in pol if w[0] < tf)}")
        chk("F3_queue_cleared", f.get("qsize_after") == 0, f"qsize {f.get('qsize_before')}→{f.get('qsize_after')}")
        last_pol = max((w[0] for w in pol), default=None)
        end_after = None if last_pol is None or "perf_handled" not in f else last_pol - f["perf_handled"]
        frames = None
        try:
            import pandas as pd
            pq = sorted((out / "dataset/data").rglob("*.parquet"))
            frames = int(sum(len(pd.read_parquet(p)) for p in pq))
        except Exception:
            pass
        chk("F4_episode_ends_quickly", end_after is not None and end_after <= 1.0,
            f"last policy-loop write − handled = {None if end_after is None else round(end_after, 3)} s · dataset frames={frames} (episode_time {a.episode_time} s = {int(a.episode_time * 30)})")
        # 로그 수집기는 lerobot init_logging 이 root handler 를 다시 만들어 놓칠 수 있다 → 주입 호출 수 (실제 재시도 횟수) 와 fault_latch 카운터로 본다
        chk("F5_retries_stopped", 1 <= inj["n_fail"] <= 2 and (F or {}).get("n_rtc_errors", 0) >= 1 and n_fatal == 0,
            f"injected failing calls={inj['n_fail']} (공식: 10 번 뒤 Fatal) fault_latch rtc_error lines={(F or {}).get('n_rtc_errors')} captured logs={n_err} fatal={n_fatal}")
        fl_rows = (out / "fault_latch.csv").read_text().splitlines() if (out / "fault_latch.csv").exists() else []
        r2_rows = (out / "r2_safety.csv").read_text().splitlines() if (out / "r2_safety.csv").exists() else []
        chk("F6_eval_ui_path_and_logs", exc is None and any(m.startswith("[eval_ui] READY") for m in marks) and n_saved == 1
            and any(",FAULT_HANDLED," in r for r in fl_rows) and any(",FAULT," in r for r in r2_rows),
            f"exception={exc} SAVED={n_saved} fault_latch.csv rows={len(fl_rows)} r2 FAULT rows={sum(1 for r in r2_rows if ',FAULT,' in r)} marks={marks[:8]}")
    elif a.scenario == "fault_off":
        tf = inj["t_first_fail"] or float("inf")
        after = [w for w in pol if w[0] >= tf]
        moving = [w for w in after if max(abs(w[1][j] - after[0][1][j]) for j in J5) > 0.5] if after else []
        info("O1_official_after_first_error", {"policy_cmds_after_first_error": len(after),
                                               "span_s": round(after[-1][0] - tf, 3) if after else 0.0,
                                               "cmds_differing_from_first_post_error_cmd": len(moving),
                                               "rtc_error_logs_captured": n_err, "fatal_captured": n_fatal, "injected_failing_calls": inj["n_fail"],
                                               "fault_latch_rtc_error_lines": (F or {}).get("n_rtc_errors"),
                                               "exception": exc, "saved": n_saved, "duration_s": round(dur, 1)})
    elif a.scenario == "r2stop":
        stops = S["stop_records"] if S else []
        chk("S1_r2_stop", len(stops) == 1 and "pan_present_limit" in stops[0]["rules"], f"stops={[(s['episode'], s['tick'], s['rules']) for s in stops]}")
        chk("S2_queue_cleared", stops and stops[0]["qsize_after"] == 0, f"{[(s['qsize_before'], s['qsize_after']) for s in stops]}")
        bad = []
        for s in stops:
            for w in pol:
                if w[0] >= s["perf_trigger"]:
                    dev = max(abs(w[1][j] - s["hold"][f"{j}.pos"]) for j in J5 if f"{j}.pos" in s["hold"])
                    if dev > 0.5:
                        bad.append(round(dev, 2))
        chk("S3_no_policy_cmd_after_stop", stops and not bad, f"non_hold={bad[:5]}")
        chk("S4_no_false_fault", (F or {}).get("fault") is None and n_err == 0, f"fault={(F or {}).get('fault')} rtc_errors={n_err}")
        chk("S5_eval_ui_path", exc is None and n_saved == 1, f"exception={exc} SAVED={n_saved} marks={marks[:8]}")
    elif a.scenario in ("normal_timeout", "user_next", "ctrl_c", "ctrl_c2", "rerecord"):
        E = EH0.LAST_STATE or {}
        want = {"normal_timeout": ["episode_end_or_user_next"], "user_next": ["episode_end_or_user_next"], "rerecord": ["user_rerecord"],
                "ctrl_c": ["shutdown_signal"], "ctrl_c2": ["shutdown_signal", "exception:SystemExit"]}[a.scenario]
        chk("N1_ended_by", E.get("ended_by") in want and (a.scenario == "normal_timeout" or trig["t"] is not None),
            f"ended_by={E.get('ended_by')} (want {want}) trigger={trig}")
        frames = len(pol)
        if a.scenario == "normal_timeout":
            el = None if t_pol1 is None else t_pol1 - trig["loop_start"]
            chk("N2_ran_full_episode_time", el is not None and el >= a.episode_time - 0.5 and not (S or {}).get("stop_records"),
                f"loop start → last policy write {None if el is None else round(el, 2)} s (episode {a.episode_time} s) policy writes={frames} "
                f"r2 stops={len((S or {}).get('stop_records') or [])}")
        if a.scenario == "rerecord":
            chk("N3_rerecord_discarded_and_stopped", n_saved == 0 and any(m.startswith("[eval_ui] DISCARD") for m in marks) and E.get("rerecord_to_stop") == 1
                and sum(1 for m in marks if m.startswith("[eval_ui] START")) == 1, f"SAVED={n_saved} marks={marks} rerecord_to_stop={E.get('rerecord_to_stop')}")
        elif a.scenario == "ctrl_c2":  # 강제 종료 (sys.exit(1)) — 저장 여부는 기록만
            info("N3_ctrl_c2_save", f"SAVED={n_saved} exception={exc}")
        else:
            chk("N3_data_saved", n_saved == 1 and exc is None, f"SAVED={n_saved} exception={exc}")

    if SERIES:
        E = EH0.LAST_STATE or {}
        homes = E.get("homes") or []
        pol_ts = [w[0] for w in pol]
        es_p = out / "end_state.json"
        es = json.loads(es_p.read_text()) if es_p.exists() else {}
        steps, prev = [], None   # 정책 밖 쓰기의 틱당 변화 (복귀 속도)
        for w in W:
            if w[3].get("in_policy"):
                prev = None
                continue
            if prev is not None:
                steps.append(max(abs(w[1][j] - prev[j]) for j in FR.J[:5]))
            prev = w[1]
        if a.scenario == "series_home":
            chk("H1_homed_between_and_at_end", sum(1 for h in homes if h.get("ok")) >= 2 and {h["where"] for h in homes if h.get("ok")} >= {"between_episodes", "teardown"},
                f"homes={[(h['where'], h.get('ended_by'), h.get('ok'), h.get('result'), (h.get('move') or {}).get('reason')) for h in homes]}")
            chk("H2_home_speed", steps and max(steps) <= 0.5 * 1.1, f"(15°/s ÷ 30 Hz = 0.5°/틱, 유지→첫 보간 이음매 여유 10 %) 정책 밖 쓰기 {len(steps)} · 틱당 최대 {max(steps, default=None)}")
            chk("H3_end_near_start", es.get("max_abs_diff_deg") is not None and es["max_abs_diff_deg"] <= 3.0, f"max_abs_diff={es.get('max_abs_diff_deg')}")
            chk("H4_two_saved", n_saved == 2 and exc is None, f"SAVED={n_saved} exc={exc}")
            import glob as _g
            import pandas as _pd
            _pq = sorted(_g.glob(str(out / "dataset/data/*/*.parquet")))
            _df = _pd.concat([_pd.read_parquet(x) for x in _pq]) if _pq else None
            g_init = float((E.get("initial_position") or {}).get("gripper.pos", float("nan")))
            g_ep1 = float(_df[_df.episode_index == 1]["observation.state"].iloc[0][5]) if _df is not None and (_df.episode_index == 1).any() else None
            g_ep0_end = float(_df[_df.episode_index == 0]["observation.state"].iloc[-1][5]) if _df is not None and (_df.episode_index == 0).any() else None
            gh = [h.get("gripper") for h in homes if h.get("where") == "between_episodes"]
            chk("H7_gripper_reset_between", g_ep1 is not None and abs(g_ep1 - g_init) <= 3.0 and any((h or {}).get("moved") for h in gh),
                f"gripper initial={g_init:.1f} ep0 end={g_ep0_end} ep1 start={g_ep1} home rec={gh}")
            far = [h for h in homes if h.get("where") == "between_episodes"]
            info("home_dist", [(h.get("checks") and [c["name"] for c in h["checks"] if not c["pass"]], (h.get("move") or {}).get("n_steps")) for h in far])
        else:
            post = [w for w in W if pol_ts and w[0] > max(pol_ts) and not w[3].get("in_policy")]
            nonhold = [round(max(abs(w[1][j] - w[2][j]) for j in FR.J[:5]), 2) for w in post if max(abs(w[1][j] - w[2][j]) for j in FR.J[:5]) > 0.5]
            chk("H6_ctrl_c_no_home_move", not nonhold and not any(h.get("ok") for h in homes) and E.get("ended_by") == "shutdown_signal" and n_saved <= 1,
                f"ended_by={E.get('ended_by')} nonhold={nonhold[:5]} homes={[(h['where'], h.get('result')) for h in homes]} SAVED={n_saved}")
        chk("H5_torque_kept", len(disc) >= 1 and all(d["kwargs"].get("disable_torque") is False for d in disc) and es.get("torque_left_on") is True,
            f"disconnect={[(d['args'], d['kwargs']) for d in disc]} torque_left_on={es.get('torque_left_on')}")
        res["meta"] = {"out": str(out), "scenario": a.scenario, "duration_s": dur, "n_writes": len(W), "marks": marks}
        (out / "result.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
        print(("ALL_PASS" if ok else "SOME_FAIL"), out, flush=True)
        return 0 if ok else 1

    # ---- v2 공통 (모든 시나리오): 자동 원위치 복귀 명령 0 · 토크 유지 · 끝 상태 기록
    E = EH0.LAST_STATE or {}
    t_pol0 = min((w[0] for w in pol), default=None)
    t_pol1 = max((w[0] for w in pol), default=None)
    post = [w for w in W if t_pol1 is not None and w[0] > t_pol1 and not w[3].get("in_policy")]
    init = (E.get("initial_position") or {})
    non_hold, toward = [], []
    for w in post:
        dev = max(abs(w[1][j] - w[2][j]) for j in J5)
        if dev > 0.5:
            non_hold.append(round(dev, 2))
        if init:  # 보낸 Goal 이 Present 보다 시작 자세 쪽으로 0.5° 넘게 간 관절이 있으면 '복귀 명령'
            if any(abs(init[f"{j}.pos"] - w[2][j]) - abs(init[f"{j}.pos"] - w[1][j]) > 0.5 for j in J5 if f"{j}.pos" in init):
                toward.append(round(w[0] - t_pol1, 3))
    homing = [m for m in marks if m.startswith("[eval_ui] HOM")]
    chk("R1_auto_return_cmds_zero", not toward and not non_hold and not homing,
        f"post-policy writes={len(post)} (모두 제자리 유지여야 함) non_hold={non_hold[:5]} toward_initial={toward[:5]} eval_ui HOMING marks={homing} "
        f"blocked return calls={len(E.get('blocked_returns') or [])}")
    es_p = out / "end_state.json"
    es = json.loads(es_p.read_text()) if es_p.exists() else {}
    chk("R2_end_state_written", es.get("torque_left_on") is True and es.get("bus_ok_at_teardown") and es.get("auto_return_blocked_calls") is not None
        and (E.get("teardown") or {}).get("lerobot_return_flag") is False,
        f"ended_by={es.get('ended_by')} max_diff={es.get('max_abs_diff_deg')} torque_left_on={es.get('torque_left_on')} "
        f"lerobot return flag={(E.get('teardown') or {}).get('lerobot_return_flag')} steps={es.get('teardown_steps')}")
    chk("R3_torque_not_disabled", len(disc) >= 1 and all(d["kwargs"].get("disable_torque") is False or (d["args"] and d["args"][0] is False) for d in disc),
        f"FakeBus.disconnect calls={[(d['args'], d['kwargs']) for d in disc]}")
    chk("R4_end_hold_written", len(E.get("holds") or []) >= 1, f"holds={[(h['why'], ) for h in (E.get('holds') or [])]}")
    info("end_pose_vs_initial", {"max_abs_diff_deg": es.get("max_abs_diff_deg"), "diff": es.get("diff_from_initial_deg")})
    res["meta"] = {"out": str(out), "scenario": a.scenario, "ckpt": a.ckpt, "duration_s": dur, "n_writes": len(W), "n_policy_writes": len(pol),
                   "rtc_logs": [(round(t - (inj["t_first_fail"] or t), 3), m) for t, m in rtc_logs][:40], "marks": marks,
                   "fault_blocked": (F or {}).get("n_blocked"), "r2_blocked": (S or {}).get("n_blocked")}
    (out / "result.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    print(("ALL_PASS" if ok else "SOME_FAIL"), out, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
