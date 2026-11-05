"""가짜 장치 e2e: 설치된 lerobot 0.6.2 `lerobot-rollout --strategy.type=dagger --inference.type=rtc` 진입 경로 그대로 + 가짜 HW + stub 정책.

사용: python test_dagger_fake_e2e.py <scenario> <out_dir>
  scenario: S1_normal S2_key_race S3_esc_in_correction S4_leader_fault S5_rtc_fault S6a_enable_stale S6b_enable_present
            S7_adapter_normal S8_adapter_esc_in_correction S9_follower_write_fault
결과: <out_dir>/<scenario>/result.json (검사 결과 + 측정값), raw.json (쓰기·리더·엔진 기록), dataset/

이 스크립트는 실물 장치 · GPU 를 쓰지 않는다 (fake_hil_hw.py 머리말). 실행 전 환경: CUDA_VISIBLE_DEVICES="" , DISPLAY 없음.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CUDA_VISIBLE_DEVICES='' 로 실행해야 함 (GPU 학습 보호)"
assert not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"), "DISPLAY 를 지우고 실행해야 함 (전역 키 후킹 차단)"

import fake_hil_hw as F  # noqa: E402

CKPT = Path.home() / "so101_runs/main_k8/d2/train/32_20000/pi05_expert_bs32_20k/checkpoints/020000/pretrained_model"
TASK = "pick up the red cube and put it in the brown box"


def lerobot_args(scen, out):
    cams = ("{ front: {type: opencv, index_or_path: %s, width: 64, height: 48, fps: 30}, "
            "wrist: {type: opencv, index_or_path: %s, width: 64, height: 48, fps: 30} }" % F.FAKE_CAMS)
    return ["lerobot-rollout", "--strategy.type=dagger", "--strategy.num_episodes=6",
            f"--policy.path={CKPT}", "--device=cpu", "--policy.num_inference_steps=5",
            "--inference.type=rtc", "--inference.rtc.execution_horizon=20", "--inference.rtc.prefix_attention_schedule=EXP",
            "--inference.queue_threshold=30",
            "--robot.type=so101_follower", f"--robot.port={F.FOLLOWER_PORT}", "--robot.id=hil_fake", "--robot.max_relative_target=8",
            f"--robot.cameras={cams}",
            "--teleop.type=so101_leader", f"--teleop.port={F.LEADER_PORT}", "--teleop.id=hil_fake_leader",
            f"--dataset.repo_id=oxr/rollout_hil_fake_{scen}", f"--dataset.root={out}/dataset", "--dataset.no_stamp=true",
            f"--dataset.single_task={TASK}", "--dataset.num_episodes=6", "--dataset.push_to_hub=false",
            "--fps=30", "--play_sounds=false", "--display_data=false"]


OPS = []
PTY_MODE = {"on": False}  # S16: 키를 실제 터미널(pty) 로 넣는다 — 부모 test_pty_terminal.py 가 @@KEY@@ 를 보고 키를 쓴다


def op(kind, **kw):
    OPS.append({"t": F.now(), "kind": kind, **kw})


class Operator:
    """사람 흉내: 키 · 손 움직임 · 표시 키. 키는 lerobot DAggerEvents 에 공식 dispatch 와 같은 방식으로 넣는다."""

    def __init__(self, hil_state=None):
        self.hil = hil_state

    @property
    def ev(self):
        return F.HOLD["strategy"]._events

    def key(self, name):
        op("key", name=name, phase=self.ev.phase.value)
        if PTY_MODE["on"]:
            print(f"@@KEY {name}@@", flush=True)
            time.sleep(0.3)
            return
        if name == "space":
            self.ev.request_transition("pause_resume")
        elif name == "tab":
            self.ev.request_transition("correction")
        elif name == "esc":
            if self.hil is not None:
                self.hil["log"].write("key", event="esc", phase=self.ev.phase.value)
            self.ev.stop_recording.set()
        else:
            if self.hil is not None:
                self.hil["mark"](name)

    def wait_phase(self, p, timeout=10):
        t = time.time()
        while self.ev.phase.value != p:
            if time.time() - t > timeout:
                raise TimeoutError(f"phase {p} not reached")
            time.sleep(0.01)

    def wait_policy_writes(self, n, timeout=60):
        t = time.time()
        while sum(1 for w in F.REC["follower_writes"] if w.get("origin") == "policy") < n:
            if time.time() - t > timeout:
                raise TimeoutError("policy writes not started")
            time.sleep(0.02)

    def wait_leader_torque(self, on, timeout=10):
        t = time.time()
        while F.HOLD["leader_bus"].torque != on:
            if time.time() - t > timeout:
                raise TimeoutError("leader torque state")
            time.sleep(0.01)

    def hand(self, delta, speed=30.0):
        lb = F.HOLD["leader_bus"]
        with lb.lock:
            base = dict(lb.present)
        tgt = {j: base[j] + d for j, d in delta.items()}
        lb.hand_speed = speed
        lb.hand_target = tgt
        op("hand", target=tgt, speed=speed)

    def hand_release(self):
        F.HOLD["leader_bus"].hand_target = None
        op("hand_release")

    def pause_and_take(self):
        self.key("space")
        self.wait_phase("paused")
        self.wait_leader_torque(True)
        time.sleep(2.4)  # 공식 리더 이동 2 s (blocking) 이 끝나길 기다림
        self.key("tab")
        self.wait_phase("correcting")


def script(scen, o: Operator):
    s = time.sleep
    if scen == "S16_adapter_pty_keys":
        # 실제 터미널 키 경로: lerobot TerminalKeyListener → adapter 표시 키 → 공식 dispatch; 끝 메뉴도 터미널 입력
        o.wait_phase("paused", timeout=30)
        s(1.0)
        o.key("space")
        o.wait_phase("autonomous")
        o.wait_policy_writes(20)
        s(1.5)
        o.key("space")
        o.wait_phase("paused")
        o.wait_leader_torque(True)
        s(2.6)
        o.key("tab")
        o.wait_phase("correcting")
        o.key("1")
        o.hand({"shoulder_pan": -20.0}, 30.0)
        s(0.8)
        o.key("m")
        o.key("g")
        o.key("b")
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.6)
        o.key("esc")
        return
    if scen == "S10_adapter_start_paused_reset":
        # A9: PAUSED 로 시작 → 정책 안 움직임 확인 → 원위치(reset) 교정 → 정책 → 교정(R1) → 원위치 → ESC
        o.wait_phase("paused", timeout=30)  # run() 의 events.reset() 이후 (A9)
        s(1.5)
        op("phase_at_start", phase=o.ev.phase.value)
        o.key("tab")
        o.wait_phase("correcting")
        o.key("r")
        o.hand({"shoulder_pan": -5.0}, 20.0)
        s(0.8)
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(1.0)
        o.key("space")
        o.wait_phase("autonomous")
        o.wait_policy_writes(20)
        s(1.5)
        o.pause_and_take()
        o.key("1")
        o.hand({"shoulder_pan": -20.0}, 30.0)
        s(1.0)
        o.key("m")
        o.hand({"gripper": 25.0}, 40.0)
        s(1.0)
        o.key("g")
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.5)
        o.key("tab")
        o.wait_phase("correcting")
        o.key("r")
        o.hand({"shoulder_pan": 15.0, "gripper": -25.0}, 30.0)
        s(1.0)
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.5)
        o.key("esc")
        return
    o.wait_policy_writes(20)
    if scen == "S11_adapter_fast_correction":
        # 교정 중 사람 손이 틱당 8° 보다 빨리 움직임 → clamp 와 저장 action 관계
        s(1.5)
        o.pause_and_take()
        o.hand({"shoulder_pan": -40.0, "shoulder_lift": 30.0}, 600.0)  # 20 °/틱
        s(0.8)
        o.hand({"shoulder_pan": 40.0, "shoulder_lift": -30.0}, 600.0)
        s(0.8)
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.5)
        o.key("esc")
        return
    if scen == "S12_adapter_rtc_fault":
        s(1.5)
        op("inject", what="policy_fail")
        F.HOLD["strategy"]._engine._policy.fail = True
        o.wait_phase("paused", timeout=10)  # A10 강제 정지
        op("forced_pause_seen", phase=o.ev.phase.value)
        o.wait_leader_torque(True)
        s(2.6)
        o.key("space")  # 재개 시도 → 막혀야 함
        s(0.6)
        op("phase_after_space_attempt", phase=o.ev.phase.value)
        o.key("tab")  # 오류 뒤에도 사람 교정은 가능
        o.wait_phase("correcting")
        o.key("2")
        o.hand({"shoulder_pan": -15.0}, 30.0)
        s(0.8)
        o.key("m")
        o.hand({"gripper": 20.0}, 40.0)
        s(0.6)
        o.key("g")
        s(0.3)
        o.key("b")
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.5)
        o.key("esc")
        return
    if scen == "S15_adapter_normal_end_home":
        s(1.5)
        o.pause_and_take()
        o.key("1")
        o.hand({"shoulder_pan": -20.0}, 30.0)
        s(0.8)
        o.key("m")
        s(0.3)
        o.key("g")
        o.key("b")
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.5)
        o.key("esc")
        return
    if scen in ("S1_normal", "S6a_enable_stale", "S6b_enable_present", "S7_adapter_normal", "S17_adapter_viewer_killed", "S18_adapter_tap_fault"):
        s(2.0)
        o.pause_and_take()
        if scen.startswith(("S7", "S17", "S18")):
            o.key("2")  # 유형 R2
        s(0.3)
        o.hand({"shoulder_pan": -25.0, "gripper": 30.0}, 30.0)  # 복구: pan 되돌림 + 그리퍼 열기
        s(1.6)
        if scen.startswith(("S7", "S17", "S18")):
            o.key("m")  # 복구 끝
        o.hand({"gripper": -26.0, "shoulder_lift": 6.0}, 30.0)  # 교정: 접근 + 닫기
        s(1.4)
        if scen.startswith(("S7", "S17", "S18")):
            o.key("g")
        o.hand_release()
        o.key("tab")  # 교정 끝 → 저장
        o.wait_phase("paused")
        s(1.5)
        o.key("space")  # 정책 재개
        o.wait_phase("autonomous")
        if scen.startswith(("S7", "S17", "S18")):
            s(1.0)
            o.key("space")  # 재개 1 s 뒤 정지
            o.wait_phase("paused")
            o.wait_leader_torque(True)
            s(0.3)
            o.key("space")  # 리더 이동 중 두 번째 Space (debounce 대상)
            s(2.6)
            op("phase_after_double_space", phase=o.ev.phase.value)
            if o.ev.phase.value == "autonomous":
                s(0.5)
                o.key("space")
                o.wait_phase("paused")
                s(2.4)
            o.key("tab")
            o.wait_phase("correcting")
        else:
            s(2.5)
            o.pause_and_take()
        o.hand({"shoulder_pan": 10.0}, 20.0)
        s(1.0)
        o.hand_release()
        o.key("tab")
        o.wait_phase("paused")
        s(0.8)
        o.key("esc")
    elif scen == "S2_key_race":
        s(1.5)
        o.key("tab")  # AUTONOMOUS 에서 Tab → 무시돼야
        s(0.3)
        op("phase_after_tab_in_auto", phase=o.ev.phase.value)
        o.key("space")
        o.wait_phase("paused")
        o.wait_leader_torque(True)
        s(0.3)
        o.key("space")  # 리더 이동(blocking) 중 두 번째 Space
        s(3.0)
        op("phase_after_double_space", phase=o.ev.phase.value)
        s(1.0)
        o.key("esc")
    elif scen in ("S3_esc_in_correction", "S8_adapter_esc_in_correction"):
        s(1.5)
        o.pause_and_take()
        o.hand({"shoulder_pan": -15.0}, 30.0)
        s(1.0)
        o.key("esc")
    elif scen in ("S4_leader_fault", "S13_adapter_leader_fault"):
        s(1.5)
        o.pause_and_take()
        o.hand({"shoulder_pan": -15.0}, 30.0)
        s(0.7)
        op("inject", what="leader_read_fail")
        F.HOLD["leader_bus"].fail_reads = True
    elif scen == "S5_rtc_fault":
        s(1.5)
        op("inject", what="policy_fail")
        F.HOLD["strategy"]._engine._policy.fail = True
    elif scen in ("S9_follower_write_fault", "S14_adapter_follower_fault"):
        s(1.5)
        o.pause_and_take()
        o.hand({"shoulder_pan": -15.0}, 30.0)
        s(0.7)
        op("inject", what="follower_write_fail")
        F.HOLD["follower_bus"].fail_writes = True


def main():
    scen, outroot = sys.argv[1], Path(sys.argv[2])
    out = outroot / scen
    if out.exists():
        import shutil
        shutil.rmtree(out)
    out.mkdir(parents=True)
    adapter = scen.startswith(("S7", "S8", "S10", "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18"))
    PTY_MODE["on"] = scen.startswith("S16")
    goal_mode = "present" if scen == "S6b_enable_present" else "stale"
    F.install(goal_on_enable=goal_mode, leader_offset={"shoulder_pan": 15.0, "shoulder_lift": 10.0} if scen.startswith("S10") else None)
    argv = lerobot_args(scen, out)
    hil_state = None
    if adapter:
        sys.path.insert(0, str(Path.home() / "so101_runs/main_k8/d2/eval"))
        os.environ["ROLLOUT_DEBUG_LOG"] = str(out / "debug.log")
        # run_hil.sh 기본과 같게: 팔 필터 OFF (rollout_logged 기본), --rollout_guard=warn 으로 filter_log 만, 교정 clamp keep (8)
        sys.argv = argv + ["--rollout_guard=warn", f"--hil.events={out}/hil_events.jsonl", "--hil.debounce_s=0.8", "--hil.pre_s=3",
                           "--hil.correction_max_relative_target=keep", "--return_to_initial_position=false"] \
            + ([] if os.environ.get("HIL_TEST_NO_TAP") == "1" else [f"--hil.tap={out}/tap", f"--hil.tap_log={out}/tap_log.jsonl"]) \
            + (["--hil.start_paused=true"] if scen.startswith(("S10", "S16")) else ["--hil.start_paused=false"])
        if scen.startswith("S18"):
            os.environ["HIL_TAP_TEST_FAIL_AT"] = "20"  # tap 이 20 번째 기록부터 오류 → tap 만 멈춰야 함
        else:
            os.environ.pop("HIL_TAP_TEST_FAIL_AT", None)
        if scen.startswith("S15"):
            os.environ["HIL_TEST_END_CHOICE"] = "home"
        else:
            os.environ.pop("HIL_TEST_END_CHOICE", None)
        import hil_dagger_entry as H
        hil, rest = H._pop_hil(sys.argv)
        sys.argv = rest
        import rollout_logged as rl
        rl_state = rl.install(rl._OPTS) if rl._OPTS["active"] else None
        sys.argv = rl._ARGV
        hil_state = H.install(hil, list(sys.argv))
        hil_state["log"].write("rollout_logged", active=bool(rl_state), opts=dict(rl._OPTS))
        import lerobot.rollout.strategies.dagger as dmod
        import lerobot.rollout.strategies.core as cmod
        op("adapter_patch", dagger_send_is_core=dmod.send_next_action is cmod.send_next_action,
           dagger_send_name=dmod.send_next_action.__name__, core_send_module=cmod.send_next_action.__module__)
    else:
        sys.argv = argv

    import lerobot.scripts.lerobot_rollout as lr

    viewer = None
    if adapter and os.environ.get("HIL_TEST_NO_TAP") != "1" and scen.startswith(("S7", "S12", "S14", "S16", "S17")):
        import subprocess

        venv = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
        viewer = subprocess.Popen(["nice", "-n", "19", "python3", str(HERE.parent / "tools/hil_viewer.py"), "--tap", f"{out}/tap", "--headless",
                                   "--snap-dir", f"{out}/viewer", "--seconds", "200"], env=venv, stdout=open(out / "viewer.log", "w"),
                                  stderr=subprocess.STDOUT)
        op("viewer_started", pid=viewer.pid)
        if scen.startswith("S17"):
            def _kill():
                time.sleep(9.0)
                viewer.kill()
                op("viewer_killed", pid=viewer.pid, phase=F.HOLD["strategy"]._events.phase.value if F.HOLD["strategy"] else None)
            threading.Thread(target=_kill, daemon=True).start()

    o = Operator(hil_state)
    err = {}

    def run_script():
        try:
            while F.HOLD["strategy"] is None:
                time.sleep(0.05)
            script(scen, o)
        except Exception:
            err["script"] = traceback.format_exc()
            try:
                F.HOLD["strategy"]._events.stop_recording.set()
            except Exception:
                pass

    th = threading.Thread(target=run_script, daemon=True, name="operator")
    th.start()
    t0 = time.time()
    try:
        lr.main()
        err["main"] = None
    except BaseException:
        err["main"] = traceback.format_exc()
    wall = time.time() - t0
    th.join(timeout=5)
    if viewer is not None:
        try:
            viewer.wait(timeout=8)
        except Exception:
            viewer.kill()
        op("viewer_exit", rc=viewer.returncode)
    if adapter and rl_state is not None and rl_state["log"] is not None:
        rl_state["log"].close()
    raw = {"follower_writes": F.REC["follower_writes"], "leader_events": F.REC["leader_events"],
           "engine_events": F.REC["engine_events"], "chunks": F.REC["chunks"], "ops": OPS, "err": err, "wall_s": wall,
           "goal_on_enable": goal_mode, "adapter": adapter, "rec_t0": F.REC["t0"], "leader_reads": F.REC["leader_reads"],
           "policy_fail_t": F.REC["policy_fail_t"], "end_choice_env": os.environ.get("HIL_TEST_END_CHOICE")}
    (out / "raw.json").write_text(json.dumps(raw, default=float))
    print(f"[{scen}] done wall={wall:.1f}s main_err={'yes' if err.get('main') else 'no'} script_err={'yes' if err.get('script') else 'no'}")
    if err.get("main"):
        print(err["main"][-1500:])
    if err.get("script"):
        print(err["script"][-1500:])


if __name__ == "__main__":
    main()
