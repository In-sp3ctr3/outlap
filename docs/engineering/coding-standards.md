# Coding Standards

## Principles

- Keep the deterministic core simple, explicit, and well tested.
- Prefer the fewest necessary concepts over speculative extension points.
- Remove meaningful duplication, but do not hide simple local behavior behind vague helpers.
- Use typed boundaries: Pydantic for API/backend contracts, TypeScript types and Zod where runtime validation is needed in the web app.
- Preserve local-first privacy defaults.

## Python

- Domain code belongs in `raceweek.core` and should be pure where practical.
- Framework, storage, provider, and connector code belongs at the edges.
- Use explicit Pydantic models instead of untyped dictionaries for public contracts.
- Test rules, transfers, chips, projections, and optimizer behavior before or alongside implementation.
- Keep route handlers thin.

## TypeScript And React

- Prefer focused components with clear props.
- Do not put a complete app surface into one long component file.
- Keep browser API calls in `lib/api.ts`.
- Use semantic HTML, labels, focus-visible states, and text alternatives.
- Do not use official logos, team marks, driver images, broadcast assets, or proprietary typefaces.

## File Size Review

- Source file target: under 250 lines.
- Review threshold: 350 lines.
- Split threshold: 500 lines, except generated/spec/schema files.
- Long files should split around product surfaces, domain concepts, or runtime boundaries.

## Dependency Policy

- Add dependencies only when they materially improve the requested outcome.
- Pin production dependencies.
- Update lockfiles with dependency changes.
- Prefer first-party or small auditable libraries for provider and connector edges.

## Secrets And Logs

- Never commit real provider keys, session tokens, cookies, or private league/team data.
- Do not log request headers or raw provider credentials.
- Test fixtures must use synthetic data.
