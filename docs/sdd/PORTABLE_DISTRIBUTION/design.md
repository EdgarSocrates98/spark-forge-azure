---
sdd: 1
feature: PORTABLE_DISTRIBUTION
phase: design
profile: dev
status: ready
upstream:
  path: docs/sdd/PORTABLE_DISTRIBUTION/define.md
  sha256: "fdb30266d3587920a19f61b3bf0f497e9eb466344c4644598d094f3e98c70ad2"
files:
  - path: sparkforge_azure/distribution/__init__.py
    action: create
    reason: API pública do pacote — exports mínimos, sem lógica
  - path: sparkforge_azure/distribution/errors.py
    action: create
    reason: vocabulário fechado de `kind` + PortableError + refused_document
  - path: sparkforge_azure/distribution/paths.py
    action: create
    reason: resolve_paths único — package/executable/state/cache/config/project/
      workspace, cada um com source registrado (§45, §103–§105)
  - path: sparkforge_azure/distribution/discovery.py
    action: create
    reason: caminhada de ancestrais limitada (MAX_ANCESTORS=24) procurando os dois
      manifests — determinística, offline, sem varrer home (§24–§26)
  - path: sparkforge_azure/distribution/manifests.py
    action: create
    reason: schemas estritos de project.yaml/workspace.yaml — ids gerados
      independentes de path, paths declarados normalizados, segredos recusados
  - path: sparkforge_azure/distribution/config.py
    action: create
    reason: precedência defaults<user<workspace<project<cli com fonte por chave;
      chave desconhecida recusa (strict) ou é reportada (§44–§47)
  - path: sparkforge_azure/distribution/assets.py
    action: create
    reason: inventário de assets empacotados com sha256; resolve _data/ na wheel
      e dirs de fonte no checkout (mesmo modelo de doctor.data_root)
  - path: sparkforge_azure/distribution/hosts.py
    action: create
    reason: catálogo de hosts (claude/devin/codex) + detecção por PATH sem falha
      + entry MCP apontando o binário instalado (§65–§79)
  - path: sparkforge_azure/distribution/managed.py
    action: create
    reason: ledger managed.json — path/kind/sha256/mode/owned_keys;
      apply_json_key preserva conteúdo do usuário; drift detectável (§82, §110)
  - path: sparkforge_azure/distribution/service.py
    action: create
    reason: operações inspect/init/status/doctor — o que os verbos chamam
  - path: sparkforge_azure/distribution/detach.py
    action: create
    reason: remoção só do registrado; state preservado por default; dry-run;
      modificado vira trabalho do usuário e é preservado (§80–§89)
  - path: sparkforge_azure/cli/cmd_distribution.py
    action: create
    reason: verbos distribution * sobre o service — wrapper converte
      PortableError em documento refused estruturado
  - path: sparkforge_azure/cli/main.py
    action: modify
    reason: registrar cmd_distribution em COMMAND_MODULES (lista fechada)
  - path: tests/test_distribution.py
    action: create
    reason: AC1–AC9 — lifecycle, drift, precedência, recusas, env overrides
  - path: tests/test_architecture_layers.py
    action: modify
    reason: declarar arestas cli→distribution e distribution→durable com razão
  - path: docs/reference/cli.md
    action: modify
    reason: seção `sparkforge-azure distribution <op>` — gate docs_surface
  - path: docs/surface.lock.json
    action: modify
    reason: regen do lock com os 5 verbos novos (tool_or_verb → surface_lock)
  - path: docs/portability/PORTABLE_DISTRIBUTION.md
    action: create
    reason: doc da camada — contrato, paths, config, ledger, detach, estados
