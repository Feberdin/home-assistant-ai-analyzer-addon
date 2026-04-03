"""
Purpose:
Score Jinja templates for patterns that commonly cause unnecessary reevaluation or broad state scans in Home Assistant.

Input/Output:
Input is the list of TemplateRecord objects discovered during config parsing.
Output is a JSON-friendly dictionary with scores, reasons, and suggestions.

Important invariants:
This module should prefer explainable heuristics over opaque scoring so operators can understand each warning.

How to debug:
If a template score feels wrong, inspect the reasons list before changing thresholds or adding more rules.
"""

from __future__ import annotations

from .models import TemplateRecord
from .utils import excerpt_text


def analyze_templates(templates: list[TemplateRecord]) -> dict:
    """Analyze all discovered templates and return structured performance findings."""

    findings = []
    expensive_count = 0

    for template_record in templates:
        score, reasons, suggestions = score_template(template_record.template)
        expensive = score >= 4
        if expensive:
            expensive_count += 1
        findings.append(
            {
                "source_file": template_record.source_file,
                "context": template_record.context,
                "score": score,
                "expensive": expensive,
                "reasons": reasons,
                "suggestions": suggestions,
                "entity_refs": template_record.entity_refs,
                "template_excerpt": excerpt_text(template_record.template, limit=180),
            }
        )

    return {
        "summary": {
            "templates_scanned": len(templates),
            "expensive_templates": expensive_count,
        },
        "templates": findings,
    }


def score_template(template_text: str) -> tuple[int, list[str], list[str]]:
    """Return a simple cost score plus concrete reasons and improvement ideas."""

    lower = template_text.lower()
    score = 0
    reasons: list[str] = []
    suggestions: list[str] = []

    # Why this exists:
    # These heuristics intentionally mirror common Home Assistant anti-patterns
    # so operators can act on them without needing profiler tooling first.
    if "now()" in lower or "utcnow()" in lower:
        score += 3
        reasons.append("Uses now()/utcnow(), which can force frequent reevaluation.")
        suggestions.append("Prefer a trigger-based template when the dependencies are known.")

    if "states." in lower or "states[" in lower or "states |" in lower or "states\n" in lower:
        score += 2
        reasons.append("Scans a broad states collection instead of explicit entities.")
        suggestions.append("Replace broad state iteration with explicit entity dependencies.")

    if "{% for" in lower:
        score += 2
        reasons.append("Contains a loop, which increases template evaluation cost.")
        suggestions.append("Precompute the result in a helper entity or narrow the input set.")

    state_attr_count = lower.count("state_attr(")
    if state_attr_count >= 2:
        score += 2
        reasons.append("Calls state_attr() repeatedly, which can be noisy in complex templates.")
        suggestions.append("Cache repeated attribute access or move logic into a helper sensor.")
    elif state_attr_count == 1:
        score += 1
        reasons.append("Uses state_attr(), which is worth reviewing when templates grow.")

    if "selectattr(" in lower or "rejectattr(" in lower:
        score += 1
        reasons.append("Uses attribute filtering, which often implies list-wide processing.")

    if "expand(" in lower:
        score += 1
        reasons.append("Uses expand(), which can hide wide entity fan-out.")

    if not suggestions:
        suggestions.append("Keep the template as-is, but monitor it if automation churn appears high.")

    return score, reasons, sorted(set(suggestions))
