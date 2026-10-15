---
id: cyc9-05
title: scenarios-data-engineering-azure
status: active
created: 2026-10-15
owner: spark-forge-azure
scope: repo
cycle: 9
wave: 3
priority: p1
risk: medium
agent: codex
source: prompt_evo_cycles.md §9.3 Data Engineering Azure
verification:
  - python -m pytest -q
  - python -m ruff check sparkforge_azure tests scripts
  - sparkforge-azure sdd check
  - python scripts/check_surface_lock.py
---

# Cenários Forge Lab — Data Engineering Azure

## Outcome

Biblioteca versionada de cenários do domínio Spark/Fabric Azure com fixtures locais e ground truth: revisão PySpark, arquitetura de pipeline, cenários Fabric, Data Factory, governança, streaming.

## Grill gate

- Problema observado: capacidades do especialista sem cenários mensuráveis.
- Usuário afetado: Benchmark Engineer e usuário avaliando o especialista.
- Falha concreta: claims de qualidade sem dataset verificável.
- Decisão: cenários do §9.3 Azure como fixtures sintéticos + diagnósticos classificados, limitados às capacidades suportadas.
- Fora de escopo: acesso a Azure real como requisito; centralizar motor no the-forge.
- Critério de parada: ao menos um cenário por categoria suportada, executável localmente e integrável ao harness federado.

## Acceptance

- Cenários versionados por categoria: revisão PySpark, arquitetura de pipeline, Fabric, Data Factory, governança, streaming.
- Cada cenário: fixture + entrada + resultado esperado + diagnóstico classificado (ground truth).
- Execução local sem credenciais; saída compatível com contrato de métricas (cyc9-02).
- Categorias não suportadas → `not_available`, não simuladas.

## Constraints

- Independência: roda sem the-forge/CLI/Portal.
- Sem credenciais Azure em fixtures.

## Verificação

- Confirmar no dispatch: `python -m pytest` / gates do repo.

## Pending

- ⚠ Capacidades efetivamente implementadas (baseline cyc0-01).
