"""Ollama VLM interaction and conversation history management."""

import ollama

from .config import VLM_MODEL, MAX_HISTORY_TURNS


class ConversationHistory:
    """Sliding-window conversation memory for multi-turn VLM dialogue."""

    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.messages: list[dict] = []
        self.max_turns = max_turns

    def add(self, role: str, content: str, images: list[str] | None = None):
        msg = {"role": role, "content": content}
        if images:
            msg["images"] = images
        self.messages.append(msg)
        max_msgs = self.max_turns * 2
        while len(self.messages) > max_msgs:
            self.messages.pop(0)

    def clear(self):
        self.messages.clear()

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def __len__(self):
        return len(self.messages)


def ask_vlm(image_b64: str | None, question: str,
            system_prompt: str | None = None,
            history: ConversationHistory | None = None) -> str:
    """Send question (optionally with image) to Ollama VLM.

    If history is provided, it is prepended and the exchange is auto-appended.
    """
    print("  🤖  Thinking …")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if history is not None:
        messages.extend(history.get_messages())

    user_msg: dict = {"role": "user", "content": question}
    if image_b64:
        user_msg["images"] = [image_b64]
    messages.append(user_msg)

    response = ollama.chat(model=VLM_MODEL, messages=messages)
    answer = response["message"]["content"].strip()

    if history is not None:
        history.add("user", question, [image_b64] if image_b64 else None)
        history.add("assistant", answer)

    return answer
