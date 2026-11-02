#!/home/user/so101-env/bin/python
"""Preview 용 가짜 lerobot-record — 로봇·리더·카메라·lerobot 을 전혀 불러오지 않는다. dataset 도 쓰지 않는다.

r12_collect.py preview 가 LEROBOT_RECORD 로 지정한다. 화면·터미널이 실제 녹화 때와 같은 경로로 움직이게:
  - lerobot_record.record() 의 판 반복 구조(녹화 → reset → 저장 / ← 다시 찍기 / Esc)를 그대로 흉내 낸 record()
  - 실제 녹화와 **같은** r12_record_entry.install() (준비 단계 · 시작 자세 검사 · 화면 탭) 을 이 가짜 모듈에 끼운다
  - 키는 lerobot TerminalKeyListener 와 같은 규칙 (→/n 다음 · ←/r 다시 · Esc/q 종료), 같은 안내 문장 출력
관측·명령 = 기존 녹화(d2 를 이룬 세션)의 review 영상(front|wrist) + 같은 판의 observation.state·action 을 재생 (읽기만),
또는 --source dummy 면 만든 그림 + 고정 관절값.
"""

import argparse
import datetime
import os
import select
import sys
import termios
import threading
import time
import tty
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r12_common as rc  # noqa: E402

HOME = os.path.expanduser("~")
DEFAULT_SRC_SESSION = os.path.join(HOME, "so101_runs/main_k8/redbox_t1_known")


def log(msg):
    print(f"INFO {datetime.datetime.now():%Y-%m-%d %H:%M:%S} fake_record.py {msg}", flush=True)


class Source:
    """review 영상 한 판 (1280×480 = front|wrist) + 같은 판의 state/action. 끝나면 처음으로."""

    def __init__(self, kind, session_dir, episode):
        import numpy as np

        self.np = np
        self.kind = kind
        self.i = 0
        if kind == "dummy":
            self.state = {"shoulder_pan.pos": -2.2, "shoulder_lift.pos": 17.5, "elbow_flex.pos": 7.1,
                          "wrist_flex.pos": 73.4, "wrist_roll.pos": 4.4, "gripper.pos": 28.2}
            self.label = "더미 영상 (만든 그림) · 관절값 고정 (d2 접근 구간 중앙값)"
            return
        import av
        import pandas as pd
        import glob

        self.video = os.path.join(session_dir, "review_videos", f"episode_{episode:03d}.mp4")
        fs = sorted(glob.glob(os.path.join(session_dir, "dataset", "data", "*", "*.parquet")))
        df = pd.concat([pd.read_parquet(f, columns=["observation.state", "action", "episode_index"]) for f in fs])
        d = df[df.episode_index == episode]
        self.S = np.stack(d["observation.state"].values)
        self.A = np.stack(d["action"].values)
        self.av = av
        self._open()
        rel = os.path.relpath(session_dir, os.path.join(HOME, "so101_runs"))
        self.label = f"기존 녹화 {rel} episode {episode} 재생 (d2 구성 세션, 읽기만)"

    def _open(self):
        self.c = self.av.open(self.video)
        self.it = self.c.decode(video=0)
        self.k = 0

    def step(self):
        np = self.np
        if self.kind == "dummy":
            self.i += 1
            f = np.full(rc.FRAME_SHAPE, 60, np.uint8)
            w = np.full(rc.FRAME_SHAPE, 45, np.uint8)
            x = 200 + int(80 * np.sin(self.i / 20))
            w[260:330, x:x + 70] = (200, 30, 40)
            f[180:200, 300:320] = (200, 30, 40)
            for img, t in ((f, "DUMMY FRONT"), (w, "DUMMY WRIST")):
                img[10:40, 10:300] = 120
            st = dict(self.state)
            return f, w, st, dict(st)
        try:
            fr = next(self.it)
        except StopIteration:
            self.c.close()
            self._open()
            fr = next(self.it)
        img = fr.to_ndarray(format="rgb24")
        k = min(self.k, len(self.S) - 1)
        self.k += 1
        names = [f"{j}.pos" for j in rc.JOINTS]
        st = {n: float(v) for n, v in zip(names, self.S[k])}
        ac = {n: float(v) for n, v in zip(names, self.A[k])}
        return img[:, :640].copy(), img[:, 640:].copy(), st, ac


