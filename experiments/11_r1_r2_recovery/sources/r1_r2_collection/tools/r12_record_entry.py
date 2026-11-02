#!/home/user/so101-env/bin/python
"""lerobot-record 대신 실행되는 얇은 진입점 (R1/R2 수집용). r12_collect.py record 가 LEROBOT_RECORD 로 지정한다.

lerobot 0.6.2 의 lerobot_record.record() 를 그대로 부른다 — 로봇·리더 연결, observation.state/action 기록,
add_frame/save_episode, dataset 형식은 d2 와 같은 코드다. 바꾸는 것은 세 가지뿐:
  1) 화면 탭: --display_data 경로 (init/log/shutdown_visualization) 를 rerun 대신 /dev/shm 공유 파일 쓰기로 바꾼다.
     (record_loop 가 매 틱 부르는 자리. 녹화되는 값은 건드리지 않는다.)
  2) 준비 단계: 녹화하는 record_loop 앞에는 항상 '준비'(녹화 안 함, 리더로 팔 조종) 단계가 있다.
     lerobot 의 reset 단계가 곧 다음 판 준비이고, 첫 판·다시 찍기(←) 앞에는 같은 준비 단계를 끼워 넣는다.
     → 오류 자세를 만드는 동작이 정답 action 으로 녹화되지 않는다. 준비 단계는 시간 초과로 끝나지 않는다 (→ 로만 끝).
     (4차) 결과 단계의 → 는 방금 판 저장 뒤 다시 준비 단계로 간다 — 녹화는 늘 준비 단계 → 바로 뒤에 시작 (저장 사이 공백 없음).
  3) 시작 자세 검사: 준비 단계에서 → 를 눌렀을 때 r12_common.safety_check 가 BLOCK 이면 녹화를 시작하지 않고 준비를 계속한다.

표준 출력에 '[r12] {json}' 줄로 단계를 알린다 (r12_collect.py 의 화면이 읽는다, 원본 로그에도 남는다).
환경 변수: R12_LIVE_DIR (공유 폴더, 필수) · R12_CONFIG · R12_RUN_ID
"""

import collections
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r12_common as rc  # noqa: E402

LIVE = os.environ.get("R12_LIVE_DIR")
RUN_ID = os.environ.get("R12_RUN_ID", time.strftime("%Y%m%d_%H%M%S"))
CFG = rc.load_config(os.environ.get("R12_CONFIG"))
LIMITS = rc.calib_limits(CFG)
SETUP_MAX = float(CFG["safety"].get("setup_max_s", 3600))


def emit(**ev):
    ev.setdefault("run_id", RUN_ID)
    print("[r12] " + json.dumps(ev, ensure_ascii=False), flush=True)


