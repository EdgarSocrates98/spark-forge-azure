# Receita — usar os agents do spark-forge-azure

**O quê:** a frota tem 40 agents (roles, specialists, subagents, executores)
com contrato v2: `kind`, `domain`, `autonomy` L0–L2, `risk` e evals. Tudo é
inventariável e roteável por comando.
**Por que:** escolher agente é dado, não julgamento — `agents route` explica
o caminho determinístico e o spawn gate de cada candidato.
**Quando:** antes de delegar uma investigação a um specialist (ex.:
`adf-specialist`, `unity-catalog-specialist`, `fabric-specialist`).
**Quando não:** para rodar análise direta sem host — os verbos `analyze`/
`diagnose`/`judge` não precisam de agente.

## Passo a passo

```bash
sparkforge-azure agents list                    # status de cada agent
sparkforge-azure agents inspect <id>            # contrato completo de um agent
sparkforge-azure agents route "<tarefa>"        # rota + spawn gate explicados
sparkforge-azure agents runtimes                # adapters de runtime + prova
sparkforge-azure agents execute "<tarefa>"      # dry-run do plano (nunca executa o host)
```

`execute` é sempre dry-run do plano — o dispatch real é do host (Devin,
Claude, Codex), instalado via `sparkforge-azure install --host <h>`.

## Interpretação

`autonomy` ≤ L2 por contrato — reviewer/subagent é spawn-only e nunca entra
na routing table top-level. `route` devolve candidato + razão, não execução.

## Verificação

`agents list` cobre os 40 ids do catálogo gerado
(`docs/reference/AGENTS.md`); `agents route` sempre devolve um
`recommended_agent` ou a recusa nomeada.

## Limitações

O agente despachado como subagente não despacha executores — subagente não
pode criar subagente; a decomposição roda inline.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| "executor não aparece no host" | executores não são publicados no layout de discovery | orquestre pelo coordenador, não pelo nome do executor |
| route devolveu candidato errado | prompt ambíguo | nomeie o domínio (adf, fabric, uc, event-hubs) no prompt |
