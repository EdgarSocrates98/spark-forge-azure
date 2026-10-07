# PROCESSO (era AgentSpec — arquivado)

> Arquivado na migracao para o SDD. Ver `docs/sdd/README.md` para o fluxo atual.

O AgentSpec era um plugin (`.claude/settings.json` hoje registra
`agentspec@agentspec: false`) que guiava features por specs em `.claude/sdd/`:

1. **spec livre** — markdown sem schema, validado por revisao de agente;
2. **debate** — dois agentes discutiam a spec ate consenso ou veto;
3. **aprovacao humana** — o revisor assinava o plano;
4. **execucao** — a spec guiava a implementacao, sem gate deterministico.

Faltava o que o SDD formalizou depois: schema por fase, `upstream.sha256`
ligando artefato ao seu antecessor, criterios `AC*` com `verified_by`, e
recusas nomeadas. O que a revisao humana pegava, o gate pega antes.
