# Cycle 6 — Outcome Brief (Agentic Engineering Runtime Hardening)

`prompt_evo_agentic_enginner.md` implementado em fases/ondas com commit por
wave na branch `feat/cycle6-agentic-runtime`. Tese da spec: **NO AGENT
WITHOUT CONTRACT** — runtime agentico operacional, governado, testavel e
mensuravel, nao uma colecao de arquivos de manifest.

## STATUS

- Agentic runtime hardening = **CONTRACTED + GATED + OBSERVED**

A auditoria inicial (exigida pela propria spec) encontrou um substrato forte
ja existente — manifests v1 estritos (38 agents), routing deterministico,
governor strictest-wins, handoff DATA_ONLY com taint, blackboard, budgets,
recovery. O ciclo formalizou o que faltava: inventario por agent, contrato
v2, role plans derivados, spawn gate, teams, spans agênticos, labs e as
superficies de fechamento (fingerprint, impact graph).

## SHAs

| Marco | SHA |
|---|---|
| `BASE_SHA` | `4f4f57558520460125ed21d836b72e6682261025` (main pós-PR #10) |
| `WAVE0_SDD` | `4240534` — 7 sub-SDDs sha-encadeados (gate vermelho honesto `test_not_written`) |
| `WAVE1` | `bda8c90` — AGENT_INVENTORY |
| `WAVE2` | `b32df99` — AGENT_CONTRACT_V2 |
| `WAVE3` | `a45832c` — ROLE_PLANS + SPAWN GATE |
| `WAVE4` | `2c14ca6` — TEST_EVAL_AGENTS |
| `WAVE5` | `06b5ff4` — AGENT_TEAMS |
| `WAVE6` | `2729032` — AGENTOPS_AGENT |
| `WAVE7` | `13fa056` — AGENT_LABS_SECURITY |
| `CLOSURE` | fingerprint + impact graph + docs + gates (este commit) |
| `FINAL_MAIN_SHA` | commit de merge do PR (post-hoc) |

## W1 — AGENT_INVENTORY

`agentic/inventory.py` + `agents list|inspect` + doctor `agentic_fleet` +
`docs/agentic/AGENT_INVENTORY.md` (gerada). Vocabulario fechado
`ready|partial|manifest_only|broken|unevaluated`. Dimensoes: manifest,
role_plan, tool_policy, knowledge, budget, handoff, routing, evals,
agentops. Resultado honesto: **40/40 `unevaluated`** — contrato completo,
sem evals declarados ainda. `agentmanifest/tools.py` virou o registry
interno que separa verbos de runtime (`sfa_analyze`, `sfa_judge`, …) do
catalogo MCP — sem ele o inventario marcava toda a frota `partial` por
tools validas nao-MCP.

## W2 — AGENT_CONTRACT_V2

Schema v2 nos 40 manifests: `family/domain/mission/inputs/outputs/
allowed_tools/denied_tools/spawn/stop/handoffs/review_policy/evals`.
Resolveu um bug latente: `CallPolicy.from_manifest` ja lia
`manifest.allowed_tools`/`denied_tools` que o modelo v1 nao expunha.
Dois roles novos — `test-engineer`, `evaluation-specialist` — taxonomia
14→16 roles, 38→40 agents.

## W3 — ROLE_PLANS + SPAWN GATE

`role_plan_for` deriva o RoleContextPlan DO MANIFEST (a segunda tabela que
a spec pedia ja existia nos campos v2 — derivar e o que impede a deriva).
`agentic/spawn.py`: SPAWN/SKIP/DEFER com information-gain por trigger
(always/on_domain_match/on_finding_review/on_disagreement/on_conflict/
on_parent_spawn/on_gate). `explain_route` + `agents route`: decisao por
candidato (selected/below_cap/no_match) com matched_terms.

## W4 — TEST_EVAL_AGENTS

CONTEXT_KINDS + `eval_result/metric/claim`. `evaluation-specialist` consome
so o plano de eval — nunca artifact/tool_output cru. `test-engineer` com
policy read-only (tokensave read/symbols). Ambos spawnam por trigger
explicito (on_gate + gate_requested) — nunca por routing de dominio.

## W5 — AGENT_TEAMS

`agent-teams/{databricks,fabric,streaming,migration}.yaml`: elegibilidade
apenas — NUNCA spawn list. `teams.py` audit: eligible ⊆ taxonomia;
familias control/evidence/adversarial/test_eval nunca elegiveis em team de
dominio; subagent exige parent elegivel; max_specialists ≤ ceiling; o
arquivo nao pode ampliar privilegio (allowed_tools/context/budget/trust/
members no YAML = recusa nomeada).

## W6 — AGENTOPS_AGENT

`agentic/spans.py`: `AgentSpan` (lane `agent` do trace persistido) com
contadores de saida — facts/findings/unresolved_resolved/decisions_changed;
tokens/cost `None`+status `unresolved` quando sem fonte. 
`AgentExecutionReceipt`: considered com razao, spawned/skipped/deferred,
handoffs, budgets. `agent_waste`: `empty_agent_spawn` e
`duplicate_agent_spawn` (observed apenas). `agent_value_report`: vetor
multi-eixo por agent, sem score magico.

## W7 — AGENT_LABS_SECURITY

`test_agentic_labs.py`: routing lab (canonico → esperado e so ele;
multi-dominio databricks+uc+adls), negative routing (sem sinal → ninguem),
budget lab (estouro nomeado em qualquer dimensao).
`test_agentic_security_lab.py`: CallPolicy nega tool fora da allowlist;
confused deputy → `handoff_confused_deputy`; origin forjada →
`handoff_sender_origin_mismatch`; poisoned → deny; injecao → SUSPICIOUS +
REVIEW; benigno externo nunca vira clean; memoria com evidencia fabricada →
quarantine/rejeitada.

## CLOSURE — fingerprint + impact + superficies

`agentic/fingerprint.py`: `sha256:` sobre campos de contrato dos 40
manifests + routing table + 4 teams + vocabularios fechados — identidade da
frota detectavel em review (nao e score; o gate/testes medem correcao).
`agentic/impact.py`: grafo de impacto declarado — `agents/<id>.md` → testes
do contrato; `model.py` → fleet-wide; path desconhecido → `unresolved`
(nunca vazio confiante). Verbos `agents fingerprint` e `agents impact` na
CLI (surface lock regerado, cli.md atualizado).

## ESTADO HONESTO DA FROTA

- 40 manifests v2 validados; 4 teams auditadas; 20 rotas deterministicas
- Status da frota: **40 `unevaluated`** — o inventario existe exatamente
  para nao deixar isso invisivel; `evals: []` nos manifests e a proxima
  fronteira (promover para `ready` exige evals executados, nao declarados)
- Fingerprint `sha256:d3901db1…` na data do commit — qualquer drift de
  contrato muda o hash

## VERIFICACAO

```
pytest -q              verde (suites agentic + labs + closure)
sdd check              ok — 7 features Cycle 6, 0 refused
docs-index             ok
docs-surface           ok — agents list/inspect/route/fingerprint/impact
surface.lock           regerado (+2 verbos)
ruff                   clean
REMOTE_CI              NOT_OBSERVED (quota — ignorado conforme instruido)
```

## O QUE ESTE CICLO NAO FEZ (honesto)

- Nenhum agent foi EXECUTADO — a frota esta contratada, roteada, gated e
  observavel; execucao real e o ciclo que vem
- `evals: []` em todos os manifests — `unevaluated` nao e `ready`
- Impact graph cobre a superficie agentica; paths fora dela saem
  `unresolved` por design
