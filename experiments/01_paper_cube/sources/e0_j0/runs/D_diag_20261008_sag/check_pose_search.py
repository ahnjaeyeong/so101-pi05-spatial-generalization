"""자기 점검·home 자세 후보: P16 처짐 TCP 오차 최소, z>=0.06 이고 각 관절 +0.1 rad 에도 z>=0.04, 벽 안, 시작 자세에 가까움."""
import itertools, math, sys
import numpy as np
sys.path.insert(0, '/ws/e0j0_runs/diag_20261008_sag')
import sag_model as sm  # noqa: E402
from twin_e0j0.convert import lerobot_to_twin, twin_to_lerobot
from twin_e0j0.walls import CommandWalls
walls = CommandWalls('/ws/src/twin_bringup/config/sites/thor/calibration_so101_jetson.json', '/ws/src/twin_e0j0/config/physical_limits_thor_e0j0.yaml')
start = [70.9, 15.8, 34.1, 74.3, 6.8, 0.6]
best = []
for lift, elbow, wf in itertools.product(range(-60, 41, 5), range(-10, 101, 5), range(0, 101, 5)):
    lr = [start[0], lift, elbow, wf, start[4], start[5]]
    q = lerobot_to_twin(lr)
    if walls.reasons(q):
        continue
    qa = {n: q[n] for n in sm.names}
    z = sm.fk.solve(qa).position[2]
    if z < 0.06:
        continue
    ok = True
    for j in sm.names:
        q2 = dict(qa); q2[j] += 0.1
        full = dict(q); full[j] += 0.1
        if sm.fk.solve(q2).position[2] < 0.04 or walls.reasons(full):
            ok = False; break
    if not ok:
        continue
    err = sm.sag(qa)[1]
    dist = max(abs(a - b) for a, b in zip(lr[:5], start[:5]))
    best.append((err, dist, lr, z))
best.sort(key=lambda r: (round(r[0] * 1000), r[1]))
print('후보 %d개. 처짐 오차 작은 순 (같으면 시작 자세에 가까운 순):' % len(best))
for err, dist, lr, z in best[:8]:
    print('  P16 TCP %.1f mm  z %.3f  시작 자세와 최대 %.0f°  lerobot %s' % (err * 1000, z, dist, lr))
near = sorted([b for b in best if b[0] < 0.010], key=lambda r: r[1])[:5]
print('P16 처짐 < 10 mm 중 시작 자세에 가장 가까운 것:')
for err, dist, lr, z in near:
    print('  P16 TCP %.1f mm  z %.3f  시작 자세와 최대 %.0f°  lerobot %s' % (err * 1000, z, dist, lr))
