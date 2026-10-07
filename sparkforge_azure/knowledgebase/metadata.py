"""Contrato de metadados da base de conhecimento Azure (secoes 277, 161, 162).

Todo `knowledge/**/*.md` (exceto `INDEX.md`) comeca com front matter YAML:

    ---
    id: azure.databricks.runtime-and-compute
    title: ...
    domain: azure-databricks
    authority: microsoft_official
    sources:
      - {url: https://learn.microsoft.com/..., retrieved: 2026-10-06}
    verified_at: 2026-10-06
    versions: {dbr: ["18 LTS"]}
    status: VERIFIED
    preview: false
    related: [azure.adls.gen2]
    ---

Este modulo so le e valida. Le o front matter linha a linha, em binario, e
para no `---` de fechamento: o corpo nunca e decodificado aqui (secao 71,
lazy loading). Quem precisa do corpo chama `loader.load_body`.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.paths import resolve_within

DOMAINS: frozenset[str] = frozenset(
    {
        "azure-spark",
        "azure-databricks",
        "unity-catalog",
        "fabric-data-engineering",
        "fabric-onelake",
        "fabric-realtime",
        "fabric-data-factory",
        "azure-synapse",
        "azure-data-factory",
        "azure-adls",
        "azure-event-hubs",
        "azure-purview",
        "azure-entra",
        "azure-keyvault",
        "azure-networking",
        "azure-finops",
        "azure-observability",
        "azure-terraform",
        "azure-bicep",
        "delta-lake",
        "iceberg",
        "open-table-formats",
        "spark-performance",
        "spark-streaming",
        "data-quality",
        "governance",
        "migration",
        "agentic",
    }
)

AUTHORITIES: frozenset[str] = frozenset(
    {
        "microsoft_official",
        "databricks_official",
        "apache_official",
        "terraform_official",
        "vendor_official",
        "community",
        "internal",
    }
)

STATUSES: frozenset[str] = frozenset(
    {"VERIFIED", "STALE", "CONFLICTED", "DEPRECATED", "UNRESOLVED"}
)

REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "domain",
    "authority",
    "sources",
    "verified_at",
    "versions",
    "status",
    "preview",
    "related",
)

# Arquivos de knowledge/ que nao sao entradas do contrato.
NON_ENTRY_FILES: frozenset[str] = frozenset({"INDEX.md", "README.md"})

_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_URL = re.compile(r"^https?://[^\s]+$")
_DELIM = b"---"


class KnowledgeError(ValueError):
    """Documento ou base que viola o contrato."""


@dataclass(frozen=True)
class Source:
    url: str
    retrieved: date

    def to_dict(self) -> dict[str, str]:
        return {"url": self.url, "retrieved": self.retrieved.isoformat()}


@dataclass(frozen=True)
class KnowledgeEntry:
    """Uma entrada validada. `path` e relativo a raiz de knowledge (posix)."""

    id: str
    title: str
    domain: str
    authority: str
    sources: tuple[Source, ...]
    verified_at: date
    versions: Mapping[str, Any]
    status: str
    preview: bool
    related: tuple[str, ...]
    path: str
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def source_urls(self) -> tuple[str, ...]:
        return tuple(s.url for s in self.sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "authority": self.authority,
            "sources": [s.to_dict() for s in self.sources],
            "verified_at": self.verified_at.isoformat(),
            "versions": dict(self.versions),
            "status": self.status,
            "preview": self.preview,
            "related": list(self.related),
            "path": self.path,
        }


def as_date(value: Any) -> date | None:
    """`date` ISO (YAML ja converte `2026-10-06`); string ISO tambem vale."""
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def read_front_matter_text(path: Path) -> str:
    """Le so o bloco de front matter, em binario, parando no fechamento.

    O corpo nao e lido alem da linha de fechamento, entao um corpo com bytes
    invalidos (ou gigante) nao afeta o indice.
    """
    lines: list[str] = []
    with open(path, "rb") as handle:
        first = handle.readline()
        if first.rstrip(b"\r\n").lstrip(b"\xef\xbb\xbf") != _DELIM:
            raise KnowledgeError(f"{path}: front matter ausente (primeira linha deve ser ---)")
        for raw in handle:
            if raw.rstrip(b"\r\n") == _DELIM:
                return "".join(lines)
            try:
                lines.append(raw.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise KnowledgeError(f"{path}: front matter nao e UTF-8: {exc}") from exc
    raise KnowledgeError(f"{path}: front matter sem --- de fechamento")


def parse_front_matter_text(text: str, origin: str = "<text>") -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise KnowledgeError(f"{origin}: YAML invalido no front matter: {exc}") from exc
    if not isinstance(data, dict):
        raise KnowledgeError(f"{origin}: front matter precisa ser um mapeamento")
    return data


def split_document(text: str, origin: str = "<text>") -> tuple[dict[str, Any], str]:
    """Separa (front matter, corpo) de um documento ja lido inteiro."""
    normalized = text.lstrip("﻿")
    lines = normalized.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise KnowledgeError(f"{origin}: front matter ausente (primeira linha deve ser ---)")
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == "---":
            fm = parse_front_matter_text("".join(lines[1:index]), origin)
            return fm, "".join(lines[index + 1 :])
    raise KnowledgeError(f"{origin}: front matter sem --- de fechamento")


def _validate_sources(
    raw: Any, authority: str, origin: str, errors: list[str]
) -> tuple[Source, ...]:
    if not isinstance(raw, list):
        errors.append(f"{origin}: 'sources' precisa ser lista")
        return ()
    out: list[Source] = []
    before = len(errors)
    for pos, item in enumerate(raw):
        if not isinstance(item, Mapping):
            errors.append(f"{origin}: sources[{pos}] precisa ser mapeamento {{url, retrieved}}")
            continue
        url = item.get("url")
        retrieved = as_date(item.get("retrieved"))
        if not isinstance(url, str) or not _URL.match(url):
            errors.append(f"{origin}: sources[{pos}].url invalida: {url!r}")
            continue
        if retrieved is None:
            errors.append(f"{origin}: sources[{pos}].retrieved precisa ser data ISO")
            continue
        out.append(Source(url=url, retrieved=retrieved))
    if not out and authority != "internal" and len(errors) == before:
        errors.append(f"{origin}: 'sources' vazio (so permitido com authority=internal)")
    return tuple(out)


def validate_front_matter(
    data: Mapping[str, Any], path: str = "<memory>"
) -> tuple[KnowledgeEntry | None, list[str]]:
    """Valida UM front matter. Devolve (entrada ou None, erros)."""
    errors: list[str] = []
    origin = path
    missing = [name for name in REQUIRED_FIELDS if name not in data]
    if missing:
        return None, [f"{origin}: campos obrigatorios ausentes: {', '.join(missing)}"]

    entry_id = data["id"]
    if not isinstance(entry_id, str) or not _ID.match(entry_id) or "." not in entry_id:
        errors.append(
            f"{origin}: id invalido {entry_id!r} (pontilhado, minusculo, ex.: azure.adls.gen2)"
        )
    title = data["title"]
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{origin}: title vazio")
    domain = data["domain"]
    if domain not in DOMAINS:
        errors.append(f"{origin}: domain desconhecido {domain!r}")
    authority = data["authority"]
    if authority not in AUTHORITIES:
        errors.append(f"{origin}: authority desconhecida {authority!r}")
    status = data["status"]
    if status not in STATUSES:
        errors.append(f"{origin}: status desconhecido {status!r}")
    preview = data["preview"]
    if not isinstance(preview, bool):
        errors.append(f"{origin}: preview precisa ser booleano")
    verified_at = as_date(data["verified_at"])
    if verified_at is None:
        errors.append(f"{origin}: verified_at precisa ser data ISO (YYYY-MM-DD)")
    versions = data["versions"]
    if not isinstance(versions, Mapping):
        errors.append(
            f"{origin}: versions precisa ser mapeamento ({{}} quando independente de versao)"
        )
    else:
        for key, value in versions.items():
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                errors.append(f"{origin}: versions.{key} precisa ser lista de strings")
    related = data["related"]
    if not isinstance(related, list) or not all(isinstance(r, str) for r in related):
        errors.append(f"{origin}: related precisa ser lista de ids")
        related = []
    elif isinstance(entry_id, str) and entry_id in related:
        errors.append(f"{origin}: related cita o proprio id")
    sources = _validate_sources(data["sources"], str(authority), origin, errors)

    if errors:
        return None, errors
    extra = {k: v for k, v in data.items() if k not in REQUIRED_FIELDS}
    entry = KnowledgeEntry(
        id=entry_id,
        title=title.strip(),
        domain=domain,
        authority=authority,
        sources=sources,
        verified_at=verified_at,  # type: ignore[arg-type]
        versions=dict(versions),
        status=status,
        preview=preview,
        related=tuple(related),
        path=path,
        extra=extra,
    )
    return entry, []


def validate_graph(entries: Iterable[KnowledgeEntry]) -> list[str]:
    """Regras entre entradas: ids unicos e `related` resolvendo."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    entries = list(entries)
    for entry in entries:
        if entry.id in seen:
            errors.append(f"id duplicado {entry.id!r}: {seen[entry.id]} e {entry.path}")
        else:
            seen[entry.id] = entry.path
    for entry in entries:
        for ref in entry.related:
            if ref not in seen:
                errors.append(f"{entry.path}: related {ref!r} nao resolve para nenhum id")
    return errors


