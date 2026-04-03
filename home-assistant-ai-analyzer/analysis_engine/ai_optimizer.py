"""
Purpose:
Optionally ask an external LLM for improvement proposals based on the deterministic findings produced locally.

Input/Output:
Input is the add-on settings and the top findings from the local analyzers.
Output is a structured JSON response that stays optional and never blocks the core analysis pipeline.

Important invariants:
AI is opt-in only, prompt payloads must stay redacted, and model output must be treated as draft guidance.

How to debug:
If AI proposals do not appear, inspect the warnings and the outbound endpoint configuration before changing prompt content.
"""

from __future__ import annotations

import json
import logging

import httpx

from .models import AppSettings


LOGGER = logging.getLogger(__name__)


def maybe_generate_ai_proposals(
    settings: AppSettings,
    automation_issues: dict,
    unused_entities: dict,
    template_performance: dict,
    integration_usage: dict,
) -> dict:
    """Generate optional AI proposals when the operator enabled the feature."""

    if not settings.enable_ai:
        return {"enabled": False, "attempted": False, "proposals": [], "warnings": []}

    warnings: list[str] = []
    if not settings.llm_api_key:
        warnings.append("AI is enabled but no llm_api_key is configured.")
        return {"enabled": True, "attempted": False, "proposals": [], "warnings": warnings}

    prompt_payload = _build_prompt_payload(
        settings,
        automation_issues,
        unused_entities,
        template_performance,
        integration_usage,
    )

    try:
        response = httpx.post(
            settings.llm_base_url,
            timeout=httpx.Timeout(20.0, connect=10.0),
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
                            "You are a Home Assistant automation optimization assistant. "
                            "Return only valid JSON with a top-level 'proposals' array."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=True)},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        proposals = _parse_json_proposals(content)
        return {"enabled": True, "attempted": True, "proposals": proposals, "warnings": warnings}
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("AI proposal request failed: %s", err)
        warnings.append(f"AI request failed: {err}")
        return {"enabled": True, "attempted": True, "proposals": [], "warnings": warnings}


def _build_prompt_payload(
    settings: AppSettings,
    automation_issues: dict,
    unused_entities: dict,
    template_performance: dict,
    integration_usage: dict,
) -> dict:
    """Build a bounded and redacted payload for an OpenAI-compatible endpoint."""

    return {
        "goal": "Suggest safe Home Assistant automation improvements as draft proposals.",
        "constraints": [
            "Do not invent entities or services.",
            "Do not propose secrets or credentials.",
            "Keep proposals additive and explainable.",
            "Return concise YAML snippets only when useful.",
        ],
        "scan_mode": settings.scan_mode,
        "top_automation_issues": automation_issues.get("automations", [])[: settings.llm_max_findings],
        "missing_entities": unused_entities.get("missing_referenced_entities", [])[: settings.llm_max_findings],
        "expensive_templates": [
            item
            for item in template_performance.get("templates", [])
            if item.get("expensive")
        ][: settings.llm_max_findings],
        "integration_hints": integration_usage.get("possible_stale_integrations", [])[: settings.llm_max_findings],
    }


def _parse_json_proposals(content: str) -> list[dict]:
    """Extract a top-level proposals array from plain JSON or fenced JSON text."""

    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        normalized = normalized.replace("json\n", "", 1).strip()

    data = json.loads(normalized)
    proposals = data.get("proposals", [])
    return [proposal for proposal in proposals if isinstance(proposal, dict)]
