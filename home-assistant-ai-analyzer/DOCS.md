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
- build a geolocation timeline for people and GPS-capable trackers
- show recent movement on an OpenStreetMap-backed local map and OpenStreetMap links
- answer dashboard chat questions about settings, findings, and YAML ideas
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
7. Use the built-in chat panel if you want to discuss findings or ask for YAML guidance

## Configuration

### Main Options

- `base_config_path`: Mounted Home Assistant configuration path. Default: `/homeassistant`
- `output_path`: Report output directory. Default: `/data/analysis`
- `scan_mode`: `quick`, `full`, or `deep`
- `lookback_days`: Runtime lookback window for future and current history-based analysis
- `run_on_startup`: Run one scan automatically after the add-on starts
- `enable_runtime_analysis`: Use Home Assistant API runtime data
- `enable_geolocation_analysis`: Build a per-person location timeline and map from Home Assistant runtime history
- `enable_recorder_db`: Allow optional recorder database inspection
- `recorder_db_path`: Default SQLite recorder path
- `enable_ai`: Enable optional LLM proposal generation
- `enable_ai_geolocation_context`: Allow summarized people location timelines to be included in AI prompts
- `llm_base_url`: OpenAI-compatible chat completion endpoint
- `llm_model`: LLM model name
- `llm_api_key`: API key for the chosen LLM service
- `max_history_entities`: Reserved limit for bounded runtime history analysis
- `geolocation_entity_limit`: Maximum number of tracked people or GPS trackers in one scan
- `geolocation_point_limit`: Maximum number of map points rendered per person
- `exclude_paths`: Paths below the config directory that should not be scanned

## Generated Reports

The add-on writes these files to `/data/analysis`:

- `automation_issues.json`
- `unused_entities.json`
- `template_performance.json`
- `integration_usage.json`
- `geolocation_history.json`
- `automation_graph.json`
- `suggestions.md`
- `run_summary.json`

## How To Use

1. Open the add-on dashboard
2. Review the current status and latest scan summary
3. Click `Run Scan`
4. Open the generated reports from the dashboard
5. Review `suggestions.md` first for the operator-friendly summary
6. Use the Assistant card if you want to ask follow-up questions or request YAML ideas
7. Review the location map and per-person timeline cards if geolocation analysis is enabled

## Troubleshooting

### The add-on starts but shows no results

- Run a scan from the dashboard
- Check the add-on logs
- Verify that `/homeassistant` is mounted and readable

### Runtime analysis is unavailable

- Confirm the add-on has `homeassistant_api: true`
- Check whether the supervisor proxy is reachable from the container
- Review the `runtime` warnings in `run_summary.json`

### Geolocation map is empty

- Confirm `enable_geolocation_analysis` is enabled
- Ensure Home Assistant has `person.*` entities or GPS-capable `device_tracker.*` entities with latitude and longitude
- Increase `lookback_days` if you expect older movement history
- Review `geolocation_history.json` for warnings and entity counts

### The map shows routes but no tiles

- The browser loads OpenStreetMap tiles directly, so local network filters or privacy blockers may suppress the background map
- The route overlay should still remain visible; use the OpenStreetMap link in the people card to confirm the latest coordinates
- Check the browser console if you suspect blocked tile requests

### The dashboard chat does not answer

- Refresh the dashboard after updating the add-on so the new ingress-safe API URLs are loaded
- If AI is disabled, the chat still answers locally from the latest reports
- If AI is enabled, verify `llm_base_url`, `llm_model`, `llm_api_key`, and outbound network access

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
- `/data/analysis/geolocation_history.json`
- add-on logs in Home Assistant

## Security Notes

- The add-on does not write into the Home Assistant config directory
- Secrets are masked before AI requests
- Geolocation stays local unless `enable_ai_geolocation_context` is explicitly enabled
- AI-generated content is treated as a draft proposal
- Runtime requests are bounded and fail safely
