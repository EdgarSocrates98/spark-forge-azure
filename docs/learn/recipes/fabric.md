# Receita — diagnóstico Microsoft Fabric

**O quê:** `sparkforge-azure diagnose fabric --bundle <case>` cobre o
vertical Fabric: workspace, permissões de item, OneLake/shortcut, Spark,
capacidade e pipeline — com `failure_layer` e recibo.
**Por que:** Fabric não é Synapse nem ADF: artefatos, APIs e o modelo de
permissão são próprios — o diagnóstico separa camada por camada.
**Quando:** permissão negada em item/Lakehouse, shortcut quebrado,
pipeline do Fabric falhando, capacidade em throttling.
**Quando não:** Streaming/RTI (`diagnose stream`), migração para Fabric
(`migration assess`), access multicamada genérico (`diagnose --bundle`).

## Passo a passo

```bash
sparkforge-azure diagnose fabric --bundle <dir-do-case>
sparkforge-azure diagnose fabric --suite tests/fixtures/fabric   # 16 cenários
sparkforge-azure diagnose fabric --suite tests/fixtures/fabric --profile deep
```

Cada case é `case.yaml` + exports (permissões, shortcuts, capacities,
pipeline JSON). `--profile` escolhe o orçamento de contexto
(economy|balanced|deep).

## Interpretação

`failure_layer` nomeia a camada que falhou (ex.: `onelake`, `workspace`,
`pipeline`); `diagnosis` traz causa raiz + conflitos; `unresolved` lista o
que ficou sem evidência — resultado honesto, nunca preenchido.

## Verificação

`--suite` confere cada case contra seu `expect:` — leitura `PASS` só com
camada e status corretos.

## Limitações

Fabric ≠ Synapse ≠ ADF — um bundle de Synapse aqui produz `unresolved`,
não diagnóstico emprestado. Detalhe por camada: `docs/labs/fabric.md`.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| shortcut "vê a tabela, não os arquivos" | identidade do shortcut sem acesso à origem | export do OneLake no bundle; ver `fabric-onelake` skill |
| capacity throttling sem número | capacity metrics não exportadas | incluir métricas de capacidade no bundle |
