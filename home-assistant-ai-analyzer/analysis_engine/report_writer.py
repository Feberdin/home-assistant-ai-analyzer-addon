"""
Purpose:
Persist one completed scan run into the required JSON and Markdown files consumed by users and the dashboard.

Input/Output:
Input is the structured ScanArtifacts object from the orchestrator.
Output is a stable set of files below the configured analysis directory.

Important invariants:
All required report files must always be written, even when some modules produced warnings instead of full results.

How to debug:
If the dashboard cannot find a report, verify the output paths and run_summary.json first.
"""

from __future__ import annotations

from pathlib import Path

from .models import AppSettings, ScanArtifacts
from .utils import ensure_directory, write_json, write_text


def write_reports(settings: AppSettings, artifacts: ScanArtifacts) -> dict:
    """Write all required output files plus helpful metadata files."""

    analysis_dir = ensure_directory(settings.output_path)

    write_json(analysis_dir / "automation_issues.json", artifacts.automation_issues)
    write_json(analysis_dir / "unused_entities.json", artifacts.unused_entities)
    write_json(analysis_dir / "template_performance.json", artifacts.template_performance)
    write_json(analysis_dir / "integration_usage.json", artifacts.integration_usage)
    write_json(analysis_dir / "automation_graph.json", artifacts.automation_graph)
    write_text(analysis_dir / "suggestions.md", artifacts.suggestions_markdown)
    write_json(analysis_dir / "run_summary.json", artifacts.run_summary)

    proposals_dir = ensure_directory(Path(analysis_dir) / "proposals")
    write_json(proposals_dir / "latest.json", artifacts.ai_proposals)

    return {
        "analysis_dir": str(analysis_dir),
        "files": sorted(
            [
                "automation_issues.json",
                "unused_entities.json",
                "template_performance.json",
                "integration_usage.json",
                "automation_graph.json",
                "suggestions.md",
                "run_summary.json",
                "proposals/latest.json",
            ]
        ),
    }
