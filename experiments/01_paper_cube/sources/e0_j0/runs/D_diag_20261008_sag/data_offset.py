"""practice_50: action(리더) − state(팔로워, P16) 가 중력 처짐 모형과 맞는가 — 정지 구간에서."""
import math, sys
import numpy as np
sys.path.insert(0, '/ws/e0j0_runs/diag_20261008_sag')
import sag_model as sm  # noqa: E402 (모형·눈금 재사용, 출력은 한 번 더 찍힌다)
from twin_e0j0.convert import lerobot_to_twin

d = np.load('/ws/src/twin_e0j0/test/data/practice50_joints.npz')
S, A, E = d['state'], d['action'], d['episode']
rows = []
for ep in np.unique(E):
    s, a = S[E == ep], A[E == ep]
    v = np.abs(np.diff(s, axis=0)).max(1)
    for i in range(5, len(s) - 5):
        if v[i - 5:i + 5].max() < 0.3:       # 0.33 s 동안 거의 정지 (도/프레임)
            q = {n: x for n, x in lerobot_to_twin(list(s[i])).items() if n in sm.names}
            pred = -sm.C * sm.G(q)           # rad, 처짐 = 명령보다 아래 (부호는 관절 축 기준)
            rows.append((a[i, 1] - s[i, 1], a[i, 2] - s[i, 2], math.degrees(pred[1]), math.degrees(pred[2])))
r = np.array(rows)
print('정지 프레임 n=%d' % len(r))
for j, name in ((0, 'shoulder_lift'), (1, 'elbow_flex')):
    meas, pred = r[:, j], r[:, j + 2]
    c = np.corrcoef(meas, pred)[0, 1]
    k = np.polyfit(pred, meas, 1)
    print('%-14s 데이터 action−state 중앙값 %+.2f° (p10 %+.2f, p90 %+.2f) | 모형 P16 처짐 중앙값 %+.2f° | 상관 %.2f, 기울기 %.2f'
          % (name, np.median(meas), *np.percentile(meas, [10, 90]), np.median(pred), c, k[0]))
