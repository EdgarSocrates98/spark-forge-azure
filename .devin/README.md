# Devin project config — spark-forge-azure

Azure Spark engineering (Databricks, ADLS, Synapse, Event Hubs, Fabric).

- CLI: `sparkforge-azure` (see AGENTS.md for the operating contract).
- Obsidian export: `sparkforge-azure obsidian status|scan|preview|sync-plan|history` (read verbs pre-allowed in `config.json`; `export`/`export-note` mutate the vault and stay gated).
- MCP server: `sparkforge-azure mcp serve --transport stdio` (`mcp_config.json`).
- `config.json` only declares `permissions` (repo-declarable keys); user-level settings are out of scope.
