#!/usr/bin/with-contenv bashio
# Purpose: Start the add-on service with predictable logging and option visibility.
# Input/Output: Reads /data/options.json through Bashio and starts the Python web service.
# Invariants: The script must exit on errors and must not mutate the Home Assistant config directory.
# Debugging: Check add-on logs for the echoed settings and the Python process startup line.
set -euo pipefail

# Why this exists:
# We log the important startup values once so operators can quickly verify
# whether Home Assistant passed the expected configuration to the container.
CONFIG_PATH=/data/options.json

bashio::log.info "Starting Home Assistant AI Analyzer"
bashio::log.info "Config path: $(bashio::config 'base_config_path')"
bashio::log.info "Output path: $(bashio::config 'output_path')"
bashio::log.info "Scan mode: $(bashio::config 'scan_mode')"
bashio::log.info "Runtime analysis: $(bashio::config 'enable_runtime_analysis')"
bashio::log.info "AI enabled: $(bashio::config 'enable_ai')"

exec python3 -m analysis_engine
