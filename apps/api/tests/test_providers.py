import httpx
from fastapi.testclient import TestClient

from raceweek.main import app
from raceweek.providers.adapters import ChatMessage, OpenAICompatibleProvider, ProviderRequest
from raceweek.providers.registry import provider_registry

client = TestClient(app)


def test_provider_registry_covers_required_providers_without_exposing_keys(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("CUSTOM_OPENAI_API_KEY", "custom-secret")
    monkeypatch.setenv("CUSTOM_OPENAI_BASE_URL", "http://localhost:9999/v1")

    configs = provider_registry().browser_configs()
    names = {config.provider_name for config in configs}

    assert {
        "fake",
        "fake-fail",
        "openai",
        "anthropic",
        "gemini",
        "ollama",
        "openrouter",
        "groq",
        "xai",
        "mistral",
        "custom-openai",
    } <= names
    assert next(config for config in configs if config.provider_name == "openai").key_configured
    assert next(config for config in configs if config.provider_name == "custom-openai").enabled
    assert "test-openai-key" not in str([config.model_dump() for config in configs])
    assert "custom-secret" not in str([config.model_dump() for config in configs])


def test_openai_compatible_provider_sends_redacted_config() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        seen["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Recommendation: hold the optimizer plan."}}],
                "model": "demo-model",
                "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            },
        )

    provider = OpenAICompatibleProvider(
        provider_name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        default_model="demo-model",
        api_key="secret-token",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = provider.complete(
        ProviderRequest(
            messages=[ChatMessage(role="user", content="Explain recrun_123.")],
            model="demo-model",
        )
    )

    assert response.content == "Recommendation: hold the optimizer plan."
    assert response.provider_name == "openrouter"
    assert response.model == "demo-model"
    assert response.input_tokens == 12
    assert seen["authorization"] == "Bearer secret-token"
    assert "secret-token" not in str(response.model_dump())


def test_provider_api_does_not_expose_configured_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-secret")

    payload = client.get("/api/v1/providers").json()

    assert any(
        item["providerName"] == "openrouter" and item["keyConfigured"] is True
        for item in payload["items"]
    )
    assert "openrouter-secret" not in str(payload)


def test_provider_test_route_handles_fake_and_unknown_providers() -> None:
    fake = client.post("/api/v1/providers/test", json={"providerName": "fake"}).json()
    failing = client.post("/api/v1/providers/test", json={"providerName": "fake-fail"}).json()
    unknown = client.post("/api/v1/providers/test", json={"providerName": "unknown"})

    assert fake == {
        "ok": True,
        "providerName": "fake",
        "message": "Fake provider is available for deterministic tests.",
        "latencyMs": None,
    }
    assert failing["ok"] is False
    assert failing["providerName"] == "fake-fail"
    assert unknown.status_code == 400
