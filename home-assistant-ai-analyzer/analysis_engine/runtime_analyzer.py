"""
Purpose:
Collect bounded runtime information from Home Assistant APIs and, optionally, the recorder database.

Input/Output:
Input is the add-on settings and the parsed configuration result.
Output is a RuntimeSnapshot containing current state, components, services, selected logbook data, and warnings.

Important invariants:
Runtime collection must fail safely, stay bounded, and never block the entire scan when one endpoint is unavailable.

How to debug:
If runtime analysis is empty, check SUPERVISOR_TOKEN, API reachability, and the warnings list before investigating parser logic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging
import os
import sqlite3
from urllib.parse import quote, urlencode

import httpx

from .models import AppSettings, ConfigParseResult, RuntimeSnapshot


LOGGER = logging.getLogger(__name__)


def collect_runtime(settings: AppSettings, _parse_result: ConfigParseResult) -> RuntimeSnapshot:
    """Collect runtime data through the Supervisor proxy when enabled."""

    snapshot = RuntimeSnapshot()
    if not settings.runtime_mode_enabled():
        snapshot.warnings.append("Runtime analysis is disabled by the current add-on settings.")
        return snapshot

    supervisor_token = os.getenv("SUPERVISOR_TOKEN", "").strip()
    if not supervisor_token:
        snapshot.warnings.append("SUPERVISOR_TOKEN is missing, so Home Assistant API access is unavailable.")
        _maybe_collect_recorder(settings, snapshot)
        return snapshot

    headers = {"Authorization": f"Bearer {supervisor_token}"}
    timeout = httpx.Timeout(10.0, connect=5.0)
    client = httpx.Client(timeout=timeout, headers=headers)

    try:
        snapshot.config = _get_json(client, f"{settings.ha_api_url}/config", snapshot.warnings) or {}
        snapshot.components = _get_json(client, f"{settings.ha_api_url}/components", snapshot.warnings) or []
        snapshot.services = _get_json(client, f"{settings.ha_api_url}/services", snapshot.warnings) or []
        state_list = _get_json(client, f"{settings.ha_api_url}/states", snapshot.warnings) or []
        snapshot.states = {
            item["entity_id"]: item
            for item in state_list
            if isinstance(item, dict) and "entity_id" in item
        }
        snapshot.error_log_excerpt = _get_text(
            client,
            f"{settings.ha_api_url}/error_log",
            snapshot.warnings,
        )[:4000]
        snapshot.logbook_entries = _get_logbook(client, settings, snapshot.warnings)
        snapshot.geolocation_entities = _collect_geolocation_entities(
            snapshot.states,
            settings.geolocation_entity_limit,
        )
        if settings.enable_geolocation_analysis and snapshot.geolocation_entities:
            snapshot.geolocation_history = _get_geolocation_history(
                client,
                settings,
                snapshot.geolocation_entities[: settings.geolocation_entity_limit],
                snapshot.warnings,
            )
        snapshot.available = True
    finally:
        client.close()

    _maybe_collect_recorder(settings, snapshot)
    return snapshot


def _get_json(client: httpx.Client, url: str, warnings: list[str]):
    """Perform one JSON request and collect a warning instead of throwing."""

    try:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Runtime JSON request failed for %s: %s", url, err)
        warnings.append(f"Runtime JSON request failed for {url}: {err}")
        return None


def _get_text(client: httpx.Client, url: str, warnings: list[str]) -> str:
    """Perform one text request and collect a warning instead of throwing."""

    try:
        response = client.get(url)
        response.raise_for_status()
        return response.text
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Runtime text request failed for %s: %s", url, err)
        warnings.append(f"Runtime text request failed for {url}: {err}")
        return ""


def _get_logbook(client: httpx.Client, settings: AppSettings, warnings: list[str]) -> list[dict]:
    """Fetch a bounded logbook slice to capture recent automation and error context."""

    start = datetime.now(timezone.utc) - timedelta(days=settings.lookback_days)
    start_text = quote(start.isoformat(), safe="")
    try:
        response = client.get(f"{settings.ha_api_url}/logbook/{start_text}")
        response.raise_for_status()
        entries = response.json()
        if isinstance(entries, list):
            return entries[:500]
        warnings.append("Logbook endpoint returned an unexpected payload shape.")
        return []
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Runtime logbook request failed: %s", err)
        warnings.append(f"Runtime logbook request failed: {err}")
        return []


def _maybe_collect_recorder(settings: AppSettings, snapshot: RuntimeSnapshot) -> None:
    """Inspect the recorder SQLite file in read-only mode when explicitly enabled."""

    if not settings.enable_recorder_db:
        return

    db_path = Path(settings.recorder_db_path)
    if not db_path.exists():
        snapshot.warnings.append(f"Recorder DB path does not exist: {db_path}")
        return

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
            cursor = connection.cursor()
            tables = [row[0] for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()]
            snapshot.recorder_details = {
                "path": str(db_path),
                "size_bytes": db_path.stat().st_size,
                "tables": tables[:25],
                "table_count": len(tables),
            }
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Recorder DB inspection failed: %s", err)
        snapshot.warnings.append(f"Recorder DB inspection failed: {err}")


def _collect_geolocation_entities(states: dict[str, dict], limit: int) -> list[dict]:
    """Pick person entities first and fall back to GPS-capable device trackers when needed."""

    people = []
    fallback_trackers = []

    for entity_id, state in sorted(states.items()):
        if entity_id.startswith("person."):
            people.append(_state_to_geolocation_candidate(entity_id, state))
            continue

        if entity_id.startswith("device_tracker.") and _state_has_coordinates(state):
            fallback_trackers.append(_state_to_geolocation_candidate(entity_id, state))

    candidates = people if people else fallback_trackers
    return [candidate for candidate in candidates[:limit] if candidate]


def _state_to_geolocation_candidate(entity_id: str, state: dict) -> dict:
    """Normalize one runtime state into a geolocation-capable entity record."""

    attributes = state.get("attributes", {})
    return {
        "entity_id": entity_id,
        "name": attributes.get("friendly_name", entity_id),
        "domain": entity_id.split(".", 1)[0],
        "state": state.get("state", "unknown"),
        "latitude": _safe_float(attributes.get("latitude")),
        "longitude": _safe_float(attributes.get("longitude")),
        "source_type": attributes.get("source_type", ""),
        "accuracy": attributes.get("gps_accuracy"),
        "last_changed": state.get("last_changed", ""),
    }


def _state_has_coordinates(state: dict) -> bool:
    """Return true when the runtime state includes a usable latitude and longitude pair."""

    attributes = state.get("attributes", {})
    return _safe_float(attributes.get("latitude")) is not None and _safe_float(attributes.get("longitude")) is not None


def _safe_float(value) -> float | None:
    """Convert coordinate-like values to float when possible."""

    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_geolocation_history(
    client: httpx.Client,
    settings: AppSettings,
    entities: list[dict],
    warnings: list[str],
) -> dict[str, list[dict]]:
    """Fetch bounded history for person or GPS-capable tracker entities."""

    if not entities:
        return {}

    start = datetime.now(timezone.utc) - timedelta(days=settings.lookback_days)
    start_text = quote(start.isoformat(), safe="")
    end_text = datetime.now(timezone.utc).isoformat()
    entity_ids = ",".join(item["entity_id"] for item in entities)
    params = urlencode(
        {
            "filter_entity_id": entity_ids,
            "end_time": end_text,
        },
        doseq=False,
    )
    params = f"{params}&significant_changes_only"

    url = f"{settings.ha_api_url}/history/period/{start_text}?{params}"
    payload = _get_json(client, url, warnings)
    if not isinstance(payload, list):
        warnings.append("Geolocation history endpoint returned an unexpected payload shape.")
        return {}

    history: dict[str, list[dict]] = {item["entity_id"]: [] for item in entities}
    for series in payload:
        if not isinstance(series, list):
            continue
        current_entity_id = None
        for event in series:
            if not isinstance(event, dict):
                continue
            current_entity_id = event.get("entity_id", current_entity_id)
            if not current_entity_id:
                continue
            history.setdefault(current_entity_id, []).append(event)
    return history
