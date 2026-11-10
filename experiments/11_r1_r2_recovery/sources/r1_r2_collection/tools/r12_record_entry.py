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
  4) (2026-11-03, 설정 safety.teleop_guard.enabled 일 때만 — 파일럿 12편 설정) 텔레오퍼레이션 명령 보호 TeleopGuard:
     robot.send_action 으로 '보내는' 값만 바꾼다. 녹화되는 action (리더 값) 은 lerobot record_loop 이 그대로 기록한다.
       - 리더 Pan 명령 |·| > pan_cmd_abs_max_deg → 팔로워에는 ±한계까지만
       - 팔 관절 리더−팔로워 차이 > hold_gap_deg → 팔로워를 그 순간 자세에 고정 (점프 · 막힘 밀기 방지).
         리더를 고정 자세 ± release_gap_deg 안으로 맞추면 풀림. 자동 홈 복귀 없음 (고정 = 그 자리).
       - 녹화 중 보호가 걸리면 그 판은 무효: 사유를 알리고 자동으로 버림 (lerobot '다시 찍기' 경로, ← 와 같음)
     녹화 시작 첫 프레임 front · wrist 를 PNG 로 저장 (R12_START_DIR, 별도 스레드).

표준 출력에 '[r12] {json}' 줄로 단계를 알린다 (r12_collect.py 의 화면이 읽는다, 원본 로그에도 남는다).
환경 변수: R12_LIVE_DIR (공유 폴더, 필수) · R12_CONFIG · R12_RUN_ID · R12_START_DIR (시작 프레임 폴더, 없으면 저장 안 함)
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
START_DIR = os.environ.get("R12_START_DIR")
CFG = rc.load_config(os.environ.get("R12_CONFIG"))
LIMITS = rc.calib_limits(CFG)
SETUP_MAX = float(CFG["safety"].get("setup_max_s", 3600))
GUARD_CFG = (CFG["safety"].get("teleop_guard") or {})


def emit(**ev):
    ev.setdefault("run_id", RUN_ID)
    print("[r12] " + json.dumps(ev, ensure_ascii=False), flush=True)


class TeleopGuard:
    """robot.get_observation / send_action 을 감싸 '보내는' 명령만 제한한다 (녹화되는 action = 리더 값은 그대로).
    phase/ep/attempt 는 Tap 에서 읽는다. 걸린 내용은 [r12] guard 사건과 status.json 'guard' 로 알린다."""

    def __init__(self, cfg, tap):
        self.cfg = cfg
        self.tap = tap
        self.events = None
        self.present = None
        self.hold = None          # 고정 중인 팔 관절 목표 {key: °}
        self.hold_reason = ""
        self.warn_since = None
        self.warned = False
        self.n_trips = 0
        self.rec_invalid = None   # 녹화 중 무효 사유 (판마다 초기화)
        self.last = {}            # 화면 표시용

    def install(self, robot):
        if getattr(robot, "_r12_guard", None) is self:
            return
        orig_get, orig_send = robot.get_observation, robot.send_action

        def get_observation(*a, **k):
            obs = orig_get(*a, **k)
            try:
                self.present = {key: float(v) for key, v in obs.items() if key.endswith(".pos")}
            except Exception:  # 관측 형식이 달라도 녹화는 계속
                self.present = None
            return obs

        def send_action(action, *a, **k):
            return orig_send(self.filter(action), *a, **k)

        robot.get_observation, robot.send_action = get_observation, send_action
        robot._r12_guard = self

    def trip(self, reason, **info):
        phase = self.tap.phase
        self.n_trips += 1
        invalid = phase == "rec" and bool(self.cfg.get("invalidate_in_rec", True))
        emit(ev="guard", reason=reason, phase=phase, ep=self.tap.ep, attempt_id=self.tap.attempt, invalid=invalid,
             **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in info.items()})
        if invalid and self.rec_invalid is None and self.events is not None:
            self.rec_invalid = reason
            self.events["rerecord_episode"] = True  # ← 와 같은 경로: 이 판을 저장하지 않음
            self.events["exit_early"] = True

    def filter(self, action):
        if self.present is None:
            return action
        a = dict(action)
        cap = float(self.cfg.get("pan_cmd_abs_max_deg", 95))
        p = a.get("shoulder_pan.pos")
        if p is not None and abs(float(p)) > cap:
            a["shoulder_pan.pos"] = cap if p > 0 else -cap
            if self.last.get("pan_cap") is not True:
                self.trip("pan_cmd_limit", cmd=float(p), sent=a["shoulder_pan.pos"])
            self.last["pan_cap"] = True
        else:
            self.last["pan_cap"] = False
        arm = [f"{j}.pos" for j in rc.ARM_JOINTS if f"{j}.pos" in a and f"{j}.pos" in self.present]
        if not arm:
            return a
        if self.hold is not None:
            back = max(abs(float(a[k]) - self.hold[k]) for k in arm)
            if back <= float(self.cfg.get("release_gap_deg", 10)):
                emit(ev="guard_release", phase=self.tap.phase, ep=self.tap.ep, gap=round(back, 1))
                self.hold = None
            else:
                for k in arm:
                    a[k] = self.hold[k]
                self.last.update(hold=True, gap=round(back, 1))
                return a
        gaps = {k: abs(float(a[k]) - self.present[k]) for k in arm}
        kmax = max(gaps, key=gaps.get)
        gap = gaps[kmax]
        self.last.update(hold=False, gap=round(gap, 1))
        if gap > float(self.cfg.get("hold_gap_deg", 25)):
            self.hold = {k: self.present[k] for k in arm}
            self.hold_reason = f"{kmax.split('.')[0]} 리더−팔로워 {gap:.0f}°"
            for k in arm:
                a[k] = self.hold[k]
            self.last.update(hold=True)
            self.trip("leader_follower_gap", joint=kmax.split(".")[0], gap=gap)
            return a
        now = time.monotonic()
        if gap > float(self.cfg.get("warn_gap_deg", 15)):
            self.warn_since = self.warn_since or now
            if not self.warned and now - self.warn_since >= float(self.cfg.get("warn_s", 1.0)):
                self.warned = True
                emit(ev="guard_warn", phase=self.tap.phase, ep=self.tap.ep, joint=kmax.split(".")[0], gap=round(gap, 1),
                     msg=f"추종 오차 {gap:.0f}° 가 {self.cfg.get('warn_s', 1.0)} s 넘게 이어짐 (팔로워가 막혔거나 리더가 빠름)")
        else:
            self.warn_since, self.warned = None, False
        return a

    def status(self):
        return {"enabled": True, "hold": self.hold is not None, "hold_reason": self.hold_reason if self.hold is not None else "",
                "gap": self.last.get("gap"), "pan_cap": bool(self.last.get("pan_cap")), "trips": self.n_trips,
                "rec_invalid": self.rec_invalid}


