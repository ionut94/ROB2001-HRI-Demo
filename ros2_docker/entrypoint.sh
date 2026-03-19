#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint for the ROB2001 ROS2 Docker container
#
# Launches each component step-by-step:
#   Xvnc + noVNC → gzserver → spawn robot → robot_state_publisher →
#   rosbridge → Nav2 → initial pose → hri_bridge → gzclient → rviz2
#
# GUI is streamed via noVNC on port 6080 — open http://localhost:6080
# in your browser to see RViz2 and Gazebo.
#
# We avoid the bundled turtlebot3_world.launch.py because its 30 s
# spawn timeout is too short under emulation.  Instead we start
# gzserver alone, wait until the /spawn_entity service appears, then
# spawn the robot ourselves.
# ─────────────────────────────────────────────────────────────────────────────

source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash

export TURTLEBOT3_MODEL=waffle
export GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models

TB3_URDF_DIR=/opt/ros/humble/share/turtlebot3_gazebo
TB3_MODEL_SDF="$TB3_URDF_DIR/models/turtlebot3_waffle/model.sdf"
TB3_WORLD="$TB3_URDF_DIR/worlds/turtlebot3_world.world"

# ── 1. VNC display server (replaces Xvfb — accessible via noVNC) ────────────
echo "🖥  Starting VNC display server …"
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1

# Create VNC password dir (no password for local dev)
mkdir -p /root/.vnc
echo "" | vncpasswd -f > /root/.vnc/passwd 2>/dev/null || true
chmod 600 /root/.vnc/passwd 2>/dev/null || true

# Start Xvnc (TigerVNC) — provides a real X server accessible over VNC
Xvnc :1 -geometry 1280x800 -depth 24 \
    -rfbport 5901 \
    -SecurityTypes None \
    -AlwaysShared \
    -AcceptKeyEvents -AcceptPointerEvents \
    +extension GLX \
    &>/dev/null &
XVNC_PID=$!
export DISPLAY=:1
sleep 2

# Start fluxbox window manager (lightweight, gives window decorations)
echo "🪟  Starting window manager …"
fluxbox &>/dev/null &
sleep 1

# ── 2. noVNC web proxy (browser → VNC) ──────────────────────────────────────
echo "🌐  Starting noVNC on port 6080 …"
NOVNC_DIR="/usr/share/novnc"
websockify --web="$NOVNC_DIR" 6080 localhost:5901 &>/dev/null &
NOVNC_PID=$!
sleep 1

# ── 3. gzserver (physics only — gzclient added later for GUI) ───────────────
echo "🌍  Starting gzserver …"
gzserver "$TB3_WORLD" \
    -slibgazebo_ros_init.so \
    -slibgazebo_ros_factory.so \
    -slibgazebo_ros_force_system.so &
GZSERVER_PID=$!

echo "⏳  Waiting for /spawn_entity service …"
for i in $(seq 1 300); do
    if ros2 service list 2>/dev/null | grep -q "/spawn_entity"; then
        echo "✅  gzserver ready (${i}s)"
        break
    fi
    if [ "$i" = "300" ]; then
        echo "❌  gzserver never provided /spawn_entity — giving up"
        exit 1
    fi
    sleep 1
done

# ── 4. Spawn TurtleBot3 into Gazebo ─────────────────────────────────────────
echo "🤖  Spawning TurtleBot3 waffle …"
ros2 run gazebo_ros spawn_entity.py \
    -entity waffle \
    -file "$TB3_MODEL_SDF" \
    -x -2.0 -y -0.5 -z 0.01 \
    -timeout 120 &
wait $!
echo "✅  Robot spawned"

# ── 5. robot_state_publisher (TF for the URDF) ──────────────────────────────
echo "📐  Starting robot_state_publisher …"
URDF_FILE="$TB3_URDF_DIR/urdf/turtlebot3_waffle.urdf"
if [ -f "$URDF_FILE" ]; then
    ros2 run robot_state_publisher robot_state_publisher \
        --ros-args -p robot_description:="$(cat $URDF_FILE)" \
                   -p use_sim_time:=true &
else
    ros2 run robot_state_publisher robot_state_publisher \
        --ros-args -p robot_description:="$(xacro /opt/ros/humble/share/turtlebot3_description/urdf/turtlebot3_waffle.urdf.xacro)" \
                   -p use_sim_time:=true &
fi
RSP_PID=$!
sleep 2

# ── 6. rosbridge WebSocket ──────────────────────────────────────────────────
echo "🌉  Starting rosbridge on port 9090 …"
ros2 launch rosbridge_server rosbridge_websocket_launch.xml \
    port:=9090 address:=0.0.0.0 &
ROSBRIDGE_PID=$!

echo "⏳  Waiting for rosbridge …"
for i in $(seq 1 60); do
    if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost',9090)); s.close()" 2>/dev/null; then
        echo "✅  rosbridge ready (${i}s)"
        break
    fi
    sleep 1
done

# ── 7. Nav2 ─────────────────────────────────────────────────────────────────
echo "🗺  Starting Nav2 …"
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
    use_sim_time:=true &
NAV2_PID=$!

echo "⏳  Waiting for Nav2 …"
for i in $(seq 1 120); do
    if ros2 topic list 2>/dev/null | grep -q "/local_costmap/costmap"; then
        echo "✅  Nav2 ready (${i}s)"
        break
    fi
    sleep 1
done

# ── 7b. Set initial pose for AMCL (matches spawn position) ──────────────────
echo "📍  Publishing initial pose for AMCL …"
sleep 3
ros2 topic pub --once /initialpose \
    geometry_msgs/msg/PoseWithCovarianceStamped \
    "{header: {frame_id: 'map'}, pose: {pose: {position: {x: -2.0, y: -0.5, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}" \
    2>/dev/null &
wait $!
echo "✅  Initial pose set"

# ── 8. HRI Bridge Node ──────────────────────────────────────────────────────
echo "🤖  Starting HRI bridge node …"
ros2 run hri_bridge robot_status_node.py &
HRI_PID=$!

# ── 9. GUI: gzclient + RViz2 (streamed via noVNC) ───────────────────────────
echo "🎨  Starting Gazebo client (gzclient) …"
gzclient &>/dev/null &
GZCLIENT_PID=$!

echo "📊  Starting RViz2 …"
ros2 run rviz2 rviz2 -d /rviz_config.rviz --ros-args -p use_sim_time:=true &>/dev/null &
RVIZ_PID=$!

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅  All systems launched!"
echo "  🌐  noVNC:      http://0.0.0.0:6080/vnc.html"
echo "  📡  rosbridge:  ws://0.0.0.0:9090"
echo "  🌍  gzserver:   PID $GZSERVER_PID"
echo "  🎮  gzclient:   PID $GZCLIENT_PID"
echo "  📊  RViz2:      PID $RVIZ_PID"
echo "  🗺   Nav2:       PID $NAV2_PID"
echo "  🤖  HRI bridge: PID $HRI_PID"
echo "════════════════════════════════════════════════════════"
echo ""
echo "  Open your browser → http://localhost:6080/vnc.html"
echo ""

# Keep container alive
tail -f /dev/null
