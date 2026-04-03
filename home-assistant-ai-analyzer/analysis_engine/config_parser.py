"""
Purpose:
Scan the mounted Home Assistant configuration tree, parse YAML safely, and normalize automations, templates, entities, and integrations.

Input/Output:
Input is the mounted Home Assistant configuration directory from the add-on settings.
Output is a ConfigParseResult that later analyzers can consume without reparsing the filesystem.

Important invariants:
Parsing must stay read-only, tolerate Home Assistant custom YAML tags, and keep going when one file is malformed.

How to debug:
If entities or automations are missing from reports, inspect parse_errors and file_summaries before debugging later analyzers.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import logging

import yaml

from .models import AppSettings, AutomationRecord, ConfigParseResult, TemplateRecord
from .utils import excerpt_text, extract_entity_ids, extract_service_id, safe_relative_path


LOGGER = logging.getLogger(__name__)


class HomeAssistantLoader(yaml.SafeLoader):
    """PyYAML loader that ignores Home Assistant's custom tags without failing."""


def _construct_any_tag(loader: HomeAssistantLoader, _tag_suffix: str, node):
    """Why this exists: HA configs use tags like !include and !secret that SafeLoader does not understand."""

    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


HomeAssistantLoader.add_multi_constructor("!", _construct_any_tag)


TEMPLATE_KEYS = {
    "template",
    "value_template",
    "availability_template",
    "icon_template",
    "friendly_name_template",
}

ENTITY_COLLECTION_KEYS = {"entity_id", "entity_ids"}
SERVICE_KEYS = {"service", "action"}


def parse_configuration(settings: AppSettings) -> ConfigParseResult:
    """Parse YAML files below the mounted Home Assistant configuration tree."""

    result = ConfigParseResult(base_config_path=settings.base_config_path)
    base_dir = Path(settings.base_config_path)
    if not base_dir.exists():
        result.parse_errors.append(
            {
                "file": settings.base_config_path,
                "error": "Base configuration path does not exist inside the container.",
            }
        )
        return result

    yaml_files = _collect_yaml_files(base_dir, settings.exclude_paths)
    result.yaml_files_scanned = len(yaml_files)

    automation_keys_seen: set[tuple] = set()
    entity_counter: Counter[str] = Counter()
    service_counter: Counter[str] = Counter()
    configured_integrations: set[str] = set()

    for path in yaml_files:
        relative_path = safe_relative_path(path, base_dir)
        file_summary = {
            "file": relative_path,
            "documents": 0,
            "automations": 0,
            "templates": 0,
            "parse_error": False,
        }

        if "blueprints" in path.parts:
            result.blueprint_files.append(relative_path)
        if "packages" in path.parts:
            result.package_files.append(relative_path)

        try:
            documents = list(yaml.load_all(path.read_text(encoding="utf-8"), Loader=HomeAssistantLoader))
        except Exception as err:  # noqa: BLE001
            LOGGER.warning("Failed to parse %s: %s", relative_path, err)
            result.parse_errors.append({"file": relative_path, "error": str(err)})
            file_summary["parse_error"] = True
            result.file_summaries.append(file_summary)
            continue

        file_summary["documents"] = len(documents)
        for document in documents:
            if document is None:
                continue

            if path.name == "configuration.yaml" and isinstance(document, dict):
                configured_integrations.update(str(key) for key in document.keys())

            result.scripts_count += _count_scripts(document, path)

            templates = list(_collect_templates(document, relative_path))
            result.templates.extend(templates)
            file_summary["templates"] += len(templates)

            document_entity_counter, document_service_counter = _collect_references(document)
            entity_counter.update(document_entity_counter)
            service_counter.update(document_service_counter)

            automations = list(_extract_automations(document, relative_path))
            for automation in automations:
                dedupe_key = (
                    automation.source_file,
                    automation.automation_id,
                    automation.alias,
                    tuple(automation.trigger_entities),
                    tuple(automation.action_entities),
                    tuple(automation.service_calls),
                )
                if dedupe_key in automation_keys_seen:
                    continue
                automation_keys_seen.add(dedupe_key)
                result.automations.append(automation)
            file_summary["automations"] += len(automations)

        result.file_summaries.append(file_summary)

    result.configured_integrations = sorted(configured_integrations)
    result.referenced_entities = sorted(entity_counter.keys())
    result.entity_reference_counts = dict(sorted(entity_counter.items()))
    result.service_reference_counts = dict(sorted(service_counter.items()))
    result.blueprint_files = sorted(set(result.blueprint_files))
    result.package_files = sorted(set(result.package_files))
    return result


def _collect_yaml_files(base_dir: Path, exclude_paths: list[str]) -> list[Path]:
    """Collect YAML files while skipping known noisy folders like .storage."""

    excluded = {item.strip("/").lower() for item in exclude_paths}
    collected: list[Path] = []
    for path in base_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        relative_parts = {part.lower() for part in path.relative_to(base_dir).parts}
        if excluded.intersection(relative_parts):
            continue
        collected.append(path)
    return sorted(collected)


