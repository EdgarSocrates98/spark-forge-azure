---
sdd: 1
feature: INSTALL_EVALS_SURFACE
phase: design
profile: dev
status: done
upstream:
  path: docs/sdd/INSTALL_EVALS_SURFACE/define.md
  sha256: "184b84236bc5029a6844cf75b544aa373467619449cad7808241769af413b2fb"
files:
  - {path: sparkforge_azure/evals/taxonomy.py, action: create, reason: "tabela declarada §7.1: 9 suites, categoria, ambiente, selagem, runner por suite + sha256 de integridade"}
  - {path: sparkforge_azure/evals/surface.py, action: create, reason: "evals.run/result sobre a taxonomia; recusas nomeadas; runners delegados (script/pytest/nativo)"}
  - {path: sparkforge_azure/cli/cmd_evals.py, action: create, reason: "verbo `sparkforge-azure evals list|describe|run|result`"}
  - {path: sparkforge_azure/cli/main.py, action: modify, reason: "registrar cmd_evals em COMMAND_MODULES"}
  - {path: sparkforge_azure/discovery_ops.py, action: modify, reason: "EVAL_OPS §7.2 + eval_commands() + eval_ops_expanded() — fonte única"}
  - {path: sparkforge_azure/install/service.py, action: modify, reason: "_context_manifest: eval_suites classificadas + capabilities.evals.detail + eval commands"}
  - {path: sparkforge_azure/discovery.py, action: modify, reason: "capabilities() classificado + ops §7.2"}
  - {path: tests/test_evals_surface.py, action: create, reason: "prova as 7 ACs incluindo o teste de exposição §7.3"}
  - {path: docs/evals-taxonomy.md, action: create, reason: "inventário classificado + mapeamento de ops + postura §7.3"}
  - {path: docs/README.md, action: modify, reason: "indexar docs/evals-taxonomy.md (gate check_docs_index)"}
  - {path: docs/reference/cli.md, action: modify, reason: "documentar o verbo evals (gate check_docs_surface)"}
  - {path: docs/surface.lock.json, action: modify, reason: "lock regenerado com o verbo evals (gate surface_lock)"}
decisions:
  - id: D1
    choice: "os seis ops §7.2 viram discovery.commands nomeados (evals-list, verification-plan...) em vez de entradas em discovery.ops"
    rejected: ["discovery.ops é o vocabulário fechado do §6.2 no _forgecontext.py canônico — adicionar evals.* quebraria validate_manifest e invadiria o módulo do the-forge"]
    rollback: "remover eval_commands() do _context_manifest e EVAL_OPS de discovery_ops"
  - id: D2
    choice: "classificação declarada em evals/taxonomy.py — uma tabela por suite — em vez do varrimento de evals/ que marcava tudo output-verification"
    rejected: ["varrimento não conhece categoria/ambiente/selagem e classificava errado (agentic, host_proof e parity não são output-verification)"]
    rollback: "voltar eval_suites ao iterdir() — perde §7.1 e a selagem"
  - id: D3
    choice: "suites environment=host recusam EVALS-REQUIRES-HOST; corpus sem runner recusa EVALS-RUNNER-UNAVAILABLE"
    rejected: ["executar uma suite de host pela CLI seria o avaliador incorporando o executor — prova sintética marcada como real"]
    rollback: "n/d — recusa é contrato §7.3"
  - id: D4
    choice: "verification.plan/run mapeados para `lab plan`/`lab verify` — os verbos reais do Forge Lab; evidência de execução via `lab run --execute --confirm` + `lab inspect`/`lab reproduce` documentada no op"
    rejected: ["criar um motor de verificação novo duplicaria o pipeline plan->run->receipt que o lab já é"]
    rollback: "n/d"
covers:
  - {part: sparkforge_azure/evals/taxonomy.py, acceptance: [AC1, AC2, AC4]}
  - {part: sparkforge_azure/evals/surface.py, acceptance: [AC5, AC6]}
  - {part: sparkforge_azure/cli/cmd_evals.py, acceptance: [AC5, AC6]}
  - {part: sparkforge_azure/discovery_ops.py, acceptance: [AC3, AC7]}
  - {part: sparkforge_azure/install/service.py, acceptance: [AC2, AC3]}
  - {part: sparkforge_azure/discovery.py, acceptance: [AC1, AC3]}
  - {part: tests/test_evals_surface.py, acceptance: [AC1, AC2, AC3, AC4, AC5, AC6, AC7]}
---

# Design — INSTALL_EVALS_SURFACE

A superfície nova é fina por decisão: `taxonomy.py` declara o que já
existe; `surface.py` despacha para os runners que já existem; o verbo
`evals` só formata e recusa. Nenhum motor de avaliação foi reescrito.
