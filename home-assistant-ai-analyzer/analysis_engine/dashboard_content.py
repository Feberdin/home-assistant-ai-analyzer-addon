"""
Purpose:
Build localized dashboard text and small explanatory view-models from the raw scan reports.

Input/Output:
Input is the preferred UI language, add-on settings, scan summary, report bundle, and report URLs.
Output is a JSON-serializable collection of translated labels, metric cards, finding cards, guidance items, and client-side helper strings.

Important invariants:
This module must stay deterministic and side-effect free so the dashboard remains easy to test and reason about.

How to debug:
If the UI wording or examples look wrong, inspect the intermediate report dictionaries before changing the translations or card builders.
"""

from __future__ import annotations

from collections.abc import Mapping


TRANSLATIONS = {
    "en": {
        "analyzer_label": "Analyzer",
        "app_title": "Home Assistant AI Analyzer",
        "app_intro": (
            "Scan the mounted Home Assistant configuration, compare it with runtime data, "
            "and generate explainable findings before changing anything live."
        ),
        "run_scan_label": "Run Scan",
        "current_status_label": "Current Status",
        "latest_run_label": "Latest run:",
        "scan_mode_label": "Scan mode:",
        "status_idle": "IDLE",
        "status_running": "RUNNING",
        "status_success": "SUCCESS",
        "status_error": "ERROR",
        "reports_label": "Reports",
        "open_label": "Open",
        "latest_findings_label": "Latest Findings",
        "assistant_label": "Assistant",
        "assistant_intro": (
            "Ask about findings, settings, or let the analyzer propose Home Assistant YAML from the current scan context."
        ),
        "assistant_placeholder": (
            "Example: Create Home Assistant YAML for a presence-based hallway light using the available people or trackers."
        ),
        "assistant_button": "Ask Analyzer",
        "assistant_initial_answer": (
            "Ask a concrete question about your settings, automations, or a YAML goal. "
            "If AI is disabled, the analyzer answers locally from the reports."
        ),
        "ai_label": "AI",
        "geo_ai_label": "Geo AI context",
        "enabled_label": "enabled",
        "disabled_label": "disabled",
        "guidance_label": "Guidance",
        "location_map_label": "Location Map",
        "map_intro": (
            "OpenStreetMap tile view for the latest tracked positions. Routes and markers remain visible even if tile loading is blocked."
        ),
        "map_bounds_prefix": "Bounds:",
        "map_no_bounds": "No coordinate bounds available yet.",
        "map_note": (
            "The browser loads OpenStreetMap tiles directly. If your network blocks that traffic, the route overlay still remains visible."
        ),
        "people_timeline_label": "Routes and Timeline",
        "kind_person": "Person",
        "kind_vehicle": "Vehicle",
        "kind_tracker": "Tracker",
        "current_label": "Current",
        "last_update_label": "Last update",
        "known_places_label": "Known places",
        "open_osm_label": "Open latest position in OpenStreetMap",
        "recent_stays_label": "Recent stays",
        "route_summary_label": "Route",
        "route_points_label": "points",
        "route_distance_label": "km",
        "no_people_timeline": "No people timeline is available for this scan.",
        "no_known_places": "none",
        "no_examples": "No concrete examples are available yet.",
        "examples_label": "Examples",
        "assistant_thinking": "Analyzer is thinking...",
        "assistant_empty_question": "Please ask a concrete question first, for example about one automation, entity, or YAML idea.",
        "assistant_no_answer": "No answer was returned.",
        "assistant_fetch_failed": "The chat request failed. Technical hint:",
        "no_points_available": (
            "No geolocation points are available yet. Run a scan with runtime analysis enabled and ensure Home Assistant exposes person or GPS tracker entities."
        ),
        "preset_top_problems_label": "Top problems",
        "preset_top_problems_prompt": "Which three problems should I fix first?",
        "preset_missing_entities_label": "Missing entities",
        "preset_missing_entities_prompt": "Explain the missing referenced entities and how I should clean them up.",
        "preset_presence_yaml_label": "Presence YAML",
        "preset_presence_yaml_prompt": "Create Home Assistant YAML for a presence-based light using the available people or trackers.",
        "preset_settings_label": "Settings advice",
        "preset_settings_prompt": "Which add-on settings should I adjust first?",
        "scan_mode_quick": "Quick",
        "scan_mode_full": "Full",
        "scan_mode_deep": "Deep",
        "metric_yaml_files_title": "YAML Files",
        "metric_yaml_files_description": "Number of YAML files the analyzer actually parsed below the mounted configuration path.",
        "metric_automations_title": "Automations",
        "metric_automations_description": "Automations normalized into one internal model so references, templates, and actions can be compared consistently.",
        "metric_suggestions_title": "Suggestions",
        "metric_suggestions_description": "Prioritized actions derived from the findings, not just raw warning counts.",
        "metric_people_title": "Tracked Entities",
        "metric_people_description": "People, vehicles, or extra GPS trackers found in runtime history and prepared for route analysis.",
        "report_automation_issues": "Automation structure findings with reasons, severity, and remediation hints.",
        "report_unused_entities": "Entity references that look missing at runtime or likely unused in YAML.",
        "report_template_performance": "Template cost heuristics, why they were flagged, and what to improve.",
        "report_integration_usage": "Configured integrations compared with runtime components and recorder-related clues.",
        "report_geolocation_history": "Per-person location timeline, recent stays, visited places, and map data.",
        "report_automation_graph": "Dependency graph linking automations, entities, services, and templates.",
        "report_suggestions": "Operator-friendly markdown summary of the most important next steps.",
        "report_run_summary": "Compact overview of the latest run, settings snapshot, and module summaries.",
        "finding_missing_title": "Missing referenced entities",
        "finding_missing_description": (
            "These entity IDs appear in YAML, but Home Assistant did not expose them at runtime during the scan. "
            "That often points to renamed devices, removed integrations, or stale automation targets."
        ),
        "finding_templates_title": "Expensive templates",
        "finding_templates_description": (
            "These templates are likely reevaluated too broadly or too often. They are good candidates for trigger-based templates or narrower entity dependencies."
        ),
        "finding_automation_title": "Automation issues",
        "finding_automation_description": (
            "This combines missing entities, duplicated aliases, long action chains, and costly template usage inside automations."
        ),
        "finding_runtime_title": "Runtime warnings",
        "finding_runtime_description": (
            "Warnings from API or recorder collection. They usually explain why parts of the analysis are incomplete or need extra permissions."
        ),
        "guidance_runtime": "Runtime analysis is {value}. This controls whether the add-on can compare YAML with live Home Assistant state.",
        "guidance_geo": "Geolocation analysis is {value}. When enabled, people, vehicles, and tracker history is summarized locally into stays and routes.",
        "guidance_lookback": "Lookback window: {value} days. Increase this if you want longer history for people movement or runtime trend checks.",
        "guidance_points": "Geolocation point limit: {value}. This is the maximum number of timeline points kept per tracked entity for the map.",
        "guidance_interval": "There is no fixed add-on polling interval. Routes use the recorded Home Assistant history within the last {days} days and keep up to {points} significant location changes per tracked entity.",
        "guidance_reports": "If a report looks stale, run a fresh scan and reopen the linked report afterwards.",
        "message_loaded": "Loaded the latest scan summary from disk.",
        "message_no_scan": "No scan has been started yet.",
        "message_running": "Scan is running.",
        "message_success": "Scan finished successfully.",
        "message_already_running": "A scan is already running.",
        "message_failed_prefix": "Scan failed:",
    },
    "de": {
        "analyzer_label": "Analysator",
        "app_title": "Home Assistant AI Analyzer",
        "app_intro": (
            "Analysiere die eingebundene Home-Assistant-Konfiguration, vergleiche sie mit Laufzeitdaten "
            "und erzeuge nachvollziehbare Hinweise, bevor irgendetwas live geändert wird."
        ),
        "run_scan_label": "Scan starten",
        "current_status_label": "Aktueller Status",
        "latest_run_label": "Letzter Lauf:",
        "scan_mode_label": "Scan-Modus:",
        "status_idle": "BEREIT",
        "status_running": "LÄUFT",
        "status_success": "ERFOLGREICH",
        "status_error": "FEHLER",
        "reports_label": "Berichte",
        "open_label": "Öffnen",
        "latest_findings_label": "Aktuelle Erkenntnisse",
        "assistant_label": "Assistent",
        "assistant_intro": (
            "Frage nach Auffälligkeiten, Einstellungen oder lasse dir aus dem aktuellen Scan-Kontext Home-Assistant-YAML vorschlagen."
        ),
        "assistant_placeholder": (
            "Beispiel: Erstelle Home-Assistant-YAML für ein Anwesenheitslicht im Flur auf Basis der vorhandenen Personen oder Tracker."
        ),
        "assistant_button": "Analysator fragen",
        "assistant_initial_answer": (
            "Stelle eine konkrete Frage zu deinen Einstellungen, Automationen oder einem YAML-Ziel. "
            "Wenn KI deaktiviert ist, antwortet der Analyzer lokal aus den Reports."
        ),
        "ai_label": "KI",
        "geo_ai_label": "Geo-KI-Kontext",
        "enabled_label": "aktiv",
        "disabled_label": "deaktiviert",
        "guidance_label": "Einordnung",
        "location_map_label": "Standortkarte",
        "map_intro": (
            "OpenStreetMap-Kartenansicht für die zuletzt erkannten Positionen. Routen und Marker bleiben sichtbar, auch wenn Kacheln blockiert werden."
        ),
        "map_bounds_prefix": "Grenzen:",
        "map_no_bounds": "Es sind noch keine Koordinatengrenzen verfügbar.",
        "map_note": (
            "Die Browseransicht lädt OpenStreetMap-Kacheln direkt. Wenn dein Netzwerk das blockiert, bleibt das Routen-Overlay trotzdem sichtbar."
        ),
        "people_timeline_label": "Routen und Zeitachse",
        "kind_person": "Person",
        "kind_vehicle": "Fahrzeug",
        "kind_tracker": "Tracker",
        "current_label": "Aktuell",
        "last_update_label": "Letzte Aktualisierung",
        "known_places_label": "Bekannte Orte",
        "open_osm_label": "Neueste Position in OpenStreetMap öffnen",
        "recent_stays_label": "Letzte Aufenthalte",
        "route_summary_label": "Route",
        "route_points_label": "Punkte",
        "route_distance_label": "km",
        "no_people_timeline": "Für diesen Scan ist noch keine Personen-Zeitachse verfügbar.",
        "no_known_places": "keine",
        "no_examples": "Es sind noch keine konkreten Beispiele verfügbar.",
        "examples_label": "Beispiele",
        "assistant_thinking": "Analyzer denkt nach...",
        "assistant_empty_question": "Bitte stelle zuerst eine konkrete Frage, zum Beispiel zu einer Automation, Entity oder YAML-Idee.",
        "assistant_no_answer": "Es wurde keine Antwort zurückgegeben.",
        "assistant_fetch_failed": "Die Chat-Anfrage ist fehlgeschlagen. Technischer Hinweis:",
        "no_points_available": (
            "Es sind noch keine Geopunkte verfügbar. Starte einen Scan mit aktivierter Laufzeitanalyse und stelle sicher, dass Home Assistant Personen- oder GPS-Tracker-Entities liefert."
        ),
        "preset_top_problems_label": "Top-Probleme",
        "preset_top_problems_prompt": "Welche drei Probleme sollte ich zuerst beheben?",
        "preset_missing_entities_label": "Fehlende Entities",
        "preset_missing_entities_prompt": "Erkläre mir die fehlenden referenzierten Entities und wie ich sie bereinigen sollte.",
        "preset_presence_yaml_label": "Anwesenheits-YAML",
        "preset_presence_yaml_prompt": "Erstelle Home-Assistant-YAML für ein Anwesenheitslicht mit den vorhandenen Personen oder Trackern.",
        "preset_settings_label": "Einstellungs-Hilfe",
        "preset_settings_prompt": "Welche Add-on-Einstellungen sollte ich zuerst anpassen?",
        "scan_mode_quick": "Schnell",
        "scan_mode_full": "Voll",
        "scan_mode_deep": "Tiefgehend",
        "metric_yaml_files_title": "YAML-Dateien",
        "metric_yaml_files_description": "So viele YAML-Dateien hat der Analyzer unter dem eingebundenen Konfigurationspfad tatsächlich eingelesen.",
        "metric_automations_title": "Automationen",
        "metric_automations_description": "Diese Automationen wurden in ein gemeinsames Modell überführt, damit Referenzen, Templates und Aktionen vergleichbar analysiert werden können.",
        "metric_suggestions_title": "Empfehlungen",
        "metric_suggestions_description": "Priorisierte Maßnahmen aus den Findings, nicht nur eine rohe Anzahl an Warnungen.",
        "metric_people_title": "Verfolgte Entitäten",
        "metric_people_description": "Personen, Fahrzeuge oder zusätzliche GPS-Tracker, die in der Laufzeithistorie gefunden und für Routen analysiert wurden.",
        "report_automation_issues": "Strukturprobleme in Automationen mit Begründung, Schweregrad und Verbesserungshinweisen.",
        "report_unused_entities": "Entity-Referenzen, die zur Laufzeit fehlen oder in YAML wahrscheinlich ungenutzt sind.",
        "report_template_performance": "Template-Kostenheuristiken, warum sie auffällig sind und was du verbessern kannst.",
        "report_integration_usage": "Konfigurierte Integrationen im Vergleich zu Runtime-Komponenten und Recorder-Hinweisen.",
        "report_geolocation_history": "Standortverlauf pro Person, letzte Aufenthalte, bekannte Orte und Kartendaten.",
        "report_automation_graph": "Abhängigkeitsgraph zwischen Automationen, Entities, Services und Templates.",
        "report_suggestions": "Operator-freundliche Markdown-Zusammenfassung der wichtigsten nächsten Schritte.",
        "report_run_summary": "Kompakter Überblick über den letzten Lauf, Settings-Snapshot und Modulzusammenfassungen.",
        "finding_missing_title": "Fehlende referenzierte Entities",
        "finding_missing_description": (
            "Diese Entity-IDs tauchen in YAML auf, wurden aber während des Scans nicht in Home Assistant gefunden. "
            "Das deutet oft auf umbenannte Geräte, entfernte Integrationen oder veraltete Automationsziele hin."
        ),
        "finding_templates_title": "Teure Templates",
        "finding_templates_description": (
            "Diese Templates werden vermutlich zu breit oder zu häufig neu ausgewertet. "
            "Sie sind gute Kandidaten für triggerbasierte Templates oder engere Entity-Abhängigkeiten."
        ),
        "finding_automation_title": "Automationsprobleme",
        "finding_automation_description": (
            "Hier werden fehlende Entities, doppelte Aliasse, lange Aktionsketten und teure Template-Nutzung in Automationen zusammengeführt."
        ),
        "finding_runtime_title": "Runtime-Warnungen",
        "finding_runtime_description": (
            "Warnungen aus API- oder Recorder-Abfragen. Sie erklären meist, warum Teile der Analyse unvollständig sind oder zusätzliche Rechte brauchen."
        ),
        "guidance_runtime": "Laufzeitanalyse ist {value}. Nur damit kann das Add-on YAML mit dem aktuellen Home-Assistant-Zustand vergleichen.",
        "guidance_geo": "Geolokalisierungsanalyse ist {value}. Wenn sie aktiv ist, werden Personen-, Fahrzeug- und Tracker-Verläufe lokal zu Aufenthalten und Routen verdichtet.",
        "guidance_lookback": "Rückblickfenster: {value} Tage. Erhöhe den Wert, wenn du längere Historien für Bewegungen oder Laufzeittrends brauchst.",
        "guidance_points": "Geopunkt-Limit: {value}. So viele Verlaufspunkte werden maximal pro verfolgter Entität für die Karte behalten.",
        "guidance_interval": "Es gibt kein festes Polling-Intervall des Add-ons. Die Routen nutzen die in Home Assistant aufgezeichnete Historie der letzten {days} Tage und behalten bis zu {points} signifikante Ortsänderungen pro verfolgter Entität.",
        "guidance_reports": "Wenn ein Report veraltet wirkt, starte einen neuen Scan und öffne den Bericht danach erneut.",
        "message_loaded": "Die letzte Scan-Zusammenfassung wurde von der Festplatte geladen.",
        "message_no_scan": "Es wurde noch kein Scan gestartet.",
        "message_running": "Der Scan läuft.",
        "message_success": "Der Scan wurde erfolgreich abgeschlossen.",
        "message_already_running": "Es läuft bereits ein Scan.",
        "message_failed_prefix": "Scan fehlgeschlagen:",
    },
}


