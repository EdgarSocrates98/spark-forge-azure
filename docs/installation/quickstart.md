# Quickstart — spark-forge-azure

Três comandos:

```bash
git clone <spark-forge-azure repo>
cd spark-forge-azure
./install.sh      # Windows: .\install.ps1 — account runtime + editable CLI
```

Depois, dentro de qualquer projeto:

```bash
cd ~/meu-projeto
sparkforge-azure install
```

Pronto. Abra seu AI host (Devin, Claude, Codex ou Copilot) — as skills do
spark-forge-azure já estão instaladas.

Em diretório vazio, o wizard oferece `Entire workspace` e `My user account`;
`Current repository` aparece somente quando há VCS detectado.

## Verificar

```bash
sparkforge-azure distribution status
sparkforge-azure doctor
```

Detalhes: [account-installation.md](account-installation.md). Problemas? → [troubleshooting.md](troubleshooting.md)
