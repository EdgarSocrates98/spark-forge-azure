"""Refresh das fontes de `knowledge/` e `rules/` — confere hashes e relata o drift.

Sem rede por padrao: `--report` so le o lock e o catalogo e imprime o estado.
`--update` baixa cada URL nao-pinada, compara `sha256` com o lock e atualiza
`checked_at`/`changed_at` — e o unico modo que toca rede ou reescreve o lock.

O relatorio sempre termina com a secao "## Impacto" do Knowledge Drift Radar
(`sparkforge_azure/knowledge_drift.render_markdown`) quando ha lock para
cruzar: fonte que mudou arrasta regra, golden, eval, agente e skill.

Uso:
    python scripts/refresh_knowledge.py --report [--as-of 2026-10-07]
    python scripts/refresh_knowledge.py --update [--only URL] [--timeout 20]

Sai com 0 sempre no modo --report (drift e informacao, nao falha); com 1 em
--update quando uma URL nao pode ser conferida.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sparkforge_azure.knowledge_drift import (  # noqa: E402
    build_index,
    drift,
    render_markdown,
    repo_root,
)
from sparkforge_azure.knowledge_freshness import (  # noqa: E402
    LOCK_NAME,
    carregar_lock,
    fontes_de_knowledge,
)
from sparkforge_azure.rules.loader import catalog_dir, load_catalog  # noqa: E402

KNOWLEDGE = ROOT / "knowledge"
LOCK_PATH = KNOWLEDGE / LOCK_NAME


def _carregar_fontes() -> tuple[dict[str, dict], dict[str, dict[str, list[str]]]]:
    """`por_url` (formato do lock) e `por_doc` (datas por documento)."""
    return fontes_de_knowledge(KNOWLEDGE)


def _carregar_regras() -> list[dict[str, Any]]:
    try:
        base = catalog_dir()
    except Exception:
        return []
    if base is None or not Path(base).is_dir():
        return []
    try:
        return load_catalog(Path(base))
    except Exception:
        return []


def _buscar(url: str, timeout: int) -> tuple[str | None, str | None]:
    """`(sha256, None)` da pagina, ou `(None, motivo)`. So GET, so HTTPS/HTTP."""
    if not url.startswith(("https://", "http://")):
        return None, "esquema_nao_suportado"
    try:
        request = urllib.request.Request(  # noqa: S310 - esquema limitado a http(s) acima
            url, headers={"User-Agent": "sparkforge-azure-refresh/0.1"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as resposta:  # noqa: S310
            return hashlib.sha256(resposta.read()).hexdigest(), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _atualizar(only: str | None, timeout: int, as_of: date) -> tuple[int, list[dict[str, Any]]]:
    """Confere cada URL do lock que nao e `pinned` e regrava `changed_at`."""
    lock, motivo = carregar_lock(KNOWLEDGE)
    if lock is None:
        print(json.dumps({"ok": False, "error": f"lock: {motivo}"}, ensure_ascii=False))
        return 1, []
    por_url, _por_doc = _carregar_fontes()
    hoje = as_of.isoformat()
    linhas: list[dict[str, Any]] = []
    falhas = 0
    for url, entrada in sorted(lock.items()):
        if only is not None and url != only:
            continue
        if entrada.get("pinned"):
            linhas.append({"url": url, "state": "pinned", "changed": False})
            continue
        sha, erro = _buscar(url, timeout)
        if sha is None:
            falhas += 1
            linhas.append({"url": url, "state": "unresolved", "reason": erro})
            continue
        mudou = bool(entrada.get("sha256")) and entrada["sha256"] != sha
        entrada["checked_at"] = hoje
        if mudou:
            entrada["changed_at"] = hoje
        entrada["sha256"] = sha
        linhas.append({"url": url, "state": "fresh", "changed": mudou})
    bruto = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    bruto["sources"] = dict(lock)
    bruto["refreshed_at"] = hoje
    LOCK_PATH.write_text(json.dumps(bruto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return falhas, linhas


def render_report(
    checked: list[dict[str, Any]],
    lock: dict[str, Any] | None,
    as_of: str,
    drift_payload: dict[str, Any] | None = None,
) -> str:
    """O relatorio de uma rodada de refresh (texto, nao JSON — vai para CI/PR)."""
    linhas = ["# Refresh das fontes de knowledge", "", f"Data de referencia: {as_of}.", ""]
    if checked:
        linhas.append("## Conferidas nesta rodada")
        linhas.append("")
        for item in checked:
            detalhe = item.get("reason") or ("mudou" if item.get("changed") else "inalterada")
            linhas.append(f"- {item['url']}: `{item['state']}` ({detalhe})")
        linhas.append("")
    if lock is not None:
        pinadas = sum(1 for e in lock.values() if isinstance(e, dict) and e.get("pinned"))
        linhas += [
            "## Lock",
            "",
            f"Fontes vigiadas: {len(lock)} ({pinadas} fixadas por versao).",
            "",
        ]
    if drift_payload is not None:
        linhas.append(render_markdown(drift_payload))
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--report", action="store_true", help="so le o lock e relata (padrao)")
    modos.add_argument("--update", action="store_true", help="baixa e confere hashes (rede)")
    parser.add_argument("--only", type=str, default=None, help="limita --update a uma URL")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = parser.parse_args(argv)
    as_of = args.as_of or datetime.now(timezone.utc).date()

    falhas, checked = (0, [])
    if args.update:
        falhas, checked = _atualizar(args.only, args.timeout, as_of)

    lock, motivo = carregar_lock(KNOWLEDGE)
    payload = None
    if lock is not None:
        raiz = repo_root()
        indice = build_index(raiz) if raiz is not None else None
        _por_url, por_doc = _carregar_fontes()
        payload = drift(lock, motivo, _carregar_regras(), por_doc, indice, as_of)

    print(render_report(checked, lock, as_of.isoformat(), payload))
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
