# TokenSave benchmark — caso UC/ADLS

Reproduzível:

```bash
sparkforge-azure tokensave benchmark --case evals/token_efficient/access_case
```

Corpus: `evals/token_efficient/access_case` — bundle de diagnóstico UC/ADLS
(espelho de `tests/fixtures/access/s01_uc_privilege_denied` enriquecido):
`case.yaml`, `unity_catalog.json` (3 credentials, 4 locations, 5 schemas,
8 tables, 5 grants), `rbac.json`, `adls.json` (6 ACLs), `entra.json`,
`network.json`, 4 notebooks, `README.md` — 11 arquivos.

## Medição atual (commit desta doc)

| profile  | bytes lidos | bytes evitados | níveis | status     |
|----------|-------------|----------------|--------|------------|
| baseline | 10415       | 0              | —      | (leitura integral) |
| economy  | 1964        | 8451           | L1     | sufficient |
| balanced | 2981        | 7434           | L1     | sufficient |
| deep     | 2981        | 7434           | L1     | sufficient |

`bytes` = payload entregue ao contexto, medido como
`len(json.dumps(payload, ensure_ascii=False, sort_keys=True))`.
**Tokens: `unresolved`** — nenhuma chamada a provider existe neste caminho;
inventar um número violaria a regra "observed ≠ estimated".

## O que o benchmark prova

- O ladder para no primeiro nível suficiente: os termos exigidos do caso
  (`abfss`, `spn-job-1`, `loc_finance`, `cred_lake`) são cobertos por L1
  (search literal); L2–L6 nunca disparam (AC3).
- `read_full` (L6) é recusado fora do profile `deep` e exige `reason`
  declarada (AC4).
- A métrica é honesta: bytes medidos do ledger, `bytes_avoided` contra o
  baseline do mesmo corpus, nunca um multiplicador de "tokens estimados".

Regenerar: `sparkforge-azure tokensave benchmark --case evals/token_efficient/access_case`
e atualizar a tabela quando o corpus ou o engine mudarem.
