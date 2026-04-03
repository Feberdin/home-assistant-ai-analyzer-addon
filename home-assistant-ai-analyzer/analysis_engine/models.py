"""
Purpose:
Define the typed data structures shared by the parser, analyzers, report writer, and web UI.

Input/Output:
Inputs are add-on options, parsed Home Assistant configuration data, runtime snapshots, and generated findings.
Outputs are Python dataclass instances that are easy to validate, serialize, and test.

Important invariants:
These models must stay JSON-serializable, avoid hidden side effects, and remain stable enough for report generation.

How to debug:
If a report or UI view looks wrong, inspect the dataclass values first before debugging the surrounding logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass(slots=True)
class AppSettings:
    """Runtime configuration loaded from the add-on options file."""

    base_config_path: str = "/homeassistant"
    output_path: str = "/data/analysis"
    log_level: str = "info"
    scan_mode: str = "full"
    lookback_days: int = 7
    run_on_startup: bool = True
    enable_runtime_analysis: bool = True
    enable_geolocation_analysis: bool = True
    enable_recorder_db: bool = False
    recorder_db_path: str = "/homeassistant/home-assistant_v2.db"
    enable_ai: bool = False
    enable_ai_geolocation_context: bool = False
    llm_base_url: str = "https://api.openai.com/v1/chat/completions"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str = ""
    llm_max_findings: int = 5
    max_history_entities: int = 20
    geolocation_entity_limit: int = 10
    geolocation_point_limit: int = 300
    exclude_paths: list[str] = field(default_factory=lambda: [".storage", "deps", "__pycache__"])
    ha_api_url: str = "http://supervisor/core/api"

    @classmethod
    def from_options_file(cls, options_path: str = "/data/options.json") -> "AppSettings":
        """Load add-on options, falling back to safe defaults for local development."""

        options_file = Path(options_path)
        if not options_file.exists():
            return cls()

        with options_file.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        return cls(
            base_config_path=str(raw.get("base_config_path", "/homeassistant")),
            output_path=str(raw.get("output_path", "/data/analysis")),
            log_level=str(raw.get("log_level", "info")).lower(),
            scan_mode=str(raw.get("scan_mode", "full")).lower(),
            lookback_days=int(raw.get("lookback_days", 7)),
            run_on_startup=bool(raw.get("run_on_startup", True)),
            enable_runtime_analysis=bool(raw.get("enable_runtime_analysis", True)),
            enable_geolocation_analysis=bool(raw.get("enable_geolocation_analysis", True)),
            enable_recorder_db=bool(raw.get("enable_recorder_db", False)),
            recorder_db_path=str(raw.get("recorder_db_path", "/homeassistant/home-assistant_v2.db")),
            enable_ai=bool(raw.get("enable_ai", False)),
            enable_ai_geolocation_context=bool(raw.get("enable_ai_geolocation_context", False)),
            llm_base_url=str(raw.get("llm_base_url", "https://api.openai.com/v1/chat/completions")),
            llm_model=str(raw.get("llm_model", "gpt-4.1-mini")),
            llm_api_key=str(raw.get("llm_api_key", "")),
            llm_max_findings=int(raw.get("llm_max_findings", 5)),
            max_history_entities=int(raw.get("max_history_entities", 20)),
            geolocation_entity_limit=int(raw.get("geolocation_entity_limit", 10)),
            geolocation_point_limit=int(raw.get("geolocation_point_limit", 300)),
            exclude_paths=[str(item) for item in raw.get("exclude_paths", [".storage", "deps", "__pycache__"])],
        )

    def runtime_mode_enabled(self) -> bool:
        """Return true when runtime API analysis should run in the current mode."""

        return self.enable_runtime_analysis and self.scan_mode in {"full", "deep"}

    def deep_mode_enabled(self) -> bool:
        """Return true when advanced analysis paths should be available."""

        return self.scan_mode == "deep"

    def safe_dict(self) -> dict:
        """Return a log-friendly settings snapshot with secrets masked."""

        data = asdict(self)
        if data["llm_api_key"]:
            data["llm_api_key"] = "***redacted***"
        return data


@dataclass(slots=True)
class AutomationRecord:
    """Normalized view of one automation-like object found in YAML."""

    automation_id: str
    alias: str
    source_file: str
    trigger_entities: list[str] = field(default_factory=list)
    condition_entities: list[str] = field(default_factory=list)
    action_entities: list[str] = field(default_factory=list)
    service_calls: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    mode: str = ""
    raw_excerpt: str = ""


@dataclass(slots=True)
class TemplateRecord:
    """Normalized template snippet used for performance scoring."""

    source_file: str
    context: str
    template: str
    entity_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConfigParseResult:
    """Aggregated parser output used by all later analyzers."""

    base_config_path: str
    yaml_files_scanned: int = 0
    parse_errors: list[dict] = field(default_factory=list)
    file_summaries: list[dict] = field(default_factory=list)
    automations: list[AutomationRecord] = field(default_factory=list)
    templates: list[TemplateRecord] = field(default_factory=list)
    configured_integrations: list[str] = field(default_factory=list)
    referenced_entities: list[str] = field(default_factory=list)
    entity_reference_counts: dict[str, int] = field(default_factory=dict)
    service_reference_counts: dict[str, int] = field(default_factory=dict)
    scripts_count: int = 0
    blueprint_files: list[str] = field(default_factory=list)
    package_files: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        """Return a short parser summary for logs and run metadata."""

        return {
            "yaml_files_scanned": self.yaml_files_scanned,
            "parse_errors": len(self.parse_errors),
            "automations": len(self.automations),
            "templates": len(self.templates),
            "referenced_entities": len(self.referenced_entities),
            "scripts_count": self.scripts_count,
            "blueprint_files": len(self.blueprint_files),
            "package_files": len(self.package_files),
        }


@dataclass(slots=True)
class RuntimeSnapshot:
    """Best-effort runtime data collected through the Home Assistant API and recorder."""

    available: bool = False
    warnings: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    components: list[str] = field(default_factory=list)
    states: dict[str, dict] = field(default_factory=dict)
    services: list[dict] = field(default_factory=list)
    error_log_excerpt: str = ""
    logbook_entries: list[dict] = field(default_factory=list)
    geolocation_entities: list[dict] = field(default_factory=list)
    geolocation_history: dict[str, list[dict]] = field(default_factory=dict)
    recorder_details: dict = field(default_factory=dict)

    def state_ids(self) -> set[str]:
        """Return the set of runtime entity ids currently visible from Home Assistant."""

        return set(self.states.keys())


@dataclass(slots=True)
class ScanArtifacts:
    """Structured artifacts produced by one scan run before persistence."""

    run_id: str
    parser_summary: dict
    automation_issues: dict
    unused_entities: dict
    template_performance: dict
    integration_usage: dict
    geolocation_history: dict
    automation_graph: dict
    suggestions_markdown: str
    ai_proposals: dict
    run_summary: dict
