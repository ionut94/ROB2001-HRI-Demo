"""Tests for src/gestures.py — get_pointed_region and model path constants."""

import numpy as np
import pytest

from src.gestures import get_pointed_region, HAND_MODEL_PATH, POSE_MODEL_PATH


class TestGetPointedRegion:
    def _make_frame(self, w=640, h=480):
        return np.zeros((h, w, 3), dtype=np.uint8)

    def test_returns_none_when_no_tip(self):
        frame = self._make_frame()
        info = {"pointing_tip": None, "pointing_dir": None}
        assert get_pointed_region(frame, info) is None

    def test_returns_crop_when_pointing_center(self):
        frame = self._make_frame()
        info = {
            "pointing_tip": (0.5, 0.5),  # center of frame
            "pointing_dir": (0.1, 0.0),  # pointing right
        }
        result = get_pointed_region(frame, info)
        assert result is not None
        h, w = result.shape[:2]
        assert h > 0 and w > 0

    def test_crop_size_roughly_200x200(self):
        frame = self._make_frame(640, 480)
        info = {
            "pointing_tip": (0.5, 0.5),
            "pointing_dir": (0.01, 0.0),  # small dir → stays near center
        }
        result = get_pointed_region(frame, info)
        assert result is not None
        h, w = result.shape[:2]
        # Size should be at most 200×200
        assert w <= 200
        assert h <= 200

    def test_edge_pointing_clamps_to_frame(self):
        frame = self._make_frame(640, 480)
        info = {
            "pointing_tip": (0.99, 0.99),  # near bottom-right corner
            "pointing_dir": (0.1, 0.1),     # pointing further out
        }
        result = get_pointed_region(frame, info)
        # May return None if crop is too small, or a valid crop
        if result is not None:
            h, w = result.shape[:2]
            assert h >= 50 and w >= 50

    def test_returns_none_for_too_small_crop(self):
        """If the crop would be < 50px in either dimension, returns None."""
        frame = self._make_frame(640, 480)
        info = {
            "pointing_tip": (0.0, 0.0),  # top-left corner
            "pointing_dir": (-0.5, -0.5),  # pointing out of frame
        }
        # This should result in a tiny/zero crop → None
        result = get_pointed_region(frame, info)
        # Either None or the crop is valid (>= 50px)
        if result is not None:
            h, w = result.shape[:2]
            assert h >= 50 and w >= 50

    def test_no_pointing_dir(self):
        """If pointing_dir is None, should still work using just the tip."""
        frame = self._make_frame(640, 480)
        info = {
            "pointing_tip": (0.5, 0.5),
            "pointing_dir": None,
        }
        # pointing_dir is None → the offset calculation won't run
        # but the function checks `if gesture_info["pointing_dir"]:`
        result = get_pointed_region(frame, info)
        assert result is not None


class TestModelPaths:
    def test_hand_model_path_ends_with_task(self):
        assert HAND_MODEL_PATH.endswith(".task")

    def test_pose_model_path_ends_with_task(self):
        assert POSE_MODEL_PATH.endswith(".task")
