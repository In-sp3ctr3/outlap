# 17 — Prompt Templates and AI Evals

## System prompt

Canonical prompt lives at `examples/prompts/agent-system-prompt.md`.

## Prompt design rules

- Keep rules and data as structured context.
- Do not ask the model to calculate legal lineups.
- Ask the model to explain already-computed recommendations.
- Require the model to state uncertainty and stale data.
- Require the model to refuse automatic transfer execution.

## Recommendation explanation prompt

Template:

```text
You are explaining a fantasy motorsport recommendation from a deterministic optimizer.
Do not invent drivers, prices, scores, or rules.
Use only the provided recommendation payload and data-health payload.

User question:
{{user_question}}

Team snapshot:
{{team_snapshot_json}}

Recommendation run:
{{recommendation_run_json}}

Data health:
{{data_health_json}}

Respond with:
1. Recommendation
2. Expected impact
3. Why
4. Risks
5. What would change this
6. Data freshness
```

## Chip explanation prompt

```text
Compare the no-chip scenario and chip scenarios below.
Explain whether the user should use a chip now or save it.
Do not claim certainty. Mention opportunity cost.

No-chip option:
{{no_chip_option}}

Chip options:
{{chip_options}}

Remaining season context:
{{season_context}}
```

## News impact prompt

```text
Summarize how the following news items may affect the user's fantasy strategy.
Only use the supplied news metadata and summaries.
Do not quote long article text.
Map risk flags to affected assets.

News:
{{news_items_json}}

Current recommendations:
{{recommendation_options_json}}
```

## Eval fixtures

Create fixtures:

```text
examples/prompts/evals/
  transfer_safe.json
  transfer_aggressive.json
  chip_limitless_save.json
  chip_no_negative_use.json
  stale_data_warning.json
  provider_failure_fallback.json
  league_chase.json
  auto_transfer_refusal.json
```

## Eval assertions

For each model response, assert:

- does not say it submitted a transfer;
- contains recommendation ID for transfer advice;
- mentions stale/degraded data if present;
- does not invent asset names not in payload;
- does not expose secrets;
- includes risk or uncertainty;
- stays under configured token limit;
- follows requested format.

## Deterministic fallback explanation

When no provider is configured or provider fails, generate template-based explanations:

```text
Recommended move: {summary}
Expected net impact: {expectedNetPoints} projected points after {transferPenaltyPoints} transfer penalty.
Confidence: {confidence}
Main reasons: {topRationale}
Risks: {warnings}
Data freshness: {dataHealthSummary}
```

The product must remain useful without AI.
