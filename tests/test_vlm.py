"""Tests for src/vlm.py — ConversationHistory class.

Note: ask_vlm() requires a running Ollama server and is not unit-tested here.
"""

import pytest

from src.vlm import ConversationHistory


class TestConversationHistory:
    def test_empty_on_creation(self):
        h = ConversationHistory()
        assert len(h) == 0
        assert h.get_messages() == []

    def test_add_message(self):
        h = ConversationHistory()
        h.add("user", "Hello")
        assert len(h) == 1
        msg = h.get_messages()[0]
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"

    def test_add_with_images(self):
        h = ConversationHistory()
        h.add("user", "What is this?", images=["base64data"])
        msg = h.get_messages()[0]
        assert msg["images"] == ["base64data"]

    def test_no_images_key_when_none(self):
        h = ConversationHistory()
        h.add("user", "Hello")
        assert "images" not in h.get_messages()[0]

    def test_sliding_window(self):
        h = ConversationHistory(max_turns=2)  # keeps 4 messages (2 turns × 2)
        for i in range(10):
            h.add("user", f"msg {i}")
        assert len(h) == 4

    def test_sliding_window_preserves_latest(self):
        h = ConversationHistory(max_turns=2)
        for i in range(10):
            h.add("user", f"msg {i}")
        messages = h.get_messages()
        # Should keep the last 4 messages: msg 6, 7, 8, 9
        assert messages[-1]["content"] == "msg 9"
        assert messages[0]["content"] == "msg 6"

    def test_clear(self):
        h = ConversationHistory()
        h.add("user", "Hello")
        h.add("assistant", "Hi")
        h.clear()
        assert len(h) == 0
        assert h.get_messages() == []

    def test_get_messages_returns_copy(self):
        h = ConversationHistory()
        h.add("user", "Hello")
        msgs = h.get_messages()
        msgs.append({"role": "fake", "content": "injected"})
        assert len(h) == 1  # original not affected

    def test_multiple_roles(self):
        h = ConversationHistory()
        h.add("user", "What is this?")
        h.add("assistant", "It is a cup.")
        h.add("user", "What color?")
        h.add("assistant", "Red.")
        assert len(h) == 4
        roles = [m["role"] for m in h.get_messages()]
        assert roles == ["user", "assistant", "user", "assistant"]

    def test_default_max_turns(self):
        from src.config import MAX_HISTORY_TURNS
        h = ConversationHistory()
        assert h.max_turns == MAX_HISTORY_TURNS
