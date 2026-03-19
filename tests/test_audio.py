"""Tests for src/audio.py — transcribe function with a mock Whisper model."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.audio import transcribe
from src.config import SAMPLE_RATE


class TestTranscribe:
    def _make_mock_model(self, text: str = "Hello world"):
        model = MagicMock()
        model.transcribe.return_value = {"text": f"  {text}  "}
        return model

    def test_returns_stripped_text(self):
        model = self._make_mock_model("Hello world")
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        result = transcribe(model, audio)
        assert result == "Hello world"

    def test_passes_audio_to_model(self):
        model = self._make_mock_model()
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        transcribe(model, audio)
        model.transcribe.assert_called_once()
        call_args = model.transcribe.call_args
        np.testing.assert_array_equal(call_args[0][0], audio)

    def test_english_does_not_set_language(self):
        model = self._make_mock_model()
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        transcribe(model, audio, language="en")
        kwargs = model.transcribe.call_args[1]
        assert "language" not in kwargs

    def test_non_english_sets_language(self):
        model = self._make_mock_model()
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        transcribe(model, audio, language="fr")
        kwargs = model.transcribe.call_args[1]
        assert kwargs["language"] == "fr"

    def test_fp16_disabled(self):
        model = self._make_mock_model()
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        transcribe(model, audio)
        kwargs = model.transcribe.call_args[1]
        assert kwargs["fp16"] is False

    def test_empty_result(self):
        model = MagicMock()
        model.transcribe.return_value = {"text": "   "}
        audio = np.zeros(SAMPLE_RATE, dtype="float32")
        result = transcribe(model, audio)
        assert result == ""
