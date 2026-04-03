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

This repository now contains:

- the complete architecture concept
- a minimal but installable Home Assistant app/add-on
- a Python analysis engine with a small ingress dashboard
- tests for the core analysis logic

## Features Planned

- Analyze the full Home Assistant config directory
- Parse automations, scripts, blueprints, packages, and templates
- Build an automation dependency graph
- Detect unused, missing, and noisy entities
- Detect expensive templates and trigger-pattern issues
- Inspect runtime data through the Home Assistant API
- Track people geolocation history and render local movement maps
- Optionally inspect recorder database data
- Generate structured findings and human-readable suggestions
- Optionally ask an LLM to propose improved automations

## Documentation

- Main architecture concept: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- Implementation roadmap: [docs/IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md)
- Planned repository structure: [docs/REPOSITORY_STRUCTURE.md](./docs/REPOSITORY_STRUCTURE.md)
- Security expectations: [SECURITY.md](./SECURITY.md)
- Install and usage guide: [home-assistant-ai-analyzer/DOCS.md](./home-assistant-ai-analyzer/DOCS.md)

## Quickstart

To install this through Home Assistant Apps/Add-ons:

1. Open Home Assistant `Settings > Apps > App Store`
2. Add the repository URL `https://github.com/Feberdin/home-assistant-ai-analyzer-addon`
3. Install `Home Assistant AI Analyzer`
4. Open the add-on and review the options
5. Start the add-on
6. Open the web UI and run a scan

## Configuration

Supported add-on configuration topics include:

- scan mode
- runtime lookback window
- geolocation analysis and AI geolocation sharing
- recorder database access
- AI provider settings
- logging level
- exclusions and allowlists

## Troubleshooting

Common situations at this stage:

- If the add-on does not appear in the App Store: verify that Home Assistant can access [repository.yaml](./repository.yaml).
- If the add-on starts but the dashboard is empty: check whether `/homeassistant` is mounted and readable.
- If runtime analysis is unavailable: verify Supervisor API access and the Home Assistant API proxy.
- If you want the full architecture background: start with [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Logs And Debugging

The add-on is designed to expose:

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

No final license has been selected yet. This should be decided before a public release.
