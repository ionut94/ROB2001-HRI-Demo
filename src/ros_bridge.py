"""Rosbridge WebSocket client for communicating with the ROS2 Docker container.

Uses the rosbridge_suite JSON protocol over WebSocket to:
  • Subscribe to topics  (camera images, robot status)
  • Publish to topics    (navigation goals, cancel commands)
  • Call services         (if needed)

This keeps the host machine free from any ROS2 installation — only the
`websocket-client` Python package is required.
"""

import base64
import json
import math
import threading
import time
from typing import Callable, Optional

import websocket  # websocket-client


class RosbridgeClient:
    """Thin async wrapper around rosbridge_suite's WebSocket protocol."""

    def __init__(self, host: str = "localhost", port: int = 9090):
        self.url = f"ws://{host}:{port}"
        self.ws: Optional[websocket.WebSocketApp] = None
        self._connected = threading.Event()
        self._subscribers: dict[str, Callable] = {}
        self._ws_thread: Optional[threading.Thread] = None
        self._running = False

    # ── Connection ───────────────────────────────────────────────────────

    def connect(self, timeout: float = 30.0) -> bool:
        """Connect to rosbridge. Blocks until connected or timeout."""
        print(f"  🔌  Connecting to rosbridge at {self.url} …")
        self._running = True

        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._ws_thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": 10, "ping_timeout": 5},
            daemon=True,
        )
        self._ws_thread.start()

        if self._connected.wait(timeout):
            print("  ✅  Connected to rosbridge")
            return True
        else:
            print("  ❌  Connection timeout")
            return False

    def disconnect(self):
        """Close the WebSocket connection."""
        self._running = False
        if self.ws:
            self.ws.close()
        if self._ws_thread:
            self._ws_thread.join(timeout=5)
        print("  🔌  Disconnected from rosbridge")

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    # ── Subscribe / Publish ──────────────────────────────────────────────

    def subscribe(self, topic: str, msg_type: str, callback: Callable,
                  throttle_rate: int = 0, queue_length: int = 1,
                  compression: str = "none"):
        """Subscribe to a ROS topic via rosbridge."""
        self._subscribers[topic] = callback
        msg = {
            "op": "subscribe",
            "topic": topic,
            "type": msg_type,
            "throttle_rate": throttle_rate,
            "queue_length": queue_length,
        }
        if compression != "none":
            msg["compression"] = compression
        self._send(msg)

    def unsubscribe(self, topic: str):
        """Unsubscribe from a ROS topic."""
        self._subscribers.pop(topic, None)
        self._send({"op": "unsubscribe", "topic": topic})

    def publish(self, topic: str, msg_type: str, msg_data: dict):
        """Publish a message to a ROS topic."""
        self._send({
            "op": "publish",
            "topic": topic,
            "type": msg_type,
            "msg": msg_data,
        })

    def advertise(self, topic: str, msg_type: str):
        """Advertise a topic (needed before publishing)."""
        self._send({
            "op": "advertise",
            "topic": topic,
            "type": msg_type,
        })

    # ── Navigation helpers ───────────────────────────────────────────────

    def send_nav_goal(self, x: float, y: float, yaw_deg: float = 0.0):
        """Publish a PoseStamped to /goal_pose for Nav2."""
        yaw_rad = math.radians(yaw_deg)
        # Quaternion from yaw
        qz = math.sin(yaw_rad / 2.0)
        qw = math.cos(yaw_rad / 2.0)

        now = time.time()
        secs = int(now)
        nsecs = int((now - secs) * 1e9)

        pose_msg = {
            "header": {
                "stamp": {"sec": secs, "nanosec": nsecs},
                "frame_id": "map",
            },
            "pose": {
                "position": {"x": x, "y": y, "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": qz, "w": qw},
            },
        }
        self.publish("/goal_pose", "geometry_msgs/msg/PoseStamped", pose_msg)

    def send_cmd_vel(self, linear_x: float = 0.0, angular_z: float = 0.0):
        """Publish a Twist to /cmd_vel for direct velocity control."""
        twist = {
            "linear": {"x": linear_x, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": angular_z},
        }
        self.publish("/cmd_vel", "geometry_msgs/msg/Twist", twist)

    # ── Internal ─────────────────────────────────────────────────────────

    def _send(self, data: dict):
        if self.ws and self._connected.is_set():
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                print(f"  ⚠  WebSocket send error: {e}")

    def _on_open(self, ws):
        self._connected.set()

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return
        topic = data.get("topic")
        if topic and topic in self._subscribers:
            try:
                self._subscribers[topic](data.get("msg", {}))
            except Exception as e:
                print(f"  ⚠  Subscriber error on {topic}: {e}")

    def _on_error(self, ws, error):
        if self._running:
            print(f"  ⚠  WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self._connected.clear()
        if self._running:
            print("  ⚠  WebSocket closed, attempting reconnect in 3s…")
            time.sleep(3)
            if self._running:
                self.connect(timeout=10)
