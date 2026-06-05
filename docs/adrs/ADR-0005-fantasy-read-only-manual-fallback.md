# ADR-0005 — Fantasy Connector Is Read-Only with Manual Import Fallback

## Status

Accepted.

## Context

Fantasy APIs and terms can change. Automated login/transfer execution creates legal, security, and account-risk concerns.

## Decision

v1 supports manual import and optional read-only token/session-based connector. It does not store passwords and does not auto-submit transfers.

## Consequences

Positive:

- safer legal posture;
- lower account risk;
- product still works when connector breaks;
- easier open-source launch.

Negative:

- less seamless than full automation;
- users may need to manually import/update.

Mitigation:

- make manual import polished;
- clear instructions;
- data-health warnings;
- optional token connector for advanced users.
