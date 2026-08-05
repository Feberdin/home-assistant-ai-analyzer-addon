# Purpose: Build a portable Home Assistant add-on image that runs the Python analysis service.
# Input/Output: Input is the add-on source tree; output is the runnable container image.
# Invariants: The working directory must match the copied package layout and /run.sh must stay executable.
# Debugging: If the add-on builds but will not start, verify the pip install step and the module entrypoint first.
ARG BUILD_FROM=ghcr.io/home-assistant/base:stable
FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}"

ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
  apk add --no-cache \
    python3 \
    py3-pip \
    curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /opt/home-assistant-ai-analyzer

COPY pyproject.toml README.md DOCS.md /opt/home-assistant-ai-analyzer/
COPY analysis_engine /opt/home-assistant-ai-analyzer/analysis_engine
COPY webui /opt/home-assistant-ai-analyzer/webui

RUN \
  python3 -m venv "${VIRTUAL_ENV}" && \
  "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir --upgrade pip setuptools wheel && \
  "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir .

COPY run.sh /run.sh
RUN chmod +x /run.sh \
  && chown -R appuser:appgroup /opt/home-assistant-ai-analyzer /run.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD ["curl", "--fail", "http://127.0.0.1:8099/api/health"]

CMD ["/run.sh"]
