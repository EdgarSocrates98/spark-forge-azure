# Receita — Graphfy: o grafo do workspace

**O quê:** `sparkforge-azure graph` constrói o grafo semântico/de workspace
offline — `build` gera, `query` consulta por kind/layer/neighbors/path,
`impact` mede impacto de mudança, `federate` compõe ids, `view` emite
`forge/ForgeGraphView/v1`, `ui` abre o Graph Studio local.
**Por que:** "o que quebra se eu mudar este dataset" é pergunta de grafo —
`impact` responde com caminho real, não inferência.
**Quando:** revisar dependências antes de mudar, visualizar a estrutura,
consultar relações versionadas.
**Quando não:** para facts de código PySpark (`analyze pyspark`) — grafo é
relação, não julgamento por regra.

## Passo a passo

```bash
sparkforge-azure graph build --root . --out <dir-do-grafo>
sparkforge-azure graph query --graph <dir> --kind <kind> --layer <layer>
sparkforge-azure graph impact --graph <dir> --changed <path-ou-id>
sparkforge-azure graph view --graph <dir>        # documento ForgeGraphView/v1
sparkforge-azure graph ui --graph <dir>          # Graph Studio local
```

`federate` compõe ids explícitos de grafos estáticos/live/artefato/knowledge
numa resposta única — a federação é por id declarado, nunca adivinhada.

## Interpretação

`query` e `impact` devolvem nós/arestas reais do grafo construído — um impact
vazio é "nenhum dependente registrado", não "seguro". `view`/`ui` são a
mesma verdade do grafo em formato visual.

## Verificação

`graph view` emite o documento versionado `forge/ForgeGraphView/v1` — o
mesmo formato que o Graph Studio renderiza.

## Limitações

O grafo é tão completo quanto o que foi indexado no `build`; artefato fora
do manifesto não vira nó. `ui` é local e offline.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| grafo vazio | `build` sem `--root`/manifesto certo | aponte o root do workspace real |
| `impact` sem dependente | mudança em nó folha, ou relação não indexada | confira `graph query` se o nó existe |
