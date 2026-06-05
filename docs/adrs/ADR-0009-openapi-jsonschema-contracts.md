# ADR-0009 — Use OpenAPI and JSON Schema as Contracts

## Status

Accepted.

## Context

The implementation agent needs clear contracts to avoid hallucinating shapes. The web and API need shared types.

## Decision

Use OpenAPI 3.1 for HTTP API and JSON Schema 2020-12 for important domain payloads. Generate client/server types where useful.

## Consequences

Positive:

- fewer mismatches;
- better docs;
- testable contracts;
- easier contributor onboarding.

Negative:

- schemas need maintenance;
- generation tooling adds complexity.

Mitigation:

- schemas live in repository;
- CI validates OpenAPI and JSON schemas;
- update schemas as part of feature PRs.
