# ADR-0004 — Deterministic Optimizer Is Source of Truth

## Status

Accepted.

## Context

LLMs can explain and synthesize, but they are not reliable calculators for fantasy rules, budgets, transfer penalties, and lineup constraints.

## Decision

Use deterministic rules, projection, and optimization services as the source of truth. The LLM can call tools and explain outputs but cannot create unsourced transfer recommendations.

## Consequences

Positive:

- reproducible recommendations;
- testable logic;
- fewer hallucinations;
- user trust.

Negative:

- more up-front engineering;
- model output may feel less magical.

Mitigation:

- polished AI explanations;
- recommendation cards with rationale;
- strategy modes and what-if tools.
