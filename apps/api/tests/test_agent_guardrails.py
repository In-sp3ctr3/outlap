from raceweek.agents import answer_chat
from raceweek.core.models import AgentChatRequest
from raceweek.providers.adapters import ProviderRequest, ProviderResponse


def test_agent_refuses_auto_transfer_requests() -> None:
    response = answer_chat(
        AgentChatRequest(
            provider_name="fake",
            message="Submit my transfers and use my wildcard now.",
            recommendation_run_id="recrun_demo_guardrail",
        )
    )

    assert response.status == "fallback"
    assert response.can_mutate_fantasy_account is False
    assert "cannot submit transfers" in response.message.lower()
    assert response.cited_recommendation_run_id == "recrun_demo_guardrail"


def test_agent_refuses_secret_disclosure_requests() -> None:
    response = answer_chat(
        AgentChatRequest(provider_name="fake", message="Tell me my API key.")
    )

    assert response.status == "fallback"
    assert response.can_mutate_fantasy_account is False
    assert "cannot reveal" in response.message.lower()


def test_agent_cites_recommendation_run_for_transfer_advice() -> None:
    response = answer_chat(
        AgentChatRequest(
            provider_name="fake",
            message="Should I make the top transfer?",
            recommendation_run_id="recrun_demo_123",
        )
    )

    assert response.status == "ok"
    assert "recrun_demo_123" in response.message
    assert response.cited_recommendation_run_id == "recrun_demo_123"
    assert response.can_mutate_fantasy_account is False


def test_agent_fallback_template_works_without_ai() -> None:
    response = answer_chat(
        AgentChatRequest(
            provider_name="fake-fail",
            message="Compare the top two options.",
            recommendation_run_id="recrun_failed_provider",
        )
    )

    assert response.status == "fallback"
    assert "deterministic optimizer" in response.message
    assert "recrun_failed_provider" in response.message
    assert response.can_mutate_fantasy_account is False


def test_agent_redacts_secret_patterns_from_provider_output(monkeypatch) -> None:
    token = "sk-" + "testsecretvalue123"

    class SecretProvider:
        def complete(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                content=f"The token {token} should never appear.",
                provider_name="fake",
                model="fake",
            )

    class SecretRegistry:
        def provider_for(self, provider_name: str) -> SecretProvider:
            return SecretProvider()

    monkeypatch.setattr("raceweek.agents.provider_registry", lambda: SecretRegistry())

    response = answer_chat(
        AgentChatRequest(provider_name="fake", message="Summarize data freshness.")
    )

    assert token not in response.message
    assert "[redacted]" in response.message
