#!/home/user/so101-env/bin/python
"""팔로워 (또는 리더) 모터 버스 읽기 전용 점검 — 토크를 켜지 않고 팔을 움직이지 않는다.

모터마다 ping 을 여러 번 보내 응답률을 재고, Present_Position · Present_Voltage · Present_Temperature · Present_Load · Status (오류 비트) ·
Torque_Enable 을 읽는다. 버스의 쓰기 함수 (write · sync_write · _write · enable/disable_torque) 는 실행 전에 막아 둔다.
포트만 열고 (handshake 없음) 끝낼 때도 토크 끄기 쓰기 없이 닫는다. 다른 로봇 프로그램이 포트를 쓰고 있으면 실행하지 않는다.

  ~/so101-env/bin/python tools/r12_bus_check.py [--arm follower|leader] [--pings 20]
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r12_common as rc  # noqa: E402

PORTS = {"follower": ("/dev/so101_follower", "robots/so_follower/my_arm.json"),
         "leader": ("/dev/so101_leader", "teleoperators/so_leader/my_leader.json")}
STATUS_BITS = {0: "전압", 1: "센서", 2: "온도", 3: "전류", 4: "각도", 5: "과부하"}  # Feetech STS 상태 비트 (참고)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="follower", choices=list(PORTS))
    ap.add_argument("--pings", type=int, default=20)
    a = ap.parse_args()
    port, calp = PORTS[a.arm]
    conf = [c for c in rc.robot_conflicts() if port in c["devices"] or c["name"]]
    if conf:
        print("다른 로봇 프로그램이 실행 중이라 점검하지 않았어요:", *[f"pid {c['pid']} {c['cmd'][:80]}" for c in conf], sep="\n  ")
        return 2
    from lerobot.motors import Motor, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    cal = json.load(open(os.path.expanduser(f"~/.cache/huggingface/lerobot/calibration/{calp}")))
    motors = {n: Motor(v["id"], "sts3215", MotorNormMode.DEGREES) for n, v in cal.items()}
    bus = FeetechMotorsBus(port=port, motors=motors)

    def no_write(*_a, **_k):
        raise RuntimeError("읽기 전용 점검: 쓰기 차단")

    for name in ("write", "sync_write", "_write", "enable_torque", "disable_torque"):
        setattr(bus, name, no_write)
    bus.connect(handshake=False)
    out = {}
    try:
        for n, m in motors.items():
            ok, t0 = 0, time.time()
            for _ in range(a.pings):
                if bus.ping(m.id) is not None:
                    ok += 1
            r = {"id": m.id, "ping_ok": f"{ok}/{a.pings}"}
            for reg in ("Present_Position", "Present_Voltage", "Present_Temperature", "Present_Load", "Status", "Torque_Enable"):
                try:
                    r[reg] = bus.read(reg, n, normalize=False)
                except Exception as e:  # 응답 없음 등
                    r[reg] = f"읽기 실패 ({type(e).__name__})"
            st = r.get("Status")
            if isinstance(st, int):
                r["status_bits"] = [STATUS_BITS.get(b, str(b)) for b in range(8) if st >> b & 1]
            if isinstance(r.get("Present_Voltage"), int):
                r["voltage_V"] = r["Present_Voltage"] / 10
            out[n] = r
    finally:
        bus.port_handler.closePort()  # disconnect(disable_torque=False) 와 같음 — 쓰기 없음
    print(f"{a.arm} {port} 읽기 전용 점검 ({time.strftime('%H:%M:%S')}) — 토크 · 위치 쓰기 없음")
    print(f"{'모터':12s} id  ping   전압V 온도°C  부하  상태비트  토크  위치(raw)")
    for n, r in out.items():
        print(f"{n:12s} {r['id']:>2}  {r['ping_ok']:>5}  {r.get('voltage_V', '-')!s:>5} {r.get('Present_Temperature')!s:>5} {r.get('Present_Load')!s:>5}  "
              f"{','.join(r.get('status_bits', [])) or ('없음' if isinstance(r.get('Status'), int) else r.get('Status'))!s:8s}  "
              f"{r.get('Torque_Enable')!s:>4}  {r.get('Present_Position')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
