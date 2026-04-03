"""
Purpose:
Provide a simple in-app assistant that can discuss scan findings and, when AI is enabled, generate Home Assistant YAML suggestions from the current analysis reports.

Input/Output:
Input is the current AppSettings, the user question, and a small bundle of already-generated reports.
Output is a plain-text answer intended for the dashboard chat panel.

Important invariants:
The assistant must stay bounded to the current report context and must not expose secrets or raw geolocation coordinates unless explicitly allowed.

How to debug:
If the chat answer feels wrong, inspect the report bundle and whether AI is enabled before changing the prompt or fallback logic.
"""

from __future__ import annotations

import json
import logging

import httpx

from .models import AppSettings


LOGGER = logging.getLogger(__name__)


def answer_chat_question(settings: AppSettings, question: str, reports: dict, language: str = "en") -> str:
    """Return a local or AI-assisted answer for the dashboard chat."""

    cleaned_question = question.strip()
    german = language.startswith("de")
    if not cleaned_question:
        return (
            "Bitte stelle eine konkrete Frage, zum Beispiel zu fehlenden Entities, teuren Templates oder einer neuen Automation."
            if german
            else "Please ask a concrete question, for example about missing entities, expensive templates, or a new automation."
        )

    if settings.enable_ai and settings.llm_api_key:
        return _answer_with_ai(settings, cleaned_question, reports, language=language)

    return _answer_locally(cleaned_question, reports, ai_enabled=settings.enable_ai, language=language)


def _answer_locally(question: str, reports: dict, ai_enabled: bool, language: str) -> str:
    """Provide a useful fallback answer from local report data when AI is disabled."""

    german = language.startswith("de")
    summary = reports.get("run_summary", {})
    parser = summary.get("parser", {})
    results = summary.get("results", {})
    settings = summary.get("settings", {})
    suggestions = reports.get("suggestions_markdown", "")
    geo = reports.get("geolocation_history", {})

    if german:
        lines = [
            "Lokale Analyse-Antwort",
            "",
            f"- Gescannte YAML-Dateien: {parser.get('yaml_files_scanned', 0)}",
            f"- Automationen: {parser.get('automations', 0)}",
            f"- Fehlende referenzierte Entities: {results.get('unused_entities', {}).get('missing_referenced_entities', 0)}",
            f"- Teure Templates: {results.get('template_performance', {}).get('expensive_templates', 0)}",
            f"- Personen mit Geodaten: {results.get('geolocation_history', {}).get('people_tracked', 0)}",
            "",
        ]
    else:
        lines = [
            "Local analysis answer",
            "",
            f"- Scanned YAML files: {parser.get('yaml_files_scanned', 0)}",
            f"- Automations: {parser.get('automations', 0)}",
            f"- Missing referenced entities: {results.get('unused_entities', {}).get('missing_referenced_entities', 0)}",
            f"- Expensive templates: {results.get('template_performance', {}).get('expensive_templates', 0)}",
            f"- People with geodata: {results.get('geolocation_history', {}).get('people_tracked', 0)}",
            "",
        ]

    lower = question.lower()
    if "yaml" in lower or "automation" in lower:
        lines.extend(
            [
                "Ich kann dir lokal schon sagen, welche Bereiche auffaellig sind, aber fuer konkrete YAML-Erzeugung solltest du `enable_ai: true` aktivieren.",
                "Dann kann der Chat direkt aus den aktuellen Findings Home-Assistant-YAML entwerfen.",
                "",
            ]
            if german
            else [
                "I can already point out the relevant areas locally, but for concrete YAML generation you should enable `enable_ai: true`.",
                "Then the chat can draft Home Assistant YAML directly from the current findings.",
                "",
            ]
        )
    elif "geo" in lower or "person" in lower or "standort" in lower:
        people = geo.get("people", [])
        if people:
            for person in people[:5]:
                if german:
                    lines.append(
                        f"- {person.get('name')}: aktueller Ort `{person.get('current_state', 'unknown')}`, bekannte Orte: {', '.join(person.get('visited_places', [])[:6]) or 'keine'}"
                    )
                else:
                    lines.append(
                        f"- {person.get('name')}: current place `{person.get('current_state', 'unknown')}`, known places: {', '.join(person.get('visited_places', [])[:6]) or 'none'}"
                    )
            lines.append("")
        else:
            lines.extend(
                [
                    "Es wurden aktuell keine Personen- oder GPS-Tracker-Daten fuer die Geolocation-Auswertung gefunden.",
                    "",
                ]
                if german
                else [
                    "No person or GPS tracker data is currently available for geolocation analysis.",
                    "",
                ]
            )
    elif "einstellung" in lower or "setting" in lower or "konfiguration" in lower:
        lines.extend(
            [
                f"- Scan-Modus: `{settings.get('scan_mode', 'unknown')}`",
                f"- Runtime-Analyse: `{settings.get('enable_runtime_analysis', False)}`",
                f"- Geolocation-Analyse: `{settings.get('enable_geolocation_analysis', False)}`",
                f"- AI aktiv: `{settings.get('enable_ai', False)}`",
                f"- Lookback-Tage: `{settings.get('lookback_days', 0)}`",
                "",
                "Wenn du mehr YAML-Hilfe willst, ist die wichtigste Stellschraube `enable_ai: true` plus ein gueltiger API-Schluessel.",
                "",
            ]
            if german
            else [
                f"- Scan mode: `{settings.get('scan_mode', 'unknown')}`",
                f"- Runtime analysis: `{settings.get('enable_runtime_analysis', False)}`",
                f"- Geolocation analysis: `{settings.get('enable_geolocation_analysis', False)}`",
                f"- AI enabled: `{settings.get('enable_ai', False)}`",
                f"- Lookback days: `{settings.get('lookback_days', 0)}`",
                "",
                "If you want stronger YAML help, the most important switch is `enable_ai: true` plus a valid API key.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Die wichtigsten Handlungspunkte stehen bereits in `suggestions.md`.",
                "Wenn du magst, frage mich konkreter nach einer Automation, einem Bereich oder einem Ziel wie 'erstelle mir eine YAML fuer Anwesenheitslicht'.",
                "",
            ]
            if german
            else [
                "The most important action items are already summarized in `suggestions.md`.",
                "If you want, ask me more specifically about one automation, one area, or a goal such as 'create YAML for a presence-based light'.",
                "",
            ]
        )

    if not ai_enabled:
        lines.append(
            "Hinweis: Fuer einen echten YAML-Generator im Chat aktiviere im Add-on `enable_ai` und hinterlege einen gueltigen API-Schluessel."
            if german
            else "Note: For a real YAML generator in the chat, enable `enable_ai` in the add-on and provide a valid API key."
        )

    if suggestions:
        suggestion_lines = [line.strip() for line in suggestions.splitlines() if line.strip()]
        lines.extend(
            [
                "",
                "Auszug aus den aktuellen Empfehlungen:",
                suggestion_lines[1] if len(suggestion_lines) > 1 else suggestion_lines[0] if suggestion_lines else "",
            ]
            if german
            else [
                "",
                "Excerpt from the current recommendations:",
                suggestion_lines[1] if len(suggestion_lines) > 1 else suggestion_lines[0] if suggestion_lines else "",
            ]
        )

    return "\n".join(line for line in lines if line != "")


