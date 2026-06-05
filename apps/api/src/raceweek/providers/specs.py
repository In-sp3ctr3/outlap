from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSpec:
    provider_name: str
    display_name: str
    default_model: str | None = None
    supports_streaming: bool = True
    supports_tools: bool = False
    api_key_env_var: str | None = None
    adapter_family: str = "registered"


PROVIDER_SPECS = [
    ProviderSpec(
        "fake",
        "Fake deterministic provider",
        default_model="fake-strategist",
        supports_tools=True,
        adapter_family="fake",
    ),
    ProviderSpec(
        "fake-fail",
        "Fake failing provider",
        default_model="fake-failure",
        adapter_family="fake",
    ),
    ProviderSpec(
        "ollama",
        "Ollama local",
        default_model="llama3.1",
        supports_tools=True,
        adapter_family="official-ollama",
    ),
    ProviderSpec(
        "openai",
        "OpenAI",
        default_model="gpt-5.4",
        supports_tools=True,
        api_key_env_var="OPENAI_API_KEY",
        adapter_family="official-openai",
    ),
    ProviderSpec(
        "anthropic",
        "Anthropic Claude",
        default_model="claude-sonnet-4-5",
        supports_tools=True,
        api_key_env_var="ANTHROPIC_API_KEY",
        adapter_family="official-anthropic",
    ),
    ProviderSpec(
        "gemini",
        "Google Gemini",
        default_model="gemini-2.5-pro",
        supports_tools=True,
        api_key_env_var="GEMINI_API_KEY",
        adapter_family="official-gemini",
    ),
    ProviderSpec(
        "mistral",
        "Mistral",
        default_model="mistral-large-latest",
        api_key_env_var="MISTRAL_API_KEY",
        adapter_family="official-mistral",
    ),
    ProviderSpec(
        "openrouter",
        "OpenRouter",
        default_model="openrouter/auto",
        api_key_env_var="OPENROUTER_API_KEY",
        adapter_family="openai-compatible",
    ),
    ProviderSpec(
        "groq",
        "Groq",
        default_model="llama-3.3-70b-versatile",
        api_key_env_var="GROQ_API_KEY",
        adapter_family="openai-compatible",
    ),
    ProviderSpec(
        "xai",
        "xAI",
        default_model="grok-4",
        api_key_env_var="XAI_API_KEY",
        adapter_family="openai-compatible",
    ),
    ProviderSpec(
        "custom-openai",
        "Custom OpenAI-compatible",
        supports_tools=True,
        api_key_env_var="CUSTOM_OPENAI_API_KEY",
        adapter_family="openai-compatible",
    ),
]
