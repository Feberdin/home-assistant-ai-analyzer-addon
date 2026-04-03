"""
Purpose:
Turn person and GPS-capable runtime history into a structured geolocation report that humans can inspect and the AI can optionally summarize.

Input/Output:
Input is the AppSettings and RuntimeSnapshot produced by the runtime collector.
Output is a JSON-friendly report with people, stays, timeline points, warnings, and a coordinate-based map model.

Important invariants:
Geolocation data is privacy-sensitive, so the report must stay local by default and AI context must be derived from a dedicated summary instead of raw coordinates.

How to debug:
If the map or timeline looks wrong, inspect the normalized geolocation_history entries before adjusting aggregation logic.
"""

from __future__ import annotations

from datetime import datetime
from itertools import groupby

from .models import AppSettings, RuntimeSnapshot


COLOR_PALETTE = [
    "#0f766e",
    "#b45309",
    "#7c3aed",
    "#be123c",
    "#2563eb",
    "#0f766e",
    "#475569",
    "#9333ea",
]


def analyze_geolocation(settings: AppSettings, runtime_snapshot: RuntimeSnapshot) -> dict:
    """Create a local geolocation report from runtime state and history data."""

    if not settings.enable_geolocation_analysis:
        return {
            "summary": {
                "enabled": False,
                "people_tracked": 0,
                "timeline_points": 0,
                "places_seen": 0,
            },
            "warnings": ["Geolocation analysis is disabled in the add-on settings."],
            "people": [],
            "map": {},
            "ai_summary": [],
        }

    warnings = list(runtime_snapshot.warnings)
    if not runtime_snapshot.available:
        warnings.append("Runtime analysis is unavailable, so no geolocation timeline could be collected.")
        return {
            "summary": {
                "enabled": True,
                "people_tracked": 0,
                "timeline_points": 0,
                "places_seen": 0,
            },
            "warnings": warnings,
            "people": [],
            "map": {},
            "ai_summary": [],
        }

    people = []
    total_points = 0
    all_places: set[str] = set()

    for index, candidate in enumerate(runtime_snapshot.geolocation_entities):
        entity_id = candidate["entity_id"]
        history_events = runtime_snapshot.geolocation_history.get(entity_id, [])
        person_report = _build_person_report(candidate, history_events, color=COLOR_PALETTE[index % len(COLOR_PALETTE)])
        people.append(person_report)
        total_points += len(person_report["timeline"])
        all_places.update(stay["place"] for stay in person_report["stays"] if stay["place"])

    return {
        "summary": {
            "enabled": True,
            "tracked_entities": len(people),
            "people_tracked": len([person for person in people if _person_kind(person) == "person"]),
            "vehicle_trackers": len([person for person in people if _person_kind(person) == "vehicle"]),
            "extra_trackers": len([person for person in people if _person_kind(person) == "tracker"]),
            "timeline_points": total_points,
            "places_seen": len(all_places),
            "lookback_days": settings.lookback_days,
            "point_limit": settings.geolocation_point_limit,
            "sampling_model": "significant_changes_only",
        },
        "warnings": warnings,
        "people": people,
        "map": _build_map_model(people, settings.geolocation_point_limit),
        "ai_summary": [_build_ai_summary(person) for person in people],
    }


def _build_person_report(candidate: dict, history_events: list[dict], color: str) -> dict:
    """Normalize one person's current state and historical state changes."""

    normalized_events = [_normalize_history_event(event) for event in history_events]
    normalized_events = [event for event in normalized_events if event.get("when")]
    normalized_events.sort(key=lambda item: item["when"])

    if not normalized_events:
        normalized_events = [_candidate_to_event(candidate)]

    stays = _build_stays(normalized_events)
    timeline = normalized_events[-300:]
    current = timeline[-1] if timeline else _candidate_to_event(candidate)
    current_lat = current.get("latitude")
    current_lon = current.get("longitude")

    return {
        "entity_id": candidate["entity_id"],
        "name": candidate["name"],
        "domain": candidate["domain"],
        "kind": _person_kind(candidate),
        "current_state": current.get("state", candidate.get("state", "unknown")),
        "current_latitude": current_lat,
        "current_longitude": current_lon,
        "current_when": current.get("when", candidate.get("last_changed", "")),
        "source_type": candidate.get("source_type", ""),
        "accuracy": candidate.get("accuracy"),
        "color": color,
        "timeline": timeline,
        "stays": stays,
        "route_distance_km": _calculate_route_distance_km(timeline),
        "route_point_count": len([point for point in timeline if point.get("latitude") is not None and point.get("longitude") is not None]),
        "visited_places": sorted({stay["place"] for stay in stays if stay["place"]}),
        "openstreetmap_url": _build_openstreetmap_url(current_lat, current_lon),
    }


