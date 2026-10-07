# DESIGN_DEBATE_ROI_GATE (era AgentSpec — arquivado)

> Documento arquivado da era AgentSpec, anterior ao SDD
> (`sparkforge_azure/sdd/`). Mantido para historia: nao descreve o processo
> atual. O sucessor e `docs/sdd/README.md` e o gate em
> `sparkforge_azure/sdd/checks.py`.

## O que este documento fazia

Na era AgentSpec, a decisao de abrir uma feature passava por um *debate gate*:
dois agentes (proponente e revisor) debatiam o retorno sobre investimento da
mudanca antes de qualquer artefato. O gate media:

- **custo estimado** — tokens, arquivos tocados, tempo de revisor humano;
- **retorno esperado** — risco removido, capability nova, divida paga;
- **confianca** — o revisor podia vetar por evidencia insuficiente.

## Por que saiu

O debate era probabilistico sobre premissas declaradas — e o erro que ele
produzia era sutil: um gate eloquente aprovava feature sem criterio
verificavel. O SDD troca o debate por artefatos deterministicos: hipotese com
`prediction` + `experiment`, criterios `AC*` com `verified_by`, e o `red` do
teste falhando antes do codigo. O que o debate tentava garantir por
argumento, o gate garante por recusa nomeada.

## O que ficou do aprendizado

- ROI continua importando, mas como *conteudo* do `define.md` (a hipotese e o
  `success`), nao como ritual de debate.
- A recusa do revisor virou `unresolved`/`refused` com `unlock` — estado
  nomeado, nao opiniao de agente.
