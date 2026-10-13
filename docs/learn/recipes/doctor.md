# Receita — minha instalação está íntegra?

**O quê:** `sparkforge-azure doctor` checa pacote, dependências e ambiente
com detalhe acionável por check.
**Por que:** diagnóstico antes de qualquer workflow.
**Quando:** pós-install, troca de máquina, antes de `lab`/`collect`.
**Quando não:** saúde de serviços Azure — doctor é local e offline.

## Passo a passo

```bash
sparkforge-azure doctor --format json
```

Saída real observada:

```json
{"area": "installation", "status": "ok",
 "detail": "sparkforge-azure 0.1.0 on Python 3.12.13 (win32)"},
{"area": "dependencies", "status": "ok",
 "detail": "core dependencies importable (PyYAML, jsonschema)"}
```

## Interpretação

`ok`/`warn`/`fail` por área (`installation`, `dependencies`, `cli`, …);
falhas trazem `data` com o contexto do check.

## Verificação

Re-rodar após o remédio deve virar `ok` na área correspondente.

## Limitações

Local e offline — não valida credencial Azure nem endpoints.

## Erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `dependencies: fail` | pacote fora do venv | `pip install -e .` no venv certo |
| `cli` não achado | launcher fora do PATH | re-rodar o setup |

## Uso por agentes

Workflow `doctor` do `forge.agentic.json`; `--format json` máquina-first.