def _candidate_to_event(candidate: dict) -> dict:
    """Build a timeline-compatible event from the current runtime state."""

    return {
        "when": candidate.get("last_changed", ""),
        "state": candidate.get("state", ""),
        "latitude": candidate.get("latitude"),
        "longitude": candidate.get("longitude"),
        "source_type": candidate.get("source_type", ""),
        "accuracy": candidate.get("accuracy"),
    }


def _normalize_history_event(event: dict) -> dict:
    """Reduce one raw history event to the fields we need for reporting and mapping."""

    attributes = event.get("attributes", {}) if isinstance(event, dict) else {}
    when = event.get("last_changed") or event.get("last_updated") or ""
    latitude = _to_float(attributes.get("latitude"))
    longitude = _to_float(attributes.get("longitude"))
    return {
        "when": when,
        "state": str(event.get("state", "")),
        "latitude": latitude,
        "longitude": longitude,
        "source_type": str(attributes.get("source_type", "")),
        "accuracy": attributes.get("gps_accuracy"),
    }


def _build_stays(events: list[dict]) -> list[dict]:
    """Aggregate consecutive timeline events into larger stays that are easier to read."""

    grouped_stays = []
    for _key, group in groupby(
        events,
        key=lambda item: (
            item.get("state", ""),
            _rounded_coord(item.get("latitude")),
            _rounded_coord(item.get("longitude")),
        ),
    ):
        items = list(group)
        first = items[0]
        last = items[-1]
        grouped_stays.append(
            {
                "place": first.get("state", ""),
                "start": first.get("when", ""),
                "end": last.get("when", ""),
                "duration_minutes": _duration_minutes(first.get("when", ""), last.get("when", "")),
                "latitude": first.get("latitude"),
                "longitude": first.get("longitude"),
                "points": len(items),
            }
        )

    # Extend each stay until the next detected state change so single history points
    # still produce a meaningful dwell time in the dashboard.
    for index, stay in enumerate(grouped_stays):
        if index + 1 < len(grouped_stays):
            stay["end"] = grouped_stays[index + 1]["start"]
        stay["duration_minutes"] = _duration_minutes(stay.get("start", ""), stay.get("end", ""))

    return grouped_stays[-80:]


