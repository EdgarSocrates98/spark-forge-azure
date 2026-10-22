# FORGE_CONTEXT_FINAL_HOMOLOGATION — spark-forge-azure

Relatório final do programa Install 2.0 (spec-fonte
`prompt_evo_install2.0.md` §12.6), cobrindo os ciclos 2–7 executados sobre a
baseline `docs/audits/FORGE_CONTEXT_BASELINE.md` (ciclo 1, lf-0034).
Documento de evidência: cada afirmação cita commit/PR, arquivo:linha ou
comando executado. O que não foi executado está marcado **NÃO EXECUTADO**
(§16 — nenhum teste não executado é reportado como sucesso).

- **Repo:** `/home/edgar/Documentos/projetos/forjas/spark-forge-azure`
- **SHA antes:** `d35305c2b6eacfb35d6d9c38061894e680f04330` (tag `v0.1.6`,
  2026-10-21 — mesma HEAD auditada no baseline)
- **SHA depois:** `ea69b020c8cb00d3e32bb4272c30a778a76a0678` (HEAD de `main`)
- **Versão:** `sparkforge-azure` 0.1.6 → **0.2.0** (`pyproject.toml` bumpado
  em worktree, **pendente de publicação** — §10)
- **Python:** `>=3.10`
- **Data:** 2026-10-22
- **Processo:** mudanças comportamentais passaram pelo SDD
  (`docs/sdd/INSTALL_EVALS_SURFACE/` — define/design/plan/build_report)

---

## 1. SHAs antes/depois

| | SHA | Descrição |
|---|---|---|
| Tag base / baseline | `d35305c2b6eacfb35d6d9c38061894e680f04330` | `release: 0.1.6 — governed peer delegation + Windows fixture shim` |
| HEAD final | `ea69b020c8cb00d3e32bb4272c30a778a76a0678` | `fix(install): installkit 1.0.1 — stale-lock created_at + backport bootstrap fixes (#96)` |

Range medido: `git log v0.1.6..HEAD` → **28 commits**, `git diff --stat` →
**35 arquivos, +7.157/−55 linhas**.

## 2. PRs

Todos os PRs mergeados em `EdgarSocrates98/spark-forge-azure`, verdes no
CI no momento do merge.

| PR | Merge / squash | Conteúdo |
|---|---|---|
| #77 | `baac70f` (merge), `617a214` | docs(audit): FORGE_CONTEXT_BASELINE (lf-0034) |
| #78 | `57e4a09` (merge), `9aa91a4` | fix(doctor): `agentic_fleet` resolve fleet via `fleet_root()` — não `REPO` (gap P0-1 do baseline) |
| #79 | `7798432` (merge), `80b02c9` | feat(context): `forge/context/v1` — vendored registry + install wiring (ciclo 2) |
| #80 | `471482f` (merge), `f5b2419` | feat(context): consumer-docs layer — blocos `forge:*` + AGENT_PROTOCOL.md consolidado (ciclo 3, lf-0036) |
| #81 | `4aa1594` (merge), `5329bd6` | test(gate): isenta `_forgecontext` + install wiring do raw-glob scan |
| #82 | `fba28fe` (merge), `d92b2ce` `70bdf8d` `03cdc40` | feat(install): wheel distribution parity — manifests + knowledge resolver (lf-0039 §8); discovery lf-0037 (verbs §6.2 + knowledge pointer stubs); fix §8.2 leitor `_data/forge*.json` |
| #83 | `197d900` (squash) | fix(lint): F401 json unused em `test_discovery_ops` |
| #84 | `22813da` (squash) | fix(tests): declara arestas discovery/cli→knowledge\|rules\|distribution (lf-0037); remove fantasma cli→knowledge_drift |
| #85 | `a0cad7f` (squash) | fix(tests): isenta `discovery.py` do gate de glob cru (vars bounded em dirs do pacote) |
| #86 | `f0f8a6d` (squash) | fix(installkit): `_forgecontext` v1.2.1 — `timezone.utc` p/ Python 3.10 |
| #87 | `44415ca` (squash) | chore(docs): regen `CURRENT_STATE.md` — CLI_COMMANDS 91 pós lf-0037 |
| #88 | `5eacfd9` (squash) | feat(evals): ciclo 5 — taxonomia §7.1 + ops §7.2 + selagem §7.3 (lf-0038; via SDD `INSTALL_EVALS_SURFACE`) |
| #89 | `cdaa54f` (squash) | fix(evals): runtime→avaliacao via importlib (harness boundary) |
| #90 | `fb0bf6a` (squash) | fix(arch): remove exceções fantasma `*→evals` (arestas viraram importlib) |
| #91 | `608f0fc` (squash) | fix(test): knowledge stub check separator-agnostic |
| #92 | `b5005ba` (squash) | fix(test): wheel isolation fallback `uv venv --seed` (ensurepip ausente no py3.10 managed) |
| #93 | `e75dd98` (squash) | fix(test): `uv venv --seed` — limpa dir parcial + `--python` explícito |
| #94 | `7f1e1cf` (squash) | docs(reference): rules/capabilities no `cli.md` + DISTRIBUTION_PARITY no index |
| #95 | `b92300d` (squash) | feat(install): transactional context registry + canonical `forge_id` (lf-0040, ciclo 7) |
| #96 | `ea69b02` (squash) | fix(install): installkit 1.0.1 — stale-lock `created_at` + backports do bootstrap |

