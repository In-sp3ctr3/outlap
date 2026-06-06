# 02 — Product Scope and Feature Inventory

## Scope rule

All features listed in this document are in v1 unless explicitly marked as excluded. The implementation plan sequences delivery, but does not defer these features out of v1.

## Feature map

### A. Setup and configuration

| Feature | v1 status | Notes |
|---|---:|---|
| Docker Compose local run | Required | `web` + `api` + local DuckDB volume |
| Setup wizard | Required | Provider, team import, data health |
| BYO AI key | Required | No built-in paid account |
| Local Ollama option | Required | Works without paid AI provider |
| Demo mode | Required | Uses fixtures only, no secrets |
| Data-source health page | Required | Shows source status and stale data |
| Export/import app settings | Required | Secrets excluded |

### B. Fantasy data

| Feature | v1 status | Notes |
|---|---:|---|
| Manual team import | Required | JSON and CSV |
| Manual market import | Required | JSON and CSV fallback |
| Optional authenticated fantasy connector | Required | Read-only; user-provided token/session only |
| Asset prices | Required | Snapshot and trend history |
| Asset scores | Required | Snapshot and trend history |
| User teams | Required | Up to three fantasy teams |
| Transfer allowance | Required | Rules engine configurable |
| Chip state | Required | User-managed or connector-derived |
| League data | Required | If imported/available |
| Auto-transfer execution | Excluded | Legal/ToS risk; not in v1 |

### C. Race and session data

| Feature | v1 status | Notes |
|---|---:|---|
| Race calendar | Required | Jolpica/FastF1/OpenF1 sources |
| Session results | Required | FP/Quali/Sprint/Race where available |
| Weather observations | Required | OpenF1 weather; future forecast optional through configurable provider |
| Race-control messages | Required | OpenF1 when available |
| Pit stop summary | Required | OpenF1/FastF1 |
| Telemetry-derived features | Required | Basic pace and position features; avoid heavy UI telemetry replay in v1 |
| Live streaming UI | Optional within v1 | Polling is enough; websockets not required |

### D. Market and analytics

| Feature | v1 status | Notes |
|---|---:|---|
| Asset market table | Required | Price, form, value, risk, projections |
| Compare assets | Required | Side-by-side comparison |
| Price movement model | Required | Transparent heuristic from available data |
| Points-per-million | Required | Asset value metric |
| Risk score | Required | DNF/reliability/news/weather flags |
| Ownership/differential score | Required | Use imported/available data |
| Data freshness badges | Required | Per table/card |

### E. Projection engine

| Feature | v1 status | Notes |
|---|---:|---|
| Baseline projection model | Required | Transparent weighted model |
| Configurable model weights | Required | User-editable advanced settings |
| Confidence intervals | Required | P10/P50/P90 or low/median/high |
| Feature importance/explanation | Required | Simple contribution breakdown |
| Model backtesting | Required | Historical/fixture backtest page |
| ML model plugin interface | Required | Default remains deterministic/transparent |

### F. Optimizer

| Feature | v1 status | Notes |
|---|---:|---|
| Legal lineup optimizer | Required | 5 drivers + 2 constructors, configurable rules |
| Transfer penalty modeling | Required | Net transfer counting |
| Budget cap constraints | Required | With Limitless exception |
| Chip simulation | Required | All known chips listed in rules doc |
| Strategy modes | Required | Safe, balanced, aggressive, budget, differential, chip |
| Ranked recommendation cards | Required | Not one opaque answer |
| What-if optimizer | Required | User can lock/ban assets |
| Explainable scoring | Required | Gross, penalties, risk, confidence |

### G. AI assistant

| Feature | v1 status | Notes |
|---|---:|---|
| Provider registry | Required | OpenAI, Anthropic, Gemini, Ollama, OpenRouter, Groq, xAI, Mistral, custom OpenAI-compatible |
| Strategy chat | Required | Tool-using, read-only |
| Recommendation explanation | Required | Based on optimizer output |
| News summarization | Required | Store metadata and short summaries |
| Compare plans | Required | User can ask “safe vs aggressive?” |
| Prompt/eval fixtures | Required | Prevent regressions |
| Streaming responses | Required | For providers that support it; fallback non-streaming |

### H. UI/UX

| Feature | v1 status | Notes |
|---|---:|---|
| Polished dashboard | Required | Desktop-first, responsive tablet/mobile |
| Dark mode | Required | Motorsport-inspired but not official branding |
| Race-week timeline | Required | Sessions and lock deadlines |
| Recommendation cards | Required | Explainable, compareable |
| Data-health page | Required | Connector status |
| Settings/provider page | Required | BYO AI and data config |
| Accessibility | Required | Keyboard nav, contrast, semantic UI |
| Empty/error/loading states | Required | All major views |

### I. Operations and open-source

| Feature | v1 status | Notes |
|---|---:|---|
| CI | Required | Lint, typecheck, unit, API, UI, E2E |
| Test fixtures | Required | No live API needed in CI |
| Release process | Required | Versioned docs/changelog |
| Contributor guide | Required | Plugin patterns |
| Security policy | Required | Vulnerability reporting |
| License | Required | MIT selected |
