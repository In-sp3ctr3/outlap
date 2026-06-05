# 15 — Observability and Operations

## Operational goal

Users should always know whether recommendations are based on fresh, complete data or stale/degraded data.

## Observability surfaces

### Data Health page

Shows every source:

- status;
- last successful sync;
- last attempted sync;
- freshness;
- rate-limit state;
- latest error;
- connector version;
- user action.

### Recommendation provenance panel

Every recommendation option has a “Why this?” or “Sources” panel showing:

- recommendation run ID;
- projection run ID;
- ruleset version;
- optimizer version;
- source snapshot IDs;
- data freshness;
- assumptions;
- warnings.

### Logs

Use structured JSON logs in API:

```json
{
  "level": "INFO",
  "event": "optimizer.run.completed",
  "requestId": "req_...",
  "recommendationRunId": "recrun_...",
  "durationMs": 83
}
```

## Log redaction

Implement a central redactor for:

- authorization headers;
- cookies;
- API keys;
- bearer tokens;
- high-entropy strings;
- provider request bodies when configured.

## Connector run records

Each sync should record:

- sync ID;
- source;
- start/end time;
- status;
- rows fetched;
- rows normalized;
- snapshot IDs;
- error message;
- retry count.

This can be implemented as a table later, but v1 must at least expose source status from `source_snapshots` and logs.

## Health checks

`GET /health` returns API process health.

`GET /api/v1/app/status` returns:

- version;
- setup status;
- DB status;
- current event;
- required connector availability.

Do not make `/health` fail because an external API is down. External source health belongs in data-source status.

## Local troubleshooting UX

Settings/Data Health should include actions:

- retry sync;
- force refresh;
- disable source;
- switch to manual import;
- clear cache;
- open logs location;
- export diagnostics without secrets.

## Diagnostics export

Diagnostics export must include:

- app version;
- OS/container metadata if available;
- connector statuses;
- last 100 redacted logs;
- OpenAPI version;
- schema versions;
- dependency versions;
- no secrets;
- no raw tokens;
- no raw full news articles.
