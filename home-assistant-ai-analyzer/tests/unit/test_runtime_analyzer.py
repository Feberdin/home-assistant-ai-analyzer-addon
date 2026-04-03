"""
Purpose:
Verify that geolocation candidate collection keeps people, excludes linked phone trackers, and adds unlinked vehicle trackers such as Tesla.

Input/Output:
Input is a synthetic Home Assistant state registry with one person, one linked phone tracker, and one Tesla tracker.
Output is an ordered geolocation candidate list ready for history collection.

Important invariants:
The analyzer should not duplicate the same person via their linked phone tracker, but it should still surface an additional vehicle route when available.

How to debug:
If this test fails, inspect runtime candidate classification before changing dashboard logic or geolocation aggregation.
"""

from analysis_engine.runtime_analyzer import _collect_geolocation_entities


def test_collect_geolocation_entities_keeps_people_and_unlinked_tesla_tracker() -> None:
    states = {
        "person.joachim": {
            "state": "home",
            "attributes": {
                "friendly_name": "Joachim",
                "source": "device_tracker.joachim_phone",
                "latitude": 52.52,
                "longitude": 13.40,
            },
            "last_changed": "2026-04-03T10:00:00+00:00",
        },
        "device_tracker.joachim_phone": {
            "state": "home",
            "attributes": {
                "friendly_name": "Joachim Phone",
                "latitude": 52.52,
                "longitude": 13.40,
            },
            "last_changed": "2026-04-03T10:00:00+00:00",
        },
        "device_tracker.tesla_model_y": {
            "state": "parked",
            "attributes": {
                "friendly_name": "Tesla Model Y",
                "manufacturer": "Tesla",
                "model": "Model Y",
                "latitude": 52.53,
                "longitude": 13.42,
            },
            "last_changed": "2026-04-03T10:05:00+00:00",
        },
    }

    candidates = _collect_geolocation_entities(states, limit=10)

    assert [item["entity_id"] for item in candidates] == [
        "person.joachim",
        "device_tracker.tesla_model_y",
    ]
    assert candidates[0]["kind"] == "person"
    assert candidates[1]["kind"] == "vehicle"
