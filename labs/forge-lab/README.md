# Forge Lab / Digital Twin

Forge Lab is a local reproduction blueprint and evidence factory for streaming
and batch incidents. The analyzer reads `lab.yaml`; it does not start Compose,
stop a broker, mutate a table or call a cloud provider.

The product contract lives in `lab/versions.yaml` and
`lab/scenarios/golden.yaml`.

## Inspect topology

```python
from sparkforge_azure.lab.spec import analyze_forge_lab

analyze_forge_lab("labs/forge-lab/lab.yaml")
```

The output includes component dependency order, a deterministic fingerprint,
offline readiness, unresolved declarations and seven topological scenario plans:

- `broker_kill`
- `skew`
- `consumer_lag`
- `checkpoint_failure`
- `small_files`
- `schema_evolution`
- `cdc_restart`

Those seven scenarios describe the topology blueprint in `lab.yaml`. The
versioned executable corpus is the Golden 20 in `lab/scenarios/golden.yaml`,
which is compiled and checked by `sparkforge_azure.lab.contract`.

The `sparkforge-azure lab` commands expose the same contract from the CLI:

```bash
sparkforge-azure lab verify            # registry + suite + contracts + probes
sparkforge-azure lab scenarios         # the Golden 20 with fingerprints
sparkforge-azure lab plan LAB-001      # compiled runtime plan (dry-run)
sparkforge-azure lab run LAB-001       # plan + status; --all for the suite
```

`run`/`plan` emit `planned` unless the operator passes `--execute --confirm`
on a host — the guard lives in the lab, not the CLI layer.

## Run locally

1. Choose pinned images in a private `.env` file; do not commit credentials.
2. Review the scenario and its expected evidence.
3. Inspect and compile the scenario first.
4. Start only the requested profile with Docker Compose.
5. Capture metrics, logs, checkpoints and table metadata.
6. Tear down only after preserving evidence needed for diagnosis.

Image availability, compatibility, ports and runtime versions remain unresolved
until the operator validates them on the host. Runs belong in
`.sparkforge-azure/lab/runs/`, never in Git. Nothing here claims that Docker
images are available or that a cloud run occurred.
