"""Robot command parsing — VLM system prompt and JSON extraction."""

import json
import re

COMMAND_SYSTEM_PROMPT = """You are a robot command parser. Given the user's spoken command and optionally an image, output ONLY a JSON object with these keys:
- "action": the verb (e.g., "pick", "move", "go", "look", "turn", "stop")
- "object": the target object or null
- "color": color of the object or null
- "location": spatial reference (e.g., "left", "table", "ahead") or null
- "confidence": your confidence 0.0-1.0

Output ONLY the JSON object, no other text. Example:
{"action": "pick", "object": "cup", "color": "red", "location": "table", "confidence": 0.9}"""


def parse_command_json(vlm_response: str) -> dict | None:
    """Extract command JSON from VLM response."""
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
