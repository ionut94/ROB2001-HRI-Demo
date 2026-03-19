#!/usr/bin/env python3
"""
ROB2001 — Robot Status Node

Runs inside the Docker container alongside TurtleBot3 Gazebo.
Publishes a JSON status message containing:
  • Robot position (x, y, yaw) from /odom
  • Navigation state from nav2 action feedback
  • Latest compressed camera image re-published on /hri/camera/compressed

This node makes it easy for the host-side rosbridge client to get
everything it needs from a small number of topics.
"""
import json
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String


def quaternion_to_yaw(q):
    """Extract yaw from a quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RobotStatusNode(Node):
    def __init__(self):
        super().__init__("robot_status_node")
        self.get_logger().info("Robot Status Node starting…")

        # State
        self.position = {"x": 0.0, "y": 0.0, "yaw": 0.0}
        self.nav_state = "idle"  # idle | navigating | succeeded | failed

        # QoS for sensor topics
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=1,
        )

        # Subscribers
        self.create_subscription(
            Odometry, "/odom", self._odom_cb, sensor_qos
        )

        # Republish camera compressed for easy websocket access
        self.create_subscription(
            CompressedImage,
            "/camera/image_raw/compressed",
            self._camera_cb,
            sensor_qos,
        )

        # Publishers
        self.status_pub = self.create_publisher(String, "/hri/robot_status", 10)
        self.camera_pub = self.create_publisher(
            CompressedImage, "/hri/camera/compressed", sensor_qos
        )

        # Publish status at 2 Hz
        self.create_timer(0.5, self._publish_status)

        self.get_logger().info("Robot Status Node ready ✓")

    # ── Callbacks ────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry):
        p = msg.pose.pose.position
        yaw = quaternion_to_yaw(msg.pose.pose.orientation)
        self.position = {
            "x": round(p.x, 3),
            "y": round(p.y, 3),
            "yaw": round(math.degrees(yaw), 1),
        }

    def _camera_cb(self, msg: CompressedImage):
        # Republish on /hri/ namespace so the host can easily subscribe
        self.camera_pub.publish(msg)

    # ── Status publishing ────────────────────────────────────────────────

    def _publish_status(self):
        status = {
            "position": self.position,
            "nav_state": self.nav_state,
        }
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
