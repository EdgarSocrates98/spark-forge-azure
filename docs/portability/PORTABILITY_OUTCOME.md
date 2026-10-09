# PORTABILITY_OUTCOME — brief final da wave portável

Scorecard por status (§202): `PROVEN` = prova executável no repo;
`PARTIAL` = implementado, prova parcial; `DEFERRED` = fora de escopo
declarado.

```text
BASE_SHA  9f5a1f7   (main pós-hardening, antes do branch)
FINAL_SHA branch feat/portable-distribution (último commit de wave na PR)

DISTRIBUTION         PROVEN   inspect/init/status/doctor/detach idempotente;
                              receipt + ledger + asset inventory sha256
WORKSPACE            PROVEN   workspace.yaml explícito; monorepo (relativo),
                              multi-repo (absoluto externo), ciclos nomeados
IDENTITY             PROVEN   sfa-<uuid> independente de path; state/cache
                              namespacados por id lógico (W3)
RELOCATION           PROVEN   mover preserva id; copiar exige --regen-id;
                              add distingue relocated vs copy (evals ok)
MULTI_REPO           PROVEN   repo externo declarado por path absoluto;
                              sem varredura implícita
CONTEXT_RESOLUTION   PROVEN   target/direct/transitive/all; TokenSave por
                              projeto confinado; recibo §58 com bytes
HOST_INTEGRATION     PROVEN   .mcp.json managed key + markers em
                              AGENTS.md/CLAUDE.md + mirrors opt-in;
                              detecção PATH-only, ausência nunca falha
MCP                  PROVEN   entry aponta o binário instalado
                              (sparkforge-azure mcp serve); nunca path de
                              checkout (gate check_portability)
DETACH               PROVEN   ledger-driven; preserve-por-padrão; purge
                              granular; dry-run; absent≠erro; reattach
                              mesmo project_id
STATE                PROVEN   .sparkforge-azure preservado; --purge-state
                              explícito; SPARKFORGE_AZURE_STATE_DIR honrado
CACHE                PROVEN   state/cache preservado; --purge-cache
                              independente de state
SECURITY             PROVEN   symlinks recusados; paths confinados ao root;
                              segredos recusados em manifest + user config +
                              --set + layers; config vocabulário fechado
WHEEL                PROVEN   T3: uv build → temp venv fora do checkout →
                              init/status/detach/reattach OK
                              (scripts/check_portability.py --wheel)
TESTS                PROVEN   2985 passed / 9 skipped; evals/portability
                              10/10 casos ok
REMOTE_CI            PARTIAL  CI fora de quota no momento do merge —
                              gates locais executados (owner instruction)
```

## Pirâmide de testes (§193)

| Tier | Cobre | Prova |
|---|---|---|
| T0 contracts | manifestos, ledger, erros nomeados | `tests/test_distribution.py`, `test_forge_workspace.py` |
| T1 temp fs | lifecycle single-repo, detach | `tests/` + `evals/portability` single/detach |
| T2 multi-repo | workspace, deps, context scopes | `evals/portability` monorepo/multi/direct/transitive |
| T3 wheel | pacote instalado fora do checkout | `scripts/check_portability.py --wheel` |
| T4 real host | prova de host existente reutilizada | `evals/host_proof/claude_code.json` |

## Paridade final (§203–§204)

| Dimensão | API Forge | Spark Forge AWS | Spark Forge Azure |
|---|---|---|---|
| Portable architecture | PROVEN | parcial | PROVEN |
| Portable distribution | PROVEN | ausente | PROVEN |
| Workspace portability | PROVEN | parcial | PROVEN |
| Host portability | PROVEN (integrate/) | integrate/ | PROVEN (markers+ledger) |
| Relocatable identity | path-hash | — | **melhor**: uuid, move-safe |
| Detach reversível | sim | sim | PROVEN + markers strip |
| Context scopes | locality.py | — | PROVEN (target→all) |

Notas de paridade: `project_id` do api-forge deriva de sha256(path) —
quebra em realocação; o Azure usa uuid persistido, decisão registrada em
`docs/sdd/RELOCATABLE_IDENTITY`. `repair` não existe como verbo — `init`
idempotente cobre (§113, decisão D3 em DETACH_HARDENING).

## Não-provas declaradas

- T4 reusa `evals/host_proof/claude_code.json` (host real já provado;
  §196 — nenhuma prova nova onde não era necessária).
