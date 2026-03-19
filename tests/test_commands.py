"""Tests for src/commands.py — robot command JSON parsing."""

import json

import pytest

from src.commands import parse_command_json, COMMAND_SYSTEM_PROMPT


class TestParseCommandJson:
    def test_valid_command(self):
        raw = json.dumps({
            "action": "pick",
            "object": "cup",
            "color": "red",
            "location": "table",
            "confidence": 0.9,
        })
        result = parse_command_json(raw)
        assert result is not None
        assert result["action"] == "pick"
        assert result["object"] == "cup"
        assert result["color"] == "red"
        assert result["location"] == "table"
        assert result["confidence"] == 0.9

    def test_with_markdown_fences(self):
        raw = '```json\n{"action": "move", "object": null, "color": null, "location": "left", "confidence": 0.8}\n```'
        result = parse_command_json(raw)
        assert result is not None
        assert result["action"] == "move"

    def test_with_surrounding_text(self):
        raw = 'Here is the command: {"action": "stop", "object": null, "color": null, "location": null, "confidence": 1.0} parsed.'
        result = parse_command_json(raw)
        assert result is not None
        assert result["action"] == "stop"

    def test_null_fields(self):
        raw = json.dumps({
            "action": "look",
            "object": None,
            "color": None,
            "location": None,
            "confidence": 0.7,
        })
        result = parse_command_json(raw)
        assert result is not None
        assert result["object"] is None

    def test_garbage_returns_none(self):
        assert parse_command_json("no json here at all") is None

    def test_empty_string_returns_none(self):
        assert parse_command_json("") is None

    def test_array_instead_of_dict_returns_none(self):
        raw = '[{"action": "pick"}]'
        assert parse_command_json(raw) is None

    def test_partial_fields_still_parse(self):
        raw = '{"action": "go"}'
        result = parse_command_json(raw)
        assert result is not None
        assert result["action"] == "go"


class TestCommandSystemPrompt:
    def test_prompt_mentions_action(self):
        assert "action" in COMMAND_SYSTEM_PROMPT

    def test_prompt_mentions_object(self):
        assert "object" in COMMAND_SYSTEM_PROMPT

    def test_prompt_mentions_confidence(self):
        assert "confidence" in COMMAND_SYSTEM_PROMPT

    def test_prompt_mentions_json(self):
        assert "JSON" in COMMAND_SYSTEM_PROMPT
