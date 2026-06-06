# Security Requirements

- Browser must never receive provider API keys or session tokens.
- AI responses must be read-only explanations and must not mutate fantasy account state.
- Manual imports and fixtures must be synthetic or user-provided local data only.
- Live connector failures must surface data-health status instead of crashing the app.
- External source provenance must include snapshot IDs in recommendation output where data contributes to a recommendation.
- `.env` files, DuckDB files, caches, build output, and test artifacts must stay out of Git.
- Public docs and UI must avoid official branding, logos, driver images, team marks, and copyrighted media.
- CI must include lint, typecheck, tests, E2E, dependency updates, and secret scanning.
