# ─────────────────────────────────────────────────────────────────────────────
# ROB2001 — ROS2 Humble + Gazebo + Nav2 + TurtleBot3
#
# Uses osrf/ros:humble-desktop-full (amd64).  On Apple Silicon this runs
# under Docker's QEMU translation — first boot takes ≈3-5 min but the
# container stays up afterwards.
#
# Provides:
#   • TurtleBot3 Gazebo simulation (with camera plugin)
#   • Nav2 autonomous navigation stack
#   • rosbridge_suite  → WebSocket bridge on port 9090
#   • image_transport   → compressed camera images
#   • noVNC             → browser access to RViz2 / gzclient on port 6080
# ─────────────────────────────────────────────────────────────────────────────
FROM osrf/ros:humble-desktop-full

SHELL ["/bin/bash", "-c"]

# ── Extra ROS / sim packages ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-navigation2 \
        ros-humble-nav2-bringup \
        ros-humble-turtlebot3-gazebo \
        ros-humble-turtlebot3-navigation2 \
        ros-humble-turtlebot3-teleop \
        ros-humble-turtlebot3-description \
        ros-humble-turtlebot3-msgs \
        ros-humble-rosbridge-suite \
        ros-humble-image-transport-plugins \
        ros-humble-compressed-image-transport \
        ros-humble-robot-localization \
        ros-humble-slam-toolbox \
        ros-humble-robot-state-publisher \
        ros-humble-joint-state-publisher \
        ros-humble-xacro \
        ros-humble-cv-bridge \
        python3-pip \
        xvfb \
        mesa-utils \
        libgl1-mesa-dri \
        libgl1-mesa-glx \
        tigervnc-standalone-server \
        tigervnc-common \
        novnc \
        python3-websockify \
        fluxbox \
        xterm \
        net-tools \
    && rm -rf /var/lib/apt/lists/*

# ── Environment ──────────────────────────────────────────────────────────────
ENV TURTLEBOT3_MODEL=waffle
ENV GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models
ENV ROS_DOMAIN_ID=0

# ── Custom ROS2 workspace ───────────────────────────────────────────────────
WORKDIR /ros2_ws
COPY ros2_ws/src /ros2_ws/src

RUN source /opt/ros/humble/setup.bash && \
    colcon build --symlink-install --packages-select hri_bridge

# ── Entrypoint ───────────────────────────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── RViz2 config (map + laser + camera + robot model + nav goals) ────────────
COPY rviz_config.rviz /rviz_config.rviz

EXPOSE 9090
EXPOSE 6080

ENTRYPOINT ["/entrypoint.sh"]