def detect_language(accept_language: str | None) -> str:
    """Pick a supported UI language from the browser language header."""

    if not accept_language:
        return "en"

    candidates = [item.strip().lower() for item in accept_language.split(",")]
    for candidate in candidates:
        language = candidate.split(";")[0].split("-")[0]
        if language in TRANSLATIONS:
            return language
    return "en"


def get_text(language: str) -> dict:
    """Return the translation dictionary for the chosen language."""

    return TRANSLATIONS.get(language, TRANSLATIONS["en"])


def localize_status(status: str, language: str) -> str:
    """Translate the short scan status label used in the badge."""

    text = get_text(language)
    return {
        "idle": text["status_idle"],
        "running": text["status_running"],
        "success": text["status_success"],
        "error": text["status_error"],
    }.get(status, status.upper())


def localize_message(message: str, language: str) -> str:
    """Translate well-known scan lifecycle messages without hiding unknown details."""

    text = get_text(language)
    known = {
        "Loaded the latest scan summary from disk.": text["message_loaded"],
        "No scan has been started yet.": text["message_no_scan"],
        "Scan is running.": text["message_running"],
        "Scan finished successfully.": text["message_success"],
        "A scan is already running.": text["message_already_running"],
    }
    if message in known:
        return known[message]
    if message.startswith("Scan failed:"):
        suffix = message.split("Scan failed:", 1)[1].strip()
        return f"{text['message_failed_prefix']} {suffix}".strip()
    return message


