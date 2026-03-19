"""Tests for src/navigation.py — navigation command parsing and location management."""

import json

import pytest

from src.navigation import (
    NAMED_LOCATIONS,
    resolve_location,
    get_location_list,
    parse_nav_command,
    describe_robot_position,
    NAV_COMMAND_SYSTEM_PROMPT,
)


class TestResolveLocation:
    def test_exact_match(self):
        loc = resolve_location("spawn")
        assert loc is not None
        assert loc["x"] == -2.0
        assert loc["y"] == -0.5

    def test_case_insensitive(self):
        loc = resolve_location("Spawn")
        assert loc is not None
        assert loc["x"] == -2.0

    def test_with_underscores_and_spaces(self):
        loc = resolve_location("north east")
        assert loc is not None
        assert loc["x"] == 1.5
        assert loc["y"] == 1.5

    def test_partial_match(self):
        loc = resolve_location("north")
        assert loc is not None

    def test_unknown_location(self):
        assert resolve_location("mars") is None

    def test_centre(self):
        loc = resolve_location("centre")
        assert loc is not None
        assert loc["x"] == 0.55
        assert loc["y"] == 0.55

    def test_all_corners(self):
        for name in ("north_east", "north_west", "south_east", "south_west"):
            loc = resolve_location(name)
            assert loc is not None, f"Missing location: {name}"


class TestGetLocationList:
    def test_returns_string(self):
        result = get_location_list()
        assert isinstance(result, str)

    def test_contains_all_locations(self):
        result = get_location_list()
        for name in NAMED_LOCATIONS:
            assert name in result


class TestParseNavCommand:
    def test_valid_go_to(self):
        raw = json.dumps({
            "action": "go_to",
            "location": "north_east",
            "x": None,
            "y": None,
            "distance": None,
            "angle": None,
            "confidence": 0.95,
        })
        result = parse_nav_command(raw)
        assert result is not None
        assert result["action"] == "go_to"
        assert result["location"] == "north_east"

    def test_valid_go_to_coordinates(self):
        raw = json.dumps({
            "action": "go_to_coordinates",
            "location": None,
            "x": 2.0,
            "y": 2.0,
            "distance": None,
            "angle": None,
            "confidence": 0.95,
        })
        result = parse_nav_command(raw)
        assert result is not None
        assert result["action"] == "go_to_coordinates"
        assert result["x"] == 2.0
        assert result["y"] == 2.0

    def test_valid_stop(self):
        raw = json.dumps({
            "action": "stop",
            "location": None,
            "distance": None,
            "angle": None,
            "confidence": 1.0,
        })
        result = parse_nav_command(raw)
        assert result is not None
        assert result["action"] == "stop"

    def test_with_markdown_fences(self):
        raw = '```json\n{"action": "turn_left", "location": null, "distance": null, "angle": 90, "confidence": 0.9}\n```'
        result = parse_nav_command(raw)
        assert result is not None
        assert result["action"] == "turn_left"
        assert result["angle"] == 90

    def test_with_surrounding_text(self):
        raw = 'Sure! {"action": "move_forward", "location": null, "distance": 2.0, "angle": null, "confidence": 0.8} done.'
        result = parse_nav_command(raw)
        assert result is not None
        assert result["action"] == "move_forward"
        assert result["distance"] == 2.0

    def test_garbage_returns_none(self):
        assert parse_nav_command("no json here") is None

    def test_empty_returns_none(self):
        assert parse_nav_command("") is None


class TestDescribeRobotPosition:
    def test_at_spawn(self):
        desc = describe_robot_position({"x": -2.0, "y": -0.5, "yaw": 0.0})
        assert "start" in desc.lower() or "spawn" in desc.lower() or "west" in desc.lower()

    def test_near_centre(self):
        desc = describe_robot_position({"x": 0.55, "y": 0.55, "yaw": 0.0})
        assert "centre" in desc.lower() or "center" in desc.lower()

    def test_facing_direction(self):
        desc = describe_robot_position({"x": 0.0, "y": 0.0, "yaw": 0.0})
        assert "east" in desc.lower()

        desc = describe_robot_position({"x": 0.0, "y": 0.0, "yaw": 90.0})
        assert "north" in desc.lower()

    def test_contains_coordinates(self):
        desc = describe_robot_position({"x": 1.2, "y": -0.3, "yaw": 45.0})
        assert "1.2" in desc
        assert "-0.3" in desc

    def test_far_from_any_location(self):
        desc = describe_robot_position({"x": 10.0, "y": 10.0, "yaw": 0.0})
        assert "metres" in desc.lower()


class TestNavCommandSystemPrompt:
    def test_prompt_contains_locations(self):
        for name in NAMED_LOCATIONS:
            assert name in NAV_COMMAND_SYSTEM_PROMPT

    def test_prompt_contains_actions(self):
        for action in ["go_to", "go_to_coordinates", "move_forward", "turn_left", "stop"]:
            assert action in NAV_COMMAND_SYSTEM_PROMPT

    def test_prompt_mentions_coordinates(self):
        assert "x" in NAV_COMMAND_SYSTEM_PROMPT
        assert "y" in NAV_COMMAND_SYSTEM_PROMPT
