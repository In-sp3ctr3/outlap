# Contributing to Outlap

Thanks for contributing. This project is an unofficial fan-made fantasy motorsport analytics tool. Do not add official Formula 1 logos, team logos, driver photos, broadcast graphics, proprietary media, secrets, or real user data.

## Development flow

1. Read `AGENTS.md`, `README.md`, and the relevant docs in `docs/`.
2. Create a focused branch such as `feat/optimizer-mode`, `fix/data-health`, or `docs/setup`.
3. Add tests before or with the implementation.
4. Keep commits small and reviewable.
5. Run the smallest relevant check while working, then `make check` before pushing.
6. Open a PR with a clear description and screenshots for UI changes.

## Commit style

Use concise Conventional Commit messages:

```text
docs: add repository architecture guide
test: cover transfer penalty chips
feat: add optimizer recommendation endpoint
fix: preserve deterministic recommendation ordering
```

Do not add generated-code disclaimers, tool branding, prompt transcripts, co-author trailers, or vague commit messages.

## Contribution requirements

- Domain logic must have unit tests.
- API changes must update `api/openapi.yaml`.
- Payload shape changes must update `schemas/*.json`.
- Data connector changes must include fixture/mocked tests and source notes.
- AI provider changes must include fake-provider tests and no-secret logging tests.
- UI changes must include loading, empty, and error states.
- Source files should usually stay under 250 lines. Files over 350 lines need a clear reason; files over 500 lines should be split before commit unless generated or documented as an exception.
- Keep domain logic free of framework imports.
- Keep UI components split by product surface or responsibility.
- Update `CHANGELOG.md` for user-visible behavior, repository standards, or release-process changes.

## Legal/content rules

Do not commit:

- official Formula 1 logos or protected assets;
- copyrighted article bodies;
- real user fantasy account data;
- API keys or tokens;
- screenshots from official apps unless legally cleared.

Use synthetic fixtures.