class FakeRobot:
    name = "so_follower(preview-fake)"

    def __init__(self, src):
        self.src = src
        self.last_action = None
        self.is_connected = False

    def connect(self):
        self.is_connected = True  # 장치를 열지 않는다

    def disconnect(self):
        self.is_connected = False

    def get_observation(self):
        f, w, st, ac = self.src.step()
        self.last_action = ac
        return {**st, "front": f, "wrist": w}

    def send_action(self, a):
        return a


class FakeTeleop:
    def __init__(self, robot):
        self.robot = robot
        self.is_connected = False

    def connect(self):
        self.is_connected = True

    def disconnect(self):
        self.is_connected = False

    def get_action(self):
        return dict(self.robot.last_action or {})


class FakeDataset:
    def __init__(self, start):
        self.num_episodes = start
        self.buf = 0

    def add_frame(self, frame):
        self.buf += 1

    def clear_episode_buffer(self):
        self.buf = 0

    def save_episode(self):
        if self.buf == 0:
            raise ValueError("빈 판 저장 시도 (실제 lerobot 도 거부)")
        print("Map: 100%|██████████| 1/1 [00:00<00:00]  (preview: 디스크에 쓰지 않음)", flush=True)
        time.sleep(1.2)
        log(f"[preview] episode {self.num_episodes} 저장 흉내 — {self.buf} 프레임 (쓰지 않음)")
        self.num_episodes += 1
        self.buf = 0


def key_listener(events):
    """lerobot TerminalKeyListener 와 같은 규칙. stdin(pty) 을 cbreak 로."""
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except termios.error:
        old = None

    def rd(timeout):
        r, _, _ = select.select([fd], [], [], timeout)
        return os.read(fd, 1).decode(errors="ignore") if r else None

    def apply(c):
        if c == "right":
            print("Right arrow key pressed. Exiting loop...", flush=True)
            events["exit_early"] = True
        elif c == "left":
            print("Left arrow key pressed. Exiting loop and rerecord the last episode...", flush=True)
            events["rerecord_episode"] = True
            events["exit_early"] = True
        elif c == "esc":
            print("Escape key pressed. Stopping data recording...", flush=True)
            events["stop_recording"] = True
            events["exit_early"] = True

    def run():
        while not events.get("_closed"):
            ch = rd(0.2)
            if ch is None:
                continue
            if ch == "\x1b":
                ch2 = rd(0.02)
                if ch2 is None:
                    apply("esc")
                elif ch2 in "[O":
                    ch3 = rd(0.02)
                    apply({"C": "right", "D": "left"}.get(ch3 or ""))
                continue
            low = ch.lower()
            apply({"n": "right", "r": "left", "q": "esc"}.get(low))

    th = threading.Thread(target=run, daemon=True)
    th.start()
    return old


PROC = {"teleop_action_processor": None, "robot_action_processor": None, "robot_observation_processor": None}


