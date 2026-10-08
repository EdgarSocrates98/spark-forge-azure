# Cycle 2 — design consolidado

Quatro sub-SDDs (`docs/sdd/`): `MCP_RUNTIME`, `DATABRICKS_UC_ADLS`,
`GRAPHFY_ACCESS`, `TOKENSAVE_PROOF`. Este documento é a vista única do
desenho; detalhes e hashes encadeados vivem nos SDDs.

## O caso que ancora tudo

> "Meu job Azure Databricks não consegue acessar uma tabela/path
> governado por Unity Catalog em ADLS."

A resposta exige a cadeia inteira:

```text
Entra identity → workspace → UC (grants, bindings)
  → storage credential → external location
  → Azure RBAC → ADLS ACL → network/DNS → runtime (DBR) → Delta
```

## Decisões estruturais

1. **Facts → Rules → Findings, sempre.** Extractors (`azure/extract.py`)
   produzem facts ancorados; `governance.diagnose` julga a cadeia; o
   catálogo `SF-ACC` e findings estruturais (`SF-ACC-010..013`) cobrem o
   que a cadeia não decide sozinha. Nada no caminho inventa veredito sem
   evidence — sem evidência, `unresolved`.
2. **Offline first, live opt-in explícito** (prompts 165-167). Collectors
   default a `mode=export`; live exige SDK extra + credencial + grant.
   `LiveCache` marca freshness; stale nunca volta como current sem
   `allow_stale` + registro em `unresolved` (168-169).
3. **Confiança no piso (196-197).** Todo producer do vertical emite
   `authority=data_only`; artifacts são redatados na fronteira de
   extração — secrets nunca entram em facts (192).
4. **Cross-environment é finding, não merge** (193-195). Facts
   `environment.scope` por artefato; divergência de tenant/subscription/
   workspace/metastore → `SF-ACC-013`, `failure_layer=cross_environment`.
5. **Grafo participa da resolução** (209). `graph/access.py` constrói a
   cadeia tipada que alimenta `evidence_paths` e as queries de impacto —
   não é JSON decorativo.
6. **Economia observável** (185-187, 221). Benchmark mede bytes por
   perfil no mesmo corpus; `frontier` expõe eixos lado a lado
   (recall, bytes, calls, latência, unresolved) sem score mágico.
7. **MCP = interface de capabilities reais** (218). 10 tools
   composicionais; inspector-por-API recusado (`docs/reference/mcp-tools.md`).

## Camadas públicas de falha

`entra`, `workspace_binding`, `unity_catalog`, `external_location`,
`storage_credential`, `network`, `azure_rbac`, `adls_acl`, `runtime`,
`delta_perf`, `governance_bypass`, `cross_environment`, `unresolved`.

## Verificação

Gates: `pytest`, `ruff`, `check_surface_lock`, `check_claims`,
`check_knowledge`, `check_skills_agents`, `sdd check`. Red runs honestos
registrados em cada `build_report.md` (worktree na base `b1caf70`).
