"""Tests for src/vision.py — frame encoding and helper functions."""

import base64

import cv2
import numpy as np
import pytest

from src.vision import _round_to_28, encode_frame_to_base64, capture_frame
from src.config import MAX_IMAGE_DIM


class TestRoundTo28:
    def test_exact_multiple(self):
        assert _round_to_28(280) == 280

    def test_rounds_down(self):
        assert _round_to_28(300) == 280

    def test_minimum_is_28(self):
        assert _round_to_28(10) == 28
        assert _round_to_28(0) == 28

    def test_28_itself(self):
        assert _round_to_28(28) == 28

    def test_just_above_28(self):
        assert _round_to_28(29) == 28

    def test_large_value(self):
        assert _round_to_28(1000) == 980  # 35*28=980

    def test_result_divisible_by_28(self):
        for dim in [50, 100, 200, 333, 500, 512, 640, 1920]:
            result = _round_to_28(dim)
            assert result % 28 == 0


class TestEncodeFrameToBase64:
    def _make_frame(self, w=200, h=150):
        """Create a synthetic BGR frame."""
        return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

    def test_returns_base64_string(self):
        frame = self._make_frame()
        result = encode_frame_to_base64(frame)
        assert isinstance(result, str)
        # Should be valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_decodes_to_valid_jpeg(self):
        frame = self._make_frame()
        b64 = encode_frame_to_base64(frame)
        jpg_bytes = base64.b64decode(b64)
        # JPEG files start with FF D8
        assert jpg_bytes[:2] == b'\xff\xd8'

    def test_small_frame_not_resized_beyond_max(self):
        frame = self._make_frame(100, 100)
        b64 = encode_frame_to_base64(frame)
        assert isinstance(b64, str) and len(b64) > 0

    def test_large_frame_is_downsized(self):
        frame = self._make_frame(1920, 1080)
        b64 = encode_frame_to_base64(frame)
        # Decode and check the resulting image dimensions
        jpg_bytes = base64.b64decode(b64)
        arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
        decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        h, w = decoded.shape[:2]
        assert max(h, w) <= MAX_IMAGE_DIM
        assert h % 28 == 0 or w % 28 == 0  # at least one dimension divisible by 28


class TestCaptureFrame:
    def test_raises_when_cap_not_open(self):
        """capture_frame should raise RuntimeError for a closed capture."""
        cap = cv2.VideoCapture()  # not opened
        with pytest.raises(RuntimeError, match="not open"):
            capture_frame(cap)
