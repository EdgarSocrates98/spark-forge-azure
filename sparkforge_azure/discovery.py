# sparkforge_azure/discovery.py
"""Retrieval offline do install-2.0 (§6.2/§6.4) sobre as fontes reais do forge.

Cada funcao devolve um dict JSON-safe; a CLI (`cli/cmd_discovery.py` e a folha
`context pack` de `cli/cmd_context.py`) so adapta argv. Nada aqui inventa
catalogo: regras vem de `rules.loader.load_catalog`, documentos de
`knowledge_ref.knowledge_dir`, skills/agents/evals de
`distribution.assets._group_dir` — a mesma resolucao checkout-vs-wheel que o
install usa. Ausencia volta como `None`/lista vazia + marcador explicito,
nunca como conteudo fabricado.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from sparkforge_azure import __version__, discovery_ops
from sparkforge_azure.knowledge_ref import KnowledgeError, knowledge_dir, safe_knowledge_file
from sparkforge_azure.rules.loader import CatalogError, catalog_dir, load_catalog

INDEX_FIELDS = ("id", "category", "title", "severity_default", "runtime_scope")
SEVERITIES = ("P0", "P1", "P2", "P3", "P4")
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
_SNIPPET_MAX = 3
_SNIPPET_WIDTH = 160


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = DEFAULT_LIMIT
    return max(1, min(value, MAX_LIMIT))


def _cursor_offset(cursor: str | None) -> int:
    """Cursor = offset inteiro determinístico (mesma semântica do AWS)."""
    if cursor in (None, ""):
        return 0
    try:
        offset = int(str(cursor), 10)
    except ValueError:
        raise DiscoveryError(f"cursor invalido: {cursor!r}") from None
    if offset < 0:
        raise DiscoveryError(f"cursor invalido: {cursor!r}")
    return offset


def _paginate(items: list[Any], limit: int | None, cursor: str | None) -> dict[str, Any]:
    offset = _cursor_offset(cursor)
    lim = _clamp_limit(limit)
    page = items[offset : offset + lim]
    nxt = offset + lim if offset + lim < len(items) else None
    return {
        "items": page,
        "total": len(items),
        "limit": lim,
        "offset": offset,
        "next_cursor": str(nxt) if nxt is not None else None,
    }


class DiscoveryError(ValueError):
    """Input recusado pelo retrieval (cursor, dominio, caminho)."""


def _sha256_of(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _match_domain(seg: str, prefix: str) -> bool:
    return seg == prefix or seg.startswith(prefix + "-") or seg.startswith(prefix + "_")


def _domain_of_doc(rel: str, prefixes: tuple[str, ...]) -> bool:
    parts = re.split(r"[/\\_-]+", rel.lower())
    stem = Path(rel).stem.lower()
    parts.append(stem)
    for prefix in prefixes:
        if any(_match_domain(part, prefix) for part in parts):
            return True
    return False


def _rule_domains(rule: dict[str, Any], prefixes: tuple[str, ...]) -> bool:
    hay = " ".join(
        str(rule.get(k) or "") for k in ("id", "category", "title")
    ).lower()
    parts = re.split(r"[^a-z0-9]+", hay)
    return any(_match_domain(p, prefix) for prefix in prefixes for p in parts)


def _load_rules() -> list[dict[str, Any]]:
    try:
        return load_catalog()
    except CatalogError:
        return []


def _rule_index(rule: dict[str, Any]) -> dict[str, Any]:
    return {k: rule.get(k) for k in INDEX_FIELDS} | {
        "source_file": rule.get("_source_file")
    }


def rules_search(
    *,
    query: str | None = None,
    rule_id: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    index: bool = False,
) -> dict[str, Any]:
    """§6.2 rules.search sobre `rules/catalog` real — case-insensitive em
    id/title/category/explanation; paginacao deterministica por offset."""
    rules = _load_rules()
    if rule_id:
        rules = [r for r in rules if str(r.get("id")) == rule_id]
    if category:
        cat = category.lower()
        rules = [r for r in rules if cat in str(r.get("category") or "").lower()]
    if severity:
        sev = severity.upper()
        rules = [r for r in rules if str(r.get("severity_default")) == sev]
    if query:
        q = query.lower()
        rules = [
            r
            for r in rules
            if q in " ".join(
                str(r.get(k) or "")
                for k in ("id", "title", "category", "explanation")
            ).lower()
        ]
    rules = sorted(rules, key=lambda r: str(r.get("id")))
    page = _paginate([_rule_index(r) if index else r for r in rules], limit, cursor)
    return {
        "status": "ok",
        "forge": "sparkforge-azure",
        "catalog_dir": str(catalog_dir()),
        "filters_applied": {
            k: v
            for k, v in {
                "query": query,
                "id": rule_id,
                "category": category,
                "severity": severity,
            }.items()
            if v is not None
        },
        "rules": page["items"],
        "total": page["total"],
        "limit": page["limit"],
        "next_cursor": page["next_cursor"],
    }


def rules_get(rule_id: str) -> dict[str, Any]:
    """§6.2 rules.get — a regra completa ou `rule: None` + found=false."""
    for rule in _load_rules():
        if str(rule.get("id")) == rule_id:
            return {"status": "ok", "found": True, "rule": rule}
    return {
        "status": "ok",
        "found": False,
        "rule": None,
        "detail": f"{rule_id} ausente do catalogo — nada inventado",
    }


def _knowledge_docs(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def _knowledge_origin(root: Path) -> str:
    env = os.environ.get("SPARKFORGE_AZURE_KNOWLEDGE") or os.environ.get(
        "SPARK_FORGE_AZURE_KNOWLEDGE"
    )
    if env and root == Path(env).expanduser().resolve():
        return "env"
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "pyproject.toml").is_file() and root == repo_root / "knowledge":
        return "checkout"
    return "package"


def _doc_meta(root: Path, path: Path, *, term: str | None = None) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    meta: dict[str, Any] = {
        "ref": rel,
        "sha256": _sha256_of(path),
        "bytes": path.stat().st_size,
    }
    if term is None:
        return meta
    text = path.read_text(encoding="utf-8", errors="replace")
    needle = term.lower()
    hits = [
        (n, line.strip())
        for n, line in enumerate(text.splitlines(), 1)
        if needle in line.lower()
    ]
    meta["matched_lines"] = len(hits)
    meta["name_hit"] = needle in rel.lower() or needle in path.stem.lower()
    meta["snippets"] = [
        {"line": n, "text": s[:_SNIPPET_WIDTH]} for n, s in hits[:_SNIPPET_MAX]
    ]
    meta["snippets_truncated"] = len(hits) > _SNIPPET_MAX
    return meta


def knowledge_search(
    term: str,
    *,
    domain: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """§6.2 knowledge.search — um hit por documento (nunca dump de linhas),
    com sha256, proveniencia e paginacao."""
    root = knowledge_dir()
    prefixes = discovery_ops.domain_prefixes(domain) if domain else None
    needle = term.lower()
    matched: list[dict[str, Any]] = []
    total = 0
    for path in _knowledge_docs(root):
        rel = path.relative_to(root).as_posix()
        if prefixes and not _domain_of_doc(rel, prefixes):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if needle in rel.lower() or needle in text.lower():
            total += 1
            matched.append(path)
    offset = _cursor_offset(cursor)
    lim = _clamp_limit(limit)
    window = matched[offset : offset + lim]
    items = [_doc_meta(root, p, term=term) for p in window]
    nxt = offset + lim if offset + lim < len(matched) else None
    return {
        "status": "ok",
        "knowledge_root": str(root),
        "knowledge_origin": _knowledge_origin(root),
        "term": term,
        "domain": domain,
        "domain_prefixes": list(prefixes) if prefixes else None,
        "documents_total": total,
        "documents": items,
        "limit": lim,
        "next_cursor": str(nxt) if nxt is not None else None,
    }


def knowledge_get(file: str) -> dict[str, Any]:
    """§6.2 knowledge.get — caminho resolvido + proveniencia + sha256."""
    root = knowledge_dir()
    path = safe_knowledge_file(root, file)
    rel = path.relative_to(root).as_posix()
    return {
        "status": "ok",
        "knowledge_root": str(root),
        "knowledge_origin": _knowledge_origin(root),
        "document": {
            "ref": rel,
            "path": str(path),
            "sha256": _sha256_of(path),
            "bytes": path.stat().st_size,
        },
    }


def knowledge_list(limit: int | None = None, cursor: str | None = None) -> dict[str, Any]:
    root = knowledge_dir()
    docs = [p.relative_to(root).as_posix() for p in _knowledge_docs(root)]
    page = _paginate(docs, limit, cursor)
    return {
        "status": "ok",
        "knowledge_root": str(root),
        "knowledge_origin": _knowledge_origin(root),
        "documents": page["items"],
        "total": page["total"],
        "next_cursor": page["next_cursor"],
    }


def _group_names(group: str) -> list[str]:
    try:
        from sparkforge_azure.distribution.assets import _group_dir

        root = _group_dir(group)
    except Exception:
        return []
    if not root.is_dir():
        return []
    if group in ("skills",):
        return sorted(
            d.name for d in root.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
        )
    if group in ("agents",):
        return sorted(p.stem for p in root.glob("*.md"))
    if group in ("evals",):
        return sorted(d.name for d in root.iterdir() if d.is_dir())
    return []


def capabilities() -> dict[str, Any]:
    """§6.2 capabilities.list + protocol.describe num documento só."""
    rules = _load_rules()
    try:
        kroot = knowledge_dir()
        kdocs = _knowledge_docs(kroot)
        kstate: Any = {
            "root": str(kroot),
            "origin": _knowledge_origin(kroot),
            "documents": len(kdocs),
        }
    except KnowledgeError as exc:
        kstate = {"unavailable": str(exc)}
    return {
        "status": "ok",
        "forge": "sparkforge-azure",
        "version": __version__,
        "cli": discovery_ops.CLI,
        "offline": True,
        "rules": {
            "catalog_dir": str(catalog_dir()),
            "count": len(rules),
            "severities": list(SEVERITIES),
            "index_fields": list(INDEX_FIELDS),
        },
        "knowledge": kstate,
        "skills": {"count": len(_group_names("skills")), "ids": _group_names("skills")},
        "agents": {"count": len(_group_names("agents")), "ids": _group_names("agents")},
        "eval_suites": _group_names("evals"),
        "domains": list(discovery_ops.DOMAINS),
        "protocols": list(discovery_ops.PROTOCOLS),
        "interfaces": {"mcp": discovery_ops.MCP_INTERFACE},
        "operations": discovery_ops.ops_expanded(),
    }


def context_pack(
    domain: str | None = None,
    *,
    rules_limit: int | None = None,
    knowledge_limit: int | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """§6.2 context.build — pack deterministico e limitado por dominio:
    regras (index fields) + metadados de knowledge (sem dump) + protocolos +
    hash do pacote."""
    prefixes = discovery_ops.domain_prefixes(domain) if domain else None
    rules = _load_rules()
    if prefixes:
        rules = [r for r in rules if _rule_domains(r, prefixes)]
    rules = sorted(rules, key=lambda r: str(r.get("id")))
    rlim = _clamp_limit(rules_limit)
    rules_page = rules[:rlim]

    try:
        kroot = knowledge_dir()
        docs = [
            p
            for p in _knowledge_docs(kroot)
            if not prefixes or _domain_of_doc(p.relative_to(kroot).as_posix(), prefixes)
        ]
        klim = _clamp_limit(knowledge_limit)
        kpage = [_doc_meta(kroot, p) for p in docs[:klim]]
        kinfo: Any = {
            "root": str(kroot),
            "origin": _knowledge_origin(kroot),
            "documents": kpage,
            "documents_total": len(docs),
            "truncated": len(docs) > klim,
        }
    except KnowledgeError as exc:
        kinfo = {"unavailable": str(exc), "documents": []}

    pack: dict[str, Any] = {
        "schema": "forge/context-pack/v1",
        "forge": "sparkforge-azure",
        "version": __version__,
        "domain": domain,
        "domain_prefixes": list(prefixes) if prefixes else None,
        "rules": [_rule_index(r) for r in rules_page],
        "rules_total": len(rules),
        "rules_truncated": len(rules) > rlim,
        "knowledge": kinfo,
        "protocols": list(discovery_ops.PROTOCOLS),
        "operations": discovery_ops.ops(),
        "offline": True,
    }
    if as_of:
        pack["as_of"] = as_of
    pack["pack_sha256"] = hashlib.sha256(
        json.dumps(pack, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return pack