decisions:
  - id: D1
    choice: "Identidade é `sfa-<uuid24>` gerada e persistida em
      .sparkforge-azure/project.yaml — nunca derivada de path (§38). Path do
      projeto é *localização*, resolvida a cada chamada."
    rejected:
      - "sha256 do path (modelo api-forge) — quebra na relocação; audit marcou ADAPT"
      - "derivar do remote git — repo sem remote ou com remote trocado muda de id"
    rollback: "o manifest é state local regenerável; trocar o esquema é
      migration de estado, não de API"
  - id: D2
    choice: "Ledger `managed.json` registra path+sha256+mode+owned_keys. mode
      `merge` grava também o sha do valor de cada chave — drift de *valor* é
      detectado, não só presença."
    rejected:
      - "só existência da chave — passou no primeiro teste e falhou: usuário
        mudando o valor não era detectado"
    rollback: "ledger é regenerável; entradas órfãs viram drift `missing`"
  - id: D3
    choice: "Detach trata `project.yaml`/`workspace.yaml`/receipt/ledger como
      *state* — preservados por default; removidos só com --purge-state (§84–§85).
      Asset modificado é trabalho do usuário: preservado com warning, não revertido."
    rejected:
      - "apagar project.yaml no detach default — destrói identidade e impede
        reattach com o mesmo id"
    rollback: "--purge-state cobre o caso de remoção completa explícita"
  - id: D4
    choice: "Config fecha num vocabulário KNOWN_CONFIG_KEYS pequeno; chave
      desconhecida recusa em strict, reporta em inspect (strict=False)."
    rejected:
      - "aceitar qualquer chave — erro de digitação vira config silenciosamente
        morta (§47)"
    rollback: "ampliar KNOWN_CONFIG_KEYS é aditivo; recusar chave é só remover
      do conjunto — sem migração de estado"
  - id: D5
    choice: "Hosts são detectados por `shutil.which` apenas — available/
      unavailable/unproven; ausência nunca falha doctor (§76–§77). MCP entry
      usa o binário `sparkforge-azure`, não path de checkout (§74–§75)."
    rejected:
      - "sondar versão do host — probe vira dependência de runtime do init"
    rollback: "a entrada gerenciada sai inteira via detach; adicionar probes
      depois é aditivo no HostSpec"
covers:
  - part: sparkforge_azure/distribution/errors.py
    acceptance: [AC4]
  - part: sparkforge_azure/distribution/paths.py
    acceptance: [AC9]
  - part: sparkforge_azure/distribution/discovery.py
    acceptance: [AC1]
  - part: sparkforge_azure/distribution/manifests.py
    acceptance: [AC2, AC7]
  - part: sparkforge_azure/distribution/config.py
    acceptance: [AC6]
  - part: sparkforge_azure/distribution/assets.py
    acceptance: [AC1, AC8]
  - part: sparkforge_azure/distribution/hosts.py
    acceptance: [AC8]
  - part: sparkforge_azure/distribution/managed.py
    acceptance: [AC2, AC4]
  - part: sparkforge_azure/distribution/service.py
    acceptance: [AC1, AC2, AC3, AC4]
  - part: sparkforge_azure/distribution/detach.py
    acceptance: [AC5]
  - part: sparkforge_azure/cli/cmd_distribution.py
    acceptance: [AC1, AC2, AC3, AC4, AC5]
---

# PORTABLE_DISTRIBUTION — design

## O grafo de arquivos

`errors` e `discovery` são folhas do pacote. `paths`, `config`, `assets`,
`hosts` dependem só de `errors`. `manifests` e `managed` usam `durable`
(escrita atômica do kernel). `service` compõe tudo; `detach` usa `managed` +
`discovery`. A CLI (`cmd_distribution`) é a única superfície — arestas novas
declaradas: `cli→distribution` e `distribution→durable`.

## Estado em `.sparkforge-azure/`

```
project.yaml      identidade relocável (sfa-*, name, created, generator, config)
workspace.yaml    ForgeWorkspace declarado (W2 opera; aqui é lido/validado)
managed.json      ledger do que escrevemos — o que torna detach seguro
receipt-distribution.json   recibo do último init
cache/            raiz de cache (SPARKFORGE_AZURE_CACHE override)
```

`.mcp.json` na raiz do projeto é o único arquivo fora do state dir — é o
ponto de integração MCP projeto-scope dos hosts; possuímos só a chave
`mcpServers.sparkforge-azure` (modo merge), nunca o arquivo inteiro.

## Riscos e mitigações

- **Escrita fora do projeto**: só `.mcp.json` na raiz + state dir; overrides
  de env são explicitamente do operador. Nada em HOME (§104).
- **Symlink/traversal**: `resolve_declared_path` resolve contra a raiz atual;
  manifests rejeitam conteúdo fora do vocabulário; `paths.resolve_within` do
  kernel segue intacto para o resto do pacote.
- **Drift silencioso**: ledger + sha256 de arquivo e de valor de chave —
  `status` expõe `partial`/`drifted`/`broken` em vez de re-escrever.
