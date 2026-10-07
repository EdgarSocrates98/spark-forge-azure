"""Grafo de impacto do conhecimento (secao 163).

Dado um conjunto de ids de knowledge que ficaram STALE ou mudaram, lista quem
depende deles:

- `knowledge`: outras entradas cujo `related` aponta para o id (transitivo,
  opcional);
- `rule`: `rules/catalog/*.yaml` com `knowledge_refs` citando o id, ou
  `sources[].url` igual ao caminho do doc ou a uma URL que o doc cita;
- `skill`: `skills/*/SKILL.md` com `knowledge_refs` no front matter (direto ou
  sob `metadata:`);
- `agent`: `agents/*.md` com `knowledge_refs` no front matter;
- `eval`: arquivos em `evals/` ou `lab/scenarios/` que mencionam o id ou o
  caminho do doc;
- `doc`: `docs/**/*.md` que mencionam o id ou o caminho do doc.

Diretorios ausentes ou vazios sao tolerados (estao sendo construidos em
paralelo); arquivos ilegiveis viram `warnings`, nunca excecao.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.knowledgebase.metadata import (
    KnowledgeEntry,
    KnowledgeError,
    parse_front_matter_text,
    read_front_matter_text,
)
from sparkforge_azure.paths import resolve_within


@dataclass(frozen=True)
class Dependent:
    kind: str
    path: str
    ref: str
    via: str
    name: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "path": self.path,
            "ref": self.ref,
            "via": self.via,
            "name": self.name,
        }


def _rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _refs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def _iter_rule_docs(data: Any) -> list[Mapping[str, Any]]:
    if isinstance(data, Mapping):
        rules = data.get("rules")
        if isinstance(rules, list):
            return [r for r in rules if isinstance(r, Mapping)]
        return [data]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, Mapping)]
    return []


def reverse_related(entries: Iterable[KnowledgeEntry]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for entry in entries:
        for ref in entry.related:
            reverse.setdefault(ref, []).append(entry.id)
    return {k: sorted(v) for k, v in reverse.items()}


def knowledge_closure(
    changed: Iterable[str], entries: Iterable[KnowledgeEntry], transitive: bool = True
) -> dict[str, str]:
    """Ids de knowledge afetados -> por qual id chegaram la (o proprio, se mudou)."""
    entries = list(entries)
    reverse = reverse_related(entries)
    affected: dict[str, str] = {c: c for c in changed}
    frontier = list(affected)
    while frontier:
        nxt: list[str] = []
        for current in frontier:
            for dependent in reverse.get(current, []):
                if dependent not in affected:
                    affected[dependent] = current
                    nxt.append(dependent)
        frontier = nxt if transitive else []
    return affected


def impact(
    changed_ids: Iterable[str],
    entries: Iterable[KnowledgeEntry],
    repo_root: Path,
    transitive: bool = True,
) -> dict[str, Any]:
    repo_root = Path(repo_root).expanduser().resolve()
    entries = list(entries)
    by_id = {e.id: e for e in entries}
    changed = sorted(set(changed_ids))
    unknown = [c for c in changed if c not in by_id]
    known = [c for c in changed if c in by_id]

    closure = knowledge_closure(known, entries, transitive=transitive)
    dependents: list[Dependent] = []
    warnings: list[str] = []
    for kid, via in sorted(closure.items()):
        if kid not in known:
            dependents.append(
                Dependent("knowledge", f"knowledge/{by_id[kid].path}", via, "related", kid)
            )

    # Referencias que contam como "cita o doc", por id mudado.
    doc_paths = {c: f"knowledge/{by_id[c].path}" for c in known}
    urls = {c: set(by_id[c].source_urls) for c in known}

    def match_text(text: str) -> list[tuple[str, str]]:
        hits = []
        for c in known:
            if c in text:
                hits.append((c, "mention:id"))
            elif doc_paths[c] in text:
                hits.append((c, "mention:path"))
        return hits

    # rules
    catalog = repo_root / "rules" / "catalog"
    if catalog.is_dir():
        for file in sorted(list(catalog.rglob("*.yaml")) + list(catalog.rglob("*.yml"))):
            rel = _rel(file, repo_root)
            if resolve_within(repo_root, rel) is None:
                warnings.append(f"{rel}: escapa da raiz (recusado)")
                continue
            try:
                data = yaml.safe_load(file.read_text(encoding="utf-8"))
            except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
                warnings.append(f"{rel}: ilegivel ({type(exc).__name__})")
                continue
            for rule in _iter_rule_docs(data):
                name = str(rule.get("id") or rule.get("rule_id") or "")
                refs = set(_refs(rule.get("knowledge_refs")))
                rule_urls = {
                    s.get("url")
                    for s in rule.get("sources") or []
                    if isinstance(s, Mapping) and isinstance(s.get("url"), str)
                }
                for c in known:
                    if c in refs:
                        dependents.append(Dependent("rule", rel, c, "knowledge_refs", name))
                    elif any(u.rstrip("/").endswith(doc_paths[c]) for u in rule_urls):
                        dependents.append(Dependent("rule", rel, c, "sources.url:path", name))
                    elif rule_urls & urls[c]:
                        dependents.append(Dependent("rule", rel, c, "sources.url:shared", name))

    # skills e agents (front matter)
    def scan_front_matter(files: list[Path], kind: str) -> None:
        for file in files:
            rel = _rel(file, repo_root)
            if resolve_within(repo_root, rel) is None:
                warnings.append(f"{rel}: escapa da raiz (recusado)")
                continue
            try:
                fm = parse_front_matter_text(read_front_matter_text(file), rel)
            except KnowledgeError:
                continue
            refs = set(_refs(fm.get("knowledge_refs")))
            meta = fm.get("metadata")
            if isinstance(meta, Mapping):
                refs |= set(_refs(meta.get("knowledge_refs")))
            name = str(fm.get("name") or file.stem)
            for c in known:
                if c in refs:
                    dependents.append(Dependent(kind, rel, c, "knowledge_refs", name))

    skills = repo_root / "skills"
    if skills.is_dir():
        scan_front_matter(sorted(skills.glob("*/SKILL.md")), "skill")
    agents = repo_root / "agents"
    if agents.is_dir():
        scan_front_matter(sorted(agents.glob("*.md")), "agent")

    # evals e docs (mencao textual)
    def scan_text(base: Path, patterns: tuple[str, ...], kind: str) -> None:
        if not base.is_dir():
            return
        files: set[Path] = set()
        for pattern in patterns:
            files.update(base.rglob(pattern))
        for file in sorted(files):
            rel = _rel(file, repo_root)
            if resolve_within(repo_root, rel) is None:
                warnings.append(f"{rel}: escapa da raiz (recusado)")
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                warnings.append(f"{rel}: ilegivel ({type(exc).__name__})")
                continue
            for c, via in match_text(text):
                dependents.append(Dependent(kind, rel, c, via, file.stem))

    eval_patterns = ("*.yaml", "*.yml", "*.json", "*.md")
    scan_text(repo_root / "evals", eval_patterns, "eval")
    scan_text(repo_root / "lab" / "scenarios", eval_patterns, "eval")
    scan_text(repo_root / "docs", ("*.md",), "doc")

    dependents = sorted(set(dependents), key=lambda d: (d.kind, d.path, d.ref, d.via))
    by_kind: dict[str, int] = {}
    for dep in dependents:
        by_kind[dep.kind] = by_kind.get(dep.kind, 0) + 1
    return {
        "changed": changed,
        "unknown_ids": unknown,
        "affected_knowledge": sorted(closure),
        "dependents": [d.to_dict() for d in dependents],
        "counts": dict(sorted(by_kind.items())),
        "warnings": warnings,
    }
