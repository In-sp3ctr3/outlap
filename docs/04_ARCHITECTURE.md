# 04 — System Architecture

## Architectural style

Use a hexagonal/ports-and-adapters architecture.

```text
                 ┌──────────────────────┐
                 │      Web UI          │
                 │  Next.js / React     │
                 └──────────┬───────────┘
                            │ HTTP/OpenAPI
                 ┌──────────▼───────────┐
                 │      API Layer       │
                 │ FastAPI Controllers  │
                 └──────────┬───────────┘
                            │ use cases
┌───────────────────────────▼───────────────────────────┐
│                    Domain Core                         │
│ Rules • Projections • Optimizer • Recommendations      │
│ Pure functions where possible                          │
└───────────────┬───────────────┬───────────────┬────────┘
                │               │               │
        ┌───────▼───────┐ ┌────▼─────┐ ┌──────▼──────┐
        │ Data Ports    │ │ AI Ports │ │ Storage Port │
        └───────┬───────┘ └────┬─────┘ └──────┬──────┘
                │              │              │
┌───────────────▼─────────┐ ┌──▼────────────┐ ┌▼──────────┐
│ Connectors              │ │ Provider SDKs │ │ DuckDB     │
│ Fantasy/OpenF1/Jolpica  │ │ OpenAI/etc.   │ │ snapshots  │
└─────────────────────────┘ └───────────────┘ └───────────┘
```

## Monorepo structure

```text
outlap/
  apps/
    api/
      src/raceweek/
        api/                 # FastAPI routers and dependencies
        core/                # pure domain logic
        connectors/          # external data adapters
        storage/             # DuckDB repository implementations
        agents/              # provider adapters and tool orchestration
        jobs/                # sync jobs and schedulers
        settings.py
      tests/
    web/
      app/
      components/
      lib/
      tests/
  packages/
    contracts/               # shared JSON schema, generated TS types
    fixtures/                # safe demo data
    ui/                      # reusable UI primitives if needed
  docs/
  api/
    openapi.yaml
  schemas/
  data/
    .gitkeep                 # local DuckDB lives here, gitignored
  docker-compose.yml
  Makefile
```

## Logical modules

### 1. Rules engine

Owns fantasy game constraints:

- lineup composition;
- budget/cost cap;
- transfer allowances;
- transfer penalties;
- net-transfer counting;
- chip effects;
- deadline/lock handling;
- scoring-rule configuration.

Rules are versioned by season and game version.

### 2. Data ingestion

Owns fetching, caching, raw snapshot storage, normalization, and data health.

Connectors:

- fantasy connector;
- manual import connector;
- OpenF1 connector;
- Jolpica connector;
- FastF1 adapter;
- RSS/news connector;
- weather connector if separate from OpenF1.

### 3. Feature engine

Transforms normalized data into model-ready features:

- rolling fantasy points;
- rolling price deltas;
- points per million;
- qualifying form;
- race pace indicators;
- teammate deltas;
- constructor reliability;
- DNF/penalty risk;
- weather/race-control risk;
- ownership/differential score.

### 4. Projection engine

Produces transparent expected points and uncertainty bands for each asset and event.

Default v1 projection model:

- weighted heuristic model;
- configurable weights;
- feature contribution breakdown;
- no opaque LLM predictions.

### 5. Optimizer

Produces legal recommendations using projections, rules, risk preferences, and strategy mode weights.

Output is ranked recommendation options with:

- proposed transfers;
- chip action;
- expected gross points;
- transfer penalty;
- net expected points;
- budget after move;
- risk;
- confidence;
- assumptions;
- explanation payload for AI.

### 6. AI agent layer

The agent layer exposes read-only tools to the LLM. The LLM may ask the deterministic services for calculations and then explain them.

Provider adapters implement a common interface:

```python
class AiProvider(Protocol):
    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...
    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[ChatCompletionChunk]: ...
    async def list_models(self) -> list[ModelInfo]: ...
```

### 7. API layer

FastAPI exposes typed endpoints documented in `api/openapi.yaml`. Controllers must remain thin and call use cases.

### 8. Web UI

Next.js web app consumes the API and handles:

- setup wizard;
- dashboard;
- market;
- optimizer;
- race week;
- league analysis;
- AI chat;
- settings;
- data health.

## Data flow

```text
External APIs / manual files
  → raw source_snapshots
  → normalized domain tables
  → feature tables
  → projection runs
  → optimizer runs
  → recommendation options
  → AI explanation/chat
  → UI
```

## Snapshot and reproducibility requirement

Every recommendation must be reproducible.

For each recommendation run store:

- run ID;
- timestamp;
- source snapshot IDs;
- fantasy rules version;
- projection model version;
- optimizer version;
- strategy mode and weights;
- request payload;
- ranked output payload;
- AI explanation metadata, if any.

## Error handling architecture

External data failures must produce structured degraded states:

```json
{
  "source": "openf1",
  "status": "degraded",
  "severity": "warning",
  "message": "Weather endpoint unavailable; using last successful snapshot from 2026-06-05T12:00:00Z",
  "lastSuccessfulSyncAt": "2026-06-05T12:00:00Z"
}
```

Do not allow connector exceptions to crash the dashboard.

## Security boundaries

- Browser never receives provider API keys.
- API logs redact headers and secrets.
- Provider requests include only the minimum relevant strategy context.
- Stored raw snapshots must not include authentication tokens.
- User can delete all local data.

## Extensibility points

- `FantasyDataProvider`
- `RaceDataProvider`
- `NewsProvider`
- `ProjectionModel`
- `OptimizerStrategy`
- `AiProvider`
- `UiPlugin` later, but not necessary in v1.
