# Security

## Security Position

This project is intended for analyzing Home Assistant installations. That makes security and privacy first-order concerns, not secondary concerns.

The architecture currently assumes the following baseline:

- access to the Home Assistant configuration must be read-only in v1
- generated suggestions must never silently modify live configuration
- AI usage must be optional
- secrets and credentials must be redacted before any external API call

## Sensitive Data Categories

The future implementation must treat the following as sensitive:

- `secrets.yaml` contents
- access tokens
- webhook identifiers
- API keys
- recorder database credentials
- local network topology details where unnecessary
- personally identifying device or location labels where avoidable

## Required Controls

- explicit redaction layer before AI requests
- allowlist-based payload building for LLM prompts
- structured validation for generated automation proposals
- audit trail for each scan run
- no auto-apply of generated changes in v1
- bounded runtime queries and configurable lookback windows

## Disclosure

If future implementation introduces a security concern, document it clearly in the repository and treat it as a release blocker for production use.
