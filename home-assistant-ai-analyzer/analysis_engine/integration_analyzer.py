"""
Purpose:
Summarize configured integrations and compare them with runtime components, recorder hints, and static usage signals.

Input/Output:
Input is the parsed configuration plus optional runtime snapshot.
Output is a JSON report describing integration presence, usage clues, and probable inefficiencies.

Important invariants:
Integration matching must stay conservative because configuration keys and runtime component names are not always identical.

How to debug:
If an integration looks misclassified, inspect the configured and runtime lists side by side before adjusting heuristics.
"""

from __future__ import annotations

from .models import ConfigParseResult, RuntimeSnapshot


def analyze_integrations(parse_result: ConfigParseResult, runtime_snapshot: RuntimeSnapshot) -> dict:
    """Create an operator-friendly view of configured and active integrations."""

    runtime_components = set(runtime_snapshot.components)
    configured = sorted(set(parse_result.configured_integrations))
    analyzed = []

    for integration in configured:
        analyzed.append(
            {
                "integration": integration,
                "loaded_at_runtime": integration in runtime_components,
                "notes": _integration_notes(integration, runtime_snapshot),
            }
        )

    possible_stale = [
        item
        for item in analyzed
        if not item["loaded_at_runtime"] and item["integration"] not in {"default_config", "homeassistant"}
    ]

    recorder_signals = []
    if "recorder" in configured:
        recorder_signals.append("Recorder is configured in YAML.")
    if runtime_snapshot.recorder_details:
        recorder_signals.append("Recorder database file is reachable from the add-on.")
    if "recorder" in runtime_snapshot.error_log_excerpt.lower():
        recorder_signals.append("Recorder-related messages were found in the current error log excerpt.")

    return {
        "summary": {
            "configured_integrations": len(configured),
            "runtime_components": len(runtime_components),
            "possible_stale_integrations": len(possible_stale),
        },
        "configured_integrations": analyzed,
        "possible_stale_integrations": possible_stale,
        "recorder_signals": recorder_signals,
        "runtime_warnings": runtime_snapshot.warnings,
    }


def _integration_notes(integration: str, runtime_snapshot: RuntimeSnapshot) -> list[str]:
    """Return lightweight hints that help operators interpret one integration line item."""

    notes: list[str] = []
    if integration == "recorder":
        notes.append("Review include/exclude settings if database growth is high.")
    if integration == "template":
        notes.append("Template-heavy setups benefit from reviewing expensive templates first.")
    if integration not in runtime_snapshot.components:
        notes.append("No matching runtime component was detected during this scan.")
    return notes
