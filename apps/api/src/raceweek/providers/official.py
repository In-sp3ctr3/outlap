from __future__ import annotations

from typing import Any

from raceweek.providers.adapters import (
    ProviderRequest,
    ProviderResponse,
)
from raceweek.providers.parsing import (
    anthropic_messages,
    attr,
    chat_choice_text,
    dict_int,
    ollama_text,
    openai_response_text,
    prompt_text,
    required_text,
    system_text,
    text_blocks,
    usage_int,
)


class OpenAISdkProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        default_model: str,
        api_key: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._default_model = default_model
        self._api_key = api_key
        self._base_url = base_url
        self._client = client

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        response = self._client_or_default().responses.create(
            model=model,
            instructions=system_text(request.messages) or None,
            input=[
                {"role": message.role, "content": message.content}
                for message in request.messages
                if message.role != "system"
            ],
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
        return ProviderResponse(
            content=openai_response_text(response),
            provider_name=self.provider_name,
            model=str(attr(response, "model", model)),
            input_tokens=usage_int(response, "input_tokens"),
            output_tokens=usage_int(response, "output_tokens"),
        )

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        from openai import OpenAI

        return OpenAI(api_key=self._api_key, base_url=self._base_url)


class AnthropicSdkProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        default_model: str,
        api_key: str,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._default_model = default_model
        self._api_key = api_key
        self._client = client

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        response = self._client_or_default().messages.create(
            model=model,
            system=system_text(request.messages) or None,
            messages=anthropic_messages(request.messages),
            temperature=request.temperature,
            max_tokens=request.max_output_tokens,
        )
        return ProviderResponse(
            content=text_blocks(response),
            provider_name=self.provider_name,
            model=str(attr(response, "model", model)),
            input_tokens=usage_int(response, "input_tokens"),
            output_tokens=usage_int(response, "output_tokens"),
        )

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        from anthropic import Anthropic

        return Anthropic(api_key=self._api_key)


class GeminiSdkProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        default_model: str,
        api_key: str,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._default_model = default_model
        self._api_key = api_key
        self._client = client

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        response = self._client_or_default().models.generate_content(
            model=model,
            contents=prompt_text(request.messages),
            config={
                "temperature": request.temperature,
                "max_output_tokens": request.max_output_tokens,
            },
        )
        return ProviderResponse(
            content=required_text(attr(response, "text", None)),
            provider_name=self.provider_name,
            model=model,
        )

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        from google import genai

        return genai.Client(api_key=self._api_key)


class MistralSdkProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        default_model: str,
        api_key: str,
        server_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._default_model = default_model
        self._api_key = api_key
        self._server_url = server_url
        self._client = client

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        response = self._client_or_default().chat.complete(
            model=model,
            messages=[message.model_dump(exclude_none=True) for message in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_output_tokens,
        )
        return ProviderResponse(
            content=chat_choice_text(response),
            provider_name=self.provider_name,
            model=str(attr(response, "model", model)),
            input_tokens=usage_int(response, "prompt_tokens"),
            output_tokens=usage_int(response, "completion_tokens"),
        )

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        from mistralai.client import Mistral

        return Mistral(api_key=self._api_key, server_url=self._server_url)


class OllamaSdkProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        default_model: str,
        host: str,
        client: Any | None = None,
    ) -> None:
        self.provider_name = provider_name
        self._default_model = default_model
        self._host = host
        self._client = client

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or self._default_model
        response = self._client_or_default().chat(
            model=model,
            messages=[message.model_dump(exclude_none=True) for message in request.messages],
            options={
                "temperature": request.temperature,
                "num_predict": request.max_output_tokens,
            },
        )
        return ProviderResponse(
            content=ollama_text(response),
            provider_name=self.provider_name,
            model=model,
            input_tokens=dict_int(response, "prompt_eval_count"),
            output_tokens=dict_int(response, "eval_count"),
        )

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        from ollama import Client

        return Client(host=self._host)
