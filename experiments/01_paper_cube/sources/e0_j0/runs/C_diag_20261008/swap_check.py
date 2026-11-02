"""녹화 관측을 떠 있는 정책 서버에 넣어 출발 시점을 본다 (팔 무관). PYTHONDONTWRITEBYTECODE=1 so101-env python."""
import json, sys, time
import av, cv2, numpy as np
sys.path.insert(0, '/home/user/so101_boxpick/e0_j0')
import protocol
TASK = 'pick up the red cube and put it in the brown box'
R = '/home/user/so101_runs/practice/practice_50/eval/rollouts/20261007_104105_15k_rtc_fast'
SH = '/home/user/Ros2_e0j0/ros2_ws/e0j0_runs/shadow_20261008_005222'
N = 300

def frames(path, n):
    out = []
    with av.open(path) as c:
        for f in c.decode(video=0):
            out.append(np.ascontiguousarray(f.to_ndarray(format='rgb24')).tobytes())
            if len(out) == n:
                break
    return out

st = np.load(R + '/analysis.npz')
r_state, r_action = st['ep0_state'], st['ep0_action']
r_img = {k: frames('{0}/dataset/videos/observation.images.{1}/chunk-000/file-000.mp4'.format(R, k), N) for k in ('front', 'wrist')}
sh0 = json.loads(open(SH + '/ticks.jsonl').readline())['state']
sh_img = {k: cv2.cvtColor(cv2.imread('{0}/{1}_0000.0.png'.format(SH, k)), cv2.COLOR_BGR2RGB).tobytes() for k in ('front', 'wrist')}

def session(name, get):
    sock = protocol.connect('172.17.0.1', 5555, 5.0); sock.settimeout(5.0)
    protocol.request(sock, {'type': 'hello', 'v': protocol.PROTOCOL_VERSION, 'client': 'replay_check'})
    rep = protocol.request(sock, {'type': 'reset', 'task': TASK})
    acts, t = [], time.monotonic()
    for i in range(N):
        state, imgs = get(i)
        blobs = [(k, (480, 640, 3), imgs[k]) for k in ('front', 'wrist')]
        rep = protocol.request(sock, {'type': 'step', 'seq': i, 'state': [float(v) for v in state], 'task': TASK}, blobs)
        if rep.get('action') is not None:
            acts.append(rep['action'])
        t += 1 / 30; time.sleep(max(0, t - time.monotonic()))
    protocol.send_message(sock, {'type': 'bye'}); protocol.recv_message(sock); sock.close()
    a = np.array(acts); s0 = np.array(get(0)[0])
    d = np.abs(a[:, :5] - s0[:5]).max(1)
    first = next((i for i, v in enumerate(d) if v > 3), None)
    print('{0:16s} actions {1:3d} | first >3deg at {2} | max dev {3:.1f} deg | gripper max {4:.1f} | a[150]-s0 {5}'.format(
        name, len(a), first, d.max(), a[:, 5].max(), np.round(a[min(150, len(a) - 1), :5] - s0[:5], 1)), flush=True)


sh30 = {k: cv2.cvtColor(cv2.imread('{0}/{1}_0030.2.png'.format(SH, k)), cv2.COLOR_BGR2RGB).tobytes() for k in ('front', 'wrist')}
r0 = {k: r_img[k][0] for k in r_img}
session('Sstate+Rimg', lambda i: (sh0, r0))
session('Rstate+Simg', lambda i: (r_state[0], sh_img))
session('R+Sfront+Rwrist', lambda i: (r_state[0], {'front': sh_img['front'], 'wrist': r0['wrist']}))
session('R+Rfront+Swrist', lambda i: (r_state[0], {'front': r0['front'], 'wrist': sh_img['wrist']}))
session('Sstate+Simg@30s', lambda i: (sh0, sh30))
