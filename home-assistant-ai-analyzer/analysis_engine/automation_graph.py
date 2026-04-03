"""
Purpose:
Build a lightweight dependency graph between automations, entities, services, and templates.

Input/Output:
Input is the normalized ConfigParseResult from the parser.
Output is a Cytoscape-friendly JSON structure with nodes, edges, and summary metrics.

Important invariants:
Graph ids must be stable within one run and edge semantics should stay human-readable.

How to debug:
If the graph looks incomplete, inspect the normalized automation records before changing this builder.
"""

from __future__ import annotations

from collections import Counter

from .models import ConfigParseResult


def build_automation_graph(parse_result: ConfigParseResult) -> dict:
    """Create a graph that the UI and later analyzers can both reuse."""

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()
    trigger_counter: Counter[str] = Counter()
    service_counter: Counter[str] = Counter()

    def add_node(node_id: str, label: str, node_type: str) -> None:
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append({"data": {"id": node_id, "label": label, "type": node_type}})

    for automation in parse_result.automations:
        automation_node = f"automation:{automation.automation_id}"
        add_node(automation_node, automation.alias, "automation")

        for entity_id in automation.trigger_entities:
            entity_node = f"entity:{entity_id}"
            add_node(entity_node, entity_id, "entity")
            edges.append(
                {"data": {"source": entity_node, "target": automation_node, "type": "triggers"}}
            )
            trigger_counter[entity_id] += 1

        for entity_id in automation.condition_entities:
            entity_node = f"entity:{entity_id}"
            add_node(entity_node, entity_id, "entity")
            edges.append(
                {"data": {"source": entity_node, "target": automation_node, "type": "conditions"}}
            )

        for entity_id in automation.action_entities:
            entity_node = f"entity:{entity_id}"
            add_node(entity_node, entity_id, "entity")
            edges.append(
                {"data": {"source": automation_node, "target": entity_node, "type": "targets"}}
            )

        for service_id in automation.service_calls:
            service_node = f"service:{service_id}"
            add_node(service_node, service_id, "service")
            edges.append(
                {"data": {"source": automation_node, "target": service_node, "type": "calls"}}
            )
            service_counter[service_id] += 1

        for index, template_text in enumerate(automation.templates):
            template_node = f"template:{automation.automation_id}:{index}"
            add_node(template_node, f"Template {index + 1}", "template")
            edges.append(
                {"data": {"source": automation_node, "target": template_node, "type": "contains"}}
            )
            edges.append(
                {
                    "data": {
                        "source": template_node,
                        "target": automation_node,
                        "type": "influences",
                        "excerpt": template_text[:120],
                    }
                }
            )

    return {
        "summary": {
            "automations": len(parse_result.automations),
            "nodes": len(nodes),
            "edges": len(edges),
            "top_trigger_entities": trigger_counter.most_common(10),
            "top_service_calls": service_counter.most_common(10),
        },
        "nodes": nodes,
        "edges": edges,
    }
