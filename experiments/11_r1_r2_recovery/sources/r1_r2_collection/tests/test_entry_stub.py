#!/home/user/so101-env/bin/python
"""실제 lerobot 0.6.2 record() + r12_record_entry.install() 를 가짜 로봇·리더로 돌려 dataset 을 임시 폴더에 만든다.
실물 장치 차단 (2026-10-19 mock 사고 뒤 규칙):
  1) 포트·카메라 경로 = /nonexistent/...  2) FeetechMotorsBus/SerialMotorsBus/MotorsBus.connect · OpenCVCamera.connect ·
  serial.Serial.open 을 예외로 막음  3) make_robot_from_config/make_teleoperator_from_config 를 바꿔 가짜만 만들고,
  연결 전에 가짜인지 assert  4) 진짜 SO101Follower/SO101Leader 클래스는 만들지 않는다.
확인: 준비 단계의 쉬는 자세가 녹화되지 않음 · 진입점 안의 안전 조건(BLOCK = NaN·|pan|>95·리더−팔로워>25) · 결과 단계 → = 저장 뒤 준비 ·
     ← 버리기 → 같은 번호 다시 ·
     저장된 판 길이 = rec_end 프레임 수 · info.json features·fps·robot_type·codebase_version 이 d2 와 같음 · Esc 로 준비 중 끝내도 빈 판 저장 없음.

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_entry_stub.py [--root DIR]
"""

import datetime
import json
import os
import queue
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)
D2_INFO = os.path.expanduser("~/so101_runs/main_k8/d2/dataset/meta/info.json")

ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/r12_entry_test_{datetime.datetime.now():%Y%m%d_%H%M%S}"
os.makedirs(ROOT, exist_ok=True)
os.environ["R12_LIVE_DIR"] = os.path.join(ROOT, "live")
os.makedirs(os.environ["R12_LIVE_DIR"], exist_ok=True)
os.environ["R12_RUN_ID"] = "stubtest"

REST = {"shoulder_pan.pos": -4.0, "shoulder_lift.pos": -102.9, "elbow_flex.pos": 96.1, "wrist_flex.pos": 61.8,
        "wrist_roll.pos": 2.7, "gripper.pos": 1.1}  # d2 첫/마지막 프레임 중앙값 = 쉬는 자세
SAFE = {"shoulder_pan.pos": -2.2, "shoulder_lift.pos": 17.5, "elbow_flex.pos": 7.1, "wrist_flex.pos": 73.4,
        "wrist_roll.pos": 4.4, "gripper.pos": 28.2}  # d2 접근 구간 중앙값


# ---------------------------------------------------------------- 장치 차단
def block_hardware():
    import serial

    import lerobot.cameras.opencv.camera_opencv as co
    import lerobot.motors.motors_bus as mb
    from lerobot.motors.feetech import feetech as fe

    def boom(*a, **k):
        raise RuntimeError("시험 중 실물 장치 연결 시도 — 차단됨")

    for cls in [getattr(mb, n) for n in ("MotorsBusBase", "MotorsBus", "SerialMotorsBus") if hasattr(mb, n)] + [fe.FeetechMotorsBus, co.OpenCVCamera]:
        if "connect" in cls.__dict__:
            cls.connect = boom
    serial.Serial.open = boom


class StubRobot:
    name = "so_follower"

    def __init__(self):
        self.cameras = {"front": object(), "wrist": object()}
        self.pose = dict(REST)
        self.is_connected = False
        self.n = 0
        self.sent = []

    @property
    def observation_features(self):
        return {**{k: float for k in REST}, "front": (480, 640, 3), "wrist": (480, 640, 3)}

    @property
    def action_features(self):
        return {k: float for k in REST}

    def connect(self, calibrate=True):
        self.is_connected = True

    def disconnect(self):
        self.is_connected = False

    def get_observation(self):
        self.n += 1
        f = np.full((480, 640, 3), (self.n * 3) % 255, np.uint8)
        w = np.full((480, 640, 3), (self.n * 5) % 255, np.uint8)
        return {**{k: float(v) for k, v in self.pose.items()}, "front": f, "wrist": w}

    def send_action(self, a):
        self.sent.append(dict(a))
        return a


