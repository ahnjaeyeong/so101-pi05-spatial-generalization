"""점검 자세를 practice_50 에서 실제로 지나간 자세 중에서: z>=0.05, 각 관절 +0.1 rad 에도 z>=0.03, 벽 안, P16 처짐 최소."""
import math, sys
import numpy as np
sys.path.insert(0, '/ws/e0j0_runs/diag_20261008_sag')
import sag_model as sm  # noqa: E402
from twin_e0j0.convert import lerobot_to_twin
from twin_e0j0.walls import CommandWalls
walls = CommandWalls('/ws/src/twin_bringup/config/sites/thor/calibration_so101_jetson.json', '/ws/src/twin_e0j0/config/physical_limits_thor_e0j0.yaml')
d = np.load('/ws/src/twin_e0j0/test/data/practice50_joints.npz')
S, E = d['state'], d['episode']
START = np.array([70.9, 15.8, 34.1, 74.3, 6.8, 0.6])
out = []
for i in range(0, len(S), 3):
    lr = list(S[i]); lr[5] = 0.6                       # 집게는 닫힘으로
    q = lerobot_to_twin(lr)
    if walls.reasons(q):
        continue
    qa = {n: q[n] for n in sm.names}
    z = sm.fk.solve(qa).position[2]
    if z < 0.05:
        continue
    bad = False
    for j in sm.names:
        q2 = dict(qa); q2[j] += 0.1; full = dict(q); full[j] += 0.1
        if sm.fk.solve(q2).position[2] < 0.03 or walls.reasons(full):
            bad = True; break
    if bad:
        continue
    out.append((sm.sag(qa)[1], float(np.abs(S[i, :5] - START[:5]).max()), int(E[i]), i, np.round(S[i], 1), z))
print('조건을 지키는 실제 프레임 %d개' % len(out))
for err, dist, ep, i, s, z in sorted(out, key=lambda r: r[0])[:5]:
    print('  처짐 최소: P16 %.1f mm  z %.3f  시작 자세와 %.0f°  ep %d  %s' % (err * 1000, z, dist, ep, s))
for err, dist, ep, i, s, z in sorted([r for r in out if r[0] < 0.008], key=lambda r: r[1])[:5]:
    print('  P16<8mm 중 시작 자세에 가까운 것: %.1f mm  z %.3f  %.0f°  ep %d  %s' % (err * 1000, z, dist, ep, s))
