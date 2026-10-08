# Access lab — UC/ADLS (prompt #126-139)

Labs do vertical de acesso. Tudo offline, determinístico, reproduzível.

## Scenarios 1–10 — `diagnose --suite`

```bash
sparkforge-azure diagnose --suite tests/fixtures/access
```

Cada diretório `tests/fixtures/access/sNN_*` é um case bundle
(`case.yaml` + artefatos). O bloco `expect:` do `case.yaml` é o oráculo; o
runner compara `status`/`failure_layer` esperados vs medidos e emite o
`evidence_paths` de cada caso (finding → fact → artefato).

| #  | fixture                       | esperado                        | prompt |
|----|-------------------------------|----------------------------------|--------|
| 1  | s01_uc_privilege_denied       | `denied` / `unity_catalog`      | #127   |
| 2  | s02_rbac_control_plane_only   | `denied` / `azure_rbac`         | #128   |
| 3  | s03_acl_missing_execute       | `denied` / `adls_acl`           | #129   |
| 4  | s04_private_dns_not_linked    | `denied` / `network`            | #130   |
| 5  | s05_workspace_not_bound       | `denied` / `workspace_binding`  | #131   |
| 6  | s06_no_covering_location      | `denied` / `external_location`  | #132   |
| 7  | s07_governance_bypass         | `findings` / `governance_bypass`| #133 (contextual, não auto-vuln) |
| 8  | s08_legacy_access_mode        | `denied` / `runtime`            | #134   |
| 9  | s09_delta_direct_path         | `findings` / `delta_perf`       | #135   |
| 10 | s10_missing_evidence          | `unresolved` (ABSTAIN)          | #136   |

Cobertura: `tests/test_access_suite.py`, `tests/test_access_pipeline.py`,
`tests/test_access_scenarios.py`.

## Security lab — taint (#137)

`tests/test_security_taint.py` injeta `IGNORE PREVIOUS INSTRUCTIONS ...` em
quatro superfícies e prova `trust.taint == "suspicious"`,
`instruction_authority == "data_only"`, e veredito inalterado:

- **table comment** — `unity_catalog.json` → tables[].comment
- **resource tag** — `adls.json` → tags
- **notebook metadata** — célula/comentário em `notebooks/*.py`
- **tool result** — `entra.json` display_name (payload de collector)

O scan de trust cobre **toda a entrada crua** do bundle (case + artefatos +
bytes de notebook), não só os facts extraídos — texto malicioso em campo
descartado pela extração continua flaggeado.

## Graph lab — static/live merge (#138)

`tests/test_access_graph_federation.py` prova: merge por ARM-id,
`observed_by` multi-fonte, `attr_conflicts` com valores canônicos,
provenance por escrita (primeiro escritor na ordem static→live→artifact
vence), bindings ausentes como `unresolved` — nunca link por nome.

## TokenSave lab — mesmo caso, 4 perfis (#139)

```bash
sparkforge-azure tokensave benchmark --case evals/token_efficient/access_case
```

Baseline (leitura integral: 10415 B) vs `economy` (1964 B) / `balanced` /
`deep` (2981 B). Medido: `docs/tokensave/benchmark.md`.

## Knowledge escopado (#151-153)

Cada relatório traz `knowledge`: os packs de `knowledge/packs.yaml`
mapeados pelo `failure_layer` + `excluded_domains` (prova de que
fabric/synapse/adf ficaram fora). Ver `docs/reference/knowledge-packs.md`.
