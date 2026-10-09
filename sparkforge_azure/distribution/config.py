"""Deterministic config precedence (spec §44–§47).

Order, lowest to highest:

    package defaults
    < user config   (file pointed by SPARKFORGE_AZURE_CONFIG)
    < workspace     (.sparkforge-azure/workspace.yaml `config:`)
    < project       (.sparkforge-azure/project.yaml `config:`)
    < CLI explicit  (--set key=value, repeatable)

The resolution is inspectable: ``resolve_config`` returns both the effective
mapping and per-key provenance so `distribution inspect` can show
value + source (§45). Unknown keys are refused in strict mode and surface as
``unknown_config_keys`` otherwise — never silently ignored (§47).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.distribution.errors import PortableError

#: The closed vocabulary of config keys the lifecycle understands today.
KNOWN_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "context.default_scope",
        "context.profile",
        "host.activation",
        "network.mode",
        "state.retention",
    }
)

DEFAULT_CONFIG: dict[str, Any] = {
    "context": {"default_scope": "target", "profile": "balanced"},
    "host": {"activation": "managed_only"},
    "network": {"mode": "offline_first"},
    "state": {"retention": "preserve"},
}

_LAYERS = ("defaults", "user", "workspace", "project", "cli")


def _flatten(data: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            out.update(_flatten(value, dotted))
        else:
            out[dotted] = value
    return out


def _unflatten(flat: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for dotted, value in flat.items():
        cursor = out
        parts = str(dotted).split(".")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return out


def _load_user_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise PortableError(
            "config_invalid", f"user config unreadable: {exc}",
            unlock="fix the file or unset SPARKFORGE_AZURE_CONFIG",
        ) from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise PortableError("config_invalid", f"{path}: config must be a mapping")
    return dict(raw)


def parse_overrides(pairs: list[str] | tuple[str, ...] | None) -> dict[str, Any]:
    """`--set a.b=value` pairs → nested mapping. Values stay strings."""
    out: dict[str, Any] = {}
    for pair in pairs or ():
        if "=" not in pair:
            raise PortableError(
                "config_invalid", f"--set expects key=value, got {pair!r}"
            )
        key, _, value = pair.partition("=")
        key = key.strip()
        if not key:
            raise PortableError("config_invalid", "--set key cannot be empty")
        cursor = out
        parts = key.split(".")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return out


def resolve_config(
    *,
    user_config_path: Path | None = None,
    workspace_config: Mapping[str, Any] | None = None,
    project_config: Mapping[str, Any] | None = None,
    cli_overrides: Mapping[str, Any] | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """Merge the five layers; returns effective config + per-key sources."""
    layers: list[tuple[str, Mapping[str, Any]]] = [
        ("defaults", DEFAULT_CONFIG),
        ("user", _load_user_config(user_config_path)),
        ("workspace", workspace_config or {}),
        ("project", project_config or {}),
        ("cli", cli_overrides or {}),
    ]
    flat: dict[str, Any] = {}
    sources: dict[str, str] = {}
    unknown: list[str] = []
    for layer, data in layers:
        for dotted, value in _flatten(data).items():
            if dotted not in KNOWN_CONFIG_KEYS and layer != "defaults":
                if strict:
                    raise PortableError(
                        "config_invalid",
                        f"unknown config key {dotted!r} in {layer} layer",
                        unlock=f"known keys: {sorted(KNOWN_CONFIG_KEYS)}",
                    )
                unknown.append(dotted)
                continue
            flat[dotted] = value
            sources[dotted] = layer
    result = _unflatten(flat)
    return {
        "config": result,
        "sources": dict(sorted(sources.items())),
        "unknown_keys": sorted(unknown),
        "precedence": list(_LAYERS),
    }


__all__ = [
    "DEFAULT_CONFIG",
    "KNOWN_CONFIG_KEYS",
    "parse_overrides",
    "resolve_config",
]
