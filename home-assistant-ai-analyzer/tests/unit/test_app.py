"""
Purpose:
Verify that the dashboard uses ingress-safe URLs and the correct TemplateResponse call signature for the installed FastAPI/Starlette stack.

Input/Output:
Input is a monkeypatched template renderer and lightweight fake request objects.
Output is an assertion that the request object is passed first and all action/report URLs are built from request.url_for.

Important invariants:
The dashboard must keep working even when template loading is cached internally by Jinja2, and it must not hard-code root-relative paths that break under Home Assistant ingress.

How to debug:
If this test fails, inspect the TemplateResponse signature and request.url_for handling in the installed Starlette version before changing the route again.
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

    class FakeRequest(SimpleNamespace):
        def url_for(self, name: str, **path_params):
            if name == "report":
                return f"/ingress-addon/api/report/{path_params['report_name']}"
            routes = {
                "trigger_scan": "/ingress-addon/scan",
                "status": "/ingress-addon/api/status",
                "chat": "/ingress-addon/api/chat",
            }
            return routes[name]

    fake_request = FakeRequest()
    response = await app_module.dashboard(fake_request)

    assert captured["request"] is fake_request
    assert captured["name"] == "dashboard.html"
    assert response["request"] is fake_request
    assert response["scan_url"] == "/ingress-addon/scan"
    assert response["status_url"] == "/ingress-addon/api/status"
    assert response["chat_url"] == "/ingress-addon/api/chat"
    assert response["report_urls"]["run_summary.json"] == "/ingress-addon/api/report/run_summary.json"


@pytest.mark.anyio
async def test_trigger_scan_redirects_back_to_ingress_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(app_module.SCAN_MANAGER, "start_scan", lambda: True)

    class FakeRequest(SimpleNamespace):
        def url_for(self, name: str, **path_params):
            assert name == "dashboard"
            return "/ingress-addon/"

    response = await app_module.trigger_scan(FakeRequest())

    assert response.status_code == 303
    assert response.headers["location"] == "/ingress-addon/"


@pytest.mark.anyio
async def test_chat_endpoint_returns_answer_payload(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "_load_report_bundle", lambda settings: {"run_summary": {"run_id": "test-run"}})
    monkeypatch.setattr(app_module, "answer_chat_question", lambda settings, question, reports: f"echo: {question}")

    response = await app_module.chat(app_module.ChatRequest(question="Bitte hilf mir"))

    assert response.status_code == 200
    assert json.loads(response.body) == {"answer": "echo: Bitte hilf mir"}
