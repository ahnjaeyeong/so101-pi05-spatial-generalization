#!/home/user/so101-env/bin/python
"""교정 시연 파일럿 12편 시험 (로봇 없음). 실물 장치 차단 규칙은 test_entry_stub.py 와 같다 (/nonexistent 경로 · connect 차단 · 가짜 assert).

A. 단위: 파일럿 설정 (extends) · 기존 설정 불변 · 계획 3 개 (R1 4 · R2-P 4 · R2-O 4) · 시작 조건 · 실패 상태 비슷함 · 동시 명령 프로세스 찾기 ·
   닫힘 세기 · 코드 버전 · 파일럿 메타데이터 · 파일럿 QA 규칙
B. 실제 lerobot 0.6.2 record() + r12_record_entry (파일럿 설정 = 명령 보호 켬) + 가짜 팔로워 (보낸 명령을 따라감) · 가짜 리더:
   시작 프레임 PNG · 녹화 중 Pan 명령 100° → 팔로워에는 95° · 무효 → 자동 버림 · 준비 중 리더−팔로워 97° → 팔로워 고정 (점프 없음) →
   리더를 맞추면 풀림 · 정상 녹화 저장 (action = 리더 값 그대로) · 막힌 팔로워 → 고정 + 무효 · 기본 설정에서는 보호 꺼짐

  PYTHONDONTWRITEBYTECODE=1 ~/so101-env/bin/python tests/test_pilot12.py [--root DIR]
"""

import datetime
import glob
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
TOOLS = os.path.join(COLL, "tools")
PILOT_CFG = os.path.join(COLL, "config", "r12_pilot12.yaml")
BASE_CFG = os.path.join(COLL, "config", "r12_scenarios.yaml")
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else f"/tmp/r12_pilot12_test_{datetime.datetime.now():%Y%m%d_%H%M%S}"
os.makedirs(ROOT, exist_ok=True)
# test_entry_stub 의 도우미를 쓰되 그 모듈의 임시 폴더를 이 시험 폴더로 (모듈이 import 때 sys.argv 의 --root 를 읽음)
sys.argv = [sys.argv[0], "--root", ROOT]
sys.path.insert(0, HERE)
sys.path.insert(0, TOOLS)
os.environ["R12_CONFIG"] = PILOT_CFG
os.environ["R12_START_DIR"] = os.path.join(ROOT, "start_frames")
import test_entry_stub as T  # noqa: E402  (R12_LIVE_DIR · R12_RUN_ID 를 ROOT 아래로 정함)
import r12_common as rc  # noqa: E402

OK = []


def check(name, cond, detail=""):
    print(f"  {'✓' if cond else '✗'} {name} {detail}", flush=True)
    OK.append(bool(cond))


