"""후보 점검 자세 C 검증: 관절 처짐, 휴식→C (램프) 와 C→시작 자세 (관절 직선) 경로 높이, practice_50 에서 가장 가까운 실제 자세."""
import math, sys
import numpy as np
sys.path.insert(0, '/ws/e0j0_runs/diag_20261008_sag')
import sag_model as sm  # noqa: E402
from twin_e0j0.convert import lerobot_to_twin
from twin_e0j0.motion import waypoints
C = [70.9, 25.0, 55.0, 95.0, 6.8, 0.6]
REST = [70.33, -30.29, 70.29, 51.25, 20.97, 0.69]
START = [70.9, 15.8, 34.1, 74.3, 6.8, 0.6]
arm = lambda lr: {n: v for n, v in lerobot_to_twin(lr).items() if n in sm.names}
for P, s in (('P16', 1.0), ('P32', 0.5)):
    d, e = sm.sag(arm(C), s)
    print('C %s: TCP 오차 %.1f mm, 관절 처짐 lift %.3f elbow %.3f wf %.3f rad' % (P, e * 1000, abs(d[1]), abs(d[2]), abs(d[3])))
def ramp(a, b, V=0.5, A=5.0, dt=1 / 30):
    q, v, zs = dict(a), {n: 0.0 for n in a}, []
    for _ in range(900):
        for n in a:
            err = b[n] - q[n]; stop = v[n] ** 2 / (2 * A)
            want = math.copysign(V, err) if abs(err) > stop + 1e-6 else 0.0
            v[n] += max(-A * dt, min(A * dt, want - v[n]))
            if abs(err) < abs(v[n]) * dt: q[n], v[n] = b[n], 0.0
            else: q[n] += v[n] * dt
        zs.append(sm.fk.solve(q).position[2])
        if all(abs(b[n] - q[n]) < 1e-6 for n in a): break
    return len(zs) * dt, min(zs)
t, zmin = ramp(arm(REST), arm(C))
print('휴식 → C (드라이버 램프): %.1f s, TCP z min %.4f (휴식 z %.4f)' % (t, zmin, sm.fk.solve(arm(REST)).position[2]))
t, zmin = ramp(arm(C), arm(REST))
print('C → 휴식 (램프): %.1f s, z min %.4f' % (t, zmin))
pts = waypoints(arm(C), arm(START), 0.3, 30.0)
zs = [sm.fk.solve(p).position[2] for p in pts]
print('C → 시작 자세 (관절 직선 0.3 rad/s): %.1f s, z min %.4f max %.4f' % (len(pts) / 30, min(zs), max(zs)))
d = np.load('/ws/src/twin_e0j0/test/data/practice50_joints.npz')
dist = np.abs(d['state'][:, 1:4] - np.array(C[1:4])).max(1)
i = int(np.argmin(dist))
print('practice_50 에서 가장 가까운 자세 (lift·elbow·wf 최대 차) %.1f°: ep %d frame-state %s' % (dist[i], d['episode'][i], np.round(d['state'][i], 1)))
print('practice_50 에서 C 의 lift·elbow·wf 가 각각 5° 안인 프레임: %d' % int((dist < 5).sum()))
