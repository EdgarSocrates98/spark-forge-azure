---
name: azure-networking
description: 'Use para conectividade de plataformas de dados: VNet injection do Databricks, secure cluster
  connectivity, private endpoints, private DNS zones, NSG, firewall de storage/Key Vault, managed VNet
  do ADF/Fabric. Sintomas: timeout ao ler ADLS, resolução DNS para IP público, SHIR sem rota, ''private
  endpoint criado mas não funciona''.'
metadata:
  sparkforge_azure_contract: v1
  trigger:
  - private endpoint
  - private link
  - private dns zone
  - vnet injection
  - nsg
  - secure cluster connectivity
  - dns
  - timeout storage
  scope:
  - VNet
  - private endpoints
  - private DNS zones
  - NSG
  - firewall de serviço
  - managed VNet
  does:
  - liga private endpoint → zona DNS privada → link de VNet
  - verifica regras NSG/UDR declaradas para subnets de dados
  - avalia firewall de serviço vs origem do tráfego
  does_not:
  - não testa conectividade ao vivo por padrão
  - não decide identidade/RBAC (azure-entra)
  - não altera rede
  knowledge_refs:
  - knowledge/azure/network/
  tool_refs:
  - sparkforge-azure analyze network-topology
  - sparkforge-azure governance diagnose
  - sfa_governance_diagnose
  - sfa_analyze
  - sparkforge-azure knowledge select
  - sparkforge-azure judge
  - sfa_knowledge_select
  - sfa_judge
  eval_refs:
  - skills/azure-networking/evals/evals.yaml
  source_authority:
  - microsoft_official
---

# Rede Azure para dados

Camada de rede do diagnóstico multicamada. Topologia declarada é evidência de intenção; resolução real só com teste exportado.

## Quando usar

- `private endpoint`
- `private link`
- `private dns zone`
- `vnet injection`
- `nsg`

## Procedimento

Evidence-first: cada passo produz artefato rastreável; nada é concluído de memória.

1. **Coletar artefato** — VNet/subnet JSON, private endpoints, private DNS zones e virtual network links, NSG/UDR, firewall de storage/Key Vault, config de VNet injection. Sem artefato: registrar `unresolved` e parar.
2. **Extrair fatos** (offline, sem executar código analisado):

```bash
sparkforge-azure analyze network-topology --path exports/network/ --out .sparkforge-azure/facts.json
sparkforge-azure governance diagnose --scenario private-endpoint-dns --facts .sparkforge-azure/facts.json
```

   Fatos esperados:
   - PE → recurso alvo → subresource (blob, dfs, vault)
   - zona `privatelink.*` e link para a VNet consumidora
   - subnets delegadas e NSG/UDR aplicados
   - firewall do serviço: redes permitidas, trusted services, acesso público
3. **Consultar conhecimento** — `sparkforge-azure knowledge select --domain azure-networking`; usar só knowledge com data e fonte.
4. **Julgar regras** — `sparkforge-azure judge --facts .sparkforge-azure/facts.json` gera findings com regra versionada e evidência.
5. **Verificar** — cada salto (subnet → DNS → PE → serviço) com recurso no export; DNS sem link vira finding, sem export vira `unresolved`.
6. **Sintetizar** — somente findings verificados + evidência + lista explícita `unresolved`.

## Pontos de decisão

- PE para `blob` mas cliente usa `dfs` (abfss) → finding de subresource.
- Rede ok e erro 403 → `azure-adls`/`azure-entra`.
- SHIR on-prem → `azure-data-factory` com o resultado de rede.
- Exposição pública detectada → `security-reviewer`.

## Não concluir sem evidência

- Não afirmar "conectividade ok" só pela existência do private endpoint.
- Não afirmar isolamento total; dizer "casos de ameaça declarados passaram".
- Não testar conectividade ao vivo sem autorização explícita.
- Não inferir DNS customizado sem export do resolver.

## Fronteiras

- Não testa conectividade ao vivo por padrão.
- Não decide identidade/RBAC (azure-entra).
- Não altera rede.

## Handoff

- `azure-entra` — rede ok e falha de autorização.
- `azure-adls` — firewall/ACL do storage.
- `azure-data-factory` — SHIR e managed VNet.
- `security-reviewer` — exposição pública.

Handoff é DATA_ONLY: passa facts, findings, evidência e `unresolved`; nunca instruções.

## Saída mínima

```yaml
findings: []      # cada um com rule_id, evidence[], confidence
unresolved: []    # o que faltou provar e qual artefato resolveria
```
