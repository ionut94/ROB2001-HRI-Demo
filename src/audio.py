"""Audio recording (CLI) and Whisper speech-to-text."""

import threading

import numpy as np
import sounddevice as sd

from .config import SAMPLE_RATE


def record_audio_interactive() -> np.ndarray:
    """Record until the user presses Enter. CLI-only (blocks on input)."""
    print("  🎙  Recording … press Enter to stop.")
    audio_chunks: list[np.ndarray] = []
    stop_event = threading.Event()

    def callback(indata, frames, time_info, status):
        if not stop_event.is_set():
            audio_chunks.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", callback=callback)
    stream.start()
    input()  # blocks until Enter
    stop_event.set()
    stream.stop()
    stream.close()

    if not audio_chunks:
        return np.zeros(SAMPLE_RATE, dtype="float32")
    return np.concatenate(audio_chunks).squeeze()


def transcribe(model, audio: np.ndarray, language: str = "en") -> str:
    """Transcribe audio with Whisper, with optional language selection."""
    kwargs = {"fp16": False}
    if language != "en":
        kwargs["language"] = language
    result = model.transcribe(audio, **kwargs)
    return result["text"].strip()