class StubTeleop:
    def __init__(self, robot):
        self.robot = robot
        self.is_connected = False

    def connect(self, calibrate=True):
        self.is_connected = True

    def disconnect(self):
        self.is_connected = False

    def get_action(self):  # 리더 = 팔로워 자세 + 시험용 차이 (저장 중 리더가 움직인 경우 흉내)
        return {k: v + getattr(self.robot, "leader_offset", {}).get(k, 0.0) for k, v in self.robot.pose.items()}


def run_record(lr, entry, argv, script):
    """script(events, q, robot) 를 스레드로 돌리며 lr.main() 실행."""
    robot = StubRobot()
    events = {"exit_early": False, "rerecord_episode": False, "stop_recording": False}
    q = queue.Queue()
    orig_emit = entry.emit

    def emit(**ev):
        q.put(ev)
        orig_emit(**ev)

    entry.emit = emit

    def mk_robot(cfg):
        return robot

    def mk_teleop(cfg):
        return StubTeleop(robot)

    lr.make_robot_from_config = mk_robot
    lr.make_teleoperator_from_config = mk_teleop
    lr.init_keyboard_listener = lambda: (None, events)
    if not isinstance(lr.Teleoperator, tuple):  # record_loop 의 isinstance(teleop, Teleoperator) 를 가짜 리더도 통과하게
        lr.Teleoperator = (lr.Teleoperator, StubTeleop)
    orig_connect = StubRobot.connect

    def guarded_connect(self, calibrate=True):
        assert type(self) is StubRobot, f"가짜가 아닌 로봇: {type(self)}"
        orig_connect(self)

    StubRobot.connect = guarded_connect
    err = []

    def drive():
        try:
            script(events, q, robot)
        except Exception as e:
            err.append(e)
            events["stop_recording"] = True
            events["exit_early"] = True

    th = threading.Thread(target=drive, daemon=True)
    th.start()
    sys.argv = ["lerobot-record"] + argv
    lr.main()
    th.join(5)
    entry.emit = orig_emit
    if err:
        raise err[0]
    return robot


def expect(q, kind, timeout=20, **match):
    end = time.time() + timeout
    while time.time() < end:
        try:
            ev = q.get(timeout=0.2)
        except queue.Empty:
            continue
        if ev.get("ev") == kind and all(ev.get(k) == v for k, v in match.items()):
            return ev
    raise TimeoutError(f"사건 {kind} {match} 이 안 옴")


def press(events, key):
    if key == "right":
        events["exit_early"] = True
    elif key == "left":
        events["rerecord_episode"] = True
        events["exit_early"] = True
    elif key == "esc":
        events["stop_recording"] = True
        events["exit_early"] = True


