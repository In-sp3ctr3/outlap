from __future__ import annotations

import time
from typing import Any, Literal, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field


class ProviderError(RuntimeError):
    pass


class ProviderModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatMessage(ProviderModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None


class ToolDefinition(ProviderModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class ProviderRequest(ProviderModel):
    messages: list[ChatMessage]
    model: str | None = None
    tools: list[ToolDefinition] = Field(default_factory=list)
    temperature: float = 0.2
    max_output_tokens: int = 1200


class ProviderResponse(ProviderModel):
    content: str
    provider_name: str
    model: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None


class ProviderAdapter(Protocol):
    provider_name: str

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError


class FakeProvider:
    provider_name = "fake"

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            content=(
                "Recommendation: follow the top deterministic optimizer option.\n"
                "Confidence: medium.\n"
                "Why: the optimizer output is the source of truth, and this answer is "
                "read-only."
            ),
            provider_name=self.provider_name,
            model=request.model or "fake-strategist",
        )


class FailingProvider:
    provider_name = "fake-fail"

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise ProviderError("Fake provider failure path verified.")


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        default_model: str,
        api_key: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._api_key = api_key
        self._http_client = http_client or httpx.Client(timeout=20)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [message.model_dump(exclude_none=True) for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]

        headers = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"

        started = time.perf_counter()
        try:
            response = self._http_client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_name} provider request failed") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        data = response.json()
        choice = _first_choice(data)
        content = _message_content(choice)
        usage = data.get("usage", {})
        return ProviderResponse(
            content=content,
            provider_name=self.provider_name,
            model=str(data.get("model") or model),
            tool_calls=_tool_calls(choice),
            input_tokens=_optional_int(usage.get("prompt_tokens")),
            output_tokens=_optional_int(usage.get("completion_tokens")),
            latency_ms=latency_ms,
        )


def _first_choice(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderError("Provider response did not include choices.")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ProviderError("Provider response choice was malformed.")
    return choice


def _message_content(choice: dict[str, Any]) -> str:
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ProviderError("Provider response did not include a message.")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise ProviderError("Provider response message was empty.")


def _tool_calls(choice: dict[str, Any]) -> list[dict[str, Any]]:
    message = choice.get("message")
    if not isinstance(message, dict):
        return []
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list):
        return [item for item in tool_calls if isinstance(item, dict)]
    return []


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None
