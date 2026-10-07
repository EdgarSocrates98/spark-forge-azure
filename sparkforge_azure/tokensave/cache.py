"""Content-addressed result cache.

Cache is NOT memory (section 286): it stores results of deterministic
primitives keyed by ``(primitive, canonical args, source fingerprint)``.  When
the fingerprint of what was read changes, the key changes and the old entry is
simply never hit again.  Nothing here is a decision or a learned fact.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def key(primitive: str, args: dict[str, Any], fingerprint: str) -> str:
    raw = json.dumps({"p": primitive, "a": args, "f": fingerprint}, sort_keys=True,
                     ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def file_fingerprint(path: Path) -> str:
    st = path.stat()
    return f"{st.st_size}:{st.st_mtime_ns}"


class ResultCache:
    def __init__(self, directory: Path | None = None) -> None:
        self._mem: dict[str, Any] = {}
        self._dir = directory

    def get(self, k: str) -> Any | None:
        if k in self._mem:
            return self._mem[k]
        if self._dir is not None:
            f = self._dir / f"{k}.json"
            if f.is_file():
                try:
                    value = json.loads(f.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    return None
                self._mem[k] = value
                return value
        return None

    def put(self, k: str, value: Any) -> None:
        self._mem[k] = value
        if self._dir is not None:
            self._dir.mkdir(parents=True, exist_ok=True)
            (self._dir / f"{k}.json").write_text(
                json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8"
            )
