from __future__ import annotations

from raceweek.core.models import ProviderConfig, ProviderTestResponse
from raceweek.providers.adapters import (
    ChatMessage,
    FailingProvider,
    FakeProvider,
    OpenAICompatibleProvider,
    ProviderAdapter,
    ProviderError,
    ProviderRequest,
)
from raceweek.providers.official import (
    AnthropicSdkProvider,
    GeminiSdkProvider,
    MistralSdkProvider,
    OllamaSdkProvider,
    OpenAISdkProvider,
)
from raceweek.providers.specs import PROVIDER_SPECS, ProviderSpec
from raceweek.settings import Settings


class ProviderRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._specs = {spec.provider_name: spec for spec in PROVIDER_SPECS}

    def browser_configs(self) -> list[ProviderConfig]:
        return [self._browser_config(spec) for spec in self._specs.values()]

    def provider_for(self, provider_name: str) -> ProviderAdapter:
        spec = self._require_spec(provider_name)
        if spec.provider_name == "fake":
            return FakeProvider()
        if spec.provider_name == "fake-fail":
            return FailingProvider()
        if spec.adapter_family.startswith("official-"):
            return self._official_provider(spec)
        if spec.adapter_family == "openai-compatible":
            return self._openai_compatible_provider(spec)
        raise ProviderError(
            f"{spec.display_name} is registered but its live adapter is not enabled."
        )

    def test_provider(self, provider_name: str, model: str | None = None) -> ProviderTestResponse:
        spec = self._require_spec(provider_name)
        if provider_name == "fake-fail":
            return ProviderTestResponse(
                ok=False,
                provider_name=provider_name,
                message="Fake provider failure path verified.",
            )
        if provider_name == "fake":
            return ProviderTestResponse(
                ok=True,
                provider_name=provider_name,
                message="Fake provider is available for deterministic tests.",
            )
        if spec.adapter_family not in {"openai-compatible"} and not spec.adapter_family.startswith(
            "official-"
        ):
            return ProviderTestResponse(
                ok=False,
                provider_name=provider_name,
                message=f"{spec.display_name} is registered; live SDK adapter is pending.",
            )
        if not self._is_enabled(spec):
            return ProviderTestResponse(
                ok=False,
                provider_name=provider_name,
                message=f"{spec.display_name} is not configured.",
            )
        probe = self.provider_for(provider_name).complete(
            ProviderRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content="Reply with a short readiness confirmation.",
                    )
                ],
                model=model,
            )
        )
        return ProviderTestResponse(
            ok=True,
            provider_name=provider_name,
            message=f"{spec.display_name} responded with {probe.model}.",
            latency_ms=probe.latency_ms,
        )

    def _browser_config(self, spec: ProviderSpec) -> ProviderConfig:
        return ProviderConfig(
            provider_name=spec.provider_name,
            display_name=spec.display_name,
            enabled=self._is_enabled(spec),
            base_url=None,
            default_model=self._default_model(spec),
            api_key_env_var=spec.api_key_env_var,
            supports_streaming=spec.supports_streaming,
            supports_tools=spec.supports_tools,
            key_configured=self._key_configured(spec),
        )

    def _require_spec(self, provider_name: str) -> ProviderSpec:
        try:
            return self._specs[provider_name]
        except KeyError as exc:
            raise ProviderError(f"Unknown provider: {provider_name}") from exc

    def _is_enabled(self, spec: ProviderSpec) -> bool:
        if spec.provider_name in {"fake", "fake-fail"}:
            return True
        if spec.provider_name == "ollama":
            return bool(self._settings.ollama_base_url)
        if spec.provider_name == "custom-openai":
            return bool(self._settings.custom_openai_base_url)
        return self._key_configured(spec)

    def _key_configured(self, spec: ProviderSpec) -> bool:
        if spec.provider_name == "ollama":
            return False
        key = self._api_key(spec)
        return bool(key and key.strip())

    def _api_key(self, spec: ProviderSpec) -> str | None:
        field_name = {
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
            "mistral": "mistral_api_key",
            "openrouter": "openrouter_api_key",
            "groq": "groq_api_key",
            "xai": "xai_api_key",
            "custom-openai": "custom_openai_api_key",
        }.get(spec.provider_name)
        if field_name is None:
            return None
        value = getattr(self._settings, field_name)
        return value if value else None

    def _openai_compatible_provider(self, spec: ProviderSpec) -> OpenAICompatibleProvider:
        base_url = self._base_url(spec)
        if not base_url:
            raise ProviderError(f"{spec.display_name} base URL is not configured.")
        return OpenAICompatibleProvider(
            provider_name=spec.provider_name,
            base_url=base_url,
            default_model=self._default_model(spec) or spec.provider_name,
            api_key=self._api_key(spec),
        )

    def _official_provider(self, spec: ProviderSpec) -> ProviderAdapter:
        api_key = self._api_key(spec)
        model = self._default_model(spec) or spec.provider_name
        if spec.provider_name == "ollama":
            return OllamaSdkProvider(
                provider_name=spec.provider_name,
                default_model=model,
                host=self._settings.ollama_base_url,
            )
        if not api_key:
            raise ProviderError(f"{spec.display_name} API key is not configured.")
        if spec.provider_name == "openai":
            return OpenAISdkProvider(
                provider_name=spec.provider_name,
                default_model=model,
                api_key=api_key,
                base_url=self._settings.openai_base_url,
            )
        if spec.provider_name == "anthropic":
            return AnthropicSdkProvider(
                provider_name=spec.provider_name,
                default_model=model,
                api_key=api_key,
            )
        if spec.provider_name == "gemini":
            return GeminiSdkProvider(
                provider_name=spec.provider_name,
                default_model=model,
                api_key=api_key,
            )
        if spec.provider_name == "mistral":
            return MistralSdkProvider(
                provider_name=spec.provider_name,
                default_model=model,
                api_key=api_key,
                server_url=self._settings.mistral_base_url,
            )
        raise ProviderError(f"{spec.display_name} official SDK adapter is not implemented.")

    def _base_url(self, spec: ProviderSpec) -> str | None:
        return {
            "openai": self._settings.openai_base_url,
            "ollama": f"{self._settings.ollama_base_url.rstrip('/')}/v1",
            "mistral": self._settings.mistral_base_url,
            "openrouter": self._settings.openrouter_base_url,
            "groq": self._settings.groq_base_url,
            "xai": self._settings.xai_base_url,
            "custom-openai": self._settings.custom_openai_base_url,
        }.get(spec.provider_name)

    def _default_model(self, spec: ProviderSpec) -> str | None:
        return {
            "openai": self._settings.openai_model,
            "ollama": self._settings.ollama_model,
            "anthropic": self._settings.anthropic_model,
            "gemini": self._settings.gemini_model,
            "mistral": self._settings.mistral_model,
            "openrouter": self._settings.openrouter_model,
            "groq": self._settings.groq_model,
            "xai": self._settings.xai_model,
            "custom-openai": self._settings.custom_openai_model,
        }.get(spec.provider_name) or spec.default_model


def provider_registry(settings: Settings | None = None) -> ProviderRegistry:
    return ProviderRegistry(settings)
