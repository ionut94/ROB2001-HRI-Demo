#!/usr/bin/env python3
"""
ROB2001 — HRI ROS2 Demo (CLI)

Third demo that integrates the STT + VLM pipeline with a ROS2 virtual
environment running inside Docker. The robot can:

  1. Tell the user where it is (position + nearest named location)
  2. Capture a camera image from the Gazebo simulation and discuss it
  3. Accept voice navigation commands ("go to north east", "go to coordinates 2, 2", etc.)
  4. Full conversational memory with the VLM

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │  macOS HOST                                                  │
  │  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────────┐    │
  │  │ Whisper   │→│ VLM    │→│ pyttsx3 │  │ RosBridge    │    │
  │  │ STT       │  │ Ollama │  │ TTS    │  │ WS Client    │    │
  │  └──────────┘  └────────┘  └────────┘  └──────┬───────┘    │
  └─────────────────────────────────────────────────┼───────────┘
                          WebSocket :9090           │
  ┌─────────────────────────────────────────────────┼───────────┐
  │  DOCKER CONTAINER                               │            │
  │  ┌──────────┐  ┌────────┐  ┌────────────────┐  │            │
  │  │ Gazebo   │  │ Nav2   │  │ rosbridge_suite│◄─┘            │
  │  │ TurtleBot│  │ Stack  │  │ (WebSocket)    │               │
  │  └──────────┘  └────────┘  └────────────────┘               │
  └─────────────────────────────────────────────────────────────┘

Requirements:
  pip install -r requirements.txt
  ollama pull qwen2.5vl:3b
  docker compose up -d    (starts the ROS2 simulation)
"""

import base64
import json
import math
import threading
import time
from io import BytesIO

import cv2
import numpy as np
import whisper

from src.config import LANGUAGE_MAP
from src.audio import record_audio_interactive, transcribe
from src.tts import speak_pyttsx3
from src.emotion import classify_emotion, get_emotion_rate
from src.vlm import ask_vlm, ask_llm, ConversationHistory
from src.commands import parse_command_json
from src.ros_bridge import RosbridgeClient
from src.vision import encode_frame_to_base64
from src.navigation import (
    NAV_COMMAND_SYSTEM_PROMPT,
    parse_nav_command,
    resolve_location,
    describe_robot_position,
    get_location_list,
    NAMED_LOCATIONS,
)

# ── State ────────────────────────────────────────────────────────────────────

history = ConversationHistory()
settings = {"language": "en", "emotion_tts": True}

# Shared state updated by rosbridge callbacks
robot_state = {
    "position": {"x": 0.0, "y": 0.0, "yaw": 0.0},
    "nav_state": "idle",
    "last_image_b64": None,
    "last_image_np": None,
    "image_lock": threading.Lock(),
    "status_lock": threading.Lock(),
}


def speak(text: str, emotion: str = "neutral"):
    """Speak text with optional emotion-aware rate adjustment."""
    if settings["emotion_tts"] and emotion != "neutral":
        print(f"  🎭  Emotion: {emotion}")
    rate = get_emotion_rate(emotion) if settings["emotion_tts"] else 175
    speak_pyttsx3(text, rate=rate, language=settings["language"])


# ── Rosbridge Callbacks ─────────────────────────────────────────────────────

def on_robot_status(msg: dict):
    """Callback for /hri/robot_status (JSON string)."""
    try:
        data = json.loads(msg.get("data", "{}"))
        with robot_state["status_lock"]:
            robot_state["nav_state"] = data.get("nav_state", robot_state["nav_state"])
    except (json.JSONDecodeError, TypeError):
        pass


def on_odom(msg: dict):
    """Callback for /odom — extract position + yaw directly."""
    try:
        pose = msg.get("pose", {}).get("pose", {})
        pos = pose.get("position", {})
        ori = pose.get("orientation", {})
        # Extract yaw from quaternion
        qz = ori.get("z", 0.0)
        qw = ori.get("w", 1.0)
        yaw = math.degrees(2.0 * math.atan2(qz, qw))
        with robot_state["status_lock"]:
            robot_state["position"] = {
                "x": round(pos.get("x", 0.0), 3),
                "y": round(pos.get("y", 0.0), 3),
                "yaw": round(yaw, 1),
            }
    except Exception:
        pass


