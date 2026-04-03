"""
Purpose:
Verify that geolocation runtime history is aggregated into per-person stays and a map model suitable for the dashboard.

Input/Output:
Input is a synthetic RuntimeSnapshot with one person entity and a short movement timeline.
Output is a structured geolocation report with summary counts, stays, projected map points, and privacy-safe AI summaries.

Important invariants:
AI summaries should omit raw coordinates even though the local report keeps them for the map.

How to debug:
If this test fails, inspect the timeline normalization and stay aggregation output before adjusting the map projection or dashboard renderer.
"""

from analysis_engine.geolocation_analyzer import analyze_geolocation
from analysis_engine.models import AppSettings, RuntimeSnapshot


def test_geolocation_analyzer_builds_people_stays_and_map() -> None:
    settings = AppSettings(
        enable_runtime_analysis=True,
        enable_geolocation_analysis=True,
        geolocation_point_limit=50,
    )
    snapshot = RuntimeSnapshot(
        available=True,
        geolocation_entities=[
            {
                "entity_id": "person.alice",
                "name": "Alice",
                "domain": "person",
                "state": "work",
                "latitude": 52.52,
                "longitude": 13.40,
                "source_type": "gps",
                "accuracy": 10,
                "last_changed": "2026-04-03T08:30:00+00:00",
            }
        ],
        geolocation_history={
            "person.alice": [
                {
                    "entity_id": "person.alice",
                    "state": "home",
                    "last_changed": "2026-04-03T06:00:00+00:00",
                    "attributes": {"latitude": 52.50, "longitude": 13.37, "source_type": "gps"},
                },
                {
                    "entity_id": "person.alice",
                    "state": "commute",
                    "last_changed": "2026-04-03T07:00:00+00:00",
                    "attributes": {"latitude": 52.51, "longitude": 13.38, "source_type": "gps"},
                },
                {
                    "entity_id": "person.alice",
                    "state": "work",
                    "last_changed": "2026-04-03T08:30:00+00:00",
                    "attributes": {"latitude": 52.52, "longitude": 13.40, "source_type": "gps"},
                },
            ]
        },
    )

    report = analyze_geolocation(settings, snapshot)

    assert report["summary"]["people_tracked"] == 1
    assert report["summary"]["timeline_points"] == 3
    assert report["people"][0]["name"] == "Alice"
    assert len(report["people"][0]["stays"]) == 3
    assert report["people"][0]["stays"][0]["duration_minutes"] == 60
    assert report["people"][0]["stays"][1]["duration_minutes"] == 90
    assert "home" in report["people"][0]["visited_places"]
    assert report["people"][0]["openstreetmap_url"]
    assert report["map"]["people"][0]["polyline"]
    assert report["map"]["people"][0]["path"][0]["latitude"] == 52.5
    assert report["map"]["center"]["latitude"] > 52.50
    assert "latitude" not in report["ai_summary"][0]["stays"][0]
