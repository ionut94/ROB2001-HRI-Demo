#!/usr/bin/env python3
"""
ROB2001 — HRI Text-to-Speech Demo v2 (CLI)

Extended demo with 7 features:
  1. Conversation memory    2. Wake word detection
  3. Emotion-aware TTS      4. Object detection overlay
  5. Command parsing        6. Multi-language support
  7. Gesture + speech fusion

Requirements:
  pip install -r requirements.txt
  ollama pull qwen2.5vl:3b
"""

import json
import threading

import cv2
import whisper

from src.config import LANGUAGE_MAP
from src.audio import record_audio_interactive, transcribe
from src.tts import speak_pyttsx3
from src.emotion import classify_emotion, get_emotion_rate
from src.vision import open_webcam, capture_frame, encode_frame_to_base64
from src.vlm import ask_vlm, ConversationHistory
from src.detection import DETECTION_PROMPT, parse_detections, draw_detections
from src.commands import COMMAND_SYSTEM_PROMPT, parse_command_json
from src.wakeword import wait_for_wake_word
from src.gestures import (create_hand_landmarker, create_pose_landmarker,
                          detect_gestures, draw_skeleton, get_pointed_region)

# ── State ────────────────────────────────────────────────────────────────────

history = ConversationHistory()
settings = {"language": "en", "emotion_tts": True}


def speak(text: str, emotion: str = "neutral"):
    if settings["emotion_tts"] and emotion != "neutral":
        print(f"  🎭  Emotion: {emotion}")
    rate = get_emotion_rate(emotion) if settings["emotion_tts"] else 175
    speak_pyttsx3(text, rate=rate, language=settings["language"])


# ── Pipelines ────────────────────────────────────────────────────────────────

