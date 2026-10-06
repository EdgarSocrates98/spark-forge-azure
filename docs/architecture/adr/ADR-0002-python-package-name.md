# ADR-0002 — Nome do pacote Python: `sparkforge_azure`

- Status: **Accepted** (2026-10-06)
- Contexto e análise completos: [MULTI-FORGE-INSTALLATION.md](../MULTI-FORGE-INSTALLATION.md).

## Decisão

Pacote top-level `sparkforge_azure`, distribuição `sparkforge-azure`, CLI `sparkforge-azure`.
Namespace `sparkforge.azure` rejeitado: o AWS instala `sparkforge` como pacote regular, e PEP 420
não mescla pacote regular com namespace.

## Consequências

- Código portado do AWS recebe rename mecânico de import (`sparkforge.` → `sparkforge_azure.`),
  auditado por `scripts/port_from_aws.py` — único caso permitido de substituição automática; termos
  de domínio nunca são substituídos (§269).
- Prefixos: env `SPARKFORGE_AZURE_*`, estado `.sparkforge-azure/`, MCP tools `sfa_*`.
