# Receita — diagnóstico de acesso/governança Azure

**O quê:** `sparkforge-azure diagnose --bundle <case>` roda o pipeline de
governança multicamada (Unity Catalog → RBAC → ACL ADLS → rede) sobre um
bundle de case e devolve `failure_layer` + causa raiz com evidência.
**Por que:** falha de acesso em Azure data quase sempre é "RBAC deu, ACL
negou" ou "private endpoint sem DNS" — a camada certa decide a correção.
**Quando:** 403/AuthorizationPermissionMismatch, acesso negado em UC/ADLS,
rede privada que "foi criada mas não funciona".
**Quando não:** custo (`azure-finops`), performance de job (`analyze` +
`judge`), migração (`migration assess`).

## Passo a passo

```bash
# cenário único — bundle com case.yaml + artefatos exportados
sparkforge-azure diagnose --bundle <dir-do-case>

# bateria — diretório de bundles; cada case declara o `expect:` que confere
sparkforge-azure diagnose --suite tests/fixtures/access
```

O bundle é offline: artefatos JSON exportados (grants UC, role assignments,
ACLs, DNS/endpoints). Coleta cloud é opt-in via `collect` (read-only) —
nunca obrigatória.

## Interpretação

Saída traz `status` (`denied`/`allowed`), `failure_layer` (a camada que
bloqueou), `diagnosis` com a cadeia e `evidence_paths` por regra — cada
veredito aponta o fact que o sustenta.

## Verificação

No modo `--suite`, `checks` comparam `actual` vs `expect` por case — verde
só quando a camada E o status batem.

## Limitações

Sem o artefato certo no bundle a camada fica `unresolved` — nunca chutada.
`docs/labs/access.md` cobre os 10 cenários nomeados.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `unresolved` numa camada | artefato ausente no bundle | colete com `collect adls-meta`/`collect azure-rbac`/`collect unity-catalog` |
| failure_layer != esperado | diagnóstico multicamada ordem importa | leia `diagnosis` — a camada anterior passou |
