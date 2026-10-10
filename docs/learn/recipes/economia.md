# Receita — economia de contexto honesta

**O quê:** `sparkforge-azure tokensave <op>` é a escada de recuperação
L0–L6 — `search` (L1 literal), `symbols`/`refs` (L2), `expand` (L3),
`read` (L5 slice), `diff` — e `context` anda a escada até suficiente.
`benchmark` mede baseline vs profiles num corpus.
**Por que:** regra de ouro do repo — bytes medidos são fact, tokens de
provider só vêm de transcript de host, nunca inferidos. `Observed ≠
Estimated`, `Bytes ≠ Tokens`.
**Quando:** antes de ler arquivo inteiro (regra do AGENTS.md); provar que
um profile economiza de verdade num caso.
**Quando não:** para julgar custo Azure — isso é `azure-finops` /
`collect` + `diagnose`, não tokensave.

## Passo a passo

```bash
sparkforge-azure tokensave context "descrever a tarefa antes de ler"
sparkforge-azure tokensave search --query "<termo>" --root .
sparkforge-azure tokensave read --path <arquivo> --start 1 --end 80
sparkforge-azure tokensave benchmark            # baseline vs profiles
```

`context` resolve com o orçamento do profile (`economy`/`balanced`/`deep`) e
devolve `payload_bytes` medido — `provider_tokens` fica `None`/`unresolved`
sem transcript de host.

## Interpretação

Um `unresolved` em tokens é a resposta honesta — o número exigiria o
transcript real do provider. `payload_bytes` é sempre medido, nunca estimado.

## Verificação

`tokensave benchmark` produz baseline vs profiles no mesmo corpus — é o
único número de economia que o repo aceita (mesma-caso, medido).

## Limitações

O ganho é por caso e profile — extrapolar para "economia geral" sem baseline
é claim que o check_claims reprova.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `provider_tokens: null` | sem transcript de host | honesto — tokens só vêm do provider, não são derivados de bytes |
| `expand` recusa | índice ausente (`--index`) | construa o índice codeintel antes |
