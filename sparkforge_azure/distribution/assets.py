"""Packaged-asset inventory and content hashing (spec §106–§108).

The wheel force-includes the canonical assets under ``sparkforge_azure/_data``
(``rules/catalog``, ``knowledge``, ``skills``, ``agents``, ``lab/scenarios`` —
see ``pyproject.toml``). From a source checkout the same files live at the
repository root. This module resolves both layouts the same way
``doctor.data_root`` does — source dirs when ``pyproject.toml`` sits beside
the package, packaged ``_data/`` otherwise — so the inventory is identical in
shape from source and from an installed wheel.

Hashes are content integrity markers, **not** signatures (§108): they answer
"did this asset change?", never "is this asset authentic?".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from sparkforge_azure.distribution.errors import PortableError

_PKG = Path(__file__).resolve().parents[1]
_REPO = _PKG.parent

#: Asset groups, as declared in `[tool.hatch.build.targets.wheel.force-include]`.
ASSET_GROUPS: tuple[str, ...] = ("agents", "knowledge", "lab", "rules", "skills")

TEMPLATES_PACKAGE = "sparkforge_azure.distribution.templates"


@dataclass(frozen=True, slots=True)
class PackageAsset:
    group: str
    name: str
    sha256: str


def asset_source() -> str:
    """``source`` when running from the checkout, ``wheel`` when installed."""
    if (_REPO / "pyproject.toml").is_file() and (_REPO / "rules" / "catalog").is_dir():
        return "source"
    return "wheel"


def group_dir(group: str) -> Path:
    """Root of one asset group, in whichever layout is active.

    Public counterpart of ``asset_source()``: ``sparkforge_azure.rules.loader``
    and ``knowledge_ref`` resolve packaged ``rules/catalog`` and ``knowledge``
    through here instead of re-deriving the source/wheel split, so the two
    resolvers cannot drift apart again (the pre-`_data` package-local fallback
    they carried pointed at paths that do not exist in the wheel).
    """
    return _group_dir(group)


def _group_dir(group: str) -> Path:
    if asset_source() == "source":
        return _REPO / group
    return _PKG / "_data" / group


def _walk(root: Path, group: str, prefix: str = "") -> list[PackageAsset]:
    assets: list[PackageAsset] = []
    for item in sorted(root.iterdir(), key=lambda entry: entry.name):
        relative = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_dir():
            if item.name == "__pycache__":
                continue
            assets.extend(_walk(item, group, relative))
        elif item.is_file():
            try:
                digest = hashlib.sha256(item.read_bytes()).hexdigest()
            except OSError:
                continue
            assets.append(PackageAsset(group=group, name=relative, sha256=digest))
    return assets


def asset_inventory() -> tuple[PackageAsset, ...]:
    """Every packaged asset with its sha256, grouped by top-level dir."""
    out: list[PackageAsset] = []
    for group in ASSET_GROUPS:
        root = _group_dir(group)
        if not root.is_dir():
            raise PortableError(
                "manifest_invalid",
                f"packaged asset group {group!r} missing at {root}",
                unlock="reinstall sparkforge-azure; the wheel carries _data/",
            )
        out.extend(_walk(root, group))
    out.extend(_template_assets())
    return tuple(out)


def _template_assets() -> tuple[PackageAsset, ...]:
    try:
        root = files(TEMPLATES_PACKAGE)
    except (ModuleNotFoundError, ValueError):
        return ()
    assets: list[PackageAsset] = []
    for item in sorted(root.iterdir(), key=lambda entry: entry.name):
        if item.is_file():
            try:
                digest = hashlib.sha256(item.read_bytes()).hexdigest()
            except OSError:
                continue
            assets.append(PackageAsset(group="templates", name=item.name, sha256=digest))
    return tuple(assets)


def load_template(name: str) -> tuple[str, str]:
    """UTF-8 template content + sha256, or a named refusal."""
    try:
        resource = files(TEMPLATES_PACKAGE).joinpath(name)
    except (ModuleNotFoundError, ValueError) as exc:
        raise PortableError("host_unavailable", f"template package missing: {exc}") from exc
    if not resource.is_file():
        raise PortableError("host_unavailable", f"template {name!r} not packaged")
    try:
        content = resource.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PortableError("host_unavailable", f"template {name!r} unreadable: {exc}") from exc
    return content, hashlib.sha256(content.encode("utf-8")).hexdigest()


def asset_summary() -> dict[str, object]:
    """Compact per-group counts for inspect/doctor output."""
    inventory = asset_inventory()
    groups: dict[str, int] = {}
    for asset in inventory:
        groups[asset.group] = groups.get(asset.group, 0) + 1
    return {
        "asset_count": len(inventory),
        "source": asset_source(),
        "groups": dict(sorted(groups.items())),
    }


__all__ = [
    "ASSET_GROUPS",
    "TEMPLATES_PACKAGE",
    "PackageAsset",
    "asset_inventory",
    "asset_source",
    "group_dir",
    "asset_summary",
    "load_template",
]
