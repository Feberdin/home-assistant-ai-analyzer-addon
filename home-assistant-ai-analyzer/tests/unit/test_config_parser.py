"""
Purpose:
Verify that YAML parsing finds automations, templates, and parse errors in a realistic Home Assistant-like config tree.

Input/Output:
Inputs are temporary YAML files written during the test.
Outputs are assertions about ConfigParseResult contents.

Important invariants:
The parser must keep going even when one file is malformed.

How to debug:
If this test fails, inspect the temporary files and parse_errors before changing parser heuristics.
"""

from pathlib import Path

from analysis_engine.config_parser import parse_configuration
from analysis_engine.models import AppSettings


def test_parse_configuration_collects_automations_templates_and_errors(tmp_path: Path) -> None:
    (tmp_path / "configuration.yaml").write_text(
        """
default_config:
automation: !include automations.yaml
template:
  - sensor:
      - name: "Outdoor Summary"
        state: "{{ states('sensor.outdoor_temp') }}"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "automations.yaml").write_text(
        """
- id: kitchen_motion_lights
  alias: Kitchen Motion Lights
  trigger:
    - platform: state
      entity_id: binary_sensor.kitchen_motion
      to: "on"
  action:
    - service: light.turn_on
      target:
        entity_id: light.kitchen
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "broken.yaml").write_text("automation: [\n", encoding="utf-8")

    settings = AppSettings(base_config_path=str(tmp_path), output_path=str(tmp_path / "analysis"))
    result = parse_configuration(settings)

    assert result.yaml_files_scanned == 3
    assert len(result.automations) == 1
    assert "binary_sensor.kitchen_motion" in result.referenced_entities
    assert "light.kitchen" in result.referenced_entities
    assert result.templates
    assert result.parse_errors

