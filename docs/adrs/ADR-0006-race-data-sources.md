# ADR-0006 — Use OpenF1 + Jolpica + FastF1 for Race Data

## Status

Accepted.

## Context

The product needs session/race context, historical results, weather, race control, pit stops, and schedule data.

## Decision

Use:

- OpenF1 for modern session/weather/race-control/pit data;
- Jolpica for Ergast-compatible schedules/results/standings;
- FastF1 for Python data access, caching, and feature engineering.

## Consequences

Positive:

- complementary sources;
- open/community-friendly;
- good Python integration;
- historical and modern session coverage.

Negative:

- source licenses and limits differ;
- fields may not align perfectly;
- live data may require paid/limited access.

Mitigation:

- connector provenance;
- cache and rate limits;
- source-health UI;
- normalization tests.
