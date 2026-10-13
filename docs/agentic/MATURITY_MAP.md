# Maturity Map — `prompt_evo_maturity1.md` (≡ `prompt_evo_agentic_enginner.md`)

Auditoria do Cycle 7: cada bloco de seções do prompt mapeado para o artefato
que o entrega, com status honesto. `delivered` = código + teste + doc;
`partial` = existe mas falta cobertura; `missing` = lacuna real. A tabela é
autoral (auditoria de época) — os status de frota ao vivo estão em
`AGENT_INVENTORY.md` (gerado).

## Coberto no Cycle 6 (delivered)

| Seções | Tema | Evidência |
|---|---|---|
| §5–9 | auditoria, inventário, status fechado | `agentic/inventory.py`, `agents list`, `AGENT_INVENTORY.md` |
| §10–14 | coordinator + routing data-driven | `agentmanifest/routing.py` (`ROUTING_TABLE`, `route`, `explain_route`, longest-phrase masking) |
| §15 | manifest v2 | `agentmanifest/model.py`, 40 manifests |
| §16–19 | role context plan, sem transcript completo | `agentic/role_plans.py`, `required_context_kinds` |
| §21–24 | handoff DATA_ONLY, sem privesc, confused deputy | `agentic/handoff.py`, `tests/test_agentic_security_lab.py` |
| §25–28 | blackboard, estado estruturado, anti summary-laundering | `agentic/blackboard.py`, `executor/digest.py` |
| §33–35 | spawn gate SPAWN/SKIP/DEFER + info gain | `agentic/spawn.py`, `agents route` |
| §36–41 | subagents | `agentic/runtime.py` (`nested_agents`, `max_nesting_depth`) |
| §42–51 | test-engineer + evaluation-specialist | manifests + `tests/test_agentic_test_eval.py` |
| §55–60 | spans, waste, value vector | `agentic/spans.py`, `agentops` CLI |
| §61–68 | budgets, strictest wins | `agentic/budget.py`, `GovernorLimits.min_with` |
| §76–83 | referee, conflito, abstain | `agentic/referee.py`, `debate.py`, `arbitration.py` |
| §94–98, §191–196 | domain teams, elegibilidade, anti-amplificação | `agent-teams/*.yaml`, `agentic/teams.py` |
| §126–129 | memory roles, quarantine, poisoning | `agentic/memory.py`, labs de security |
| §149–150 | CLI de inspeção + route explainability | `agents list/inspect/route/fingerprint/impact` |
| §156–158 | receipt, report, timeline | `agentic/spans.py`, `agentops` |
| §205–216 | supply chain, surface lock, fingerprint, impact, claims | `scripts/supply_chain.py`, `docs/surface.lock.json`, `agentic/fingerprint.py`, `impact.py` |

## Lacunas atacadas no Cycle 7

| Seções | Tema | Estado antes | Plano |
|---|---|---|---|
| §101–117 | eval suite por agent, routing quality | `evals: []` ×40; `_eval_coverage` não resolvia artefatos | `evals/agents/<id>.yaml` executáveis via harness (`AGENT_EVAL_SUITE`) |
| §30–32 | base agent graph + branches condicionais | grafo genérico existe; cadeia §30 não declarada | `agentic/pipeline.py` canônico (`BASE_AGENT_PIPELINE`) |
| §52–54 | necessity eval, value vector | vector existe; necessity case-by-case | coberto pelo harness de evals (route positive/negative) |
| §137, §214 | capability manifest | inventário MD gerado | `agents/CAPABILITY.json` gerado (`AGENT_DOD_GATE`) |
| §142 | agent mirrors | `.claude/agents` vazio | mirrors gerados padrão skills (`AGENT_MIRRORS`) |
| §147–148 | agent control MCP sem bloat | 13 tools, nenhuma de agent | `sfa_agents_list` + `sfa_agents_explain_route` read-only (`MCP_AGENT_ADMIN`) |
| §153–155 | autonomy default BOUNDED, human gates | `autonomy.py` tem L0–L5 + `approval_policy` | teste trava default conservador + gates |
| §217–221 | DoD por papel | dims do inventário ≈ core | testes por família (`AGENT_DOD_GATE`) |
| §222–231 | exit criteria, new-agent gate, deprecação | práticas difusas | gate documentado em CONTRIBUTING + enforced por teste |
| §171–182 | labs restantes | labs de routing/security/spawn existem | mapa cobre; novos labs só com valor novo |

## Não-objetivos deste ciclo

- §69–70 model router econômico por agent: `model_tier` já declarado no
  manifest; runtime de roteamento de modelo é superfície nova — fica fora
  por decisão de escopo (não há chamada de modelo a rotear).
- §159–165 execução paralela real/replay: o executor é determinístico e
  sequencial; `runtime.py` já mede `parallel_agents` por harness.
  Implementar paralelismo real exigiria um runner — fora de escopo.
