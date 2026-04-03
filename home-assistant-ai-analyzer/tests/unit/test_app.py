"""
Purpose:
Verify that the dashboard uses ingress-safe URLs and the correct TemplateResponse call signature for the installed FastAPI/Starlette stack.

Input/Output:
Input is a monkeypatched template renderer and lightweight fake request objects.
Output is an assertion that the request object is passed first, ingress URLs respect root_path, and localized text can switch to German.

Important invariants:
The dashboard must keep working even when template loading is cached internally by Jinja2, and it must not hard-code root-relative paths that break under Home Assistant ingress.

How to debug:
If this test fails, inspect the TemplateResponse signature, root_path handling, and localization inputs before changing the route again.
"""

import json
from types import SimpleNamespace

import pytest

from analysis_engine import app as app_module


@pytest.mark.anyio
async def test_dashboard_passes_request_first_to_template_response(monkeypatch) -> None:
    captured: dict = {}

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return context

    monkeypatch.setattr(app_module.TEMPLATES, "TemplateResponse", fake_template_response)

    fake_request = SimpleNamespace(
        headers={"accept-language": "de-DE,de;q=0.9,en;q=0.8"},
        scope={"root_path": "/ingress-addon"},
    )
    response = await app_module.dashboard(fake_request)

    assert captured["request"] is fake_request
    assert captured["name"] == "dashboard.html"
    assert response["request"] is fake_request
    assert response["language"] == "de"
    assert response["ui"]["run_scan_label"] == "Scan starten"
    assert response["scan_url"] == "/ingress-addon/scan"
    assert response["status_url"] == "/ingress-addon/api/status"
    assert response["chat_url"] == "/ingress-addon/api/chat"
    assert response["report_urls"]["run_summary.json"] == "/ingress-addon/api/report/run_summary.json"


@pytest.mark.anyio
async def test_trigger_scan_redirects_back_to_ingress_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(app_module.SCAN_MANAGER, "start_scan", lambda: True)

    response = await app_module.trigger_scan(SimpleNamespace(scope={"root_path": "/ingress-addon"}))

    assert response.status_code == 303
    assert response.headers["location"] == "/ingress-addon/"


@pytest.mark.anyio
async def test_chat_endpoint_returns_answer_payload(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "_load_report_bundle", lambda settings: {"run_summary": {"run_id": "test-run"}})
    monkeypatch.setattr(
        app_module,
        "answer_chat_question",
        lambda settings, question, reports, language: f"{language}: {question}",
    )

    response = await app_module.chat(
        SimpleNamespace(headers={"accept-language": "de-DE,de;q=0.9"}),
        app_module.ChatRequest(question="Bitte hilf mir"),
    )

    assert response.status_code == 200
    assert json.loads(response.body) == {"answer": "de: Bitte hilf mir"}
