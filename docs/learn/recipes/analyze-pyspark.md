# Receita — fatos determinísticos de código PySpark

**O quê:** `sparkforge-azure analyze pyspark --path <dir>` extrai facts por
AST — reads, writes, SQL, APIs — com provenance por artefato.
**Por que:** assessment offline começa por inventário factual.
**Quando:** primeira passada num repo Synapse/Databricks/Fabric.
**Quando não:** análise de runtime — facts são estáticos; `collect` (com
credencial) é outro caminho.

## Problema

"O que este notebook/job lê, escreve e quais APIs usa — sem rodar?"

## Passo a passo

```bash
sparkforge-azure analyze pyspark --path jobs/
```

## Saída esperada / interpretação

Facts JSON por arquivo (`api`, `target`, `provenance.extractor` +
`artifact_sha256`). `--format text` para leitura humana; `json` é o default.

## Verificação

`artifact_sha256` casa com o sha256 do arquivo — determinístico no mesmo
input.

## Limitações

`analyze` cobre só kinds com extractor (`analyze --help` lista — hoje
`pyspark`); o restante vem de `collect`/`graph`/`diagnose`.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `invalid choice` | kind sem extractor | `analyze --help` lista os válidos |
| facts vazios | path sem `.py` | aponte o dir dos jobs |

## Uso por agentes

Workflow `analyze` do `forge.agentic.json`; o the-forge delega este argv.
