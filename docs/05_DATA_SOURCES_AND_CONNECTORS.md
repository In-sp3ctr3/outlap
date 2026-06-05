# 05 — Data Sources and Connectors

## Source strategy

The app must not rely on a single fragile data source. Use adapters with explicit provenance, caching, and fallback.

Data source priority:

1. User manual import when authenticated sources are unavailable or legally uncertain.
2. Read-only fantasy connector using user-provided session/token when user opts in.
3. Public motorsport data APIs for race/session context.
4. RSS/news feeds for headlines and short summaries.
5. Fixture/demo data for tests and demos.

## Connector rules

Every connector must:

- implement a typed port/interface;
- save raw snapshots before normalization;
- save source metadata and response hash;
- use rate limits and retries;
- never log secrets;
- degrade gracefully;
- include contract tests using fixtures or mocked HTTP;
- expose a data-health status.

## Fantasy data connector

### Important status

The fantasy game API is not treated as a stable official public API. It is an optional read-only connector. The product must work with manual import even if this connector breaks.

### Known base URL

Community documentation describes this REST base URL:

```text
https://fantasy-api.formula1.com/partner_games/f1
```

The game-version segment has historically appeared as `2022` in documented paths. Do **not** hardcode that value in code; configure it:

```env
FANTASY_API_BASE_URL=https://fantasy-api.formula1.com/partner_games/f1
FANTASY_GAME_VERSION=2022
```

### Documented endpoints to support

These paths are documented by community/third-party sources and must be implemented through a configurable endpoint map:

| Resource | Method | Path template | Data selector | Required? |
|---|---|---|---|---:|
| players | GET | `{game_version}/players` | `players` | Yes |
| teams | GET | `{game_version}/teams` | `teams` | Yes |
| leaderboards | GET | `{game_version}/leaderboards/leagues?league_id={league_id}` | `leaderboards` | Yes, when league ID exists |
| live_stats | GET | `{game_version}/live_stats?game_period_id={game_period_id}` | `live_stats` | Yes |
| picked_teams | GET | `{game_version}/picked_teams/for_slot?game_period_id={game_period_id}&slot={slot}&user_global_id={user_global_id}` | `picked_teams` | Yes, when authenticated/imported context exists |

### Authentication approach

v1 must not ask for or store the user's official account password.

Allowed v1 approaches:

- manual import;
- user-pasted session/bearer token in local `.env` or local settings;
- browser-devtools token extraction instructions in docs, clearly marked advanced and user-responsibility;
- local-only encrypted storage if UI entry is implemented.

Disallowed in v1:

- automated login with username/password;
- scraping browser cookies without explicit user action;
- submitting transfers;
- bypassing rate limits or anti-bot controls.

### Fantasy connector port

```python
class FantasyDataProvider(Protocol):
    async def get_assets(self) -> list[FantasyAssetRaw]: ...
    async def get_constructors(self) -> list[FantasyConstructorRaw]: ...
    async def get_live_stats(self, game_period_id: str) -> FantasyLiveStatsRaw: ...
    async def get_league_leaderboard(self, league_id: str) -> FantasyLeaderboardRaw: ...
    async def get_picked_team(self, game_period_id: str, slot: int, user_global_id: str) -> FantasyPickedTeamRaw: ...
    async def health(self) -> DataSourceStatus: ...
```

### Manual import

Manual import is a first-class connector, not a fallback afterthought.

Supported formats:

- `fantasy_team.json`
- `fantasy_market_snapshot.json`
- `fantasy_scores.csv`
- `fantasy_league.csv`

Required import validation:

- schema validation;
- asset type validation;
- price numeric validation;
- no duplicate lineup assets;
- budget legality validation;
- warnings for unknown fields, not failure.

## OpenF1 connector

Use OpenF1 for recent/historical race-week context from 2023 onward.

Recommended base URL:

```text
https://api.openf1.org/v1
```

OpenF1 endpoints to support in v1:

