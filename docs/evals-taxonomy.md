# Evals taxonomy — install-2.0 §7 (lf-0038)

Inventário classificado do corpus de avaliação desta forja. Fonte única:
`sparkforge_azure/evals/taxonomy.py` — servida por
`sparkforge-azure evals list|describe|run|result` e persistida no
manifesto `forge/context/v1` (`eval_suites[].kind` +
`capabilities.evals.detail`).

## As 4 categorias (§7.1)

| Categoria | O que prova |
|---|---|
| `developer` | qualidade interna — roteamento dos agents, portabilidade, economia, paridade de corpus |
| `runtime-decision` | decisões do runtime — findings permitidos/proibidos, unresolved preservados |
| `output-verification` | o contrato do resultado — convergência cross-vertical |
| `host-conformance` | conformidade de host — provas reais de execução, matriz MCP, suite agentic |

## Inventário

| Suite | Categoria | Ambiente | Selada | Runner |
|---|---|---|---|---|
| `agentic-sdd` | host-conformance | host | sim | `scripts/run_agentic_eval.py --suite sdd` + `python -m sparkforge_azure.evals grade` |
| `agent-runtime` | runtime-decision | deterministic | sim | in-process `agent_eval.evaluate_case` (configs A–D) |
| `agents-routes` | developer | deterministic | sim | `pytest tests/test_agent_eval_cases.py` |
| `convergence` | output-verification | deterministic | sim | `python evals/convergence/runner.py --json` |
| `host-proof` | host-conformance | host | não | prova de host (`claude -p`) + recibos commitados |
| `mcp-conformance` | host-conformance | deterministic | não | `pytest tests/test_mcp_conformance_matrix.py` |
| `parity` | developer | deterministic | sim | corpus — verificada por `check_token_efficient_bench.py` + `check_aws_parity.py` |
| `portability` | developer | deterministic | sim | `python evals/portability/runner.py --json` |
| `token-efficient` | developer | deterministic | sim | `python scripts/check_token_efficient_bench.py` |

Contagem: developer=4, runtime-decision=1, output-verification=1,
host-conformance=3.

## Ops §7.2 → verbos reais

| Op conceitual | Verbo |
|---|---|
| `evals.list` | `sparkforge-azure evals list` |
| `evals.describe` | `sparkforge-azure evals describe --suite <id>` |
| `evals.run` | `sparkforge-azure evals run --suite <id>` |
| `evals.result` | `sparkforge-azure evals result --suite <id> --run <run>` |
| `verification.plan` | `sparkforge-azure lab plan <cenario>` |
| `verification.run` | `sparkforge-azure lab verify` (+ evidência: `lab run --execute --confirm` → `lab inspect`/`lab reproduce --receipt`) |

Os seis ops são publicados como `discovery.commands` nomeados
(`evals-list`, …, `verification-run`) no manifesto — `discovery.ops` é o
vocabulário fechado do §6.2 (`_forgecontext.py` canônico, outro dono) e
permanece inalterado. O verbo `capabilities` expõe o mesmo mapa em
`evals.ops`.

## Postura §7.3

- **Gabarito selado nunca sai**: `list`/`describe` emitem id, categoria,
  ambiente e `integrity.suite_sha256` — nunca o conteúdo de `expected/`
  ou `baselines/`. `tests/test_evals_surface.py` prova por grepping de
  fatias reais das respostas em todos os payloads.
- **Baselines protegidas por hash**: `evals describe` publica o sha256
  agregado do diretório da suite; o `compare` do
  `python -m sparkforge_azure.evals` resolve baselines por nome, nunca
  por caminho arbitrário.
- **Executor ≠ avaliador**: suites `environment=host` recusam
  `EVALS-REQUIRES-HOST` — a CLI não incorpora o agente medido. Corpus sem
  runner próprio (`parity`) recusa `EVALS-RUNNER-UNAVAILABLE`.
- **Simulado ≠ real**: todo resultado carrega `environment` e
  `real_environment_proof` — `deterministic` prova o engine, nunca um
  ambiente vivo; `host-proof` é a única prova de ambiente real.

## §7.4 — plan → run → evidence

`lab plan <cenario>` compila o plano de verificação; `lab run --execute
--confirm` executa sob guarda explícita; `lab inspect`/`lab reproduce
--receipt` registram e verificam a evidência. Falhas e `unresolved` são
estados explícitos de saída, nunca promovidos a pass.

## §7.5 — contrato de agents

Diferente do sibling AWS, esta forja não tem `AGENT_PROTOCOL.md`
portado: o contrato canônico do agente é o manifest `schema_version: 2`
em cada `agents/*.md` (`sparkforge_azure.agentmanifest.model`), e os
mirrors de host em `.claude/agents/`, `.agents/agents/` são gerados
byte-a-byte por `scripts/sync_agent_mirrors.py` — verificados
`in_sync`. Nenhum texto de protocolo é duplicado nos mirrors; o que cada
agente referencia é o contrato versionado, não uma cópia.
