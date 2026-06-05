from __future__ import annotations

from typing import Any

from raceweek.providers.adapters import ChatMessage, ProviderError


def system_text(messages: list[ChatMessage]) -> str:
    return "\n\n".join(message.content for message in messages if message.role == "system")


def prompt_text(messages: list[ChatMessage]) -> str:
    return "\n\n".join(f"{message.role}: {message.content}" for message in messages)


def anthropic_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        if message.role == "system":
            continue
        role = "assistant" if message.role == "assistant" else "user"
        normalized.append({"role": role, "content": message.content})
    return normalized


def openai_response_text(response: Any) -> str:
    return required_text(attr(response, "output_text", None))


def text_blocks(response: Any) -> str:
    parts = [
        attr(block, "text", "")
        for block in attr(response, "content", [])
        if attr(block, "type", "text") == "text"
    ]
    return required_text("\n".join(str(part) for part in parts if part))


def chat_choice_text(response: Any) -> str:
    choices = attr(response, "choices", [])
    if not choices:
        raise ProviderError("Provider response did not include choices.")
    message = attr(choices[0], "message", None)
    return required_text(attr(message, "content", None))


def ollama_text(response: Any) -> str:
    if isinstance(response, dict):
        message = response.get("message", {})
        if isinstance(message, dict):
            return required_text(message.get("content"))
    message = attr(response, "message", None)
    return required_text(attr(message, "content", None))


def required_text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ProviderError("Provider response message was empty.")


def usage_int(response: Any, key: str) -> int | None:
    usage = attr(response, "usage", None)
    value = attr(usage, key, None)
    return value if isinstance(value, int) else None


def dict_int(response: Any, key: str) -> int | None:
    if isinstance(response, dict):
        value = response.get(key)
        return value if isinstance(value, int) else None
    value = attr(response, key, None)
    return value if isinstance(value, int) else None


def attr(value: Any, key: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)
