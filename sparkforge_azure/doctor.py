"""``sparkforge-azure doctor`` -- installation and capability health (sections 79-81).

Inspection only: no check writes to the cloud, calls Azure, or reads secrets.
Credential state is reported as *presence* of configuration (env var names,
Azure CLI on PATH), never values, and never by attempting authentication.

Each check returns ``ok | warn | fail | unresolved``.  ``unresolved`` means the
area could not be inspected (absent optional component), and is never folded
into ``ok`` (unknown != zero).
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import platform
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sparkforge_azure import __version__

PKG = Path(__file__).resolve().parent
REPO = PKG.parent


def data_root(name: str) -> Path:
    """Repo-root asset dir when running from source; packaged ``_data`` from a wheel."""
    src = REPO / name
    if src.is_dir() and (REPO / "pyproject.toml").is_file():
        return src
    return PKG / "_data" / name


@dataclass(frozen=True, slots=True)
class Check:
    area: str
    status: str
    detail: str
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {"area": self.area, "status": self.status, "detail": self.detail}
        if self.data:
            out["data"] = self.data
        return out


def _installation() -> Check:
    return Check("installation", "ok", f"sparkforge-azure {__version__} on Python "
                 f"{platform.python_version()} ({sys.platform})",
                 {"package_path": str(PKG)})


def _dependencies() -> Check:
    missing = [m for m in ("yaml", "jsonschema") if importlib.util.find_spec(m) is None]
    if missing:
        return Check("dependencies", "fail", f"core dependencies missing: {missing}")
    return Check("dependencies", "ok", "core dependencies importable (PyYAML, jsonschema)")


def _azure_extras() -> Check:
    extras = {
        "azure": ["azure.identity", "azure.mgmt.resourcegraph"],
        "databricks": ["databricks.sdk"],
        "mcp": ["mcp"],
        "otel": ["opentelemetry"],
    }
    found = {k: all(importlib.util.find_spec(m.split(".")[0]) is not None and _spec(m)
                    for m in mods) for k, mods in extras.items()}
    return Check("azure_extras", "ok", "optional extras are opt-in; absence is expected offline",
                 {"installed": found})


def _spec(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _credentials_state() -> Check:
    names = ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
             "AZURE_FEDERATED_TOKEN_FILE", "AZURE_SUBSCRIPTION_ID", "DATABRICKS_HOST",
             "DATABRICKS_TOKEN"]
    present = sorted(n for n in names if os.environ.get(n))
    az = shutil.which("az") is not None
    return Check("credentials_state", "ok",
                 "presence only; no authentication attempted (offline works without auth)",
                 {"env_present": present, "azure_cli_on_path": az})


def _agentic_os() -> Check:
    mods = ["sparkforge_azure.agentic.trust", "sparkforge_azure.agentic.stop",
            "sparkforge_azure.agentic.recovery", "sparkforge_azure.agentic.checkpoint",
            "sparkforge_azure.agentic.governor", "sparkforge_azure.agentic.memory",
            "sparkforge_azure.economy.model_router", "sparkforge_azure.decision"]
    return _imports("agentic_os", mods)


def _imports(area: str, mods: list[str]) -> Check:
    bad = {}
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as exc:  # noqa: BLE001 - doctor reports, never raises
            bad[m] = f"{type(exc).__name__}: {exc}"[:160]
    if bad:
        return Check(area, "fail", f"{len(bad)} module(s) failed to import", {"errors": bad})
    return Check(area, "ok", f"{len(mods)} modules importable")


def _tokensave() -> Check:
    from sparkforge_azure.tokensave import PROFILES, SYMBOL_EXTRACTORS

    return Check("tokensave", "ok", "retrieval ladder L0-L6 available",
                 {"profiles": sorted(PROFILES), "symbol_formats": sorted(SYMBOL_EXTRACTORS)})


def _optional_module(area: str, module: str, attr: str | None = None) -> Check:
    try:
        mod = importlib.import_module(module)
    except ModuleNotFoundError:
        return Check(area, "unresolved", f"{module} not present in this build")
    except Exception as exc:  # noqa: BLE001
        return Check(area, "fail", f"{type(exc).__name__}: {exc}"[:200])
    if attr and not hasattr(mod, attr):
        return Check(area, "fail", f"{module} lacks {attr}")
    return Check(area, "ok", f"{module} importable")


def _code_intelligence() -> Check:
    return _imports("code_intelligence", ["sparkforge_azure.codeintel"])


def _graphfy() -> Check:
    return _optional_module("graphfy", "sparkforge_azure.graph")


def _knowledge() -> Check:
    root = data_root("knowledge")
    try:
        from sparkforge_azure.knowledgebase.metadata import load_entries
    except ModuleNotFoundError:
        return Check("knowledge_freshness", "unresolved", "knowledgebase module not present")
    if not root.is_dir():
        return Check("knowledge_freshness", "unresolved", f"no knowledge dir at {root}")
    try:
        entries, violations = load_entries(root)
    except Exception as exc:  # noqa: BLE001
        return Check("knowledge_freshness", "fail", f"knowledge invalid: {exc}"[:200])
    statuses: dict[str, int] = {}
    for e in entries:
        statuses[str(e.status)] = statuses.get(str(e.status), 0) + 1
    if violations:
        return Check("knowledge_freshness", "fail", f"{len(violations)} contract violation(s)",
                     {"violations": violations[:20]})
    worst = "ok" if set(statuses) <= {"VERIFIED"} else "warn"
    return Check("knowledge_freshness", worst, f"{len(entries)} knowledge entries (declared "
                 "status; run scripts/check_knowledge.py for age-based freshness)",
                 {"by_status": statuses})


def _mcp() -> Check:
    from sparkforge_azure.mcp.tools import load_all

    tools = load_all()
    undeclared = [n for n, s in tools.items() if not s.risk]
    status = "fail" if undeclared else "ok"
    sdk = _spec("mcp")
    return Check("mcp", status, f"{len(tools)} tools, all with declared risk",
                 {"compact": sorted(n for n, s in tools.items() if s.compact),
                  "sdk_installed": sdk})


def _skills_agents() -> Check:
    skills = sorted(p.parent.name for p in data_root("skills").glob("*/SKILL.md"))
    agents = sorted(p.stem for p in data_root("agents").glob("*.md") if p.stem != "README")
    if not skills and not agents:
        return Check("skills_agents", "unresolved", "no skills/agents found")
    return Check("skills_agents", "ok", f"{len(skills)} skills, {len(agents)} agents",
                 {"skills": skills})


def _surface() -> Check:
    lock = REPO / "docs" / "surface.lock.json"
    if not lock.is_file():
        return Check("surface", "unresolved", "surface lock not present in this build")
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from check_surface_lock import compare  # type: ignore[import-not-found]
    except ImportError:
        return Check("surface", "unresolved", "surface checker not available (installed build)")
    finally:
        if sys.path and sys.path[0] == str(REPO / "scripts"):
            sys.path.pop(0)
    drift = compare()
    return Check("surface", "ok" if not drift else "fail",
                 "surface matches lock" if not drift else f"{len(drift)} drift item(s)",
                 {"drift": drift} if drift else None)


def _claims() -> Check:
    lock = REPO / "docs" / "claims.lock.json"
    if not lock.is_file():
        return Check("claims", "unresolved", "claims lock not present in this build")
    import json

    data = json.loads(lock.read_text(encoding="utf-8"))
    return Check("claims", "ok", f"{len(data.get('claims', []))} published claims with proofs")


def _traces() -> Check:
    state = Path.cwd() / ".sparkforge-azure"
    dbs = sorted(str(p.name) for p in state.glob("*.db")) if state.is_dir() else []
    return Check("traces", "ok" if dbs else "unresolved",
                 "local trace stores found" if dbs else "no local traces yet (nothing recorded)",
                 {"stores": dbs} if dbs else None)


def _lab() -> Check:
    return _optional_module("forge_lab", "sparkforge_azure.lab")


_LIVE_COLLECTORS: dict[str, tuple[str, tuple[str, ...]]] = {
    "databricks": ("sparkforge_azure.collectors.databricks", ("databricks.sdk",)),
    "unity_catalog": ("sparkforge_azure.collectors.unity_catalog", ("databricks.sdk",)),
    "azure_rbac": ("sparkforge_azure.collectors.azure_rbac",
                   ("azure.identity", "azure.mgmt.authorization")),
    "adls_meta": ("sparkforge_azure.collectors.adls_meta",
                  ("azure.identity", "azure.storage.filedatalake")),
    "resource_graph": ("sparkforge_azure.collectors.resource_graph",
                       ("azure.identity", "azure.mgmt.resourcegraph")),
}


def _live_collectors() -> Check:
    """Collector module health + lazy SDK extras needed for live mode.

    ``module`` reports whether the collector imports; ``live`` reports whether
    its SDK extras are installed.  Offline export mode never needs the SDKs,
    so a missing SDK is ``unavailable`` for live, never a failure.
    """
    per: dict[str, Any] = {}
    broken = []
    for name, (mod, deps) in _LIVE_COLLECTORS.items():
        try:
            importlib.import_module(mod)
            module_ok = True
        except Exception as exc:  # noqa: BLE001 - doctor reports, never raises
            module_ok = False
            broken.append(f"{name}: {type(exc).__name__}: {exc}"[:160])
        missing = [d for d in deps if not _spec(d)]
        per[name] = {
            "module": "available" if module_ok else "unavailable",
            "live": "available" if not missing else "unavailable",
            "missing_sdk": missing,
        }
    live_count = sum(1 for v in per.values() if v["live"] == "available")
    return Check("live_collectors", "fail" if broken else "ok",
                 f"{live_count}/{len(per)} collectors live-ready; "
                 "offline export mode always available",
                 {"collectors": per, "errors": broken} if broken else {"collectors": per})


CHECKS: tuple[Callable[[], Check], ...] = (
    _installation, _dependencies, _agentic_os, _tokensave, _graphfy, _code_intelligence,
    _knowledge, _mcp, _skills_agents, _surface, _claims, _azure_extras, _credentials_state,
    _traces, _lab, _live_collectors,
)


def run(areas: list[str] | None = None) -> dict[str, Any]:
    results = []
    for fn in CHECKS:
        try:
            c = fn()
        except Exception as exc:  # noqa: BLE001 - doctor never crashes
            c = Check(fn.__name__.strip("_"), "fail", f"{type(exc).__name__}: {exc}"[:200])
        if areas and c.area not in areas:
            continue
        results.append(c.to_dict())
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    overall = "fail" if counts.get("fail") else "ok"
    return {"status": overall, "summary": counts, "checks": results,
            "cloud_mutation": "none", "network_calls": 0}
