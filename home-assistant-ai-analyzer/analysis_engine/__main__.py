"""
Purpose:
Start the FastAPI ingress server inside the Home Assistant add-on container.

Input/Output:
Input is the add-on options file and the container environment.
Output is a running HTTP service on the configured ingress port.

Important invariants:
Logging must initialize before the server starts so startup failures are visible in add-on logs.

How to debug:
If the add-on starts but no web UI appears, inspect the uvicorn startup log line and the ingress port in config.yaml.
"""

from __future__ import annotations

import logging

import uvicorn

from .app import SETTINGS, app


def main() -> None:
    """Configure logging and launch the ingress web server."""

    logging.basicConfig(
        level=getattr(logging, SETTINGS.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger(__name__).info("Starting web service with settings: %s", SETTINGS.safe_dict())
    uvicorn.run(app, host="0.0.0.0", port=8099, log_level=SETTINGS.log_level)


if __name__ == "__main__":
    main()
