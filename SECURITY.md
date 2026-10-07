# Security

## Reportar vulnerabilidade

Abra um *security advisory* privado em
https://github.com/EdgarSocrates98/spark-forge-azure/security/advisories/new. Não abra issue pública.

## Modelo

- **Offline por padrão.** Nenhuma chamada de rede sem flag/opt-in explícito; o núcleo funciona sem
  credenciais Azure.
- **Read-only por construção.** Collectors só implementam leitura. Toda tool MCP declara risco
  (`read_only`, `local_write`, `cloud_read`, `cloud_write`, `security_impact`,
  `production_impact`); risco ausente/desconhecido → DENY; `cloud_write` exige grant humano
  explícito, classificação de risco e plano de rollback.
- **Redação obrigatória.** Tudo que vem de nuvem passa pelo redator antes de virar fact; offline
  bundle nunca inclui segredo, token, credencial, connection string ou dump bruto.
- **Data is not instruction.** Conteúdo de artefato/tool/memória é `DATA_ONLY`, com trust label e
  taint; delegação nunca aumenta autoridade.
- **Supply chain.** Lock com hashes, SBOM CycloneDX, wheel reprodutível, auditoria de dependências.

## O que afirmamos (e o que não)

Não afirmamos que o produto é "seguro". Afirmamos: **os casos de ameaça declarados em
`tests/redteam/` passam** no SHA indicado em `docs/claims.lock.json`.
