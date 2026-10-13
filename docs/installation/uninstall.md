# Uninstall — spark-forge-azure

```bash
sparkforge-azure install uninstall            # remove só arquivos gerenciados
sparkforge-azure install uninstall --purge    # + remove o estado local (.sparkforge-azure/)
```

O ledger SHA-256 decide ownership: arquivos que você criou ou modificou
depois da instalação ficam no lugar (reportados como `kept`). Diretórios
que esvaziam são podados; os seus permanecem.
