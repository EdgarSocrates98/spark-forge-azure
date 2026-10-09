"""Safe, reversible detach (spec §80–§89).

``detach`` removes only what the managed ledger records (§82): merged keys
inside shared files are excised, fully-owned *integration* files (host
configs) are deleted, and user content is never touched (§83). Lifecycle
state — ``project.yaml``, ``workspace.yaml``, receipts, the ledger itself —
is *preserved by default* (§84–§85): ``--purge-state``/``--purge-cache`` are
the explicit opt-outs, and a modified managed file is treated as user work
and preserved. ``--dry-run`` reports without writing. Reattach is
``distribution init`` idempotence — with the same ``project_id`` when state
was preserved (§88).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from sparkforge_azure.distribution.discovery import STATE_DIR_NAME, discover
from sparkforge_azure.distribution.managed import (
    assess_file,
    ledger_path,
    load_ledger,
    remove_json_key,
    save_ledger,
    strip_marker_block,
)
from sparkforge_azure.durable import write_atomic

#: Ledger kinds that live under `.sparkforge-azure/` — lifecycle *state*,
#: removed only via --purge-state.
STATE_KINDS = frozenset({"project_manifest", "workspace_manifest", "receipt", "ledger"})


def detach(
    root: Path | None = None,
    *,
    dry_run: bool = False,
    purge_state: bool = False,
    purge_cache: bool = False,
) -> dict[str, Any]:
    base = Path(root or Path.cwd()).resolve()
    found = discover(base)
    project_root = found.project_root or base
    state = project_root / STATE_DIR_NAME
    ledger = load_ledger(state)
    if not ledger["files"]:
        return {
            "status": "ok",
            "detached": [],
            "preserved": [],
            "warnings": ["nothing managed recorded; detach is a no-op"],
            "dry_run": dry_run,
        }

    detached: list[dict[str, Any]] = []
    preserved: list[str] = []
    warnings: list[str] = []
    remaining = list(ledger["files"])

    def drop(entry: dict[str, Any]) -> None:
        nonlocal remaining
        remaining = [r for r in remaining if r["path"] != entry["path"]]

    for entry in ledger["files"]:
        target = Path(str(entry["path"]))
        kind = str(entry.get("kind") or "")
        state_now = assess_file(entry)
        record = {"path": entry["path"], "kind": kind, "state": state_now}

        if kind in STATE_KINDS and not purge_state:
            record["action"] = "preserved_state"
            preserved.append(entry["path"])
            detached.append(record)
            continue
        if state_now == "missing":
            record["action"] = "absent"
            detached.append(record)
            drop(entry)
            continue
        # A managed asset modified since our write — file or merged key — is
        # user work now: preserve it and warn instead of reverting (§83, §85).
        if state_now == "modified":
            record["action"] = "preserved_modified"
            preserved.append(entry["path"])
            warnings.append(f"modified after our write, preserved: {entry['path']}")
            detached.append(record)
            continue
        if entry.get("mode") == "markers":
            if dry_run:
                record["action"] = "would_strip_block"
            else:
                text = target.read_text(encoding="utf-8")
                stripped = strip_marker_block(text)
                if stripped:
                    write_atomic(target, stripped)
                    record["action"] = "stripped_block"
                else:
                    target.unlink(missing_ok=True)
                    record["action"] = "removed_empty_file"
            detached.append(record)
            drop(entry)
            continue
        if entry.get("mode") == "merge":
            if dry_run:
                record["action"] = "would_remove_keys"
            else:
                emptied = remove_json_key(
                    target, str((entry.get("owned_keys") or ("",))[0])
                )
                if emptied:
                    target.unlink(missing_ok=True)
                    record["action"] = "removed_keys_and_empty_file"
                else:
                    record["action"] = "removed_keys"
            detached.append(record)
            drop(entry)
            continue
        if dry_run:
            record["action"] = "would_remove"
        else:
            target.unlink(missing_ok=True)
            record["action"] = "removed"
        detached.append(record)
        drop(entry)

    purged: list[str] = []
    for flag, directory in ((purge_state, state), (purge_cache, state / "cache")):
        if not flag or not directory.is_dir():
            continue
        if dry_run:
            purged.append(f"would_remove:{directory}")
            continue
        shutil.rmtree(directory)
        purged.append(str(directory))

    if not dry_run:
        if remaining and not purge_state:
            save_ledger(state, {"version": 1, "files": remaining})
        elif not purge_state:
            ledger_path(state).unlink(missing_ok=True)
        # purge_state removed the whole dir including the ledger.

    return {
        "status": "ok",
        "detached": detached,
        "preserved": preserved,
        "purged": purged,
        "warnings": warnings,
        "dry_run": dry_run,
        "state_preserved": not purge_state,
        "reattach": "sparkforge-azure distribution init",
    }


__all__ = ["detach"]