def resolve_root(root: Path | str) -> Path:
    """Normaliza a raiz (env/CLI) uma vez: `expanduser().resolve()` + exige diretorio."""
    resolved = Path(root).expanduser().resolve()
    if not resolved.is_dir():
        raise KnowledgeError(f"raiz de knowledge nao e diretorio: {resolved}")
    return resolved


def _scan_entry_files(root: Path) -> tuple[list[Path], list[str]]:
    """(arquivos dentro da raiz, erros de arquivos que escapam dela via symlink)."""
    files: list[Path] = []
    escaped: list[str] = []
    for p in root.rglob("*.md"):
        if p.name in NON_ENTRY_FILES:
            continue
        rel = p.relative_to(root).as_posix()
        safe = resolve_within(root, rel)
        if safe is None:
            escaped.append(f"{rel}: caminho escapa da raiz de knowledge (recusado)")
            continue
        files.append(p)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    return files, sorted(escaped)


def iter_entry_files(root: Path) -> list[Path]:
    """Os `.md` de `root` que sao entradas, confinados a raiz (ordem deterministica)."""
    try:
        base = resolve_root(root)
    except KnowledgeError:
        return []
    return _scan_entry_files(base)[0]


def load_entries(root: Path) -> tuple[list[KnowledgeEntry], list[str]]:
    """Le o front matter de toda a base e valida contrato + grafo."""
    try:
        root = resolve_root(root)
    except KnowledgeError as exc:
        return [], [str(exc)]
    entries: list[KnowledgeEntry] = []
    files, errors = _scan_entry_files(root)
    for file in files:
        rel = file.relative_to(root).as_posix()
        safe = resolve_within(root, rel)
        if safe is None:  # pragma: no cover - ja filtrado em _scan_entry_files
            errors.append(f"{rel}: caminho escapa da raiz de knowledge (recusado)")
            continue
        try:
            data = parse_front_matter_text(read_front_matter_text(safe), rel)
        except KnowledgeError as exc:
            errors.append(str(exc).replace(str(safe), rel))
            continue
        entry, problems = validate_front_matter(data, rel)
        errors.extend(problems)
        if entry is not None:
            entries.append(entry)
    errors.extend(validate_graph(entries))
    return entries, errors
