# Purpose: Build a portable Home Assistant add-on image that runs the Python analysis service.
# Input/Output: Input is the add-on source tree; output is the runnable container image.
# Invariants: The working directory must match the copied package layout and /run.sh must stay executable.
# Debugging: If the add-on builds but will not start, verify the pip install step and the module entrypoint first.
ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
  io.hass.type="addon" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}"

ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
  apk add --no-cache \
    python3 \
    py3-pip

WORKDIR /opt/home-assistant-ai-analyzer

COPY pyproject.toml README.md DOCS.md /opt/home-assistant-ai-analyzer/
COPY analysis_engine /opt/home-assistant-ai-analyzer/analysis_engine
COPY webui /opt/home-assistant-ai-analyzer/webui

RUN pip3 install --no-cache-dir .

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
