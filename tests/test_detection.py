"""Tests for src/detection.py — VLM detection JSON parsing & bbox drawing."""

import json

import numpy as np
import pytest

from src.detection import parse_detections, draw_detections, DETECTION_PROMPT


class TestParseDetections:
    def test_valid_json_array(self):
        raw = '[{"label": "cup", "bbox": [10, 40, 25, 70]}]'
        result = parse_detections(raw)
        assert len(result) == 1
        assert result[0]["label"] == "cup"
        assert result[0]["bbox"] == [10, 40, 25, 70]

    def test_multiple_objects(self):
        raw = json.dumps([
            {"label": "cup", "bbox": [10, 40, 25, 70]},
            {"label": "laptop", "bbox": [30, 10, 80, 60]},
        ])
        result = parse_detections(raw)
        assert len(result) == 2

    def test_strips_markdown_fences(self):
        raw = '```json\n[{"label": "cup", "bbox": [10, 40, 25, 70]}]\n```'
        result = parse_detections(raw)
        assert len(result) == 1
        assert result[0]["label"] == "cup"

    def test_strips_plain_fences(self):
        raw = '```\n[{"label": "cup", "bbox": [10, 40, 25, 70]}]\n```'
        result = parse_detections(raw)
        assert len(result) == 1

    def test_embedded_in_text(self):
        raw = 'Here are the objects: [{"label": "cup", "bbox": [10, 40, 25, 70]}] found.'
        result = parse_detections(raw)
        assert len(result) == 1

    def test_empty_array(self):
        assert parse_detections("[]") == []

    def test_garbage_returns_empty(self):
        assert parse_detections("no json here") == []

    def test_dict_instead_of_list_returns_empty(self):
        raw = '{"label": "cup", "bbox": [10, 40, 25, 70]}'
        assert parse_detections(raw) == []

    def test_empty_string(self):
        assert parse_detections("") == []


class TestDrawDetections:
    def _make_frame(self, w=200, h=150):
        return np.zeros((h, w, 3), dtype=np.uint8)

    def test_returns_copy_not_original(self):
        frame = self._make_frame()
        detections = [{"label": "cup", "bbox": [10, 20, 50, 80]}]
        result = draw_detections(frame, detections)
        assert result is not frame

    def test_draws_bounding_box(self):
        frame = self._make_frame()
        detections = [{"label": "cup", "bbox": [10, 20, 50, 80]}]
        result = draw_detections(frame, detections)
        # The annotated frame should have non-zero pixels where the box was drawn
        assert result.sum() > 0

    def test_empty_detections_returns_clean_copy(self):
        frame = self._make_frame()
        result = draw_detections(frame, [])
        np.testing.assert_array_equal(frame, result)

    def test_malformed_detection_skipped(self):
        frame = self._make_frame()
        detections = [
            {"label": "cup", "bbox": [10, 20, 50, 80]},
            {"bad_key": "value"},  # missing bbox → should be skipped
            {"label": "phone", "bbox": [60, 10, 90, 50]},
        ]
        result = draw_detections(frame, detections)
        assert result.sum() > 0  # at least the valid ones were drawn

    def test_multiple_colors(self):
        frame = self._make_frame(400, 300)
        detections = [
            {"label": f"obj{i}", "bbox": [i*10, 10, i*10+15, 30]}
            for i in range(6)
        ]
        result = draw_detections(frame, detections)
        assert result.sum() > 0


class TestDetectionPrompt:
    def test_prompt_mentions_json(self):
        assert "JSON" in DETECTION_PROMPT

    def test_prompt_mentions_bbox(self):
        assert "bbox" in DETECTION_PROMPT

    def test_prompt_mentions_label(self):
        assert "label" in DETECTION_PROMPT
