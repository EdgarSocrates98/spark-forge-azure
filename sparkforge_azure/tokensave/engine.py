"""TokenSave: the explicit retrieval-economy capability (sections 40-45).

Primitives (section 42): ``search``, ``read``, ``symbols``, ``refs``, ``diff``,
``expand``, ``context``.  Every primitive:

* is confined to the workspace root and to ``WorkspaceScanPolicy`` (secrets,
  key files and ``.env`` are never read);
* records what it put into context in the ``RetrievalLedger`` (bytes, items,
  level, cache hit, reuse) -- bytes, never tokens;
* consults the content-addressed cache first and reports reuse when the same
  item was already delivered in this session (no repeated context).

``context(task)`` walks the ladder L0 -> L6 and STOPS at the first level whose
result is sufficient (section 43).  L4 (semantic retrieval) is honestly
reported as unavailable offline.  L6 (full file) is a fallback that only the
``deep`` profile may take, and only with a declared reason (section 44).
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sparkforge_azure.paths import WorkspaceScanPolicy, resolve_within, scan_repository
from sparkforge_azure.tokensave import cache as cache_mod
from sparkforge_azure.tokensave.ledger import RetrievalLedger, RetrievalRecord, payload_bytes
from sparkforge_azure.tokensave.levels import Level, Profile, profile

SymbolExtractor = Callable[[str, str], list[dict[str, Any]]]

# Extension -> symbol extractor. Python is built in; Code Intelligence registers
# the Azure formats (SQL, Terraform, Bicep, notebooks, ADF JSON...) here.
SYMBOL_EXTRACTORS: dict[str, SymbolExtractor] = {}

_STOP = frozenset(
    "the and for with from that this into what when where which como para com sem que uma um "
    "dos das por nao não está esta isso por que qual quais onde quando".split()
)
_REF = re.compile(
    r"(?P<path>[\w./\\-]+\.(?:py|sql|tf|bicep|json|ya?ml|ipynb|scala|kql|md))(?::(?P<line>\d+))?"
)
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{2,}")


def _python_symbols(text: str, rel: str) -> list[dict[str, Any]]:
    from sparkforge_azure.codeintel.extract import extrair_nos

    return [
        {"name": n.name, "qualified_name": n.qualified_name, "kind": n.kind,
         "start_line": n.start_line, "end_line": n.end_line}
        for n in extrair_nos(text, rel)
    ]


SYMBOL_EXTRACTORS[".py"] = _python_symbols


@dataclass
class ContextResult:
    status: str  # sufficient | partial | refused
    stop_reason: str
    levels_used: list[str]
    items: list[dict[str, Any]]
    unresolved: list[str]
    ledger: dict[str, Any]
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "stop_reason": self.stop_reason,
            "levels_used": self.levels_used,
            "items": self.items,
            "unresolved": self.unresolved,
            "ledger": self.ledger,
            "trace": self.trace,
            "authority": "data_only",
        }


class TokenSave:
    def __init__(
        self,
        root: str | Path,
        *,
        profile_name: str = "economy",
        index_db: str | Path | None = None,
        cache_dir: Path | None = None,
        policy: WorkspaceScanPolicy | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.profile: Profile = profile(profile_name)
        self.index_db = Path(index_db) if index_db else None
        self.ledger = RetrievalLedger()
        self.cache = cache_mod.ResultCache(cache_dir)
        self.policy = policy or WorkspaceScanPolicy()
        self._files: list[Path] | None = None

    # ------------------------------------------------------------------ helpers
    def _remaining(self) -> int:
        return max(0, self.profile.budget_bytes - self.ledger.total_bytes)

    def _resolve(self, path: str) -> Path | None:
        target = resolve_within(self.root, path)
        if target is None or not target.is_file():
            return None
        name = target.name
        if (
            name in self.policy.deny_files
            or target.suffix in self.policy.deny_suffixes
            or any(part in self.policy.deny_names for part in target.relative_to(self.root).parts)
            or target.stat().st_size > self.policy.max_file_bytes
        ):
            return None
        return target

    def _files_list(self) -> list[Path]:
        if self._files is None:
            self._files = list(scan_repository(self.root, self.policy).files)
        return self._files

    def _rel(self, p: Path) -> str:
        return p.relative_to(self.root).as_posix()

    def _emit(self, primitive: str, level: Level, payload: Any, *, item_key: str = "",
              cache_hit: bool = False, fallback: bool = False, outcome: str = "ok",
              reason: str = "") -> Any:
        reused = bool(item_key) and self.ledger.seen(item_key)
        if item_key:
            self.ledger.mark(item_key)
        items = len(payload) if isinstance(payload, list) else (1 if payload else 0)
        self.ledger.add(RetrievalRecord(
            primitive=primitive, level=int(level),
            payload_bytes=0 if reused else payload_bytes(payload),
            items=items, cache_hit=cache_hit, reused=reused, fallback=fallback,
            outcome=outcome if items or outcome != "ok" else "empty", reason=reason,
        ))
        return payload

    def _refuse(self, primitive: str, level: Level, reason: str) -> dict[str, Any]:
        self._emit(primitive, level, [], outcome="refused", reason=reason)
        return {"refused": True, "reason": reason}

    # ---------------------------------------------------------------- primitives
    def search(self, query: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        """L1 literal search: every token must appear on the line (case-insensitive)."""
        limit = min(limit or self.profile.max_hits, self.profile.max_hits)
        tokens = [t.lower() for t in _TOKEN.findall(query)]
        if not tokens:
            return self._emit("search", Level.L1_LITERAL, [])
        fp = str(len(self._files_list()))
        k = cache_mod.key("search", {"q": tokens, "limit": limit}, fp)
        cached = self.cache.get(k)
        if cached is not None:
            return self._emit("search", Level.L1_LITERAL, cached, item_key=k, cache_hit=True)
        hits: list[dict[str, Any]] = []
        for f in self._files_list():
            try:
                lines = f.read_text(encoding="utf-8", errors="strict").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(lines, 1):
                low = line.lower()
                if all(t in low for t in tokens):
                    hits.append({"path": self._rel(f), "line": i, "text": line.strip()[:160]})
                    if len(hits) >= limit:
                        break
            if len(hits) >= limit:
                break
        self.cache.put(k, hits)
        return self._emit("search", Level.L1_LITERAL, hits, item_key=k)

    def symbols(self, path: str) -> list[dict[str, Any]] | dict[str, Any]:
        """L2 symbols of one file -- names and line ranges, never bodies."""
        target = self._resolve(path)
        if target is None:
            return self._refuse("symbols", Level.L2_SYMBOL, f"not readable under policy: {path}")
        extractor = SYMBOL_EXTRACTORS.get(target.suffix.lower())
        if extractor is None:
            return self._refuse("symbols", Level.L2_SYMBOL, f"no extractor for {target.suffix}")
        k = cache_mod.key("symbols", {"p": self._rel(target)}, cache_mod.file_fingerprint(target))
        cached = self.cache.get(k)
        if cached is not None:
            return self._emit("symbols", Level.L2_SYMBOL, cached, item_key=k, cache_hit=True)
        text = target.read_text(encoding="utf-8", errors="replace")
        syms = extractor(text, self._rel(target))
        self.cache.put(k, syms)
        return self._emit("symbols", Level.L2_SYMBOL, syms, item_key=k)

    def refs(self, name: str) -> list[dict[str, Any]]:
        """L2 references. With an index: resolved callers. Without: literal call sites."""
        if self.index_db and self.index_db.is_file():
            from sparkforge_azure.codeintel.graph import chamadores
            from sparkforge_azure.codeintel.search import buscar

            out: list[dict[str, Any]] = []
            for hit in buscar(self.index_db, name, limite=self.profile.max_hits):
                for c in chamadores(self.index_db, hit.node_id):
                    out.append({"symbol": hit.qualified_name, "caller": c.qualified_name,
                                "path": c.path, "line": c.start_line, "basis": "index"})
            return self._emit("refs", Level.L2_SYMBOL, out[: self.profile.max_hits])
        hits = [dict(h, basis="literal") for h in self.search(f"{name}")]
        return self._emit("refs", Level.L2_SYMBOL, hits)

    def expand(self, node_id: str, *, depth: int | None = None) -> list[dict[str, Any]] | dict:
        """L3 bounded graph expansion (impact) from a node id. Requires the index."""
        if not (self.index_db and self.index_db.is_file()):
            return self._refuse("expand", Level.L3_GRAPH, "no code-intelligence index")
        from sparkforge_azure.codeintel.graph import impacto

        d = min(depth or self.profile.max_expansion_depth, self.profile.max_expansion_depth)
        nodes = [
            {"node_id": n.node_id, "name": n.qualified_name, "path": n.path,
             "line": n.start_line, "depth": n.depth}
            for n in impacto(self.index_db, node_id, d)
        ][: self.profile.max_hits]
        return self._emit("expand", Level.L3_GRAPH, nodes)

    def read(self, path: str, start: int = 1, end: int | None = None) -> dict[str, Any]:
        """L5 bounded slice. Never more than ``profile.slice_lines`` lines."""
        target = self._resolve(path)
        if target is None:
            return self._refuse("read", Level.L5_SLICE, f"not readable under policy: {path}")
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, start)
        end = min(len(lines), end or start + self.profile.slice_lines - 1,
                  start + self.profile.slice_lines - 1)
        body = "\n".join(lines[start - 1 : end])
        payload = {"path": self._rel(target), "start": start, "end": end,
                   "total_lines": len(lines), "truncated": end < len(lines) or start > 1,
                   "text": body}
        if payload_bytes(payload) > self._remaining():
            return self._refuse("read", Level.L5_SLICE, "budget exhausted")
        return self._emit("read", Level.L5_SLICE, payload,
                          item_key=f"read:{payload['path']}:{start}:{end}")

    def read_full(self, path: str, *, reason: str) -> dict[str, Any]:
        """L6 full artifact -- fallback only (section 44)."""
        if not self.profile.allow_full_read:
            return self._refuse("read_full", Level.L6_FULL,
                                f"profile {self.profile.name} forbids full reads")
        if not reason.strip():
            return self._refuse("read_full", Level.L6_FULL, "full read requires a reason")
        target = self._resolve(path)
        if target is None:
            return self._refuse("read_full", Level.L6_FULL, f"not readable under policy: {path}")
        payload = {"path": self._rel(target), "text": target.read_text(encoding="utf-8",
                                                                          errors="replace")}
        if payload_bytes(payload) > self._remaining():
            return self._refuse("read_full", Level.L6_FULL, "budget exhausted")
        return self._emit("read_full", Level.L6_FULL, payload, fallback=True, reason=reason,
                          item_key=f"full:{payload['path']}")

    def diff(self, rev: str = "HEAD", path: str | None = None) -> dict[str, Any]:
        """Bounded ``git diff --unified=1`` (L5). Never the whole repo history."""
        # A revision starting with "-" would be parsed by git as an option
        # (e.g. --output=<file>): refuse it, and pin it after --end-of-options.
        if rev.startswith("-") or not re.fullmatch(r"[\w./~^@{}][\w./~^@{}-]{0,79}", rev):
            return self._refuse("diff", Level.L5_SLICE, "invalid revision")
        argv = ["git", "-C", str(self.root), "diff", "--unified=1", "--no-color",
                "--no-ext-diff", "--no-textconv", "--end-of-options", rev, "--"]
        if path:
            target = resolve_within(self.root, path)
            if target is None:
                return self._refuse("diff", Level.L5_SLICE, "path escapes root")
            if self._denied(target.relative_to(self.root).as_posix()):
                return self._refuse("diff", Level.L5_SLICE, f"denied by scan policy: {path}")
            argv.append(path)
        else:
            argv += ["."] + [f":(exclude,glob)**/{n}" for n in sorted(self.policy.deny_files)]
            argv += [f":(exclude,glob)**/*{s}" for s in sorted(self.policy.deny_suffixes)]
            argv += [f":(exclude,glob)**/{n}/**" for n in sorted(self.policy.deny_names)]
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=30,  # noqa: S603
                                  check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return self._refuse("diff", Level.L5_SLICE, f"git unavailable: {exc}")
        if proc.returncode != 0:
            return self._refuse("diff", Level.L5_SLICE, proc.stderr.strip()[:200])
        budget = min(self._remaining(), self.profile.budget_bytes // 2)
        filtered = self._filter_diff(proc.stdout)  # defense in depth after pathspecs
        text = filtered.encode("utf-8")[:budget].decode("utf-8", errors="ignore")
        payload = {"rev": rev, "path": path, "truncated": len(filtered.encode()) > budget,
                   "diff": text}
        return self._emit("diff", Level.L5_SLICE, payload)

    def _denied(self, rel: str) -> bool:
        parts = rel.split("/")
        name = parts[-1]
        return (name in self.policy.deny_files
                or any(name.endswith(s) for s in self.policy.deny_suffixes)
                or any(part in self.policy.deny_names for part in parts[:-1]))

    def _filter_diff(self, text: str) -> str:
        """Drop whole file sections whose a/ or b/ path is denied by policy."""
        out: list[str] = []
        keep = True
        for line in text.splitlines(keepends=True):
            if line.startswith("diff --git "):
                paths = [p[2:] for p in line.split()[2:4] if p[:2] in ("a/", "b/")]
                keep = not any(self._denied(p) for p in paths)
            if keep:
                out.append(line)
        return "".join(out)

    # ------------------------------------------------------------------ ladder
    def context(self, task: str, *, required_terms: list[str] | None = None) -> ContextResult:
        """Walk L0 -> L6, stopping as soon as context is sufficient."""
        items: list[dict[str, Any]] = []
        levels: list[str] = []
        trace: list[dict[str, Any]] = []

        def stop(reason: str, unresolved: list[str]) -> ContextResult:
            status = "sufficient" if reason == "STOP_SUFFICIENT" else "partial"
            return ContextResult(status, reason, levels, items, unresolved,
                                 self.ledger.summary(), trace)

        # L0: exact references named in the task
        for m in _REF.finditer(task):
            line = int(m.group("line") or 1)
            half = self.profile.slice_lines // 2
            sl = self.read(m.group("path"), max(1, line - half), line + half)
            if not sl.get("refused"):
                items.append({"level": "L0", **sl})
        if items:
            levels.append("L0")
        terms = required_terms or self._terms(task)
        expanded = self._expand_terms(terms)
        trace.append({"level": "L0", "terms": terms, "expanded": expanded})

        def uncovered() -> list[str]:
            blob = " ".join(
                (str(i.get("text", "")) + " " + str(i.get("path", ""))).lower() for i in items
            )
            return [t for t in terms if t.lower() not in blob]

        if items and not uncovered():
            return stop("STOP_SUFFICIENT", [])

        # L1: literal search per term (plus deterministic expansions)
        before = len(items)
        for term in [*terms, *expanded]:
            if self._remaining() <= 0:
                return stop("STOP_BUDGET", uncovered())
            for h in self.search(term):
                if h not in items:
                    items.append({"level": "L1", **h})
        levels.append("L1")
        gained = len(items) - before
        trace.append({"level": "L1", "gained": gained})
        missing = uncovered()
        if not missing and items:
            # Located: hits carry path:line + the matching line. Code bodies only if asked.
            return stop("STOP_SUFFICIENT", [])
        if gained == 0 and not items:
            return stop("STOP_NO_GAIN", missing)

        # L2: enclosing symbols of the files that matched (names + ranges only)
        files = sorted({i["path"] for i in items if "path" in i})[: self.profile.max_slices]
        sym_ranges: dict[str, list[dict[str, Any]]] = {}
        for f in files:
            syms = self.symbols(f)
            if isinstance(syms, list):
                sym_ranges[f] = syms
        levels.append("L2")

        # L3: graph expansion only with an index and only within profile depth
        if self.index_db and self.index_db.is_file() and self.profile.max_expansion_depth > 0:
            levels.append("L3")

        # L4: semantic retrieval is not available offline -- declared, not faked
        trace.append({"level": "L4", "skipped": "no semantic index (offline, deterministic)"})

        # L5: bounded slices around the best hits (enclosing symbol when known)
        slices = 0
        for item in [i for i in items if i.get("level") == "L1"]:
            if slices >= self.profile.max_slices or self._remaining() <= 0:
                break
            start, end = self._window(item["path"], item["line"], sym_ranges.get(item["path"], []))
            sl = self.read(item["path"], start, end)
            if sl.get("refused"):
                if sl.get("reason") == "budget exhausted":
                    return stop("STOP_BUDGET", uncovered())
                continue
            items.append({"level": "L5", **sl})
            slices += 1
        if slices:
            levels.append("L5")
        missing = uncovered()
        if not missing:
            return stop("STOP_SUFFICIENT", [])
        # L6 is never taken automatically: it needs an explicit read_full(reason).
        return stop("STOP_UNRESOLVED", missing)

    def _window(self, path: str, line: int, syms: list[dict[str, Any]]) -> tuple[int, int]:
        enclosing = [s for s in syms if s["start_line"] <= line <= s.get("end_line", line)]
        if enclosing:
            s = min(enclosing, key=lambda s: s.get("end_line", line) - s["start_line"])
            if s.get("end_line", line) - s["start_line"] < self.profile.slice_lines:
                return s["start_line"], s["end_line"]
        half = self.profile.slice_lines // 2
        return max(1, line - half), line + half

    @staticmethod
    def _terms(task: str) -> list[str]:
        seen: list[str] = []
        for tok in _TOKEN.findall(task):
            low = tok.lower()
            if low in _STOP or _REF.fullmatch(tok):
                continue
            if low not in (s.lower() for s in seen):
                seen.append(tok)
        return seen[:8]

    @staticmethod
    def _expand_terms(terms: list[str]) -> list[str]:
        try:
            from sparkforge_azure.codeintel.query_expansion import expand_query
        except ImportError:  # pragma: no cover - defensive
            return []
        try:
            result = expand_query(" ".join(terms))
        except Exception:  # noqa: BLE001 - expansion is optional enrichment
            return []
        extra = getattr(result, "expanded_terms", None) or getattr(result, "terms", None) or []
        low = {t.lower() for t in terms}
        return [t for t in extra if isinstance(t, str) and t.lower() not in low][:8]
