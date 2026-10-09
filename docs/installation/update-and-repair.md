# Update e repair — spark-forge-azure

## Update

```bash
sparkforge-azure install update --to <versão ou tag pinada>
```

`latest` é recusado por contrato — sempre pin a versão. Sem checkout
registrado o update reporta BLOCKED honestamente.

## Repair

```bash
sparkforge-azure doctor   # mostra o drift
sparkforge-azure install repair   # reassegura regiões gerenciadas
```

Repair restaura arquivos gerenciados removidos e cura blocos
`spark-forge-azure:managed` dentro de arquivos seus — conteúdo fora do bloco nunca
é tocado. Antes de sobrescrever, um snapshot vai para
`<state_dir>/backups/`.
