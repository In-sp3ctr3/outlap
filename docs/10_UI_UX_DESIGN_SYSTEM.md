# 10 — UI/UX and Design System

## Product feel

The app should feel like a modern strategy cockpit: sharp, data-dense, calm, and confident. It should not copy Formula 1 official visual identity.

Recommended visual direction:

- dark-first interface;
- neutral charcoal backgrounds;
- subtle grid/track-inspired geometry;
- high-contrast cards;
- clear status chips;
- one accent color chosen by project maintainers, not official F1 red;
- no official logos, team badges, driver photos, broadcast graphics, or proprietary typefaces.

## Information architecture

Primary navigation:

```text
Dashboard
Race Week
Optimizer
Market
My Teams
League
AI Strategist
Data Health
Settings
```

## Page requirements

### 1. Setup Wizard

Steps:

1. Welcome + unofficial disclaimer.
2. Choose local/demo/live mode.
3. Configure data sources.
4. Configure AI provider.
5. Import team or connect read-only token.
6. Validate data health.
7. Generate first recommendation.

Required states:

- no AI provider configured;
- local Ollama unavailable;
- fantasy connector unavailable;
- manual import invalid;
- data sync partially failed;
- success.

### 2. Dashboard

Sections:

- Next Race card.
- Team summary cards for up to three teams.
- Recommendation highlight.
- Budget/transfer/chip status.
- Data-health strip.
- News risk strip.
- Projection delta chart.

Dashboard must answer in five seconds of reading:

- What is the next event?
- Is my data fresh?
- What move is currently recommended?
- Is a chip recommended?
- What is the biggest risk?

### 3. Race Week

Sections:

- event timeline;
- sessions/results;
- weather observations;
- race-control and penalty feed;
- practice/quali/race summary;
- news and risk flags;
- “rerun projections” button.

### 4. Optimizer

Main components:

- strategy mode selector;
- team selector;
- lock/ban assets controls;
- chip scenario toggles;
- ranked recommendation cards;
- comparison drawer;
- explanation panel;
- export/copy action list.

Recommendation card fields:

- rank;
- title;
- transfer list;
- chip action;
- expected net points;
- transfer penalty;
- budget after move;
- risk/confidence;
- key rationale;
- warnings;
- assumptions;
- source snapshots.

### 5. Market

Table columns:

- asset;
- type;
- constructor/team;
- price;
- projected points;
- P10/P90;
- points per million;
- recent points;
- price trend;
- ownership;
- differential score;
- risk;
- tags.

Interactions:

- sort;
- filter;
- compare;
- add to locked/banned list;
- open asset details drawer.

### 6. My Teams

Shows:

- team snapshots;
- current lineup;
- budget;
- free transfers;
- chips;
- historical team changes;
- import/update button.

### 7. League

Shows:

- league table if available;
- user rank/gap;
- rival overlap;
- common assets;
- differential suggestions;
- catch-up strategy.

### 8. AI Strategist

Chat interface with:

- context chips for selected team/event;
- provider/model selector;
- prompt suggestions;
- cited recommendation IDs;
- tool-call transparency panel;
- stale-data warnings.

Suggested prompts:

- “What is my safest move this week?”
- “Should I use a chip?”
- “I am 80 points behind. What aggressive move makes sense?”
- “Compare the top two recommendations.”
- “What news changes the projections?”

### 9. Data Health

Table:

- source;
- status;
- last sync;
- freshness;
- last error;
- connector version;
- license/legal note;
- actions.

Actions:

- sync now;
- disable source;
- open docs;
- clear cache;
- inspect snapshots.

### 10. Settings

Sections:

- AI providers;
- data sources;
- ruleset;
- projection weights;
- privacy;
- import/export;
- about/legal.

## Component system

Required reusable components:

- `StatusBadge`
- `DataFreshnessBadge`
- `RiskMeter`
- `ConfidenceMeter`
- `MetricCard`
- `RecommendationCard`
- `TransferPill`
- `ChipBadge`
- `AssetAvatarPlaceholder`
- `AssetComparisonDrawer`
- `SourceSnapshotLink`
- `ProviderConfigForm`
- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`

## Responsive behavior

- Desktop: side nav and two/three-column dashboard.
- Tablet: collapsible nav, two-column cards.
- Mobile: bottom nav or top menu, single-column cards, tables become cards/drawers.

## Accessibility

Minimum requirements:

- semantic headings;
- keyboard navigation for all controls;
- visible focus states;
- color is never the only status indicator;
- labels for all inputs;
- chart data available in tables or summaries;
- contrast meets WCAG AA.

## Empty/error states

Every page must have useful states:

- no team imported;
- no upcoming race found;
- no AI provider configured;
- connector disabled;
- stale data;
- optimizer cannot find legal lineup;
- projections missing;
- provider request failed.

Example empty state:

```text
No fantasy team imported yet.
Import your team manually or configure a read-only fantasy connector. You can still explore demo mode.
```

## Copywriting style

Use direct, helpful language:

- “Recommended move” instead of “AI insight”.
- “Data is stale” instead of “Something went wrong”.
- “Manual action required” instead of “Transfer submitted”.
- “Confidence” and “Risk” should always be accompanied by explanation.

## Legal UI text

Footer/about page must include:

```text
Outlap is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1, Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
```