def build_ui(language: str) -> dict:
    """Return localized static strings and chat presets for the dashboard."""

    text = get_text(language)
    return {
        **text,
        "assistant_presets": [
            {
                "label": text["preset_top_problems_label"],
                "prompt": text["preset_top_problems_prompt"],
            },
            {
                "label": text["preset_missing_entities_label"],
                "prompt": text["preset_missing_entities_prompt"],
            },
            {
                "label": text["preset_presence_yaml_label"],
                "prompt": text["preset_presence_yaml_prompt"],
            },
            {
                "label": text["preset_settings_label"],
                "prompt": text["preset_settings_prompt"],
            },
        ],
        "client_text": {
            "no_points_available": text["no_points_available"],
            "assistant_thinking": text["assistant_thinking"],
            "assistant_empty_question": text["assistant_empty_question"],
            "assistant_no_answer": text["assistant_no_answer"],
            "assistant_fetch_failed": text["assistant_fetch_failed"],
        },
    }


def build_metric_cards(language: str, settings: Mapping[str, object], summary: dict, geolocation_report: dict) -> list[dict]:
    """Create the top-level metric cards with translated explanations."""

    text = get_text(language)
    results = summary.get("results", {}) if isinstance(summary, dict) else {}
    parser = summary.get("parser", {}) if isinstance(summary, dict) else {}
    return [
        {
            "title": text["metric_yaml_files_title"],
            "value": parser.get("yaml_files_scanned", 0),
            "description": text["metric_yaml_files_description"],
            "detail": settings.get("base_config_path", "/homeassistant"),
        },
        {
            "title": text["metric_automations_title"],
            "value": parser.get("automations", 0),
            "description": text["metric_automations_description"],
            "detail": "",
        },
        {
            "title": text["metric_suggestions_title"],
            "value": results.get("suggestions", 0),
            "description": text["metric_suggestions_description"],
            "detail": "",
        },
        {
            "title": text["metric_people_title"],
            "value": geolocation_report.get("summary", {}).get(
                "tracked_entities",
                geolocation_report.get("summary", {}).get("people_tracked", 0),
            ),
            "description": text["metric_people_description"],
            "detail": _tracked_entities_detail(language, geolocation_report.get("summary", {})),
        },
    ]


