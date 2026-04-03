"""
Purpose:
Verify that one end-to-end scan writes the required report files for a small static-only configuration.

Input/Output:
Input is a temporary Home Assistant config tree and local add-on settings.
Output is the persisted report bundle in the configured output directory.

Important invariants:
The orchestrator must always write the required files, even when runtime analysis is disabled.

How to debug:
If a file is missing, inspect run_summary.json and the report writer before changing the test.
"""

from pathlib import Path

from analysis_engine.models import AppSettings
from analysis_engine.orchestrator import run_scan


def test_orchestrator_writes_required_reports(tmp_path: Path) -> None:
    (tmp_path / "configuration.yaml").write_text(
        """
default_config:
automation: !include automations.yaml
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "automations.yaml").write_text(
        """
- id: missing_sensor_check
  alias: Missing Sensor Check
  trigger:
    - platform: state
      entity_id: binary_sensor.fake_motion
      to: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: light.entryway
""".strip()
        + "\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "analysis"
    settings = AppSettings(
        base_config_path=str(tmp_path),
        output_path=str(output_dir),
        scan_mode="quick",
        enable_runtime_analysis=False,
        enable_ai=False,
        run_on_startup=False,
    )

    summary = run_scan(settings)

    assert summary["results"]["suggestions"] >= 1
    assert (output_dir / "automation_issues.json").exists()
    assert (output_dir / "unused_entities.json").exists()
    assert (output_dir / "template_performance.json").exists()
    assert (output_dir / "integration_usage.json").exists()
    assert (output_dir / "geolocation_history.json").exists()
    assert (output_dir / "automation_graph.json").exists()
    assert (output_dir / "suggestions.md").exists()
