"""Shared constants for the ROB2001 HRI demo."""

SAMPLE_RATE = 16000          # Whisper expects 16 kHz
MAX_IMAGE_DIM = 512          # Resize large webcam frames for faster VLM inference
MAX_HISTORY_TURNS = 10       # Keep last N user+assistant pairs
WAKE_THRESHOLD = 0.5         # openwakeword detection threshold
VLM_MODEL = "qwen2.5vl:3b"  # Ollama vision-language model
WEBCAM_UPDATE_MS = 33        # ~30 fps for GUI webcam refresh

LANGUAGE_MAP = {
    "en": "english",
    "fr": "french",
    "es": "spanish",
    "de": "german",
    "zh": "chinese",
    "ja": "japanese",
    "ro": "romanian",
}
