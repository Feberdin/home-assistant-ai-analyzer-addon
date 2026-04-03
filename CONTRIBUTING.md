# Contributing

## Goal

This repository currently focuses on architecture, design decisions, and implementation planning for the `Home Assistant AI Analyzer` add-on.

Contributions should make the project easier to understand, safer to implement, and easier to operate.

## How To Contribute

1. Start with the architecture document in [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
2. Keep changes small and easy to review
3. Explain the reason for each architectural or operational decision
4. Prefer improving clarity over adding complexity

## Contribution Priorities

Work should follow this order:

1. Correctness
2. Readability
3. Robustness
4. Testability
5. Operator experience
6. Performance

## Documentation Style

- Write for mixed audiences: developers, operators, and advanced Home Assistant users
- Prefer concrete wording over abstract claims
- Document assumptions and risks explicitly
- Avoid "magic" decisions without rationale

## Planned Code Style

When implementation begins:

- Python should follow PEP 8
- modules should stay small and focused
- error handling must be explicit
- logging must help operators reproduce problems
- tests must cover happy path and important edge cases

## Review Checklist

Before opening a change:

- Does the change improve clarity?
- Are assumptions written down?
- Are risks or trade-offs visible?
- Would a non-programmer still understand the high-level intent?
- Does the change preserve the read-only and safety-first direction of v1?
