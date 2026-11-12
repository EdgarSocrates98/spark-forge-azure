"""Generate docs/gates-por-mudanca.md from change_kinds.yaml (run once)."""
import io
from pathlib import Path

import yaml

d = yaml.safe_load(
    Path("sparkforge_azure/sdd/change_kinds.yaml").read_text(encoding="utf-8"))

out = io.StringIO()
out.write("""# Gates por tipo de mudanca

Todo tipo de mudanca em `sparkforge_azure/sdd/change_kinds.yaml` mapeia para uma
secao DESTE documento. O gate `sparkforge-azure sdd check` le o frontmatter
`change_kinds:` do ship.md da feature e exige que o ship liste cada registro da
secao correspondente — o titulo da secao abaixo e LITERAL; `tests/test_sdd.py`
trava a deriva nos dois sentidos.

Formato de cada secao: que evidencias o ship precisa citar e como produzi-las.
""")
for kind, v in d.items():
    if not isinstance(v, dict) or "section" not in v:
        continue
    out.write(f"\n## {v['section']}\n\n")
    out.write(f"**change_kind:** `{kind}`\n\n")
    out.write("**Registros obrigatorios no ship.md:**\n\n")
    for r in v.get("registries", []):
        out.write(
            f"- `{r}` — evidencia nomeada; produza via `sparkforge-azure sdd "
            "check` e cite o artefato/run que a gerou.\n")
    out.write(
        "\nRegistro ausente ⇒ recusa `change_kind_registry_missing` com "
        "unlock apontando esta secao.\n")

Path("docs/gates-por-mudanca.md").write_text(out.getvalue(), encoding="utf-8")
print("written", len(out.getvalue()))
