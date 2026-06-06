# 01 — Product Requirements Document

## 1. Product name

Working/public name: **Outlap**.

Repository slug: `outlap`.

Product description: an unofficial, open-source fantasy motorsport strategy assistant for fans who want a data-driven, AI-explained way to manage race-week fantasy lineups.

## 2. Problem

Fantasy motorsport players must make weekly decisions under uncertainty:

- which drivers and constructors to select;
- whether to use free transfers or take transfer penalties;
- whether to deploy one-time chips;
- whether to chase expected points, price growth, safety, or league differentials;
- how to react to practice, qualifying, penalties, weather, DNFs, and news;
- how to interpret price movements and changing asset value.

Existing fantasy interfaces show team state and scoring, but they do not provide a transparent strategy engine that combines rules, projections, optimization, data health, and explainable AI.

## 3. Target users

### Persona 1 — Competitive private-league player

- Wants to beat friends or coworkers.
- Cares about differential picks and risk-reward decisions.
- Needs recommendations that explain upside/downside.

### Persona 2 — Data-driven fan

- Watches sessions and consumes stats.
- Wants a single place to combine fantasy, performance, weather, and news signals.
- Cares about provenance and explainability.

### Persona 3 — Casual player who wants help

- Does not want to build spreadsheets.
- Wants one or two clear recommended actions each race week.
- Needs plain-language explanations.

### Persona 4 — Open-source contributor

- Wants to add projection models, connectors, visualizations, or providers.
- Needs clean architecture and good tests.

## 4. Goals

- Provide race-week recommendations that are mathematically legal and explainable.
- Support all major AI providers through bring-your-own-key configuration.
- Make all recommendations reproducible from saved data snapshots.
- Allow community extension without sacrificing correctness.
- Avoid legal and branding risk by remaining unofficial, data-source-aware, and conservative with third-party IP.

## 5. Product requirements

### PRD-001: Setup wizard

The app must guide users through:

- choosing local-only or optional hosted configuration;
- selecting AI provider;
- configuring provider key/base URL/model;
- importing or connecting fantasy team state;
- validating data-source health;
- creating first baseline projection and recommendation run.

Acceptance criteria:

- setup can be completed without any paid service if using local Ollama and manual import;
- missing AI provider does not block deterministic optimizer use;
- broken fantasy connector shows structured import/team-selection fallback and CSV/TSV as a recovery path;
- secrets are not logged.

### PRD-002: Dashboard

Dashboard must show:

- next race/weekend;
- countdown/deadline field when available;
- user teams;
- cost cap and remaining budget;
- free transfers and transfer penalties;
- chip availability;
- current projected score;
- current strategy recommendation;
- data-health cards.

Acceptance criteria:

- every displayed recommendation links to its source snapshot and run ID;
- every data card has loading, empty, stale, and error states.

### PRD-003: Fantasy market

Market table must show drivers and constructors with:

- name, type, team/constructor;
- current price;
- recent fantasy score fields;
- price movement fields when available;
- ownership/selection fields when available;
- projected points;
- points per million;
- risk score;
- recommendation tags.

Acceptance criteria:

- table supports sorting, filtering, pinning, and comparison;
- user can compare any two drivers or constructors;
- missing upstream fields show `unknown`, not fake values.

### PRD-004: Transfer optimizer

Optimizer must return ranked recommendations under multiple strategy modes:

- safe;
- balanced;
- aggressive;
- budget-builder;
- differential;
- chip-optimized;
- custom weights.

Acceptance criteria:

- all recommendations satisfy lineup, cap, transfer, and chip constraints;
- every option includes expected gross points, transfer cost, net points, budget after move, confidence, risk, assumptions, and rationale;
- recommendations are reproducible by run ID.

### PRD-005: Chip simulator

Chip simulator must model:

- regular 2x/DRS boost;
- 3x/extra boost;
- Autopilot;
- No Negative;
- Wildcard;
- Limitless;
- Final Fix.

Acceptance criteria:

- chip rules live in rules engine, not prompt text;
- optimizer can compare no-chip vs chip scenarios;
- chip recommendations include “use now” and “save for later” rationale.

### PRD-006: Race-week intelligence

Race-week page must show:

- meetings/races;
- sessions;
- practice, qualifying, sprint, and race result summaries when available;
- weather observations and forecast fields when available;
- race-control messages and penalties when available;
- pit-stop summary when available;
- news flags and summaries.

Acceptance criteria:

- session data can come from OpenF1/FastF1/Jolpica adapters;
- data source and freshness are visible;
- stale session data does not silently feed projections without warning.

### PRD-007: AI strategy chat

Chat must answer strategy questions using read-only tools:

- get current team;
- get fantasy market snapshot;
- run optimizer;
- compare recommendations;
- summarize news;
- explain rules;
- explain assumptions.

Acceptance criteria:

- AI responses include recommendation IDs or data snapshot IDs when discussing specific decisions;
- AI must not claim certainty where data is missing;
- AI must not submit transfers;
- AI must not request passwords.

### PRD-008: League analysis

When league/rival data exists, app must show:

- league rank and gap;
- rival team overlap;
- high-owned picks;
- differential opportunities;
- catch-up scenarios;
- risk exposure relative to rivals.

Acceptance criteria:

- league analysis degrades gracefully if only partial league data is imported;
- differential optimizer mode can use league context.

### PRD-009: Data provenance and health

App must track:

- source;
- connector version;
- fetched timestamp;
- normalized table;
- snapshot hash;
- stale/error state;
- license/legal notes where relevant.

Acceptance criteria:

- user can open a data-health page and see the status of every connector;
- recommendations display stale-data warnings.

### PRD-010: Open-source contributor experience

Repository must include:

- clear setup;
- docs;
- examples;
- fixtures;
- tests;
- provider adapter guide;
- connector adapter guide;
- projection model guide;
- contribution and security policy.

Acceptance criteria:

- fresh clone runs real-data mode without live secrets and shows skeleton/empty states until data is synced or provided;
- CI can run with fixtures only.

## 6. Success metrics

Because v1 is open-source and local-first, do not add telemetry by default. Recommended opt-in metrics for maintainers:

- GitHub stars/forks;
- issue quality and contributor count;
- release downloads;
- docs completion rate from GitHub analytics if available;
- user-reported recommendation usefulness;
- test coverage and connector health.

## 7. Risks

- Fantasy API instability.
- Legal/IP restrictions around Formula 1 content.
- Users expecting exact predictions.
- AI hallucinations.
- Provider API changes.
- Supply-chain dependency compromise.

Mitigations are described in security, legal, connector, and testing documents.
