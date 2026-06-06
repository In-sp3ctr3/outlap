# 16 — Contributing and Open-Source Governance

## License

Selected v1 license: MIT.

Reasoning:

- permissive and familiar;
- friendly to contributors and downstream users;
- avoids friction for a new community project.

Do not change license casually after accepting contributions.

## Contribution areas

- data connectors;
- projection models;
- optimizer strategies;
- UI components;
- AI provider adapters;
- docs;
- tests/fixtures;
- accessibility;
- localization.

## Pull request rules

Every PR must:

- describe the change;
- include tests;
- update docs if behavior changes;
- avoid official/proprietary assets;
- avoid secrets and real user data;
- pass CI.

## Connector contribution rules

New connectors must include:

- source license/terms note;
- rate-limit behavior;
- typed raw/normalized models;
- fixture tests;
- data-health status;
- fallback behavior;
- no secrets in logs.

## Projection model contribution rules

New projection models must include:

- model name/version;
- input features;
- output schema;
- backtest method;
- explainability payload;
- tests;
- configuration defaults.

## AI provider contribution rules

New providers must include:

- provider config schema;
- fake provider tests;
- error handling;
- streaming behavior if supported;
- tool-call support if available;
- no dependency bloat unless justified.

## Code of conduct

Adopt Contributor Covenant or similar. Keep community friendly and clear that the project is unofficial.

## Security reporting

Create `SECURITY.md` with:

- supported versions;
- private vulnerability report method;
- expected response timeline;
- secret leakage procedures;
- dependency compromise procedures.

## Documentation expectations

Every user-facing feature needs:

- short README mention;
- setup/config docs;
- troubleshooting notes;
- screenshot later if project assets are safe.
