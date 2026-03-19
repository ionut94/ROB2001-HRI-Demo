"""Wake word detection via openwakeword ('Hey Jarvis')."""

import threading

import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model as WakeWordModel

from .config import SAMPLE_RATE, WAKE_THRESHOLD


def create_wake_word_model() -> WakeWordModel:
    """Initialise and return the wake word model (for GUI non-blocking use)."""
    openwakeword.utils.download_models()
    return WakeWordModel(wakeword_models=["hey_jarvis"],
                         inference_framework="onnx")


def wait_for_wake_word() -> bool:
    """Block until wake word is detected. CLI-only.

    Returns True on detection, False on Ctrl+C.
    """
    print("  👂  Listening for wake word ('Hey Jarvis') … Ctrl+C to stop.")
    ww_model = create_wake_word_model()
    detected = threading.Event()
    stop = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if stop.is_set():
            return
        audio_int16 = (indata.squeeze() * 32767).astype(np.int16)
        prediction = ww_model.predict(audio_int16)
        for model_name, score in prediction.items():
            if score > WAKE_THRESHOLD:
                print(f"\n  ✨  Wake word detected! (score={score:.2f})")
                detected.set()

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", callback=audio_callback,
                            blocksize=1280)
    stream.start()
    try:
        while not detected.is_set():
            detected.wait(timeout=0.1)
    except KeyboardInterrupt:
        stop.set()
        stream.stop()
        stream.close()
        return False

    stop.set()
    stream.stop()
    stream.close()
    return True
