#!/usr/bin/env python3
"""
ROB2001 — HRI Text-to-Speech Demo (GUI version)

Tkinter GUI with:
  - Live webcam feed on the left
  - Pipeline selector, record button, and conversation log on the right

Requirements:
  pip install -r requirements.txt
  ollama pull qwen2.5vl:3b
"""

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

import cv2
import numpy as np
import sounddevice as sd
from PIL import Image, ImageTk
import whisper

from src.config import SAMPLE_RATE, WEBCAM_UPDATE_MS
from src.audio import transcribe
from src.tts import speak_pyttsx3_safe
from src.vision import open_webcam, encode_frame_to_base64
from src.vlm import ask_vlm


class HRIDemoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ROB2001 — HRI Speech Demo")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.recording = False
        self.audio_chunks: list[np.ndarray] = []
        self.stream = None
        self.current_frame = None
        self.cap = None
        self.whisper_model = None

        self._build_ui()
        self._start_webcam()
        self._load_models_async()

    def _build_ui(self):
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(main, width=640, height=480)
        main.add(left, weight=1)
        self.cam_label = ttk.Label(left, text="Webcam loading…")
        self.cam_label.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(main, width=400)
        main.add(right, weight=1)

        sel_frame = ttk.LabelFrame(right, text="Pipeline")
        sel_frame.pack(fill=tk.X, padx=5, pady=5)
        self.pipeline_var = tk.StringVar(value="basic")
        ttk.Radiobutton(sel_frame, text="1. Basic STT + TTS",
                        variable=self.pipeline_var, value="basic").pack(
            anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(sel_frame, text="2. Vision + STT + TTS",
                        variable=self.pipeline_var, value="vision").pack(
            anchor=tk.W, padx=10, pady=2)

        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.record_btn = ttk.Button(btn_frame, text="Hold to Record",
                                     state=tk.DISABLED)
        self.record_btn.pack(fill=tk.X, ipady=10)
        self.record_btn.bind("<ButtonPress-1>", self._on_record_press)
        self.record_btn.bind("<ButtonRelease-1>", self._on_record_release)

        self.status_var = tk.StringVar(value="Loading models…")
        ttk.Label(right, textvariable=self.status_var,
                  font=("Helvetica", 11, "italic")).pack(padx=5, pady=(0, 5))

        log_frame = ttk.LabelFrame(right, text="Conversation")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                             state=tk.DISABLED,
                                             font=("Helvetica", 11))
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.tag_configure("user", foreground="#0066cc")
        self.log.tag_configure("robot", foreground="#009933")
        self.log.tag_configure("system", foreground="#999999")

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
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail((640, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                self.cam_label.configure(image=imgtk, text="")
                self.cam_label.image = imgtk
        self.root.after(WEBCAM_UPDATE_MS, self._update_webcam)

    def _load_models_async(self):
        threading.Thread(target=self._load_models, daemon=True).start()

    def _load_models(self):
        self.whisper_model = whisper.load_model("base")
        self.root.after(0, self._models_ready)

    def _models_ready(self):
        self.status_var.set("Ready — hold the button to record")
        self.record_btn.configure(state=tk.NORMAL)
        self._log("System: Models loaded. Ready!", "system")

    def _on_record_press(self, event):
        if self.whisper_model is None:
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

    def _on_record_release(self, event):
        if not self.recording:
            return
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.record_btn.configure(text="Hold to Record")
        self.status_var.set("Processing…")
        frame_copy = self.current_frame.copy() if self.current_frame is not None else None
        threading.Thread(target=self._process, args=(frame_copy,), daemon=True).start()

    def _process(self, frame):
        if not self.audio_chunks:
            self.root.after(0, lambda: self.status_var.set("No audio captured"))
            return

        audio = np.concatenate(self.audio_chunks).squeeze()
        text = transcribe(self.whisper_model, audio)

        if not text:
            self.root.after(0, lambda: self.status_var.set("No speech detected"))
            self.root.after(0, lambda: self._log("System: No speech detected.", "system"))
            return

        pipeline = self.pipeline_var.get()

        if pipeline == "basic":
            self.root.after(0, lambda: self._log(f"You: {text}", "user"))
            self.root.after(0, lambda: self.status_var.set("Speaking…"))
            self.root.after(0, lambda: self._log(f"Robot (echo): {text}", "robot"))
            speak_pyttsx3_safe(text)
        else:
            self.root.after(0, lambda: self._log(f"You: {text}", "user"))
            self.root.after(0, lambda: self.status_var.set("Asking VLM…"))
            if frame is None:
                self.root.after(0, lambda: self._log(
                    "System: No webcam frame available.", "system"))
                self.root.after(0, lambda: self.status_var.set("Ready"))
                return
            img_b64 = encode_frame_to_base64(frame)
            try:
                answer = ask_vlm(img_b64, text)
            except Exception as e:
                answer = f"Error contacting Ollama: {e}"
            self.root.after(0, lambda: self._log(f"Robot: {answer}", "robot"))
            self.root.after(0, lambda: self.status_var.set("Speaking…"))
            speak_pyttsx3_safe(answer)

        self.root.after(0, lambda: self.status_var.set(
            "Ready — hold the button to record"))

    def _log(self, message: str, tag: str = ""):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n", tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def on_close(self):
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    root = tk.Tk()
    root.geometry("1100x600")
    HRIDemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
