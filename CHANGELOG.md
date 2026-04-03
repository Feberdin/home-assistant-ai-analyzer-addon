# Changelog

# Changelog

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
