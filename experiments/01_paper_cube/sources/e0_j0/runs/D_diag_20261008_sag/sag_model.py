"""P16 중력 처짐 추정 — URDF 질량으로 자세별 중력 토크 G(q), home 실측(lift 0.061, elbow 0.050 rad)으로 눈금."""
import json, math, sys
import numpy as np
import PyKDL as kdl
from urdf_parser_py.urdf import URDF
import kdl_parser_py.urdf as kp
from twin_kinematics import TcpForwardKinematics
from twin_e0j0.convert import lerobot_to_twin

U = open('/ws/src/twin_description/urdf/so101_new_calib.urdf').read()
fk = TcpForwardKinematics(U, 'base_link', 'gripper_frame_link')
ok, tree = kp.treeFromUrdfModel(URDF.from_xml_string(U.split('?>', 1)[-1] if U.startswith('<?xml') else U), quiet=True)
chain = tree.getChain('base_link', 'gripper_frame_link')
names = list(fk.joint_names)
dyn = kdl.ChainDynParam(chain, kdl.Vector(0, 0, -9.81))

def G(q):
    a = kdl.JntArray(len(names))
    for i, n in enumerate(names): a[i] = q[n]
    g = kdl.JntArray(len(names)); dyn.JntToGravity(a, g)
    return np.array([g[i] for i in range(len(names))])

home = {n: 0.0 for n in names}
g0 = G(home)
print('joint order', names); print('G(home) N·m', np.round(g0, 4))
# 눈금: P16 에서 rad per N·m (lift·elbow 실측). 같은 STS3215 라 관절별 값이 비슷해야 모형이 맞다.
c_lift, c_elbow = 0.061 / abs(g0[1]), 0.050 / abs(g0[2])
print('compliance P16 rad/Nm: lift %.3f elbow %.3f' % (c_lift, c_elbow))
C = np.array([0, c_lift, c_elbow, (c_lift + c_elbow) / 2, 0]) if len(names) == 5 else None

def sag(q, scale=1.0):
    g = G(q)
    d = -C * g * scale
    q2 = {n: q[n] + d[i] for i, n in enumerate(names)}
    p, p2 = fk.solve(q).position, fk.solve(q2).position
    return d, math.dist(p, p2)

d, e = sag(home)
print('home: 모형 처짐 rad', np.round(d, 3), 'TCP %.4f m (사용자 실측 잔차 0.0373)' % e)
poses = {
    'home (URDF 영점, ㄱ자)': home,
    '휴식 자세 (② 첫 관측)': lerobot_to_twin([70.33, -30.29, 70.29, 51.25, 20.97, 0.69]),
    '학습 시작 자세 (29번 편)': lerobot_to_twin([70.9, 15.8, 34.1, 74.3, 6.8, 0.6]),
}
for label, q in poses.items():
    q = {n: q[n] for n in names}
    for P, s in (('P16', 1.0), ('P32', 0.5)):
        d, e = sag(q, s)
        print('%-22s %s TCP 오차 %5.1f mm  관절 처짐 lift %.3f elbow %.3f wf %.3f rad' % (label, P, e * 1000, abs(d[1]), abs(d[2]), abs(d[3])))
# practice_50 전 프레임 (정책 단계 자세 분포)
data = np.load('/ws/src/twin_e0j0/test/data/practice50_joints.npz')
errs16 = []
for s in data['state'][::5]:
    q = {n: v for n, v in lerobot_to_twin(list(s)).items() if n in names}
    errs16.append(sag(q)[1])
errs16 = np.array(errs16) * 1000
print('practice_50 자세 (n=%d) P16 TCP 오차 mm: p50 %.1f p90 %.1f max %.1f' % (len(errs16), *np.percentile(errs16, [50, 90]), errs16.max()))
# B단계 계획 결과의 박스 standoff·place 자세
try:
    rows = json.load(open('/ws/e0j0_runs/fast_plan_check.json'))['rows']
    for key in ('standoff', 'place'):
        es = []
        for r in rows:
            v = r['box'] and r['box']['new'][key]
            if v:
                es.append(sag(dict(zip(names, v)))[1] * 1000)
        print('박스 %-8s (n=%d) P16 TCP 오차 mm: p50 %.1f max %.1f | P32 절반' % (key, len(es), np.median(es), max(es)))
except FileNotFoundError:
    print('fast_plan_check.json 없음')
