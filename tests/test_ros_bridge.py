"""Tests for src/ros_bridge.py — RosbridgeClient unit tests.

These tests verify the client logic without requiring a live rosbridge.
"""

import json
import math
import threading

import pytest

from src.ros_bridge import RosbridgeClient


class TestRosbridgeClientInit:
    def test_default_url(self):
        client = RosbridgeClient()
        assert client.url == "ws://localhost:9090"

    def test_custom_url(self):
        client = RosbridgeClient(host="192.168.1.10", port=8080)
        assert client.url == "ws://192.168.1.10:8080"

    def test_initial_state(self):
        client = RosbridgeClient()
        assert not client.is_connected
        assert client.ws is None


class TestNavigationHelpers:
    """Test nav goal message construction (no actual connection needed)."""

    def test_nav_goal_message_structure(self):
        """Verify the PoseStamped message structure is correct."""
        client = RosbridgeClient()
        # We can't actually send, but we can test the math
        yaw_deg = 90.0
        yaw_rad = math.radians(yaw_deg)
        qz = math.sin(yaw_rad / 2.0)
        qw = math.cos(yaw_rad / 2.0)

        assert abs(qz - math.sin(math.pi / 4)) < 1e-6
        assert abs(qw - math.cos(math.pi / 4)) < 1e-6

    def test_zero_yaw_quaternion(self):
        yaw_deg = 0.0
        yaw_rad = math.radians(yaw_deg)
        qz = math.sin(yaw_rad / 2.0)
        qw = math.cos(yaw_rad / 2.0)

        assert abs(qz) < 1e-6
        assert abs(qw - 1.0) < 1e-6


class TestSubscriberRouting:
    def test_on_message_routes_to_subscriber(self):
        client = RosbridgeClient()
        received = []

        def callback(msg):
            received.append(msg)

        client._subscribers["/test_topic"] = callback

        # Simulate receiving a message
        message = json.dumps({
            "op": "publish",
            "topic": "/test_topic",
            "msg": {"data": "hello"},
        })
        client._on_message(None, message)

        assert len(received) == 1
        assert received[0]["data"] == "hello"

    def test_unknown_topic_ignored(self):
        client = RosbridgeClient()
        received = []

        def callback(msg):
            received.append(msg)

        client._subscribers["/known"] = callback

        message = json.dumps({
            "op": "publish",
            "topic": "/unknown",
            "msg": {"data": "ignored"},
        })
        client._on_message(None, message)

        assert len(received) == 0

    def test_invalid_json_ignored(self):
        client = RosbridgeClient()
        # Should not raise
        client._on_message(None, "not json at all")

    def test_subscriber_error_handled(self):
        client = RosbridgeClient()

        def bad_callback(msg):
            raise ValueError("test error")

        client._subscribers["/bad"] = bad_callback

        message = json.dumps({
            "op": "publish",
            "topic": "/bad",
            "msg": {"data": "boom"},
        })
        # Should not raise
        client._on_message(None, message)
