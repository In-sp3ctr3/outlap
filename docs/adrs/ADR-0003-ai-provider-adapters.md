# ADR-0003 — Use Self-Authored AI Provider Adapters

## Status

Accepted.

## Context

The project must support many providers: OpenAI, Anthropic, Gemini, Ollama, OpenRouter, Groq, xAI, Mistral, and custom OpenAI-compatible endpoints. All-in-one AI routing dependencies are convenient but increase supply-chain and abstraction risk.

## Decision

Implement a small provider adapter interface directly. Use official SDKs where appropriate and OpenAI-compatible clients for compatible providers.

LiteLLM is not a core runtime dependency in v1.

## Consequences

Positive:

- lower dependency risk;
- easier to audit;
- precise provider behavior;
- simpler secret handling.

Negative:

- more adapter code;
- provider differences must be handled explicitly.

Mitigation:

- keep interface small;
- fake provider for tests;
- provider-specific tests;
- optional gateway integration can be added later.
