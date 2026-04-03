"""
Purpose:
Turn normalized automation records into explainable issues such as missing entities, long action chains, and costly templates.

Input/Output:
Input is the parsed configuration, runtime snapshot, and template scoring heuristics.
Output is a JSON report grouped by automation.

Important invariants:
Each issue should carry evidence and a remediation hint so the report is useful without reading the source code.

How to debug:
If an automation issue looks surprising, inspect the normalized automation record and the runtime entity set first.
"""

from __future__ import annotations

from collections import Counter

from .models import ConfigParseResult, RuntimeSnapshot
from .template_analyzer import score_template


def analyze_automation_issues(parse_result: ConfigParseResult, runtime_snapshot: RuntimeSnapshot) -> dict:
    """Generate automation-focused issues from static and runtime evidence."""

    runtime_entities = runtime_snapshot.state_ids()
    alias_counter = Counter(automation.alias for automation in parse_result.automations)
    automation_reports = []
    total_issues = 0

    for automation in parse_result.automations:
        issues = []

        if not automation.mode:
            issues.append(
                {
                    "severity": "low",
                    "title": "Automation mode not set explicitly",
                    "reason": "Explicit mode makes concurrency behavior easier to understand and debug.",
                    "suggestion": "Set mode intentionally, for example single, restart, queued, or parallel.",
                }
            )

        if alias_counter[automation.alias] > 1:
            issues.append(
                {
                    "severity": "medium",
                    "title": "Automation alias is duplicated",
                    "reason": "Duplicate aliases make logs and UI views harder to interpret.",
                    "suggestion": "Give each automation a unique alias and stable id.",
                }
            )

        if runtime_snapshot.available:
            missing_entities = sorted(
                entity_id
                for entity_id in set(
                    automation.trigger_entities + automation.condition_entities + automation.action_entities
                )
                if entity_id not in runtime_entities
            )
            if missing_entities:
                issues.append(
                    {
                        "severity": "high",
                        "title": "Automation references missing runtime entities",
                        "reason": "The automation points to entities that are not currently present in Home Assistant.",
                        "entities": missing_entities,
                        "suggestion": "Check renamed entities, disabled integrations, or removed devices.",
                    }
                )

        if len(automation.service_calls) >= 5 or len(automation.action_entities) >= 6:
            issues.append(
                {
                    "severity": "medium",
                    "title": "Automation contains a long action chain",
                    "reason": "Large action chains are harder to test and often benefit from script extraction.",
                    "suggestion": "Move repeated or lengthy action sections into named scripts.",
                }
            )

        for template_text in automation.templates:
            score, reasons, suggestions = score_template(template_text)
            if score >= 4:
                issues.append(
                    {
                        "severity": "medium",
                        "title": "Automation contains a costly template",
                        "reason": "Template heuristics suggest broad or frequent reevaluation.",
                        "score": score,
                        "template_reasons": reasons,
                        "suggestion": suggestions,
                    }
                )
                break

        if issues:
            total_issues += len(issues)
            automation_reports.append(
                {
                    "automation_id": automation.automation_id,
                    "alias": automation.alias,
                    "source_file": automation.source_file,
                    "issues": issues,
                    "service_calls": automation.service_calls,
                    "trigger_entities": automation.trigger_entities,
                    "action_entities": automation.action_entities,
                }
            )

    return {
        "summary": {
            "automations_scanned": len(parse_result.automations),
            "automations_with_issues": len(automation_reports),
            "issues_found": total_issues,
        },
        "automations": automation_reports,
        "parse_errors": parse_result.parse_errors,
    }
