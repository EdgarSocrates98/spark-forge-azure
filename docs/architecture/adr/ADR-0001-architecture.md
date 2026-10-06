# ADR-0001 — Arquitetura fundacional

- Status: **Accepted** (2026-10-06)
- Fase: 2 (§231)

## Contexto

O prompt fundacional exige paridade de *engenharia* (não de arquivos) com o Spark Forge AWS,
nascimento econômico (TokenSave desde o início), e núcleo determinístico. A auditoria
([portability matrix](../AWS_TO_AZURE_PORTABILITY_MATRIX.md)) mostrou que o núcleo agentic do AWS é
quase todo provider-neutro, mas o grafo de imports o acopla ao AWS por poucas arestas
(`economy→collect`, `codeintel→facts`, `receipt→findings`, `case→collect`).

## Decisão

1. **Camadas** (de baixo para cima; dependências só descem):

   ```text
   L0 kernel       paths, durable, protocols (Forge Protocol)
   L1 contracts    findings (Fact/Finding/RuntimeContext), trust, policy
   L2 engines      rules, decision, context, economy, tokensave, codeintel, knowledge
   L3 graph        Graphfy (code/data/azure/knowledge/evidence + live + federation + impact)
   L4 agentic      agentic runtime (governor, budget, stop, recovery, memory, checkpoint, router)
   L5 domain       azure/* (identity, storage, network, databricks, unity_catalog, fabric, synapse,
                   adf, eventhubs, purview, finops, observability, governance) + spark/*
   L6 collectors   collect/* (read-only, redaction obrigatória)
   L7 surfaces     cli (sparkforge-azure), mcp, doctor, offline bundle, lab
   L8 assurance    claims, surface lock, manifest, parity, supply chain
   ```
   `tests/test_architecture_layers.py` impõe a direção.

2. **Cortes de aresta** no código copiado: um módulo COPY_SAFE não pode importar L5/L6.
   Integração com domínio Azure acontece via *ports* (protocolos) no L2.

3. **Facts → Rules → Findings** é o caminho determinístico central (§174). LLM só entra
   via agentic runtime e sob Information Gain + budget.

4. **Domínio Azure separado por plataforma**: `fabric` ≠ `synapse` (§15); `adf` ≠
   `fabric.data_factory` (§20); Lake Formation não vira alias de UC (§8).

5. **Optional deps** (§180): núcleo = `PyYAML` + `jsonschema`. Extras: `azure`, `databricks`,
   `mcp`, `otel`, `dev`. Import de SDK sempre lazy via `require_*()`.

6. **Read-only por construção**: collectors só expõem operações de leitura; toda tool MCP
   declara risco (`read_only`, `local_write`, `cloud_read`, `cloud_write`, `security_impact`,
   `production_impact`); risco desconhecido → DENY (§154).

## Consequências

- Código copiado do AWS mantém comportamento provado; diffs ficam em `provenance.json`.
- Ganho de simetria não justifica módulo: só porta o que tem teste Azure.
- `adapters/` do AWS (30k LOC, 914 marcadores) **não** é copiado; a superfície é reescrita
  menor, com registro declarativo.
