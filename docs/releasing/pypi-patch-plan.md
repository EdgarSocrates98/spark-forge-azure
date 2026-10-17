# PyPI patch plan — sparkforge-azure

Cycle 11.2 (P1-004 + P1-006). Prepared for maintainer approval; nothing here
publishes, tags or uploads anything.

## Current state (audited in cycle 11.2)

| Signal | Value |
|---|---|
| PyPI published | `sparkforge-azure 0.1.0` (only release) |
| `pyproject.toml` | `0.1.0` — aligned |
| Git tag / GitHub release | `v0.1.0` — aligned |
| `requires-python` | `>=3.10` |
| CI `full` matrix before this PR | `["3.10","3.12","3.14"]` × {ubuntu, windows} — missing 3.11, 3.13 |
| Classifiers | already claim 3.10–3.14 |

**No version drift**: PyPI = pyproject = tag = GitHub release.

## What changes in this PR

1. **CI matrix** (`ci.yml`, `full` job): python axis now
   `["3.10","3.11","3.12","3.13","3.14"]` on both OS legs. The
   `claims` and `verify_wheel` steps remain gated to `ubuntu-latest` +
   `3.12`, exactly as designed (claims.lock is env-stamped).
2. **project.urls**: added `Documentation` (docs/README.md) and `Changelog`
   (CHANGELOG.md) — both exist on `main`; PyPI 0.1.0 lacks them.

Classifiers were already correct (3.10–3.14 declared).

## Proposed next release: `0.1.1` (patch)

Rationale: metadata URL additions + CI coverage. No runtime/dependency/rule
change.

### Provenance checklist for the maintainer

- [ ] CI green on this PR, including the new `full` legs (3.11, 3.13 on
      ubuntu + windows).
- [ ] `uv run ruff check sparkforge_azure tests scripts` and
      `uv run pytest -q -m "not live_azure"` locally on at least one version.
- [ ] Bump `version = "0.1.1"` in `pyproject.toml` at release time.
- [ ] Tag `v0.1.1` after merge; publish via `publish-pypi.yml`.
- [ ] Verify PyPI page shows the new project URLs.

## Local smoke evidence (this PR)

- Interpreters: system `python3.12` (3.12.3); uv-managed 3.10.21, 3.11.16,
  3.13.15, 3.14.7.
- `uv pip install -e ".[dev]"` resolves on the previously untested 3.11 and
  3.13; `sparkforge-azure --help` smoke OK.
- `python -m build` produces the wheel on a uv-managed interpreter.

## Blockers

None. All five versions within `requires-python` install and smoke clean.
