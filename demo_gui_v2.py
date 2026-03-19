#!/usr/bin/env python3
"""
ROB2001 — HRI Text-to-Speech Demo v2 (GUI)

Tkinter GUI with all 7 features:
  1. Conversation memory          2. Wake word detection
  3. Emotion-aware TTS            4. Object detection overlay
  5. Command parsing              6. Multi-language support
  7. Gesture + speech fusion

Requirements:
  pip install -r requirements.txt
  ollama pull qwen2.5vl:3b
"""

import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

import cv2
import numpy as np
import sounddevice as sd
from PIL import Image, ImageTk
import whisper
import ollama as ollama_client

from src.config import (SAMPLE_RATE, WEBCAM_UPDATE_MS, VLM_MODEL,
                         LANGUAGE_MAP, WAKE_THRESHOLD)
from src.audio import transcribe
from src.tts import speak_pyttsx3_safe
from src.emotion import classify_emotion
from src.vision import open_webcam, encode_frame_to_base64
from src.vlm import ConversationHistory
from src.detection import DETECTION_PROMPT, parse_detections, draw_detections
from src.commands import COMMAND_SYSTEM_PROMPT, parse_command_json
from src.wakeword import create_wake_word_model
from src.gestures import (create_hand_landmarker, create_pose_landmarker,
                          detect_gestures, draw_skeleton, get_pointed_region)


class HRIDemoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ROB2001 — HRI Speech Demo v2")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # State
        self.recording = False
        self.audio_chunks: list[np.ndarray] = []
        self.stream = None
        self.current_frame = None
        self.cap = None

        # Models
        self.whisper_model = None
        self.mp_hands = None
        self.mp_pose = None

        # Feature state
        self.history = ConversationHistory()
        self.current_detections: list[dict] = []
        self.last_gesture_info: dict = {"gesture": "none"}
        self.wake_active = False
        self.wake_model = None
        self.wake_stream = None

        self._build_ui()
        self._start_webcam()
        self._load_models_async()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: webcam + indicators
        left = ttk.Frame(main, width=640)
        main.add(left, weight=2)
        self.cam_label = ttk.Label(left, text="Webcam loading…")
        self.cam_label.pack(fill=tk.BOTH, expand=True)

        ind_frame = ttk.Frame(left)
        ind_frame.pack(fill=tk.X, padx=5, pady=2)
        self.emotion_var = tk.StringVar(value="Emotion: —")
        ttk.Label(ind_frame, textvariable=self.emotion_var,
                  font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.wake_status_var = tk.StringVar(value="Wake: off")
        ttk.Label(ind_frame, textvariable=self.wake_status_var,
                  font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.gesture_var = tk.StringVar(value="Gesture: —")
        ttk.Label(ind_frame, textvariable=self.gesture_var,
                  font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)

        # Right: controls + log
        right = ttk.Frame(main, width=420)
        main.add(right, weight=1)

        # Pipeline selector
        sel_frame = ttk.LabelFrame(right, text="Pipeline")
        sel_frame.pack(fill=tk.X, padx=5, pady=3)
        self.pipeline_var = tk.StringVar(value="basic")
        for text, val in [("1. Basic STT + TTS", "basic"),
                          ("2. Vision + STT + TTS", "vision"),
                          ("3. Object Detection", "object_detect"),
                          ("4. Command Parsing", "command"),
                          ("5. Wake Word + Vision", "wake_vision"),
                          ("6. Gesture + Speech", "gesture")]:
            ttk.Radiobutton(sel_frame, text=text, variable=self.pipeline_var,
                            value=val).pack(anchor=tk.W, padx=10, pady=1)

        # Settings
        settings_frame = ttk.LabelFrame(right, text="Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=3)

        lang_row = ttk.Frame(settings_frame)
        lang_row.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(lang_row, text="Language:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="en")
        lang_combo = ttk.Combobox(lang_row, textvariable=self.lang_var,
                                  values=list(LANGUAGE_MAP.keys()),
                                  state="readonly", width=5)
        lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_label = ttk.Label(lang_row, text="english")
        self.lang_label.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        self.emotion_tts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Emotion-aware TTS",
                        variable=self.emotion_tts_var).pack(
            anchor=tk.W, padx=5, pady=1)

        self.wake_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Wake Word (Hey Jarvis)",
                        variable=self.wake_var,
                        command=self._toggle_wake).pack(
            anchor=tk.W, padx=5, pady=1)

        # Record button
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X, padx=5, pady=3)
        self.record_btn = ttk.Button(btn_frame, text="Hold to Record",
                                     state=tk.DISABLED)
        self.record_btn.pack(fill=tk.X, ipady=8)
        self.record_btn.bind("<ButtonPress-1>", lambda e: self._start_recording())
        self.record_btn.bind("<ButtonRelease-1>", lambda e: self._stop_recording_and_process())

        self.status_var = tk.StringVar(value="Loading models…")
        ttk.Label(right, textvariable=self.status_var,
                  font=("Helvetica", 10, "italic")).pack(padx=5, pady=2)

        # Conversation log
        log_frame = ttk.LabelFrame(right, text="Conversation")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)
        self.log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                             state=tk.DISABLED,
                                             font=("Helvetica", 10))
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_configure("user", foreground="#0066cc")
        self.log.tag_configure("robot", foreground="#009933")
        self.log.tag_configure("system", foreground="#999999")
        self.log.tag_configure("emotion", foreground="#9933cc")
        self.log.tag_configure("json", foreground="#555555", font=("Courier", 10))
        self.log.tag_configure("gesture", foreground="#cc6600")

        ttk.Button(right, text="Clear History",
                   command=self._clear_history).pack(padx=5, pady=3)

    # ── Webcam ────────────────────────────────────────────────────────────

    def _start_webcam(self):
        try:
            self.cap = open_webcam(warmup_frames=5)
        except RuntimeError:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self._log("System: Could not open webcam.", "system")
        self._update_webcam()

    def _update_webcam(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                display = frame.copy()

                pipeline = self.pipeline_var.get()
                if pipeline == "gesture" and self.mp_hands and self.mp_pose:
                    info, hr, pr = detect_gestures(display, self.mp_hands,
                                                   self.mp_pose)
                    display = draw_skeleton(display, hr, pr)
                    self.last_gesture_info = info
                    self.gesture_var.set(f"Gesture: {info['gesture']}")
                    cv2.putText(display, f"Gesture: {info['gesture']}",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 255, 0), 2)

                if self.current_detections:
                    display = draw_detections(display, self.current_detections)

                rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail((640, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                self.cam_label.configure(image=imgtk, text="")
                self.cam_label.image = imgtk

        self.root.after(WEBCAM_UPDATE_MS, self._update_webcam)

    # ── Model loading ─────────────────────────────────────────────────────

    def _load_models_async(self):
        threading.Thread(target=self._load_models, daemon=True).start()

    def _load_models(self):
        self.whisper_model = whisper.load_model("base")
        self.mp_hands = create_hand_landmarker()
        self.mp_pose = create_pose_landmarker()
        self.root.after(0, self._models_ready)

    def _models_ready(self):
        self.status_var.set("Ready — hold the button to record")
        self.record_btn.configure(state=tk.NORMAL)
        self._log("System: Models loaded. Ready!", "system")

    # ── Language ──────────────────────────────────────────────────────────

    def _on_lang_change(self, event=None):
        lang = self.lang_var.get()
        self.lang_label.configure(text=LANGUAGE_MAP.get(lang, "?"))
        self._log(f"System: Language set to {LANGUAGE_MAP.get(lang, lang)}", "system")

    # ── Wake word ─────────────────────────────────────────────────────────

    def _toggle_wake(self):
        if self.wake_var.get():
            self._start_wake_listener()
        else:
            self._stop_wake_listener()

    def _start_wake_listener(self):
        if self.wake_active:
            return
        self.wake_active = True
        self.wake_status_var.set("Wake: listening…")
        self._log("System: Wake word listening started (say 'Hey Jarvis')", "system")

        def run():
            self.wake_model = create_wake_word_model()

            def audio_cb(indata, frames, time_info, status):
                if not self.wake_active or self.recording:
                    return
                audio_int16 = (indata.squeeze() * 32767).astype(np.int16)
                prediction = self.wake_model.predict(audio_int16)
                for name, score in prediction.items():
                    if score > WAKE_THRESHOLD:
                        self.root.after(0, self._on_wake_detected)

            self.wake_stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                callback=audio_cb, blocksize=1280)
            self.wake_stream.start()

        threading.Thread(target=run, daemon=True).start()

    def _stop_wake_listener(self):
        self.wake_active = False
        if self.wake_stream:
            self.wake_stream.stop()
            self.wake_stream.close()
            self.wake_stream = None
        self.wake_status_var.set("Wake: off")
        self._log("System: Wake word listening stopped", "system")

    def _on_wake_detected(self):
        self.wake_status_var.set("Wake: DETECTED!")
        self._log("System: Wake word detected!", "system")
        self._start_recording()
        self.root.after(5000, self._stop_recording_and_process)

    # ── Recording ─────────────────────────────────────────────────────────

    def _start_recording(self):
        if self.whisper_model is None or self.recording:
            return
        self.recording = True
        self.audio_chunks = []
        self.status_var.set("Recording…")
        self.record_btn.configure(text="Recording…")

        def audio_callback(indata, frames, time_info, status):
            if self.recording:
                self.audio_chunks.append(indata.copy())

        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                     dtype="float32", callback=audio_callback)
        self.stream.start()

    def _stop_recording_and_process(self):
        if not self.recording:
            return
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.record_btn.configure(text="Hold to Record")
        self.status_var.set("Processing…")
        self.wake_status_var.set("Wake: listening…" if self.wake_active else "Wake: off")

        frame_copy = self.current_frame.copy() if self.current_frame is not None else None
        gesture_copy = dict(self.last_gesture_info)

        threading.Thread(target=self._process,
                         args=(frame_copy, gesture_copy), daemon=True).start()

    # ── Processing pipeline ───────────────────────────────────────────────

    def _process(self, frame, gesture_info):
        if not self.audio_chunks:
            self.root.after(0, lambda: self.status_var.set("No audio captured"))
            return

        audio = np.concatenate(self.audio_chunks).squeeze()
        text = transcribe(self.whisper_model, audio, self.lang_var.get())

        if not text:
            self.root.after(0, lambda: self.status_var.set("No speech detected"))
            self.root.after(0, lambda: self._log("System: No speech detected.", "system"))
            return

        pipeline = self.pipeline_var.get()
        if pipeline == "basic":
            self._process_basic(text)
        elif pipeline in ("vision", "wake_vision"):
            self._process_vision(text, frame)
        elif pipeline == "object_detect":
            self._process_object_detect(text, frame)
        elif pipeline == "command":
            self._process_command(text, frame)
        elif pipeline == "gesture":
            self._process_gesture(text, frame, gesture_info)

        self.root.after(0, lambda: self.status_var.set(
            "Ready — hold the button to record"))

    def _process_basic(self, text):
        self.root.after(0, lambda: self._log(f"You: {text}", "user"))
        self.history.add("user", text)
        emotion = classify_emotion(text)
        if self.emotion_tts_var.get() and emotion != "neutral":
            self.root.after(0, lambda: self._log(f"  [Emotion: {emotion}]", "emotion"))
        self.root.after(0, lambda: self.emotion_var.set(f"Emotion: {emotion}"))
        self.root.after(0, lambda: self._log(f"Robot (echo): {text}", "robot"))
        self.history.add("assistant", text)
        speak_pyttsx3_safe(text, language=self.lang_var.get())

    def _process_vision(self, text, frame):
        self.root.after(0, lambda: self._log(f"You: {text}", "user"))
        self.root.after(0, lambda: self.status_var.set("Asking VLM…"))
        if frame is None:
            self.root.after(0, lambda: self._log("System: No webcam frame.", "system"))
            return
        img_b64 = encode_frame_to_base64(frame)
        messages = self.history.get_messages()
        messages.append({"role": "user", "content": text, "images": [img_b64]})
        try:
            response = ollama_client.chat(model=VLM_MODEL, messages=messages)
            answer = response["message"]["content"].strip()
        except Exception as e:
            answer = f"Error: {e}"
        self.history.add("user", text, [img_b64])
        self.history.add("assistant", answer)
        emotion = classify_emotion(answer)
        self.root.after(0, lambda: self.emotion_var.set(f"Emotion: {emotion}"))
        if self.emotion_tts_var.get() and emotion != "neutral":
            self.root.after(0, lambda: self._log(f"  [Emotion: {emotion}]", "emotion"))
        self.root.after(0, lambda: self._log(f"Robot: {answer}", "robot"))
        speak_pyttsx3_safe(answer, language=self.lang_var.get())

    def _process_object_detect(self, text, frame):
        self.root.after(0, lambda: self._log(f"You: {text}", "user"))
        self.root.after(0, lambda: self.status_var.set("Detecting objects…"))
        if frame is None:
            self.root.after(0, lambda: self._log("System: No webcam frame.", "system"))
            return
        img_b64 = encode_frame_to_base64(frame)
        query = text + "\n\n" + DETECTION_PROMPT
        try:
            response = ollama_client.chat(model=VLM_MODEL,
                                          messages=[{"role": "user", "content": query,
                                                     "images": [img_b64]}])
            raw = response["message"]["content"].strip()
        except Exception as e:
            raw = f"Error: {e}"
        detections = parse_detections(raw)
        self.current_detections = detections
        if detections:
            det_text = ", ".join(d.get("label", "?") for d in detections)
            self.root.after(0, lambda: self._log(
                f"Robot: Found {len(detections)} object(s): {det_text}", "robot"))
            speak_pyttsx3_safe(f"I found {len(detections)} objects: {det_text}",
                               language=self.lang_var.get())
        else:
            self.root.after(0, lambda: self._log(f"Robot: {raw}", "robot"))
            speak_pyttsx3_safe("I couldn't identify specific objects with bounding boxes.",
                               language=self.lang_var.get())

    def _process_command(self, text, frame):
        self.root.after(0, lambda: self._log(f"Command: {text}", "user"))
        self.root.after(0, lambda: self.status_var.set("Parsing command…"))
        img_b64 = encode_frame_to_base64(frame) if frame is not None else None
        messages = [{"role": "system", "content": COMMAND_SYSTEM_PROMPT}]
        user_msg = {"role": "user", "content": text}
        if img_b64:
            user_msg["images"] = [img_b64]
        messages.append(user_msg)
        try:
            response = ollama_client.chat(model=VLM_MODEL, messages=messages)
            raw = response["message"]["content"].strip()
        except Exception as e:
            raw = f"Error: {e}"
        parsed = parse_command_json(raw)
        if parsed:
            json_str = json.dumps(parsed, indent=2)
            self.root.after(0, lambda: self._log(f"Parsed command:\n{json_str}", "json"))
            action = parsed.get("action", "unknown")
            obj = parsed.get("object", "") or ""
            speak_pyttsx3_safe(f"Understood: {action} {obj}", language=self.lang_var.get())
        else:
            self.root.after(0, lambda: self._log(f"Robot: {raw}", "robot"))
            speak_pyttsx3_safe("Sorry, I could not parse that command.", language=self.lang_var.get())

    def _process_gesture(self, text, frame, gesture_info):
        gesture = gesture_info.get("gesture", "none")
        self.root.after(0, lambda: self._log(f"You: {text}", "user"))
        self.root.after(0, lambda: self._log(f"  [Gesture: {gesture}]", "gesture"))
        self.root.after(0, lambda: self.status_var.set("Asking VLM…"))
        if frame is None:
            self.root.after(0, lambda: self._log("System: No webcam frame.", "system"))
            return
        send_frame = frame
        if gesture == "pointing":
            cropped = get_pointed_region(frame, gesture_info)
            if cropped is not None:
                self.root.after(0, lambda: self._log(
                    "  Using pointed region for query", "gesture"))
                send_frame = cropped
        img_b64 = encode_frame_to_base64(send_frame)
        context = f"[User gesture: {gesture}] {text}"
        messages = self.history.get_messages()
        messages.append({"role": "user", "content": context, "images": [img_b64]})
        try:
            response = ollama_client.chat(model=VLM_MODEL, messages=messages)
            answer = response["message"]["content"].strip()
        except Exception as e:
            answer = f"Error: {e}"
        self.history.add("user", context, [img_b64])
        self.history.add("assistant", answer)
        emotion = classify_emotion(answer)
        self.root.after(0, lambda: self.emotion_var.set(f"Emotion: {emotion}"))
        self.root.after(0, lambda: self._log(f"Robot: {answer}", "robot"))
        speak_pyttsx3_safe(answer, language=self.lang_var.get())

    # ── History ───────────────────────────────────────────────────────────

    def _clear_history(self):
        self.history.clear()
        self.current_detections.clear()
        self._log("System: Conversation history cleared.", "system")

    # ── Log helper ────────────────────────────────────────────────────────

    def _log(self, message: str, tag: str = ""):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n", tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    # ── Cleanup ───────────────────────────────────────────────────────────

    def on_close(self):
        self.wake_active = False
        if self.wake_stream:
            self.wake_stream.stop()
            self.wake_stream.close()
        if self.cap:
            self.cap.release()
        if self.mp_hands:
            self.mp_hands.close()
        if self.mp_pose:
            self.mp_pose.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    root.geometry("1200x700")
    HRIDemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
