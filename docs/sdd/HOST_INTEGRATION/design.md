---
sdd: 1
feature: HOST_INTEGRATION
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/HOST_INTEGRATION/define.md
  sha256: "1cd0c37576c06e871b9ee151bb83bcb2f11d5934542baef93816e0534af88f51"
files:
  - path: sparkforge_azure/distribution/managed.py
    action: modify
    reason: "markers primitives (wrap/extract/apply/strip/sha) + modo
      `markers` no assess_file — drift do bloco independente do arquivo"
  - path: sparkforge_azure/distribution/hostfiles.py
    action: create
    reason: "install_host_assets — bloco AGENTS.md/CLAUDE.md + mirrors
      opt-in via render canônico"
  - path: sparkforge_azure/distribution/service.py
    action: modify
    reason: "initialize ganha with_mirrors + chama install_host_assets com
      os hosts detectados"
  - path: sparkforge_azure/distribution/detach.py
    action: modify
    reason: "markers mode → strip do bloco; arquivo vazio é removido"
  - path: sparkforge_azure/cli/cmd_distribution.py
    action: modify
    reason: "flag --with-mirrors em `init`"
  - path: tests/test_host_integration.py
    action: create
    reason: "AC1–AC7 — markers, mirrors, detach, drift"
  - path: tests/test_architecture_layers.py
    action: modify
    reason: "declarar aresta distribution→agentmanifest"
  - path: docs/reference/cli.md
    action: modify
    reason: "flag --with-mirrors documentada"
  - path: docs/portability/HOST_INTEGRATION.md
    action: create
    reason: "doc do modelo de integração de hosts"
  - path: docs/README.md
    action: modify
    reason: indexar HOST_INTEGRATION.md
decisions:
  - id: D1
    choice: "Markers em `managed.py` (mecanismo) + conteúdo em
      `hostfiles.py` (o que escrever) — o ledger já é a autoridade de
      ownership; markers são um terceiro modo de escrita gerenciada ao lado
      de `file` e `merge`."
    rejected:
      - "pacote `hostfiles` com ledger paralelo — duplicaria a fonte de
        verdade do que é nosso"
      - "markers em `paths.py` ou `durable.py` — camadas erradas: markers
        são semântica de *ownership*, não de escrita atômica"
    rollback: "modo novo é aditivo; entradas antigas file/merge inalteradas"
  - id: D2
    choice: "Mirrors opt-in (`--with-mirrors`): 80 arquivos por projeto é
      decisão explícita; o MCP entry já cobre o canal principal."
    rejected:
      - "sempre gerar — polui projetos que só querem o MCP server"
      - "nunca gerar — tira a opção de quem quer agent contracts completos
        no projeto"
    rollback: "detach já remove por kind=agent_mirror; sem migração"
  - id: D3
    choice: "`detect_hosts` guia só a criação de CLAUDE.md — ausência de
      host nunca bloqueia init nem omite o essencial (AGENTS.md sempre)."
    rejected:
      - "criar CLAUDE.md sempre — polui projetos sem Claude e fere 'não
        criar arquivos de host nunca visto'"
    rollback: "flag de detecção é lida na hora; rerun com host novo cria o
      arquivo depois — sem estado a migrar"
covers:
  - part: sparkforge_azure/distribution/managed.py (markers mode)
    acceptance: [AC1, AC2, AC5, AC6, AC7]
  - part: sparkforge_azure/distribution/hostfiles.py (install_host_assets)
    acceptance: [AC1, AC3, AC4]
  - part: sparkforge_azure/distribution/detach.py (markers strip)
    acceptance: [AC5, AC6]
  - part: sparkforge_azure/distribution/service.py (initialize)
    acceptance: [AC1, AC4]
---

# HOST_INTEGRATION — design

## Markers como terceiro modo gerenciado

O ledger já distingue `file` (arquivo nosso) de `merge` (chave nossa dentro
de JSON alheio). `markers` é o equivalente para texto: o *bloco* é nosso, o
arquivo é compartilhado. `assess_file` compara o sha do bloco extraído —
usuário editar fora dos markers não é drift; apagar o bloco é `modified`.

## Install idempotente

`apply_marker_block` upserta entre markers ou appenda quando o arquivo não
tem bloco. Detach stripa e remove o arquivo se esvaziar — arquivo criado
por nós volta a não existir; arquivo do usuário volta ao conteúdo dele.

## Mirrors

`agentmanifest.mirrors.render_agent_mirror(source_text, id)` — o mesmo
render que `sync_agent_mirrors` usa no repo — aplicado sobre os sources
packaged (`_group_dir('agents')` resolve source checkout ou `_data/` do
wheel). Cada arquivo é ledgered `mode=file`, `kind=agent_mirror`,
`host=<root>` — detach remove 1:1.
