# SDD_EVAL — a suite agentica do SDD

Seis perguntas sobre os cinco repositorios sinteticos de `fixtures/sdd/`
(`limpo`, `cascata`, `cobertura`, `tdd`, `operador`). Cada resposta e um valor
so — `code`, `path`, id de criterio ou fase — porque cada fixture foi montada
para produzir exatamente uma recusa (ou nenhuma, no `limpo`).

O gabarito nao e confianca: `tests/test_sdd_eval_suite.py` recomputa cada
`answer` rodando `sdd.checks.check` e `sdd.status.status` sobre o fixture — a
suite falha se alguem editar `answer` sem que o gate concorde.

## Baseline

Os scorecards de referencia moram em `baselines/<data>-<origem>/r*.json` e sao
pontuados contra o sha256 da suite resolvida (`Suite.sha256` cobre protocolo +
perguntas, nao os bytes do YAML). A semente atual veio de duas invocacoes
manuais do runner em `--repeat 1`:

    python scripts/run_agentic_eval.py --suite sdd --repeat 1 --prepare-only
    python scripts/run_agentic_eval.py --suite sdd --repeat 1 --prepare-only

As duas invocações produzem contratos identicos (o plano e deterministico) e os
scorecards `r1.json`/`r2.json` em `baselines/2026-10-02-manual/` registram a
rodada contra esta suite, pergunta por pergunta. Regravar o baseline exige
rodar as duas invocações de novo e revisar o diff — nao editar o JSON na mao.
