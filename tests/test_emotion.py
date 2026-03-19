"""Tests for src/emotion.py — keyword-based emotion classification."""

import pytest

from src.emotion import classify_emotion, get_emotion_rate, EMOTION_KEYWORDS, EMOTION_RATE


class TestClassifyEmotion:
    def test_neutral_for_plain_text(self):
        assert classify_emotion("Hello, how are you?") == "neutral"

    def test_excited_keywords(self):
        assert classify_emotion("That is amazing and wonderful!") == "excited"

    def test_positive_keywords(self):
        assert classify_emotion("That looks nice and pretty.") == "positive"

    def test_warning_keywords(self):
        assert classify_emotion("Danger! Be careful, there is a hazard.") == "warning"

    def test_negative_keywords(self):
        assert classify_emotion("That is terrible and awful.") == "negative"

    def test_case_insensitive(self):
        assert classify_emotion("AMAZING WONDERFUL FANTASTIC") == "excited"

    def test_empty_string(self):
        assert classify_emotion("") == "neutral"

    def test_mixed_returns_highest_score(self):
        # "great" (excited) + "nice" (positive) + "good" (positive) → positive wins 2-1
        result = classify_emotion("great nice good")
        assert result == "positive"

    def test_single_keyword(self):
        assert classify_emotion("love") == "excited"
        assert classify_emotion("sorry") == "negative"
        assert classify_emotion("danger") == "warning"


class TestGetEmotionRate:
    def test_all_emotions_have_rate(self):
        for emotion in EMOTION_RATE:
            rate = get_emotion_rate(emotion)
            assert isinstance(rate, int)
            assert rate > 0

    def test_neutral_rate(self):
        assert get_emotion_rate("neutral") == 175

    def test_excited_faster_than_neutral(self):
        assert get_emotion_rate("excited") > get_emotion_rate("neutral")

    def test_warning_slower_than_neutral(self):
        assert get_emotion_rate("warning") < get_emotion_rate("neutral")

    def test_unknown_emotion_returns_default(self):
        assert get_emotion_rate("unknown_emotion") == 175

    def test_rate_ordering(self):
        # excited > positive > neutral > negative > warning
        assert (get_emotion_rate("excited") >
                get_emotion_rate("positive") >
                get_emotion_rate("neutral") >
                get_emotion_rate("negative") >
                get_emotion_rate("warning"))


class TestEmotionKeywords:
    def test_all_keyword_lists_non_empty(self):
        for emotion, keywords in EMOTION_KEYWORDS.items():
            assert len(keywords) > 0, f"{emotion} has no keywords"

    def test_no_duplicate_keywords_within_emotion(self):
        for emotion, keywords in EMOTION_KEYWORDS.items():
            assert len(keywords) == len(set(keywords)), \
                f"{emotion} has duplicate keywords"
