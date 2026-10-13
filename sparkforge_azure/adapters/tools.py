"""A tabela de tools que `scripts/run_agentic_eval.py` expoe ao agente.

Cada chave e um verbo `sparkforge_<nome>` como o gabarito o declara em
`required_tools`; cada valor e uma funcao local que devolve um dict. Nao ha
rede, provider ou escrita: o agente em avaliacao so consulta o que o gate ja
calcula (hoje: os dois verbos do SDD; a tabela cresce quando outra suite
declarar um verbo novo em `required_tools`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from sparkforge_azure.sdd.checks import check as _check
from sparkforge_azure.sdd.status import status as _status


def sparkforge_sdd_check(repo: str = ".", root: str = "docs/sdd") -> dict[str, Any]:
    """`check()` do SDD sobre `repo/root`: recusas e lacunas nomeadas."""
    return _check(Path(repo), root=root)


def sparkforge_sdd_status(repo: str = ".", root: str = "docs/sdd") -> dict[str, Any]:
    """`status()` do SDD sobre `repo/root`: a fase de cada feature."""
    return _status(Path(repo), root=root)


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "sparkforge_sdd_check": sparkforge_sdd_check,
    "sparkforge_sdd_status": sparkforge_sdd_status,
}


__all__ = ["TOOLS", "sparkforge_sdd_check", "sparkforge_sdd_status"]
