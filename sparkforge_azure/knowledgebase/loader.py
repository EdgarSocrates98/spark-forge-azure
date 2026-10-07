"""Carga preguicosa da base (secao 71).

- `load_index()` le SO o front matter de cada documento (para no `---` de
  fechamento, em binario); nenhum corpo e decodificado.
- `load_body(id)` le UM documento.
- `select(task_terms, domains, limit)` devolve o menor conjunto de ids
  relevantes usando so o indice + a expansao deterministica. Nunca carrega a
  base inteira.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from sparkforge_azure.knowledgebase.expansion import (
    ExpansionError,
    ExpansionRule,
    expand,
    load_rules,
    normalize,
)
from sparkforge_azure.knowledgebase.metadata import (
    KnowledgeEntry,
    KnowledgeError,
    load_entries,
    resolve_root,
    split_document,
)
from sparkforge_azure.paths import resolve_within

EXPANSION_FILE = "query_expansion.yaml"
_TOKEN = re.compile(r"[a-z0-9]+")


def default_root() -> Path:
    from sparkforge_azure.knowledge_ref import knowledge_dir

    return resolve_root(knowledge_dir())


class KnowledgeBase:
    """Vista preguicosa sobre um diretorio `knowledge/`."""

    def __init__(self, root: Path | None = None):
        self.root = resolve_root(root) if root is not None else default_root()
        self._index: dict[str, KnowledgeEntry] | None = None
        self._errors: list[str] = []
        self._rules: list[ExpansionRule] | None = None

    # -- indice -----------------------------------------------------------
    def load_index(self) -> dict[str, KnowledgeEntry]:
        if self._index is None:
            entries, errors = load_entries(self.root)
            self._errors = errors
            self._index = {e.id: e for e in entries}
        return self._index

    @property
    def errors(self) -> list[str]:
        self.load_index()
        return list(self._errors)

    def entry(self, entry_id: str) -> KnowledgeEntry:
        index = self.load_index()
        if entry_id not in index:
            raise KnowledgeError(f"id desconhecido: {entry_id!r}")
        return index[entry_id]

    # -- corpo ------------------------------------------------------------
    def load_body(self, entry_id: str) -> str:
        entry = self.entry(entry_id)
        path = resolve_within(self.root, entry.path)
        if path is None:
            raise KnowledgeError(f"caminho fora da base: {entry.path}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeError(f"{entry.path}: corpo nao e UTF-8: {exc}") from exc
        _, body = split_document(text, entry.path)
        return body

    # -- expansao ---------------------------------------------------------
    def rules(self) -> list[ExpansionRule]:
        if self._rules is None:
            path = resolve_within(self.root, EXPANSION_FILE)
            if path is None or not path.is_file():
                self._rules = []
            else:
                try:
                    self._rules = load_rules(path)
                except ExpansionError:
                    self._rules = []
        return self._rules

    # -- selecao ----------------------------------------------------------
    def select(
        self,
        task_terms: str | Iterable[str],
        domains: Iterable[str] | None = None,
        limit: int = 5,
    ) -> list[str]:
        """Ids mais relevantes para a tarefa, em ordem deterministica.

        Pontuacao (so metadados): +5 alvo direto da expansao; +2 dominio
        alvo da expansao ou pedido; +1 por token do termo expandido presente
        no id/titulo. Empate desempata por id.
        """
        if limit <= 0:
            return []
        index = self.load_index()
        if not isinstance(task_terms, str):
            task_terms = list(task_terms)
        only = set(domains or ())
        exp = expand(task_terms, self.rules())
        wanted_domains = set(exp.domains) | only
        raw = task_terms if isinstance(task_terms, str) else " ".join(task_terms)
        tokens = set(_TOKEN.findall(normalize(raw)))
        for term in exp.terms:
            tokens.update(_TOKEN.findall(term))
        tokens = {t for t in tokens if len(t) > 2}
        direct = set(exp.ids)
        scores: dict[str, int] = {}
        for entry_id, entry in index.items():
            if only and entry.domain not in only and entry_id not in direct:
                continue
            score = 0
            if entry_id in direct:
                score += 5
            if entry.domain in wanted_domains:
                score += 2
            haystack = set(_TOKEN.findall(normalize(f"{entry.id} {entry.title}")))
            score += len(tokens & haystack)
            if score > 0:
                scores[entry_id] = score
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [entry_id for entry_id, _ in ranked[:limit]]


def load_index(root: Path | None = None) -> dict[str, KnowledgeEntry]:
    return KnowledgeBase(root).load_index()


def load_body(entry_id: str, root: Path | None = None) -> str:
    return KnowledgeBase(root).load_body(entry_id)


def select(
    task_terms: str | Iterable[str],
    domains: Iterable[str] | None = None,
    limit: int = 5,
    root: Path | None = None,
) -> list[str]:
    return KnowledgeBase(root).select(task_terms, domains, limit)
