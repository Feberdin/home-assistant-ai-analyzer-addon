"""
Purpose:
Verify that the dashboard uses the correct TemplateResponse call signature for the installed FastAPI/Starlette stack.

Input/Output:
Input is a monkeypatched template renderer and a lightweight fake request object.
Output is an assertion that the request object is passed as the first positional argument.

Important invariants:
The dashboard must keep working even when template loading is cached internally by Jinja2.

How to debug:
If this test fails, inspect the TemplateResponse signature in the installed Starlette version before changing the route again.
"""

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

    fake_request = SimpleNamespace()
    response = await app_module.dashboard(fake_request)

    assert captured["request"] is fake_request
    assert captured["name"] == "dashboard.html"
    assert response["request"] is fake_request