def build_report_cards(language: str, report_urls: Mapping[str, str]) -> list[dict]:
    """Describe each downloadable report so the list is understandable at a glance."""

    text = get_text(language)
    descriptions = {
        "automation_issues.json": text["report_automation_issues"],
        "unused_entities.json": text["report_unused_entities"],
        "template_performance.json": text["report_template_performance"],
        "integration_usage.json": text["report_integration_usage"],
        "geolocation_history.json": text["report_geolocation_history"],
        "automation_graph.json": text["report_automation_graph"],
        "suggestions.md": text["report_suggestions"],
        "run_summary.json": text["report_run_summary"],
    }
    return [
        {
            "name": name,
            "url": report_urls.get(name, "#"),
            "description": descriptions.get(name, ""),
        }
        for name in descriptions
    ]


def build_finding_cards(language: str, summary: dict, reports: dict) -> list[dict]:
    """Turn raw report summaries into a few human-readable highlight cards."""

    text = get_text(language)
    unused = reports.get("unused_entities", {})
    template = reports.get("template_performance", {})
    automation = reports.get("automation_issues", {})
    runtime = summary.get("runtime", {}) if isinstance(summary, dict) else {}

    missing_examples = [
        item.get("entity_id", "")
        for item in unused.get("missing_referenced_entities", [])[:4]
        if item.get("entity_id")
    ]
    template_examples = [
        _compact_template_example(item)
        for item in template.get("templates", [])
        if item.get("expensive")
    ][:3]
    automation_examples = [
        _compact_automation_example(item)
        for item in automation.get("automations", [])[:3]
    ]
    runtime_examples = [warning for warning in runtime.get("warnings", [])[:3] if warning]

    return [
        {
            "title": text["finding_missing_title"],
            "value": unused.get("summary", {}).get("missing_referenced_entities", 0),
            "description": text["finding_missing_description"],
            "examples": missing_examples,
        },
        {
            "title": text["finding_templates_title"],
            "value": template.get("summary", {}).get("expensive_templates", 0),
            "description": text["finding_templates_description"],
            "examples": template_examples,
        },
        {
            "title": text["finding_automation_title"],
            "value": automation.get("summary", {}).get("issues_found", 0),
            "description": text["finding_automation_description"],
            "examples": automation_examples,
        },
        {
            "title": text["finding_runtime_title"],
            "value": len(runtime.get("warnings", [])),
            "description": text["finding_runtime_description"],
            "examples": runtime_examples,
        },
    ]


