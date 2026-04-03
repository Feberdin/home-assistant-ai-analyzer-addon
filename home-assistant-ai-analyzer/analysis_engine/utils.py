"""
Purpose:
Provide small helpers shared across modules for filesystem access, serialization, timestamps, and redaction.

Input/Output:
Inputs are paths, dictionaries, strings, and primitive values from the analysis pipeline.
Outputs are normalized paths, persisted files, safe string representations, and extracted identifiers.

Important invariants:
Helpers must stay deterministic, avoid mutating caller data, and never silently swallow critical write failures.

How to debug:
If outputs are missing or malformed, start by inspecting the helper functions that wrote the file or normalized the value.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from datetime import datetime, timezone


ENTITY_ID_PATTERN = re.compile(r"\b[a-z0-9_]+\.[a-z0-9_]+\b")
SERVICE_ID_PATTERN = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


def ensure_directory(path: str | Path) -> Path:
    """Create a directory tree if needed and return it as Path."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_relative_path(path: str | Path, base_dir: str | Path) -> str:
    """Return a stable relative path when possible, otherwise the absolute path."""

    try:
        return str(Path(path).resolve().relative_to(Path(base_dir).resolve()))
    except ValueError:
        return str(Path(path))


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def write_json(path: str | Path, payload: dict | list) -> None:
    """Persist JSON with predictable formatting for humans and machines."""

    target = Path(path)
    ensure_directory(target.parent)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")


def write_text(path: str | Path, content: str) -> None:
    """Persist UTF-8 text while creating parent directories as needed."""

    target = Path(path)
    ensure_directory(target.parent)
    target.write_text(content, encoding="utf-8")


def read_json(path: str | Path, default: dict | list | None = None):
    """Load JSON if present, otherwise return the provided default."""

    target = Path(path)
    if not target.exists():
        return {} if default is None else default
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def excerpt_text(value: str, limit: int = 220) -> str:
    """Create a short one-line excerpt useful for logs and reports."""

    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit - 3]}..."


def extract_entity_ids(text: str) -> list[str]:
    """Extract possible Home Assistant entity ids from free text."""

    return sorted(set(ENTITY_ID_PATTERN.findall(text)))


def extract_service_id(value: str) -> str | None:
    """Return a service id only when the full string looks like one."""

    candidate = value.strip()
    if SERVICE_ID_PATTERN.fullmatch(candidate):
        return candidate
    return None


def redact_value(value: str, keep: int = 4) -> str:
    """Mask a sensitive string while keeping a tiny suffix for debugging."""

    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * max(4, len(value) - keep)}{value[-keep:]}"
