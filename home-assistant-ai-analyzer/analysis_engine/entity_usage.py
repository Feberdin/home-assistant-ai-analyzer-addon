"""
Purpose:
Compare static configuration references with runtime state data to highlight missing, unused, and over-coupled entities.

Input/Output:
Input is the parsed configuration model, automation graph, and optional runtime snapshot.
Output is a structured JSON report focused on entity usage patterns.

Important invariants:
Unused-entity findings must be labeled as likely or confidence-based because dashboards and manual usage are not fully observable.

How to debug:
If an entity is flagged incorrectly, inspect the reference counts and runtime availability before changing thresholds.
"""

from __future__ import annotations

from collections import Counter

from .models import ConfigParseResult, RuntimeSnapshot


IGNORED_UNUSED_DOMAINS = {"automation", "group", "person", "sun", "zone"}


def analyze_entity_usage(
    parse_result: ConfigParseResult,
    automation_graph: dict,
    runtime_snapshot: RuntimeSnapshot,
) -> dict:
    """Merge static and runtime evidence into entity usage findings."""

    reference_counts = Counter(parse_result.entity_reference_counts)
    runtime_entities = runtime_snapshot.state_ids() if runtime_snapshot.available else set()
    missing_entities = sorted(entity_id for entity_id in reference_counts if entity_id not in runtime_entities)

    likely_unused_runtime_entities = []
    if runtime_snapshot.available:
        for entity_id in sorted(runtime_entities):
            if reference_counts.get(entity_id, 0) > 0:
                continue
            domain = entity_id.split(".", 1)[0]
            if domain in IGNORED_UNUSED_DOMAINS:
                continue
            likely_unused_runtime_entities.append(
                {
                    "entity_id": entity_id,
                    "reason": "Visible at runtime but not referenced in scanned YAML files.",
                    "confidence": 0.45,
                }
            )

    high_fanout_entities = []
    for entity_id, count in reference_counts.most_common():
        if count < 3:
            continue
        high_fanout_entities.append(
            {
                "entity_id": entity_id,
                "reference_count": count,
                "reason": "Entity is referenced repeatedly across the scanned configuration.",
            }
        )

    return {
        "summary": {
            "referenced_entities": len(reference_counts),
            "runtime_entities": len(runtime_entities),
            "missing_referenced_entities": len(missing_entities),
            "likely_unused_runtime_entities": len(likely_unused_runtime_entities),
            "high_fanout_entities": len(high_fanout_entities),
            "graph_nodes": automation_graph.get("summary", {}).get("nodes", 0),
        },
        "missing_referenced_entities": [
            {
                "entity_id": entity_id,
                "reference_count": reference_counts.get(entity_id, 0),
                "reason": "Referenced in YAML but not present in current Home Assistant runtime state.",
            }
            for entity_id in missing_entities
        ],
        "likely_unused_runtime_entities": likely_unused_runtime_entities[:150],
        "high_fanout_entities": high_fanout_entities[:50],
    }
