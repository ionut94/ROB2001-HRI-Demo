"""MediaPipe gesture detection — hand + pose tracking, skeleton drawing."""

import os
import urllib.request

import cv2
import numpy as np
import mediapipe as mp

# ── Model paths (relative to project root) ────────────────────────────────────

_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
HAND_MODEL_PATH = os.path.join(_PROJECT_ROOT, "hand_landmarker.task")
POSE_MODEL_PATH = os.path.join(_PROJECT_ROOT, "pose_landmarker_lite.task")

_HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
_POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

# ── MediaPipe task API aliases ────────────────────────────────────────────────

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode
HandConnections = mp.tasks.vision.HandLandmarksConnections
PoseConnections = mp.tasks.vision.PoseLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils


# ── Setup ─────────────────────────────────────────────────────────────────────

def ensure_mp_models():
    """Download MediaPipe model files if not present."""
    for path, url in [(HAND_MODEL_PATH, _HAND_MODEL_URL),
                      (POSE_MODEL_PATH, _POSE_MODEL_URL)]:
        if not os.path.exists(path):
            print(f"  Downloading {os.path.basename(path)} …")
            urllib.request.urlretrieve(url, path)


def create_hand_landmarker():
    ensure_mp_models()
    return HandLandmarker.create_from_options(HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL_PATH),
        running_mode=RunningMode.IMAGE, num_hands=1))


def create_pose_landmarker():
    ensure_mp_models()
    return PoseLandmarker.create_from_options(PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=POSE_MODEL_PATH),
        running_mode=RunningMode.IMAGE))


# ── Detection ─────────────────────────────────────────────────────────────────

def detect_gestures(frame: np.ndarray, hand_landmarker, pose_landmarker):
    """Run MediaPipe hands + pose on a frame.

    Returns (gesture_info_dict, hand_result, pose_result).
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    hand_result = hand_landmarker.detect(mp_image)
    pose_result = pose_landmarker.detect(mp_image)

    info = {
        "hand_detected": False,
        "pose_detected": False,
        "gesture": "none",
        "pointing_tip": None,
        "pointing_dir": None,
    }

    if hand_result.hand_landmarks:
        info["hand_detected"] = True
        lm = hand_result.hand_landmarks[0]

        tip = lm[8]   # index finger tip
        mcp = lm[5]   # index finger MCP
        info["pointing_tip"] = (tip.x, tip.y)
        info["pointing_dir"] = (tip.x - mcp.x, tip.y - mcp.y)

        fingertips = [8, 12, 16, 20]
        mcps = [5, 9, 13, 17]
        fingers_up = sum(1 for ft, mc in zip(fingertips, mcps)
                         if lm[ft].y < lm[mc].y)

        if fingers_up == 0:
            info["gesture"] = "closed_fist"
        elif fingers_up == 1 and lm[8].y < lm[5].y:
            info["gesture"] = "pointing"
        elif fingers_up >= 4:
            info["gesture"] = "open_hand"
        else:
            info["gesture"] = "other"

        thumb_tip = lm[4]
        thumb_ip = lm[3]
        if fingers_up == 0 and thumb_tip.y < thumb_ip.y - 0.05:
            info["gesture"] = "thumbs_up"
        elif fingers_up == 0 and thumb_tip.y > thumb_ip.y + 0.05:
            info["gesture"] = "thumbs_down"

    if pose_result.pose_landmarks:
        info["pose_detected"] = True

    return info, hand_result, pose_result


def draw_skeleton(frame: np.ndarray, hand_result, pose_result) -> np.ndarray:
    """Draw MediaPipe skeleton overlays on frame. Returns annotated copy."""
    annotated = frame.copy()
    if hand_result.hand_landmarks:
        for hand_lms in hand_result.hand_landmarks:
            mp_drawing.draw_landmarks(annotated, hand_lms,
                                      HandConnections.HAND_CONNECTIONS)
    if pose_result.pose_landmarks:
        for pose_lms in pose_result.pose_landmarks:
            mp_drawing.draw_landmarks(annotated, pose_lms,
                                      PoseConnections.POSE_LANDMARKS)
    return annotated


def get_pointed_region(frame: np.ndarray, gesture_info: dict) -> np.ndarray | None:
    """Crop the region the user is pointing at (~200×200 px)."""
    if gesture_info["pointing_tip"] is None:
        return None
    h, w = frame.shape[:2]
    tip_x = int(gesture_info["pointing_tip"][0] * w)
    tip_y = int(gesture_info["pointing_tip"][1] * h)

    if gesture_info["pointing_dir"]:
        dx, dy = gesture_info["pointing_dir"]
        mag = max((dx**2 + dy**2) ** 0.5, 0.001)
        tip_x += int(dx / mag * 150)
        tip_y += int(dy / mag * 150)

    size = 100
    x1 = max(0, tip_x - size)
    y1 = max(0, tip_y - size)
    x2 = min(w, tip_x + size)
    y2 = min(h, tip_y + size)

    if x2 - x1 < 50 or y2 - y1 < 50:
        return None
    return frame[y1:y2, x1:x2]
