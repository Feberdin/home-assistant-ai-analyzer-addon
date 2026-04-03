"""
Purpose:
Expose the Home Assistant ingress dashboard and API endpoints for manual scans and report access.

Input/Output:
Input is HTTP traffic from the add-on ingress UI and local scan state from the orchestrator.
Output is HTML, JSON, and generated report files.

Important invariants:
Only one scan should run at a time and the dashboard must stay useful even when no scan has happened yet.

How to debug:
If the UI behaves strangely, inspect the in-memory scan state and run_summary.json before changing the templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
import threading

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .models import AppSettings
from .orchestrator import run_scan
from .utils import read_json


LOGGER = logging.getLogger(__name__)


@dataclass
class ScanState:
    """Mutable scan state shared between the web routes and the background worker."""

    status: str = "idle"
    message: str = "No scan has been started yet."
    latest_summary: dict = field(default_factory=dict)
    active_run_id: str = ""


class ScanManager:
    """Own scan lifecycle so the web routes stay small and predictable."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.state = ScanState()
        self._lock = threading.Lock()
        self._load_previous_summary()

    def _load_previous_summary(self) -> None:
        """Load the most recent run summary if the add-on already scanned before."""

        summary_path = Path(self.settings.output_path) / "run_summary.json"
        if summary_path.exists():
            self.state.latest_summary = read_json(summary_path, default={})
            self.state.message = "Loaded the latest scan summary from disk."

    def start_scan(self) -> bool:
        """Start a background scan unless another scan is already running."""

        with self._lock:
            if self.state.status == "running":
                return False
            self.state.status = "running"
            self.state.message = "Scan is running."
            thread = threading.Thread(target=self._run_scan, daemon=True)
            thread.start()
            return True

    def _run_scan(self) -> None:
        """Run the orchestrator in a background thread and update shared state."""

        try:
            summary = run_scan(self.settings)
            with self._lock:
                self.state.status = "success"
                self.state.message = "Scan finished successfully."
                self.state.latest_summary = summary
                self.state.active_run_id = summary.get("run_id", "")
        except Exception as err:  # noqa: BLE001
            LOGGER.exception("Background scan failed")
            with self._lock:
                self.state.status = "error"
                self.state.message = f"Scan failed: {err}"


SETTINGS = AppSettings.from_options_file()
TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "webui" / "templates")
)
SCAN_MANAGER = ScanManager(SETTINGS)
APP = FastAPI(title="Home Assistant AI Analyzer")


@APP.on_event("startup")
async def startup_event() -> None:
    """Optionally kick off one scan after the app boots."""

    if SETTINGS.run_on_startup and not SCAN_MANAGER.state.latest_summary:
        SCAN_MANAGER.start_scan()


@APP.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the ingress dashboard with the latest status and report links."""

    summary = SCAN_MANAGER.state.latest_summary
    results = summary.get("results", {}) if isinstance(summary, dict) else {}
    geolocation_report = read_json(Path(SETTINGS.output_path) / "geolocation_history.json", default={})
    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "state": SCAN_MANAGER.state,
            "settings": SETTINGS.safe_dict(),
            "summary": summary,
            "results": results,
            "geolocation_report": geolocation_report,
            "report_names": [
                "automation_issues.json",
                "unused_entities.json",
                "template_performance.json",
                "integration_usage.json",
                "geolocation_history.json",
                "automation_graph.json",
                "suggestions.md",
                "run_summary.json",
            ],
        },
    )


@APP.post("/scan")
async def trigger_scan() -> RedirectResponse:
    """Start a new background scan and redirect back to the dashboard."""

    started = SCAN_MANAGER.start_scan()
    if not started:
        SCAN_MANAGER.state.message = "A scan is already running."
    return RedirectResponse(url="/", status_code=303)


@APP.get("/api/health")
async def health() -> JSONResponse:
    """Expose a watchdog-friendly health endpoint."""

    return JSONResponse({"status": "ok", "scan_status": SCAN_MANAGER.state.status})


@APP.get("/api/status")
async def status() -> JSONResponse:
    """Return the current scan state and latest summary."""

    return JSONResponse(
        {
            "status": SCAN_MANAGER.state.status,
            "message": SCAN_MANAGER.state.message,
            "latest_summary": SCAN_MANAGER.state.latest_summary,
        }
    )


@APP.get("/api/report/{report_name}")
async def report(report_name: str):
    """Serve one generated report either as JSON or plain text."""

    allowed = {
        "automation_issues.json",
        "unused_entities.json",
        "template_performance.json",
        "integration_usage.json",
        "geolocation_history.json",
        "automation_graph.json",
        "suggestions.md",
        "run_summary.json",
    }
    if report_name not in allowed:
        return JSONResponse({"error": "Unknown report name."}, status_code=404)

    report_path = Path(SETTINGS.output_path) / report_name
    if not report_path.exists():
        return JSONResponse({"error": "Report does not exist yet."}, status_code=404)

    if report_path.suffix == ".md":
        return PlainTextResponse(report_path.read_text(encoding="utf-8"))
    if report_path.suffix == ".json":
        return JSONResponse(read_json(report_path, default={}))
    return FileResponse(report_path)


app = APP
