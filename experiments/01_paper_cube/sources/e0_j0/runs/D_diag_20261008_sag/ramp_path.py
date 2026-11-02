"""휴식 자세 → 학습 시작 자세를 직접 명령했을 때 (드라이버 관절별 램프 0.5 rad/s · 5 rad/s²) TCP 높이."""
import math
from twin_kinematics import TcpForwardKinematics
from twin_e0j0.convert import lerobot_to_twin
from twin_e0j0.walls import CommandWalls
fk = TcpForwardKinematics(open('/ws/src/twin_description/urdf/so101_new_calib.urdf').read(), 'base_link', 'gripper_frame_link')
walls = CommandWalls('/ws/src/twin_bringup/config/sites/thor/calibration_so101_jetson.json', '/ws/src/twin_e0j0/config/physical_limits_thor_e0j0.yaml')
a = lerobot_to_twin([70.33, -30.29, 70.29, 51.25, 20.97, 0.69])
b = lerobot_to_twin([70.9, 15.8, 34.1, 74.3, 6.8, 0.6])
V, A, dt = 0.5, 5.0, 1 / 30
q, v = dict(a), {n: 0.0 for n in a}
zs, t = [], 0.0
for k in range(600):
    for n in fk.joint_names:
        err = b[n] - q[n]
        stop = v[n] ** 2 / (2 * A)
        want = math.copysign(V, err) if abs(err) > stop + 1e-6 else 0.0
        dv = max(-A * dt, min(A * dt, want - v[n])); v[n] += dv
        if abs(err) < abs(v[n]) * dt: q[n], v[n] = b[n], 0.0
        else: q[n] += v[n] * dt
    zs.append(fk.solve(q).position[2]); t += dt
    if all(abs(b[n] - q[n]) < 1e-6 for n in fk.joint_names): break
print('램프 경로: %.1f s, TCP z min %.4f max %.4f (출발 %.4f, 도착 %.4f), 벽 %s' % (t, min(zs), max(zs), zs[0], zs[-1], walls.reasons(b)))
