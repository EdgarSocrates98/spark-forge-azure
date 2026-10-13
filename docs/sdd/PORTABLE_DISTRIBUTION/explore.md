---
sdd: 1
feature: PORTABLE_DISTRIBUTION
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: Camada nova `sparkforge_azure/distribution/` — serviço de paths, manifests
      gerenciados (`project.yaml`, `workspace.yaml`), config com precedência registrada,
      ledger de assets gerenciados e detach; CLI fina por cima
    tradeoffs:
      - mais um pacote de produto; cada aresta de import precisa ser declarada
      - reusa paths/durable/doctor existentes — nada duplicado
  - id: B
    summary: Estender `workspace/` e `doctor.py` existentes com init/status/detach
    tradeoffs:
      - mistura lifecycle portátil com o domínio do grafo de workspace; o spec trata
        distribution como camada própria
      - "`workspace/` fica ainda mais carregado e menos testável isolado"
  - id: C
    summary: Portar `apiforge/distribution/` quase literal (COPY_SAFE)
    tradeoffs:
      - api-forge deriva `project_id` do path — quebra §38 (identidade sobrevive a
        mudança de lugar); é ADAPT, não COPY_SAFE, conforme o audit
chosen: A
---

# PORTABLE_DISTRIBUTION — explore

O audit (`docs/portability/PORTABILITY_AUDIT.md`) mostrou que o azure já tem
as fundações — `paths.py` (confinamento), `durable.py` (escrita atômica),
`doctor.py` (diagnóstico offline), `agentmanifest` (espelhos) — mas nenhum
lifecycle portável: não existe init/status/detach, não existe identidade de
projeto independente de path, não existe ledger do que foi escrito.

A abordagem A isola o lifecycle num pacote de produto novo (`distribution/`),
abaixo das superfícies (`cli`), reutilizando kernel e domínio sem
redesenho — exatamente o que §208 pede (camada aditiva sobre a arquitetura
congelada). O B misturaria responsabilidades; o C herda o modelo de
identidade por path que o spec proíbe.

Fronteira desta feature: inspect/init/status/doctor + esqueleto de detach
(verb existe, endurecido em W6); `workspace.yaml` é carregado/validado aqui,
o ciclo de vida completo do ForgeWorkspace (discover/init/add) é W2.