class Tap:
    """record_loop 이 매 틱 부르는 log_visualization_data 자리. 마지막 관측·명령을 들고, 공유 파일에 쓴다."""

    def __init__(self, live_dir, fps):
        self.fps = fps
        self.frames = rc.LiveFrames(live_dir, create=True) if live_dir else None
        self.status_path = os.path.join(live_dir, "status.json") if live_dir else None
        self.phase, self.ep, self.attempt = "connect", None, None
        self.state = self.action = None
        self.tick = 0
        self.last_t = None
        self.reset_counters()
        self.sig = {}
        self.error = None
        self.setup_pan = collections.deque(maxlen=int(3 * fps))

    def reset_counters(self):
        self.rec_frames = 0
        self.dt_sum = 0.0
        self.dt_n = 0
        self.late = 0
        self.stall = {c: 0 for c in rc.CAMS}
        self.hz = 0.0
        self.thumbs = []  # 녹화 중 10 틱마다 front·wrist 1/4 축소 (이전 판 다시 보기 용, 녹화 값과 무관)
        self.rec_pan, self.rec_grip = [], []  # 녹화 중 틱마다 팔로워 pan · 명령 그리퍼 (R1 복구 측정, 기록 값과 같은 관측)

    def set_phase(self, phase, ep=None):
        if phase == "setup":
            self.setup_pan = collections.deque(maxlen=int(3 * self.fps))  # 준비 단계 마지막 3 s 팔로워 pan (녹화 안 함, 사건 기록용)
        self.phase = phase
        if ep is not None:
            self.ep = ep
        self.last_t = None
        self.write_status(force=True)

    def on_data(self, display_mode=None, observation=None, action=None, compress_images=False):
        if self.error:
            return
        try:
            self._on_data(observation, action)
        except Exception as e:  # 탭 오류로 녹화가 멈추면 안 된다 — 한 번 알리고 끈다
            self.error = repr(e)
            emit(ev="tap_error", error=self.error)

    def _on_data(self, obs, action):
        now = time.perf_counter()
        if self.last_t is not None:
            dt = now - self.last_t
            self.dt_sum += dt
            self.dt_n += 1
            self.hz = 0.9 * self.hz + 0.1 / max(dt, 1e-6) if self.hz else 1 / max(dt, 1e-6)
            if self.phase == "rec" and dt > 1.5 / self.fps:
                self.late += 1
        self.last_t = now
        self.tick += 1
        if self.phase == "rec":
            self.rec_frames += 1  # record_loop 은 add_frame 뒤에 이 함수를 부른다 → 기록된 프레임 수
        self.state = {k: float(v) for k, v in obs.items() if k.endswith(".pos")}
        self.action = {k: float(v) for k, v in (action or {}).items() if k.endswith(".pos")}
        if getattr(self, "catchup_check", False) and self.action:
            self.catchup_check = False
            gap = max((abs(self.action[k] - self.state[k]) for k in self.action if k in self.state and not k.startswith("gripper")), default=0.0)
            if gap > 10:
                emit(ev="setup_note", ep=self.ep, msg=f"준비 시작 때 리더−팔로워 {gap:.0f}° — 팔로워가 리더 쪽으로 빠르게 따라감 (녹화 안 됨). "
                                                      "저장 중에는 리더를 그대로 두세요")
        pan = self.state.get("shoulder_pan.pos")
        if pan is not None:
            if self.phase == "setup":
                self.setup_pan.append(round(pan, 2))
            elif self.phase == "rec":
                self.rec_pan.append(round(pan, 2))
                self.rec_grip.append(round(self.action.get("gripper.pos", float("nan")), 1))
        if self.phase == "rec" and self.rec_frames % 10 == 1 and all(obs.get(c) is not None for c in rc.CAMS):
            self.thumbs.append([obs[c][::4, ::4].copy() for c in rc.CAMS])
        for i, c in enumerate(rc.CAMS):
            img = obs.get(c)
            if img is None:
                continue
            sig = img[::97, ::89].tobytes()  # 성긴 표본 — 같은 프레임이 그대로 다시 오면 카메라 멈춤
            if self.sig.get(c) == sig and self.phase == "rec":
                self.stall[c] += 1
            self.sig[c] = sig
            if self.frames is not None and self.tick % 2 == 0:
                self.frames.put(i, img)
        if self.frames is not None and self.tick % 2 == 0:
            self.frames.bump()
        if self.tick % 3 == 0:
            self.write_status()

    def checks(self):
        return rc.safety_check(self.state, self.action, CFG, LIMITS)

    def write_status(self, force=False):
        if not self.status_path:
            return
        rc.write_json(self.status_path, {
            "t": time.time(), "phase": self.phase, "ep": self.ep, "attempt_id": self.attempt, "fps": self.fps,
            "loop_hz": round(self.hz, 2), "rec_frames": self.rec_frames, "late_ticks": self.late,
            "stall_ticks": self.stall, "state": self.state, "action": self.action,
            "checks": self.checks() if self.state else [], "tap_error": self.error, "run_id": RUN_ID})

    def write_last(self, ep):
        """방금 녹화한 판의 축소 영상 → live/last_episode.npy + .json (p 키 '이전 판 확인'). 녹화 dataset 과 별개."""
        if not self.status_path or not self.thumbs:
            return
        import numpy as np

        d = os.path.dirname(self.status_path)
        arr = np.stack([np.stack(t) for t in self.thumbs])  # (n, 2, 120, 160, 3)
        tmp = os.path.join(d, ".last_episode.npy")
        np.save(tmp, arr)
        os.replace(tmp, os.path.join(d, "last_episode.npy"))
        rc.write_json(os.path.join(d, "last_episode.json"), {"ep": ep, "attempt_id": self.attempt, "n": len(arr), "every_ticks": 10,
                                                             "duration_s": round(self.rec_frames / self.fps, 1), "fps": self.fps,
                                                             "pan": self.rec_pan, "grip_cmd": self.rec_grip, **self.rec_summary()})

    def rec_summary(self):
        return {"frames": self.rec_frames, "loop_hz_mean": round(self.dt_n / self.dt_sum, 2) if self.dt_sum else None,
                "late_ticks": self.late, "stall_ticks": sum(self.stall.values()), "stall_by_cam": self.stall}


