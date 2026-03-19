#!/usr/bin/env python3
"""
ROB2001 — Combined launch file
Brings up: Gazebo (TurtleBot3 world) + Nav2 + rosbridge + hri_bridge node
"""
import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    TimerAction,
)
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
    AnyLaunchDescriptionSource,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # ── Paths ────────────────────────────────────────────────────────────
    tb3_gazebo_dir = get_package_share_directory("turtlebot3_gazebo")
    tb3_nav2_dir = get_package_share_directory("turtlebot3_navigation2")
    rosbridge_dir = get_package_share_directory("rosbridge_server")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # ── 1. Gazebo — TurtleBot3 World ─────────────────────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gazebo_dir, "launch", "turtlebot3_world.launch.py")
        ),
    )

    # ── 2. Nav2 Bringup ──────────────────────────────────────────────────
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_nav2_dir, "launch", "navigation2.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "true",
        }.items(),
    )

    # ── 3. rosbridge_websocket (via its official XML launch file) ────────
    rosbridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(rosbridge_dir, "launch", "rosbridge_websocket_launch.xml")
        ),
        launch_arguments={
            "port": "9090",
            "address": "0.0.0.0",
        }.items(),
    )

    # ── 4. HRI Status Bridge Node ────────────────────────────────────────
    hri_status_node = Node(
        package="hri_bridge",
        executable="robot_status_node.py",
        name="robot_status_node",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # Delay Nav2 and bridge nodes to let Gazebo start first
    delayed_nav2 = TimerAction(period=10.0, actions=[nav2_launch])
    delayed_bridge = TimerAction(period=5.0, actions=[rosbridge_launch])
    delayed_hri = TimerAction(period=15.0, actions=[hri_status_node])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gazebo_launch,
        delayed_bridge,
        delayed_nav2,
        delayed_hri,
    ])
