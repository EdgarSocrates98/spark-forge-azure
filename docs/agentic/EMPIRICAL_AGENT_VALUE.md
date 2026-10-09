# Empirical Agent Value (§50-75)

Harness em `agentic/agent_eval.py` + artefatos em `evals/agent_runtime/`:

```
cases/      4 casos (databricks-access, fabric-onelake, streaming-lag,
            migration)
expected/   required_findings / forbidden_findings / required_evidence /
            known_unresolved por caso (§160)
reports/    resultado canonico §75 por case x config
configs     A deterministic | B +specialist | C +verifier | D full team
```

## O que se mede sem host

- quality: required findings cobertos, forbidden ausentes, unresolved
  conhecidos preservados
- overhead: latencia medida, agents habilitados por config, handoffs
- cost/tokens: `unresolved` — sem provider nao se mede (§55)

## Value vector §57 + necessity §59

`value_vector(result, baseline_A)` -> information_gain, evidence_gain,
uncertainty_reduction, decision_impact, quality_delta, cost,
latency_delta_s. Nunca escalar. `classify_necessity` -> ESSENTIAL |
USEFUL | NEUTRAL | HARMFUL | UNRESOLVED; forbidden finding -> HARMFUL.

## Resultado atual (honesto)

Sem host: todas as configs produzem a mesma fronteira — specialist
resolve `unresolved` nomeado, ganho de informacao = 0 medido -> necessity
`UNRESOLVED`/`NEUTRAL`. Isso e a resposta correta de §243: nao ha prova
de valor de agente sem execucao de host, e o sistema diz isso.
