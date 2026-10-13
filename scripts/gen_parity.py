"""Regenera ``parity.yaml`` e ``manifest.json`` a partir das fontes canonicas.

Fontes:
- ``docs/architecture/evidence/aws_audit.json`` — subsistemas medidos do AWS
- ``scripts/port_manifest.yaml`` — decisao por arquivo (COPY_SAFE/ADAPT/...)
- ``sparkforge_azure/`` — o que efetivamente existe neste pacote

A secao de hosts (``platforms``/``capabilities``) e declaracao curada — e o
contrato que ``tests/test_agentic_runtime.py::TestParityBinding`` amarra com
``sparkforge_azure/agentic/runtime.py``:

- ``spawn_agent``  <-> plataforma declara o mecanismo ``subagent``
- ``tool_calling`` <-> plataforma declara o mecanismo ``mcp``

Mudar mecanismo sem mudar ``runtime.py`` (ou vice-versa) derruba o teste.

    python scripts/gen_parity.py   # regrava parity.yaml + manifest.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "architecture" / "evidence" / "aws_audit.json"
PORT = ROOT / "scripts" / "port_manifest.yaml"
PKG = ROOT / "sparkforge_azure"

# Ordem de severidade: a classe do subsistema e a PIOR classe entre seus
# arquivos — um REIMPLEMENT num mar de COPY_SAFE nao pode herdar COPY_SAFE.
SEVERITY = ["COPY_SAFE", "ADAPT", "REIMPLEMENT_AZURE_NATIVE", "NOT_APPLICABLE", "DEFER"]

REASONS = {
    "COPY_SAFE": "nucleo neutro, copia com rename de pacote",
    "ADAPT": (
        "nucleo neutro com marcadores AWS ou arestas para modulos AWS; ver changes no port_manifest"
    ),
    "REIMPLEMENT_AZURE_NATIVE": (
        "semantica AWS sem analogo Azure; implementacao nova, proibido alias"
    ),
    "NOT_APPLICABLE": "capability sem analogo util no Azure",
    "DEFER": (
        "sem caso real, dependencia externa ou evidencia insuficiente; ver gatilho de reabertura"
    ),
}

# Secao de hosts — curada, e o contrato com agentic/runtime.py.
# Mecanismos: subagent (spawn), mcp (tool calling), playbook (floor declarativo),
# skills (skills do repo), cli (binario sparkforge-azure), hooks (ganchos locais).
HOSTS = {
    "platforms": ["claude_code", "devin_cli", "devin_desktop", "copilot_ci", "codex"],
    "capabilities": [
        {
            "id": "parallel-specialist-dispatch",
            "summary": "despachar especialistas em paralelo durante analise",
            "platforms": {
                "claude_code": ["subagent"],
                "devin_cli": ["subagent"],
                "devin_desktop": ["subagent"],
                "copilot_ci": ["playbook"],
                "codex": ["playbook"],
            },
        },
        {
            "id": "mcp-tool-call",
            "summary": "chamar tools sfa_* via servidor MCP",
            "platforms": {
                "claude_code": ["mcp"],
                "devin_cli": ["mcp"],
                "devin_desktop": ["mcp"],
                "copilot_ci": ["cli"],
                "codex": ["cli"],
            },
        },
        {
            "id": "cli-commands",
            "summary": "comandos do binario sparkforge-azure",
            "platforms": {
                "claude_code": ["cli"],
                "devin_cli": ["cli"],
                "devin_desktop": ["cli"],
                "copilot_ci": ["cli"],
                "codex": ["cli"],
            },
        },
        {
            "id": "repo-skills",
            "summary": "skills versionadas em skills/ + .claude/skills/",
            "platforms": {
                "claude_code": ["skills"],
                "devin_cli": ["skills"],
                "devin_desktop": ["skills"],
                "copilot_ci": ["playbook"],
                "codex": ["playbook"],
            },
        },
    ],
}


def _rollup_class(classes: set[str], has_files: bool) -> str:
    for cls in SEVERITY[::-1]:  # da mais severa para a menos
        if cls in classes:
            return cls
    return "COPY_SAFE" if has_files else "DEFER"


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    port = yaml.safe_load(PORT.read_text(encoding="utf-8"))

    # arquivo -> classe declarada no manifesto de port. `sparkforge/<sub>/...`
    # atribui para <sub>; paths sem o prefixo (`rules/catalog/x`, `lab/...`,
    # `evals/...`) sao dados de repo e atribuem pelo primeiro componente.
    # `rules/catalog` NAO e o subsistema `catalog` (Glue Data Catalog).
    per_subsystem: dict[str, dict] = {s: {"classes": set(), "entries": 0}
                                    for s in audit["subsystems"]}
    for entry in port["entries"]:
        rel = entry["src"].split("/")
        if rel[0] == "sparkforge":
            sub = rel[1].rsplit(".", 1)[0] if len(rel) == 2 else rel[1]
        else:
            sub = rel[0].rsplit(".", 1)[0] if len(rel) == 1 else rel[0]
        if sub in per_subsystem:
            per_subsystem[sub]["classes"].add(entry["class"])
            per_subsystem[sub]["entries"] += 1

    subsystems = {}
    for sub in sorted(audit["subsystems"]):
        info = per_subsystem[sub]
        aws = audit["subsystems"][sub]
        azure_present = (PKG / sub).is_dir() or (PKG / f"{sub}.py").is_file()
        markers = aws["aws_marker_total"]
        if azure_present and info["entries"] == 0:
            # Existe no Azure mas NENHUMA decisao de port cobre o homonimo AWS:
            # e modulo novo, nao port (ex.: `adapters` = eval tools Azure; o
            # pacote AWS de adapters MCP nao foi portado).
            cls, status = "REIMPLEMENT_AZURE_NATIVE", "new_azure"
            reason = (
                f"modulo Azure nativo; o homonimo AWS ({aws['files']} arquivos, "
                f"{markers} marcadores) nao tem decisao registrada no port_manifest"
            )
        else:
            cls = _rollup_class(info["classes"], info["entries"] > 0)
            if azure_present:
                status = "ported"
            else:
                status = "planned" if cls != "NOT_APPLICABLE" else "not_applicable"
            reason = REASONS[cls]
            if markers and cls == "COPY_SAFE":
                reason = f"COPY_SAFE apesar de {markers} marcador(es) AWS; revisar port_manifest"
        subsystems[sub] = {
            "class": cls,
            "status": status,
            "aws_files": aws["files"],
            "aws_markers": markers,
            "manifest_entries": info["entries"],
            "azure_path": f"sparkforge_azure/{sub}" if azure_present else None,
            "reason": reason,
        }

    parity = {
        "schema_version": 1,
        "reference_audit": "docs/architecture/evidence/aws_audit.json",
        "reference_sha": audit["reference_sha"],
        "decision_record": "scripts/port_manifest.yaml",
        "note": (
            "class do subsistema = pior classe entre seus arquivos no port_manifest; "
            "mudanca de classe exige reason (ver AWS_TO_AZURE_PORTABILITY_MATRIX.md §6)"
        ),
        **HOSTS,
        "aws_subsystems": subsystems,
    }
    text = yaml.safe_dump(parity, sort_keys=False, allow_unicode=True, width=110)
    (ROOT / "parity.yaml").write_text(
        "# Gerado por scripts/gen_parity.py — nao editar a mao.\n" + text,
        encoding="utf-8",
    )

    # manifest.json: superficie de capabilities vista pelo surface lock.
    capabilities = [
        {
            "id": c["id"],
            "summary": c["summary"],
            "status": "SUPPORTED",
        }
        for c in HOSTS["capabilities"]
    ]
    for sub, info in subsystems.items():
        if info["status"] == "not_applicable" or sub == "__init__":
            continue
        if info["status"] == "new_azure":
            summary = f"modulo azure-native {sub} (homonimo AWS nao portado)"
        else:
            summary = f"subsistema sparkforge.{sub} portado ({info['class']})"
        capabilities.append(
            {
                "id": f"port.{sub}",
                "summary": summary,
                "status": "SUPPORTED" if info["status"] in ("ported", "new_azure") else "PLANNED",
            }
        )
    manifest = {
        "schema_version": 1,
        "name": "spark-forge-azure",
        "provider": "azure",
        "domain": "data",
        "version": "0.1.0",
        "generated_by": "scripts/gen_parity.py",
        "status_enum": ["SUPPORTED", "PARTIAL", "EXPERIMENTAL", "PLANNED", "NOT_APPLICABLE"],
        "capabilities": capabilities,
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "subsystems": len(subsystems),
        "ported": sum(1 for s in subsystems.values() if s["status"] == "ported"),
        "capabilities": len(capabilities),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