def build_guidance_items(language: str, settings: Mapping[str, object]) -> list[str]:
    """Create short explanatory guidance sentences for the current configuration."""

    text = get_text(language)
    enabled = text["enabled_label"]
    disabled = text["disabled_label"]
    return [
        text["guidance_runtime"].format(
            value=enabled if settings.get("enable_runtime_analysis") else disabled
        ),
        text["guidance_geo"].format(
            value=enabled if settings.get("enable_geolocation_analysis") else disabled
        ),
        text["guidance_lookback"].format(value=settings.get("lookback_days", 7)),
        text["guidance_points"].format(value=settings.get("geolocation_point_limit", 300)),
        text["guidance_interval"].format(
            days=settings.get("lookback_days", 7),
            points=settings.get("geolocation_point_limit", 300),
        ),
        text["guidance_reports"],
    ]


def build_people_view(language: str, geolocation_report: dict) -> list[dict]:
    """Prepare localized people timeline cards without mutating the stored report."""

    people_view = []
    for person in geolocation_report.get("people", []):
        people_view.append(
            {
                **person,
                "kind_label": localize_kind(language, str(person.get("kind", "tracker"))),
                "current_state_label": localize_entity_state(language, str(person.get("current_state", "unknown"))),
                "visited_places_label": [
                    localize_entity_state(language, str(place))
                    for place in person.get("visited_places", [])
                ],
                "stays_view": [
                    {
                        **stay,
                        "place_label": localize_entity_state(language, str(stay.get("place", "unknown"))),
                    }
                    for stay in person.get("stays", [])
                ],
            }
        )
    return people_view


