---
sdd: 1
feature: UPSTREAM_FACTS_INTAKE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/UPSTREAM_FACTS_INTAKE/define.md
  sha256: 899ab89fa3df3931d096a6389189c3f2b41c60b3ea9aa78d818267b729105dc5
files:
- path: sparkforge_azure/adapters/upstream.py
  action: create
  reason: validador fail-closed do documento upstream-facts/v1
- path: sparkforge_azure/azure/casefile.py
  action: modify
  reason: upstream.json vira artefato do bundle (CaseBundle.upstream_facts)
- path: sparkforge_azure/fabric/casefile.py
  action: modify
  reason: mesmo seam nos 4 dominios
- path: sparkforge_azure/stream/casefile.py
  action: modify
  reason: mesmo seam nos 4 dominios
- path: sparkforge_azure/migration/casefile.py
  action: modify
  reason: mesmo seam nos 4 dominios
- path: sparkforge_azure/azure/pipeline.py
  action: modify
  reason: facts upstream publicados na saida, nunca no input do judge
- path: sparkforge_azure/fabric/pipeline.py
  action: modify
  reason: idem
- path: sparkforge_azure/stream/pipeline.py
  action: modify
  reason: idem
- path: sparkforge_azure/migration/pipeline.py
  action: modify
  reason: idem
- path: tests/test_upstream_facts.py
  action: create
  reason: contrato dos ACs
decisions:
- id: D1
  choice: upstream facts ficam dicts e so entram na serializacao `facts` —
    nunca viram findings.Fact (id e propriedade derivada; rederivar lavaria a
    identidade estrangeira)
  rejected:
  - converter para Fact nativo (mata a garantia `upstream:` e o id estrangeiro)
  - alimentar judge com eles (regras casam por kind nativo; upstream.* nao
    casa, mas o input correto e nao chegar la)
  rollback: remover campo + adapter + testes
- id: D2
  choice: artefato `upstream.json` (JSON apenas) no bundle; ausente = sem
    upstream; presente e invalido = CaseError
  rejected:
  - parametro por chamada MCP (bundle e a unidade de evidencia; parametro
    solto fugiria do receipt, que cobre sources)
  rollback: remover leitura dos 4 casefiles
covers:
- part: upstream_facts_intake
  acceptance: [AC1, AC2, AC3, AC4]
---
