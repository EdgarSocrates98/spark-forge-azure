"""Runner das suites de `evals/agentic/` — prepara o workspace e o contrato.

O que o runner faz, em ordem:

1. Resolve a suite pelo NOME curto (`fase0`, `sdd`) — nunca por caminho, para
   que um `--suite evals/agentic/sdd` nao aponte o agente ao gabarito.
2. Copia para um workspace de prova so os diretorios em `WORKSPACE_DIRS` — os
   artefatos que o agente pode ler (`fixtures/` incluido, `evals/` fora: o
   gabarito nao sai do checkout).
3. Filtra a tabela `adapters.tools.TOOLS`: o agente ve apenas as tools que a
   suite exige (`mcp__sparkforge__<verbo>`); as demais vao para a denylist.
4. Grava o contrato da rodada em `evals/agentic/<suite>/runs/<id>.json` — a
   pontuacao e feita depois, contra o scorecard do runner.

Uso:
    python scripts/run_agentic_eval.py --suite sdd --runs 1 [--prepare-only]

`--prepare-only` monta o workspace e o contrato sem chamar agente — e o modo
deterministico usado em revisao e no CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.adapters.tools import TOOLS  # noqa: E402
from sparkforge_azure.evals.suite import Suite, load_suite  # noqa: E402

SUITE_DIR = ROOT / "evals"
SDD_SUITE_DIR = ROOT / "evals" / "agentic" / "sdd"

_SUITES = {"fase0": SUITE_DIR, "sdd": SDD_SUITE_DIR}

# o que o workspace de prova recebe do checkout: `evals/` fica fora de
# proposito — o gabarito nao viaja com o agente
WORKSPACE_DIRS: tuple[str, ...] = ("fixtures", "docs", "knowledge", "rules", "config")

MCP_PREFIX = "mcp__sparkforge__"


def _suite_dir(nome: str) -> Path:
    if nome not in _SUITES:
        raise SystemExit(f"suite desconhecida: {nome!r} (valores: {', '.join(sorted(_SUITES))})")
    return _SUITES[nome]


def _verbos_da_suite(suite: Suite) -> set[str]:
    """Todo verbo citado em required_tools — inclusive os de listas-alternativa."""
    verbos: set[str] = set()
    for pergunta in suite.questions:
        for item in pergunta.required_tools:
            verbos.update(item if isinstance(item, tuple) else (item,))
    return verbos


def _negadas(suite: Suite, origem: str) -> list[str]:
    """As tools de `TOOLS` que a suite NAO exige, com o prefixo MCP do host."""
    exigidas = {f"sparkforge_{verbo}" for verbo in _verbos_da_suite(suite)}
    desconhecidas = exigidas - set(TOOLS)
    if desconhecidas:
        raise SystemExit(
            f"{origem} exige tools fora de adapters/tools.TOOLS: {sorted(desconhecidas)}"
        )
    return [f"{MCP_PREFIX}{nome}" for nome in sorted(TOOLS) if nome not in exigidas]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--suite",
        choices=sorted(_SUITES),
        default="fase0",
        help="nome curto da suite (nunca um caminho)",
    )
    parser.add_argument("--runs", "--repeat", dest="repeat", type=int, default=1)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--workspace", type=Path, default=None)
    return parser


@dataclass(frozen=True)
class Plano:
    suite_dir: Path
    workspace: Path
    visible_tools: tuple[str, ...]
    denied_tools: tuple[str, ...]
    runs: int

    def to_dict(self) -> dict:
        return {
            "suite_dir": self.suite_dir.as_posix(),
            "workspace": self.workspace.as_posix(),
            "workspace_dirs": list(WORKSPACE_DIRS),
            "visible_tools": list(self.visible_tools),
            "denied_tools": list(self.denied_tools),
            "runs": self.runs,
        }


def preparar(nome: str, repeat: int, workspace: Path | None) -> Plano:
    suite_dir = _suite_dir(nome)
    suite = load_suite(suite_dir)
    negadas = _negadas(suite, f"suite {nome}")
    visiveis = sorted(set(TOOLS) - {n.removeprefix(MCP_PREFIX) for n in negadas})
    return Plano(
        suite_dir,
        workspace or (ROOT / ".eval-workspace" / nome),
        tuple(visiveis),
        tuple(negadas),
        max(1, repeat),
    )


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    plano = preparar(args.suite, args.repeat, args.workspace)
    print(json.dumps({"status": "ok", "mode": "prepare", "plan": plano.to_dict()},
                     ensure_ascii=False, indent=2, sort_keys=True))
    if not args.prepare_only:
        print(
            "nota: a execucao do agente sob avaliacao e um passo do host; "
            "este runner entrega workspace + contrato (deterministico).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
