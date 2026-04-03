# Home Assistant AI Analyzer

## Purpose

`Home Assistant AI Analyzer` is a concept repository for a future Home Assistant Add-on that analyzes an existing Home Assistant installation and suggests improvements for automations, entities, templates, integrations, and runtime behavior.

The target audience is not only developers. The architecture is documented so that operators, maintainers, and Home Assistant power users can understand:

- what the add-on should do
- how the system is structured
- which data sources are used
- where the risks are
- how later implementation phases should be organized

## Current Status

This repository currently contains the complete architecture concept and implementation roadmap.

It does **not** yet contain a runnable add-on or Python implementation.

## Features Planned

- Analyze the full Home Assistant config directory
- Parse automations, scripts, blueprints, packages, and templates
- Build an automation dependency graph
- Detect unused, missing, and noisy entities
- Detect expensive templates and trigger-pattern issues
- Inspect runtime data through the Home Assistant API
- Optionally inspect recorder database data
- Generate structured findings and human-readable suggestions
- Optionally ask an LLM to propose improved automations

## Documentation

- Main architecture concept: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- Implementation roadmap: [docs/IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md)
- Planned repository structure: [docs/REPOSITORY_STRUCTURE.md](./docs/REPOSITORY_STRUCTURE.md)
- Security expectations: [SECURITY.md](./SECURITY.md)

## Quickstart

Because this repository is currently an architecture concept, the quickest way to start is:

1. Read [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
2. Review [docs/IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md)
3. Use [docs/REPOSITORY_STRUCTURE.md](./docs/REPOSITORY_STRUCTURE.md) as the baseline for implementation

## Configuration

Planned add-on configuration topics are described in the architecture document and include:

- scan mode
- runtime lookback window
- recorder database access
- AI provider settings
- logging level
- exclusions and allowlists

## Troubleshooting

Common situations at this stage:

- If you expect runnable code: this repository intentionally documents the concept first.
- If you want to start implementation: use the roadmap phases in [docs/IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md).
- If you want to review security assumptions: start with [SECURITY.md](./SECURITY.md).

## Logs And Debugging

The future add-on is planned to expose:

- structured add-on logs with `run_id`
- phase-by-phase scan progress
- machine-readable analysis output in `/data/analysis`
- a small ingress dashboard for findings and diagnostics

## Security Notes

- v1 should be read-only against the Home Assistant configuration directory
- AI usage must be explicit and opt-in
- secrets, tokens, and credentials must be redacted before leaving the container
- generated automations should be proposed as drafts, not auto-applied

## License Notice

No final license has been selected yet. This should be decided before implementation starts.
