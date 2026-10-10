# Receita — Azure Data Factory

**O quê:** ADF entra por dois caminhos: `migration inventory|assess` para o
estate de pipelines (ARM export) e a skill `azure-data-factory` para análise
de activities/linked services/triggers/IR.
**Por que:** o caso mais comum é migrar ADF → Fabric; o assessment mede
prontidão pipeline a pipeline, com waves e rollback.
**Quando:** "quanto custa migrar esse ADF", pipeline quebrando por linked
service/dataset, trigger duplicado, SHIR offline.
**Quando não:** pipelines do Data Factory do Fabric — é outro produto
(`diagnose fabric`, skill `fabric-data-engineering`).

## Passo a passo

```bash
# census do estate a partir do ARM export — quantos pipelines, que readiness
sparkforge-azure migration inventory --bundle <dir-do-estate>

# assessment completo: readiness + recomendações + waves + validação
sparkforge-azure migration assess --bundle <dir-do-estate>
sparkforge-azure migration assess --suite tests/fixtures/migration  # 22 cenários
```

O bundle carrega o ARM export (pipelines, linked services, datasets,
triggers, IRs). Nada chama o Azure — o extrator lê o export.

## Interpretação

`assess` devolve readiness por artefato, `waves` (ordem de migração),
`rollback` e `upstream_blockers`. O `inventory` é o censo honesto antes de
qualquer plano — prontidão por categoria, não por impressão.

## Verificação

`--suite` confere os 22 cenários contra `expect:` — inclui casos de
linked service com segredo inline, IR self-hosted offline e dataset
compartilhado.

## Limitações

A análise é do export, não do serviço vivo — estado de trigger "Started"
entre o export e a execução não aparece. Não decide Data Factory do Fabric.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| pipeline some do inventory | não está no ARM export | re-exportar incluindo o resource group certo |
| segredo em linked service | parâmetro inline no ARM | é finding, não blocker — entra no relatório |
