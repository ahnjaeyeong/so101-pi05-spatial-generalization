"""탁자 놓기 검토: P16 에서 TCP 수직 강성 k = 1 / (J_z C J_z^T) — practice_50 쥔 자세(탁자 근처)에서."""
import numpy as np
import PyKDL as kdl
from kdl_parser_py.urdf import treeFromUrdfModel
from urdf_parser_py.urdf import URDF
from twin_kinematics import strip_xml_declaration
from twin_e0j0.convert import lerobot_to_twin
from twin_e0j0.handoff import HandoffDetector
from twin_e0j0.config import load_config
from twin_kinematics import TcpForwardKinematics

U = open('/ws/src/twin_description/urdf/so101_new_calib.urdf').read()
ok, tree = treeFromUrdfModel(URDF.from_xml_string(strip_xml_declaration(U)), quiet=True)
chain = tree.getChain('base_link', 'gripper_frame_link')
jac = kdl.ChainJntToJacSolver(chain)
fk = TcpForwardKinematics(U, 'base_link', 'gripper_frame_link')
names = list(fk.joint_names)
C = np.diag([0.0, 0.121, 0.118, 0.120, 0.0])
cfg = load_config('/ws/src/twin_e0j0/config/e0j0.yaml')
d = np.load('/ws/src/twin_e0j0/test/data/practice50_joints.npz')
ks = []
for ep in np.unique(d['episode']):
    m = d['episode'] == ep
    det = HandoffDetector(cfg.handoff)
    for i, s in enumerate(d['state'][m]):
        q = lerobot_to_twin(list(s))
        if det.update(i / 30, float(s[5]), float(d['action'][m][i, 5]), fk.solve(q).position[2],
                      payload={n: q[n] for n in names}) == 'handoff':
            break
    qh = det.payload_hold
    if qh is None:
        continue
    arr = kdl.JntArray(len(names))
    for k, n in enumerate(names):
        arr[k] = qh[n]
    J = kdl.Jacobian(len(names)); jac.JntToJac(arr, J)
    jz = np.array([J[2, k] for k in range(len(names))])
    ks.append(1.0 / float(jz @ C @ jz))
ks = np.array(ks)
print('쥔 자세 n=%d: P16 TCP 수직 강성 k [N/m] p10 %.0f  p50 %.0f  p90 %.0f' % (len(ks), *np.percentile(ks, [10, 50, 90])))
for mm in (3, 5, 10, 19):
    print('  수직 %2d mm 눌림 → 힘 p50 %.2f N (%.0f g)' % (mm, np.median(ks) * mm / 1000, np.median(ks) * mm / 1000 / 9.81 * 1000))