def main():
    block_hardware()
    import lerobot.scripts.lerobot_record as lr
    import r12_record_entry as entry

    entry.install(lr)
    res = {}
    base = ["--robot.type=so101_follower", "--robot.port=/nonexistent/so101_follower", "--robot.id=r12_stub_test",
            '--robot.cameras={ front: {type: opencv, index_or_path: /nonexistent/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, '
            'wrist: {type: opencv, index_or_path: /nonexistent/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }',
            "--teleop.type=so101_leader", "--teleop.port=/nonexistent/so101_leader", "--teleop.id=r12_stub_test",
            "--dataset.single_task=pick up the red cube and put it in the brown box", "--dataset.episode_time_s=20",
            "--dataset.reset_time_s=3600", "--dataset.push_to_hub=false", "--dataset.no_stamp=true", "--play_sounds=false",
            "--display_data=true"]

    # ---- 시험 1: 준비(막힘) → 녹화 → ← 버리기 → 같은 번호 → 저장 → 마지막 판
    ds1 = os.path.join(ROOT, "ds_main")

    def script1(ev, q, robot):
        expect(q, "setup_start", ep=0)
        robot.pose = {**REST, "elbow_flex.pos": float("nan")}  # 11-02 부터 BLOCK 은 관절값 없음·NaN 뿐 (쉬는 자세는 WARN)
        time.sleep(0.5)
        press(ev, "right")  # NaN → 진입점 안에서 BLOCK
        b = expect(q, "blocked", ep=0)
        res["blocked_codes"] = sorted({c[1] for c in b["checks"] if c[0] == "BLOCK"})
        robot.pose = dict(SAFE)
        time.sleep(0.4)
        press(ev, "right")
        res["armed0"] = expect(q, "armed", ep=0)
        res["rec_start0"] = expect(q, "rec_start", ep=0)
        time.sleep(1.5)
        press(ev, "right")
        res["rec_end0a"] = expect(q, "rec_end", ep=0)
        expect(q, "setup_start", ep=1)
        press(ev, "left")  # 방금 판 버리기 예약
        expect(q, "discard_pending")
        press(ev, "right")  # 4차: 결과 단계 → = 버리기(또는 저장) 뒤 준비 단계 — 녹화 안 함
        res["reset_end_discard"] = expect(q, "reset_end", discard_previous=True)
        expect(q, "setup_start", ep=0, after_episode=False)
        robot.pose = {**REST, "elbow_flex.pos": float("nan")}
        time.sleep(0.3)
        press(ev, "right")  # NaN → 막힘
        expect(q, "blocked")
        robot.pose = {**SAFE, "shoulder_pan.pos": 96.0}  # |pan| > 95 → 막힘 (4차: Pan 은 안전 조건)
        time.sleep(0.3)
        press(ev, "right")
        res["pan_block"] = expect(q, "blocked")
        robot.pose = {**SAFE, "shoulder_pan.pos": 10.0}
        time.sleep(0.3)
        press(ev, "right")
        res["armed0b"] = expect(q, "armed", ep=0)
        res["rec_start0b"] = expect(q, "rec_start", ep=0)
        time.sleep(1.0)
        press(ev, "right")
        res["rec_end0b"] = expect(q, "rec_end", ep=0)
        expect(q, "setup_start", ep=1)
        robot.leader_offset = {"shoulder_pan.pos": 30.0}  # 결과 단계에서 리더를 30° 돌려 둠 (r1_try2 ep1 과 같은 상황)
        time.sleep(0.3)
        press(ev, "right")  # → = 저장 → 준비 (바로 녹화하지 않음)
        res["reset_end1"] = expect(q, "reset_end", discard_previous=False)
        expect(q, "setup_start", ep=1, after_episode=False)
        res["catchup"] = expect(q, "setup_note", timeout=10)
        time.sleep(0.3)
        press(ev, "right")  # 리더−팔로워 30° → 막힘
        res["diff_block"] = expect(q, "blocked")
        robot.leader_offset = {}
        robot.pose = {**SAFE, "shoulder_pan.pos": -20.0}  # 팔 편 접근 자세 + Pan 오차 (R1-B 처럼) — 안전 조건 통과
        time.sleep(0.5)
        press(ev, "right")
        res["armed1"] = expect(q, "armed", ep=1)
        res["rec_start1"] = expect(q, "rec_start", ep=1, timeout=60)
        time.sleep(1.0)
        press(ev, "right")
        res["rec_end1"] = expect(q, "rec_end", ep=1)

    run_record(lr, entry, base + [f"--dataset.root={ds1}", "--dataset.repo_id=test/r12_stub_main", "--dataset.num_episodes=2"], script1)

    # ---- 시험 2: 첫 판 준비 중 Esc → 빈 판 저장 없이 끝
    ds2 = os.path.join(ROOT, "ds_esc")

    def script2(ev, q, robot):
        expect(q, "setup_start", ep=0)
        time.sleep(0.3)
        press(ev, "esc")
        res["stop2"] = expect(q, "stop_before_rec", ep=0)

    run_record(lr, entry, base + [f"--dataset.root={ds2}", "--dataset.repo_id=test/r12_stub_esc", "--dataset.num_episodes=2"], script2)

    # ---- 검사
    import pandas as pd

    ok = []

    def check(name, cond, detail=""):
        print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
        ok.append(bool(cond))

    info = json.load(open(os.path.join(ds1, "meta", "info.json")))
    d2 = json.load(open(D2_INFO))
    check("쉬는 자세 + NaN → BLOCK 이유 = NaN 만 (쉬는 자세 한계·그리퍼 닫힘은 WARN)", res["blocked_codes"] == ["nan_elbow_flex"], str(res["blocked_codes"]))
    check("|pan| 96° → BLOCK pan_abs", "pan_abs" in {c[1] for c in res["pan_block"]["checks"] if c[0] == "BLOCK"})
    check("결과 단계 → = 저장 뒤 준비 단계 (reset_end → setup_start, 녹화 안 함)", res["reset_end1"]["discard_previous"] is False)
    check("저장 중 리더 30° 이동 → 준비 시작 때 알림 + 녹화 시작 BLOCK (diff_shoulder_pan)",
          "30" in res["catchup"]["msg"] and "diff_shoulder_pan" in {c[1] for c in res["diff_block"]["checks"] if c[0] == "BLOCK"})
    check("팔 편 접근 자세 + Pan 오차 −20° 는 안전 조건 통과 (R1-B 시작)", not [c for c in res["armed1"]["checks"] if c[0] == "BLOCK"])
    check("armed 에 준비 단계 pan 열 (복구 측정용)", len(res["armed1"].get("setup_pan") or []) > 10, str(len(res["armed1"].get("setup_pan") or [])))
    lj = json.load(open(os.path.join(ROOT, "live", "last_episode.json")))
    check("판 끝 pan·그리퍼 열 = 녹화 프레임 수 (복구 측정용)", len(lj["pan"]) == len(lj["grip_cmd"]) == lj["frames"], f"{len(lj['pan'])} / {lj['frames']}")
    check("저장 2편", info["total_episodes"] == 2, str(info["total_episodes"]))
    eps = pd.read_parquet(sorted(__import__("glob").glob(os.path.join(ds1, "meta", "episodes", "*", "*.parquet")))[0])
    lens = list(eps["length"])
    check("판 길이 = rec_end 프레임 수 (버린 판 제외)", lens == [res["rec_end0b"]["frames"], res["rec_end1"]["frames"]],
          f"{lens} vs {[res['rec_end0b']['frames'], res['rec_end1']['frames']]}")
    data = pd.concat([pd.read_parquet(f) for f in sorted(__import__("glob").glob(os.path.join(ds1, "data", "*", "*.parquet")))])
    S = np.stack(data["observation.state"].values)
    A = np.stack(data["action"].values)
    check("쉬는 자세(lift −102.9)가 녹화되지 않음", float(S[:, 1].min()) > -50, f"lift min {S[:, 1].min():.1f}")
    e0 = data[data.episode_index == 0]
    check("ep0 = 버린 뒤 다시 찍은 판 (pan 10°)", np.allclose(np.stack(e0["observation.state"].values)[:, 0], 10.0))
    e1 = data[data.episode_index == 1]
    check("ep1 첫 프레임 = 준비 때 자세 (pan −20°) · 리더−팔로워 차이 0", abs(np.stack(e1["observation.state"].values)[0, 0] + 20) < 1e-3
          and abs(np.stack(e1["action"].values)[0, 0] + 20) < 1e-3)
    check("action = 리더 값 그대로 (가짜 리더 = 자세)", np.allclose(S, A))
    ts = e1["timestamp"].values
    check("timestamp = frame_index/30", np.allclose(np.diff(ts), 1 / 30, atol=1e-4))
    keys = ("action", "observation.state", "observation.images.front", "observation.images.wrist", "timestamp", "frame_index",
            "episode_index", "index", "task_index")
    same = all(json.dumps(info["features"][k], sort_keys=True) == json.dumps(d2["features"][k], sort_keys=True) for k in keys)
    check("features (이름·dtype·shape·영상 코덱 설정) d2 와 같음", same and set(info["features"]) == set(d2["features"]))
    check("fps · robot_type · codebase_version d2 와 같음",
          (info["fps"], info["robot_type"], info["codebase_version"]) == (d2["fps"], d2["robot_type"], d2["codebase_version"]))
    tasks = pd.read_parquet(os.path.join(ds1, "meta", "tasks.parquet"))
    check("과제 문장 d2 와 같음 (1개)", list(tasks.index) == list(pd.read_parquet(os.path.dirname(D2_INFO) + "/tasks.parquet").index))
    check("시작 자세 이동 기록 (armed→첫 프레임)", res["rec_start1"]["shift_from_armed_deg"] is not None,
          f"{res['rec_start1']['shift_from_armed_deg']}")
    info2 = json.load(open(os.path.join(ds2, "meta", "info.json")))
    check("준비 중 Esc → 저장 0편, 오류 없음", info2["total_episodes"] == 0)
    print(("PASS" if all(ok) else "FAIL") + f" {sum(ok)}/{len(ok)} · 임시 폴더 {ROOT}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
