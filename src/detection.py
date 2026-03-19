"""Object detection via VLM — prompt, JSON parsing, and bbox drawing."""

import json
import re

import cv2
import numpy as np

DETECTION_PROMPT = """List every distinct object visible in this image.
For each object return a JSON element: {"label": "short name", "bbox": [x1, y1, x2, y2]}
where x1, y1 is the TOP-LEFT corner and x2, y2 is the BOTTOM-RIGHT corner,
all as integer percentages 0-100 of the image width (x) and height (y).
Be precise: the box should tightly fit each object.
Return ONLY a JSON array, no markdown fences, no explanation.
Example: [{"label":"cup","bbox":[10,40,25,70]},{"label":"laptop","bbox":[30,10,80,60]}]"""


def parse_detections(vlm_response: str) -> list[dict]:
    """Parse bounding box JSON from VLM response."""
    cleaned = re.sub(r'```(?:json)?\s*', '', vlm_response)
    cleaned = cleaned.replace('```', '').strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return []


def draw_detections(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    """Draw bounding boxes and labels on frame. Returns annotated copy."""
    h, w = frame.shape[:2]
    annotated = frame.copy()
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
              (255, 0, 255), (0, 255, 255)]
    for i, det in enumerate(detections):
        try:
            bbox = det["bbox"]
            label = det.get("label", "?")
            x1 = int(bbox[0] / 100 * w)
            y1 = int(bbox[1] / 100 * h)
            x2 = int(bbox[2] / 100 * w)
            y2 = int(bbox[3] / 100 * h)
            color = colors[i % len(colors)]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        except (KeyError, IndexError, TypeError):
            continue
    return annotated
