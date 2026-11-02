"""SO-101 팔로워 모터 버스 읽기 전용 점검 (토크·설정을 쓰지 않음). 2026-10-19.

- 포트만 열고(handshake=False), 모터마다 ping 을 N 번 보내 응답이 빠지는 비율을 센다.
- 응답하는 모터는 전압·온도·Status(오류 비트)·Torque_Enable·현재 위치(raw)를 읽기만 한다.
- 끝날 때 토크를 건드리지 않고 포트만 닫는다 (disable_torque=False).

사용: ~/so101-env/bin/python motor_check.py [--port /dev/so101_follower] [--pings 50]
"""

import argparse
import time

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
# STS3215 Status 비트 (Feetech 문서): 0 전압, 1 센서(각도), 2 과열, 3 전류, 5 과부하
STATUS_BITS = {0: "voltage", 1: "angle-sensor", 2: "overheat", 3: "overcurrent", 5: "overload"}

ap = argparse.ArgumentParser()
ap.add_argument("--port", default="/dev/so101_follower")
ap.add_argument("--pings", type=int, default=50)
args = ap.parse_args()

motors = {n: Motor(i + 1, "sts3215", MotorNormMode.RANGE_M100_100) for i, n in enumerate(NAMES)}
bus = FeetechMotorsBus(port=args.port, motors=motors)
bus.connect(handshake=False)  # 포트만 연다 — 모터에 쓰지 않음
try:
    print(f"port {args.port}, {args.pings} pings per motor (읽기만 함)\n")
    print(f"{'id':>2} {'motor':14s} {'ping ok':>9} {'volt V':>7} {'temp C':>7} {'status':>7} {'torque':>6} {'pos raw':>8}  note")
    for n in NAMES:
        mid = motors[n].id
        ok = 0
        for _ in range(args.pings):
            if bus.ping(n, num_retry=0) is not None:
                ok += 1
            time.sleep(0.005)
        vals = {}
        for reg in ("Present_Voltage", "Present_Temperature", "Status", "Torque_Enable", "Present_Position"):
            try:
                vals[reg] = bus.read(reg, n, normalize=False, num_retry=2)
            except Exception as e:  # noqa: BLE001
                vals[reg] = None
        st = vals["Status"]
        flags = [name for b, name in STATUS_BITS.items() if st is not None and (int(st) >> b) & 1]
        fmt = lambda v, s=1.0: "—" if v is None else f"{v * s:.1f}" if s != 1.0 else str(v)
        print(f"{mid:>2} {n:14s} {ok:>4}/{args.pings:<4} {fmt(vals['Present_Voltage'], 0.1):>7} {fmt(vals['Present_Temperature']):>7} "
              f"{fmt(st):>7} {fmt(vals['Torque_Enable']):>6} {fmt(vals['Present_Position']):>8}  {', '.join(flags)}")
finally:
    bus.disconnect(disable_torque=False)  # 포트만 닫음
