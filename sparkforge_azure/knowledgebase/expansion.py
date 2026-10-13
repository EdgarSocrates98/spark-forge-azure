"""Expansao deterministica de consulta (secao 72). Sem LLM.

`knowledge/query_expansion.yaml`:

    schema_version: 1
    terms:
      - term: external location
        aliases: [external locations]
        expands: [storage credential, access connector, ...]
        targets: [azure.unity-catalog.troubleshooting-external-locations, unity-catalog]

`targets` sao ids de knowledge ou dominios; ambos sao validados contra a base.
A mesma consulta gera sempre a mesma expansao, na ordem do arquivo.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.knowledgebase.metadata import DOMAINS


class ExpansionError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class ExpansionRule:
    term: str
    aliases: tuple[str, ...]
    expands: tuple[str, ...]
    targets: tuple[str, ...]

    def surface_forms(self) -> tuple[str, ...]:
        return (self.term, *self.aliases)


@dataclass(frozen=True)
class Expansion:
    query: str
    matched: tuple[str, ...]
    terms: tuple[str, ...]
    ids: tuple[str, ...]
    domains: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "matched": list(self.matched),
            "terms": list(self.terms),
            "ids": list(self.ids),
            "domains": list(self.domains),
        }


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def parse_rules(data: Any, origin: str = "query_expansion.yaml") -> list[ExpansionRule]:
    errors: list[str] = []
    if not isinstance(data, Mapping) or data.get("schema_version") != 1:
        raise ExpansionError([f"{origin}: precisa ser mapeamento com schema_version: 1"])
    terms = data.get("terms")
    if not isinstance(terms, list) or not terms:
        raise ExpansionError([f"{origin}: 'terms' precisa ser lista nao vazia"])
    rules: list[ExpansionRule] = []
    seen: set[str] = set()
    for pos, raw in enumerate(terms):
        where = f"{origin}: terms[{pos}]"
        if not isinstance(raw, Mapping):
            errors.append(f"{where} precisa ser mapeamento")
            continue
        term = raw.get("term")
        if not isinstance(term, str) or not term.strip():
            errors.append(f"{where}: term ausente")
            continue
        lists: dict[str, tuple[str, ...]] = {}
        for name in ("aliases", "expands", "targets"):
            value = raw.get(name, [])
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                errors.append(f"{where}.{name} precisa ser lista de strings")
                value = []
            lists[name] = tuple(value)
        if not lists["targets"]:
            errors.append(f"{where}: targets vazio (cada termo precisa apontar para id ou dominio)")
        key = normalize(term)
        if key in seen:
            errors.append(f"{where}: termo duplicado {term!r}")
        seen.add(key)
        rules.append(
            ExpansionRule(
                term=key,
                aliases=tuple(normalize(a) for a in lists["aliases"]),
                expands=tuple(normalize(e) for e in lists["expands"]),
                targets=lists["targets"],
            )
        )
    if errors:
        raise ExpansionError(errors)
    return rules


def load_rules(path: Path) -> list[ExpansionRule]:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ExpansionError([f"{path.name}: YAML invalido: {exc}"]) from exc
    return parse_rules(data, path.name)


def validate_targets(rules: Iterable[ExpansionRule], known_ids: Iterable[str]) -> list[str]:
    ids = set(known_ids)
    errors = []
    for rule in rules:
        for target in rule.targets:
            if target not in ids and target not in DOMAINS:
                errors.append(f"expansao {rule.term!r}: alvo {target!r} nao e id nem dominio")
    return errors


def _matches(form: str, query: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(form) + r"(?![a-z0-9])"
    return re.search(pattern, query) is not None


def expand(query: str | Iterable[str], rules: Iterable[ExpansionRule]) -> Expansion:
    """Expande `query` (texto ou lista de termos). Puro e deterministico.

    Um termo expandido que tambem e termo de regra NAO e reexpandido (um nivel
    so): expansao em cadeia cresce sem limite e esconde de onde veio o alvo.
    """
    text = query if isinstance(query, str) else " ".join(query)
    norm = normalize(text)
    rules = list(rules)
    matched: list[str] = []
    terms: list[str] = []
    targets: list[str] = []
    for rule in rules:
        if any(_matches(form, norm) for form in rule.surface_forms()):
            matched.append(rule.term)
            terms.append(rule.term)
            terms.extend(rule.expands)
            targets.extend(rule.targets)
    targets_t = _dedupe(targets)
    return Expansion(
        query=text,
        matched=_dedupe(matched),
        terms=_dedupe(terms),
        ids=tuple(t for t in targets_t if t not in DOMAINS),
        domains=tuple(t for t in targets_t if t in DOMAINS),
    )
