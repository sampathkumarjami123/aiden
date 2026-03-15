# Changelog

All notable changes to this project are documented in this file.

The format is inspired by Keep a Changelog and this project follows semantic versioning for tags.

## [v1.0.1] - 2026-03-15

### Added
- Streaming chat endpoint and UI flow hardened with:
  - stop/cancel control for in-progress streams
  - one-time retry on transient stream interruptions
  - fallback to non-stream chat when streaming fails
  - structured stream events (`chunk`, `final`, `error`)
- Stream timeout guard controlled by `AIDEN_STREAM_MAX_SECONDS`.
- Desktop task filtering (`all`, `pending`, `done`).
- Expanded test coverage across core and web layers, including stream guardrails and concurrency behavior.

### Changed
- Core engine data paths use instance-scoped storage for improved isolation and test reliability.
- Web API wraps mutable engine operations with synchronization for thread-safe request handling.
- Web UI stream parser handling improved for malformed or partial NDJSON lines.

### Fixed
- Bookmark interaction selector mismatch in web UI.
- Memory-context prompt injection accumulation during chat turns.
- Task edit command usage text in help output.

## [v1.0.0] - 2026-03-15

### Added
- Baseline production-ready assistant experience across CLI, desktop, web, and voice interfaces.
- Multi-profile preferences, tasks, and memory notes support.
- Local fallback responses for development mode when API key is absent.
- Setup, test, health-check, quality-gate, and release automation scripts.
