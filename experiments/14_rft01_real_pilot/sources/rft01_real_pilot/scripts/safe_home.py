#!/usr/bin/env python3
"""시행이 끝난 뒤 팔을 시작 자세로 옮기기 · 토크 끄기 — **사용자가 직접, 명시적으로** 실행하는 도구 (rft01 실물 파일럿 v2, 2026-11-05).

※ 실물 팔에 Goal 을 쓴다 (이동). Claude 는 이 명령을 실물에서 실행하지 않는다.

eval 경로 (end_hold) 는 종료 때 자동 복귀하지 않고, 팔을 멈춘 자리에서 토크를 켠 채로 둔다. 이 도구는 그 다음 단계다.
  사용:  python3 ~/so101_runs/main_k8/rft01_real_pilot/scripts/safe_home.py --run <run 폴더>           # 점검 → 'home' 입력 시 이동 → (선택) 토크 끄기
         … --run <run 폴더> --check                                                                    # 팔 연결 없이 end_state.json 만 보고 계획 출력
         … --run <run 폴더> --mode release                                                            # 이동 없이 지금 자리에서 토크 끄기 (팔을 손으로 받친 뒤)
  ~/so101-env/bin/python 이 아니면 그 python 으로 다시 실행한다 (lerobot 필요).

연결 방식: lerobot SOFollower.connect() 를 **쓰지 않는다** — connect → configure() 가 설정 중 토크를 끄기 때문 (팔이 내려옴).
  SOFollower 객체는 만들되 (캘리브레이션 파일 my_arm 로드, 하드웨어 접근 없음) bus.connect() (포트 열기 + ping · 펌웨어 읽기) 만 한다.
  캘리브레이션 불일치면 쓰지 않고 멈춘다.

이동 전 점검 (하나라도 실패하면 이동하지 않음, 토크 유지 그대로 종료):
  H1 다른 lerobot · eval_ui 프로세스 없음          H2 6 관절 모두 Torque_Enable = 1 (꺼져 있으면 이미 힘이 빠진 상태 — 손으로 옮긴다)
  H3 팔 |Goal − Present| ≤ 4° (밀리거나 걸린 상태 아님)   H4 |pan| ≤ 100°, 모든 관절 캘리브레이션 범위 안
  H5 목표 = end_state.json 의 시작 자세 (eval 연결 순간 자세) 이고 접은 쉬는 자세 (lift ≤ −85 · elbow ≥ 80)
  H6 지금 자세가 end_state.json 끝 자세와 5° 안 (그 사이 누가 옮기지 않음 · 맞는 run)   H7 관절별 이동량 ≤ 210° (11-05: 140 → 210, 캘리브레이션 범위 안의 모든 복귀 허용)
이동: 팔 5 관절 직선 보간 (관절 공간), 가장 많이 움직이는 관절 기준 SPEED (기본 15°/s), 30 Hz. 그리퍼는 쓰지 않는다.
  틱마다 Present 확인: 어느 관절이든 |Goal − Present| > 12° 가 10 틱 연속 (추종 실패 · 충돌 의심) · |pan| > 105 · 읽기 오류 → 즉시 Goal := Present, 멈춤.
  Ctrl+C → Goal := Present, 멈춤.
--auto (run_series.sh): 점검이 모두 PASS 일 때만 입력 없이 이동, 토크 유지, 도착 못 하면 종료 코드 3.
토크 끄기: 도착 (5 관절 모두 목표 3° 안) 후, 목표가 접은 자세이면 'release' 를 입력했을 때만. 그 밖에는 토크 유지.
기록: results/home_logs/<run>_<시각>.json (점검 · 선택 · 이동 요약 · 끝 상태)
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

VENV_PY = Path.home() / "so101-env/bin/python"
if Path(sys.prefix).resolve() != VENV_PY.parent.parent.resolve() and os.environ.get("SAFE_HOME_NO_REEXEC") != "1":  # venv python 은 /usr/bin/python3.12 로의 링크 → prefix 로 판별
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])

S_DIR = Path(__file__).resolve().parents[1]
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
ALL = ARM + ["gripper"]
PORT = "/dev/so101_follower"
SPEED = 15.0
FPS = 30
TRACK_ERR, TRACK_TICKS = 12.0, 10
ARRIVE_TOL, SETTLE_S = 3.0, 3.0
MAX_MOVE = 210.0


def checks(pres, goal, torque, limits, end_state, target):
    """순수 함수 (시험과 같은 코드). 반환 [(이름, 통과, 설명)]."""
    out = []
    out.append(("H2_torque_on", all(int(torque.get(j, 0)) == 1 for j in ALL), f"Torque_Enable={ {j: torque.get(j) for j in ALL} }"))
    gap = {j: round(abs(goal[j] - pres[j]), 2) for j in ARM}
    out.append(("H3_goal_present_gap", max(gap.values()) <= 4.0, f"|Goal−Present|={gap}"))
    lim_bad = [j for j in ALL if limits and j in limits and not (limits[j][0] - 1 <= pres[j] <= limits[j][1] + 1)]
    out.append(("H4_pan_and_limits", abs(pres["shoulder_pan"]) <= 100.0 and not lim_bad, f"pan={pres['shoulder_pan']:.1f} outside_limits={lim_bad}"))
    rest = target is not None and target["shoulder_lift"] <= -85 and target["elbow_flex"] >= 80
    out.append(("H5_target_is_rest", bool(rest), f"target={target}"))
    endp = (end_state or {}).get("end_present_arm") or {}
    dd = {j: round(abs(pres[j] - endp[j]), 2) for j in ARM if j in endp}
    out.append(("H6_matches_end_state", bool(dd) and max(dd.values()) <= 5.0, f"|지금 − end_state 끝 자세|={dd}"))
    mv = {j: round(abs(target[j] - pres[j]), 1) for j in ARM} if target else {}
    out.append(("H7_move_size", bool(mv) and max(mv.values()) <= MAX_MOVE, f"이동량={mv}"))
    return out


def move(bus, start, target, sleep=time.sleep, now=time.perf_counter, speed=SPEED, fps=FPS, interrupt=None):
    """직선 보간 이동. 반환 dict (ok, reason, ticks, max_err, writes)."""
    dist = max(abs(target[j] - start[j]) for j in ARM)
    n = max(1, int(round(dist / speed * fps)))
    R = {"ok": False, "reason": None, "ticks": 0, "max_err": 0.0, "n_steps": n, "duration_planned_s": n / fps, "max_step_deg": 0.0}
    bad = {j: 0 for j in ARM}
    prev = dict(start)
    try:
        for k in range(1, n + 1 + int(SETTLE_S * fps)):
            t = min(1.0, k / n)
            g = {j: start[j] + (target[j] - start[j]) * t for j in ARM}
            R["max_step_deg"] = max(R["max_step_deg"], max(abs(g[j] - prev[j]) for j in ARM))
            prev = g
            bus.sync_write("Goal_Position", g)
            R["ticks"] = k
            sleep(1 / fps)
            if interrupt is not None and interrupt(k):
                raise KeyboardInterrupt
            p = bus.sync_read("Present_Position")
            if abs(p["shoulder_pan"]) > 105:
                return _halt(bus, R, "pan_over_105")
            for j in ARM:
                e = abs(g[j] - p[j])
                R["max_err"] = max(R["max_err"], e)
                bad[j] = bad[j] + 1 if e > TRACK_ERR else 0
                if bad[j] >= TRACK_TICKS:
                    return _halt(bus, R, f"tracking_{j}_err{e:.1f}")
            if t >= 1.0 and max(abs(target[j] - p[j]) for j in ARM) <= ARRIVE_TOL:
                R["ok"], R["reason"] = True, "arrived"
                R["final"] = {j: float(p[j]) for j in ARM}
                return R
        return _halt(bus, R, "not_arrived_after_settle")
    except KeyboardInterrupt:
        return _halt(bus, R, "ctrl_c")
    except Exception as e:  # 읽기 · 쓰기 오류
        return _halt(bus, R, f"io_error {type(e).__name__}: {e}")


def _halt(bus, R, reason):
    R["reason"] = reason
    try:
        p = bus.sync_read("Present_Position")
        bus.sync_write("Goal_Position", {j: float(p[j]) for j in ARM})
        R["final"] = {j: float(p[j]) for j in ARM}
        R["halt_hold"] = True
    except Exception as e:
        R["halt_hold"] = False
        R["halt_error"] = str(e)[:200]
    return R


def ask(prompt, inp=input):
    try:
        return inp(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def session(bus, end_state, mode, inp=input, sleep=time.sleep, interrupt=None, limits=None, others=""):
    """연결된 bus 로 한 번의 세션. 반환 기록 dict. 시험에서 가짜 bus 로 그대로 부른다."""
    L = {"mode": mode, "checks": [], "choice": None, "move": None, "released": False}
    target = {j: float(end_state["initial_position"][f"{j}.pos"]) for j in ARM} if end_state.get("initial_position") else None
    pres = bus.sync_read("Present_Position")
    goal = bus.sync_read("Goal_Position")
    torque = bus.sync_read("Torque_Enable", normalize=False)
    L["present"] = {j: round(float(pres[j]), 2) for j in ALL}
    print("\n  관절           지금     목표(시작 자세)   차이")
    for j in ARM:
        tj = target[j] if target else float("nan")
        print(f"  {j:<13} {pres[j]:8.1f}   {tj:8.1f}        {tj - pres[j]:+7.1f}")
    print(f"  gripper       {pres['gripper']:8.1f}   (쓰지 않음)")
    if mode == "release":
        near = target is not None and max(abs(pres[j] - target[j]) for j in ARM) <= 5.0
        print("\n  ⚠ 토크를 끄면 팔이 자기 무게로 내려옵니다." + ("" if near else " 지금은 접은 자세가 아닙니다 — 팔을 손으로 받치세요."))
        a = ask("  지금 자리에서 토크를 끄려면 'release' 입력 (그 밖 = 토크 유지): ", inp)
        L["choice"] = a
        if a == "release" and (near or ask("  팔을 손으로 받쳤으면 '받쳤음' 입력: ", inp) == "받쳤음"):
            bus.disable_torque()
            L["released"] = True
        return L
    C = [("H1_no_other_process", not others, others or "없음")] + checks(pres, goal, torque, limits, end_state, target)
    L["checks"] = [{"name": n, "pass": ok, "detail": d} for n, ok, d in C]
    print("\n  점검:")
    for n, ok, d in C:
        print(f"   {'PASS' if ok else 'FAIL'} {n}  {d[:150]}")
    if not all(ok for _, ok, _ in C):
        print("\n⛔ 점검 실패 — 이동하지 않았어요. 팔은 지금 자리에서 토크 유지. (필요하면 팔을 받치고 --mode release 또는 전원 차단)")
        L["choice"] = "refused_checks"
        return L
    dist = max(abs(target[j] - pres[j]) for j in ARM)
    print(f"\n  이동: 관절 공간 직선, 최대 {dist:.0f}° · {SPEED:.0f}°/s → 약 {dist / SPEED:.1f} s. 그리퍼 그대로.")
    print("  경로 (상자 · 카메라 · 손 · 케이블) 가 비었는지 확인하세요. 멈추려면 Ctrl+C (그 자리 유지), 급하면 전원 차단.")
    a = ask("  시작 자세로 옮기려면 'home' 입력 (그 밖 = 이동 안 함): ", inp)
    L["choice"] = a
    if a != "home":
        print("이동하지 않았어요. 토크 유지.")
        return L
    R = move(bus, {j: float(pres[j]) for j in ARM}, target, sleep=sleep, interrupt=interrupt)
    L["move"] = R
    print(f"\n  이동 결과: {R['reason']} · {R['ticks']} 틱 · 추종 오차 최대 {R['max_err']:.1f}° · 틱당 최대 {R['max_step_deg']:.2f}°")
    if not R["ok"]:
        print("⛔ 도중에 멈췄어요 (그 자리 유지, 토크 켬). 원인 확인 뒤 다시 실행하거나 팔을 받치고 --mode release.")
        return L
    print("\n  도착. 토크를 끄면 팔이 접은 자세에서 조금 내려앉을 수 있습니다 (다음 시행은 연결 때 어차피 토크를 잠깐 끕니다).")
    b = ask("  토크를 끄려면 'release' 입력 (Enter = 토크 켠 채 종료): ", inp)
    L["release_choice"] = b
    if b == "release":
        bus.disable_torque()
        L["released"] = True
    return L


def auto_inp(p):
    """--auto: 이동 질문에만 'home', 그 밖 (토크 끄기 등) 은 빈 입력 = 토크 유지."""
    v = "home" if "'home'" in p else ""
    print(p + v + "   (자동)")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mode", choices=["home", "release"], default="home")
    ap.add_argument("--check", action="store_true", help="팔 연결 없이 계획만")
    ap.add_argument("--auto", action="store_true", help="run_series.sh 용: 점검 H1–H7 모두 PASS 면 'home' 입력 없이 이동, 토크는 켠 채 종료")
    a = ap.parse_args()
    run = Path(a.run).resolve()
    es_p = run / "end_state.json"
    if not es_p.exists():
        raise SystemExit(f"⛔ {es_p} 없음 — end_hold 가 기록하지 못한 run (팔 상태 모름). 팔을 받치고 전원으로 정지하거나 직접 확인하세요.")
    es = json.loads(es_p.read_text())
    print(f"── safe_home · run {run.name} · 끝난 이유 {es.get('ended_by')} · 시작 자세와 최대 {es.get('max_abs_diff_deg')}° · 토크 {es.get('torque_left_on')}")
    if a.check:
        print(json.dumps({k: es.get(k) for k in ("initial_position", "end_present_arm", "diff_from_initial_deg")}, ensure_ascii=False, indent=1))
        print("CHECK_ONLY (팔 연결 안 함)")
        return 0
    others = subprocess.run(["pgrep", "-af", "eval_ui.py|lerobot-(rollout|record|teleoperate)|hil_dagger|r12_collect"], capture_output=True,
                            text=True).stdout.strip()
    others = "\n".join(ln for ln in others.splitlines() if "safe_home" not in ln)
    from lerobot.robots.so_follower.config_so_follower import SOFollowerRobotConfig
    from lerobot.robots.so_follower.so_follower import SOFollower
    robot = SOFollower(SOFollowerRobotConfig(port=PORT, id="my_arm"))  # 하드웨어 접근 없음 (캘리브레이션 파일만 읽음)
    bus = robot.bus
    bus.connect()  # 포트 열기 + ping · 펌웨어 읽기 (쓰기 없음). configure() 는 부르지 않음
    rec = {"run": str(run), "time": datetime.datetime.now().isoformat(timespec="seconds"), "end_state": es}
    try:
        if not bus.is_calibrated:  # 읽기만
            print("⛔ 서보 캘리브레이션이 my_arm 파일과 다름 — 쓰지 않고 멈춤 (토크 상태 그대로)")
            rec["result"] = "calibration_mismatch"
            return 2
        cal = robot.calibration
        limits = None
        try:
            lo = bus._normalize({cal[j].id: cal[j].range_min for j in ALL})
            hi = bus._normalize({cal[j].id: cal[j].range_max for j in ALL})
            limits = {j: (min(lo[cal[j].id], hi[cal[j].id]), max(lo[cal[j].id], hi[cal[j].id])) for j in ALL}
        except Exception:
            limits = None
        rec["limits"] = limits
        inp = auto_inp if (a.auto and a.mode == "home") else input
        rec.update(session(bus, es, a.mode, inp=inp, limits=limits, others=others))
        rec["auto"] = bool(a.auto)
        if a.auto:
            return 0 if (rec.get("move") or {}).get("ok") else 3
        return 0
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)  # 토크는 위에서 명시적으로 끈 경우만 꺼짐
        d = S_DIR / "results/home_logs"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{run.name}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
        p.write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str))
        print(f"기록: {p}")


if __name__ == "__main__":
    sys.exit(main())
