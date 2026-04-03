"""
Purpose:
Combine findings from all analyzers into ranked operator guidance and a Markdown summary.

Input/Output:
Input is the full set of structured analyzer outputs.
Output is a dictionary of prioritized suggestions plus the suggestions.md text.

Important invariants:
Suggestions must stay evidence-based and prioritize operator clarity over overly clever ranking logic.

How to debug:
If the Markdown summary feels off, inspect the ranked suggestion list before changing the text rendering.
"""

from __future__ import annotations


def build_suggestions(
    run_id: str,
    parser_summary: dict,
    automation_issues: dict,
    unused_entities: dict,
    template_performance: dict,
    integration_usage: dict,
    geolocation_history: dict,
    runtime_warnings: list[str],
    ai_proposals: dict,
) -> tuple[list[dict], str]:
    """Create ranked suggestions and the human-readable Markdown summary."""

    suggestions: list[dict] = []

    for item in unused_entities.get("missing_referenced_entities", [])[:20]:
        suggestions.append(
            {
                "priority": 90,
                "category": "entity",
                "title": f"Fix missing entity reference: {item['entity_id']}",
                "reason": item["reason"],
                "action": "Check renamed entities, removed devices, or disabled integrations.",
            }
        )

    for item in automation_issues.get("automations", [])[:20]:
        for issue in item.get("issues", []):
            severity_weight = {"high": 80, "medium": 60, "low": 40}.get(issue["severity"], 30)
            suggestions.append(
                {
                    "priority": severity_weight,
                    "category": "automation",
                    "title": f"{item['alias']}: {issue['title']}",
                    "reason": issue["reason"],
                    "action": issue["suggestion"],
                    "source_file": item["source_file"],
                }
            )

    for item in template_performance.get("templates", []):
        if not item.get("expensive"):
            continue
        suggestions.append(
            {
                "priority": 65,
                "category": "template",
                "title": f"Review expensive template in {item['source_file']}",
                "reason": "; ".join(item["reasons"]),
                "action": "; ".join(item["suggestions"]),
            }
        )

    for item in integration_usage.get("possible_stale_integrations", [])[:10]:
        suggestions.append(
            {
                "priority": 35,
                "category": "integration",
                "title": f"Review possibly stale integration: {item['integration']}",
                "reason": "Configured but not detected as a runtime component during this scan.",
                "action": "Confirm whether the integration is still needed or whether naming differs from the runtime component.",
            }
        )

    geo_summary = geolocation_history.get("summary", {})
    if geo_summary.get("enabled") and geo_summary.get("people_tracked", 0) == 0:
        suggestions.append(
            {
                "priority": 25,
                "category": "geolocation",
                "title": "No person or GPS tracker entities were available for geolocation analysis",
                "reason": "The add-on could not build a people timeline from the current runtime state.",
                "action": "Create Home Assistant person entities or ensure GPS-capable device trackers expose latitude and longitude.",
            }
        )

    for warning in runtime_warnings:
        suggestions.append(
            {
                "priority": 30,
                "category": "runtime",
                "title": "Investigate runtime analysis warning",
                "reason": warning,
                "action": "Check add-on logs, Supervisor API access, and mounted paths.",
            }
        )

    suggestions.sort(key=lambda item: item["priority"], reverse=True)

    markdown_lines = [
        "# Home Assistant AI Analyzer Suggestions",
        "",
        f"- Run ID: `{run_id}`",
        f"- YAML files scanned: `{parser_summary.get('yaml_files_scanned', 0)}`",
        f"- Automations scanned: `{parser_summary.get('automations', 0)}`",
        f"- Templates scanned: `{parser_summary.get('templates', 0)}`",
        f"- Missing referenced entities: `{unused_entities.get('summary', {}).get('missing_referenced_entities', 0)}`",
        f"- Expensive templates: `{template_performance.get('summary', {}).get('expensive_templates', 0)}`",
        f"- People tracked: `{geo_summary.get('people_tracked', 0)}`",
        f"- Geolocation timeline points: `{geo_summary.get('timeline_points', 0)}`",
        "",
        "## Top Suggestions",
    ]

    if suggestions:
        for suggestion in suggestions[:15]:
            markdown_lines.extend(
                [
                    f"### {suggestion['title']}",
                    f"- Category: `{suggestion['category']}`",
                    f"- Priority: `{suggestion['priority']}`",
                    f"- Why this matters: {suggestion['reason']}",
                    f"- Recommended action: {suggestion['action']}",
                    "",
                ]
            )
    else:
        markdown_lines.extend(
            [
                "No high-priority suggestions were generated in this run.",
                "",
                ]
            )

    if geolocation_history.get("people"):
        markdown_lines.append("## Geolocation Summary")
        for person in geolocation_history["people"][:10]:
            latest_place = person.get("current_state", "unknown")
            markdown_lines.extend(
                [
                    f"### {person['name']}",
                    f"- Current place: `{latest_place}`",
                    f"- Known places: {', '.join(person.get('visited_places', [])[:8]) or 'none'}",
                    "",
                ]
            )

    if ai_proposals.get("proposals"):
        markdown_lines.append("## AI Proposal Summary")
        for proposal in ai_proposals["proposals"][:5]:
            title = proposal.get("title", "Untitled proposal")
            benefit = proposal.get("expected_benefit", "No expected benefit was provided.")
            markdown_lines.extend(
                [
                    f"### {title}",
                    f"- Expected benefit: {benefit}",
                    "",
                ]
            )

    return suggestions, "\n".join(markdown_lines).strip() + "\n"
