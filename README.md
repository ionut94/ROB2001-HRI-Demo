# ROB2001 — Communication in Robotics: HRI Demo

A hands-on Human-Robot Interaction (HRI) demo for the **ROB2001 Communication in Robotics** module. This project showcases how speech, vision, and gesture modalities can be combined to build a multimodal communication interface for a robot.

The demo comes in three versions — **v1** (basic), **v2** (extended), and **v3 (ROS2)** — each available as both a **CLI** and a **GUI** (Tkinter) application (v3 is CLI-only with a dockerised ROS2 backend).

---

## ✨ Features

### v1 — Core Pipelines

| # | Pipeline | Description |
|---|----------|-------------|
| 1 | **Basic STT + TTS** | Speak into the microphone → Whisper transcribes → robot repeats your words aloud |
| 2 | **Vision + STT + TTS** | Ask the robot what it sees → webcam frame captured → VLM describes the scene → response spoken aloud |

### v2 — Extended Pipelines

All v1 features plus:

| # | Pipeline | Description |
|---|----------|-------------|
| 1 | **Conversation Memory** | Multi-turn dialogue with a sliding-window history so the robot remembers context |
| 2 | **Wake Word Detection** | Hands-free activation — say *"Hey Jarvis"* to wake the robot before speaking |
| 3 | **Emotion-Aware TTS** | Keyword-based emotion classification adjusts speech rate (excited → faster, warning → slower) |
| 4 | **Object Detection Overlay** | VLM returns bounding-box JSON; boxes and labels are drawn on the webcam feed |
| 5 | **Command Parsing** | Spoken commands are parsed into structured JSON (`action`, `object`, `color`, `location`, `confidence`) |
| 6 | **Multi-Language Support** | Switch between English, French, Spanish, German, Chinese, Japanese, and Romanian |
| 7 | **Gesture + Speech Fusion** | MediaPipe hand/pose tracking detects pointing, open hand, fist, thumbs up/down — pointed region is cropped and sent to the VLM |

### v3 — ROS2 Virtual Environment (Dockerised)

All the STT + VLM capabilities running on the host, communicating with a **TurtleBot3 Gazebo simulation** inside Docker via **rosbridge WebSocket**. A browser-based **noVNC** desktop lets you see Gazebo and RViz2 in real-time.

| # | Pipeline | Description |
|---|----------|-------------|
| 1 | **Where Am I?** | Robot reports its position and describes its surroundings using odometry + Gazebo camera |
| 2 | **Vision Chat** | Capture images from the virtual environment camera and have a conversation about what the robot sees |
| 3 | **Voice Navigation** | Tell the robot where to go — by name (e.g. *"go to north east"*), by coordinates (e.g. *"go to coordinates 2, 2"*), or by motion (e.g. *"turn left 90 degrees"*) |
| 4 | **Full Conversation** | Combined mode — the robot classifies your intent (navigation, location query, vision, or chat) and acts accordingly |

---

## 🏗️ Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  Microphone  │───▶│  Whisper STT │───▶│  Text Processing │
└──────────────┘    └──────────────┘    └────────┬─────────┘
                                                 │
┌──────────────┐    ┌──────────────┐             ▼
│   Webcam     │───▶│  Frame Enc.  │───▶┌──────────────────┐
└──────────────┘    └──────────────┘    │  Ollama VLM      │
                                        │  (Qwen 2.5 VL)   │
┌──────────────┐    ┌──────────────┐    └────────┬─────────┘
│  MediaPipe   │───▶│  Gesture     │             │
│  Hand + Pose │    │  Recognition │             ▼
└──────────────┘    └──────────────┘    ┌──────────────────┐
                                        │  TTS Engine      │
┌──────────────┐                        │  (pyttsx3)       │
│  OpenWakeWord│                        └──────────────────┘
│  "Hey Jarvis"│
└──────────────┘

v3 ROS2 Architecture (Docker):