## 3. Commits

28 commits no range (`git log v0.1.6..HEAD --format='%h %s'`, ordem cronológica):

```text
617a214 docs(audit): FORGE_CONTEXT_BASELINE — Install 2.0 cycle 1 (lf-0034)
baac70f Merge pull request #77 (audit/install-context)
9aa91a4 fix(doctor): agentic_fleet resolves fleet via fleet_root() not REPO
57e4a09 Merge pull request #78 (fix/doctor-fleet-root)
80b02c9 feat(context): forge/context/v1 — vendored registry + install wiring (ciclo 2)
7798432 Merge pull request #79 (cycle/install-context)
f5b2419 feat(context): consumer-docs layer — blocos forge:* + AGENT_PROTOCOL.md consolidado (lf-0036)
471482f Merge pull request #80 (cycle/install-context-docs)
5329bd6 test(gate): exempt _forgecontext + install wiring from raw-glob scan
4aa1594 Merge pull request #81 (fix/glob-gate-exemptions)
d92b2ce feat(install): wheel distribution parity — forge manifests + knowledge resolver (lf-0039 §8)
70bdf8d discovery: lf-0037 install-time §6.2 retrieval verbs + knowledge pointer stubs
03cdc40 fix(install): manifest reader resolve _data/forge*.json packaged sob wheel (lf-0039 §8.2)
fba28fe Merge pull request #82 (cycle/install-context)
197d900 fix(lint): F401 json unused em test_discovery_ops (#83)
22813da fix(tests): declara arestas discovery/cli->knowledge|rules|distribution (lf-0037) e remove fantasma cli->knowledge_drift (#84)
a0cad7f fix(tests): isenta discovery.py do gate de glob cru (vars bounded em dirs do pacote, lf-0037) (#85)
f0f8a6d fix(installkit): _forgecontext v1.2.1 — timezone.utc p/ Python 3.10 (#86)
44415ca chore(docs): regen CURRENT_STATE.md — CLI_COMMANDS 91 pós lf-0037 (#87)
5eacfd9 feat(evals): install-2.0 ciclo 5 — taxonomia §7.1 + ops §7.2 + selagem §7.3 (lf-0038) (#88)
cdaa54f fix(evals): runtime->avaliacao via importlib (harness boundary) (#89)
fb0bf6a fix(arch): remove excecoes fantasma *->evals (arestas viraram importlib) (#90)
608f0fc fix(test): knowledge stub check separator-agnostic (#91)
b5005ba fix(test): wheel isolation fallback uv venv --seed (ensurepip ausente no py3.10 managed) (#92)
e75dd98 fix(test): uv venv --seed — limpa dir parcial + --python explícito (#93)
7f1e1cf docs(reference): rules/capabilities no cli.md + DISTRIBUTION_PARITY no index (#94)
b92300d feat(install): transactional context registry + canonical forge_id (lf-0040) (#95)
ea69b02 fix(install): installkit 1.0.1 — stale-lock created_at + backport bootstrap fixes (userinfo regex, argv trim, smoke vazio) (#96)
```

## 4. Arquivos modificados

`git diff --name-only v0.1.6..HEAD` → 35 arquivos. Agrupados:

