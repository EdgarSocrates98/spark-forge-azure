---
sdd: 1
feature: CONTEXT_RESOLUTION
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Orquestrar o que já existe: `reachable` (W2) decide o conjunto
      de projetos; `scan_repository` enumera bounded; `TokenSave.context`
      anda L0→L6 por projeto confinado à própria raiz"
    tradeoffs:
      - zero código de retrieval novo — o resolve é composição e recibo
      - "sem --task não materializa conteúdo — resolve = conjunto + contagem"
  - id: B
    summary: Índice único multi-repo (um grafo que abrange o workspace)
    tradeoffs:
      - "viola §61 (indexar por project_id) e §64 (fronteira por projeto);
        mistura namespaces — rejeitado"
  - id: C
    summary: Resolver dentro do `context/gateway.py` existente
    tradeoffs:
      - "gateway governa *itens* de contexto com role/budget; a decisão
        workspace→projetos é da camada de distribuição — gateway continua
        consumidor, não resolvedor"
chosen: A
---

# CONTEXT_RESOLUTION — explore

§52 pede o pipeline `manifest → target → graph → locality → TokenSave →
CodeIntel → ContextPack`. Tudo já existe isoladamente: `reachable` (W2)
implementa locality declarada, `TokenSave` tem escada L0→L6 com ledger de
bytes, `codeintel_db` (W3) namespaceia índice por `project_id`. O trabalho
é a *orquestração* + o recibo §58 — e a garantia §64 de que conteúdo não
atravessa fronteira de projeto sem aresta declarada.

Decisão-chave: `--task` separa "resolver o conjunto" de "materializar
contexto". Sem task, o verbo responde só quais projetos/quantos arquivos —
barato e determinístico; com task, cada projeto roda sua própria escada
confinada e o recibo agrega bytes.
