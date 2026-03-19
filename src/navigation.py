"""Navigation command parsing and named waypoint management.

Works with the TurtleBot3 World Gazebo map. Provides named locations
that map to (x, y, yaw) coordinates in the simulation, and a VLM
system prompt for parsing natural-language navigation commands.
"""

import json
import re
from typing import Optional

# ── Named locations in TurtleBot3 World ──────────────────────────────────────
# The TurtleBot3 World is a ~5 × 5 m arena with 9 cylindrical pillars
# arranged in a 3×3 grid (at x,y ∈ {-1.1, 0, 1.1}) and wall segments
# connecting some of them.  Boundary walls sit at roughly ±2.5 m.
# The robot spawns at (-2.0, -0.5).
#
# These waypoints are in verified open areas between the obstacles.

NAMED_LOCATIONS: dict[str, dict] = {
    "spawn":       {"x": -2.0,  "y": -0.5,  "yaw": 0,    "description": "the starting position (west side)"},
    "centre":      {"x":  0.55, "y":  0.55, "yaw": 0,    "description": "the open area near the centre"},
    "north":       {"x":  0.0,  "y":  2.0,  "yaw": 90,   "description": "the north side of the arena"},
    "south":       {"x":  0.0,  "y": -2.0,  "yaw": 270,  "description": "the south side of the arena"},
    "east":        {"x":  2.0,  "y":  0.0,  "yaw": 0,    "description": "the east side of the arena"},
    "west":        {"x": -2.0,  "y":  0.0,  "yaw": 180,  "description": "the west side of the arena"},
    "north_east":  {"x":  1.5,  "y":  1.5,  "yaw": 45,   "description": "the north-east corner"},
    "north_west":  {"x": -1.5,  "y":  1.5,  "yaw": 135,  "description": "the north-west corner"},
    "south_east":  {"x":  1.5,  "y": -1.5,  "yaw": 315,  "description": "the south-east corner"},
    "south_west":  {"x": -1.5,  "y": -1.5,  "yaw": 225,  "description": "the south-west corner"},
}


def get_location_list() -> str:
    """Return a human-readable list of known locations."""
    lines = []
    for name, loc in NAMED_LOCATIONS.items():
        lines.append(f"  • {name}: {loc['description']} (x={loc['x']}, y={loc['y']})")
    return "\n".join(lines)


def resolve_location(name: str) -> Optional[dict]:
    """Resolve a location name to coordinates. Case-insensitive, fuzzy."""
    name_lower = name.lower().strip().replace(" ", "_")
    # Exact match
    if name_lower in NAMED_LOCATIONS:
        return NAMED_LOCATIONS[name_lower]
    # Partial match
    for key, loc in NAMED_LOCATIONS.items():
        if name_lower in key or key in name_lower:
            return loc
    # Check descriptions
    for key, loc in NAMED_LOCATIONS.items():
        if name_lower in loc["description"].lower():
            return loc
    return None


# ── VLM System Prompt for Navigation Commands ───────────────────────────────

NAV_COMMAND_SYSTEM_PROMPT = f"""You are a robot navigation assistant. The user will give you a navigation command in natural language.

You must parse the command and output ONLY a JSON object with these keys:
- "action": one of "go_to", "go_to_coordinates", "move_forward", "move_backward", "turn_left", "turn_right", "stop", "look_around", "come_back", "describe_location"
- "location": the target location name (if applicable) or null
- "x": target x coordinate in metres (only for go_to_coordinates) or null
- "y": target y coordinate in metres (only for go_to_coordinates) or null
- "distance": distance in metres (if applicable) or null
- "angle": rotation in degrees (if applicable) or null
- "confidence": your confidence 0.0–1.0

IMPORTANT: If the user specifies numeric coordinates (e.g. "go to 2, 2" or "navigate to x=1.5 y=-0.5"), use "go_to_coordinates" with "x" and "y" fields.
Only use "go_to" with "location" when the user names a known location.

Known locations in the environment:
{get_location_list()}

The navigable area is roughly -2.5 to 2.5 in both x and y.

Examples:
User: "Go to the north-east corner"
{{"action": "go_to", "location": "north_east", "x": null, "y": null, "distance": null, "angle": null, "confidence": 0.95}}

User: "Go to coordinates 2 and 2"
{{"action": "go_to_coordinates", "location": null, "x": 2.0, "y": 2.0, "distance": null, "angle": null, "confidence": 0.95}}

User: "Navigate to x=1.5, y=-0.5"
{{"action": "go_to_coordinates", "location": null, "x": 1.5, "y": -0.5, "distance": null, "angle": null, "confidence": 0.9}}

User: "Move forward 2 metres"
{{"action": "move_forward", "location": null, "x": null, "y": null, "distance": 2.0, "angle": null, "confidence": 0.9}}

User: "Turn left 90 degrees"
{{"action": "turn_left", "location": null, "x": null, "y": null, "distance": null, "angle": 90, "confidence": 0.9}}

User: "Stop"
{{"action": "stop", "location": null, "x": null, "y": null, "distance": null, "angle": null, "confidence": 1.0}}

User: "Where are you?"
{{"action": "describe_location", "location": null, "x": null, "y": null, "distance": null, "angle": null, "confidence": 0.9}}

User: "Come back to spawn"
{{"action": "come_back", "location": "spawn", "x": null, "y": null, "distance": null, "angle": null, "confidence": 0.9}}

Output ONLY the JSON object, no other text."""


def parse_nav_command(vlm_response: str) -> Optional[dict]:
    """Extract navigation command JSON from VLM response."""
    cleaned = re.sub(r'```(?:json)?\s*', '', vlm_response)
    cleaned = cleaned.replace('```', '').strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        match = re.search(r'\{[^{}]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def describe_robot_position(position: dict) -> str:
    """Generate a natural description of where the robot is, given its position dict."""
    x = position.get("x", 0.0)
    y = position.get("y", 0.0)
    yaw = position.get("yaw", 0.0)

    # Find the closest named location
    closest_name = "unknown"
    closest_dist = float("inf")
    for name, loc in NAMED_LOCATIONS.items():
        dx = x - loc["x"]
        dy = y - loc["y"]
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < closest_dist:
            closest_dist = dist
            closest_name = name

    loc_info = NAMED_LOCATIONS.get(closest_name, {})
    desc = loc_info.get("description", closest_name)

    if closest_dist < 0.3:
        proximity = f"I am at {desc}"
    elif closest_dist < 1.0:
        proximity = f"I am near {desc}"
    else:
        proximity = f"I am about {closest_dist:.1f} metres from {desc}"

    # Cardinal direction facing
    if -45 <= yaw < 45:
        facing = "east"
    elif 45 <= yaw < 135:
        facing = "north"
    elif -135 <= yaw < -45:
        facing = "south"
    else:
        facing = "west"

    return f"{proximity}, facing {facing}. My coordinates are ({x:.1f}, {y:.1f})."
