"""
Purpose:
Coordinate one complete scan run from parsing through reporting while keeping the pipeline easy to reason about.

Input/Output:
Input is the AppSettings loaded from Home Assistant options.
Output is a run summary dictionary used by the dashboard and persisted to disk.

Important invariants:
The orchestrator should be the only place that decides run order so modules stay loosely coupled and individually testable.

How to debug:
If the scan stops halfway, inspect the logged phase order and the partially written run_summary.json file.
"""

from __future__ import annotations

import logging
import uuid

from .ai_optimizer import maybe_generate_ai_proposals
from .automation_graph import build_automation_graph
from .automation_issues import analyze_automation_issues
from .config_parser import parse_configuration
from .entity_usage import analyze_entity_usage
from .integration_analyzer import analyze_integrations
from .models import AppSettings, ScanArtifacts
from .report_writer import write_reports
from .runtime_analyzer import collect_runtime
from .suggestion_engine import build_suggestions
from .template_analyzer import analyze_templates
from .utils import utc_now_iso


LOGGER = logging.getLogger(__name__)


def run_scan(settings: AppSettings) -> dict:
    """Execute one scan run and persist all required artifacts."""

    run_id = f"{utc_now_iso()}-{uuid.uuid4().hex[:8]}"
    LOGGER.info("Starting scan run %s", run_id)

    parse_result = parse_configuration(settings)
    LOGGER.info("Parsed configuration summary: %s", parse_result.summary())

    runtime_snapshot = collect_runtime(settings, parse_result)
    template_performance = analyze_templates(parse_result.templates)
    automation_graph = build_automation_graph(parse_result)
    unused_entities = analyze_entity_usage(parse_result, automation_graph, runtime_snapshot)
    automation_issues = analyze_automation_issues(parse_result, runtime_snapshot)
    integration_usage = analyze_integrations(parse_result, runtime_snapshot)
    ai_proposals = maybe_generate_ai_proposals(
        settings,
        automation_issues,
        unused_entities,
        template_performance,
        integration_usage,
    )

    suggestions, suggestions_markdown = build_suggestions(
        run_id=run_id,
        parser_summary=parse_result.summary(),
        automation_issues=automation_issues,
        unused_entities=unused_entities,
        template_performance=template_performance,
        integration_usage=integration_usage,
        runtime_warnings=runtime_snapshot.warnings + ai_proposals.get("warnings", []),
        ai_proposals=ai_proposals,
    )

    run_summary = {
        "run_id": run_id,
        "started_at": run_id.rsplit("-", 1)[0],
        "finished_at": utc_now_iso(),
        "settings": settings.safe_dict(),
        "parser": parse_result.summary(),
        "runtime": {
            "available": runtime_snapshot.available,
            "states": len(runtime_snapshot.states),
            "components": len(runtime_snapshot.components),
            "services": len(runtime_snapshot.services),
            "warnings": runtime_snapshot.warnings,
            "recorder_details": runtime_snapshot.recorder_details,
        },
        "results": {
            "automation_issues": automation_issues.get("summary", {}),
            "unused_entities": unused_entities.get("summary", {}),
            "template_performance": template_performance.get("summary", {}),
            "integration_usage": integration_usage.get("summary", {}),
            "suggestions": len(suggestions),
            "ai_proposals": len(ai_proposals.get("proposals", [])),
        },
    }

    artifacts = ScanArtifacts(
        run_id=run_id,
        parser_summary=parse_result.summary(),
        automation_issues=automation_issues,
        unused_entities=unused_entities,
        template_performance=template_performance,
        integration_usage=integration_usage,
        automation_graph=automation_graph,
        suggestions_markdown=suggestions_markdown,
        ai_proposals=ai_proposals,
        run_summary=run_summary,
    )

    persisted = write_reports(settings, artifacts)
    run_summary["output"] = persisted
    LOGGER.info("Finished scan run %s", run_id)
    return run_summary
