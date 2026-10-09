"""The single path service for the portable lifecycle (spec §103–§105).

One module resolves every path the lifecycle touches — package, executable,
state, cache, config, project, workspace — and records *where each value came
from* so `distribution inspect` can show `value` + `source` (§45).

Authority model:

- ``SPARKFORGE_AZURE_STATE_DIR`` still wins for state (§101): same variable
  `paths.state_dir()` already honors, no second name for the same thing.
- ``SPARKFORGE_AZURE_CACHE`` overrides the cache root; the boolean-ish values
  ``on/off/0/1/true/false`` are the economy switch, never a directory.
- ``SPARKFORGE_AZURE_CONFIG`` points at a user-level config file; it is read,
  never written.
- Without env overrides, state anchors at the *project root* discovered by
  the upward manifest search when one exists, else at the cwd — identical
  to today's `<cwd>/.sparkforge-azure` for non-initialized directories
  (backward compatibility, §181–184).
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from sparkforge_azure.distribution.errors import PortableError

CACHE_DIR_ENV = "SPARKFORGE_AZURE_CACHE"
CONFIG_ENV = "SPARKFORGE_AZURE_CONFIG"
STATE_DIR_ENV = "SPARKFORGE_AZURE_STATE_DIR"

PathSource = Literal["default", "environment", "discovery", "argument"]

_CACHE_SWITCH_VALUES = frozenset({"on", "off", "0", "1", "true", "false", "yes", "no"})


@dataclass(frozen=True, slots=True)
class PortablePaths:
    """Every path the lifecycle uses, each with a recorded source."""

    package_root: Path
    executable: Path
    state_root: Path
    cache_root: Path
    config_path: Path | None
    project_root: Path | None
    workspace_root: Path | None
    sources: tuple[tuple[str, PathSource], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "package_root": str(self.package_root),
            "executable": str(self.executable),
            "state_root": str(self.state_root),
            "cache_root": str(self.cache_root),
            "config_path": str(self.config_path) if self.config_path else None,
            "project_root": str(self.project_root) if self.project_root else None,
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
            "sources": {name: source for name, source in self.sources},
        }


def _env_path(
    raw: str, *, cwd: Path, field: str
) -> Path:
    value = raw.strip()
    if not value:
        raise PortableError(
            "config_invalid", f"{field} is set but empty", unlock=f"unset {field}"
        )
    target = Path(value).expanduser()
    if not target.is_absolute():
        target = cwd / target
    try:
        return target.resolve()
    except OSError as exc:
        raise PortableError(
            "config_invalid", f"{field} cannot be resolved: {exc}",
            unlock=f"fix or unset {field}",
        ) from exc


def package_root() -> Path:
    """The installed package root — never a cwd-controlled checkout guess."""
    return Path(__file__).resolve().parents[1]


def resolve_paths(
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    project_root: Path | None = None,
    workspace_root: Path | None = None,
) -> PortablePaths:
    """Resolve package, state, cache, config, project and workspace paths.

    Pure resolution: this function never writes to the filesystem.
    """
    base = Path(cwd or Path.cwd()).resolve()
    values = env if env is not None else os.environ
    sources: list[tuple[str, PathSource]] = [("package_root", "default")]

    project = project_root.resolve() if project_root else None
    workspace = workspace_root.resolve() if workspace_root else None
    if project_root:
        sources.append(("project_root", "argument"))
    if workspace_root:
        sources.append(("workspace_root", "argument"))

    state_raw = values.get(STATE_DIR_ENV)
    if state_raw:
        state = _env_path(state_raw, cwd=base, field=STATE_DIR_ENV)
        sources.append(("state_root", "environment"))
    else:
        state = (project or base) / ".sparkforge-azure"
        sources.append(("state_root", "discovery" if project else "default"))

    cache_raw = values.get(CACHE_DIR_ENV)
    if cache_raw and cache_raw.strip().lower() in _CACHE_SWITCH_VALUES:
        cache_raw = None
    if cache_raw:
        cache = _env_path(cache_raw, cwd=base, field=CACHE_DIR_ENV)
        sources.append(("cache_root", "environment"))
    else:
        cache = state / "cache"
        sources.append(("cache_root", "default"))

    config_raw = values.get(CONFIG_ENV)
    config = _env_path(config_raw, cwd=base, field=CONFIG_ENV) if config_raw else None
    if config:
        sources.append(("config_path", "environment"))

    return PortablePaths(
        package_root=package_root(),
        executable=Path(sys.executable).resolve(),
        state_root=state.resolve(),
        cache_root=cache.resolve(),
        config_path=config,
        project_root=project,
        workspace_root=workspace,
        sources=tuple(sources),
    )


__all__ = [
    "CACHE_DIR_ENV",
    "CONFIG_ENV",
    "STATE_DIR_ENV",
    "PathSource",
    "PortablePaths",
    "package_root",
    "resolve_paths",
]
