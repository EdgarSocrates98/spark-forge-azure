# ADR-0003 — Dois verticais, um núcleo (Databricks + Fabric)

- Status: **Accepted** (2026-10-08)
- Ciclos: 2 (UC/ADLS) e 3 (Microsoft Fabric)

## Contexto

Os Cycles 2 e 3 entregaram dois verticais de diagnóstico sobre a mesma
plataforma. O risco clássico de um segundo vertical é a duplicação silenciosa:
motor paralelo, grafo paralelo, memória paralela — e cada bug passa a existir
duas vezes. O prompt do Cycle 3 exigia explicitamente o contrário: Fabric como
vertical profundo *sem* reimplementar a base.

## Decisão

1. **Núcleo compartilhado, vertical fino.** Facts/findings/verdicts, motor de
   regras, evidence paths, AgentOps, trust/taint, receipts, Graphfy, TokenSave e
   knowledge scoping ficam no núcleo (L0–L4). Cada vertical contribui apenas:
   casefile loader, extratores determinísticos, cadeia de diagnóstico, catálogo
   de regras (`SF-ACC-*` / `SF-FAB-*`), fixtures e knowledge packs marcados com
   `vertical:`.
2. **Fronteiras de domínio respeitadas.** Workspace Databricks (ARM) e workspace
   Fabric (SaaS) são grafos separados com loaders separados; `vertical:` nos
   packs impede que material de UC vaze para um caso Fabric `unresolved` (bug
   real encontrado e corrigido no Cycle 3).
3. **Superfície simétrica, não fundida.** `diagnose` e `diagnose fabric` são
   verbos irmãos; `sfa_diagnose_access` e `sfa_diagnose_fabric` idem. Nenhum
   comando “universal” tenta adivinhar o vertical — o caller declara.
4. **Documentação é superfície.** `scripts/check_docs_surface.py` garante que
   todo comando/tool do `surface.lock.json` tem seção em
   `docs/reference/cli.md`/`mcp-tools.md`; verbo novo sem doc falha o gate.
5. **Skills verticais têm o mesmo contrato de eval.** Skills `fabric-*` entram
   em `VERTICAL_SKILLS`: todo eval exige trigger positivo, negativo e caso de
   fronteira — o mesmo regime das skills de acesso.

## Consequências

- Adicionar um terceiro vertical (ex.: Purview, Event Hubs profundo) segue o
  mesmo molde: loader + extratores + cadeia + regras + fixtures + packs —
  sem tocar o núcleo.
- O gate de docs torna drift de documentação um erro de build, não um achado
  de auditoria.
- Custos permanecem compartilhados: um fix em AgentOps, trust ou TokenSave vale
  para os dois verticais automaticamente.

## Rejeitado

- **Vertical Fabric independente** (pacote próprio): duplicaria núcleo e
  quebraria a promessa de custo/qualidade do projeto.
- **Comando único `diagnose --vertical x`**: esconde a fronteira de domínio e
  incentiva bundle híbrido mal definido.
