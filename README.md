# ROB2001 — Communication in Robotics: HRI Demo

A hands-on Human-Robot Interaction (HRI) demo for the **ROB2001 Communication in Robotics** module. This project showcases how speech, vision, and gesture modalities can be combined to build a multimodal communication interface for a robot.

The demo comes in two versions — **v1** (basic) and **v2** (extended) — each available as both a **CLI** and a **GUI** (Tkinter) application.

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
```

### Project Structure

```
.
├── demo_cli.py                # v1 CLI application
├── demo_gui.py                # v1 GUI application (Tkinter)
├── demo_cli_v2.py             # v2 CLI application (all 7 features)
├── demo_gui_v2.py             # v2 GUI application (all 7 features)
├── requirements.txt           # Python dependencies
├── hand_landmarker.task       # MediaPipe hand model (auto-downloaded)
├── pose_landmarker_lite.task  # MediaPipe pose model (auto-downloaded)
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
    └── gestures.py            # MediaPipe hand/pose gesture recognition
```

---

## 📋 Prerequisites

- **Python 3.10+**
- **Webcam** (built-in or USB)
- **Microphone**
- **[Ollama](https://ollama.com/)** installed and running locally

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

---

## 📄 License

This project is provided for educational purposes as part of the **ROB2001 Communication in Robotics** module.
