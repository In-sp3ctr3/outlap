# ADR-0001 — Use Next.js + FastAPI Monorepo

## Status

Accepted.

## Context

The product needs a polished dashboard UI and a Python-heavy analytics backend for connectors, projections, optimization, and AI provider SDKs.

## Decision

Use a pnpm monorepo with:

- `apps/web`: Next.js, React, TypeScript;
- `apps/api`: FastAPI, Python;
- `packages/contracts`: shared OpenAPI/JSON schemas;
- `packages/fixtures`: demo/test data.

## Consequences

Positive:

- best tool for each layer;
- easier data science integration;
- clean API boundary;
- good contributor ergonomics.

Negative:

- two runtimes;
- more setup complexity;
- must keep contracts synchronized.

Mitigation:

- Docker Compose;
- Makefile;
- generated API types;
- OpenAPI as source of truth.
