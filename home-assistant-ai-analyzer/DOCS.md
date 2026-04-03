# Home Assistant AI Analyzer

## Purpose

`Home Assistant AI Analyzer` scans a Home Assistant installation and generates reports for configuration quality, automation structure, template cost, entity usage, and runtime observations.

The add-on is designed to be understandable and safe:

- read-only against the Home Assistant config directory
- reports are written to `/data/analysis`
- AI usage is optional
- generated improvements are suggestions, not live changes

## What It Can Do Today

- scan the full mounted Home Assistant configuration tree
- parse YAML files and detect automations, entities, templates, and integrations
- build a simple automation graph
- detect missing referenced entities
- flag likely expensive templates
- summarize runtime API availability and current state inventory
- generate structured JSON and Markdown reports
- expose a dashboard through Ingress

## Installation

1. Open `Settings > Apps > App Store`
2. Add this repository as a third-party repository:
   `https://github.com/Feberdin/home-assistant-ai-analyzer-addon`
3. Install `Home Assistant AI Analyzer`
4. Review the add-on options
5. Start the add-on
6. Open the Web UI

## Configuration

### Main Options

- `base_config_path`: Mounted Home Assistant configuration path. Default: `/homeassistant`
- `output_path`: Report output directory. Default: `/data/analysis`
- `scan_mode`: `quick`, `full`, or `deep`
- `lookback_days`: Runtime lookback window for future and current history-based analysis
- `run_on_startup`: Run one scan automatically after the add-on starts
- `enable_runtime_analysis`: Use Home Assistant API runtime data
- `enable_recorder_db`: Allow optional recorder database inspection
- `recorder_db_path`: Default SQLite recorder path
- `enable_ai`: Enable optional LLM proposal generation
- `llm_base_url`: OpenAI-compatible chat completion endpoint
- `llm_model`: LLM model name
- `llm_api_key`: API key for the chosen LLM service
- `max_history_entities`: Reserved limit for bounded runtime history analysis
- `exclude_paths`: Paths below the config directory that should not be scanned

## Generated Reports

The add-on writes these files to `/data/analysis`:

- `automation_issues.json`
- `unused_entities.json`
- `template_performance.json`
- `integration_usage.json`
- `automation_graph.json`
- `suggestions.md`
- `run_summary.json`

## How To Use

1. Open the add-on dashboard
2. Review the current status and latest scan summary
3. Click `Run Scan`
4. Open the generated reports from the dashboard
5. Review `suggestions.md` first for the operator-friendly summary

## Troubleshooting

### The add-on starts but shows no results

- Run a scan from the dashboard
- Check the add-on logs
- Verify that `/homeassistant` is mounted and readable

### Runtime analysis is unavailable

- Confirm the add-on has `homeassistant_api: true`
- Check whether the supervisor proxy is reachable from the container
- Review the `runtime` warnings in `run_summary.json`

### Recorder analysis does not run

- Confirm `enable_recorder_db` is enabled
- Verify the file exists at `recorder_db_path`
- For external databases, this version only reports that direct access is not configured

### AI proposals do not appear

- Confirm `enable_ai` is enabled
- Verify `llm_base_url`, `llm_model`, and `llm_api_key`
- Check the add-on logs for outbound API errors

## Logs And Debugging

The add-on logs include:

- startup configuration summary
- scan lifecycle with `run_id`
- parser warnings
- runtime API warnings
- report publication status

For deeper debugging, inspect:

- `/data/analysis/run_summary.json`
- `/data/analysis/suggestions.md`
- add-on logs in Home Assistant

## Security Notes

- The add-on does not write into the Home Assistant config directory
- Secrets are masked before AI requests
- AI-generated content is treated as a draft proposal
- Runtime requests are bounded and fail safely
