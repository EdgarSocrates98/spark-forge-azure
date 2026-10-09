#!/usr/bin/env python3
"""Gate de recall e economia do `ContextPack` — adaptacao Azure.

Mesmo contrato do irmao AWS (`scripts/check_recall_economy.py`), tres
compromissos identicos:

- **DECIDE recall nominal.** Perguntado pelo nome do simbolo, o pack tem de
  entregar aquele simbolo. Piso duro em 100% — sem excecao silenciosa.
- **REPORTA recall conceitual, sem piso.** O titulo da regra descreve o
  defeito; o indice guarda nome. A ponte entre os dois nao esta prometida.
- **RECUSA publicar razao de economia em corpus inadequado.** Uma razao medida
  sobre corpus menor que o envelope do pack mede o piso do envelope, nao a
  economia do subsistema.

## O que e diferente aqui — e por que e honesto, nao copiado

`PISO_DE_PERGUNTAS` no AWS e 27 porque la existem 27 pares (fixture, regra)
com `input/` indexavel e `expected/findings.json` ancorado em simbolo `.py`.
A primeira passagem do gate aqui derivava **0 perguntas** — os fixtures de
dominio (`fixtures/synthetic/*`, `tests/fixtures/*`) ancoram subjects de
stage/file. Em vez de herdar um piso estrangeiro ou publicar 0/0 como sucesso,
este ciclo gerou `expected/` real para `fixtures/pyspark/*` com o extrator
`pyspark_ast` + judge do catalogo `SF-PY-*`: 12 perguntas derivaveis, piso 12.

- `PISO_DE_PERGUNTAS = 12`. Cair significa que alguma regra SF-PY perdeu
  ancoragem; subir exige fixture nova com evidence de simbolo e sobe no mesmo
  commit.
- `SEM_RECALL` segue vazio: se alguma pergunta falhar nominal, ela e defeito
  ate ser declarada com razao + medida que destrava.
- `economia` sai `unresolved` se o corpus total nao exceder o envelope fixo —
  12 fixtures de ~70 bytes de input nao pagam 747 bytes de envelope; a razao
  de economia honesta precisa de corpus maior ou da medicao sobre a arvore do
  proprio repositorio.
- O gate falha nas DUAS direcoes como no AWS: recall baixo fora de
  `SEM_RECALL`, e item de `SEM_RECALL` que passou (recusa curada nao removida
  e afirmacao falsa sobre o estado do sistema).

`ENVELOPE_FIXO_BYTES` foi medido aqui, nao herdado: `montar()` sobre um indice
de fixture minima devolve 747 bytes de estrutura fixa (chaves `index`, `query`,
`metrics`, `security`, `unresolved`, `reductions`, `relationships`, `lineage`,
`snippets`, `schema_version`, `runtime`, `rules`) antes de qualquer simbolo
entrar. O numero AWS e 840 porque o pack de la tem menos chaves.

Uso:

    python scripts/check_recall_economy.py            # relatorio + gate
    python scripts/check_recall_economy.py --json     # so o JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sparkforge_azure.economy.goldset import derivar_goldset, fora_do_alcance  # noqa: E402
from sparkforge_azure.economy.recall import medir  # noqa: E402

# Piso de perguntas derivadas. 12 fixtures em `fixtures/pyspark/*` produzem
# `expected/` com evidence ancorada em simbolo `.py` (geradas pelo extrator +
# judge reais, nao escritas a mao). E PISO, nao igualdade: quem adicionar
# fixture ancorada sobe o piso no mesmo commit, como no irmao AWS.
PISO_DE_PERGUNTAS = 12

# Recall nominal e 100% sobre o que existir — sem excecao silenciosa.
RECALL_EXIGIDO = 1.0

# Recusas NOMEADAS, no molde do irmao AWS. Chave `<rule_id>@<fixture>`, valor
# `(razao, medida que destravaria)`. O gate falha nas duas direcoes.
SEM_RECALL: dict[str, tuple[str, str]] = {}

# Envelope fixo do pack, medido neste repositorio sobre indice de fixture
# minima: `index`, `query`, `metrics`, `security`, `unresolved`, `reductions`,
# `relationships`, `lineage`, `snippets`, `schema_version`, `runtime` e
# `rules` somam isto antes de qualquer simbolo entrar.
ENVELOPE_FIXO_BYTES = 747


def _relatorio() -> dict:
    perguntas = derivar_goldset()
    medidas = medir(perguntas)
    fora = fora_do_alcance()

    falhas_nominais = [m for m in medidas if not m.respondeu]
    curadas = [
        chave
        for chave in SEM_RECALL
        if any(m.chave == chave and m.respondeu for m in medidas)
    ]

    corpus_bytes = sum(m.bytes_arquivos for m in medidas)
    medivel = corpus_bytes > ENVELOPE_FIXO_BYTES * len(medidas) > 0

    economia: dict[str, object] = {
        "bytes_pack": sum(m.bytes_pack for m in medidas),
        "bytes_arquivos": corpus_bytes,
        "bytes_grep": sum(m.bytes_grep for m in medidas),
        "bytes_por_nivel": {
            nivel: sum(m.bytes_por_nivel.get(nivel, 0) for m in medidas)
            for nivel in ("None", "summary", "full")
        },
        "envelope_fixo_bytes": ENVELOPE_FIXO_BYTES,
    }
    if not medivel:
        limiar = ENVELOPE_FIXO_BYTES * len(medidas)
        economia["limiar_bytes"] = limiar
        if not medidas:
            economia["razao_unresolved"] = (
                "economia.unresolved -- o gold set deste repositorio deriva 0 "
                "perguntas: os fixtures ancoram subjects de stage/file e os "
                "input/ carregam facts.json, nao fonte indexavel. Sem corpus "
                "nao ha denominador; uma razao aqui mediria o envelope vazio."
            )
            economia["medida_que_destravaria"] = (
                "fixture com `input/` de arquivos .py/.sql indexaveis E "
                "`expected/findings.json` cuja evidence nomeie simbolo "
                "presente nesses arquivos -- o que `goldset._casos` ja "
                "reconhece quando existe"
            )
        else:
            economia["razao_unresolved"] = (
                f"economia.unresolved -- o corpus do gold set tem "
                f"{corpus_bytes} bytes em {len(medidas)} fixtures, e o "
                f"envelope fixo do pack custa {ENVELOPE_FIXO_BYTES} bytes por "
                f"chamada, {limiar} no total. Com {corpus_bytes} < {limiar}, "
                "o pack nao pode custar menos que ler o corpus, porque o "
                "envelope sozinho ja o excede. Uma razao daqui mede o piso do "
                "envelope, nao a economia do subsistema."
            )
            economia["medida_que_destravaria"] = (
                "um corpus por fixture maior que o envelope -- ou a mesma "
                "medicao sobre a arvore do repositorio"
            )
    else:
        economia["contra_arquivos"] = round(
            corpus_bytes / max(economia["bytes_pack"], 1), 2
        )
        economia["contra_grep"] = round(
            economia["bytes_pack"] / max(economia["bytes_grep"], 1), 2
        )

    goldset_estado = (
        "derivado" if perguntas
        else "unresolved: 0 perguntas derivaveis -- fixtures sem ancora de "
             "simbolo indexavel (subjects de stage/file, input/ com facts.json)"
    )
    return {
        "goldset": goldset_estado,
        "perguntas": len(perguntas),
        "piso_de_perguntas": PISO_DE_PERGUNTAS,
        "regras_cobertas": len({p.rule_id for p in perguntas}),
        "recall_nominal": (
            {
                "exigido": RECALL_EXIGIDO,
                "passou": len(medidas) - len(falhas_nominais),
                "de": len(medidas),
                "falhas": [
                    {"chave": m.chave, "faltaram": list(m.faltaram), "erro": m.erro}
                    for m in falhas_nominais
                ],
            }
            if medidas
            else {"unresolved": "gold set vazio -- 0/0 nao e 100%"}
        ),
        "recall_conceitual": (
            {
                "piso": None,
                "passou": sum(1 for m in medidas if m.respondeu_conceitual),
                "de": len(medidas),
            }
            if medidas
            else {"unresolved": "gold set vazio"}
        ),
        "economia": economia,
        "recusas_curadas": curadas,
        "fora_do_alcance": [
            {
                "chave": f"{f.rule_id}@{f.fixture}",
                "razao": f.razao,
                "extensoes": list(f.extensoes),
                "medida_que_destravaria": f.medida_que_destravaria,
            }
            for f in fora
        ],
    }


def _imprimir(rel: dict) -> None:
    print(f"goldset ...................... {rel['goldset']}")
    print(f"perguntas derivadas .......... {rel['perguntas']} (piso {rel['piso_de_perguntas']})")
    print(f"regras cobertas .............. {rel['regras_cobertas']}")
    n = rel["recall_nominal"]
    if "unresolved" in n:
        print(f"recall NOMINAL ............... UNRESOLVED ({n['unresolved']})")
    else:
        print(f"recall NOMINAL (piso duro) ... {n['passou']}/{n['de']}")
    c = rel["recall_conceitual"]
    if "unresolved" in c:
        print("recall CONCEITUAL ............ UNRESOLVED")
    else:
        print(f"recall CONCEITUAL (sem piso) . {c['passou']}/{c['de']}")
    e = rel["economia"]
    if "razao_unresolved" in e:
        print("economia ..................... UNRESOLVED")
        print(f"  razao: {e['razao_unresolved']}")
        print(f"  destrava: {e['medida_que_destravaria']}")
    else:
        print(f"economia vs arquivos ......... {e['contra_arquivos']}x")
        print(f"economia vs grep ............. {e['contra_grep']}x")
    niveis = e["bytes_por_nivel"]
    print(f"bytes por detail_level ....... {niveis}")
    fora = rel["fora_do_alcance"]
    if fora:
        por_razao: dict[str, int] = {}
        for item in fora:
            por_razao[item["razao"]] = por_razao.get(item["razao"], 0) + 1
        print(f"fora do alcance .............. {len(fora)} {por_razao}")
    if "falhas" in n:
        for falha in n["falhas"]:
            print(f"  FALHA {falha['chave']}: {falha['erro'] or falha['faltaram']}")
    for chave in rel["recusas_curadas"]:
        print(f"  RECUSA CURADA (remova de SEM_RECALL): {chave}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="so o JSON")
    args = parser.parse_args()

    rel = _relatorio()
    if args.json:
        print(json.dumps(rel, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _imprimir(rel)

    problemas = 0
    if rel["perguntas"] < rel["piso_de_perguntas"]:
        print(
            f"\nERRO: {rel['perguntas']} perguntas, piso {rel['piso_de_perguntas']}. "
            "Alguma regra perdeu ancoragem de simbolo.",
            file=sys.stderr,
        )
        problemas += 1
    nominal = rel["recall_nominal"]
    for falha in nominal.get("falhas", []):
        if falha["chave"] not in SEM_RECALL:
            print(
                f"\nERRO: recall nominal falhou em {falha['chave']} e ela NAO esta "
                "em SEM_RECALL. Ou o funil regrediu, ou a recusa precisa ser "
                "declarada com a razao e a medida que a destravaria.",
                file=sys.stderr,
            )
            problemas += 1
    for chave in rel["recusas_curadas"]:
        print(
            f"\nERRO: {chave} esta em SEM_RECALL e PASSOU. Recusa que curou e "
            "afirmacao falsa sobre o estado do sistema -- remova a entrada.",
            file=sys.stderr,
        )
        problemas += 1

    if not args.json:
        print(f"\n{problemas} problema(s).")
    else:
        print(f"{problemas} problema(s).", file=sys.stderr)
    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
