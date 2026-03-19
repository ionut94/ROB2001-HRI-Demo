"""Webcam capture and frame encoding for Qwen VL."""

import base64

import cv2
import numpy as np

from .config import MAX_IMAGE_DIM


def _round_to_28(dim: int) -> int:
    """Round dimension down to nearest multiple of 28 (Qwen VL patch size)."""
    return max(28, (dim // 28) * 28)


def open_webcam(index: int = 0, warmup_frames: int = 15) -> cv2.VideoCapture:
    """Open webcam and discard initial frames so auto-exposure settles."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")
    for _ in range(warmup_frames):
        cap.read()
    return cap


def capture_frame(cap: cv2.VideoCapture) -> tuple[np.ndarray, str]:
    """Capture a frame, resize (28-divisible), return (bgr_frame, base64_jpg)."""
    if not cap.isOpened():
        raise RuntimeError("Webcam is not open")
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to grab frame")

    h, w = frame.shape[:2]
    if max(h, w) > MAX_IMAGE_DIM:
        scale = MAX_IMAGE_DIM / max(h, w)
        new_w = _round_to_28(int(w * scale))
        new_h = _round_to_28(int(h * scale))
    else:
        new_w = _round_to_28(w)
        new_h = _round_to_28(h)

    frame = cv2.resize(frame, (new_w, new_h))

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    b64 = base64.b64encode(buf).decode("utf-8")
    return frame, b64


def encode_frame_to_base64(frame: np.ndarray) -> str:
    """Resize an arbitrary frame (e.g. gesture crop) and encode to base64 JPEG."""
    h, w = frame.shape[:2]
    if max(h, w) > MAX_IMAGE_DIM:
        scale = MAX_IMAGE_DIM / max(h, w)
        new_w = _round_to_28(int(w * scale))
        new_h = _round_to_28(int(h * scale))
        frame = cv2.resize(frame, (new_w, new_h))

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")
