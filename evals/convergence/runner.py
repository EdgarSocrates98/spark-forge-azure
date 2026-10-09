"""Cross-vertical convergence runner (prompt_evo_cycle6 §19-20, §106-114).

Executa um caso por vertical em todos os profiles declarados em
``suite.yaml`` e valida o contrato compartilhado:

- findings requeridos presentes / proibidos ausentes;
- evidencia requerida citada na serializacao do resultado;
- ``unresolved`` restrito aos valores permitidos pelo caso;
- chaves estruturais identicas entre verticais (result/case_meta/receipt);
- finding sem evidencia nao existe (``verified`` exige >= 1 fact id);
- facts ficam dentro do namespace do vertical (contaminacao cruzada);
- ``environment_fingerprint`` presente em ``case_meta``;
- ``trust`` permanece ``DATA_ONLY`` (nunca elevado silenciosamente);
- nenhum segredo padrao vaza na serializacao.

Uso CLI::

    python evals/convergence/runner.py [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sparkforge_azure.azure.pipeline import run_case as run_databricks  # noqa: E402
from sparkforge_azure.fabric.pipeline import run_fabric_case  # noqa: E402
from sparkforge_azure.migration.pipeline import run_migration_case  # noqa: E402
from sparkforge_azure.stream.pipeline import run_stream_case  # noqa: E402

LAB = Path(__file__).resolve().parent

PIPELINES = {
    "databricks": run_databricks,
    "fabric": run_fabric_case,
    "stream": run_stream_case,
    "migration": run_migration_case,
}

SECRET_MARKERS = ("BEGIN PRIVATE KEY", "SharedAccessKey=", "AccountKey=",
                  "client_secret", "passwd=")


def _load_suite() -> dict[str, Any]:
    return yaml.safe_load((LAB / "suite.yaml").read_text(encoding="utf-8"))


def _load_cases() -> list[dict[str, Any]]:
    cases = []
    for path in sorted((LAB / "cases").glob("*.yaml")):
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        spec["_file"] = path.name
        cases.append(spec)
    return cases


def _unresolved_ok(entry: Any, allowed: list[Any]) -> bool:
    """Cada entrada de ``unresolved`` precisa casar >=1 pattern permitido.

    Pattern dict: toda chave/valor do pattern deve aparecer na entrada.
    """
    for pattern in allowed:
        if isinstance(pattern, dict) and isinstance(entry, dict):
            if all(entry.get(k) == v for k, v in pattern.items()):
                return True
        elif entry == pattern:
            return True
    return False


def _validate(spec: dict[str, Any], result: dict[str, Any],
              suite: dict[str, Any]) -> list[str]:
    """Retorna lista de violacoes; vazia == caso conforme."""
    violacoes: list[str] = []
    cid = spec["id"]

    # Paridade estrutural — chaves compartilhadas
    for key in suite["shared_result_keys"]:
        if key not in result:
            violacoes.append(f"{cid}: resultado sem chave '{key}'")
    for key in suite["shared_case_meta_keys"]:
        if key not in result.get("case_meta", {}):
            violacoes.append(f"{cid}: case_meta sem '{key}'")
    for key in suite["shared_receipt_keys"]:
        if key not in result.get("receipt", {}):
            violacoes.append(f"{cid}: receipt sem '{key}'")

    # Findings
    regras = {f.get("rule_id") for f in result.get("findings", [])}
    for req in spec.get("required_findings") or []:
        if req not in regras:
            violacoes.append(f"{cid}: finding requerido ausente: {req}")
    for proib in spec.get("forbidden_findings") or []:
        if proib in regras:
            violacoes.append(f"{cid}: finding proibido presente: {proib}")

    # Nenhum finding sem evidencia (§20: verified exige >=1 fact)
    for f in result.get("findings", []):
        if not f.get("evidence"):
            violacoes.append(
                f"{cid}: finding {f.get('rule_id')} sem evidencia")
        else:
            # o fact citado precisa existir no resultado — no pool top-level
            # ou no pool deduplicado carregado pelo diagnostico
            fact_ids = {x["id"] for x in result.get("facts", [])}
            fact_ids |= {x["id"] for x in
                         (result.get("diagnosis") or {}).get("facts", [])}
            for ev in f["evidence"]:
                if ev not in fact_ids:
                    violacoes.append(
                        f"{cid}: {f.get('rule_id')} cita fact inexistente {ev}")

    # Evidencia requerida: token presente na serializacao completa
    blob = json.dumps(result, default=str)
    for token in spec.get("required_evidence") or []:
        if token not in blob:
            violacoes.append(f"{cid}: evidencia requerida ausente: {token}")

    # Unresolved permitido
    allowed = spec.get("allowed_unresolved") or []
    for entry in result.get("unresolved", []):
        if not _unresolved_ok(entry, allowed):
            violacoes.append(f"{cid}: unresolved nao permitido: {entry}")

    # Contaminacao cruzada: facts dentro do namespace do vertical
    ns = suite["fact_kind_namespaces"][spec["vertical"]]
    for f in result.get("facts", []):
        if not any(str(f["kind"]).startswith(p) for p in ns):
            violacoes.append(
                f"{cid}: fact kind estrangeiro '{f['kind']}' "
                f"fora do namespace {spec['vertical']}")

    # Trust DATA_ONLY nunca elevado
    trust = result.get("trust") or {}
    if trust.get("instruction_authority") != "data_only":
        violacoes.append(f"{cid}: trust sem instruction_authority=data_only")

    # Segredo nunca aparece no relatorio (§20)
    for marker in SECRET_MARKERS:
        if marker in blob:
            violacoes.append(f"{cid}: marcador de segredo vazou: {marker}")

    # Fingerprint de ambiente: deterministico e com eixos
    fp = result.get("case_meta", {}).get("environment_fingerprint") or {}
    if not fp.get("axes") or not fp.get("axis_order"):
        violacoes.append(f"{cid}: environment_fingerprint vazio/incompleto")

    return violacoes


def run_suite(*, profiles: list[str] | None = None) -> dict[str, Any]:
    """Roda o lab inteiro; retorna relatorio {cases, cells, violacoes, ok}."""
    suite = _load_suite()
    cases = _load_cases()
    active = profiles or suite["profiles"]
    report: dict[str, Any] = {"cases": {}, "cells": 0, "violacoes": []}
    for spec in cases:
        pipeline = PIPELINES[spec["vertical"]]
        fixture = str(ROOT / spec["fixture"])
        cell_resultados: dict[str, Any] = {}
        for profile in active:
            result = pipeline(fixture, profile=profile)
            report["cells"] += 1
            violacoes = _validate(spec, result, suite)
            cell_resultados[profile] = {
                "status": result["status"],
                "findings": len(result["findings"]),
                "unresolved": len(result["unresolved"]),
                "ok": not violacoes,
                "violacoes": violacoes,
            }
            report["violacoes"].extend(violacoes)
        report["cases"][spec["id"]] = cell_resultados
    report["ok"] = not report["violacoes"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true",
                        help="emite o relatorio completo em JSON")
    parser.add_argument("--profile", action="append",
                        help="restringe a um profile (repetivel)")
    args = parser.parse_args()
    report = run_suite(profiles=args.profile)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        for cid, cells in report["cases"].items():
            marca = "OK " if all(c["ok"] for c in cells.values()) else "FALHOU"
            for profile, cell in cells.items():
                print(f"{marca} {cid:<16} {profile:<20} "
                      f"findings={cell['findings']} "
                      f"unresolved={cell['unresolved']}")
        print(f"\ncelulas={report['cells']} violacoes="
              f"{len(report['violacoes'])}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
