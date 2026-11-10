import time, rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
rclpy.init(); n = rclpy.create_node('fake_cam_pub')
pubs = [n.create_publisher(Image, t, qos_profile_sensor_data) for t in ('/head_camera/image_raw', '/wrist_camera/image_raw')]
data = bytes(640 * 480 * 3); t = time.monotonic()
while rclpy.ok():
    for p in pubs:
        m = Image(); m.height, m.width, m.encoding, m.step = 480, 640, 'rgb8', 1920; m.data = data; p.publish(m)
    t += 1 / 30; time.sleep(max(0, t - time.monotonic()))