- REMOTE_CI fica PARTIAL até a cota do GitHub voltar; todos os gates
  locais passaram.

## Claims travados (§189–§192)

Textos verbatim em `docs/claims.lock.json`, cada um com prova executável:

- portable lifecycle verified from installed wheel in clean temp workspace
- mover o projeto preserva project_id; copiar exige --regen-id
- scopes direct/transitive resolvem o grafo declarado com recibo de bytes
- detach remove só o ledger, preserva trabalho do usuário e estado por padrão

## Post-closure freshness update

*Snapshot histórico preservado acima (closure: `2985→2988 passed`, BASE_SHA
`9f5a1f7`). Esta seção compara contra os `main` atuais das referências —
comparações de paridade são snapshots amarrados a SHA (§161–§162). Estado
medido vivo do Azure: `docs/CURRENT_STATE.md` (gerado).*

```text
AWS_REFERENCE_SHA        904b40e   (origin/main — distribution/workspace/context resolve chegaram depois do audit)
API_FORGE_REFERENCE_SHA  07459a2   (origin/main — inalterado desde o audit)
AZURE_SHA_NA_MEDIÇÃO     1a5948f   (pós-merge PR #22 + docs completude PR #23)
REMOTE_CI                NOT_OBSERVED — quota esgotada; gates locais verdes
```

### Paridade atual (recomputada do código, não do audit)

| Capability | API Forge `07459a2` | Spark Forge AWS `904b40e` | Spark Forge Azure |
|---|---|---|---|
| Distribution lifecycle | EQUIVALENT — inspect/init/status/doctor | EQUIVALENT — idem | AZURE_AHEAD — +`detach` de projeto, ledger `managed.json`, receipts |
| Workspace lifecycle | EQUIVALENT — discover/init/add/status/graph | EQUIVALENT — discover/init/add/status | AZURE_AHEAD — +remove, arestas/ciclos nomeados, roles, scopes |
| Relocatable identity | DIFFERENT_BY_DESIGN — `project_id = sha256(path)`; quebra em realocação | EQUIVALENT parcial — id persistido pós-init, fallback `sha256(path)`; sem contrato de cópia | AZURE_AHEAD — `sfa-<uuid>` persistido, colisão `identity_collision`, `--regen-id` |
| Context locality | ausente (nenhum resolve por workspace) | DIFFERENT_BY_DESIGN — `context resolve` com scope repo/workspace/target + impact; resolve o *conjunto*, sem materialização | AZURE_AHEAD — scope target→all + escada TokenSave por projeto confinada + recibo de bytes |
| Host integration | host_assets/ | REFERENCE_AHEAD — `integrate`/`detach` nível **usuário**, 4 hosts (claude/devin/codex/copilot), marketplace plugin | DIFFERENT_BY_DESIGN — nível **projeto** (`.mcp.json` + markers + mirrors opt-in), reversível por ledger |
| Detach | ausente | `sparkforge-aws detach` — escopo usuário | AZURE_AHEAD — escopo projeto: preserve-por-padrão, purge granular, dry-run |
| Wheel proof | não observado | `scripts/verify_wheel.py` — verifica packaging, não lifecycle | AZURE_AHEAD — T3: lifecycle inteiro a partir do wheel instalado fora do checkout |
| Evals de portabilidade | não observado | não observado | PROVEN — `evals/portability/` 10/10 casos |

### O que mudou em relação ao audit original

- **AWS portable distribution**: `ausente` (histórico) → `PROVEN` atual —
  `sparkforge_aws/distribution/` + `workspace/portable.py` +
  `context resolve` existem no `904b40e`. A evolução do AWS depois do audit
  não é regressão do Azure — é estado novo de referência (§160).
- **AWS detach**: já existia como `integrate`+`detach` de nível usuário —
  paridade semântica, escopo diferente (§68).
- **API Forge**: inalterado — `project_id` continua `sha256(path)`; sem
  `detach`, sem resolve de contexto por workspace.
- **Diferenças preservadas** (§10): o `context resolve` do Azure materializa
  contexto com recibo de bytes — o do AWS resolve só o conjunto de projetos.
  O Azure cobre *reversibilidade por projeto*; o AWS cobre *amplitude de
  hosts* (copilot + install home-level + marketplace).

`PORTABILITY_STATUS = CLOSED` — nenhum gap P0/P1 de portabilidade em aberto;
itens remanescentes são P2 (docs/polish).
