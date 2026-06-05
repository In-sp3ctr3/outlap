# 07 — API Design Notes

The canonical API contract lives in `api/openapi.yaml`. This document explains conventions and implementation expectations.

## API principles

- Prefix all product endpoints with `/api/v1`.
- Return typed JSON only.
- Use ISO-8601 UTC timestamps.
- Use `snake_case` in Python internals and `camelCase` in API JSON.
- Validate all request bodies with Pydantic.
- Return stable error envelopes.
- Do not expose secrets.
- Include `runId`, `snapshotId`, or `source` fields whenever a response is derived from stored data.

## Error envelope

```json
{
  "error": {
    "code": "DATA_SOURCE_STALE",
    "message": "Fantasy market data is stale.",
    "details": {
      "source": "fantasy_api",
      "lastSuccessfulSyncAt": "2026-06-05T12:00:00Z"
    },
    "requestId": "req_..."
  }
}
```

## Pagination

Use cursor pagination for large collections:

```json
{
  "items": [],
  "nextCursor": "cursor_..."
}
```

## Endpoint groups

### Health and metadata

- `GET /health`
- `GET /api/v1/app/status`
- `GET /api/v1/data-sources/status`

### Setup and settings

- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/providers`
- `POST /api/v1/providers/test`

### Fantasy

- `POST /api/v1/fantasy/import/team`
- `POST /api/v1/fantasy/import/market`
- `POST /api/v1/fantasy/sync`
- `GET /api/v1/fantasy/assets`
- `GET /api/v1/fantasy/teams/current`
- `GET /api/v1/fantasy/rulesets/current`

### Race week

- `GET /api/v1/races`
- `GET /api/v1/races/current`
- `GET /api/v1/races/{meetingKey}/sessions`
- `GET /api/v1/races/{meetingKey}/intelligence`

### Projections and optimizer

- `POST /api/v1/projections/run`
- `GET /api/v1/projections/runs/{projectionRunId}`
- `POST /api/v1/optimizer/recommendations`
- `GET /api/v1/recommendations/runs/{recommendationRunId}`
- `GET /api/v1/recommendations/options/{optionId}`

### League

- `POST /api/v1/leagues/import`
- `GET /api/v1/leagues/{leagueId}/analysis`

### Agent

- `POST /api/v1/agent/conversations`
- `GET /api/v1/agent/conversations/{conversationId}`
- `POST /api/v1/agent/chat`

## API implementation expectations

Controllers should call use cases, not repositories directly.

Example layering:

```text
api/routes/optimizer.py
  -> use_cases/generate_recommendations.py
    -> core/rules.py
    -> core/projections.py
    -> core/optimizer.py
    -> storage/repositories.py
```

## Streaming

AI chat should support server-sent events in v1 if practical:

```text
POST /api/v1/agent/chat?stream=true
Content-Type: text/event-stream
```

Non-streaming response must always be supported.

## Idempotency

Sync and optimization endpoints should accept an optional `idempotencyKey`:

```json
{
  "idempotencyKey": "client-generated-key"
}
```

If repeated, return the existing run/result where safe.

## API security

Local mode can use no authentication by default on `localhost`, but production/hosted mode must require auth. Add a configuration flag:

```env
APP_AUTH_MODE=local_only | single_user_password | reverse_proxy
```

For v1 local mode:

- bind API to `127.0.0.1` by default;
- CORS only allows configured web origin;
- redact secrets in logs.