# ================================================================ A. 단위
def part_a():
    print("A. 단위")
    base_sha_git = subprocess.run(["git", "-C", COLL, "show", "a72cf56:config/r12_scenarios.yaml"], capture_output=True).stdout
    import hashlib

    check("기존 r12_scenarios.yaml 이 기준 커밋과 같음 (고치지 않음)",
          hashlib.sha256(open(BASE_CFG, "rb").read()).hexdigest() == hashlib.sha256(base_sha_git).hexdigest())
    base = rc.load_config(BASE_CFG)
    cfg = rc.load_config(PILOT_CFG)
    check("기본 설정: 명령 보호 없음 · 파일럿 시나리오 없음 · 진행 그룹 r1_pilot·r2_pilot",
          not base["safety"].get("teleop_guard") and "R2-O-REOPEN" not in base["scenarios"] and rc.program_groups(base) == ["r1_pilot", "r2_pilot"])
    check("파일럿 설정: extends 기본 sha 기록 · 기존 safety 키 그대로 (pan 95 · 리더−팔로워 25 · 한계 10)",
          cfg["_extends_sha256"] == hashlib.sha256(open(BASE_CFG, "rb").read()).hexdigest()
          and (cfg["safety"]["pan_abs_block_deg"], cfg["safety"]["leader_follower_diff_block_deg"], cfg["safety"]["pan_limit_margin_block_deg"])
          == (base["safety"]["pan_abs_block_deg"], base["safety"]["leader_follower_diff_block_deg"], base["safety"]["pan_limit_margin_block_deg"]))
    check("파일럿 그룹만 (r2_pilot 40 · r1_pilot 없음)", set(cfg["groups"]) == {"pilot12_r1", "pilot12_r2p", "pilot12_r2o"})
    check("R2-P-AHEAD = R2-AHEAD 복사 + 그리퍼 열림", cfg["scenarios"]["R2-P-AHEAD"]["wrist_start_region"] == base["scenarios"]["R2-AHEAD"]["wrist_start_region"]
          and cfg["scenarios"]["R2-P-AHEAD"]["gripper_start"] == "open")
    plans = {g: rc.make_plan(cfg, g) for g in rc.program_groups(cfg)}
    check("계획 R1 4 · R2-P 4 · R2-O 4 (합 12)", [len(v) for v in plans.values()] == [4, 4, 4])
    r1 = plans["pilot12_r1"]
    check("R1 복구 방향 좌우 2/2", sorted(r["pan_error_direction"] for r in r1) == ["left", "left", "right", "right"])
    check("R1 지나침 20·25° · 계획 |pan| ≤ 92 · K7/K8 안 씀",
          {abs(float(r["pan_offset_deg"])) for r in r1} <= {20.0, 25.0} and max(abs(float(r["pan_target_deg"])) for r in r1) <= 92
          and not {r["position"] for r in r1} & {"K7", "K8"}, str([(r["position"], r["pan_target_deg"]) for r in r1]))
    check("R2-P = AHEAD 2 · DEPTH 2", sorted(r["scenario_id"] for r in plans["pilot12_r2p"]) == ["R2-P-AHEAD", "R2-P-AHEAD", "R2-P-DEPTH", "R2-P-DEPTH"])
    check("계획 재현 (같은 seed → 같은 계획)", rc.make_plan(cfg, "pilot12_r2o") == plans["pilot12_r2o"])
    prog = rc.program_progress(cfg)
    check("진행률 12편 (계획 없을 때 scenario_counts 기준)", sum(t for *_, t in prog) == 12, str(prog))
    # 시작 조건
    d = rc.describe_row(cfg, plans["pilot12_r2o"][0])
    vis_ahead = {"wrist": {"detected": True, "dx": -0.3, "dy": 0.0, "area_px": 9000, "touches_edge": False},
                 "front": {"detected": True, "dist_planned_cm": 1.0, "xy_cm": [0, 0]}}
    st = {"shoulder_pan.pos": -2.0, "shoulder_lift.pos": 15.0, "elbow_flex.pos": 10.0, "wrist_flex.pos": 70.0, "wrist_roll.pos": 0.0, "gripper.pos": 1.0}
    ps = rc.pilot_start_checks(cfg, d, st, vis_ahead)
    check("R2-O 시작: 그리퍼 닫힘 ✓ · 손목 v 0.50 = 닫기 영역 위 · 실패 상태 비슷함 3/3",
          ps["values"]["gripper_state"] == "closed" and ps["values"]["wrist_relation"] == "ahead"
          and (ps["similarity"]["matched"], ps["similarity"]["total"]) == (3, 3), str(ps["similarity"]))
    ps2 = rc.pilot_start_checks(cfg, d, {**st, "gripper.pos": 30.0}, vis_ahead)
    check("R2-O 에 그리퍼 열림 → ◇ (막지 않음, 비슷함 2/3)",
          any(k == "gripper" and ok is False for ok, k, _ in ps2["items"]) and ps2["similarity"]["matched"] == 2)
    r1row = rc.describe_row(cfg, r1[0])
    ref = rc.pan_ref(cfg, r1row["position"])
    over = ref + float(r1[0]["pan_offset_deg"])
    st1 = {**st, "shoulder_pan.pos": over, "shoulder_lift.pos": -102.0, "elbow_flex.pos": 95.0}
    vis_r1 = {"wrist": {"detected": False}, "front": {"detected": True, "dist_planned_cm": 1.0, "xy_cm": [0, 0]}}
    p1 = rc.pilot_start_checks(cfg, r1row, st1, vis_r1)
    want = "right(+)" if float(r1[0]["pan_offset_deg"]) < 0 else "left(-)"
    check("R1 시작: 팔 접힘 · 지나침 · 필요한 복구 방향 · 비슷함 4/4",
          p1["values"]["pan_side"] == "over" and p1["values"]["needed_recovery_dir"] == want and p1["similarity"]["matched"] == 4,
          f"{p1['values'].get('pan_error_deg')} {p1['values'].get('needed_recovery_dir')} {p1['similarity']['matched']}/{p1['similarity']['total']}")
    # 동시 명령 프로세스
    fake = os.path.join(ROOT, "bin", "lerobot-record")
    os.makedirs(os.path.dirname(fake), exist_ok=True)
    with open(fake, "w") as f:
        f.write("#!/bin/sh\nsleep 30\n")
    os.chmod(fake, 0o755)
    pr = subprocess.Popen([fake])
    time.sleep(0.3)
    try:
        conf = rc.robot_conflicts()
        check("다른 lerobot-record 프로세스 찾음 (동시 명령 방지)", any(c["pid"] == pr.pid for c in conf), str([c["cmd"][:40] for c in conf]))
    finally:
        pr.kill()
        pr.wait()
    ed = subprocess.Popen(["less", "-f", "/dev/null"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) \
        if os.path.exists("/usr/bin/less") else None
    conf = rc.robot_conflicts()
    check("프로세스 찾기: 테스트 뒤 남은 것 없음 (pid 정리)", not any(c["pid"] == pr.pid for c in conf))
    if ed:
        ed.kill()
    # 닫힘 세기 · 코드 버전
    g = np.r_[np.full(10, 1.0), np.linspace(1, 32, 15), np.full(20, 32), np.linspace(32, 8, 10), np.full(10, 8)]
    check("닫힘 세기: 한 번", len(rc.close_events(g)) == 1)
    check("닫힘 세기: 열기 없음 = 0 (닫힌 그리퍼만)", rc.close_events(np.full(30, 1.0)) == [])
    cv = rc.code_version()
    check("코드 버전 = git HEAD", len(cv.split("+")[0]) == 12, cv)
    # 파일럿 QA 규칙 (가짜 열)
    import r12_qa

    n = 90
    S = np.tile([-2.0, 15.0, 10.0, 70.0, 0.0, 1.0], (n, 1))
    A = S.copy()
    A[:, 5] = np.r_[np.full(10, 1.0), np.linspace(1, 32, 15), np.full(35, 32), np.linspace(32, 6, 10), np.full(20, 6)]
    S[25:60, 1] = np.linspace(15, 22, 35)
    S[:, 5] = np.maximum(A[:, 5], np.r_[np.zeros(60), np.full(30, 12.0)])  # 팔로워 그리퍼: 큐브에서 멈춤 (바닥 12 = 쥠)
    q = r12_qa._pilot_one(cfg, plans["pilot12_r2o"][0], S, A, 30, vis_ahead, None, {"first_grasp_success": True, "final_success": True}, True)
    check("QA R2-O: 먼저 열고 (팔 이동 0) 최대 32 ≥ 25 → Q4 ok · 닫힘 1번 → Q5 ok", q["q4"] == "ok" and q["q5"] == "ok", q["q4_detail"])
    A2 = A.copy()
    A2[:, 5] = np.r_[np.full(10, 1.0), np.linspace(1, 20, 15), np.full(35, 20), np.linspace(20, 6, 10), np.full(20, 6)]
    q2 = r12_qa._pilot_one(cfg, plans["pilot12_r2o"][0], S, A2, 30, vis_ahead, None, {"first_grasp_success": True, "final_success": True}, True)
    check("QA R2-O: 20 까지만 엶 → Q4 check", q2["q4"] == "check", q2["q4_detail"])
    rP = plans["pilot12_r2p"][0]
    SP = S.copy()
    AP = SP.copy()
    AP[:, 5] = np.r_[np.full(60, 30.0), np.linspace(30, 6, 10), np.full(20, 6)]
    SP[:, 5] = np.maximum(AP[:, 5], 12.0)
    qP = r12_qa._pilot_one(cfg, rP, SP, AP, 30, vis_ahead, None, {"first_grasp_success": True, "final_success": True}, True)
    check("QA R2-P: 닫기 전까지 열림 → Q3 ok", qP["q3"] == "ok", qP["q3_detail"])
    SR = np.tile([over, -102.0, 95.0, 60.0, 0.0, 1.0], (n, 1))
    SR[10:50, 0] = np.linspace(over, ref + 1.0, 40)
    SR[50:, 0] = ref + 1.0
    AR = SR.copy()
    AR[:, 5] = np.r_[np.full(55, 1.0), np.linspace(1, 30, 10), np.full(10, 30), np.linspace(30, 6, 10), np.full(5, 6)]
    SR[:, 5] = np.r_[AR[:75, 5], np.maximum(AR[75:, 5], 12.0)]
    qR = r12_qa._pilot_one(cfg, r1[0], SR, AR, 30, vis_r1, None, {"first_grasp_success": True, "final_success": True}, True)
    check("QA R1: 필요한 방향으로 Pan 수정 → Q2 ok", qR["q2"] == "ok", qR["q2_detail"])
    SR2 = SR.copy()
    SR2[10:50, 0] = np.linspace(over, over + (over - ref) * 0.3, 40)
    SR2[50:, 0] = SR2[49, 0]
    qR2 = r12_qa._pilot_one(cfg, r1[0], SR2, AR, 30, vis_r1, None, {"first_grasp_success": True, "final_success": True}, True)
    check("QA R1: 반대 방향 (더 지나침) → Q2 check", qR2["q2"] == "check", qR2["q2_detail"])


# ================================================================ B. 실제 record() + 진입점 + 명령 보호
class FollowRobot(T.StubRobot):
    """보낸 명령을 다음 관측에서 따라가는 가짜 팔로워 (blocked 이면 팔 관절이 안 움직임)."""

    def __init__(self):
        super().__init__()
        self.pose = dict(T.SAFE)
        self.leader = dict(T.SAFE)
        self.blocked = False

    def send_action(self, a):
        self.sent.append(dict(a))
        for k, v in a.items():
            if k in self.pose and (not self.blocked or k == "gripper.pos"):
                self.pose[k] = float(v)
        return a


class Leader(T.StubTeleop):
    def get_action(self):
        return dict(self.robot.leader)


def run_with(lr, entry, argv, script):
    robot = FollowRobot()
    events = {"exit_early": False, "rerecord_episode": False, "stop_recording": False}
    import queue
    import threading

    q = queue.Queue()
    orig_emit = entry.emit

    def emit(**ev):
        q.put(ev)
        orig_emit(**ev)

    entry.emit = emit
    lr.make_robot_from_config = lambda cfg: robot
    lr.make_teleoperator_from_config = lambda cfg: Leader(robot)
    lr.init_keyboard_listener = lambda: (None, events)
    if not isinstance(lr.Teleoperator, tuple):
        lr.Teleoperator = (lr.Teleoperator, Leader)
    elif Leader not in lr.Teleoperator:
        lr.Teleoperator = lr.Teleoperator + (Leader,)
    orig_connect = T.StubRobot.connect

    def guarded_connect(self, calibrate=True):
        assert isinstance(self, T.StubRobot), f"가짜가 아닌 로봇: {type(self)}"
        orig_connect(self)

    FollowRobot.connect = guarded_connect
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


def part_b():
    print("B. 실제 lerobot record() + 진입점 + 명령 보호 (가짜 장치)")
    T.block_hardware()
    import lerobot.scripts.lerobot_record as lr
    import r12_record_entry as entry

    check("진입점이 파일럿 설정을 읽음 · 명령 보호 켬", entry.GUARD_CFG.get("enabled") is True and entry.CFG["_path"] == PILOT_CFG)
    entry.install(lr)
    res = {}
    base = [a.replace("r12_stub_test", "r12_pilot_test") for a in [
        "--robot.type=so101_follower", "--robot.port=/nonexistent/so101_follower", "--robot.id=r12_stub_test",
        '--robot.cameras={ front: {type: opencv, index_or_path: /nonexistent/cam_front, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, '
        'wrist: {type: opencv, index_or_path: /nonexistent/cam_wrist, width: 640, height: 480, fps: 30, fourcc: "MJPG"} }',
        "--teleop.type=so101_leader", "--teleop.port=/nonexistent/so101_leader", "--teleop.id=r12_stub_test",
        "--dataset.single_task=pick up the red cube and put it in the brown box", "--dataset.episode_time_s=20",
        "--dataset.reset_time_s=3600", "--dataset.push_to_hub=false", "--dataset.no_stamp=true", "--play_sounds=false", "--display_data=true"]]
    E = T.expect

    def step_leader(robot, key, target, step=3.0, dt=0.05):
        while abs(robot.leader[key] - target) > step:
            robot.leader[key] += step if target > robot.leader[key] else -step
            time.sleep(dt)
        robot.leader[key] = target
        time.sleep(0.3)

    # ---- 시험 1
    ds1 = os.path.join(ROOT, "ds_guard")

    def script1(ev, q, robot):
        res["guard_on"] = E(q, "guard_on", timeout=30)
        E(q, "setup_start", ep=0)
        time.sleep(0.4)
        T.press(ev, "right")
        res["armed0"] = E(q, "armed", ep=0)
        res["rec_start0"] = E(q, "rec_start", ep=0)
        res["frames0"] = E(q, "start_frames", ep=0)
        time.sleep(0.5)
        res["guard_jump"] = None
        step_leader(robot, "shoulder_pan.pos", 100.0, step=2.0, dt=0.034)  # 리더 Pan 을 천천히 100° 까지 (한계 밖 명령) — 팔로워가 따라감
        res["guard_pan"] = E(q, "guard", reason="pan_cmd_limit")
        res["rec_end_inv"] = E(q, "rec_end", ep=0)
        res["sent_pan_max"] = max(abs(s.get("shoulder_pan.pos", 0)) for s in robot.sent)
        res["setup_after_inv"] = E(q, "setup_start", ep=1)
        # 결과 단계: 리더를 SAFE 로 갑자기 되돌림 → 리더−팔로워 ~97° → 팔로워 고정 (준비 단계라 무효 아님)
        robot.leader = dict(T.SAFE)
        res["guard_hold"] = E(q, "guard", reason="leader_follower_gap")
        time.sleep(0.4)
        res["pose_during_hold"] = robot.pose["shoulder_pan.pos"]
        step_leader(robot, "shoulder_pan.pos", 95.0)  # 리더를 팔로워 (95) 쪽으로 맞춤 → 풀림
        res["release"] = E(q, "guard_release", timeout=10)
        step_leader(robot, "shoulder_pan.pos", T.SAFE["shoulder_pan.pos"])  # 천천히 되돌림 (팔로워가 따라감)
        T.press(ev, "right")  # 결과 단계 → = 버리기 (무효) → 준비
        res["reset_end"] = E(q, "reset_end")
        E(q, "setup_start", ep=0, after_episode=False)
        time.sleep(0.4)
        T.press(ev, "right")
        res["armed0b"] = E(q, "armed", ep=0)
        E(q, "rec_start", ep=0)
        step_leader(robot, "shoulder_lift.pos", T.SAFE["shoulder_lift.pos"] + 12.0, step=1.0, dt=0.033)  # 정상 시연 (천천히)
        time.sleep(0.5)
        T.press(ev, "right")
        res["rec_end_ok"] = E(q, "rec_end", ep=0)

    run_with(lr, entry, base + [f"--dataset.root={ds1}", "--dataset.repo_id=test/r12_pilot_guard", "--dataset.num_episodes=1"], script1)
    check("guard_on 사건 (파일럿 설정)", bool(res.get("guard_on")))
    fr = res["frames0"]["files"]
    ok_png = all(os.path.exists(p) for p in fr.values())
    if ok_png:
        import cv2

        im = cv2.imread(fr["front"])
        ok_png = im is not None and im.shape == (480, 640, 3)
    check("녹화 첫 프레임 front · wrist PNG 저장 (480×640)", ok_png and set(fr) == {"front", "wrist"}, str(list(fr.values())))
    check("녹화 중 리더 Pan 100° (천천히) → 팔로워에는 최대 95°", res["sent_pan_max"] <= 95.0 + 1e-6, f"{res['sent_pan_max']}")
    check("녹화 중 보호 → 무효 (invalid) · rec_end guard_invalid · 결과 단계에서 버리기 예약",
          res["guard_pan"]["invalid"] is True and res["rec_end_inv"].get("guard_invalid") == "pan_cmd_limit"
          and res["setup_after_inv"].get("discard_pending") is True)
    check("준비 단계 리더−팔로워 ~97° → 팔로워 고정 (무효 아님 · 점프 없음)",
          res["guard_hold"]["invalid"] is False and abs(res["pose_during_hold"] - 95.0) < 1e-6, f"pan {res['pose_during_hold']}")
    check("리더를 팔로워 자세로 맞추면 고정 풀림", bool(res.get("release")))
    check("무효 판 버린 뒤 같은 번호 다시 녹화", res["reset_end"].get("discard_previous") is True and res["armed0b"]["ep"] == 0)
    info = json.load(open(os.path.join(ds1, "meta", "info.json")))
    import pandas as pd

    data = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(ds1, "data", "*", "*.parquet")))])
    S = np.stack(data["observation.state"].values)
    A = np.stack(data["action"].values)
    check("저장 1편 (무효 판 빠짐) · 판 길이 = rec_end 프레임", info["total_episodes"] == 1 and len(data) == res["rec_end_ok"]["frames"],
          f"{info['total_episodes']} · {len(data)} vs {res['rec_end_ok']['frames']}")
    steps = np.diff(A[:, 1])
    check("저장 판에 Pan > 95 없음 · action = 리더 값 그대로 (리더 Lift 1°씩 → 17.5…29.5, 보호가 기록 값을 바꾸지 않음)",
          float(np.abs(S[:, 0]).max()) < 95 and abs(A[0, 1] - 17.5) < 1e-4 and abs(A[:, 1].max() - 29.5) < 1e-4
          and bool(((steps >= -1e-6) & (steps <= 2.0 + 1e-6)).all()), f"lift action {A[0, 1]:.1f} → {A[:, 1].max():.1f}, 팔로워 지연 최대 {float(np.abs(A[:, 1] - S[:, 1]).max()):.1f}°")
    d2 = json.load(open(T.D2_INFO))
    keys = ("action", "observation.state", "observation.images.front", "observation.images.wrist", "timestamp", "frame_index",
            "episode_index", "index", "task_index")
    check("features · fps · robot_type · codebase_version = d2",
          all(json.dumps(info["features"][k], sort_keys=True) == json.dumps(d2["features"][k], sort_keys=True) for k in keys)
          and (info["fps"], info["robot_type"], info["codebase_version"]) == (d2["fps"], d2["robot_type"], d2["codebase_version"]))

    # ---- 시험 2: 녹화 중 팔로워가 막힘 (리더는 움직임) → 고정 + 무효 → 준비 중 Esc → 저장 0
    ds2 = os.path.join(ROOT, "ds_blocked")

    def script2(ev, q, robot):
        E(q, "setup_start", ep=0)
        time.sleep(0.3)
        T.press(ev, "right")
        E(q, "armed", ep=0)
        E(q, "rec_start", ep=0)
        time.sleep(0.3)
        robot.blocked = True
        n0 = len(robot.sent)
        step_leader(robot, "elbow_flex.pos", T.SAFE["elbow_flex.pos"] + 40.0, step=4.0, dt=0.033)
        res["guard_block"] = E(q, "guard", reason="leader_follower_gap")
        res["rec_end_block"] = E(q, "rec_end", ep=0)
        held = [s["elbow_flex.pos"] for s in robot.sent[n0:]]
        res["elbow_sent_max"] = max(held) if held else None
        E(q, "setup_start")
        time.sleep(0.3)
        T.press(ev, "esc")

    run_with(lr, entry, base + [f"--dataset.root={ds2}", "--dataset.repo_id=test/r12_pilot_blocked", "--dataset.num_episodes=1"], script2)
    check("녹화 중 막힌 팔로워 (리더−팔로워 > 25°) → 고정 + 무효", res["guard_block"]["invalid"] is True
          and res["rec_end_block"].get("guard_invalid") == "leader_follower_gap")
    check("고정 뒤 elbow 명령이 팔로워 자세 + 25° 를 넘지 않음 (밀기 멈춤)",
          res["elbow_sent_max"] is not None and res["elbow_sent_max"] <= T.SAFE["elbow_flex.pos"] + 25.0 + 1e-6, f"{res['elbow_sent_max']}")
    info2 = json.load(open(os.path.join(ds2, "meta", "info.json"))) if os.path.exists(os.path.join(ds2, "meta", "info.json")) else {"total_episodes": 0}
    check("무효 판은 저장되지 않음 (Esc 로 끝, 0편)", info2["total_episodes"] == 0)

    # ---- 기본 설정 (보호 꺼짐) 은 별도 프로세스에서 확인
    r = subprocess.run([sys.executable, "-c", "import os,sys; os.environ.pop('R12_CONFIG',None); os.environ['R12_LIVE_DIR']='/tmp'; "
                        f"sys.path.insert(0,{TOOLS!r}); import r12_record_entry as e; print(bool(e.GUARD_CFG.get('enabled')))"],
                       capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "R12_CONFIG"})
    check("기본 설정 (기존 r1/r2 세션) 에서는 명령 보호 꺼짐 — 기존 동작 그대로", r.stdout.strip() == "False", r.stdout.strip() + r.stderr[-200:])


def main():
    part_a()
    part_b()
    print(("PASS" if all(OK) else "FAIL") + f" {sum(OK)}/{len(OK)} · 임시 폴더 {ROOT}")
    return 0 if all(OK) else 1


if __name__ == "__main__":
    sys.exit(main())