┌──────────── macOS HOST ─────────────┐   WebSocket   ┌──── DOCKER ────────┐
│  Whisper → VLM → TTS                │    :9090      │  Gazebo + Nav2     │
│  src/ros_bridge.py  ◄───────────────┼───────────────┼──► rosbridge_suite │
│  src/navigation.py                   │               │  TurtleBot3 camera │
│  demo_ros2.py                        │               │  robot_status_node │
└──────────────────────────────────────┘               └────────────────────┘
```

### Project Structure

```
.
├── demo_cli.py                # v1 CLI application
├── demo_gui.py                # v1 GUI application (Tkinter)
├── demo_cli_v2.py             # v2 CLI application (all 7 features)
├── demo_gui_v2.py             # v2 GUI application (all 7 features)
├── demo_ros2.py               # v3 ROS2 CLI application (Docker + Gazebo)
├── docker-compose.yml         # Docker Compose for ROS2 simulation
├── requirements.txt           # Python dependencies
├── hand_landmarker.task       # MediaPipe hand model (auto-downloaded)
├── pose_landmarker_lite.task  # MediaPipe pose model (auto-downloaded)
├── ros2_docker/               # Docker context for ROS2 simulation
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── rviz_config.rviz       # Pre-configured RViz2 layout
│   └── ros2_ws/src/hri_bridge/   # Custom ROS2 package
│       ├── package.xml
│       ├── CMakeLists.txt
│       ├── launch/sim_nav_bridge.launch.py
│       └── scripts/robot_status_node.py
└── src/
    ├── __init__.py
    ├── config.py              # Shared constants & settings
    ├── audio.py               # Microphone recording & Whisper transcription
    ├── tts.py                 # Text-to-speech via pyttsx3 (direct + subprocess-safe)
    ├── vision.py              # Webcam capture & base64 frame encoding
    ├── vlm.py                 # Ollama VLM interaction & conversation history
    ├── emotion.py             # Keyword-based emotion classification
    ├── detection.py           # Object detection prompt, JSON parsing & bbox drawing
    ├── commands.py            # Robot command parsing (speech → structured JSON)
    ├── wakeword.py            # Wake word detection via openwakeword
    ├── gestures.py            # MediaPipe hand/pose gesture recognition
    ├── ros_bridge.py          # Rosbridge WebSocket client (host ↔ Docker)
    └── navigation.py          # Navigation command parsing & named waypoints
```

---

## 📋 Prerequisites

- **Python 3.10+**
- **Webcam** (built-in or USB) — for v1/v2
- **Microphone**
- **[Ollama](https://ollama.com/)** installed and running locally
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — for v3 (ROS2 demo)

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd ROB2001
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull the VLM model via Ollama

Make sure Ollama is running, then:

```bash
ollama pull qwen2.5vl:3b
```

### 5. (Optional) MediaPipe models

The hand and pose landmarker models (`hand_landmarker.task`, `pose_landmarker_lite.task`) will be **automatically downloaded** on first run if not already present.

---

## ▶️ Usage

### CLI — v1 (Basic)

```bash
python demo_cli.py
```

Select a pipeline from the interactive menu, press **Enter** to record, and press **Enter** again to stop.

### GUI — v1 (Basic)

```bash
python demo_gui.py
```

Choose a pipeline via the radio buttons, then **hold the Record button** to speak.

### CLI — v2 (Extended)

```bash
python demo_cli_v2.py
```

Includes all 7 pipelines plus a **Settings** menu to change language, toggle emotion-aware TTS, and clear conversation history.

### GUI — v2 (Extended)

```bash
python demo_gui_v2.py
```

Full-featured Tkinter interface with:
- Live webcam feed with gesture skeleton overlay and detection bounding boxes
- Pipeline selector (6 pipelines)
- Language selector and emotion-aware TTS toggle
- Wake word toggle (*"Hey Jarvis"*)
- Scrollable conversation log

### CLI — v3 (ROS2 Virtual Environment)

v3 runs the STT + VLM pipeline on your Mac while a **TurtleBot3 Gazebo simulation** runs inside Docker. No ROS2 installation needed on the host.

#### 1. Start the ROS2 simulation

```bash
docker compose up -d
```

This builds and starts the container with:
- **Gazebo** — TurtleBot3 World environment with a camera-equipped robot
- **Nav2** — autonomous navigation stack (path planning + obstacle avoidance)
- **rosbridge_suite** — WebSocket bridge on `ws://localhost:9090`
- **noVNC** — browser-based desktop on `http://localhost:6080`

> ⏳ First build takes ~10–15 minutes (downloads ~3 GB of ROS2 packages). Subsequent starts are fast.

Wait for the container to be healthy:

```bash
docker compose ps   # status should show "healthy"
```

#### 2. Open the visual desktop (Gazebo + RViz2)

Open your browser and go to:

```
http://localhost:6080
```

You will see the Gazebo 3D view and RViz2 running inside the container. This lets you **watch the robot move** as you issue voice commands.

#### 3. Run the demo

```bash
python demo_ros2.py
```

#### 4. Select a pipeline

| # | Pipeline | What it does |
|---|----------|-------------|
| 1 | **Where Am I?** | Robot uses odometry + camera to describe its current location |
| 2 | **Vision Chat** | Ask questions about what the robot sees in Gazebo via the VLM |
| 3 | **Voice Navigation** | Speak commands like *"go to north east"*, *"go to coordinates 2, 2"*, *"turn left"* |
| 4 | **Full Conversation** | Natural conversation — the robot classifies your intent and combines all capabilities |

#### Named navigation locations

The TurtleBot3 World is a ~5 × 5 m arena with cylindrical pillars and wall segments. These are the available named waypoints:

