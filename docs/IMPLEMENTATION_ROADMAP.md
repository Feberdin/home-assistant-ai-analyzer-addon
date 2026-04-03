# Implementation Roadmap

## Why This Document Exists

The architecture is intentionally larger than the first implementation. This roadmap defines a low-risk path from concept to usable add-on.

## Phase 1: Repository And Core Models

Goal:

- create the real add-on repository scaffold
- define internal models and report schemas
- set up local development, linting, and tests

Deliverables:

- add-on metadata files
- Python project setup
- base models for findings, reports, and normalized installation data
- fixture-based test setup

## Phase 2: Static Config Analysis

Goal:

- parse Home Assistant YAML safely and reproducibly

Deliverables:

- include-aware parser
- automation and script normalization
- source mapping to files and lines
- baseline `automation_issues.json`

## Phase 3: Graph And Entity Analysis

Goal:

- make dependencies visible and detect obvious cleanup opportunities

Deliverables:

- automation graph builder
- missing-entity detection
- likely-unused entity heuristics
- graph export for UI

## Phase 4: Runtime Analysis

Goal:

- enrich static findings with runtime behavior

Deliverables:

- Home Assistant API client
- bounded history queries
- error log ingestion
- trigger and churn statistics

## Phase 5: Template And Integration Analysis

Goal:

- detect costly template patterns and integration inefficiencies

Deliverables:

- template cost scoring
- trigger pattern analyzer
- integration usage summaries

## Phase 6: Dashboard

Goal:

- make results visible without reading raw JSON

Deliverables:

- scan status page
- findings overview
- graph visualization
- report download links

## Phase 7: AI Proposal Engine

Goal:

- generate optional improvement drafts safely

Deliverables:

- provider adapter
- prompt builder with redaction
- structured output validation
- proposal review screen

## Testing Strategy

Every implementation phase should include:

- unit tests for core logic
- fixture-based tests with realistic Home Assistant examples
- negative tests for malformed config and missing entities
- regression tests for known false-positive patterns

## Recommended First Release Scope

The first useful release should stop before automatic writeback and focus on:

- deterministic analysis
- trustworthy reporting
- dashboard visibility
- clear operator guidance