def _answer_with_ai(settings: AppSettings, question: str, reports: dict, language: str) -> str:
    """Send a bounded report context to the configured LLM provider."""

    german = language.startswith("de")
    payload = {
        "question": question,
        "constraints": [
            "Answer in German." if german else "Answer in English.",
            "Be practical and Home-Assistant-specific.",
            "When useful, produce valid Home Assistant YAML snippets.",
            "Do not invent entities or services.",
            "Do not expose secrets, tokens, or raw private coordinates.",
        ],
        "run_summary": reports.get("run_summary", {}),
        "automation_issues": reports.get("automation_issues", {}).get("automations", [])[:8],
        "unused_entities": reports.get("unused_entities", {}).get("missing_referenced_entities", [])[:12],
        "template_findings": [
            item for item in reports.get("template_performance", {}).get("templates", []) if item.get("expensive")
        ][:8],
        "integration_findings": reports.get("integration_usage", {}).get("possible_stale_integrations", [])[:8],
    }

    if settings.enable_ai_geolocation_context:
        payload["geolocation_summary"] = reports.get("geolocation_history", {}).get("ai_summary", [])[:6]

    try:
        response = httpx.post(
            settings.llm_base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior Home Assistant architect and YAML assistant. "
                            "Discuss settings, findings, and generate Home Assistant YAML when requested."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Dashboard chat AI request failed: %s", err)
        if german:
            return (
                "Die KI-Antwort konnte gerade nicht erzeugt werden. "
                f"Technischer Hinweis: {err}\n\n"
                "Du kannst trotzdem weiter die Reports nutzen oder AI-Konfiguration und Netzwerkzugang pruefen."
            )
        return (
            "The AI answer could not be generated right now. "
            f"Technical hint: {err}\n\n"
            "You can still use the reports, or verify the AI configuration and outbound network access."
        )
