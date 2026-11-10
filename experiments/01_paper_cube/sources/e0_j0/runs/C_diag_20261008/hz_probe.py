import sys, time, threading
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
rclpy.init()
n = rclpy.create_node('hz_probe_ro')
cnt = {'f': 0, 'w': 0}; gaps = {'f': [], 'w': []}; last = {}
def cb(k):
    def f(m):
        t = time.monotonic(); cnt[k] += 1
        if k in last: gaps[k].append(t - last[k])
        last[k] = t
    return f
n.create_subscription(Image, '/head_camera/image_raw', cb('f'), qos_profile_sensor_data)
n.create_subscription(Image, '/wrist_camera/image_raw', cb('w'), qos_profile_sensor_data)
assert not [p for p in n.publishers if p.topic_name not in ('/rosout', '/parameter_events')]
ex = SingleThreadedExecutor(); ex.add_node(n)
end = time.monotonic() + 3
while time.monotonic() < end: ex.spin_once(timeout_sec=0.1)
for k in cnt: cnt[k] = 0; gaps[k] = []
t0 = time.monotonic(); dur = float(sys.argv[1]) if len(sys.argv) > 1 else 15
while time.monotonic() - t0 < dur: ex.spin_once(timeout_sec=0.1)
for k in cnt:
    g = sorted(gaps[k])
    print(k, 'hz %.1f' % (cnt[k] / dur), 'gap max %.0f ms' % (1000 * g[-1]) if g else '', '>50ms:', sum(x > 0.05 for x in g))