def on_camera_image(msg: dict):
    """Callback for /camera/image_raw/compressed (sensor_msgs/CompressedImage)."""
    try:
        img_data = msg.get("data", "")
        # rosbridge sends the image data as a base64-encoded string
        if img_data:
            img_bytes = base64.b64decode(img_data)
            np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                with robot_state["image_lock"]:
                    robot_state["last_image_np"] = frame
                    # Resize for VLM (same as webcam pipeline)
                    robot_state["last_image_b64"] = encode_frame_to_base64(frame)
    except Exception:
        pass


def get_current_image_b64() -> str | None:
    """Get the latest camera image as base64."""
    with robot_state["image_lock"]:
        return robot_state["last_image_b64"]


def get_current_position() -> dict:
    """Get the latest robot position."""
    with robot_state["status_lock"]:
        return dict(robot_state["position"])


def show_camera_feed():
    """Display the latest camera frame in an OpenCV window."""
    with robot_state["image_lock"]:
        frame = robot_state["last_image_np"]
    if frame is not None:
        cv2.imshow("Robot Camera (Gazebo)", frame)
        cv2.waitKey(1)
    else:
        print("  ⚠  No camera image available yet")


# ── Pipelines ────────────────────────────────────────────────────────────────

def pipeline_where_am_i(bridge: RosbridgeClient):
    """Pipeline 1: Robot tells the user where it is."""
    print("\n═══ Pipeline 1: Where Am I? ═══")
    print("The robot will describe its current location in the virtual environment.")
    print("Press Enter to ask, or 'q' to quit.\n")

    while True:
        cmd = input("Press Enter to ask where the robot is (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        pos = get_current_position()
        location_desc = describe_robot_position(pos)
        print(f"  📍  {location_desc}")

        # Also get camera image to give visual context
        img_b64 = get_current_image_b64()
        if img_b64:
            show_camera_feed()
            question = (
                f"You are a robot in a simulated environment. "
                f"Your current position data says: {location_desc} "
                f"Describe what you can see in this image from your camera. "
                f"Combine the position information with what you see to give "
                f"the user a comprehensive answer about where you are."
            )
            answer = ask_vlm(img_b64, question, history=history)
        else:
            answer = f"I don't have a camera feed yet, but based on my sensors: {location_desc}"

        emotion = classify_emotion(answer)
        speak(answer, emotion)

    cv2.destroyAllWindows()


def pipeline_vision_chat(bridge: RosbridgeClient, whisper_model):
    """Pipeline 2: Capture image from sim and have a conversation about it."""
    print("\n═══ Pipeline 2: Vision Chat (Gazebo Camera) ═══")
    print("Ask the robot about what it sees in the virtual environment!")
    print("Conversation memory is active. Type 'q' to quit.\n")

    while True:
        cmd = input("Press Enter to ask about the camera view (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        img_b64 = get_current_image_b64()
        if not img_b64:
            print("  ⚠  No camera image available. Is the simulation running?")
            continue

        show_camera_feed()

        audio = record_audio_interactive()
        question = transcribe(whisper_model, audio, settings["language"])
        if not question:
            print("  (no speech detected)")
            continue

        print(f"  📝  You asked: {question}")

        # Add robot context to the question
        pos = get_current_position()
        loc_desc = describe_robot_position(pos)
        context_question = (
            f"[Robot context: {loc_desc}]\n"
            f"User question: {question}"
        )

        answer = ask_vlm(img_b64, context_question, history=history)
        emotion = classify_emotion(answer)
        speak(answer, emotion)


def pipeline_navigation(bridge: RosbridgeClient, whisper_model):
    """Pipeline 3: Voice-controlled navigation."""
    print("\n═══ Pipeline 3: Voice Navigation ═══")
    print("Tell the robot where to go using natural language!")
    print(f"\nKnown locations:\n{get_location_list()}")
    print("\nExamples: 'Go to north east', 'Go to coordinates 2 and 2',")
    print("          'Move forward', 'Turn left', 'Where are you?'")
    print("          'Come back', 'Stop', 'Look around'")
    print("Type 'q' to quit.\n")

    # Advertise the topics we'll publish to
    bridge.advertise("/goal_pose", "geometry_msgs/msg/PoseStamped")
    bridge.advertise("/cmd_vel", "geometry_msgs/msg/Twist")
    time.sleep(0.5)

    while True:
        cmd = input("Press Enter to give a navigation command (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        audio = record_audio_interactive()
        command_text = transcribe(whisper_model, audio, settings["language"])
        if not command_text:
            print("  (no speech detected)")
            continue

        print(f"  📝  Command: {command_text}")

        # Parse the navigation command via text-only LLM (no image needed)
        raw = ask_llm(command_text, system_prompt=NAV_COMMAND_SYSTEM_PROMPT)
        nav_cmd = parse_nav_command(raw)

        if not nav_cmd:
            print(f"  ⚠  Could not parse command: {raw}")
            speak("Sorry, I could not understand that navigation command.", "negative")
            continue

        action = nav_cmd.get("action", "")
        location = nav_cmd.get("location")
        distance = nav_cmd.get("distance")
        angle = nav_cmd.get("angle")
        confidence = nav_cmd.get("confidence", 0.0)

        print(f"  🤖  Parsed: {json.dumps(nav_cmd, indent=2)}")

        if action == "describe_location":
            pos = get_current_position()
            location_desc = describe_robot_position(pos)
            answer = location_desc
            img_b64 = get_current_image_b64()
            if img_b64:
                answer = ask_vlm(
                    img_b64,
                    f"You are a robot. {location_desc} "
                    f"Describe what you see and where you think you are.",
                    history=history,
                )
            speak(answer, "neutral")

        elif action == "go_to_coordinates":
            tx = nav_cmd.get("x")
            ty = nav_cmd.get("y")
            if tx is not None and ty is not None:
                print(f"  🗺  Navigating to coordinates ({tx}, {ty})…")
                speak(f"Navigating to coordinates {tx}, {ty}.", "positive")
                bridge.send_nav_goal(float(tx), float(ty), 0)
            else:
                speak("I need both x and y coordinates.", "negative")

        elif action == "go_to":
            if location:
                loc = resolve_location(location)
                if loc:
                    print(f"  🗺  Navigating to {location} (x={loc['x']}, y={loc['y']})…")
                    speak(f"Navigating to {location}.", "positive")
                    bridge.send_nav_goal(loc["x"], loc["y"], loc.get("yaw", 0))
                else:
                    speak(f"I don't know where {location} is. "
                          f"Known locations are: {', '.join(NAMED_LOCATIONS.keys())}",
                          "negative")
            else:
                speak("I need a location name. Known places: {', '.join(NAMED_LOCATIONS.keys())}.", "negative")

        elif action == "come_back":
            loc = resolve_location(location or "spawn")
            if loc:
                print(f"  🗺  Returning to {location or 'spawn'}…")
                speak("Coming back!", "positive")
                bridge.send_nav_goal(loc["x"], loc["y"], loc.get("yaw", 0))

        elif action == "move_forward":
            dist = distance or 0.5
            speak(f"Moving forward {dist} metres.", "neutral")
            # Send velocity for approximate time
            duration = dist / 0.2  # 0.2 m/s
            bridge.send_cmd_vel(linear_x=0.2)
            time.sleep(duration)
            bridge.send_cmd_vel(linear_x=0.0)

        elif action == "move_backward":
            dist = distance or 0.5
            speak(f"Moving backward {dist} metres.", "neutral")
            duration = dist / 0.2
            bridge.send_cmd_vel(linear_x=-0.2)
            time.sleep(duration)
            bridge.send_cmd_vel(linear_x=0.0)

        elif action == "turn_left":
            ang = angle or 90
            speak(f"Turning left {ang} degrees.", "neutral")
            duration = (ang / 360.0) * (2 * 3.14159 / 0.5)  # at 0.5 rad/s
            bridge.send_cmd_vel(angular_z=0.5)
            time.sleep(duration)
            bridge.send_cmd_vel(angular_z=0.0)

        elif action == "turn_right":
            ang = angle or 90
            speak(f"Turning right {ang} degrees.", "neutral")
            duration = (ang / 360.0) * (2 * 3.14159 / 0.5)
            bridge.send_cmd_vel(angular_z=-0.5)
            time.sleep(duration)
            bridge.send_cmd_vel(angular_z=0.0)

        elif action == "stop":
            bridge.send_cmd_vel(linear_x=0.0, angular_z=0.0)
            speak("Stopping.", "neutral")

        elif action == "look_around":
            speak("Looking around…", "neutral")
            # Rotate slowly for a full 360
            bridge.send_cmd_vel(angular_z=0.3)
            time.sleep(2 * 3.14159 / 0.3)  # full rotation
            bridge.send_cmd_vel(angular_z=0.0)
            # Capture and describe
            time.sleep(0.5)
            img_b64 = get_current_image_b64()
            if img_b64:
                pos = get_current_position()
                loc_desc = describe_robot_position(pos)
                answer = ask_vlm(
                    img_b64,
                    f"You just looked around. {loc_desc} "
                    f"Describe what you can see.",
                    history=history,
                )
                speak(answer, "neutral")

        else:
            speak(f"I understood the action '{action}' but I'm not sure how to execute it.",
                  "negative")

    cv2.destroyAllWindows()


def pipeline_full_conversation(bridge: RosbridgeClient, whisper_model):
    """Pipeline 4: Full conversational mode — combines all capabilities."""
    print("\n═══ Pipeline 4: Full Conversation Mode ═══")
    print("Talk naturally! The robot can:")
    print("  • Tell you where it is")
    print("  • Describe what it sees in the virtual world")
    print("  • Navigate to locations you mention")
    print("  • Answer questions about the environment")
    print("Conversation memory is active. Type 'q' to quit.\n")

    # Advertise navigation topics
    bridge.advertise("/goal_pose", "geometry_msgs/msg/PoseStamped")
    bridge.advertise("/cmd_vel", "geometry_msgs/msg/Twist")
    time.sleep(0.5)

    ROUTER_PROMPT = f"""You are a helpful robot assistant in a simulated environment.
Classify the user's intent as one of:
- "navigation": they want you to go somewhere or move
- "location_query": they want to know where you are
- "vision_query": they want you to describe what you see
- "general_chat": general conversation or questions

Known locations: {', '.join(NAMED_LOCATIONS.keys())}

Output ONLY a JSON object: {{"intent": "<one of above>", "response_needed": true}}
No other text."""

    while True:
        cmd = input("Press Enter to speak (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        img_b64 = get_current_image_b64()
        if img_b64:
            show_camera_feed()

        audio = record_audio_interactive()
        user_text = transcribe(whisper_model, audio, settings["language"])
        if not user_text:
            print("  (no speech detected)")
            continue

        print(f"  📝  You said: {user_text}")

        # Step 1: Classify intent (text-only — no image needed)
        intent_raw = ask_llm(user_text, system_prompt=ROUTER_PROMPT)
        intent_data = parse_nav_command(intent_raw)  # reuse JSON parser
        intent = intent_data.get("intent", "general_chat") if intent_data else "general_chat"
        print(f"  🧠  Intent: {intent}")

        if intent == "navigation":
            # Parse as navigation command (text-only — no image needed)
            raw = ask_llm(user_text, system_prompt=NAV_COMMAND_SYSTEM_PROMPT)
            nav_cmd = parse_nav_command(raw)
            if nav_cmd:
                action = nav_cmd.get("action", "")
                location = nav_cmd.get("location")
                print(f"  🤖  Nav command: {json.dumps(nav_cmd)}")

                if action == "go_to_coordinates":
                    tx = nav_cmd.get("x")
                    ty = nav_cmd.get("y")
                    if tx is not None and ty is not None:
                        speak(f"Navigating to coordinates {tx}, {ty}.", "positive")
                        bridge.send_nav_goal(float(tx), float(ty), 0)
                        history.add("user", user_text)
                        history.add("assistant", f"Navigating to ({tx}, {ty}).")
                    else:
                        speak("I need both x and y coordinates.", "negative")
                elif action == "go_to" and location:
                    loc = resolve_location(location)
                    if loc:
                        speak(f"On my way to {location}!", "positive")
                        bridge.send_nav_goal(loc["x"], loc["y"], loc.get("yaw", 0))
                        history.add("user", user_text)
                        history.add("assistant", f"Navigating to {location}.")
                    else:
                        speak(f"I don't know where {location} is.", "negative")
                elif action == "stop":
                    bridge.send_cmd_vel(0.0, 0.0)
                    speak("Stopping now.", "neutral")
                elif action in ("move_forward", "move_backward", "turn_left", "turn_right"):
                    speak(f"Executing: {action.replace('_', ' ')}", "neutral")
                    _execute_motion(bridge, nav_cmd)
                elif action == "come_back":
                    loc = resolve_location(location or "spawn")
                    if loc:
                        speak("Coming back to spawn!", "positive")
                        bridge.send_nav_goal(loc["x"], loc["y"])
                else:
                    speak("I'm not sure how to do that.", "negative")
            else:
                speak("Sorry, I couldn't parse that navigation command.", "negative")

        elif intent == "location_query":
            pos = get_current_position()
            loc_desc = describe_robot_position(pos)
            if img_b64:
                answer = ask_vlm(
                    img_b64,
                    f"You are a robot. {loc_desc} "
                    f"The user asked: '{user_text}'. "
                    f"Describe where you are, combining sensor data and what you see.",
                    history=history,
                )
            else:
                answer = loc_desc
            speak(answer, "neutral")

        elif intent == "vision_query":
            if img_b64:
                pos = get_current_position()
                loc_desc = describe_robot_position(pos)
                answer = ask_vlm(
                    img_b64,
                    f"[Robot location: {loc_desc}]\nUser: {user_text}",
                    history=history,
                )
                speak(answer, classify_emotion(answer))
            else:
                speak("I can't see anything right now — no camera feed available.", "negative")

        else:  # general_chat
            if img_b64:
                answer = ask_vlm(img_b64, user_text, history=history)
            else:
                answer = ask_vlm(None, user_text, history=history)
            speak(answer, classify_emotion(answer))


def _execute_motion(bridge: RosbridgeClient, nav_cmd: dict):
    """Execute a simple motion command (forward/backward/turn)."""
    action = nav_cmd.get("action", "")
    distance = nav_cmd.get("distance") or 0.5
    angle = nav_cmd.get("angle") or 90

    if action == "move_forward":
        bridge.send_cmd_vel(linear_x=0.2)
        time.sleep(distance / 0.2)
        bridge.send_cmd_vel(linear_x=0.0)
    elif action == "move_backward":
        bridge.send_cmd_vel(linear_x=-0.2)
        time.sleep(distance / 0.2)
        bridge.send_cmd_vel(linear_x=0.0)
    elif action == "turn_left":
        duration = (angle / 360.0) * (2 * 3.14159 / 0.5)
        bridge.send_cmd_vel(angular_z=0.5)
        time.sleep(duration)
        bridge.send_cmd_vel(angular_z=0.0)
    elif action == "turn_right":
        duration = (angle / 360.0) * (2 * 3.14159 / 0.5)
        bridge.send_cmd_vel(angular_z=-0.5)
        time.sleep(duration)
        bridge.send_cmd_vel(angular_z=0.0)


# ── Settings ─────────────────────────────────────────────────────────────────

def settings_menu():
    """Interactive settings menu."""
    print("\n═══ Settings ═══")
    print(f"  Current language: {settings['language']} ({LANGUAGE_MAP.get(settings['language'], '?')})")
    print(f"  Emotion TTS: {'ON' if settings['emotion_tts'] else 'OFF'}")
    print(f"  Chat history: {len(history)} messages")
    print("\n  l) Change language\n  e) Toggle emotion TTS\n  c) Clear history\n  b) Back")
    choice = input("\n> ").strip().lower()
    if choice == "l":
        print(f"  Available: {', '.join(LANGUAGE_MAP.keys())}")
        lang = input("  Language code: ").strip().lower()
        if lang in LANGUAGE_MAP:
            settings["language"] = lang
            print(f"  Language set to: {lang} ({LANGUAGE_MAP[lang]})")
        else:
            print("  Unknown language code.")
    elif choice == "e":
        settings["emotion_tts"] = not settings["emotion_tts"]
        print(f"  Emotion TTS: {'ON' if settings['emotion_tts'] else 'OFF'}")
    elif choice == "c":
        history.clear()
        print("  Conversation history cleared.")


# ── Connection ───────────────────────────────────────────────────────────────

def connect_to_robot(host: str = "localhost", port: int = 9090) -> RosbridgeClient:
    """Connect to the ROS2 simulation via rosbridge WebSocket."""
    bridge = RosbridgeClient(host=host, port=port)
    if not bridge.connect(timeout=30):
        print("  ❌  Failed to connect. Is the Docker container running?")
        print("     Start it with: docker compose up -d")
        raise ConnectionError("Cannot connect to rosbridge")

    # Subscribe to topics
    # Camera: subscribe directly to the Gazebo camera topic for reliability
    bridge.subscribe(
        "/camera/image_raw/compressed",
        "sensor_msgs/msg/CompressedImage",
        on_camera_image,
        throttle_rate=200,  # 5 Hz (keep bandwidth reasonable over WS)
    )
    # Odometry: subscribe directly
    bridge.subscribe(
        "/odom",
        "nav_msgs/msg/Odometry",
        on_odom,
        throttle_rate=500,  # 2 Hz
    )
    # Also try the HRI status topic (optional, for nav_state)
    bridge.subscribe(
        "/hri/robot_status",
        "std_msgs/msg/String",
        on_robot_status,
        throttle_rate=500,
    )

    # Wait a moment for initial data
    print("  ⏳  Waiting for initial data from simulation…")
    time.sleep(3)
    return bridge


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════════╗")
    print("║   ROB2001 — HRI ROS2 Demo (Virtual Environment)   ║")
    print("╚═══════════════════════════════════════════════════╝")

    # Connect to ROS2 simulation
    print("\n📡  Connecting to ROS2 simulation…")
    try:
        bridge = connect_to_robot()
    except ConnectionError:
        return

    # Load Whisper
    print("\n🎙  Loading Whisper model (base)…")
    whisper_model = whisper.load_model("base")
    print("Whisper ready.\n")

    while True:
        print("Select a pipeline:")
        print("  1) Where Am I? — Robot describes its location")
        print("  2) Vision Chat — Ask about what the robot sees in Gazebo")
        print("  3) Voice Navigation — Tell the robot where to go")
        print("  4) Full Conversation — All capabilities combined")
        print("  s) Settings")
        print("  q) Quit")
        choice = input("\n> ").strip()

        if choice == "1":
            pipeline_where_am_i(bridge)
        elif choice == "2":
            pipeline_vision_chat(bridge, whisper_model)
        elif choice == "3":
            pipeline_navigation(bridge, whisper_model)
        elif choice == "4":
            pipeline_full_conversation(bridge, whisper_model)
        elif choice.lower() == "s":
            settings_menu()
        elif choice.lower() == "q":
            print("Disconnecting…")
            bridge.disconnect()
            cv2.destroyAllWindows()
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.\n")


if __name__ == "__main__":
    main()
