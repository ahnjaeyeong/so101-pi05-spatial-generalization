#!/usr/bin/env python3
"""그리퍼만 쉬는 값 (3) 으로 닫는다 (사용자가 터미널에서 직접 실행). ※ 그리퍼가 움직인다. 팔 관절은 쓰지 않는다.

사용:  ~/so101_runs/main_k8/sgp01_real_eval/scripts/gripper_close.py
2026-11-13: 세션이 그리퍼를 연 채 끝난 뒤 다음 세션이 열린 채 시작한 일 → 닫는 도구. 토크는 건드리지 않음 (켜진 채 유지).
멈춤: 다른 평가 · 수집 프로세스가 돌고 있음 · 캘리브레이션 불일치 · 그리퍼 토크 꺼짐 · Ctrl+C (그 자리).
"""
import csv, datetime, os, subprocess, sys, time
from pathlib import Path

VENV_PY = Path.home() / "so101-env/bin/python"
if Path(sys.prefix).resolve() != VENV_PY.parent.parent.resolve():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
S = Path(__file__).resolve().parents[1]
PORT, REST, SPEED = "/dev/so101_follower", 3.0, 30.0


def main():
    others = subprocess.run(["pgrep", "-af", "eval_ui.py|lerobot-(rollout|record|teleoperate)|hil_dagger|r12_collect|safe_home"], capture_output=True, text=True).stdout.strip()
    if others:
        print("⛔ 팔을 쓰는 다른 프로세스가 있음 — 닫지 않음:\n" + others[:400]); return 2
    led = [r for r in csv.DictReader(open(S / "results/run_ledger.csv", newline="")) if r.get("run") not in ("", "none")]
    from lerobot.robots.so_follower.config_so_follower import SOFollowerRobotConfig
    from lerobot.robots.so_follower.so_follower import SOFollower
    robot = SOFollower(SOFollowerRobotConfig(port=PORT, id="my_arm"))
    bus = robot.bus
    bus.connect()  # 포트 열기 + ping (쓰기 없음). configure() 는 부르지 않음
    try:
        if not bus.is_calibrated:
            print("⛔ 서보 캘리브레이션이 my_arm 파일과 다름 — 쓰지 않음"); return 2
        g0 = float(bus.sync_read("Present_Position")["gripper"]); tq = bus.sync_read("Torque_Enable", normalize=False)["gripper"]
        print(f"그리퍼 지금 {g0:.1f} · 토크 {tq}")
        if int(tq) != 1:
            print("⛔ 그리퍼 토크가 꺼져 있음 — 쓰지 않음 (손으로 닫아도 됨)"); return 2
        if g0 > REST + 2:
            n = max(1, int((g0 - REST) / (SPEED / 30.0)))
            try:
                for k in range(1, n + 1):
                    bus.sync_write("Goal_Position", {"gripper": g0 + (REST - g0) * k / n}); time.sleep(1 / 30.0)
            except KeyboardInterrupt:
                p = float(bus.sync_read("Present_Position")["gripper"]); bus.sync_write("Goal_Position", {"gripper": p}); print(f"중단 — 그 자리 ({p:.1f})"); return 130
            time.sleep(0.5)
        g1 = float(bus.sync_read("Present_Position")["gripper"])
        print(f"그리퍼 {g0:.1f} → {g1:.1f}")
        if g1 > 10.0:
            print("⛔ 아직 열려 있음 (10 초과) — 사이에 뭔가 끼었는지 확인"); return 3
        if led:
            (S / f"results/gripper_closed_{led[-1]['run']}.txt").write_text(f"{datetime.datetime.now().isoformat(timespec='seconds')} gripper {g0:.1f} -> {g1:.1f}\n")
        print("닫힘 확인. 이제 run_series.sh 를 실행하세요."); return 0
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    sys.exit(main())
