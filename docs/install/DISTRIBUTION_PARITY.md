# Distribution parity — SparkForge Azure

Install-2.0 §8.5 parity matrix for `sparkforge-azure` (dist `sparkforge-azure`,
Hatchling). Three columns: **Checkout** (`pip install -e .` / source tree),
**Wheel local** (wheel built from this branch, installed into a clean venv,
run outside the checkout), **PyPI publicado** (latest released wheel —
`0.1.6`, fetched with `pip download --no-deps sparkforge-azure==0.1.6`; it
predates this branch's packaging fixes).

Legend: ✅ works · ⚠️ works with documented degradation · ❌ broken ·
— not applicable.

| Surface | Checkout | Wheel local | PyPI publicado (0.1.6) |
|---|---|---|---|
| CLI (`sparkforge-azure …`) | ✅ | ✅ console script present in clean venv; `install apply`, `judge`, `knowledge select`, `doctor` all run from a consumer dir | ✅ same entry point |
| Skills | ✅ | ✅ `_data/skills` force-included; `install apply` materializes host skill mirrors (receipt `context-registry` PASS) | ✅ `_data/skills` present in published wheel |
| Agents | ✅ | ✅ `_data/agents` force-included; agent mirrors land under consumer `.claude`/`.agents`/`.devin` | ✅ `_data/agents` present |
| MCP | ✅ | ✅ `install doctor` `mcp-handshake` PASS — real stdio handshake against `sparkforge-azure mcp serve`, 18 tools enumerated | ⚠️ entry point exists; handshake not re-verified on published wheel |
| Knowledge | ✅ | ✅ `knowledge select --domain fabric` returns claims from `_data/knowledge` (fixed `_knowledge_roots` → `knowledge_dir()`, this branch) | ❌ `knowledge select` → `knowledge pack not found` — resolver only looked at checkout/cwd |
| Rules | ✅ | ✅ `judge --facts` evaluates the packaged `_data/rules/catalog` (findings/skipped non-empty) | ✅ `_data/rules/catalog` present |
| Protocols | ✅ | ⚠️ `install apply` writes `AGENT_PROTOCOL.md`; `forge/context/v1` + `forge/context-registry/v1` produced and schema-valid, capabilities populated from `_data` — **but** `_context_manifest` still reads `_REPO_DIR/forge.json` (= `site-packages/` under wheel), so `integrity.files` digests and agentic-sourced fields (`host_adapters` union, `requires_*` flags) stay empty until lf-0037's reader wiring lands; `_data/forge.json`/`forge.agentic.json` are now packaged so only the reader remains | ⚠️ same degradation, and the published wheel lacks the `_data/forge*.json` payloads entirely |
| Evals | ✅ | ✅ `_data/evals` force-included (dev-runtime corpus; consumer hosts do not execute it) | ✅ `_data/evals` present |
| Install | ✅ | ✅ `install apply --root <consumer> --yes` → `status: completed`; `managed.json` ledger written; `.mcp.json`, host mirrors, `.forge/context/` all present | ⚠️ applies, but capability manifest degraded (Protocols row) |
| Repair | ✅ | ✅ delete `.mcp.json` → `install repair` restores it | ⚠️ same path exists; not re-verified on published wheel |
| Uninstall | ✅ | ✅ `install uninstall` removes managed assets + `.forge/context` capability; `install apply` reinstalls cleanly | ⚠️ same path exists; not re-verified on published wheel |

## Documented degradations under the wheel

- **Context-manifest integrity fields** (lf-0037 wiring gap, tracked):
  `install/service.py::_context_manifest` reads `forge.json`/
  `forge.agentic.json` only via `_REPO_DIR` (the checkout parent). Under
  `pip install` that path is `site-packages/`, so `integrity.files` and
  agentic-derived fields stay empty even though this branch now ships the
  manifests at `sparkforge_azure/_data/forge*.json`. The packaging fix is
  in; the reader switch (`_REPO_DIR` → `_data` fallback, same pattern as
  `_group`) belongs to the install/service wiring owned by lf-0037 on
  `cycle/install-context` — recorded here per the ownership boundary.
- `doctor` checks **`surface`** and **`claims`** report `unresolved` under
  any wheel (local or PyPI): `doctor._surface`/`_claims` read
  `REPO/docs/{surface,claims}.lock.json` and import
  `scripts/check_surface_lock.py`, which are dev-gate artifacts that do not
  ship in the distribution. Shipping the JSON locks alone would not make the
  checks pass — the comparator script is not packaged either. These are
  checkout-only verifications; `unresolved` is the honest status.
- `install doctor` checks `dist:workspace` and `dist:host:*` may FAIL on a
  bare consumer target (no `workspace.yaml`, missing host binaries); that is
  environment state, not install corruption. Integrity checks
  (`dist:package_assets`, `dist:state_dir`, `dist:managed_assets`,
  `dist:mcp_runtime`, `mcp-handshake`) must be PASS.

## Deliberately not packaged

`parity.yaml` and `manifest.json` stay repo-root only: no runtime code path
reads them — `parity.yaml` is bound to `agentic/runtime.py`'s hard-coded
`_MEASURED_CAPABILITIES` by `tests/test_agentic_runtime.py::TestParityBinding`
(a dev gate), and `manifest.json` is a repo identity/spec artifact consumed
by docs and SDD tooling, not by installed runtime.

## Evidence

- Wheel isolation test: `tests/test_wheel_isolation.py`
  (`test_wheel_install_lifecycle_outside_checkout`) — builds the wheel,
  installs into a clean venv, runs the full lifecycle from a consumer dir
  outside the checkout. Passing locally.
- Wheel contents verified: `sparkforge_azure/_data/{forge.json,
  forge.agentic.json,skills,agents,rules/catalog,knowledge,evals,
  lab/scenarios}` + `sparkforge_azure/portal_assets` all present.
- Published `sparkforge_azure-0.1.6-py3-none-any.whl` (755 entries) inspected:
  `_data/knowledge`, `_data/rules/catalog`, `_data/skills`, `_data/agents`
  present; `_data/forge.json` and `_data/forge.agentic.json` **absent**.

## Planned (lf-0037)

Discovery verbs over `.forge/context/` (`rules.search`, `knowledge.search`,
`capabilities.list`, … via `discovery.ops` in `_forgecontext` v1.1.0) are in
flight on `cycle/install-context`. When merged, extend the wheel test to
exercise them and promote the corresponding cells.
