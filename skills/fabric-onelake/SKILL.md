---
name: fabric-onelake
description: 'Use para OneLake: shortcuts (ADLS, S3, outro workspace), segurança OneLake/roles de dados,
  permissões de workspace e acesso a arquivos/tabelas via abfss do OneLake. Sintomas: shortcut quebrado,
  ''vejo a tabela mas não os arquivos'', identidade do shortcut sem acesso ao ADLS de origem. Não confunda
  com Unity Catalog nem com ACL do ADLS de destino.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - onelake
  - shortcut
  - onelake security
  - onelake data access
  - shortcut quebrado
  - workspace role
  scope:
  - OneLake
  - shortcuts
  - OneLake security roles
  - workspace roles
  - abfss OneLake
  does:
  - mapeia shortcut → origem → identidade usada na delegação
  - separa permissão de workspace, item e role de dados OneLake
  - encadeia com ADLS quando a origem é ADLS Gen2
  does_not:
  - não cobre Unity Catalog (unity-catalog)
  - não diagnostica ACL do ADLS de origem sozinho (azure-adls)
  - não cobre engenharia de notebooks (fabric-data-engineering)
  knowledge_refs:
  - knowledge/azure/fabric/
  - knowledge/azure/storage/
  - knowledge/governance/
  tool_refs:
  - sparkforge-azure analyze onelake-shortcuts
  - sparkforge-azure governance diagnose
  - sfa_governance_diagnose
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/fabric-onelake/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Fabric OneLake

Camada de armazenamento lógico do Fabric. Shortcut delega acesso; a identidade delegada precisa ser provada em cada salto.

## Quando usar

- `onelake`
- `shortcut`
- `onelake security`
- `onelake data access`
- `shortcut quebrado`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — definições de shortcut (target, connection, path), roles de segurança OneLake, roles de workspace, RBAC/ACL do ADLS de origem quando houver. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze onelake-shortcuts --path fabric-workspace/ --out .sparkforge-azure/facts.json
sparkforge-azure governance diagnose --scenario onelake-shortcut-denied --facts .sparkforge-azure/facts.json
```

   Fatos esperados:
   - shortcut → tipo de target → connection → identidade (organizational account, SP, workspace identity)
   - roles OneLake e pastas cobertas
   - role de workspace do principal
   - RBAC/ACL do target, se exportado
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain fabric-onelake`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — cada salto (usuário → workspace → shortcut → connection → ADLS) com evidência; elo sem export vira `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- Target ADLS e erro 403 na origem → `azure-adls`.
- Pergunta sobre UC/Databricks lendo OneLake → `unity-catalog` para o lado Databricks.
- Identidade da connection é SP/MI → `azure-entra`.
- Target com firewall/private endpoint → `azure-networking`.

## Não concluir sem evidência

- Não afirmar que o usuário final "tem acesso à origem" quando a delegação usa identidade da connection.
- Não equiparar role OneLake a grant de UC.
- Não afirmar shortcut íntegro sem export do target.
- Não dizer "seguro"; dizer "casos de ameaça declarados passaram".

## Fronteiras

- Não cobre Unity Catalog (unity-catalog).
- Não diagnostica ACL do ADLS de origem sozinho (azure-adls).
- Não cobre engenharia de notebooks (fabric-data-engineering).

## Handoff

- `azure-adls` — target do shortcut é ADLS e há erro na origem.
- `azure-entra` — identidade da connection/workspace identity.
- `fabric-data-engineering` — o problema é de notebook/pipeline, não de acesso.
- `azure-networking` — target atrás de firewall/private link.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