| Location | Coordinates (x, y) | Description |
|----------|-------------------|-------------|
| `spawn` | (−2.0, −0.5) | Starting position (west side) |
| `centre` | (0.55, 0.55) | Open area near the centre |
| `north` | (0.0, 2.0) | North side of the arena |
| `south` | (0.0, −2.0) | South side of the arena |
| `east` | (2.0, 0.0) | East side of the arena |
| `west` | (−2.0, 0.0) | West side of the arena |
| `north_east` | (1.5, 1.5) | North-east corner |
| `north_west` | (−1.5, 1.5) | North-west corner |
| `south_east` | (1.5, −1.5) | South-east corner |
| `south_west` | (−1.5, −1.5) | South-west corner |

You can also say **"go to coordinates X, Y"** with any numeric values (navigable area is roughly ±2.5 m).

#### Example voice commands

```
"Go to north east"            → navigates to (1.5, 1.5)
"Go to coordinates 2 and 2"   → navigates to (2.0, 2.0)
"Move forward 1 metre"        → drives straight 1 m
"Turn left 90 degrees"        → rotates 90° counter-clockwise
"Where are you?"              → reports position + camera description
"Look around"                 → 360° rotation then describes scene
"Come back"                   → returns to spawn
"Stop"                        → halts all motion
```

#### 5. Stop the simulation

```bash
docker compose down
```

---

## ⚙️ Configuration

Key settings are defined in `src/config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `SAMPLE_RATE` | `16000` | Audio sample rate (Whisper expects 16 kHz) |
| `MAX_IMAGE_DIM` | `512` | Max dimension for webcam frames sent to the VLM |
| `MAX_HISTORY_TURNS` | `10` | Conversation memory window size |
| `WAKE_THRESHOLD` | `0.5` | openwakeword detection sensitivity |
| `VLM_MODEL` | `qwen2.5vl:3b` | Ollama vision-language model name |
| `WEBCAM_UPDATE_MS` | `33` | Webcam refresh interval (~30 fps) |

Supported languages: `en`, `fr`, `es`, `de`, `zh`, `ja`, `ro`

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| *"Cannot open webcam"* | Check that no other app is using the camera. Try changing the webcam index in `open_webcam(index=1)`. |
| *Ollama connection error* | Ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull qwen2.5vl:3b`). |
| *No audio captured* | Check your microphone permissions in System Settings and verify `sounddevice` can see your input device (`python -m sounddevice`). |
| *pyttsx3 crashes on macOS with GUI* | The GUI versions run pyttsx3 in a subprocess to avoid the known macOS NSApplication/Tkinter conflict. If issues persist, check your Python version. |
| *Wake word not detecting* | Lower `WAKE_THRESHOLD` in `src/config.py`. Ensure a quiet environment. |
| *Docker build fails* | Ensure Docker Desktop is running and has ≥8 GB RAM allocated. Try `docker compose build --no-cache`. |
| *"Cannot connect to rosbridge"* | Wait ~60 s after `docker compose up`. Check container logs: `docker compose logs -f`. |
| *No camera image in v3* | The Gazebo camera plugin needs a few seconds to initialise. Try the pipeline again after 10 s. |
| *Nav2 not responding* | Nav2 takes ~30 s to fully initialise after Gazebo starts. Check: `docker compose logs ros2_sim \| grep nav2`. |
| *noVNC shows blank screen* | Gazebo/RViz2 take ~60 s to start under emulation. Refresh the page. Check logs: `docker compose logs ros2_sim \| grep vnc`. |
| *noVNC not loading at all* | Verify port 6080 is not in use: `lsof -i :6080`. Ensure the container is healthy: `docker compose ps`. |
| *Coordinates misinterpreted as location name* | Speak coordinates explicitly, e.g. *"go to coordinates 2 and 2"* rather than just *"go to 2, 2"*. |

---

## 📚 Technologies Used

| Component | Library / Tool |
|-----------|---------------|
| Speech-to-Text | [OpenAI Whisper](https://github.com/openai/whisper) |
| Text-to-Speech | [pyttsx3](https://pyttsx3.readthedocs.io/) |
| Vision-Language Model | [Ollama](https://ollama.com/) with [Qwen 2.5 VL](https://huggingface.co/Qwen/Qwen2.5-VL-3B) |
| Webcam & Drawing | [OpenCV](https://opencv.org/) |
| Hand & Pose Tracking | [MediaPipe](https://mediapipe.dev/) |
| Wake Word Detection | [openwakeword](https://github.com/dscripka/openWakeWord) |
| Audio I/O | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| Robot Simulation | [ROS2 Humble](https://docs.ros.org/en/humble/) + [Gazebo](https://gazebosim.org/) (Docker) |
| Autonomous Navigation | [Nav2](https://navigation.ros.org/) |
| ROS2 ↔ Host Bridge | [rosbridge_suite](https://github.com/RobotWebTools/rosbridge_suite) + [websocket-client](https://pypi.org/project/websocket-client/) |

---

## 📄 License

This project is provided for educational purposes as part of the **ROB2001 Communication in Robotics** module.
