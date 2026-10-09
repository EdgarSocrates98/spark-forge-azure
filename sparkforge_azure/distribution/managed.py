"""The managed-asset ledger: what we wrote, its hash, and how to undo it.

Every file the lifecycle writes or edits is recorded in
``.sparkforge-azure/managed.json`` with the owning component, the sha256 of
the file after our write, and — for shared JSON files like ``.mcp.json`` —
the *owned keys* inside it. This is what makes detach safe (§82–§87):
removal touches only recorded assets, user content is preserved, and drift
(missing / modified) is reported instead of silently re-conquered.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sparkforge_azure.durable import write_atomic

LEDGER_NAME = "managed.json"

AssetState = Literal["present", "missing", "modified"]


@dataclass(frozen=True, slots=True)
class ManagedFile:
    path: str  # absolute, normalized posix
    kind: str  # e.g. "project_manifest", "mcp_config", "receipt"
    sha256: str
    mode: str = "file"  # "file" = we own it | "merge" = we own keys inside it
    owned_keys: tuple[str, ...] = ()
    owned_key_hashes: dict[str, str] | None = None
    host: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "path": self.path,
            "kind": self.kind,
            "sha256": self.sha256,
            "mode": self.mode,
        }
        if self.owned_keys:
            out["owned_keys"] = list(self.owned_keys)
        if self.owned_key_hashes:
            out["owned_key_hashes"] = dict(self.owned_key_hashes)
        if self.host:
            out["host"] = self.host
        return out


def ledger_path(state_root: Path) -> Path:
    return Path(state_root) / LEDGER_NAME


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _value_sha(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lookup(data: dict[str, Any], dotted: str) -> Any:
    node: Any = data
    for part in str(dotted).split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def load_ledger(state_root: Path) -> dict[str, Any]:
    target = ledger_path(state_root)
    if not target.is_file():
        return {"version": 1, "files": []}
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": 1, "files": []}
    if not isinstance(raw, dict) or not isinstance(raw.get("files"), list):
        return {"version": 1, "files": []}
    return raw


def save_ledger(state_root: Path, ledger: dict[str, Any]) -> Path:
    target = ledger_path(state_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    return target


def record_file(
    ledger: dict[str, Any],
    path: Path,
    *,
    kind: str,
    mode: str = "file",
    owned_keys: tuple[str, ...] = (),
    owned_key_hashes: dict[str, str] | None = None,
    host: str | None = None,
) -> dict[str, Any]:
    """Insert or refresh the ledger entry for ``path`` (idempotent, §110)."""
    files = [f for f in ledger["files"] if f.get("path") != path.as_posix()]
    files.append(
        ManagedFile(
            path=path.as_posix(),
            kind=kind,
            sha256=_sha(path),
            mode=mode,
            owned_keys=owned_keys,
            owned_key_hashes=owned_key_hashes,
            host=host,
        ).to_dict()
    )
    return {"version": 1, "files": sorted(files, key=lambda item: item["path"])}


def forget_file(ledger: dict[str, Any], path: Path) -> dict[str, Any]:
    files = [f for f in ledger["files"] if f.get("path") != path.as_posix()]
    return {"version": 1, "files": files}


def assess_file(entry: dict[str, Any]) -> AssetState:
    """Does the recorded file still match what we wrote?"""
    target = Path(str(entry["path"]))
    if not target.is_file():
        return "missing"
    if entry.get("mode") == "merge":
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return "modified"
        if not isinstance(data, dict):
            return "modified"
        hashes = entry.get("owned_key_hashes") or {}
        for key in entry.get("owned_keys") or ():
            node = _lookup(data, str(key))
            if node is None:
                return "modified"
            expected = hashes.get(str(key))
            if expected is not None and _value_sha(node) != expected:
                return "modified"
        return "present"
    recorded = str(entry.get("sha256") or "")
    return "present" if _sha(target) == recorded else "modified"


def assess_ledger(state_root: Path) -> tuple[dict[str, Any], ...]:
    """Drift report over every recorded asset."""
    ledger = load_ledger(state_root)
    return tuple(
        {
            "path": entry.get("path"),
            "kind": entry.get("kind"),
            "host": entry.get("host"),
            "state": assess_file(entry),
        }
        for entry in ledger["files"]
    )


def apply_json_key(
    path: Path,
    dotted_key: str,
    value: Any,
    *,
    ledger: dict[str, Any],
    kind: str,
    host: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Set one dotted key inside a shared JSON file, never clobbering the rest.

    If the key already exists with a different value and the ledger does not
    show we own it, the write is refused-by-skip: the caller reports the
    conflict instead of overwriting user configuration (§71).
    """
    target = Path(path)
    data: dict[str, Any] = {}
    if target.is_file():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"{target.name}: invalid JSON ({exc})") from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"{target.name}: expected a JSON object")
        data = loaded

    node: Any = data
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    leaf = parts[-1]
    existing = node.get(leaf)
    owned_here = any(
        f.get("path") == target.as_posix() and dotted_key in (f.get("owned_keys") or [])
        for f in ledger["files"]
    )
    if existing is not None and existing != value and not owned_here:
        return ledger, "conflict"
    node[leaf] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, json.dumps(data, indent=2, sort_keys=True) + "\n")
    ledger = record_file(
        ledger,
        target,
        kind=kind,
        mode="merge",
        owned_keys=(dotted_key,),
        owned_key_hashes={dotted_key: _value_sha(value)},
        host=host,
    )
    return ledger, "written"


def remove_json_key(path: Path, dotted_key: str) -> bool:
    """Remove one owned key; returns True when the file is left empty."""
    target = Path(path)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    parts = dotted_key.split(".")
    # Resolve the chain of parent containers once, then drop the leaf and any
    # containers our removal left empty (deepest first).
    parents: list[dict[str, Any]] = []
    node: Any = data
    for part in parts[:-1]:
        node = node.get(part)
        if not isinstance(node, dict):
            return False
        parents.append(node)
    if parents[-1].pop(parts[-1], None) is None:
        return False
    for depth in range(len(parents) - 1, -1, -1):
        if parents[depth]:
            break
        owner = parents[depth - 1] if depth else data
        owner.pop(parts[depth], None)
    write_atomic(target, json.dumps(data, indent=2, sort_keys=True) + "\n")
    return not data


__all__ = [
    "LEDGER_NAME",
    "AssetState",
    "ManagedFile",
    "apply_json_key",
    "assess_file",
    "assess_ledger",
    "forget_file",
    "ledger_path",
    "load_ledger",
    "record_file",
    "remove_json_key",
    "save_ledger",
]
