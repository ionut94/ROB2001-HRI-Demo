#!/usr/bin/env python3
"""
ROB2001 — HRI Text-to-Speech Demo (CLI version)

Two pipelines:
  1. Basic STT + TTS: speak → transcribe → speak back
  2. Vision + STT + TTS: speak a question → capture webcam frame →
     VLM describes the scene → response spoken aloud

Requirements:
  pip install -r requirements.txt
  ollama pull qwen2.5vl:3b
"""

import cv2
import whisper

from src.audio import record_audio_interactive, transcribe
from src.tts import speak_pyttsx3
from src.vision import open_webcam, capture_frame
from src.vlm import ask_vlm


# ── Pipelines ────────────────────────────────────────────────────────────────

def pipeline_basic(whisper_model):
    """Pipeline 1: Basic STT ↔ TTS loop."""
    print("\n═══ Pipeline 1: Basic STT + TTS ═══")
    print("Speak into the microphone and the system will transcribe and")
    print("repeat your words back. Type 'q' to return to the menu.\n")

    while True:
        cmd = input("Press Enter to record (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        audio = record_audio_interactive()
        text = transcribe(whisper_model, audio)

        if not text:
            print("  (no speech detected)")
            continue

        print(f"  📝  You said: {text}")
        speak_pyttsx3(text)


def pipeline_vision(whisper_model):
    """Pipeline 2: Vision + STT + TTS loop."""
    print("\n═══ Pipeline 2: Vision + STT + TTS ═══")
    print("Ask the robot what it sees! Speak a question and the robot will")
    print("capture a frame, analyse it, and respond aloud.")
    print("Type 'q' to return to the menu.\n")

    try:
        cap = open_webcam()
    except RuntimeError as e:
        print(f"  ⚠  {e}")
        return

    while True:
        cmd = input("Press Enter to ask the robot (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break

        try:
            frame, img_b64 = capture_frame(cap)
        except RuntimeError as e:
            print(f"  ⚠  Webcam error: {e}")
            continue

        cv2.imshow("Robot View", frame)
        cv2.waitKey(1)

        audio = record_audio_interactive()
        question = transcribe(whisper_model, audio)

        if not question:
            print("  (no speech detected)")
            continue

        print(f"  📝  You asked: {question}")
        answer = ask_vlm(img_b64, question)
        speak_pyttsx3(answer)

    cap.release()
    cv2.destroyAllWindows()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   ROB2001 — HRI Speech Demo (CLI)        ║")
    print("╚══════════════════════════════════════════╝")

    print("\nLoading Whisper model (base) …")
    whisper_model = whisper.load_model("base")
    print("Whisper ready.\n")

    while True:
        print("Select a pipeline:")
        print("  1) Basic STT + TTS")
        print("  2) Vision + STT + TTS (requires webcam + Ollama)")
        print("  q) Quit")
        choice = input("\n> ").strip()

        if choice == "1":
            pipeline_basic(whisper_model)
        elif choice == "2":
            pipeline_vision(whisper_model)
        elif choice.lower() == "q":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.\n")


if __name__ == "__main__":
    main()