def _duration_minutes(start_text: str, end_text: str) -> int | None:
    """Return the duration between two ISO timestamps in minutes when both are parseable."""

    try:
        start = datetime.fromisoformat(start_text)
        end = datetime.fromisoformat(end_text)
        return max(0, int((end - start).total_seconds() // 60))
    except ValueError:
        return None


def _calculate_route_distance_km(events: list[dict]) -> float:
    """Approximate route length from consecutive coordinate points using the Haversine formula."""

    route_points = [
        (point.get("latitude"), point.get("longitude"))
        for point in events
        if point.get("latitude") is not None and point.get("longitude") is not None
    ]
    if len(route_points) < 2:
        return 0.0

    distance = 0.0
    for index in range(1, len(route_points)):
        previous = route_points[index - 1]
        current = route_points[index]
        distance += _haversine_km(previous[0], previous[1], current[0], current[1])
    return round(distance, 2)


def _build_map_model(people: list[dict], point_limit: int) -> dict:
    """Project coordinates into a local SVG-friendly coordinate space."""

    coordinates = [
        (point["latitude"], point["longitude"])
        for person in people
        for point in person["timeline"][-point_limit:]
        if point.get("latitude") is not None and point.get("longitude") is not None
    ]
    if not coordinates:
        return {}

    latitudes = [item[0] for item in coordinates]
    longitudes = [item[1] for item in coordinates]
    min_lat = min(latitudes)
    max_lat = max(latitudes)
    min_lon = min(longitudes)
    max_lon = max(longitudes)

    if min_lat == max_lat:
        min_lat -= 0.01
        max_lat += 0.01
    if min_lon == max_lon:
        min_lon -= 0.01
        max_lon += 0.01

    width = 960
    height = 420
    padding = 36

    def project(latitude: float, longitude: float) -> tuple[float, float]:
        x = padding + ((longitude - min_lon) / (max_lon - min_lon)) * (width - 2 * padding)
        y = height - padding - ((latitude - min_lat) / (max_lat - min_lat)) * (height - 2 * padding)
        return round(x, 2), round(y, 2)

    map_people = []
    for person in people:
        projected_points = []
        geo_points = []
        for point in person["timeline"][-point_limit:]:
            latitude = point.get("latitude")
            longitude = point.get("longitude")
            if latitude is None or longitude is None:
                continue
            x, y = project(latitude, longitude)
            geo_points.append(
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "when": point.get("when", ""),
                    "state": point.get("state", ""),
                }
            )
            projected_points.append(
                {
                    "x": x,
                    "y": y,
                    "when": point.get("when", ""),
                    "state": point.get("state", ""),
                }
            )

        if not projected_points:
            continue

        map_people.append(
            {
                "name": person["name"],
                "entity_id": person["entity_id"],
                "color": person["color"],
                "polyline": " ".join(f"{point['x']},{point['y']}" for point in projected_points),
                "points": projected_points,
                "path": geo_points,
                "latest": projected_points[-1],
                "latest_coordinate": geo_points[-1],
            }
        )

    return {
        "width": width,
        "height": height,
        "center": {
            "latitude": round((min_lat + max_lat) / 2, 6),
            "longitude": round((min_lon + max_lon) / 2, 6),
        },
        "bounds": {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        },
        "people": map_people,
    }


def _build_ai_summary(person: dict) -> dict:
    """Return a privacy-conscious summary for optional AI context."""

    return {
        "entity_id": person["entity_id"],
        "name": person["name"],
        "kind": _person_kind(person),
        "current_state": person["current_state"],
        "current_when": person["current_when"],
        "route_distance_km": person.get("route_distance_km", 0.0),
        "visited_places": person["visited_places"][:20],
        "stays": [
            {
                "place": stay["place"],
                "start": stay["start"],
                "end": stay["end"],
                "duration_minutes": stay["duration_minutes"],
            }
            for stay in person["stays"][-30:]
        ],
    }


def _build_openstreetmap_url(latitude: float | None, longitude: float | None) -> str | None:
    """Create a direct OpenStreetMap link for the latest known position."""

    if latitude is None or longitude is None:
        return None
    return f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=15/{latitude}/{longitude}"


def _haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Return the great-circle distance in kilometers between two latitude/longitude points."""

    from math import asin, cos, radians, sin, sqrt

    lat_a_rad = radians(lat_a)
    lon_a_rad = radians(lon_a)
    lat_b_rad = radians(lat_b)
    lon_b_rad = radians(lon_b)

    delta_lat = lat_b_rad - lat_a_rad
    delta_lon = lon_b_rad - lon_a_rad
    haversine = sin(delta_lat / 2) ** 2 + cos(lat_a_rad) * cos(lat_b_rad) * sin(delta_lon / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(haversine))


def _person_kind(item: dict) -> str:
    """Return a stable route item kind even for older candidate shapes without the explicit kind field."""

    if item.get("kind") in {"person", "vehicle", "tracker"}:
        return str(item["kind"])
    if str(item.get("domain", "")) == "person" or str(item.get("entity_id", "")).startswith("person."):
        return "person"
    return "tracker"


def _to_float(value) -> float | None:
    """Convert a latitude or longitude value to float when possible."""

    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _rounded_coord(value: float | None) -> float | None:
    """Round coordinates for stay grouping so tiny GPS noise does not fragment the timeline."""

    if value is None:
        return None
    return round(value, 4)
