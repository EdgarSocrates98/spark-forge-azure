# Revisão de desenho — os blocos além do manifesto

Referência da skill `sdd-design`. O schema do `design.md` cobre `files`,
`decisions` e `covers`; estes blocos moram **no corpo** e entram quando o
risco da mudança os justifica — não é burocracia por feature, é profundidade
proporcional. Nenhum bloco substitui os campos do schema: o `D<n>` continua
obrigatório com `rejected` e `rollback`.

## Quando cada bloco é obrigatório

| bloco | dispara quando |
|---|---|
| ADR | a decisão é cara de reverter, cruza fronteira de sistema, ou muda contrato público/formato persistido |
| threat model | toca entrada não confiada, segredo, IAM, cross-account, Lake Formation ou caminho de exfiltração |
| contrato de integração | outro sistema/job lê o que a mudança publica (tabela, arquivo, tópico, API) |
| data model | a mudança cria ou altera entidade persistida |
| research | o desenho depende de comportamento que precisou ser verificado (spike, doc, fact) |
| quickstart | sempre — como o revisor confere o desenho em minutos |
| impact/compatibility | sempre que `modify`/`delete` aparece no manifesto; reforçado quando runtimes divergem |
| durabilidade de escrita | qualquer persistência ou atualização de dado |

## ADR — a forma curta

```
### ADR D<n> — título
Contexto: o que força decidir agora.
Decisão: o choice do schema.
Alternativas: as rejected[], com o motivo real de cada queda.
Consequências: o que fica fácil, o que fica caro, o que fecha porta.
Rollback: o do schema — e o que ele não cobre.
```

Decisão que não justifica ADR fica no `D<n>` do schema. ADR sem alternativa
rejeitada real é prosa, não decisão.

## Threat model — as cinco perguntas

1. O que entra sem confiança (arquivo, partição, payload, SQL)?
2. O que vale proteger (segredo, dado, permissão, metadado de governança)?
3. Que caminho tira valor do cofre (exfiltração por log, por saída, por
   grant excessivo)?
4. Que identidade executa (role do job, quem chama Step Functions,
   cross-account)?
5. O que a negação mostra — `denied_by`, conta, recurso, camada de policy?

Resposta sem evidência (o `.tf`, o `iam-access` simulado, a policy lida)
é threat model de corredor.

## Contrato de integração e data model

Para cada consumidor: formato de entrada/saída, campos com tipo,
comportamento de erro, e versão do contrato. Mudança de contrato sem
versão é incompatibilidade adiada. Data model declara entidade, chave de
negócio (a do `funcval plan` quando houver), dono e retenção.

## Compatibilidade entre runtimes

Afirmação de comportamento só com a versão em que foi verificada — **um
runtime não vale pelo outro**:

- DBR do Databricks ≠ Synapse Spark pool ≠ Fabric runtime: o mesmo
  `spark.sql` muda de significado — Photon ligado/desligado também muda.
- Serverless SQL do Synapse e endpoints SQL do Fabric: sintaxe e limite por
  engine/edition.
- Delta/Iceberg/Parquet: atomicidade, schema evolution e concorrência são
  do formato **e** do runtime que o escreve — Delta no Databricks não é
  Delta no Fabric por decreto (UniForm/Iceberg no OneLake tem camadas
  próprias).
- Streaming: checkpoint, trigger e estado por engine — o que vale em
  Structured Streaming não decorre para Eventstream/Eventhouse sem
  verificação.

Fonte: `sparkforge-azure rules lookup --id <SF-...>`, `knowledge path --file <doc>`
com a versão alvo, `runtime detect` quando o caso permite. Sem fonte, a
afirmação é `unresolved` do desenho.

## Durabilidade de escrita

Para persistência/atualização de dado, responda por escrito:

| pergunta | o que o desenho mostra |
|---|---|
| atomicidade | uma operação falha no meio — o que fica visível? |
| isolamento | leitor concorrente vê o quê, de qual snapshot? |
| consistência | o invariante de negócio preservado entre etapas? |
| idempotência | reexecutar a escrita duplica ou repara? |
| concorrência | dois writers, commit conflicts, quem perde? |
| versionamento | schema evolution aditiva vs. destrutiva, e quem lê versão velha |
| chave de negócio | o que identifica a linha — e o que acontece em reprocessamento |
| recovery | retry, reprocessamento, dados parcialmente atualizados |
| limites de transação | onde começa e onde termina o commit; o que fica fora |

Snapshot isolado não resolve falha de múltiplas operações: o desenho diz
como o invariante sobrevive quando a operação 2 de 3 falha, e qual teste
negativo prova.

## Foco Azure — o checklist por serviço

Databricks (DBR, cluster policy, Photon, jobs/DABs), Unity Catalog
(catálogo, grants, external locations, workspace binding), Synapse (Spark
pools, SQL pools, pipelines), Fabric (Lakehouse, OneLake shortcuts,
capacidade, Eventstream/Eventhouse), ADLS Gen2 (ACL POSIX, RBAC de dados,
hierarchical namespace, abfss), Entra ID (managed identity, service
principal, role assignments), ADF (activities, linked services, IR),
Event Hubs (partições, consumer groups, Capture), Delta/Iceberg (commit,
OPTIMIZE/VACUUM, deletion vectors, UniForm), Spark SQL e jobs (semântica
por versão de runtime), Terraform/Bicep (azurerm/azapi/databricks, drift,
what-if) e Networking (VNet injection, private endpoints, NSG). Para cada
um em jogo: o que muda, a versão, e a fonte.
