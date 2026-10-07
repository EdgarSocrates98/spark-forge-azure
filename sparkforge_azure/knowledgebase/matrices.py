"""Matrizes com fonte por celula (secao 213, "sourced matrices").

Forma de `knowledge/matrices/*.yaml`:

    schema_version: 1
    matrix: databricks-runtime
    verified_at: 2026-10-06
    rows:
      - key: "18 LTS"
        values:
          spark: {value: "4.1.0", source: https://..., status: VERIFIED}

Toda celula carrega `value`, `source` (URL) e `status`. Celula sem fonte ou
sem status e rejeitada: uma matriz que mistura fato lido com fato lembrado
nao serve de evidencia.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from sparkforge_azure.knowledgebase.metadata import STATUSES, as_date
from sparkforge_azure.paths import resolve_within

CELL_STATUSES: frozenset[str] = STATUSES | {"UNVERIFIED", "PREVIEW"}
_URL = re.compile(r"^https?://[^\s]+$")


class MatrixError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Cell:
    value: Any
    source: str
    status: str
    note: str | None = None


@dataclass(frozen=True)
class Matrix:
    name: str
    verified_at: date
    rows: Mapping[str, Mapping[str, Cell]]
    path: str

    def get(self, key: str, column: str) -> Cell | None:
        return self.rows.get(key, {}).get(column)

    def keys(self) -> list[str]:
        return list(self.rows)


def validate_matrix(data: Any, origin: str = "<memory>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, Mapping):
        return [f"{origin}: matriz precisa ser mapeamento"]
    if data.get("schema_version") != 1:
        errors.append(f"{origin}: schema_version precisa ser 1")
    if not isinstance(data.get("matrix"), str) or not data["matrix"]:
        errors.append(f"{origin}: 'matrix' (nome) ausente")
    if as_date(data.get("verified_at")) is None:
        errors.append(f"{origin}: verified_at precisa ser data ISO")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{origin}: 'rows' precisa ser lista nao vazia")
        return errors
    seen: set[str] = set()
    for pos, row in enumerate(rows):
        where = f"{origin}: rows[{pos}]"
        if not isinstance(row, Mapping):
            errors.append(f"{where} precisa ser mapeamento")
            continue
        key = row.get("key")
        if not isinstance(key, str) or not key:
            errors.append(f"{where}: key ausente")
        elif key in seen:
            errors.append(f"{where}: key duplicada {key!r}")
        else:
            seen.add(key)
        values = row.get("values")
        if not isinstance(values, Mapping) or not values:
            errors.append(f"{where}: values precisa ser mapeamento nao vazio")
            continue
        for column, cell in values.items():
            cw = f"{where}.values.{column}"
            if not isinstance(cell, Mapping):
                errors.append(f"{cw}: celula precisa ser {{value, source, status}}")
                continue
            if "value" not in cell:
                errors.append(f"{cw}: value ausente")
            source = cell.get("source")
            if not isinstance(source, str) or not _URL.match(source):
                errors.append(f"{cw}: source ausente ou nao e URL")
            status = cell.get("status")
            if status not in CELL_STATUSES:
                errors.append(f"{cw}: status ausente ou invalido {status!r}")
    return errors


def parse_matrix(data: Any, origin: str = "<memory>") -> Matrix:
    errors = validate_matrix(data, origin)
    if errors:
        raise MatrixError(errors)
    rows: dict[str, dict[str, Cell]] = {}
    for row in data["rows"]:
        rows[row["key"]] = {
            col: Cell(
                value=cell["value"],
                source=cell["source"],
                status=cell["status"],
                note=cell.get("note"),
            )
            for col, cell in row["values"].items()
        }
    return Matrix(
        name=data["matrix"],
        verified_at=as_date(data["verified_at"]),  # type: ignore[arg-type]
        rows=rows,
        path=origin,
    )


def load_matrix(path: Path) -> Matrix:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise MatrixError([f"{path.name}: YAML invalido: {exc}"]) from exc
    return parse_matrix(data, path.name)


def load_matrices(directory: Path) -> tuple[dict[str, Matrix], list[str]]:
    """Carrega todas as matrizes de um diretorio; devolve (matrizes, erros)."""
    directory = Path(directory).expanduser().resolve()
    matrices: dict[str, Matrix] = {}
    errors: list[str] = []
    if not directory.is_dir():
        return matrices, errors
    for file in sorted(directory.glob("*.yaml")):
        safe = resolve_within(directory, file.name)
        if safe is None:
            errors.append(f"{file.name}: caminho escapa do diretorio de matrizes (recusado)")
            continue
        try:
            matrix = load_matrix(safe)
        except MatrixError as exc:
            errors.extend(exc.errors)
            continue
        if matrix.name in matrices:
            errors.append(f"{file.name}: matriz {matrix.name!r} duplicada")
            continue
        matrices[matrix.name] = matrix
    return matrices, errors
