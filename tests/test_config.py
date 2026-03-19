"""Tests for src/config.py — shared constants and language map."""

from src.config import (
    SAMPLE_RATE,
    MAX_IMAGE_DIM,
    MAX_HISTORY_TURNS,
    WAKE_THRESHOLD,
    VLM_MODEL,
    WEBCAM_UPDATE_MS,
    LANGUAGE_MAP,
)


class TestConstants:
    def test_sample_rate_is_16khz(self):
        assert SAMPLE_RATE == 16000

    def test_max_image_dim_positive(self):
        assert MAX_IMAGE_DIM > 0

    def test_max_history_turns_positive(self):
        assert MAX_HISTORY_TURNS > 0

    def test_wake_threshold_in_range(self):
        assert 0.0 < WAKE_THRESHOLD <= 1.0

    def test_vlm_model_is_string(self):
        assert isinstance(VLM_MODEL, str) and len(VLM_MODEL) > 0

    def test_webcam_update_ms_positive(self):
        assert WEBCAM_UPDATE_MS > 0


class TestLanguageMap:
    def test_english_present(self):
        assert "en" in LANGUAGE_MAP
        assert LANGUAGE_MAP["en"] == "english"

    def test_all_values_are_strings(self):
        for code, name in LANGUAGE_MAP.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(code) == 2

    def test_expected_languages(self):
        expected = {"en", "fr", "es", "de", "zh", "ja", "ro"}
        assert expected == set(LANGUAGE_MAP.keys())
