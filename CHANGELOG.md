# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
## [0.1.3] - 2026-10-20

### Changed
- Cycle 12 portable distribution: `_data/evals` corpus + `group_dir()`
  shared resolver, `SPARKFORGE_AZURE_EVALS` override and env aliases;
  pyproject/env marker guards.

## [0.1.2] - 2026-10-18

### Changed
- Portal 2.2 vendored generation (44-asset frontend, telemetry,
  py3.10-safe server); hardened PyPI pipeline (build-once/
  publish-same-artifact, version gate, post-publish verify)

## [0.1.1] - 2026-10-18

### Fixed
- Portal vendored 2.1 final (Cycles 0-6)

## [Unreleased]

### Fixed

- `doc_manifest._check_links` now verifies `#fragment` anchors on
  tag-pinned repo URLs (they were silently dropped), exempts GitHub line
  refs (`#L10`, `#L10-L20`) and rejects `%5C` backslash escapes.

### Changed

- `pip install sparkforge-azure` line added to the README;
  links/images pinned to `v0.1.0` absolute URLs so the PyPI-rendered
  page resolves.

## [0.1.0] - 2026-10-15

### Added

- Forge Lab emitter producing `forge/BenchmarkResult/v1` receipts over the
  local lab/evaluation package (cyc9-05).
- GitHub experience files: CODE_OF_CONDUCT, SUPPORT, issue/PR templates
  (cyc10-02).

### Changed

- Vendored installkit/ui-kit/portal assets refreshed from canonical
  the-forge (cyc8-02, cyc9-10).
