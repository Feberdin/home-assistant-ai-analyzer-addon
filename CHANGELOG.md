# Changelog

# Changelog

## 0.3.3 - 2026-04-03

- Added automatic German/English dashboard localization based on the browser language used inside Home Assistant ingress
- Reworked the dashboard to explain findings, reports, and settings in more detail instead of showing mostly raw counters
- Fixed the assistant and status API URLs to use ingress-safe relative paths so browser fetch requests do not point to unreachable internal hosts
- Added German add-on option translations for the Home Assistant configuration screen

## 0.3.2 - 2026-04-03

- Fixed ingress routing by replacing hard-coded root URLs in the dashboard with request-aware route generation
- Added an in-dashboard assistant endpoint and chat panel for discussing findings, settings, and YAML ideas
- Reworked the geolocation view into a real OpenStreetMap tile-based map with route overlays and person legends
- Improved geolocation stay durations so single history points now extend until the next state change when possible

## 0.3.1 - 2026-04-03

- Fixed the dashboard `Internal Server Error` caused by the wrong `TemplateResponse` argument order with the installed FastAPI/Starlette version

## 0.3.0 - 2026-04-03

- Added opt-in geolocation analysis for Home Assistant `person.*` entities and GPS-capable trackers
- Added `geolocation_history.json` with timeline, stays, visited places, and local map projection data
- Added a dashboard geolocation map view with per-person timeline cards and OpenStreetMap deep links
- Added a separate `enable_ai_geolocation_context` option so location summaries are only shared with AI when explicitly enabled

## 0.2.1 - 2026-04-03

- Fixed Home Assistant app image builds by installing Python dependencies inside a dedicated virtual environment
- Removed deprecated app architecture values and kept supported `aarch64` and `amd64`
- Added a `.dockerignore` to reduce noisy local build context

## 0.2.0 - 2026-04-03

- Added a real Home Assistant app/add-on repository manifest with [repository.yaml](./repository.yaml)
- Added an installable add-on under [home-assistant-ai-analyzer](./home-assistant-ai-analyzer/README.md)
- Implemented a Python analysis engine for static config parsing, runtime inspection, graph building, and report writing
- Added an ingress dashboard with manual scan triggering and report access
- Added unit tests and local verification via virtualenv

## 0.1.0 - 2026-04-03

- Created initial architecture concept for the `Home Assistant AI Analyzer`
- Documented system overview, modules, data flow, AI integration, and future extensions
- Added repository guidance, roadmap, contribution notes, and security expectations
