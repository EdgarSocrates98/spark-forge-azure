---
sdd: 1
feature: FORGE_WORKSPACE
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: Operações de workspace em `distribution/workspace.py` sobre o
      manifesto `workspace.yaml` da W1 — grafo de arestas declaradas, ciclos,
      reachable(scope) reutilizável pelo contexto
    tradeoffs:
      - mantém o lifecycle num só pacote de produto; o schema já existe
  - id: B
    summary: Estender `sparkforge_azure/workspace/` (manifest.py/graph.py
      existentes) com os verbos novos
    tradeoffs:
      - o pacote antigo carrega outro schema de manifest (audit já marcou a
        divergência workspace/manifest.py vs graph/workspace.py); acrescentar
        um terceiro modelo piora a duplicação em vez de convergir
  - id: C
    summary: Discovery por heurística pesada — varrer subdirs procurando
      padrões de projeto e inferir dependências de imports
    tradeoffs:
      - "proibido pelo spec (§33 sem auto-inferir dependência de negócio;
        §24–§26 bounded, sem scan de home)"
chosen: A
---

# FORGE_WORKSPACE — explore

O spec (§20–§36) pede um `ForgeWorkspace` explícito: agrupamento lógico de
projetos, declarado em `.sparkforge-azure/workspace.yaml`, separado de
qualquer noção de workspace de nuvem. A W1 já escreveu o schema de manifesto
(`distribution/manifests.py`): esta feature é o *ciclo de vida* sobre ele.

Duas decisões carregadas do audit: (1) o azure já convive com DOIS loaders de
manifest de workspace (`workspace/manifest.py`, `graph/workspace.py`) — a
feature não adiciona um terceiro, usa o schema novo e declara a divergência
para convergência futura; (2) `paths.resolve_within` rejeita paths fora do
root — a exigência "repo fora do root só quando declarado" é satisfeita na
camada do workspace (`workspace add` é a declaração), sem afrouxar o kernel.

Discovery é sugestão determinística (cwd + ancestrais limitados + filhos
declarados + filhos do root), nunca scan irrestrito nem IA (§24–§27, §33).
