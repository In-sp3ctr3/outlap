from __future__ import annotations

from raceweek.core.models import AgentChatRequest, AgentChatResponse


def answer_chat(request: AgentChatRequest) -> AgentChatResponse:
    conversation_id = request.conversation_id or "conv_demo"
    if request.provider_name == "fake-fail":
        return AgentChatResponse(
            conversation_id=conversation_id,
            provider_name=request.provider_name,
            status="fallback",
            message=(
                "Provider failed, so I am using the deterministic optimizer output only. "
                "The deterministic optimizer remains the source of truth; manually apply any moves."
            ),
            cited_recommendation_run_id=request.recommendation_run_id,
            tool_calls=[
                {
                    "tool": "get_latest_recommendation",
                    "mode": "read_only",
                    "status": "used_fallback_context",
                }
            ],
            can_mutate_fantasy_account=False,
        )

    return AgentChatResponse(
        conversation_id=conversation_id,
        provider_name=request.provider_name,
        status="ok",
        message=(
            "The safest plan is to trust the top deterministic recommendation, avoid auto-transfer "
            "execution, and rerun projections if weather or penalty news changes."
        ),
        cited_recommendation_run_id=request.recommendation_run_id,
        tool_calls=[
            {
                "tool": "explain_recommendation",
                "mode": "read_only",
                "status": "completed",
            }
        ],
        can_mutate_fantasy_account=False,
    )
