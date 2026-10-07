"""Testes de `run_executor` -- a orquestracao da secao 7 do spec.

## Os tres invariantes, e por que cada um tem teste proprio

- **Medicao nunca derruba a chamada (regra 27).** Blackboard indisponivel nao
  impede a resposta do verbo. O teste aponta `root` para um ARQUIVO, que e a
  forma mais barata de ter um blackboard impossivel de escrever sem depender de
  permissao de sistema de arquivos, que varia entre Windows e Linux.
- **O score de arbitragem nao sai publicado.** Os pesos de `assess_claim`
  (40/30/20/10) sao convencao sem calibracao, e o `CLAUDE.md` diz isso por
  escrito. A varredura e por SUBSTRING sobre o JSON inteiro da resposta, e nao
  por chave: `independence_score` viajaria numa chave que ninguem procuraria, e
  a frase de `ArbitrationResult.reasoning` traz o numero no meio do texto.
- **Toda `Decision` tem `rollback` nao vazio.** `make_decision` ja recusa sem
  ele; este teste garante que o executor nao contorna a recusa passando espaco
  em branco.

## A uniao dos facts, e por que o teste a monta

A secao 12.9 do spec mediu que `expected/facts.json` guarda **apenas o que o
extrator daquele dominio emite**, enquanto `expected/findings.json` e o
julgamento sobre a UNIAO de entrada e derivados. Alimentar o executor com o
subconjunto fabrica claim desancorada que a execucao real nao produz.

Os ids do `input/facts.json` nao vem no artefato -- eles sao computados por
`Fact.id`, que e content-addressed sobre kind, subject e measures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from sparkforge_azure.agentic.blackboard import (
    read_claims,
    read_contradictions,
    read_decisions,
    read_objections,
)
from sparkforge_azure.agentic.executor import run_executor
from sparkforge_azure.findings.models import Fact

RAIZ = Path(__file__).resolve().parents[1]
CASO_DE_FIXTURE = RAIZ / "fixtures" / "synthetic" / "azure_timeout_spill_skew"

# O runtime que a secao 12.8 usou para medir a distribuicao de `confidence`
# sobre o corpus. Fixo aqui pela mesma razao: runtime diferente muda o escopo de
# versao, e com ele a confianca -- o teste mediria outra coisa a cada vez.
RUNTIME = {"databricks_runtime": "15.4", "spark": "3.5.0"}

_URL_SPARK_CONF = "https://learn.microsoft.com/en-us/azure/databricks/compute/configure"
_URL_SPARK = "https://spark.apache.org/docs/latest/tuning.html"
_URL_JOBS = "https://learn.microsoft.com/en-us/azure/databricks/jobs/compute"
_URL_LIBRARIES = "https://learn.microsoft.com/en-us/azure/databricks/libraries/cluster-libraries"
_URL_ALLOWLIST = (
    "https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/"
    "manage-privileges/allowlist"
)


# --------------------------------------------------------------------------
# Insumos
# --------------------------------------------------------------------------


def _lista(documento: Any, chave: str) -> list[dict]:
    return documento if isinstance(documento, list) else documento.get(chave, [])


def _carrega(caminho: Path, chave: str) -> list[dict]:
    return _lista(json.loads(caminho.read_text(encoding="utf-8")), chave)


def _com_id(facts: list[dict]) -> list[dict]:
    """Os facts de `input/`, com o `id` que `Fact.id` computa.

    O artefato de entrada nao carrega id: ele e derivado do conteudo na hora em
    que o motor constroi o `Fact`. Escrever o id a mao no teste o congelaria, e
    a fixture e o teste divergiriam no dia em que uma medida mudasse.
    """
    saida: list[dict] = []
    for bruto in facts:
        if not isinstance(bruto, dict):
            continue
        if bruto.get("id"):
            saida.append(bruto)
            continue
        fact = Fact(
            kind=str(bruto.get("kind") or ""),
            subject=bruto.get("subject") or {},
            measures=bruto.get("measures") or {},
            attrs=bruto.get("attrs") or {},
            provenance=bruto.get("provenance") or {},
        )
        saida.append({**bruto, "id": fact.id})
    return saida


def uniao_de_facts(caso: Path) -> list[dict]:
    """A uniao dos facts do case -- `input/` mais `expected/`, sem repetir id.

    E o conjunto que `judge` recebeu para produzir aqueles findings, e por isso
    e o conjunto que o executor recebe (secao 12.9 do spec).
    """
    entrada = caso / "input" / "facts.json"
    esperados = caso / "expected" / "facts.json"
    brutos = _com_id(_carrega(entrada, "facts")) if entrada.exists() else []
    brutos += _carrega(esperados, "facts") if esperados.exists() else []

    vistos: set[str] = set()
    uniao: list[dict] = []
    for fact in brutos:
        fact_id = str(fact.get("id") or "").strip()
        if fact_id and fact_id not in vistos:
            vistos.add(fact_id)
            uniao.append(fact)
    return uniao


def _fact(kind: str, fact_id: str, **attrs: Any) -> dict[str, Any]:
    return {"id": fact_id, "kind": kind, "subject": {}, "measures": {}, "attrs": dict(attrs)}


def _texto(resposta: dict[str, Any]) -> str:
    return json.dumps(resposta, ensure_ascii=False, sort_keys=True)


def _par_de_contradicao() -> tuple[list[dict], list[dict]]:
    """Par de contradicao DIRETA, sintetico e Azure-nativo.

    No AWS este par vinha do catalogo (`SF-GRAPH-005` x `SF-LF-001`). O catalogo
    AWS nao e portado, e o par Azure equivalente e de plataforma documentada:
    um lado manda declarar o JAR de GraphFrames nas bibliotecas do cluster; o
    outro manda remove-lo, porque cluster Unity Catalog em access mode standard
    (antes "shared") so carrega JAR que esteja na allowlist do metastore. Mesmo
    `target`, direcoes `add` e `remove`, as duas ancoradas em Microsoft Learn.
    """
    facts = [
        _fact("databricks.cluster", "f_lib001", library="graphframes"),
        _fact("unity_catalog.access_mode", "f_uc0001", access_mode="standard"),
    ]
    findings = [
        {
            "rule_id": "SFA-LIB-001",
            "title": "Biblioteca usada pelo job nao declarada no cluster",
            "severity": "P1",
            "subject": {"type": "job", "symbol": "etl_grafo"},
            "evidence": ["f_lib001"],
            "runtime_scope": {},
            "sources": [{"url": _URL_LIBRARIES, "retrieved": "2026-10-06"}],
            "action": {
                "kind": "dependency.declare_in_iac",
                "target": "databricks.cluster.libraries",
                "direction": "add",
                "requires_absent": [],
                "moves": ["dependency.delivered_artifacts"],
                "depends_on": [],
            },
            "validation": ["executar o job e confirmar que ele passa do import"],
            "risks": ["JAR compilado contra outro minor de Spark falha em producao"],
        },
        {
            "rule_id": "SFA-UC-001",
            "title": "JAR fora da allowlist em cluster Unity Catalog access mode standard",
            "severity": "P1",
            "subject": {"type": "job", "symbol": "etl_grafo"},
            "evidence": ["f_uc0001"],
            "runtime_scope": {},
            "sources": [{"url": _URL_ALLOWLIST, "retrieved": "2026-10-06"}],
            "action": {
                "kind": "dependency.remove_library",
                "target": "databricks.cluster.libraries",
                "direction": "remove",
                "requires_absent": [],
                "moves": ["dependency.delivered_artifacts", "correctness.write_result"],
                "depends_on": [],
            },
            "validation": ["job roda de ponta a ponta no cluster alvo, sobre dado real"],
            "risks": ["trocar o access mode para manter o JAR afrouxa o controle de acesso"],
        },
    ]
    return findings, facts


# --------------------------------------------------------------------------
# Case real de fixture
# --------------------------------------------------------------------------


def test_case_de_fixture_produz_uma_claim_por_finding(tmp_path: Path) -> None:
    """Um finding julgado -> uma claim gravada. Sem inflar, sem perder.

    A contagem e conferida contra o arquivo, e nao contra um numero escrito a
    mao: a fixture pode ganhar finding, e o invariante e a igualdade.
    """
    findings = _carrega(CASO_DE_FIXTURE / "expected" / "findings.json", "findings")
    facts = uniao_de_facts(CASO_DE_FIXTURE)

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["persisted"] is True
    assert len(resposta["claims"]) == len(findings)
    assert len(read_claims(tmp_path)) == len(findings)
    assert {c["claimant"] for c in resposta["claims"]} == {f["rule_id"] for f in findings}


def test_case_de_fixture_com_uniao_nao_produz_claim_desancorada(tmp_path: Path) -> None:
    """A secao 12.9, travada como teste.

    Com o subconjunto `expected/facts.json`, um finding desta fixture aparece
    citando fact que "nao esta no case" -- e ele esta, no `input/`. Com a uniao,
    nenhum `Unknown` de ancora ausente sai.
    """
    findings = _carrega(CASO_DE_FIXTURE / "expected" / "findings.json", "findings")

    so_esperados = run_executor(
        findings,
        _carrega(CASO_DE_FIXTURE / "expected" / "facts.json", "facts"),
        tmp_path / "subconjunto",
        runtime=RUNTIME,
    )
    com_uniao = run_executor(
        findings, uniao_de_facts(CASO_DE_FIXTURE), tmp_path / "uniao", runtime=RUNTIME
    )

    desancoradas = [u for u in so_esperados["unknowns"] if u["question"].startswith("finding ")]
    assert desancoradas, "a fixture perdeu o contrafactual que a secao 12.9 mediu"
    assert not [u for u in com_uniao["unknowns"] if u["question"].startswith("finding ")]


def test_a_ordem_sai_com_todas_as_regras_que_propoem_acao(tmp_path: Path) -> None:
    """A ordem e a decisao 4 do spec, e ela viaja na resposta."""
    findings = _carrega(CASO_DE_FIXTURE / "expected" / "findings.json", "findings")

    resposta = run_executor(findings, uniao_de_facts(CASO_DE_FIXTURE), tmp_path, runtime=RUNTIME)

    com_acao = {f["rule_id"] for f in findings if f.get("action")}
    assert set(resposta["order"]["sequence"]) == com_acao
    assert resposta["order"]["unresolved"] == {}


# --------------------------------------------------------------------------
# Revisao
# --------------------------------------------------------------------------


def test_segunda_execucao_com_facts_novos_registra_revisao(tmp_path: Path) -> None:
    """`Claim.id` cobre `evidence_refs` desde a auditoria de 2026-09-03.

    Antes daquela correcao a mesma afirmacao sustentada por evidencia nova
    colidia com a versao anterior e o blackboard a recusava como duplicata --
    nao havia como registrar revisao nenhuma. Aqui o segundo run ve o mesmo
    finding com uma ancora a mais, e o que sai e claim NOVA apontando para a
    anterior por `supersedes`.
    """
    finding = {
        "rule_id": "SF-UI-001",
        "title": "Skew de duracao de task no stage",
        "subject": {"type": "stage", "symbol": "stage-4"},
        "evidence": ["f_aaa111"],
        "runtime_scope": {},
        "sources": [{"url": _URL_SPARK, "retrieved": "2026-08-01"}],
    }
    primeiro = run_executor(
        [finding], [_fact("spark.stage.task_duration", "f_aaa111")], tmp_path, runtime=RUNTIME
    )

    revisado = {**finding, "evidence": ["f_aaa111", "f_bbb222"]}
    segundo = run_executor(
        [revisado],
        [_fact("spark.stage.task_duration", "f_aaa111"), _fact("spark.stage.spill", "f_bbb222")],
        tmp_path,
        runtime=RUNTIME,
    )

    assert segundo["persisted"] is True
    anterior = primeiro["claims"][0]
    nova = segundo["claims"][0]
    assert nova["id"] != anterior["id"]
    assert nova["supersedes"] == anterior["id"]
    assert len(read_claims(tmp_path)) == 2


def test_segunda_execucao_identica_nao_colide_nem_duplica(tmp_path: Path) -> None:
    """Mesma entrada, segunda vez: nada de novo, e nada quebrado.

    Registrar `supersedes` aqui seria mentira -- nada foi revisto. E deixar o
    append levantar por duplicata transformaria idempotencia em falha. A saida e
    a terceira: a claim ja esta gravada, o run a reconhece e nao a escreve outra
    vez.
    """
    findings = _carrega(CASO_DE_FIXTURE / "expected" / "findings.json", "findings")
    facts = uniao_de_facts(CASO_DE_FIXTURE)

    primeiro = run_executor(findings, facts, tmp_path, runtime=RUNTIME)
    segundo = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert segundo["persisted"] is True
    assert [c["id"] for c in segundo["claims"]] == [c["id"] for c in primeiro["claims"]]
    assert all(c["supersedes"] is None for c in segundo["claims"])
    assert len(read_claims(tmp_path)) == len(findings)


# --------------------------------------------------------------------------
# Contradicao direta -- o par real do catalogo
# --------------------------------------------------------------------------


def test_par_real_de_contradicao_sai_com_decisao_ou_plano(tmp_path: Path) -> None:
    """`SFA-LIB-001` x `SFA-UC-001`: contradicao gravada, e um desfecho nomeado.

    O teste aceita os DOIS desfechos de proposito. Qual deles sai depende de
    como a arbitragem ordena as duas claims, e fixar um aqui congelaria uma
    convencao nao calibrada como se fosse contrato. O que e contrato: a
    contradicao e gravada, e ou existe decisao com rollback ou existe plano de
    debate -- nunca vencedor sem nenhum dos dois.

    As duas regras citam documentacao oficial (Microsoft Learn), as duas estao
    ancoradas, e o que esta medido no case nao separa uma da outra.
    """
    findings, facts = _par_de_contradicao()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["contradictions"], "o par real do catalogo nao produziu contradicao"
    contradicao = resposta["contradictions"][0]
    assert contradicao["target"] == "databricks.cluster.libraries"
    assert sorted(contradicao["rules"]) == ["SFA-LIB-001", "SFA-UC-001"]
    assert len(read_contradictions(tmp_path)) == len(resposta["contradictions"])

    fechou = bool(resposta["decisions"])
    parou = bool(resposta["debate_plans"])
    assert fechou != parou, "o par tem que fechar por decisao OU parar por plano, nunca os dois"
    if parou:
        plano = resposta["debate_plans"][0]
        assert plano["plan"]["executed"] is False
        assert plano["plan"]["unresolved"]["reason"] == "debate.unresolved"


def test_a_contradicao_nomeia_as_ancoras_dos_dois_lados(tmp_path: Path) -> None:
    """A secao 4 exige os `fact.id` dos dois lados.

    `Contradiction` liga dois claim_id e nao tem campo de fact; a descricao e
    onde as ancoras cabem. Sem elas, quem lesse o relatorio nao teria como
    conferir de que medida cada lado saiu.
    """
    findings, facts = _par_de_contradicao()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    descricao = resposta["contradictions"][0]["description"]
    assert "f_lib001" in descricao
    assert "f_uc0001" in descricao


def _par_que_fecha() -> tuple[list[dict], list[dict]]:
    """Um par cuja arbitragem FECHA, e por que ele e sintetico.

    O par de contradicao direta (`SFA-LIB-001` x `SFA-UC-001`)
    sai `recommendation: experiment` -- as duas regras citam documentacao
    oficial, as duas estao ancoradas, e o que esta medido no case nao
    separa uma da outra. O desfecho e correto e o teste acima o aceita; mas com
    ele so, todo teste sobre `Decision` ficaria VAZIO, passando sem exercitar
    nada. Um par com lastro desigual -- um lado com duas fontes T1 ancoradas, o
    outro sem fonte nenhuma e com a ancora ausente -- e o que exercita o ramo.
    """
    findings = [
        {
            "rule_id": "SFA-DBX-001",
            "title": "Capacidade insuficiente para o SLA declarado",
            "subject": {"type": "job", "symbol": "etl_pedidos"},
            "evidence": ["f_run001"],
            "runtime_scope": {},
            "sources": [
                {"url": _URL_JOBS, "retrieved": "2026-08-01"},
                {"url": _URL_SPARK, "retrieved": "2026-08-01"},
            ],
            "action": {
                "kind": "capacity.increase_workers",
                "target": "databricks.cluster.num_workers",
                "direction": "increase",
                "requires_absent": [],
                "moves": [],
                "depends_on": [],
            },
            "validation": ["contagem total antes e depois"],
            "risks": ["o custo por execucao sobe junto com o numero de workers"],
        },
        {
            "rule_id": "SF-WASTE-001",
            "title": "Capacidade ociosa medida",
            "subject": {"type": "job", "symbol": "etl_pedidos"},
            "evidence": ["f_ausente"],
            "runtime_scope": {},
            "sources": [],
            "action": {
                "kind": "capacity.reduce_workers",
                "target": "databricks.cluster.num_workers",
                "direction": "decrease",
                "requires_absent": [],
                "moves": [],
                "depends_on": [],
            },
            "validation": [],
            "risks": [],
        },
    ]
    return findings, [_fact("databricks.job_run", "f_run001")]


def test_toda_decisao_tem_rollback(tmp_path: Path) -> None:
    """`make_decision` recusa sem rollback; o executor nao contorna a recusa."""
    findings, facts = _par_que_fecha()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["decisions"], "o par que fecha parou de fechar; o teste ficaria vazio"
    for decisao in resposta["decisions"]:
        assert decisao["rollback"].strip()
    gravadas = read_decisions(tmp_path)
    assert len(gravadas) == len(resposta["decisions"])
    for gravada in gravadas:
        assert gravada["rollback"].strip()


def test_decisao_de_disputa_resolvida_nao_sai_high(tmp_path: Path) -> None:
    """A tabela da secao 5.1: disputa resolvida e `medium`, no maximo.

    Uma contradicao direta sempre tem duas claims, entao `high` -- que a tabela
    reserva para "nenhuma contradicao aberta" -- nao esta disponivel aqui.
    """
    findings, facts = _par_que_fecha()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["decisions"]
    assert all(d["confidence"] in {"medium", "low"} for d in resposta["decisions"])


def test_a_decisao_escolhe_uma_das_duas_acoes_e_rejeita_a_outra(tmp_path: Path) -> None:
    """A decisao nomeia as duas opcoes e diz qual foi preterida.

    Registrar so a escolhida esconderia metade da decisao: quem lesse o ADR nao
    saberia contra o que ela foi tomada.
    """
    findings, facts = _par_que_fecha()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    decisao = resposta["decisions"][0]
    assert decisao["selected_option"].startswith("SFA-DBX-001")
    assert decisao["rejected_options"] == [
        "SF-WASTE-001: capacity.reduce_workers (decrease) em databricks.cluster.num_workers"
    ]


def test_o_adr_e_gravado_dentro_do_case(tmp_path: Path) -> None:
    """ADR de case viaja com o case, e nao com o repositorio.

    `docs/vnext/adrs/` guarda as decisoes de arquitetura DESTE repositorio,
    numeradas a mao e auditadas pelo gate de lastro. Um verbo de runtime que
    escrevesse ali misturaria saida de case com documentacao do produto, faria
    dois cases disputarem a mesma numeracao, e escreveria fora do `root` que
    recebeu.
    """
    findings, facts = _par_que_fecha()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    adrs = resposta["persistence"]["adrs"]
    assert len(adrs) == len([d for d in resposta["decisions"] if d["significant"]])
    for caminho in adrs:
        arquivo = Path(caminho)
        assert arquivo.is_relative_to(tmp_path)
        assert arquivo.parent == tmp_path / ".sparkforge-azure" / "blackboard" / "adr"
        texto = arquivo.read_text(encoding="utf-8")
        assert "## Rollback" in texto


# --------------------------------------------------------------------------
# Contradicao condicional -- Objection, nao Contradiction
# --------------------------------------------------------------------------


def _case_condicional() -> tuple[list[dict], list[dict]]:
    """Uma acao com `requires_absent` cuja guarda esta MEDIDA no case.

    Sintetico por medida, nao por preguica: a secao 12.5 mediu que a contradicao
    condicional nao tem caso no catalogo de hoje -- as quatro guardas declaradas
    sao kinds de recusa, que dizem *nao deu para ler* e nao *o problema esta
    presente*. Mecanismo sem caso e `unresolved` nomeado; o teste sintetico
    prova que o mecanismo funciona quando o caso existir.
    """
    findings = [
        {
            "rule_id": "SFA-DBX-004",
            "title": "Configuracao declarada que o cluster nao aplicou",
            "subject": {"type": "cluster", "symbol": "0101-120000-abcd1234"},
            "evidence": ["f_cfg001"],
            "runtime_scope": {},
            "sources": [{"url": _URL_SPARK_CONF, "retrieved": "2026-08-01"}],
            "action": {
                "kind": "config.set_property",
                "target": "databricks.cluster.spark_conf",
                "direction": "replace",
                "requires_absent": ["databricks.cluster.spark_conf.unapplied"],
                "moves": [],
                "depends_on": [],
            },
        }
    ]
    facts = [
        _fact("databricks.cluster.spark_conf", "f_cfg001"),
        _fact("databricks.cluster.spark_conf.unapplied", "f_una001", reason="cluster nao devolveu o bloco"),
    ]
    return findings, facts


def test_condicional_sai_como_objection_com_o_fact_da_medida(tmp_path: Path) -> None:
    """A condicional liga uma claim a uma MEDIDA, e `Objection` e essa forma.

    `Contradiction(claim_a, claim_b, ...)` liga DUAS claims. Enfiar a
    condicional naquele modelo exigiria inventar uma segunda claim para o lado
    que e um fact, e o registro passaria a mentir sobre o tipo do que foi
    achado.
    """
    findings, facts = _case_condicional()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["objections"], "a guarda medida nao produziu objecao"
    objecao = resposta["objections"][0]
    assert objecao["kind"] == "databricks.cluster.spark_conf.unapplied"
    assert objecao["fact_id"] == "f_una001"
    assert objecao["target_claim"] == resposta["claims"][0]["id"]

    gravadas = read_objections(tmp_path)
    assert len(gravadas) == 1
    assert gravadas[0]["evidence_refs"] == ["f_una001"]
    assert not resposta["contradictions"]
    assert not read_contradictions(tmp_path)


# --------------------------------------------------------------------------
# Os invariantes de disciplina
# --------------------------------------------------------------------------


def test_a_resposta_nao_publica_score(tmp_path: Path) -> None:
    """Varredura por SUBSTRING sobre o JSON inteiro -- e por que assim.

    Procurar a chave `score` deixaria passar `independence_score` aninhado, e
    deixaria passar o numero embutido em `ArbitrationResult.reasoning`
    (`"score 0.62"`). A busca por substring pega os tres, e o custo e que a
    palavra fica proibida em qualquer campo da resposta -- que e exatamente o
    que se quer.
    """
    findings, facts = _par_de_contradicao()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    texto = _texto(resposta).lower()
    for marca in ("score", "0.4", "40%"):
        assert marca not in texto, f"o score de arbitragem vazou para a resposta: {marca!r}"


def test_root_que_e_arquivo_nao_derruba_a_chamada(tmp_path: Path) -> None:
    """Regra 27: instrumentacao que quebra o produto e defeito, nao observabilidade.

    Um `root` que e arquivo torna o blackboard impossivel de criar. A resposta
    sai inteira, `persisted` sai `False`, e o erro sai NOMEADO -- engolir o erro
    em silencio seria o outro extremo, e a lacuna deixaria de ser conferivel.
    """
    arquivo = tmp_path / "isto_e_um_arquivo"
    arquivo.write_text("nao sou diretorio", encoding="utf-8")
    findings, facts = _par_de_contradicao()

    resposta = run_executor(findings, facts, arquivo, runtime=RUNTIME)

    assert resposta["persisted"] is False
    assert resposta["persistence"]["errors"], "a falha de gravacao saiu sem nome"
    assert resposta["claims"], "a resposta perdeu o produto por causa da gravacao"
    assert resposta["contradictions"]


@pytest.mark.parametrize(
    ("findings", "claims_esperadas"),
    [(None, 0), ([], 0), (["nao e dict"], 0), ([{}], 1)],
)
def test_entrada_degenerada_nao_derruba(
    findings: Any, claims_esperadas: int, tmp_path: Path
) -> None:
    """Regra 27, do outro lado: entrada degenerada nao levanta.

    `[{}]` sai com UMA claim, e o numero e do irmao, nao deste modulo:
    `claims_from_findings` trata dict vazio como finding sem `rule_id` e emite a
    claim com o fallback declarado (`statement` vira "finding sem rule_id"),
    porque `Claim` recusa statement vazio e derrubar o pacote por causa de um
    campo de apresentacao seria a regra 27 ao contrario. Filtrar aqui faria as
    duas camadas discordarem sobre o que e um finding.
    """
    resposta = run_executor(findings, [], tmp_path, runtime=RUNTIME)

    assert len(resposta["claims"]) == claims_esperadas
    assert resposta["contradictions"] == []
    assert resposta["persisted"] is True


def test_a_resposta_declara_autonomia_l0(tmp_path: Path) -> None:
    """O executor escreve decisao e nunca aplica mudanca.

    O nivel viaja na resposta porque quem le o ADR precisa saber que ele e
    PROPOSTA. `validate_autonomy_boundary` nao e chamado, e a razao esta na
    docstring de `run.py`.
    """
    findings, facts = _par_de_contradicao()

    resposta = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

    assert resposta["autonomy"]["level"] == "L0"
    assert resposta["autonomy"]["applied_changes"] is False


# --------------------------------------------------------------------------
# O `judge` e o `arbitrate` nao divergem
# --------------------------------------------------------------------------


class TestJudgeEArbitrateNaoDivergem:
    def test_ordem_e_contradicoes_batem_com_o_digest(self, tmp_path: Path) -> None:
        """O `judge` publica o que `plan_digest` monta; o `arbitrate` grava a
        partir do MESMO calculo. Se estes dois numeros divergirem, o operador ve
        o `judge` afirmar uma ordem e o `arbitrate` outra sobre o mesmo case.

        O teste vale contra a divergencia FUTURA: hoje as duas leituras
        concordam, e e a concordancia que ele trava.
        """
        from sparkforge_azure.agentic.executor.digest import plan_digest

        findings = _carrega(CASO_DE_FIXTURE / "expected" / "findings.json", "findings")
        facts = uniao_de_facts(CASO_DE_FIXTURE)

        bloco, _lastro = plan_digest(findings, facts, RUNTIME)
        saida = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

        assert saida["order"]["sequence"] == bloco["order"]
        assert saida["order"]["constraints"] == bloco["constraints"]
        assert saida["order"]["unresolved"] == bloco["order_unresolved"]
        assert len(saida["contradictions"]) == len(bloco["contradictions"])
        assert len(saida["unknowns"]) == len(bloco["unresolved"])

    def test_o_par_que_se_contradiz_bate_nos_dois(self, tmp_path: Path) -> None:
        """A fixture de timeout nao tem contradicao nenhuma, e por isso ela
        sozinha nao provaria a igualdade das contradicoes -- zero e zero.

        O par direto sintetico (`SFA-LIB-001` contra `SFA-UC-001`) da o
        lado nao vazio: o `judge` nomeia o mesmo par que o `arbitrate` grava.
        """
        from sparkforge_azure.agentic.executor.digest import plan_digest

        findings, facts = _par_de_contradicao()

        bloco, _lastro = plan_digest(findings, facts, RUNTIME)
        saida = run_executor(findings, facts, tmp_path, runtime=RUNTIME)

        assert bloco["contradictions"], "o catalogo perdeu o par direto"
        assert len(saida["contradictions"]) == len(bloco["contradictions"])
        assert [c["rules"] for c in saida["contradictions"]] == [
            c["rules"] for c in bloco["contradictions"]
        ]
        assert saida["order"]["sequence"] == bloco["order"]
        assert saida["order"]["constraints"] == bloco["constraints"]