def make_module(src, start_episodes):
    lr = types.ModuleType("fake_lerobot_record")

    def record_loop(robot, events, fps, teleop_action_processor=None, robot_action_processor=None,
                    robot_observation_processor=None, dataset=None, teleop=None, control_time_s=None,
                    single_task=None, display_data=False, display_mode="rerun", display_compressed_images=False, timer=None):
        t_start = time.perf_counter()
        nxt = t_start
        while time.perf_counter() - t_start < control_time_s:
            if events["exit_early"]:
                events["exit_early"] = False
                break
            obs = robot.get_observation()
            act = teleop.get_action()
            robot.send_action(act)
            if dataset is not None:
                dataset.add_frame({"task": single_task})
            if display_data:
                lr.log_visualization_data(display_mode, observation=obs, action=act, compress_images=False)
            nxt += 1 / fps
            time.sleep(max(0.0, nxt - time.perf_counter()))

    def record(cfg):
        """lerobot_record.record() 의 판 반복 구조와 같다 (0.6.2, 501–563행)."""
        if cfg["display_data"]:
            lr.init_visualization("rerun", session_name="recording")
        robot = FakeRobot(src)
        teleop = FakeTeleop(robot)
        dataset = FakeDataset(start_episodes)
        events = {"exit_early": False, "rerecord_episode": False, "stop_recording": False}
        teleop.connect()
        robot.connect()
        old = key_listener(events)
        try:
            recorded = 0
            while recorded < cfg["num_episodes"] and not events["stop_recording"]:
                ep = dataset.num_episodes
                log(f"Recording episode {ep}")
                lr.record_loop(robot=robot, events=events, fps=cfg["fps"], teleop=teleop, dataset=dataset, **PROC,
                               control_time_s=cfg["episode_time_s"], single_task=cfg["task"], display_data=True)
                if not events["stop_recording"] and ((recorded < cfg["num_episodes"] - 1) or events["rerecord_episode"]):
                    log("Reset the environment")
                    lr.record_loop(robot=robot, events=events, fps=cfg["fps"], teleop=teleop, **PROC,
                                   control_time_s=cfg["reset_time_s"], single_task=cfg["task"], display_data=True)
                if events["rerecord_episode"]:
                    log("Re-record episode")
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()
                    continue
                dataset.save_episode()
                recorded += 1
        finally:
            log("Stop recording")
            robot.disconnect()
            teleop.disconnect()
            events["_closed"] = True
            if old is not None:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)
            lr.shutdown_visualization("rerun")
            log("Exiting")

    lr.record_loop = record_loop
    lr.record = record
    lr.init_visualization = lambda *a, **k: None
    lr.log_visualization_data = lambda *a, **k: None
    lr.shutdown_visualization = lambda *a, **k: None
    return lr


def arg(argv, name, default):
    for a in argv:
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return default


def main():
    if "lerobot" in sys.modules:
        print("preview 중단: lerobot 이 불려 있음", file=sys.stderr)
        return 2
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview-source", default="d2")
    ap.add_argument("--preview-session", default=DEFAULT_SRC_SESSION)
    ap.add_argument("--preview-episode", type=int, default=5)
    ap.add_argument("--preview-start", type=int, default=0, help="이미 저장된 판 수 흉내 (episode 번호 시작)")
    ap.add_argument("--simulate-connect-error", action="store_true", help="연결 실패 흉내 (오류 처리 시험)")
    a, rest = ap.parse_known_args()
    if a.simulate_connect_error:
        print("[preview] 연결 실패 흉내", flush=True)
        print("Traceback (most recent call last):\nConnectionError: Could not connect on port '/dev/so101_follower' (preview 흉내)", flush=True)
        return 1
    print("[preview] PREVIEW 모드 — lerobot·로봇·리더·카메라를 불러오지 않고, dataset 을 쓰지 않아요.", flush=True)
    src = Source(a.preview_source, a.preview_session, a.preview_episode)
    live = os.environ.get("R12_LIVE_DIR")
    if live:
        rc.write_json(os.path.join(live, "preview_source.json"), {"label": src.label})
    import r12_record_entry as entry

    lr = make_module(src, a.preview_start)
    entry.install(lr)
    cfg = {"display_data": True, "fps": int(arg(rest, "--dataset.fps", 30)),
           "num_episodes": int(arg(rest, "--dataset.num_episodes", 3)),
           "episode_time_s": float(arg(rest, "--dataset.episode_time_s", 45)),
           "reset_time_s": float(arg(rest, "--dataset.reset_time_s", 3600)),
           "task": arg(rest, "--dataset.single_task", "pick up the red cube and put it in the brown box")}
    entry.emit(ev="entry", argv=rest, preview=True)
    lr.record(cfg)
    assert "lerobot" not in sys.modules, "preview 에서 lerobot 이 불렸어요"
    return 0


if __name__ == "__main__":
    sys.exit(main())
