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

#: Delimiters for the managed text block (§70). Content between them is
#: ours; everything else in the file is the user's and is never touched.
MARKER_BEGIN = "<!-- sparkforge-azure:begin -->"
MARKER_END = "<!-- sparkforge-azure:end -->"


def wrap_marker_block(body: str) -> str:
    """Full managed block including delimiters and trailing newline."""
    return f"{MARKER_BEGIN}\n{body.rstrip()}\n{MARKER_END}\n"


def extract_marker_block(text: str) -> str | None:
    """The managed region (markers included) or None when absent."""
    start = text.find(MARKER_BEGIN)
    end = text.find(MARKER_END)
    if start < 0 or end < 0 or end < start:
        return None
    return text[start : end + len(MARKER_END)]


def apply_marker_block(path: Path, body: str) -> str:
    """Upsert the managed block in ``path``; user content outside markers
    is byte-preserved (§70–§71). Returns the resulting file text.

    Incremental (cycle 16.1 §7.4): when the upsert produces bytes identical
    to what is already on disk nothing is written — re-installs do not
    re-touch converged host docs."""
    block = wrap_marker_block(body)
    old = path.read_text(encoding="utf-8") if path.is_file() else None
    text = old
    if text is not None:
        existing = extract_marker_block(text)
        if existing is not None:
            text = text.replace(existing, block.rstrip("\n"), 1)
            if not text.endswith("\n"):
                text += "\n"
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += "\n" + block if text.strip() else block
    else:
        text = block
    if text != old:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(path, text)
    return text


def strip_marker_block(text: str) -> str:
    """Remove the managed region and collapse the gap it leaves."""
    block = extract_marker_block(text)
    if block is None:
        return text
    out = text.replace(block, "", 1)
    out = out.replace("\n\n\n", "\n\n").strip("\n")
    return (out + "\n") if out.strip() else ""


def marker_block_sha(text: str) -> str | None:
    """sha256 of the managed region, None when no markers exist."""
    block = extract_marker_block(text)
    if block is None:
        return None
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


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
    """Persist the ledger — compare-before-write: an identical payload is
    never re-touched (incremental install, cycle 16.1 §7.4)."""
    target = ledger_path(state_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    if not (target.is_file() and target.read_text(encoding="utf-8") == payload):
        write_atomic(target, payload)
    return target


def ledger_entry(ledger: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """The ledger entry recorded for ``path`` (any mode), or None."""
    key = path.as_posix()
    for entry in ledger["files"]:
        if entry.get("path") == key:
            return entry
    return None


def write_managed_file(
    ledger: dict[str, Any],
    path: Path,
    content: str | bytes,
    *,
    kind: str,
    host: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Whole-file managed write guarded by ownership (install-2.1).

    ``content`` may be ``str`` (encoded UTF-8) or ``bytes`` — binary
    assets like fonts/images under ``references/`` copy verbatim.

    Outcomes (the ``managed_files`` action vocabulary of
    ``forge/InstallReceipt/v1``, cycle 16.1 §7.4):

    - ``"created"`` — file absent and never ledgered: new managed asset.
    - ``"restored"`` — file absent but ledgered: a deleted managed asset
      is re-created (the same thing ``repair`` does through this path).
    - ``"updated"`` — ledgered file whose bytes drifted: ours, so the
      write reconverges drift.
    - ``"unchanged"`` — file exists byte-identical: nothing is written.
      Ledgered or not, the correct content is already there — for a
      *non-ledgered* file adopting it would make ``detach`` delete a
      file we never wrote, so it stays unrecorded. Callers can tell the
      two cases apart via ``ledger_entry``.
    - ``"preserved_foreign"`` — file exists, unledgered, different bytes:
      a user/foreign file sitting at a managed path. It is preserved,
      never recorded, and the caller reports the skip honestly.
    """
    data = (
        content.encode("utf-8") if isinstance(content, str)
        else bytes(content)
    )
    entry = ledger_entry(ledger, path)
    if path.exists():
        try:
            current = path.read_bytes()
        except OSError:
            current = b""
        if current == data:
            return ledger, "unchanged"
        if entry is None:
            return ledger, "preserved_foreign"
        action = "updated"
    else:
        action = "restored" if entry is not None else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    from sparkforge_azure.durable import write_atomic_bytes

    write_atomic_bytes(path, data)
    ledger = record_file(ledger, path, kind=kind, mode="file", host=host)
    return ledger, action


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
    if entry.get("mode") == "markers":
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return "modified"
        expected = (entry.get("owned_key_hashes") or {}).get("block")
        actual = marker_block_sha(text)
        if actual is None:
            return "modified"
        if expected is not None and actual != expected:
            return "modified"
        return "present"
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

    Outcomes (cycle 16.1 §7.4 vocabulary): ``"created"`` (file absent),
    ``"updated"`` (file existed, our key (re)written), ``"unchanged"``
    (the key already holds our exact value — nothing is re-touched,
    ownership is just re-claimed) or ``"conflict"`` (foreign value kept).
    """
    target = Path(path)
    existed = target.is_file()
    data: dict[str, Any] = {}
    if existed:
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
    if existing == value:
        # Converged — the key is already ours with the right value; claim
        # ownership without re-touching the shared file (incremental).
        return record_file(
            ledger,
            target,
            kind=kind,
            mode="merge",
            owned_keys=(dotted_key,),
            owned_key_hashes={dotted_key: _value_sha(value)},
            host=host,
        ), "unchanged"
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
    return ledger, "updated" if existed else "created"


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
    "MARKER_BEGIN",
    "MARKER_END",
    "apply_json_key",
    "apply_marker_block",
    "assess_file",
    "assess_ledger",
    "forget_file",
    "ledger_entry",
    "ledger_path",
    "load_ledger",
    "marker_block_sha",
    "record_file",
    "remove_json_key",
    "save_ledger",
    "strip_marker_block",
    "wrap_marker_block",
    "write_managed_file",
]