| Endpoint | Use |
|---|---|
| `/meetings` | Race calendar/meetings |
| `/sessions` | FP/Quali/Sprint/Race sessions |
| `/drivers` | Driver metadata |
| `/session_result` | Session classification/results |
| `/starting_grid` | Grid context |
| `/position` | Position changes |
| `/laps` | Lap/pace features |
| `/stints` | Tyre/stint features |
| `/pit` | Pit-stop summary |
| `/race_control` | flags, penalties, incidents |
| `/weather` | observed session weather |
| `/championship` | standings context where available |

Rate limits and data availability must be configurable. The free historical API should be treated as rate-limited. Cache aggressively.

## Jolpica connector

Use Jolpica as an Ergast-compatible source for schedules, results, qualifying, sprint, standings, and historical context.

Recommended base URL:

```text
https://api.jolpi.ca/ergast/f1
```

Use Jolpica for:

- race calendar;
- race results;
- qualifying results;
- sprint results;
- driver standings;
- constructor standings;
- historical backtesting data.

## FastF1 adapter

Use FastF1 for Python-based data access and feature engineering where it adds value:

- schedules;
- session results;
- timing data;
- telemetry-derived features;
- caching;
- fallback to Jolpica-derived historical results.

Do not expose raw heavy telemetry in v1 UI unless needed for features. Store aggregated features, not large raw telemetry blobs by default.

## News connector

### Purpose

News helps flag uncertainty. It must not become a copyright-risk content mirror.

Supported v1 news ingestion:

- RSS/Atom feeds configured by user/maintainer;
- official article metadata when allowed;
- title, source, URL, published time, summary snippet, extracted entities;
- AI-generated short summary from retrieved permitted text or feed summary;
- manual user-added news note.

Disallowed:

- storing full copyrighted articles by default;
- bypassing paywalls;
- copying images;
- training models on scraped articles;
- using news content without provenance.

### News item schema

```json
{
  "id": "news_...",
  "source": "rss:f1-news-example",
  "title": "string",
  "url": "string",
  "publishedAt": "datetime",
  "retrievedAt": "datetime",
  "summary": "short generated or feed-provided summary",
  "entities": ["driver:...", "constructor:..."],
  "riskFlags": ["grid_penalty", "illness", "upgrade", "reliability"],
  "licenseNote": "metadata-only"
}
```

## Weather

v1 uses OpenF1 observed weather for sessions. Future forecasts are optional and should be configured through a generic weather provider interface.

If forecast is absent, do not invent it. Use `unknown` and show a UI warning.

## Data health statuses

Allowed statuses:

- `ok`
- `stale`
- `degraded`
- `error`
- `disabled`
- `unknown`

Each status includes:

- source;
- last successful sync;
- last attempted sync;
- freshness seconds;
- rate-limit status;
- error code/message;
- user-action message.

## Caching policy

| Data type | Race-week TTL | Off-week TTL | Notes |
|---|---:|---:|---|
| Fantasy market | 15 min | 6 hr | Prices/scores can change after events |
| User team | 5 min | 1 hr | Manual refresh allowed |
| Race calendar | 24 hr | 7 days | Low volatility |
| Session results | 2 min during live session | immutable after final + 12 hr | Mark provisional/final |
| Weather observations | 2 min during live session | immutable after final | Observed weather only |
| News feeds | 10 min | 30 min | Respect feed cache headers |
| Provider models | 24 hr | 24 hr | Not critical |

## Connector implementation pattern

```python
@dataclass(frozen=True)
class ConnectorResult[T]:
    source: str
    fetched_at: datetime
    raw_snapshot_id: str
    data: T
    status: DataSourceStatus

class BaseHttpConnector:
    async def fetch_json(self, request: ConnectorRequest) -> ConnectorResult[dict]:
        # 1. apply rate limit
        # 2. call with httpx
        # 3. redact secrets in logs
        # 4. save raw snapshot
        # 5. return typed result
        ...
```

## Data provenance record

Every raw fetch creates a row in `source_snapshots`:

```text
snapshot_id
source_name
source_version
request_method
request_url_template
request_params_json
fetched_at
http_status
content_hash
raw_storage_path
license_note
normalization_version
error_message
```

Never store authorization headers or tokens.
