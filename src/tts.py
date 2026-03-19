"""Text-to-speech backends.

- speak_pyttsx3(): Offline, works in CLI. Do NOT use from Tkinter on macOS.
- speak_gtts(): Cross-platform, requires internet. Safe with Tkinter.
"""

import io

import pyttsx3

from .config import LANGUAGE_MAP


# ── pyttsx3 backend (CLI) ────────────────────────────────────────────────────

def speak_pyttsx3(text: str, rate: int = 175, language: str = "en"):
    """Speak text via pyttsx3. Creates a fresh engine each call (macOS safety)."""
    print(f"  🔊  Robot says: {text}")
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    if language != "en":
        lang_name = LANGUAGE_MAP.get(language, "")
        voices = engine.getProperty("voices")
        for v in voices:
            if lang_name.lower() in v.name.lower() or language in v.id.lower():
                engine.setProperty("voice", v.id)
                break

    engine.say(text)
    engine.runAndWait()
    engine.stop()


# ── gTTS + pygame backend (GUI) ──────────────────────────────────────────────

def init_pygame_mixer():
    """Initialise pygame mixer. Call once at GUI startup."""
    import pygame
    pygame.mixer.init()


def quit_pygame_mixer():
    """Shut down pygame mixer. Call on GUI close."""
    import pygame
    pygame.mixer.quit()


def speak_gtts(text: str, language: str = "en"):
    """Speak text via Google TTS + pygame. Cross-platform, no Tkinter conflict."""
    import pygame
    from gtts import gTTS

    try:
        tts = gTTS(text=text, lang=language)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        pygame.mixer.music.load(buf, "mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)
    except Exception as e:
        print(f"  ⚠  TTS error: {e}")
