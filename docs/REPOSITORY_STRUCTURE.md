# Planned Repository Structure

## Why This Document Exists

The repository should be organized so that each concern has a clear home and can be understood by contributors who are not deep in the implementation yet.

## Target Structure

```text
home-assistant-ai-analyzer-addon/
  repository.yaml
  CONTRIBUTING.md
  LICENSE
  SECURITY.md
  CHANGELOG.md
  .gitignore
  home-assistant-ai-analyzer/
    config.yaml
    Dockerfile
    apparmor.txt
    run.sh
    README.md
    DOCS.md
    pyproject.toml
    analysis_engine/
      __main__.py
      api/
      orchestrator/
      parsers/
      collectors/
      graph/
      analyzers/
      ai/
      reports/
      storage/
      models/
      utils/
    webui/
      templates/
      static/
    tests/
      unit/
      integration/
      fixtures/
```

## Structural Intention

- root level: repository metadata and cross-project guidance
- add-on folder: everything Home Assistant needs to build and run the add-on
- `analysis_engine/`: Python implementation grouped by responsibility
- `webui/`: dashboard presentation assets
- `tests/`: local quality and regression coverage

## Output Contract

The runtime add-on should write generated files to `/data/analysis` using this shape:

```text
analysis/
  automation_issues.json
  unused_entities.json
  template_performance.json
  integration_usage.json
  geolocation_history.json
  automation_graph.json
  suggestions.md
  proposals/
```

## Current Repository State

This concept repository intentionally stops before adding runnable code. The structure above is the agreed target for the next implementation step.
