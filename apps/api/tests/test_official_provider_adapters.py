from types import SimpleNamespace

from raceweek.providers.adapters import ChatMessage, ProviderRequest
from raceweek.providers.official import (
    AnthropicSdkProvider,
    GeminiSdkProvider,
    MistralSdkProvider,
    OllamaSdkProvider,
    OpenAISdkProvider,
)
from raceweek.providers.registry import provider_registry


def sdk_request() -> ProviderRequest:
    return ProviderRequest(
        messages=[
            ChatMessage(role="system", content="Use deterministic optimizer output only."),
            ChatMessage(role="user", content="Explain recommendation recrun_123."),
        ],
        model="demo-model",
        max_output_tokens=250,
    )


def test_openai_sdk_provider_uses_responses_api() -> None:
    seen: dict[str, object] = {}

    class Responses:
        def create(self, **kwargs: object) -> SimpleNamespace:
            seen.update(kwargs)
            return SimpleNamespace(
                output_text="OpenAI official response.",
                model="demo-model",
                usage=SimpleNamespace(input_tokens=10, output_tokens=4),
            )

    provider = OpenAISdkProvider(
        provider_name="openai",
        default_model="fallback",
        api_key="test-key",
        client=SimpleNamespace(responses=Responses()),
    )

    response = provider.complete(sdk_request())

    assert response.content == "OpenAI official response."
    assert seen["model"] == "demo-model"
    assert seen["instructions"] == "Use deterministic optimizer output only."
    assert response.input_tokens == 10
    assert response.output_tokens == 4


def test_anthropic_sdk_provider_uses_messages_api() -> None:
    seen: dict[str, object] = {}

    class Messages:
        def create(self, **kwargs: object) -> SimpleNamespace:
            seen.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="Anthropic official response.")],
                model="demo-model",
                usage=SimpleNamespace(input_tokens=8, output_tokens=5),
            )

    provider = AnthropicSdkProvider(
        provider_name="anthropic",
        default_model="fallback",
        api_key="test-key",
        client=SimpleNamespace(messages=Messages()),
    )

    response = provider.complete(sdk_request())

    assert response.content == "Anthropic official response."
    assert seen["system"] == "Use deterministic optimizer output only."
    assert seen["messages"] == [{"role": "user", "content": "Explain recommendation recrun_123."}]
    assert response.input_tokens == 8
    assert response.output_tokens == 5


def test_gemini_sdk_provider_uses_generate_content() -> None:
    seen: dict[str, object] = {}

    class Models:
        def generate_content(self, **kwargs: object) -> SimpleNamespace:
            seen.update(kwargs)
            return SimpleNamespace(text="Gemini official response.")

    provider = GeminiSdkProvider(
        provider_name="gemini",
        default_model="fallback",
        api_key="test-key",
        client=SimpleNamespace(models=Models()),
    )

    response = provider.complete(sdk_request())

    assert response.content == "Gemini official response."
    assert seen["model"] == "demo-model"
    assert "deterministic optimizer" in str(seen["contents"])


def test_mistral_sdk_provider_uses_chat_complete() -> None:
    seen: dict[str, object] = {}

    class Chat:
        def complete(self, **kwargs: object) -> SimpleNamespace:
            seen.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Mistral response."))],
                model="demo-model",
                usage=SimpleNamespace(prompt_tokens=7, completion_tokens=3),
            )

    provider = MistralSdkProvider(
        provider_name="mistral",
        default_model="fallback",
        api_key="test-key",
        client=SimpleNamespace(chat=Chat()),
    )

    response = provider.complete(sdk_request())

    assert response.content == "Mistral response."
    assert seen["model"] == "demo-model"
    assert response.input_tokens == 7
    assert response.output_tokens == 3


def test_ollama_sdk_provider_uses_local_chat_client() -> None:
    seen: dict[str, object] = {}

    class Client:
        def chat(self, **kwargs: object) -> dict[str, object]:
            seen.update(kwargs)
            return {
                "message": {"content": "Ollama local response."},
                "prompt_eval_count": 6,
                "eval_count": 2,
            }

    provider = OllamaSdkProvider(
        provider_name="ollama",
        default_model="fallback",
        host="http://127.0.0.1:11434",
        client=Client(),
    )

    response = provider.complete(sdk_request())

    assert response.content == "Ollama local response."
    assert seen["model"] == "demo-model"
    assert response.input_tokens == 6
    assert response.output_tokens == 2


def test_registry_uses_official_sdk_adapters(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-test-key")

    registry = provider_registry()

    assert isinstance(registry.provider_for("openai"), OpenAISdkProvider)
    assert isinstance(registry.provider_for("anthropic"), AnthropicSdkProvider)
    assert isinstance(registry.provider_for("gemini"), GeminiSdkProvider)
    assert isinstance(registry.provider_for("mistral"), MistralSdkProvider)
    assert isinstance(registry.provider_for("ollama"), OllamaSdkProvider)
