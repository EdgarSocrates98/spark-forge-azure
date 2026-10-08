"""Direcao de import do ADR-0001 — medida, nao afirmada.

## Por que este arquivo existe

`docs/architecture/adr/ADR-0001-architecture.md` citava este arquivo como a
prova de que "dependencias so descem" — e ele nao existia. Uma camada que
ninguem mede e prosa; esta medicao e o que faz a arquitetura ser o que e.

## O que e medido (e o que NAO e)

A separacao L0-L8 ideal do ADR tem excecoes reais, medidas abaixo: contratos
agentic consumidos por engines L2 via import preguicoso (`context.gateway`,
`economy.decision_plane`, `receipt.build`). Elas ficam numa lista fechada com
razao — aresta ascendente nova reprova, e a excecao sai daqui so quando a
aresta some do codigo.

O que NAO ha excecao para:

1. **Kernel folha** — `paths`, `durable`, `protocols`, `findings` nao importam
   nada do pacote. Se um contrato precisar de outro modulo, ele subiu de camada
   e a decisao e do ADR, nao de um import escondido.
2. **Dominio Azure** — `azure` e `collectors` so sao alcancados pelas
   superficies (`cli`, `mcp`, `bundle`, `doctor`) ou pelo proprio dominio. Um
   motor ou contrato importando `azure`/`collectors` e exatamente o acoplamento
   que os cortes de aresta do port removeram (`economy→collect`,
   `codeintel→facts` etc. viraram ports).
3. **`collect` e port, `collectors` e implementacao** — `facts`, `case` e
   `economy` falam com o port neutro `collect`; nunca com `collectors` (L6).
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "sparkforge_azure"


def _top_level() -> set[str]:
    nomes = {p.stem for p in PKG.glob("*.py")}
    nomes |= {p.name for p in PKG.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    return nomes


def _arestas() -> dict[str, set[str]]:
    """Import estatico `sparkforge_azure.<sub>` por pacote de primeiro nivel."""
    top = _top_level()
    arestas: dict[str, set[str]] = {}
    for fonte in PKG.rglob("*.py"):
        dono = fonte.relative_to(PKG).parts[0].replace(".py", "")
        if dono == "__init__":
            dono = "__init__"
        try:
            arvore = ast.parse(fonte.read_text(encoding="utf-8"))
        except SyntaxError:  # fixture de recusa nao vive sob o pacote; defesa
            continue
        for no in ast.walk(arvore):
            alvos: list[str] = []
            if isinstance(no, ast.ImportFrom) and no.module:
                alvos = [no.module]
            elif isinstance(no, ast.Import):
                alvos = [a.name for a in no.names]
            for alvo in alvos:
                if alvo.startswith("sparkforge_azure.") and len(alvo.split(".")) > 1:
                    sub = alvo.split(".")[1]
                    if sub in top and sub != dono:
                        arestas.setdefault(dono, set()).add(sub)
    return arestas


ARESTAS = _arestas()

#: Pacotes que nao podem importar NADA do pacote — a folha do kernel (L0/L1).
KERNEL_FOLHA: frozenset[str] = frozenset({"paths", "durable", "protocols", "findings"})

#: Quem pode importar `azure`/`collectors`: as superficies (L7) e o dominio (L5/L6).
DOMINIO: frozenset[str] = frozenset({"azure", "fabric", "collectors"})
SUPERFICIES: frozenset[str] = frozenset({"cli", "mcp", "bundle", "doctor"})

#: Arestas medidas que sobem a camada ideal do ADR — cada uma com a razao.
#: Entrada: (origem, destino) -> por que existe. Remover so quando a aresta
#: sair do codigo; aresta ascendente nova reprova sem entrada aqui.
EXCECOES_MEDIDAS: dict[tuple[str, str], str] = {
    ("context", "agentic"): "gateway aplica TrustLabel/role_plan ao contexto",
    ("economy", "agentic"): "decision_plane consulta AgentGovernor",
    ("economy", "observability"): "ledger emite spans OTel",
    ("receipt", "agentic"): "recibo registra blackboard/executor da execucao agentica",
    ("receipt", "case"): "recibo endereca o case executado",
    ("agents", "adapters"): "autonomy le a lista sfa_* do harness de evals",
    ("adapters", "sdd"): "harness de evals executa os artefatos SDD",
    ("observability", "cli"): "surface lock mede os command_paths da CLI",
    ("observability", "mcp"): "surface lock mede o catalogo de tools",
    ("case", "collect"): "case fala com o port collect (L2), nao com collectors",
    ("facts", "collect"): "facts fala com o port collect (L2), nao com collectors",
    ("agentic", "case"): "executor orquestra o case (fases/store)",
    ("agentic", "decision"): "governor decide sobre o kernel de decisao",
    ("agentic", "economy"): "budget agentico usa o ledger de economia",
    ("agentic", "knowledge_ref"): "rotas de knowledge do executor",
    ("agentic", "registry"): "despacho de especialistas via registro",
    ("agentic", "rules"): "julgamento do executor aplica o catalogo",
    ("agentic", "durable"): "checkpoint do executor e escrita duravel",
    ("context", "agents"): "gateway monta contexto por agente declarado",
    ("context", "codeintel"): "fatias L5 vem do indice de codigo",
    ("context", "economy"): "orcamento de contexto mede custo",
    ("evals", "context"): "o harness mede a camada de contexto",
    ("evals", "decision"): "o harness mede o kernel de decisao",
    ("evals", "economy"): "o harness mede o ledger de economia",
    ("evals", "registry"): "o harness mede o registro canonico",
    ("sdd", "change"): "artefatos SDD encadeiam a mudanca (L1 autonomia)",
    ("sdd", "receipt"): "ship/report referenciam o recibo",
    ("sdd", "case"): "spec roda sobre o case",
    ("sdd", "facts"): "spec referencia facts produzidos",
    ("rules", "packs"): "catalogo aceita regras de packs de terceiro",
    ("knowledge_drift", "facts"): "drift mede citacoes em facts",
    ("knowledge_freshness", "facts"): "frescor liga fonte a fact",
    ("packs", "facts"): "pack de terceiro carrega facts junto das regras",
    ("cli", "azure"): "superficie L7 alcanca o dominio",
    ("cli", "collectors"): "superficie L7 dispara coletores read-only",
    ("cli", "observability"): "cmd_agentops le spans/runs do store de observabilidade",
    ("mcp", "azure"): "superficie MCP alcanca o dominio",
    ("mcp", "collectors"): "tool sfa_collect_* dispara o coletor",
    ("bundle", "collectors"): "offline-bundle embute coleta redigida",
    ("azure", "abfss"): "governance delega a gramatica abfss ao kernel-leaf",
    ("azure", "findings"): "dominio emite o contrato Fact/Finding",
    ("azure", "agentic"): "pipeline envolve metadados do bundle em TrustEnvelope",
    ("azure", "facts"): "pipeline reusa a varredura e o scanner de facts",
    ("azure", "graph"): "pipeline emite o grafo de acesso tipado",
    ("azure", "rules"): "pipeline julga facts com o catalogo SF-ACC",
    ("azure", "observability"): "pipeline emite spans AgentOps por estagio (diagnose.*)",
    ("azure", "knowledgebase"): "pipeline anexa knowledge escopado por failure_layer",
    ("azure", "collectors"): "extract reusa collectors.redact na fronteira do bundle (sem SDK)",
    ("fabric", "azure"): "pipeline reusa Verdict/receipt do dominio azure",
    ("fabric", "findings"): "dominio emite o contrato Fact/Finding",
    ("fabric", "agentic"): "pipeline envolve metadados do bundle em TrustEnvelope",
    ("fabric", "facts"): "pipeline reusa a varredura e o scanner de facts",
    ("fabric", "graph"): "pipeline emite o grafo Fabric tipado",
    ("fabric", "rules"): "pipeline julga facts com o catalogo SF-FAB",
    ("fabric", "observability"): "pipeline emite spans AgentOps por estagio (fabric.*)",
    ("fabric", "knowledgebase"): "pipeline anexa knowledge escopado por failure_layer",
    ("fabric", "collectors"): "extract reusa collectors.redact na fronteira do bundle (sem SDK)",
    ("cli", "fabric"): "superficie L7 alcanca o dominio",
    ("mcp", "fabric"): "superficie MCP alcanca o dominio",
    ("collectors", "findings"): "coletor emite facts/finding do dominio",
    ("collectors", "azure"): "coletor live reusa os extratores do dominio",
    ("collectors", "graph"): "coletor escreve o grafo live do workspace",
    ("collectors", "agentic"): "recover aplica a RecoveryPolicy do executor aos coletores",
    ("graph", "workspace"): "grafo federado compoe o manifest do workspace",
    ("graph", "knowledgebase"): "camada de knowledge do grafo",
    ("graph", "codeintel"): "camada de codigo do grafo",
    ("bundle", "graph"): "bundle embute a fatia do grafo",
    ("bundle", "knowledgebase"): "bundle embute knowledge citado",
    ("doctor", "knowledgebase"): "doctor mede o corpus knowledge",
    ("doctor", "mcp"): "doctor mede o registro de tools",
    ("doctor", "tokensave"): "doctor mede a escada L0-L6",
    ("doctor", "rules"): "doctor mede a integridade do catalogo SF-ACC",
    ("doctor", "collectors"): "doctor mede a fronteira de redacao",
    ("doctor", "paths"): "doctor mede o state dir",
    ("observability", "paths"): "traces.db vive sob state_dir()",
    ("decision", "paths"): "cache de decisao vive sob state_dir()",
    ("cli", "paths"): "agentops le o traces.db via state_dir()",
    ("tokensave", "codeintel"): "a escada L0-L6 usa o indice",
    ("codeintel", "facts"): "indice reusa o scanner de facts",
    ("knowledgebase", "knowledge_ref"): "localizacao dos arquivos knowledge/",
    ("knowledge_engine", "codeintel"): "compiler offline usa o indice",
    ("knowledge_drift", "knowledge_freshness"): "drift consome o estado de frescor",
    ("agentmanifest", "skills"): "manifest declara skills do specialist",
    ("workspace", "codeintel"): "manifest usa o indice do workspace",
    ("paths", "__never__"): "sentinela — paths nao importa nada",
    ("simulate", "findings"): "simulacao emite findings declarados",
    ("simulate", "proof"): "simulacao referencia obrigacoes de prova",
    ("change", "facts"): "mudanca le facts para planejar",
    ("change", "findings"): "mudanca produz findings",
    ("change", "simulate"): "sandbox executa via simulate",
    ("proof", "rules"): "prova deriva obrigacoes do catalogo",
    ("policy", "paths"): "policy resolve caminho confinado",
    ("knowledge_ref", "paths"): "localizacao confinada",
    ("tokensave", "paths"): "leitura confinada",
    ("workspace", "paths"): "manifest confinado",
    ("graph", "paths"): "grafo confinado",
    ("graph", "abfss"): "access graph resolve path de filesystem via kernel-leaf",
    ("economy", "codeintel"): "ledger mede escala do indice",
    ("economy", "collect"): "economia usa o port collect",
    ("economy", "decision"): "ledger informa o kernel de decisao",
    ("economy", "receipt"): "custo registrado no recibo",
    ("economy", "registry"): "rotas de economy via registro",
    ("economy", "rules"): "perfis de economia julgados pelo catalogo",
    ("evals", "facts"): "harness mede extracao",
    ("evals", "findings"): "harness mede validacao",
    ("sdd", "durable"): "artefatos SDD sao escritas duraveis",
    ("sdd", "paths"): "artefatos confinados",
    ("change", "paths"): "sandbox confinado",
    ("agents", "paths"): "despacho confinado",
    ("agents", "registry"): "nomes de especialista via registro canonico",
    ("case", "durable"): "store do case e escrita duravel",
    ("case", "findings"): "o case carrega findings das fases",
    ("case", "rules"): "next_step roteia pelo catalogo routing.yaml",
    ("cli", "bundle"): "verbo offline-bundle",
    ("cli", "doctor"): "verbo doctor",
    ("cli", "graph"): "verbos graph build/query/impact/federate",
    ("cli", "lab"): "verbos lab (dispatch do Forge Lab via cmd_lab)",
    ("cli", "tokensave"): "verbos tokensave L0-L6",
    ("context", "paths"): "fatias confinadas",
    ("facts", "findings"): "facts alimentam o contrato Finding",
    ("knowledgebase", "paths"): "corpus confinado",
    ("mcp", "graph"): "tools sfa_graph_*",
    ("mcp", "paths"): "tool args confinados",
    ("mcp", "tokensave"): "tools sfa_tokensave_*",
    ("mcp", "agentic"): "dispatch anexa envelope de trust ao resultado",
    ("mcp", "observability"): "dispatch grava span da chamada no ledger",
    ("cli", "mcp"): "verbo mcp catalog/serve opera o runtime MCP",
    ("observability", "economy"): "spans medem o ledger de economia",
    ("packs", "paths"): "pack de terceiro confinado",
    ("packs", "rules"): "pack estende o catalogo de regras",
    ("receipt", "findings"): "recibo registra findings da execucao",
    ("rules", "findings"): "regra julgada vira Finding",
    ("rules", "paths"): "catalogo carregado de caminho confinado",
}


def test_kernel_folha_nao_importa_nada_do_pacote():
    """O kernel e folha: se importa, nao e kernel."""
    violacoes = {
        (origem, destino)
        for origem in KERNEL_FOLHA
        for destino in ARESTAS.get(origem, ())
        if destino not in KERNEL_FOLHA
    }
    assert not violacoes, (
        f"pacote folha importando do pacote: {sorted(violacoes)}. "
        f"Contrato/kernel nao resolve nada sozinho — a dependencia nova muda a "
        f"camada do modulo, e isso e decisao de ADR, nao de import."
    )


def test_dominio_so_alcancado_pelas_superficies():
    """Ninguem fora das superficies fala com `azure`/`collectors` direto."""
    violacoes = []
    for origem, destinos in ARESTAS.items():
        if origem in SUPERFICIES or origem in DOMINIO:
            continue
        for destino in destinos & DOMINIO:
            violacoes.append((origem, destino))
    assert not violacoes, (
        f"modulo fora das superficies importando dominio Azure: {violacoes}. "
        f"Esse e o acoplamento que o corte de arestas do port removeu; "
        f"integracao com dominio acontece via port em L2 (ex.: `collect`)."
    )


def test_collectors_nao_e_alcancado_por_port():
    """`collect` e o port neutro; quem fala com ele nao pode pular para `collectors`."""
    violacoes = {
        (origem, "collectors")
        for origem in ("facts", "case", "economy", "codeintel", "decision", "context")
        if "collectors" in ARESTAS.get(origem, ())
    }
    assert not violacoes, (
        f"consumidor do port `collect` importando `collectors` direto: {violacoes}. "
        f"O port existe exatamente para isolar essa dependencia."
    )


def test_toda_aresta_ascendente_esta_declarada():
    """Aresta fora da lista medida reprova — sem excecao silenciosa.

    A lista e grande de proposito: ela e a medicao completa das arestas do
    pacote hoje, e cada aresta nova (em qualquer direcao) passa por aqui.
    """
    todas = {(o, d) for o, ds in ARESTAS.items() for d in ds}
    nao_declaradas = sorted(todas - set(EXCECOES_MEDIDAS))
    assert not nao_declaradas, (
        f"arestas novas entre pacotes sem declaracao nesta medicao: "
        f"{nao_declaradas}. Avalie a camada (ADR-0001) e declare a aresta com "
        f"a razao em EXCECOES_MEDIDAS, ou remova o import."
    )


def test_nenhuma_excecao_declarada_e_fantasma():
    """Excecao sem aresta e receita que envelheceu: medicao mente para baixo."""
    fantasmas = sorted(set(EXCECOES_MEDIDAS) - {(o, d) for o, ds in ARESTAS.items() for d in ds})
    # sentinela de documentacao, nao aresta
    fantasmas = [f for f in fantasmas if f[1] != "__never__"]
    assert not fantasmas, (
        f"excecoes declaradas sem aresta no codigo: {fantasmas}. "
        f"A aresta sumiu — retire a linha para a medicao voltar a ser exata."
    )
