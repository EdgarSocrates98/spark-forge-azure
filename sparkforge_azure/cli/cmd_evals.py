"""``sparkforge-azure evals <op>`` — §7.2 evals surface (install-2.0 lf-0038).

``evals.list/describe/run/result`` sobre a taxonomia classificada de
``sparkforge_azure.evals.taxonomy``. Suites que so um host executa
recusam ``EVALS-REQUIRES-HOST`` — a CLI nunca incorpora o executor
(§7.3). Gabaritos selados nunca sao emitidos: list/describe carregam
metadados e sha256, nunca respostas.
"""

from __future__ import annotations

import argparse
from typing import Any

from sparkforge_azure.cli.main import CliError


def _call(a: argparse.Namespace) -> dict[str, Any]:
    # importlib: o runtime nao pode depender estaticamente da avaliacao
    # (test_harness_boundary); o adapter carrega o pacote como plugin —
    # mesmo padrao de `mcp/tools.py:load_all`.
    import importlib

    surface = importlib.import_module("sparkforge_azure.evals.surface")
    taxonomy = importlib.import_module("sparkforge_azure.evals.taxonomy")

    try:
        if a.evals_action == "list":
            return taxonomy.listing()
        if a.evals_action == "describe":
            return taxonomy.describe(a.suite)
        if a.evals_action == "run":
            return surface.run(a.suite)
        if a.evals_action == "result":
            return surface.result(a.suite, a.run)
    except taxonomy.TaxonomyError as exc:
        raise CliError(str(exc)) from exc
    raise CliError(f"evals action desconhecida: {a.evals_action}")


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "evals",
        help=(
            "Inventario classificado e execucao das suites de avaliacao "
            "(§7.1/§7.2): developer, runtime-decision, output-verification, "
            "host-conformance. Gabaritos selados nunca sao emitidos."
        ),
    )
    s = p.add_subparsers(dest="evals_action", metavar="<op>")
    s.required = True

    s.add_parser(
        "list", help="evals.list (§7.2): suites classificadas por categoria."
    ).set_defaults(func=_call)

    q = s.add_parser(
        "describe",
        help="evals.describe (§7.2): categoria, ambiente, selagem e sha256.",
    )
    q.add_argument("--suite", required=True)
    q.set_defaults(func=_call)

    q = s.add_parser(
        "run",
        help=(
            "evals.run (§7.2): executa o runner deterministico da suite; "
            "suites de host recusam EVALS-REQUIRES-HOST."
        ),
    )
    q.add_argument("--suite", required=True)
    q.set_defaults(func=_call)

    q = s.add_parser(
        "result",
        help="evals.result (§7.2): scorecard de uma execucao de host gravada.",
    )
    q.add_argument("--suite", required=True)
    q.add_argument("--run", required=True)
    q.set_defaults(func=_call)