| Grupo | Arquivos |
|---|---|
| Vendored | `sparkforge_azure/_forgecontext.py` (novo, v1.3.1, `_SOURCE_SHA256 = "e72e93eab21ade74"`), `sparkforge_azure/_installkit.py` (v1.0.1, `4c446922f5e77a0c`), `scripts/forge_installkit.py`, `scripts/forge_bootstrap.py` (v1.1.1) |
| Wiring de produção | `sparkforge_azure/install/service.py` (`install_transaction`/`uninstall_transaction` em `:891`/`:936`, `_context_manifest`, knowledge pointer stubs em `:155-184`), `sparkforge_azure/discovery_ops.py` (novo), `sparkforge_azure/discovery.py`, `sparkforge_azure/distribution/{hostfiles,service}.py`, `sparkforge_azure/doctor.py` (`fleet_root()`), `sparkforge_azure/cli/{main,cmd_analyze,cmd_context,cmd_discovery,cmd_evals}.py`, `sparkforge_azure/evals/{surface,taxonomy}.py` |
| Empacotamento | `pyproject.toml` (force-include `forge.json`/`forge.agentic.json` → `sparkforge_azure/_data/`) |
| SDD | `docs/sdd/INSTALL_EVALS_SURFACE/{define,design,plan,build_report}.md` |
| Docs | `docs/audits/FORGE_CONTEXT_BASELINE.md`, `docs/install/DISTRIBUTION_PARITY.md`, `docs/evals-taxonomy.md`, `docs/CURRENT_STATE.md`, `docs/README.md`, `docs/reference/cli.md`, `docs/surface.lock.json` |
| Testes | `tests/test_install_lifecycle.py` (26 testes), `tests/test_wheel_isolation.py`, `tests/test_evals_surface.py` (22), `tests/test_discovery_ops.py` (14), `tests/test_facts_scan.py`, `tests/test_architecture_layers.py` |

## 5. Gaps corrigidos

Mapeamento gap do baseline (§5) → correção entregue:

