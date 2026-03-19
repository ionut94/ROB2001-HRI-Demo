"""Text-to-speech backends.

- speak_pyttsx3():      Offline, direct call. Fine for CLI scripts.
- speak_pyttsx3_safe(): Offline, runs pyttsx3 in a subprocess so it is safe
                        to call from Tkinter on macOS (avoids NSApplication
                        / run-loop conflicts). Used by the GUI demos.

Both produce the same system voice — no gTTS / internet required.
"""

import subprocess
import sys
import textwrap

import pyttsx3

from .config import LANGUAGE_MAP


# ── pyttsx3 backend (direct — CLI) ───────────────────────────────────────────

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


# ── pyttsx3 backend (subprocess — GUI-safe) ──────────────────────────────────

def speak_pyttsx3_safe(text: str, rate: int = 175, language: str = "en"):
    """Speak text via pyttsx3 in a child process.

    This avoids the macOS conflict between pyttsx3's NSApplication run-loop
    and Tkinter's main loop, while producing the exact same system voice as
    the CLI backend.
    """
    # Build a small self-contained script that the subprocess will execute.
    script = textwrap.dedent(f"""\
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", {rate})
        language = {language!r}
        if language != "en":
            lang_map = {dict(LANGUAGE_MAP)!r}
            lang_name = lang_map.get(language, "")
            voices = engine.getProperty("voices")
            for v in voices:
                if lang_name.lower() in v.name.lower() or language in v.id.lower():
                    engine.setProperty("voice", v.id)
                    break
        engine.say({text!r})
        engine.runAndWait()
        engine.stop()
    """)
    try:
        subprocess.run(
            [sys.executable, "-c", script],
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("  ⚠  TTS subprocess timed out")
