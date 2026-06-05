# 08 — AI Provider and Agent Architecture

## Principle

The AI assistant is an explanation, comparison, and interaction layer over deterministic data and optimizer outputs. It is not the calculation engine.

## Required providers

v1 must support:

| Provider | Adapter strategy | Notes |
|---|---|---|
| OpenAI | Official `openai` Python SDK; Responses API where available | Use for tool-capable hosted models |
| Anthropic Claude | Official `anthropic` Python SDK | Messages API/tool use |
| Google Gemini | Official `google-genai` SDK | Developer API or Vertex-compatible config |
| Ollama | Local SDK or OpenAI-compatible endpoint | Default local option; no API key needed for local |
| OpenRouter | OpenAI-compatible chat endpoint | User supplies key and model slug |
| Groq | OpenAI-compatible endpoint | User supplies key and model |
| xAI | OpenAI-compatible endpoint | User supplies key and model |
| Mistral | Official `mistralai` SDK or OpenAI-compatible where configured | Pin safe SDK version |
| Custom OpenAI-compatible | OpenAI SDK with configurable base URL | For LM Studio, vLLM, local gateways, etc. |

## Provider configuration

Provider config must not store raw secrets. Store only env var names or local encrypted references.

Example:

```json
{
  "providerName": "openrouter",
  "displayName": "OpenRouter",
  "baseUrl": "https://openrouter.ai/api/v1",
  "defaultModel": "user-selected-model",
  "apiKeyEnvVar": "OPENROUTER_API_KEY",
  "enabled": true,
  "supportsStreaming": true,
  "supportsTools": false
}
```

## Provider interface

```python
class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant', 'tool']
    content: str
    tool_call_id: str | None = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]

class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str
    tools: list[ToolDefinition] = []
    temperature: float = 0.2
    max_output_tokens: int = 4000
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    content: str
    tool_calls: list[ToolCall] = []
    model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
```

## Tool model

LLM tools are read-only. Mutating actions require explicit user confirmation in the UI and remain local-only metadata actions.

### Required tools

| Tool | Purpose | Mutates? |
|---|---|---:|
| `get_current_team` | Fetch team snapshot | No |
| `get_market_snapshot` | Fetch assets/prices/projections | No |
| `get_data_health` | Fetch connector status | No |
| `run_projection` | Create projection run | Yes, local data only |
| `run_optimizer` | Create recommendation run | Yes, local data only |
| `get_recommendation_run` | Fetch recommendations | No |
| `compare_recommendations` | Compare option IDs | No |
| `search_news` | Search stored news items | No |
| `explain_rules` | Retrieve configured rules | No |
| `get_league_analysis` | Fetch league analytics | No |

Important: `run_projection` and `run_optimizer` mutate the local database by creating runs, but they do not touch the user's fantasy account.

## Agent workflow

### Strategy question workflow

```text
User asks strategy question
  → classify intent
  → fetch current team + data health
  → run optimizer if no recent compatible run exists
  → fetch top recommendation options
  → produce explanation with assumptions/warnings
```

### News workflow

```text
User asks about news impact
  → search stored news
  → map entities to assets
  → fetch projections/recommendations
  → explain risk impact
```

### Chip workflow

```text
User asks whether to use chip
  → fetch chip state
  → simulate no-chip and chip scenarios
  → compare expected net points, risk, future opportunity cost
  → explain use/save recommendation
```

## System prompt requirements

The system prompt must include:

- unofficial tool disclaimer;
- deterministic source-of-truth rule;
- no auto-transfer rule;
- uncertainty and data freshness rule;
- concise but actionable output format;
- no API key or secret disclosure;
- no claims beyond data.

See `examples/prompts/agent-system-prompt.md`.

## AI answer format

Default recommendation answer:

```text
Recommendation: [action]
Confidence: [low/medium/high + numeric if available]
Expected impact: [gross, penalty, net]
Why: [3 bullets max]
Risks: [key risks]
What would change this: [conditions]
Data freshness: [source statuses]
```

## Hallucination controls

- The LLM cannot call external web directly in product runtime unless a provider/tool is explicitly configured.
- Use local stored data and connector snapshots.
- Always pass rules as structured JSON, not just prose.
- Require recommendation IDs in any answer that advises a transfer.
- Post-process AI response to detect banned claims:
  - “guaranteed”;
  - “official” affiliation;
  - “I made the transfer”;
  - raw secret patterns.

## Provider fallback

Provider fallback order is user-configurable. Default recommendation:

1. selected provider/model;
2. local Ollama model if configured;
3. no-AI deterministic explanation template.

The app must remain useful without AI.

## Prompt/eval testing

Create eval fixtures for:

- transfer recommendation explanation;
- chip recommendation explanation;
- missing-data warning;
- stale-data warning;
- league differential strategy;
- provider failure fallback;
- refusal to auto-submit transfers;
- refusal to claim official affiliation.

For each fixture, assert:

- includes recommendation/run IDs when applicable;
- does not invent drivers/prices;
- includes risk/data freshness where relevant;
- does not expose secrets;
- stays within output shape.
