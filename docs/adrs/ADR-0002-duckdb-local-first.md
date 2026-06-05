# ADR-0002 — Use DuckDB for Local-First Analytics Store

## Status

Accepted.

## Context

The project should be open-source, easy to run locally, and analytics-heavy. Users should not need to administer Postgres to try it.

## Decision

Use DuckDB as the default database. Store it at `./data/raceweek.duckdb`.

## Consequences

Positive:

- zero-admin local setup;
- excellent analytical SQL;
- easy snapshot/export;
- simple Docker volume.

Negative:

- not ideal for multi-user hosted writes;
- migrations must be managed carefully;
- fewer auth/multi-tenant primitives than Postgres.

Mitigation:

- keep storage behind repository interfaces;
- hosted mode can later add Postgres adapter;
- use source snapshots and typed repositories.
