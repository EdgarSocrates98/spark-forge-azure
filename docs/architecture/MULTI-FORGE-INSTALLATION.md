# RFC — Multi-Forge Installation (§183–§186)

- Status: **Accepted** — implementado em v0.1.0.
- Também registrado como [ADR-0002](adr/ADR-0002-python-package-name.md).

## Problema

`spark-forge-aws`, `spark-forge-azure` e o futuro `spark-forge-gcp` precisam coexistir na mesma
máquina e, idealmente, no **mesmo venv** (um agente que opera ambos). Dois eixos de colisão:

1. **Entrypoint de CLI** — resolvido pelo prompt (§0): `sparkforge-azure`.
2. **Pacote Python importável** — a decidir aqui.

## Fatos medidos

- `spark-forge-aws` distribui `sparkforge-aws` e instala o **pacote regular** `sparkforge/`
  (tem `__init__.py`), com entrypoints `sparkforge` e `sparkforge-tools`.
- Python não mescla pacote regular com namespace package: se o AWS instala
  `site-packages/sparkforge/__init__.py`, um `sparkforge/azure/` de outra distribuição seria
  sobrescrito/ocultado ou sobrescreveria arquivos do AWS (pip reporta conflito de arquivo apenas
  em `RECORD`, não impede).

## Opções

| Opção | Coexistência | Risco |
|---|---|---|
| A. `sparkforge` (mesmo nome) | ❌ colide | sobrescreve `sparkforge/__init__.py` do AWS |
| B. namespace `sparkforge.azure` (PEP 420) | ❌ hoje | exige que o AWS **remova** `sparkforge/__init__.py` — mudança breaking em outro repo |
| C. **`sparkforge_azure`** (pacote top-level próprio) | ✅ | nenhuma; nome não-estético mas explícito |

## Decisão

**C — `sparkforge_azure`.** Distribuição `sparkforge-azure`; entrypoint `sparkforge-azure`.

Regras derivadas:

- Variáveis de ambiente prefixadas `SPARKFORGE_AZURE_*` (nunca `SPARKFORGE_*`, que é do AWS).
- Diretório de estado local `.sparkforge-azure/` (AWS usa `.sparkforge/`).
- Servidor MCP nomeado `sparkforge-azure`; tools prefixadas `sfa_` (AWS: `sparkforge_`).
- Skills instaladas com prefixo de bundle `sparkforge-azure/` para não sobrescrever skills AWS
  de mesmo nome em `~/.claude/skills`.
- Nenhum import cruzado entre Forges. Interoperabilidade **só** via Forge Protocol (JSON).

## Prova

`tests/test_multi_forge_coexistence.py`:
- constrói o wheel e verifica que todo arquivo fica sob `sparkforge_azure/` ou `*.dist-info/`;
- verifica que nenhum entrypoint chama-se `sparkforge` ou `sparkforge-tools`;
- verifica que nenhuma env var lida pelo código começa com `SPARKFORGE_` sem `AZURE_`.

Quando o checkout AWS estiver disponível (`SPARKFORGE_AZURE_AWS_REPO`), o teste opcional instala
ambos no mesmo venv e importa os dois pacotes.

## Futuro

Uma CLI agregadora pertence ao **The Forger** (§0), descobrindo cada Forge via Forge Protocol
(`sparkforge-azure forge describe --json`).