def save_start_frames(obs, ep, attempt):
    """녹화 첫 틱의 front · wrist (모델 입력과 같은 RGB) → START_DIR/ep{ep:03d}_{attempt}_{cam}.png. 별도 스레드 (녹화 루프를 막지 않음)."""
    if not START_DIR:
        return {}
    import threading

    imgs = {c: obs.get(c) for c in rc.CAMS}
    files = {c: os.path.join(START_DIR, f"ep{ep:03d}_{attempt}_{c}.png") for c, im in imgs.items() if im is not None}
    imgs = {c: im.copy() for c, im in imgs.items() if im is not None}

    def work():
        try:
            import cv2

            os.makedirs(START_DIR, exist_ok=True)
            for c, im in imgs.items():
                cv2.imwrite(files[c], cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
            emit(ev="start_frames", ep=ep, attempt_id=attempt, files=files)
        except Exception as e:  # 저장 실패로 녹화가 멈추면 안 됨
            emit(ev="tap_error", error=f"start_frames {e!r}")

    threading.Thread(target=work, daemon=True).start()
    return files


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
        self.rec_grip_state = []  # 녹화 중 틱마다 팔로워 그리퍼 (2026-11-03 검토 표시: 첫 닫힘 빈 파지 의심)

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
            held = getattr(self, "guard", None) is not None and gap > float(GUARD_CFG.get("hold_gap_deg", 25))
            if held:  # 명령 보호가 팔로워를 고정함 (점프 없음)
                emit(ev="setup_note", ep=self.ep, msg=f"준비 시작 때 리더−팔로워 {gap:.0f}° — 팔로워를 그 자리에 고정했어요. "
                                                      "리더를 팔로워 자세 쪽으로 천천히 맞추면 풀려요 (저장 중에는 리더를 그대로 두세요)")
            elif gap > 10:
                emit(ev="setup_note", ep=self.ep, msg=f"준비 시작 때 리더−팔로워 {gap:.0f}° — 팔로워가 리더 쪽으로 빠르게 따라감 (녹화 안 됨). "
                                                      "저장 중에는 리더를 그대로 두세요")
        pan = self.state.get("shoulder_pan.pos")
        if pan is not None:
            if self.phase == "setup":
                self.setup_pan.append(round(pan, 2))
            elif self.phase == "rec":
                self.rec_pan.append(round(pan, 2))
                self.rec_grip.append(round(self.action.get("gripper.pos", float("nan")), 1))
                self.rec_grip_state.append(round(self.state.get("gripper.pos", float("nan")), 1))
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
            "checks": self.checks() if self.state else [], "tap_error": self.error, "run_id": RUN_ID,
            "guard": self.guard.status() if getattr(self, "guard", None) else {"enabled": False}})

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
                                                             "pan": self.rec_pan, "grip_cmd": self.rec_grip, "grip_state": self.rec_grip_state,
                                                             **self.rec_summary()})

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
            if GUARD_CFG.get("enabled"):
                tap_holder["tap"].guard = TeleopGuard(GUARD_CFG, tap_holder["tap"])
                emit(ev="guard_on", cfg={k: v for k, v in GUARD_CFG.items()})
        return tap_holder["tap"]

    def guard_for(robot, events, tap):
        g = getattr(tap, "guard", None)
        if g is not None:
            g.install(robot)
            g.events = events
        return g

    def setup_phase(robot, events, fps, kw, after_episode, next_ep):
        """준비 단계 (녹화 안 함). 반환 'armed' | 'stop'.
        after_episode=True (lerobot reset 단계): ← = 방금 녹화한 판 버리기 예약 (되돌릴 수 없음) — 준비는 계속하고,
        → 로 시작할 때 events['rerecord_episode'] 를 다시 세워 record() 가 그 판을 버리고 같은 번호로 녹화하게 한다."""
        tap = tap_for(fps)
        guard_for(robot, events, tap)
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
        g = guard_for(robot, events, tap)
        if g is not None:
            g.rec_invalid = None
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
                save_start_frames(observation, ep, tap.attempt)
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
                 rerecord=bool(events.get("rerecord_episode")), stop=bool(events.get("stop_recording")),
                 guard_invalid=(g.rec_invalid if g is not None else None))
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
