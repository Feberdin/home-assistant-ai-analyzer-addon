"""
Purpose:
Verify that obviously costly Home Assistant templates receive a non-trivial score and actionable reasons.

Input/Output:
Input is a synthetic TemplateRecord.
Output is a scored template performance report.

Important invariants:
The analyzer should explain why a template was flagged, not only return a number.

How to debug:
If the score looks wrong, inspect the reasons list before tuning thresholds.
"""

from analysis_engine.models import TemplateRecord
from analysis_engine.template_analyzer import analyze_templates


def test_template_analyzer_flags_broad_now_based_template() -> None:
    record = TemplateRecord(
        source_file="templates.yaml",
        context="root.template",
        template="{% for item in states.sensor %}{{ now() }} {{ state_attr(item.entity_id, 'friendly_name') }}{% endfor %}",
        entity_refs=[],
    )

    report = analyze_templates([record])

    assert report["summary"]["expensive_templates"] == 1
    assert report["templates"][0]["score"] >= 4
    assert report["templates"][0]["reasons"]

