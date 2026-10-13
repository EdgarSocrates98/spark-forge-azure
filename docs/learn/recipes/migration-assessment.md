# Receita — assessment de migração ADF/Synapse → Fabric

**O quê:** `sparkforge-azure migration` avalia migração ADF/Synapse para
Fabric, **offline**, a partir dos artefatos declarados.
**Por que:** decisão de migração com evidência versionada, não opinião.
**Quando:** discovery de migração, business case, plano de ondas.
**Quando não:** execução da migração — assessment informa, não migra; e não
tocar em ambiente real sem credencial é feature, não bug.

## Problema

"Tenho pipelines ADF — o que migra, o que trava, o que falta decidir?"

## Passo a passo

```bash
sparkforge-azure migration inventory --bundle <dir-do-bundle>
sparkforge-azure migration assess    --bundle <dir-do-bundle> --profile balanced
sparkforge-azure migration plan      --help   # ondas + rollback + blockers
```

Subcomandos reais: `inventory` (censo de prontidão), `assess` (readiness +
recs + ondas + validação), `plan`, `validate` — todos sobre o *bundle* de
artefatos exportado, offline.

## Saída esperada / interpretação

Achados por artefato com severidade e o que ficou `unresolved` — o
assessment reporta lacunas em vez de preencher com chute.

## Verificação

Os achados citam o artefato de origem; re-rodar no mesmo input é
determinístico.

## Limitações

Offline por construção — cobre o que os artefatos declaram; capacidade de
runtime de Fabric/ADF fica `unresolved` sem evidência externa.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| findings vazios | artefatos fora do escopo | aponte o export correto |
| `unresolved` alto | evidência insuficiente | complemente o bundle, não force |

## Uso por agentes

Saída `--format json`; unresolved vai para o brief — nunca vira "aprovado".
