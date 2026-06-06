# 11 — Security, Privacy, and Legal Guardrails

## Product posture

Outlap is an unofficial fan-made analytics tool. It must not imply official status or use protected branding as product identity.

## Legal constraints to design around

### Branding

Do not use:

- official Formula 1 logos;
- official F1 word marks as product branding;
- official typefaces;
- official team logos;
- official driver images;
- broadcast graphics;
- official app screenshots as marketing assets.

Allowed posture:

- plain-text editorial references where necessary to explain compatibility;
- prominent unofficial disclaimer;
- independent project name and visual identity.

### Data and content

Do not:

- scrape or redistribute substantial official timing/results/statistics content where not licensed;
- store full copyrighted articles by default;
- bypass paywalls;
- use Formula 1-owned content to train, develop, or operate AI models unless licensed;
- bundle proprietary data in test fixtures.

Do:

- rely on documented/open/community APIs where permitted;
- store provenance and license notes;
- support manual user import;
- store short metadata and summaries for news, not article mirrors;
- use synthetic/demo fixtures in repository.

### Fantasy account actions

v1 must be read-only with respect to the official fantasy account. The app can recommend moves, but the user executes them manually.

Disallowed:

- automated login with username/password;
- auto-submitting transfers;
- bypassing anti-bot protections;
- scraping user account data without explicit user action.

## Privacy

Default privacy stance:

- local-first;
- no telemetry by default;
- no hosted account required;
- no secrets in browser;
- no secrets in logs;
- no AI prompts containing unnecessary personal data.

## Secrets management

Supported local secret sources:

1. `.env` file excluded by `.gitignore`;
2. environment variables;
3. local encrypted secret store later, if implemented;
4. Docker secrets for advanced deployment.

Never store:

- provider API keys in database plaintext;
- fantasy bearer tokens in raw snapshots;
- authorization headers;
- cookies;
- passwords.

Redaction patterns:

- `sk-...` style API keys;
- bearer tokens;
- session cookies;
- OAuth tokens;
- provider-specific key prefixes;
- long high-entropy strings in logs.

## AI prompt privacy

Only send the minimum relevant data to AI providers.

Allowed in prompts:

- selected team assets;
- budget;
- transfer count;
- recommendation options;
- risk summaries;
- data freshness status.

Avoid unless explicitly needed:

- user email;
- user global ID;
- league member names;
- raw tokens;
- full news article text;
- raw external API payloads.

## Supply-chain security

- Pin direct dependencies.
- Commit lockfiles.
- Run dependency audit in CI.
- Use secret scanning.
- Pin GitHub Actions by SHA.
- Avoid unnecessary transitive-heavy AI abstraction libraries.
- Review AI/agent dependencies with extra scrutiny.
- Never install known-compromised versions.

## Threat model

### Threat: Provider API key leakage

Mitigations:

- server-side provider calls only;
- env var references instead of stored key values;
- log redaction;
- prompt redaction;
- no frontend exposure.

### Threat: Fantasy token leakage

Mitigations:

- local-only storage;
- never store in raw snapshot;
- no token in query strings;
- optional manual import;
- user can clear token.

### Threat: Malicious dependency

Mitigations:

- lockfiles;
- package provenance review;
- dependency audit;
- minimal dependencies;
- CI install from lockfile only;
- renovate/dependabot with human review.

### Threat: AI hallucinated recommendation

Mitigations:

- deterministic recommendation IDs;
- AI must reference optimizer outputs;
- post-response validation;
- tests/evals;
- show data freshness.

### Threat: Upstream API breaking change

Mitigations:

- connector contract tests;
- source health UI;
- manual import fallback;
- endpoint map configuration;
- graceful degradation.

## Security headers for hosted mode

If hosted behind reverse proxy:

- HTTPS only;
- HSTS;
- CSP;
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- CSRF protection if cookies are used;
- authenticated access.

## Data deletion

Settings must include:

- clear provider config;
- clear fantasy token/session;
- delete local database;
- export user data;
- delete conversations;
- clear raw snapshots.

## Disclaimer text

Use this in README, UI footer, and About page:

```text
Outlap is an unofficial fan-made fantasy analytics tool. It is not affiliated with, endorsed by, or sponsored by Formula 1, Formula One Management, or any team/constructor. Users are responsible for complying with the terms of the services they connect.
```

## Maintainer checklist before public release

- No official logos/assets in repository.
- No real user data in fixtures.
- No secrets in git history.
- No unlicensed full article content.
- README contains disclaimer.
- Connector docs explain optional/user-responsibility nature.
- Terms/legal docs reviewed by maintainer.
- Security policy exists.