def _count_scripts(document, path: Path) -> int:
    """Count likely script definitions without needing full script normalization yet."""

    if path.name == "scripts.yaml" and isinstance(document, dict):
        return len(document)

    count = 0
    if isinstance(document, dict):
        scripts = document.get("script")
        if isinstance(scripts, dict):
            count += len(scripts)
        elif isinstance(scripts, list):
            count += len(scripts)
        for value in document.values():
            count += _count_scripts(value, path)
    elif isinstance(document, list):
        for item in document:
            count += _count_scripts(item, path)
    return count


def _collect_templates(document, source_file: str, context: str = "root"):
    """Yield TemplateRecord objects for Jinja-looking strings throughout the YAML tree."""

    if isinstance(document, dict):
        for key, value in document.items():
            next_context = f"{context}.{key}"
            if isinstance(value, str) and (key in TEMPLATE_KEYS or "{{" in value or "{%" in value):
                yield TemplateRecord(
                    source_file=source_file,
                    context=next_context,
                    template=value,
                    entity_refs=extract_entity_ids(value),
                )
            yield from _collect_templates(value, source_file, next_context)
    elif isinstance(document, list):
        for index, item in enumerate(document):
            yield from _collect_templates(item, source_file, f"{context}[{index}]")


def _collect_references(document) -> tuple[Counter[str], Counter[str]]:
    """Walk the YAML structure and collect entity and service references."""

    entity_counter: Counter[str] = Counter()
    service_counter: Counter[str] = Counter()

    def walk(node, current_key: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ENTITY_COLLECTION_KEYS:
                    for entity_id in _normalize_entity_values(value):
                        entity_counter[entity_id] += 1

                if key == "target" and isinstance(value, dict):
                    for entity_id in _normalize_entity_values(value.get("entity_id")):
                        entity_counter[entity_id] += 1

                if key in SERVICE_KEYS and isinstance(value, str):
                    service_id = extract_service_id(value)
                    if service_id:
                        service_counter[service_id] += 1

                if isinstance(value, str) and ("{{" in value or "{%" in value):
                    for entity_id in extract_entity_ids(value):
                        entity_counter[entity_id] += 1

                walk(value, key)
        elif isinstance(node, list):
            for item in node:
                walk(item, current_key)

    walk(document)
    return entity_counter, service_counter


def _normalize_entity_values(value) -> list[str]:
    """Normalize a scalar or list of entity ids into a clean string list."""

    if value is None:
        return []
    if isinstance(value, str):
        return [item for item in [value.strip()] if "." in item]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and "." in item]
    return []


def _extract_automations(document, source_file: str):
    """Recursively find automation-like mappings and convert them into normalized records."""

    seen_objects: set[int] = set()

    def walk(node, index_hint: int = 0):
        if id(node) in seen_objects:
            return
        seen_objects.add(id(node))

        if isinstance(node, dict):
            if _looks_like_automation(node):
                yield _build_automation_record(node, source_file, index_hint)

            nested_automations = node.get("automation")
            if isinstance(nested_automations, list):
                for nested_index, item in enumerate(nested_automations):
                    if isinstance(item, dict):
                        yield _build_automation_record(item, source_file, nested_index)

            for value in node.values():
                yield from walk(value, index_hint + 1)
        elif isinstance(node, list):
            for list_index, item in enumerate(node):
                yield from walk(item, list_index)

    yield from walk(document)


def _looks_like_automation(node: dict) -> bool:
    """Return true when a mapping looks enough like an automation to analyze."""

    has_trigger = "trigger" in node or "triggers" in node
    has_action = "action" in node or "actions" in node
    return has_trigger and has_action


def _build_automation_record(node: dict, source_file: str, index_hint: int) -> AutomationRecord:
    """Normalize one automation mapping into a smaller, report-friendly structure."""

    triggers = node.get("triggers", node.get("trigger", []))
    conditions = node.get("conditions", node.get("condition", []))
    actions = node.get("actions", node.get("action", []))
    templates = [record.template for record in _collect_templates(node, source_file, context="automation")]

    automation_id = str(node.get("id") or f"{Path(source_file).stem}_{index_hint}")
    alias = str(node.get("alias") or automation_id)

    return AutomationRecord(
        automation_id=automation_id,
        alias=alias,
        source_file=source_file,
        trigger_entities=sorted(_extract_section_entities(triggers)),
        condition_entities=sorted(_extract_section_entities(conditions)),
        action_entities=sorted(_extract_section_entities(actions)),
        service_calls=sorted(_extract_section_services(actions)),
        templates=templates,
        mode=str(node.get("mode", "")),
        raw_excerpt=excerpt_text(json.dumps(node, ensure_ascii=True, default=str)),
    )


def _extract_section_entities(section) -> set[str]:
    """Collect entity ids from one automation section."""

    entity_counter, _service_counter = _collect_references(section)
    return set(entity_counter.keys())


def _extract_section_services(section) -> set[str]:
    """Collect service ids from one automation action section."""

    _entity_counter, service_counter = _collect_references(section)
    return set(service_counter.keys())
