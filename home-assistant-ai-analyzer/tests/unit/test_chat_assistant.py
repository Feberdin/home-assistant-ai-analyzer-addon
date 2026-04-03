"""
Purpose:
Verify that the dashboard chat provides a useful local fallback answer when AI is disabled.

Input/Output:
Input is a synthetic report bundle and a user question about YAML generation.
Output is a human-readable answer that references current findings and explains how AI changes the behavior.

Important invariants:
The fallback must stay bounded to the current reports and must never require network access.

How to debug:
If this test fails, inspect the local answer builder before changing the dashboard chat endpoint.
"""

from analysis_engine.chat_assistant import answer_chat_question
from analysis_engine.models import AppSettings


def test_chat_assistant_answers_locally_when_ai_is_disabled() -> None:
    settings = AppSettings(enable_ai=False)
    reports = {
        "run_summary": {
            "parser": {"yaml_files_scanned": 12, "automations": 4},
            "results": {
                "unused_entities": {"missing_referenced_entities": 3},
                "template_performance": {"expensive_templates": 1},
                "geolocation_history": {"people_tracked": 2},
            },
        },
        "suggestions_markdown": "# Suggestions\n\n- Fix missing entities first.",
        "geolocation_history": {
            "people": [
                {
                    "name": "Joachim",
                    "current_state": "home",
                    "visited_places": ["home", "office"],
                }
            ]
        },
    }

    answer = answer_chat_question(settings, "Erstelle mir YAML fuer eine Automation", reports, language="de")

    assert "Lokale Analyse-Antwort" in answer
    assert "Gescannte YAML-Dateien: 12" in answer
    assert "enable_ai" in answer
