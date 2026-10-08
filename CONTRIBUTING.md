# Contribuindo

Leia primeiro `AGENTS.md` — e o contrato unico para humanos e agentes neste
repositorio (Facts → Rules → Findings, evidence-first, CLI `sparkforge-azure`).

## Fluxo de mudanca: SDD

Toda mudanca comportamental passa pelo SDD (`docs/sdd/`):

1. `sdd-define` — abre a feature: `docs/sdd/<FEATURE>/define.md` com hipotese,
   criterios `AC*` com `verified_by`, `success` com `source`, `out_of_scope`.
2. `design.md` — arquivos, decisoes com `rollback`, `covers` dos criterios.
3. `plan.md` — tarefas `T*`; no perfil dev cada uma declara o `test` que falha
   antes do codigo; no `operator`, `proof` (funcval/fact/finding).
4. `build_report.md` — `red` (exit != 0) e `green` por tarefa; claims com
   `evidence_ref`; no operator, `change_id` do sandbox.
5. `ship.md` — `hypothesis_outcome`, `registries`, `deviations`, `evidence`.

O gate roda a qualquer momento: `sparkforge-azure sdd check` (no sibling AWS e
`sparkforge sdd check` — aqui o binario e `sparkforge-azure`). Cada falha e uma
recusa nomeada com `unlock`.

## Verificacao antes de entregar

```bash
.venv/Scripts/python -m ruff check sparkforge_azure tests scripts   # Windows
python -m pytest -q
python scripts/check_knowledge.py
python scripts/check_skills_agents.py
python scripts/check_surface_lock.py
python scripts/check_docs_surface.py
python scripts/check_docs_index.py
python scripts/check_claims.py
```

Mudou superficie de CLI/MCP? `python scripts/check_surface_lock.py --update` e
explique no commit — e documente o verbo/tool em `docs/reference/`
(`check_docs_surface.py` falha sem isso). Criou doc? Indexe em
`docs/README.md` (`check_docs_index.py` falha sem isso). Mudou fonte de
knowledge? `python scripts/refresh_knowledge.py --report`.

## Novo agent: gate obrigatorio

Adicionar um agent a frota nunca e so um `.md`. Checklist minimo — cada item
tem enforcement automatizado:

1. `agents/<id>.md` com manifest v2 (`schema_version: 2`), `evals` apontando
   para artefatos que existem (`tests/` ou `evals/`) — `check_skills_agents`
   e `test_eval_refs_must_exist` reprovam refs fantasmas.
2. Registrar o id na taxonomia (`ALL_AGENT_IDS`, familia correta em
   `agentmanifest/model.py`).
3. Role plan resolvendo via `role_plan_for` (`tests/test_agentic_role_plans.py`).
4. Specialist novo? Entra na `ROUTING_TABLE` + ganha
   `evals/agents/<id>.yaml` com `route_positive`/`route_negative` executados
   por `tests/test_agent_eval_cases.py`. Reviewer/subagent novo? Nunca entra
   na `ROUTING_TABLE` — spawna via pai (`test_role_specific_dod`).
5. Regenerar mirrors (`scripts/sync_agent_mirrors.py`) e
   `agents/CAPABILITY.json` (`scripts/gen_agent_capability.py`) — os testes
   de sync reprovam se esquecer.
6. Status deve fechar `ready` ou `partial` em `sparkforge-azure agents list`.

## O que nao entra

- Dado bruto de nuvem, segredo, connection string (`.gitignore` + redator).
- Equivalencia falsa AWS↔Azure — `docs/architecture/AWS_TO_AZURE_PORTABILITY_MATRIX.md`.
- Numero de versao/limite sem URL oficial + `verified_at`.
- `sparkforge` como nome de CLI deste pacote (e o do projeto AWS).
