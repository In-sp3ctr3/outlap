# 19 — References and Source Notes

This package was prepared with information available on June 5, 2026. Verify source availability during implementation.

## Fantasy game/rules references

- Formula 1 official fantasy 2026 article: documents current high-level game structure including five drivers, two constructors, $100m cost cap, three teams, two free transfers, net-transfer counting changes, Sprint DNF change, and chip examples.
- Fantasy Formula 1 “How to play” and “Game rules” pages: document transfer allowance and extra-transfer penalties.

## Formula 1 IP/legal references

- Formula 1 brand/IP guidelines: use for unofficial disclaimer, no logo usage, careful word-mark use, data/media restrictions, and AI-related restrictions.

## Fantasy API references

- dltHub F1 Fantasy REST API context: documents base URL, token approach, and example endpoints.
- Community F1 Fantasy API repositories/Postman collections: useful for connector discovery, but treat as unofficial and brittle.

## Race data references

- OpenF1 API documentation and homepage: endpoints for meetings, sessions, drivers, laps, pit, race control, weather, etc.; free historical data and rate limits; unofficial/non-commercial posture.
- Jolpica API: Ergast-compatible endpoint for F1 schedules/results/standings.
- FastF1 documentation/PyPI: Python package for schedules, results, timing, telemetry, caching, and Jolpica integration.

## AI provider references

- OpenAI platform docs: Responses API, models, tools.
- Anthropic docs: Messages API, tools, SDKs.
- Google GenAI docs: official Python SDK.
- Ollama docs: local API and OpenAI-compatible endpoints.
- OpenRouter docs: OpenAI-compatible chat API.
- Groq docs: OpenAI-compatible API.
- xAI docs: OpenAI/Anthropic SDK-compatible API.
- Mistral docs: official SDK and API docs.

## Dependency/security references

- PyPI/npm package pages for version pins.
- LiteLLM security update and public security reporting for AI-package supply-chain risk.
- Mistral security advisory for compromised SDK release context.

## Implementation note

Do not copy facts from these sources into runtime claims without storing source provenance. External rules and APIs can change.
