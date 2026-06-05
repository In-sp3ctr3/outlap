# Security Policy

## Supported versions

v1.x receives security fixes after public release.

## Reporting vulnerabilities

Before public release, report privately to the project maintainer. After public release, use GitHub private vulnerability reporting if enabled.

Please include:

- affected version/commit;
- reproduction steps;
- impact;
- whether secrets may be exposed;
- suggested mitigation if known.

## Secret leakage response

If a secret is committed or logged:

1. revoke/rotate the secret immediately;
2. remove it from runtime config;
3. purge from logs if possible;
4. inspect git history;
5. publish advisory if public users may be affected.

## Security expectations

- Provider keys stay server-side and are never sent to the browser.
- Logs, tests, fixtures, prompts, snapshots, and crash reports must not include secrets.
- The AI layer is read-only and cannot submit or mutate fantasy account state.
- Live connector failures must degrade safely to cached/manual/demo data and surface data-health status.

## Dependency compromise response

1. identify affected versions;
2. block install via lockfile/update;
3. rotate secrets if installed in trusted environments;
4. publish mitigation steps;
5. add regression check.