def localized_scan_mode(language: str, scan_mode: str) -> str:
    """Return a human-readable label for the current scan mode."""

    text = get_text(language)
    return {
        "quick": text["scan_mode_quick"],
        "full": text["scan_mode_full"],
        "deep": text["scan_mode_deep"],
    }.get(scan_mode, scan_mode)


def _compact_template_example(item: Mapping[str, object]) -> str:
    """Build one short template example for the dashboard highlight card."""

    context = str(item.get("context", "")).strip()
    source = str(item.get("source_file", "")).strip().split("/")[-1]
    if context and source:
        return f"{context} ({source})"
    return context or source


def _compact_automation_example(item: Mapping[str, object]) -> str:
    """Build one short automation example that includes the first detected issue title."""

    alias = str(item.get("alias", "")).strip()
    issues = item.get("issues", []) if isinstance(item.get("issues", []), list) else []
    first_issue = issues[0].get("title", "") if issues else ""
    if alias and first_issue:
        return f"{alias}: {first_issue}"
    return alias or first_issue


def localize_entity_state(language: str, state: str) -> str:
    """Translate a few common Home Assistant state values while leaving named places untouched."""

    if language == "de":
        return {
            "home": "Zuhause",
            "not_home": "Unterwegs",
            "unknown": "Unbekannt",
            "unavailable": "Nicht verfügbar",
        }.get(state, state)
    return state


def localize_kind(language: str, kind: str) -> str:
    """Translate the semantic route item kind for timeline cards."""

    text = get_text(language)
    return {
        "person": text["kind_person"],
        "vehicle": text["kind_vehicle"],
        "tracker": text["kind_tracker"],
    }.get(kind, kind)


def _tracked_entities_detail(language: str, summary: Mapping[str, object]) -> str:
    """Return a short breakdown of tracked entity kinds for the metric card."""

    if language == "de":
        return (
            f"Personen: {summary.get('people_tracked', 0)} | "
            f"Fahrzeuge: {summary.get('vehicle_trackers', 0)} | "
            f"Tracker: {summary.get('extra_trackers', 0)}"
        )
    return (
        f"People: {summary.get('people_tracked', 0)} | "
        f"Vehicles: {summary.get('vehicle_trackers', 0)} | "
        f"Trackers: {summary.get('extra_trackers', 0)}"
    )