def pipeline_basic(whisper_model):
    print("\n═══ Pipeline 1: Basic STT + TTS ═══")
    print("Speak and the system will transcribe and repeat your words.")
    print("Conversation memory is active. Type 'q' to quit.\n")
    while True:
        cmd = input("Press Enter to record (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break
        audio = record_audio_interactive()
        text = transcribe(whisper_model, audio, settings["language"])
        if not text:
            print("  (no speech detected)")
            continue
        print(f"  📝  You said: {text}")
        history.add("user", text)
        emotion = classify_emotion(text)
        speak(text, emotion)
        history.add("assistant", text)


def pipeline_vision(whisper_model):
    print("\n═══ Pipeline 2: Vision + STT + TTS ═══")
    print("Ask the robot what it sees! Conversation memory is active.")
    print("Type 'q' to quit.\n")
    try:
        cap = open_webcam()
    except RuntimeError as e:
        print(f"  ⚠  {e}")
        return
    while True:
        cmd = input("Press Enter to ask (or 'q' to quit): ").strip()
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
        question = transcribe(whisper_model, audio, settings["language"])
        if not question:
            print("  (no speech detected)")
            continue
        print(f"  📝  You asked: {question}")
        answer = ask_vlm(img_b64, question, history=history)
        emotion = classify_emotion(answer)
        speak(answer, emotion)
    cap.release()
    cv2.destroyAllWindows()


def pipeline_object_detection(whisper_model):
    print("\n═══ Pipeline 3: Object Detection Overlay ═══")
    print("The robot will detect objects and draw bounding boxes.")
    print("Type 'q' to quit.\n")
    try:
        cap = open_webcam()
    except RuntimeError as e:
        print(f"  ⚠  {e}")
        return
    while True:
        cmd = input("Press Enter to detect objects (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break
        try:
            frame, img_b64 = capture_frame(cap)
        except RuntimeError as e:
            print(f"  ⚠  Webcam error: {e}")
            continue
        cv2.imshow("Object Detection", frame)
        cv2.waitKey(1)
        print("  (speak a question or just press Enter for default detection)")
        audio = record_audio_interactive()
        question = transcribe(whisper_model, audio, settings["language"])
        if not question:
            question = "What objects do you see?"
        print(f"  📝  Query: {question}")
        raw = ask_vlm(img_b64, question + "\n\n" + DETECTION_PROMPT)
        detections = parse_detections(raw)
        if detections:
            print(f"  📦  Found {len(detections)} object(s):")
            for d in detections:
                print(f"      - {d.get('label', '?')}: {d.get('bbox', [])}")
            annotated = draw_detections(frame, detections)
        else:
            print(f"  📝  VLM response: {raw}")
            annotated = frame
        cv2.imshow("Object Detection", annotated)
        cv2.waitKey(1)
    cap.release()
    cv2.destroyAllWindows()


def pipeline_command_parsing(whisper_model):
    print("\n═══ Pipeline 4: Command Parsing ═══")
    print("Speak robot commands and they'll be parsed into structured JSON.")
    print("Type 'q' to quit.\n")
    while True:
        cmd = input("Press Enter to give a command (or 'q' to quit): ").strip()
        if cmd.lower() == "q":
            break
        img_b64 = None
        try:
            cap = open_webcam()
            _, img_b64 = capture_frame(cap)
            cap.release()
        except RuntimeError:
            pass
        audio = record_audio_interactive()
        command_text = transcribe(whisper_model, audio, settings["language"])
        if not command_text:
            print("  (no speech detected)")
            continue
        print(f"  📝  Command: {command_text}")
        raw = ask_vlm(img_b64, command_text, system_prompt=COMMAND_SYSTEM_PROMPT)
        parsed = parse_command_json(raw)
        if parsed:
            print("  🤖  Parsed command:")
            print(f"      {json.dumps(parsed, indent=2)}")
            speak(f"Understood: {parsed.get('action', 'unknown')} "
                  f"{parsed.get('object', '') or ''}", "neutral")
        else:
            print(f"  ⚠  Could not parse: {raw}")
            speak("Sorry, I could not parse that command.", "negative")


def pipeline_wake_word(whisper_model):
    print("\n═══ Pipeline 5: Wake Word + Vision ═══")
    print("Say 'Hey Jarvis' to activate, then ask your question.")
    print("Ctrl+C to return to menu.\n")
    try:
        cap = open_webcam()
    except RuntimeError as e:
        print(f"  ⚠  {e}")
        return
    while True:
        if not wait_for_wake_word():
            break
        try:
            frame, img_b64 = capture_frame(cap)
        except RuntimeError as e:
            print(f"  ⚠  Webcam error: {e}")
            continue
        cv2.imshow("Robot View", frame)
        cv2.waitKey(1)
        audio = record_audio_interactive()
        question = transcribe(whisper_model, audio, settings["language"])
        if not question:
            print("  (no speech detected)")
            continue
        print(f"  📝  You asked: {question}")
        answer = ask_vlm(img_b64, question, history=history)
        emotion = classify_emotion(answer)
        speak(answer, emotion)
        print()
    cap.release()
    cv2.destroyAllWindows()


def pipeline_gesture(whisper_model):
    print("\n═══ Pipeline 6: Gesture + Speech Fusion ═══")
    print("Point at objects while asking questions!")
    print("The robot will focus on the region you're pointing at.")
    print("Type 'q' to quit.\n")
    try:
        cap = open_webcam()
    except RuntimeError as e:
        print(f"  ⚠  {e}")
        return
    hands = create_hand_landmarker()
    pose = create_pose_landmarker()
    print("  Live skeleton feed running. Press Enter in terminal to ask.")
    print("  (cv2 window for skeleton view; terminal for input)\n")
    input_queue: list[str] = []
    input_done = threading.Event()
    def input_loop():
        while not input_done.is_set():
            try:
                line = input()
                input_queue.append(line.strip())
            except EOFError:
                input_queue.append("q")
                break
    threading.Thread(target=input_loop, daemon=True).start()
    processing = False
    print("Press Enter to ask (or type 'q' + Enter to quit):")
    while True:
        ret, frame = cap.read()
        if ret and not processing:
            gesture_info, hr, pr = detect_gestures(frame, hands, pose)
            annotated = draw_skeleton(frame, hr, pr)
            cv2.putText(annotated, f"Gesture: {gesture_info['gesture']}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Gesture View", annotated)
        key = cv2.waitKey(33) & 0xFF
        if key == ord('q'):
            break
        if input_queue:
            cmd = input_queue.pop(0)
            if cmd.lower() == "q":
                break
            processing = True
            ret, frame = cap.read()
            if not ret:
                print("  ⚠  Failed to grab frame")
                processing = False
                continue
            gesture_info, hr, pr = detect_gestures(frame, hands, pose)
            print(f"  🤚  Gesture: {gesture_info['gesture']}")
            audio = record_audio_interactive()
            question = transcribe(whisper_model, audio, settings["language"])
            if not question:
                print("  (no speech detected)")
                processing = False
                print("\nPress Enter to ask (or type 'q' + Enter to quit):")
                continue
            print(f"  📝  You asked: {question}")
            send_frame = frame
            if gesture_info["gesture"] == "pointing":
                cropped = get_pointed_region(frame, gesture_info)
                if cropped is not None:
                    print("  👉  Using pointed region for VLM query")
                    send_frame = cropped
                    cv2.imshow("Pointed Region", cropped)
                    cv2.waitKey(1)
            img_b64 = encode_frame_to_base64(send_frame)
            context = f"[User gesture: {gesture_info['gesture']}] {question}"
            answer = ask_vlm(img_b64, context, history=history)
            emotion = classify_emotion(answer)
            speak(answer, emotion)
            processing = False
            print("\nPress Enter to ask (or type 'q' + Enter to quit):")
    input_done.set()
    cap.release()
    hands.close()
    pose.close()
    cv2.destroyAllWindows()


# ── Settings ─────────────────────────────────────────────────────────────────

def settings_menu():
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


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════╗")
    print("║   ROB2001 — HRI Speech Demo v2 (CLI)          ║")
    print("╚═══════════════════════════════════════════════╝")
    print("\nLoading Whisper model (base) …")
    whisper_model = whisper.load_model("base")
    print("Whisper ready.\n")
    while True:
        print("Select a pipeline:")
        print("  1) Basic STT + TTS (with memory)")
        print("  2) Vision + STT + TTS (with memory)")
        print("  3) Object Detection Overlay")
        print("  4) Command Parsing")
        print("  5) Wake Word + Vision (hands-free)")
        print("  6) Gesture + Speech Fusion")
        print("  s) Settings")
        print("  q) Quit")
        choice = input("\n> ").strip()
        if choice == "1": pipeline_basic(whisper_model)
        elif choice == "2": pipeline_vision(whisper_model)
        elif choice == "3": pipeline_object_detection(whisper_model)
        elif choice == "4": pipeline_command_parsing(whisper_model)
        elif choice == "5": pipeline_wake_word(whisper_model)
        elif choice == "6": pipeline_gesture(whisper_model)
        elif choice.lower() == "s": settings_menu()
        elif choice.lower() == "q": print("Goodbye!"); break
        else: print("Invalid choice, try again.\n")


if __name__ == "__main__":
    main()
