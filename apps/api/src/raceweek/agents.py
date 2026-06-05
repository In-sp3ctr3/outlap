from __future__ import annotations

import re

from raceweek.core.models import AgentChatRequest, AgentChatResponse
from raceweek.providers.adapters import ChatMessage, ProviderError, ProviderRequest
from raceweek.providers.registry import provider_registry

_BANNED_CLAIMS = (
    "guaranteed",
    "official formula 1",
    "official f1",
    "i made the transfer",
    "i submitted the transfer",
)
_SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{24,})"
)


def answer_chat(request: AgentChatRequest) -> AgentChatResponse:
    conversation_id = request.conversation_id or "conv_demo"
    if _asks_for_secret(request.message):
        return _fallback_response(
            request,
            conversation_id,
            "I cannot reveal, request, or handle passwords, API keys, session tokens, or other "
            "secrets. Keep credentials in local environment variables and never paste them into "
            "strategy chat.",
            tool_status="refused_secret_request",
        )
    if _asks_to_mutate_account(request.message):
        return _fallback_response(
            request,
            conversation_id,
            "I cannot submit transfers, apply chips, or mutate your fantasy account. "
            "Use the deterministic recommendation run as read-only guidance and apply any "
            "moves manually.",
            tool_status="refused_mutation_request",
        )
    if request.provider_name == "fake-fail":
        try:
            provider_registry().provider_for(request.provider_name).complete(
                ProviderRequest(messages=_messages_for(request))
            )
        except ProviderError:
            return _fallback_response(
                request,
                conversation_id,
                _fallback_message(request.recommendation_run_id),
                tool_status="used_fallback_context",
            )
    if _needs_recommendation_id(request.message) and not request.recommendation_run_id:
        return _fallback_response(
            request,
            conversation_id,
            "I need a deterministic recommendation run before giving transfer or chip advice. "
            "The deterministic optimizer is the source of truth; run it first so the answer "
            "can cite a recommendation ID.",
            tool_status="missing_recommendation_run",
        )

    try:
        provider_response = provider_registry().provider_for(request.provider_name).complete(
            ProviderRequest(messages=_messages_for(request))
        )
    except ProviderError:
        return _fallback_response(
            request,
            conversation_id,
            _fallback_message(request.recommendation_run_id),
            tool_status="used_fallback_context",
        )

    message = _post_process_message(provider_response.content, request)
    if _has_banned_claim(message):
        return _fallback_response(
            request,
            conversation_id,
            _fallback_message(request.recommendation_run_id),
            tool_status="blocked_banned_claim",
        )

    return AgentChatResponse(
        conversation_id=conversation_id,
        provider_name=request.provider_name,
        status="ok",
        message=message,
        cited_recommendation_run_id=request.recommendation_run_id,
        tool_calls=[
            {
                "tool": "explain_recommendation",
                "mode": "read_only",
                "status": "completed",
                "providerModel": provider_response.model,
            }
        ],
        can_mutate_fantasy_account=False,
    )


def _messages_for(request: AgentChatRequest) -> list[ChatMessage]:
    recommendation_context = (
        f"Recommendation run ID: {request.recommendation_run_id}."
        if request.recommendation_run_id
        else "No recommendation run ID was supplied."
    )
    return [
        ChatMessage(
            role="system",
            content=(
                "You are an unofficial RaceWeek Strategist explanation layer. "
                "Deterministic projections and optimizer outputs are the source of truth. "
                "Do not calculate final lineups, budgets, penalties, or fantasy scores. "
                "Do not submit transfers or mutate fantasy accounts. "
                "Do not expose API keys or secrets. "
                "Cite recommendation IDs when discussing transfer or chip advice."
            ),
        ),
        ChatMessage(
            role="user",
            content=f"{recommendation_context}\n\nUser question: {request.message}",
        ),
    ]


def _fallback_response(
    request: AgentChatRequest,
    conversation_id: str,
    message: str,
    *,
    tool_status: str,
) -> AgentChatResponse:
    return AgentChatResponse(
        conversation_id=conversation_id,
        provider_name=request.provider_name,
        status="fallback",
        message=message,
        cited_recommendation_run_id=request.recommendation_run_id,
        tool_calls=[
            {
                "tool": "get_latest_recommendation",
                "mode": "read_only",
                "status": tool_status,
            }
        ],
        can_mutate_fantasy_account=False,
    )


def _fallback_message(recommendation_run_id: str | None) -> str:
    suffix = (
        f" Reference recommendation run: {recommendation_run_id}."
        if recommendation_run_id
        else ""
    )
    return (
        "Provider failed, so I am using the deterministic optimizer output only. "
        "The deterministic optimizer remains the source of truth; manually apply any moves."
        f"{suffix}"
    )


def _post_process_message(content: str, request: AgentChatRequest) -> str:
    cleaned = _SECRET_PATTERN.sub("[redacted]", content).strip()
    if (
        request.recommendation_run_id
        and _needs_recommendation_id(request.message)
        and request.recommendation_run_id not in cleaned
    ):
        cleaned = f"{cleaned}\n\nReference recommendation run: {request.recommendation_run_id}."
    return cleaned


def _asks_to_mutate_account(message: str) -> bool:
    lowered = message.lower()
    mutation_terms = ("submit", "apply", "execute", "confirm", "lock in", "save my")
    account_terms = ("transfer", "transfers", "chip", "wildcard", "lineup", "team")
    return any(term in lowered for term in mutation_terms) and any(
        term in lowered for term in account_terms
    )


def _asks_for_secret(message: str) -> bool:
    lowered = message.lower()
    disclosure_terms = ("show", "tell", "reveal", "print", "what is", "give me")
    secret_terms = ("password", "api key", "secret", "session token", "token")
    return any(term in lowered for term in disclosure_terms) and any(
        term in lowered for term in secret_terms
    )


def _needs_recommendation_id(message: str) -> bool:
    lowered = message.lower()
    advice_terms = ("transfer", "lineup", "chip", "wildcard", "boost", "recommendation")
    return any(term in lowered for term in advice_terms)


def _has_banned_claim(message: str) -> bool:
    lowered = message.lower()
    return any(claim in lowered for claim in _BANNED_CLAIMS)