def install(lr):
    """lerobot_record 모듈의 이름을 바꿔 끼운다 (모듈 전역을 찾는 record()/record_loop 에 적용됨)."""
    fps_holder = {}
    tap_holder = {}

    def init_visualization(display_mode, **kw):
        pass

    def log_visualization_data(display_mode, observation=None, action=None, compress_images=False):
        t = tap_holder.get("tap")
        if t is not None:
            t.on_data(display_mode, observation, action, compress_images)

    def shutdown_visualization(display_mode):
        t = tap_holder.get("tap")
        if t is not None:
            t.set_phase("closed")

    orig_loop = lr.record_loop
    st = {"armed": False}

    def tap_for(fps):
        if "tap" not in tap_holder:
            tap_holder["tap"] = Tap(LIVE, fps)
            fps_holder["fps"] = fps
        return tap_holder["tap"]

    def setup_phase(robot, events, fps, kw, after_episode, next_ep):
        """준비 단계 (녹화 안 함). 반환 'armed' | 'stop'.
        after_episode=True (lerobot reset 단계): ← = 방금 녹화한 판 버리기 예약 (되돌릴 수 없음) — 준비는 계속하고,
        → 로 시작할 때 events['rerecord_episode'] 를 다시 세워 record() 가 그 판을 버리고 같은 번호로 녹화하게 한다."""
        tap = tap_for(fps)
        kw = {k: v for k, v in kw.items() if k not in ("dataset", "timer", "control_time_s")}
        pending = bool(events["rerecord_episode"]) and after_episode  # REC 중 ← 로 이미 버리기 예약
        events["rerecord_episode"] = False
        tap.attempt = None
        tap.set_phase("setup", next_ep)
        emit(ev="setup_start", ep=next_ep, after_episode=after_episode, discard_pending=pending)
        tap.catchup_check = True  # 준비 첫 틱에 리더−팔로워 차이를 알림 (저장 중 리더가 움직였으면 팔로워가 빠르게 따라감 — 녹화 안 됨)
        while True:
            t0 = time.monotonic()
            orig_loop(robot=robot, events=events, fps=fps, dataset=None, control_time_s=SETUP_MAX, **kw)
            if events["stop_recording"]:
                if pending:
                    events["rerecord_episode"] = True  # Esc: 예약된 판은 버리고 끝냄
                emit(ev="setup_end", ep=next_ep, reason="stop", discard_pending=pending)
                return "stop"
            if events["rerecord_episode"]:
                events["rerecord_episode"] = False
                if after_episode:
                    if not pending:
                        pending = True
                        emit(ev="discard_pending", ep=next_ep)
                else:
                    emit(ev="setup_note", ep=next_ep, msg="버릴 판이 없어요 — 준비를 계속합니다")
                continue
            if time.monotonic() - t0 >= SETUP_MAX - 0.5:
                emit(ev="setup_timeout", ep=next_ep)  # 저절로 녹화를 시작하지 않는다
                continue
            if after_episode:
                # 4차 (2026-11-02): 결과 단계의 → = 방금 판 저장 (또는 버리기) 뒤 '준비 단계' 로. 바로 녹화하지 않는다.
                # 전에는 → 뒤 저장(~6 s) 이 끝나자마자 녹화가 시작돼, 저장 중 움직인 리더 쪽으로 팔로워가 첫 프레임부터 튐
                # (practice/r1_try2 ep1: 리더−팔로워 pan 34°, 0.3 s 에 28°). 이제 녹화는 늘 준비 단계의 → (안전 검사) 바로 뒤에 시작.
                if pending:
                    events["rerecord_episode"] = True
                st["armed"] = False
                emit(ev="reset_end", ep=next_ep, discard_previous=pending)
                return "next"
            checks = tap.checks()
            if rc.blocking(checks):
                emit(ev="blocked", ep=next_ep, checks=checks, state=tap.state, action=tap.action)
                tap.write_status(force=True)
                continue
            tap.attempt = uuid.uuid4().hex[:12]
            ep_armed = (next_ep - 1) if (pending and next_ep is not None) else next_ep
            emit(ev="armed", ep=ep_armed, attempt_id=tap.attempt, checks=checks, state=tap.state, action=tap.action,
                 discard_previous=pending, setup_pan=list(tap.setup_pan))
            if pending:
                events["rerecord_episode"] = True
            st["armed"] = True
            st["armed_state"] = dict(tap.state)
            return "armed"

    def record_loop(robot, events, fps, teleop_action_processor, robot_action_processor, robot_observation_processor,
                    dataset=None, teleop=None, control_time_s=None, single_task=None, display_data=False,
                    display_mode="rerun", display_compressed_images=False, timer=None):
        kw = dict(teleop_action_processor=teleop_action_processor, robot_action_processor=robot_action_processor,
                  robot_observation_processor=robot_observation_processor, teleop=teleop, single_task=single_task,
                  display_data=display_data, display_mode=display_mode,
                  display_compressed_images=display_compressed_images)
        if dataset is None:  # lerobot 의 reset 단계 = 방금 판 결과 입력 + 다음 판 준비
            tap = tap_for(fps)
            setup_phase(robot, events, fps, kw, after_episode=True, next_ep=None if tap.ep is None else tap.ep + 1)
            return
        ep = dataset.num_episodes
        if not st["armed"]:  # 첫 판 · 다시 찍기 앞: 준비 단계를 끼워 넣는다
            r = setup_phase(robot, events, fps, kw, after_episode=False, next_ep=ep)
            if r == "stop":
                # 아무것도 녹화하지 않았다 → record() 가 빈 판을 저장하지 않고 (다시 찍기 경로로 버리고) 끝내게 한다
                events["rerecord_episode"] = True
                emit(ev="stop_before_rec", ep=ep)
                return
        st["armed"] = False
        tap = tap_for(fps)
        tap.reset_counters()
        tap.set_phase("rec", ep)
        first = {}

        def first_tick(display_mode_, observation=None, action=None, compress_images=False):
            if not first:
                first["state"] = {k: float(v) for k, v in observation.items() if k.endswith(".pos")}
                a = st.get("armed_state") or {}
                shift = max((abs(first["state"][k] - a[k]) for k in a if k in first["state"]), default=None)
                emit(ev="rec_start", ep=ep, attempt_id=tap.attempt, state=first["state"],
                     shift_from_armed_deg=None if shift is None else round(shift, 2))
            log_visualization_data(display_mode_, observation, action, compress_images)

        lr.log_visualization_data = first_tick
        try:
            orig_loop(robot=robot, events=events, fps=fps, dataset=dataset, control_time_s=control_time_s, timer=timer,
                      **{k: v for k, v in kw.items()})
        finally:
            lr.log_visualization_data = log_visualization_data
            try:
                tap.write_last(ep)
            except Exception as e:  # 다시 보기 파일 실패로 녹화가 멈추면 안 됨
                emit(ev="tap_error", error=f"last_episode {e!r}")
            emit(ev="rec_end", ep=ep, attempt_id=tap.attempt, **tap.rec_summary(),
                 rerecord=bool(events.get("rerecord_episode")), stop=bool(events.get("stop_recording")))
            tap.set_phase("after_rec", ep)

    lr.init_visualization = init_visualization
    lr.log_visualization_data = log_visualization_data
    lr.shutdown_visualization = shutdown_visualization
    lr.record_loop = record_loop
    return tap_holder


def main():
    if not LIVE:
        print("R12_LIVE_DIR 가 없어요 — r12_collect.py record 로 실행하세요.", file=sys.stderr)
        return 2
    argv = [a for a in sys.argv[1:] if not a.startswith("--display_data")]
    sys.argv = [sys.argv[0]] + argv + ["--display_data=true"]  # 탭 경로를 켠다 (rerun 은 쓰지 않음)
    import lerobot.scripts.lerobot_record as lr

    install(lr)
    emit(ev="entry", argv=argv)
    lr.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
