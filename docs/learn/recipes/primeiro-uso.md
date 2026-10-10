# Receita — primeiro uso do spark-forge-azure

**O quê:** o menor caminho real: instalar no projeto, conferir saúde, extrair
facts de um arquivo PySpark e julgar pelo catálogo.
**Por que:** prova a cadeia inteira (CLI → facts → rules → findings) sem
precisar de Azure.
**Quando:** logo após a instalação, ou para validar um ambiente novo.
**Quando não:** para diagnóstico de acesso/governança — aí o caminho é
`diagnose` com um bundle de case (receita `analise-azure`).

## Passo a passo

```bash
sparkforge-azure install --yes          # grava ativos gerenciados
sparkforge-azure doctor                 # saúde local, offline
sparkforge-azure analyze pyspark --path <seu_job.py> --out facts.json  # facts determinísticos (AST)
sparkforge-azure judge --facts facts.json   # aplica o catálogo de regras
```

`analyze pyspark` aceita arquivo ou diretório; cada fact sai com âncora
(file:line:col) — observação, nunca julgamento. `judge` lê os facts e emite
findings com `rule_id` rastreável a `rules/catalog/`.

## Interpretação

Fact ≠ finding: facts são medida; findings citam ≥1 `fact_id` + `rule_id`.
Um analyze sem findings é resultado válido — "nenhuma regra disparou",
não "está tudo certo".

## Verificação

`sparkforge-azure install status` → `healthy`; `doctor` → `ok` por área;
o pipeline analyze→judge deve terminar com findings ou `[]` honesto.

## Limitações

Offline por construção: `analyze`/`judge` nunca tocam Azure. Dado de nuvem
só entra via `collect` (export read-only) num bundle de case.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| judge sem findings | facts insuficientes ou contrato ok | verifique que o analyze leu o arquivo certo |
| `analyze` recusa o arquivo | extensão não é `.py` | só PySpark tem extrator hoje |