| Gap baseline | Status | Evidência |
|---|---|---|
| **GAP-P0-1** — `doctor.agentic_fleet` marcava os 40 agents como `broken` numa instalação wheel | **CORRIGIDO** | `doctor.py` resolve via `fleet_root()` (pacote `_data/`), não `REPO`; commit `9aa91a4` (PR #78 — achado do próprio baseline) |
| **GAP-P0-2** — `knowledge_refs`/`tool_refs` repo-relativos nos mirrors instalados | **CORRIGIDO** | `install/service.py:155-184` materializa pointer stubs `knowledge/<rel>` apontando para os verbos nativos (lf-0037); commit `70bdf8d` |
| **GAP-P1-1** — sem `install manifest`/`install env` e manifests não viajam | **CORRIGIDO (manifesto)** | `forge.json`/`forge.agentic.json` empacotados em `_data/` (`pyproject.toml:93-94`); install emite `forge/context/v1` com capabilities reais; commits `d92b2ce`, `03cdc40` |
| **GAP-P1-2** — `forge.agentic.json` vazio e defasado | **CORRIGIDO (transporte)** | o manifesto agora viaja no wheel e é lido sob `_PKG_DIR`; revisão de conteúdo do `forge.agentic.json` em si não foi alterada no range |
| **GAP-P1-3** — marker aponta verbos obsoletos; nada explica o ecossistema | **CORRIGIDO** | consumer-docs ciclo 3: blocos `forge:ecosystem`/`forge:sparkforge-azure` + `AGENT_PROTOCOL.md` consolidado; `_planned_files` inclui `CLAUDE.md`/`AGENT_PROTOCOL.md` (`service.py:197-200`); commit `f5b2419` |
| — registry de contexto no workspace | **CORRIGIDO** | `.forge/context/registry.json` + `capabilities/sparkforge-azure.json` + `ROUTING.md`; commits `80b02c9`, `b92300d` |
| — evals não classificados (§7) | **CORRIGIDO** | `evals/taxonomy.py` + `evals/surface.py` + `evals list|describe|run|result`; SDD `INSTALL_EVALS_SURFACE`; commit `5eacfd9` |
| — `_forgecontext` incompatível com py3.10 | **CORRIGIDO** | v1.2.1 `timezone.utc`; commit `f0f8a6d` |
| — wheel isolation quebrava sem `ensurepip` (py3.10 managed) | **CORRIGIDO** | fallback `uv venv --seed` em `tests/test_wheel_isolation.py`; commits `b5005ba`, `e75dd98` |
| — installkit 1.0.0 / bootstrap 1.1.0 (staleness, userinfo regex, argv trim, smoke vazio) | **CORRIGIDO** | `_installkit.py` v1.0.1 + `forge_bootstrap.py` v1.1.1 byte-idênticos ao canônico; commit `ea69b02` |

## 6. Gaps restantes

- **E2E real de hosts (§10.2) — NÃO EXECUTADO** (ciclo 8 pendente; ver §9).
- **Economia/observabilidade (ciclo 9, §11) — pendente.**
- **Publicação PyPI — pendente** (§10).
- **GAP-P1-4** — `MANIFEST.sha256` de assets + locks de superfície não
  viajam no wheel: o contrato suporta `integrity.files` sha256, mas um
  manifesto dedicado assinável do bundle canônico não foi emitido;
  `doctor` continua reportando `unresolved` para `surface`/`claims` sob
  wheel (locks ficam em `docs/` do checkout — degradação documentada em
  `DISTRIBUTION_PARITY.md`).
- **GAP-P1-5** — `.mcp.json` usa o console script `sparkforge-azure`
  (`distribution/hosts.py:25-27` — PATH-resolvido por design, "installed
  binary only"); `install doctor` faz handshake real (18 tools, PASS em
  wheel local). Permanece a decisão documentada; sem alternativa
  implementada.
- **GAP-P2-1…P2-7** — `--host copilot|all` sem handler, csv/`none`,
  `knowledge path` ausente (o discovery cobre `knowledge search|get`),
  `agents list` `unevaluated` sob wheel, `distribution` vs `install`
  paralelos, `evals/host_proof` 1 runtime, sdist por profundidade — não
  tocados no range.
- **`DISTRIBUTION_PARITY.md`** descreve a lacuna do leitor pré-§8.2 como
  "tracked" — o §8.2 (`03cdc40`) corrigiu; o doc registra o histórico.

## 7. Testes executados

| Suíte | Arquivo | Contagem | Resultado |
|---|---|---|---|
| install lifecycle + context txn | `tests/test_install_lifecycle.py` | 26 | verde |
| wheel isolation (lf-0039) | `tests/test_wheel_isolation.py` | 1 (e2e) | verde |
| evals §7 surface | `tests/test_evals_surface.py` | 22 | verde |
| discovery ops §6.2 | `tests/test_discovery_ops.py` | 14 | verde |
| gates estruturais | `tests/test_facts_scan.py`, `tests/test_architecture_layers.py` | — | verde |

Cross-forge (rodado em the-forge, cobrindo esta wheel): **120/120**
permutações de ordem de instalação (`test_multi_forge_e2e.py`, marker
`slow`) e `vendor.py --check` **CLEAN**.

## 8. Resultados

- `sparkforge_azure/_forgecontext.py` **byte-idêntico** ao canônico e às
  4 outras forjas (sha256 `390f5e0e61ab80dc…`, `_SOURCE_SHA256 =
  "e72e93eab21ade74"`, v1.3.1).
- `install apply` escreve `.forge/context/{registry.json,
  capabilities/sparkforge-azure.json, ROUTING.md}` + consumer-docs +
  `.mcp.json` managed key sob um único lock transacional
  (`service.py:891`); `install uninstall` idem (`:936`).
- `discovery_ops.py` é fonte única do mapa §6.2 → verbos reais; `domains`
  publicados: `microsoft-fabric, azure-synapse, adf, apache-iceberg,
  spark-streaming, terraform, data-quality`.
- `canonical forge_id` reforçado no ciclo 7 (`b92300d`): registry entries
  carregam `qualified_ids` (`<forge>:<recurso>`).
- Evals classificados §7.1 + ops §7.2 + sealing §7.3 via SDD
  (`docs/sdd/INSTALL_EVALS_SURFACE/build_report.md`).
- `forge.json`/`forge.agentic.json` empacotados em `_data/`; leitor
  `_PKG_DIR`-aware (§8.2).

## 9. Evidências Devin/Claude/Codex

**NÃO EXECUTADO.** A prova E2E real por host (§10.2 — Devin CLI, Claude
Code, Codex CLI, Copilot) pertence ao ciclo 8, pendente. Os artefatos
instalados foram verificados por testes de integração e wheel isolation
— não por telemetria de host real.

## 10. Matriz PyPI

| Componente | Estado |
|---|---|
| Wheel local (HEAD) | construída e testada em venv limpa fora do checkout (`tests/test_wheel_isolation.py`); usada na matriz 5! do the-forge |
| `forge.json`/`forge.agentic.json` no wheel | presentes em `sparkforge_azure/_data/` (force-include `pyproject.toml:93-94`) |
| `_data/{skills,agents,knowledge,rules,evals}` | empacotados (ver `docs/install/DISTRIBUTION_PARITY.md`) |
| Publicação no índice | **PENDENTE DE PUBLICAÇÃO** — worktree marca `0.2.0`; PyPI ainda serve `0.1.6` |
| PyPI 0.1.6 publicado | bit-idêntico ao wheel 0.1.6 local (baseline) |

## 11. Compatibilidade

- Contratos `forge/*` v1 estáveis; `forge/context/v1` +
  `forge/context-registry/v1` adicionados sem quebrar
  `forge/InstallationManifest/v1`.
- Engine vendored roda em py3.10 (`_forgecontext` v1.2.1, #86) — o piso
  desta forja; `uv venv --seed` cobre interpretadores managed sem
  `ensurepip` no teste de isolamento (#92/#93).
- Rollback: uninstall transacional só remove o próprio manifesto/entry/
  blocks; `FORGE-CONTEXT-OWNERSHIP` impede deleção cruzada.

## 12. Segurança

Herdada do motor vendored + wiring local:

- `_txn_restore` com validação de path (`..`, absoluto, `\`, drive;
  blob `^\d{1,8}$`) — `_forgecontext.py:2495-2531`.
- KeyboardInterrupt/SystemExit propagam bare após rollback (`:2670+`).
- `forge_bootstrap.py` 1.1.1: `_URL_USERINFO_RE` `[^/\s]+@` (userinfo com
  `@` interno não vaza), argv trim, smoke vazio≠PASS.
- installkit 1.0.1: stale-lock `created_at` fallback para PID indecidível
  (Windows/PermissionError).
- Gate de raw-glob isenta explicitamente o vendored + wiring (`5329bd6`);
  boundaries de harness respeitadas via importlib (`cdaa54f`, `fb0bf6a`).
- Ownership `FORGE-CONTEXT-OWNERSHIP`; markers ambíguos →
  `FORGE-CONTEXT-CONFLICT`; conteúdo de usuário byte-preservado.

## 13. Performance

- Reinstall inalterado = zero writes (registry determinístico — prova na
  matriz 5!).
- Sem claims quantitativos — ciclo 9 (§11) não executado.

## 14. Recomendações

1. Ciclo 8 (§10.2) — prova real Devin/Claude/Codex com esta wheel
   instalada num consumidor Azure (Databricks/Fabric/ADF); sem ela o
   aceite §16 sobre hosts fica aberto.
2. Publicar `0.2.0` (§12.5) ou marcar release bloqueada — nunca simular.
3. `MANIFEST.sha256` do bundle + verificação no `doctor` (GAP-P1-4);
   decidir se locks de superfície (`surface.lock.json`, `claims.lock.json`)
   viajam no wheel para o `doctor` não reportar `unresolved`.
4. Revisão de conteúdo do `forge.agentic.json` (GAP-P1-2 residual: o
   transporte foi corrigido; o conteúdo publicado continua o do checkout).
5. Resíduos P2: handlers `copilot|all`, `--host` csv/`none`,
   `knowledge path`, convergência `distribution`/`install`, `host_proof`
   multi-runtime, sdist por barra.

## 15. Status por Forge

| Forge | `forge/context/v1` | `_forgecontext` | `_installkit` | `forge_bootstrap` | Status |
|---|---|---|---|---|---|
| the-forge | registry + docs + txn | v1.3.1 | v1.0.1 | v1.1.1 | **merged, pendente de release** (0.6.0) |
| spark-forge-aws | registry + docs + txn | v1.3.1 | v1.0.1 | v1.1.1 | **merged, pendente de release** (0.6.0) |
| **spark-forge-azure** | registry + docs + txn | v1.3.1 | v1.0.1 | v1.1.1 | **merged, pendente de release** (0.2.0) |
| api-forge | registry + docs + txn | v1.3.1 | v1.0.1 | v1.1.1 | **merged, pendente de release** (0.2.0) |
| platform-forge | registry + docs + txn | v1.3.1 | v1.0.1 | v1.1.1 | **merged, pendente de release** (0.2.0) |
| forge-doctor-api | — | ausente | v1.0.1 | v1.1.1 | **installkit only (boundary)** |
| forge-doctor-data | — | ausente | v1.0.1 | v1.1.1 | **installkit only (boundary)**; certifi PYSEC-2026-4320 |
| data-sentinel-forge | — | ausente | v1.0.0 | ausente | **deferred by owner** |

---

## Apêndice — comandos executados para este relatório

```text
git log v0.1.6..HEAD --format='%h %H %s'        → 28 commits
git diff --stat v0.1.6..HEAD                    → 35 files, +7157/−55
sha256sum sparkforge_azure/_forgecontext.py     → 390f5e0e61ab80dc…
sha256sum sparkforge_azure/_installkit.py       → 1484135ae71c396e…
sha256sum scripts/forge_bootstrap.py            → 978862ebedb9ecfb…
grep _FORGECONTEXT_VERSION sparkforge_azure/_forgecontext.py → "1.3.1"
grep -c 'def test_' tests/test_{install_lifecycle,wheel_isolation,
  evals_surface,discovery_ops}.py               → 26/1/22/14
```
