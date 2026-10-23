# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
## [0.2.3] - 2026-10-23

### Security

- Vendored `_installkit` 1.0.4: unsafe ledger keys surfaced in
  `status().drift.unsafe`; `doctor` marks them non-repairable.

## [0.2.2] - 2026-10-23

### Fixed

- `_forgecontext` v1.3.3 + `_installkit` v1.0.3 (vendored): `repair_context`
  reports malformed capability files per-file instead of crashing;
  context/install locks carry a unique ownership token; poisoned journals
  quarantine instead of wedging later ops; asset/ledger paths are
  validated before disk writes (`FORGE-INSTALL-UNSAFE-PATH`);
  `_atomic_write` preserves file modes.
- `install`: `knowledge/<rel>` references extracted from SKILL.md docs
  now discard traversal refs (`..`, absolute, drive, backslash) at
  extraction AND at the stub-write layer — no file can be created or
  recorded outside the install root via a crafted doc mention.
- A `BLOCKED` check on the mandatory context-registry component now marks
  the receipt `failed` (nonzero exit) — on install AND on both uninstall
  paths.

## [0.2.1] - 2026-10-22

### Fixed

- `_forgecontext` v1.3.2: non-UTF-8 consumer docs (AGENTS.md / CLAUDE.md /
  AGENT_PROTOCOL.md) now refuse with named `FORGE-CONTEXT-CONFLICT` on
  install and uninstall — never a bare `UnicodeDecodeError` mid-write.
- `evals result --run`: run names are validated against a safe pattern
  and resolved under the runs root — `../../` and absolute paths can no
  longer escape the agentic-evals directory (§13.1).

## [0.2.0] - 2026-10-22

### Added

- Install 2.0: `forge-context/v1` registry integration, transactional
  install/uninstall via vendored `_forgecontext` v1.3.1, consumer-doc managed
  blocks, evals classification, `qualified_ids` + `route()` support.

### Fixed

- `_txn_restore` journal path validation; interrupt-safe rollback;
  stale-lock `created_at` fallback (Windows); vendored `_installkit` v1.0.2 +
  `forge_bootstrap` v1.1.1 security backports (userinfo redaction, argv trim,
  empty-stdout smoke).

## [0.1.5] - 2026-10-21

### Changed

- Cycle 13 (graph): Graph Studio vendored update — P0 physics fix (NaN blow-up on hubs/star), scalable visualization modes (overview/explore/full), navigation, inspectors and bounded analysis; post-lf-0023 portal explorer assets re-vendored; security/accessibility/reliability hardening.

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



## [0.3.0] - 2026-10-23

### Fixed

- `ui._has_vcs_root`/`_cli_argv`: stray `forge.json` ancestor bound as in
  siblings. Regression tests added.

## [0.1.6] - 2026-10-21

### Added

- Integrations cycle: governed peer delegation (parity with spark-forge-aws) to data-sentinel-forge and forge-doctor-data; `sparkforge-azure-delegate-specialists` skill; delegation CLI verbs; Windows `.cmd` fixture shim; Python 3.10 `timezone.utc` compat fix; portal bundle re-vendored with explorer pages.

## [0.1.4] - 2026-10-20

### Changed
- Cycle 12.1: vendored `scripts/forge_bootstrap.py` re-stamped to the canonical ruff-formatted source; `install.windows.sh` added as the Git Bash/MSYS install route; CI gains a `bash -n` gate for it; CURRENT_STATE regenerated.

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
