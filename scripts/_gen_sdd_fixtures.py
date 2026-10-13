"""Gerador one-shot das fixtures `fixtures/sdd/` — rode uma vez e apague."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sparkforge_azure.receipt._hash import text_sha256

ROOT = Path("fixtures/sdd")


def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha(path):
    return text_sha256(path)


def explore(feature):
    return (
        f"---\nsdd: 1\nfeature: {feature}\nphase: explore\nprofile: dev\n"
        f"status: done\n---\n\n# Explore\n\nLevantamento da feature {feature}.\n"
    )


def define(feature, acceptance, case_id=None, upstream=None, profile="dev"):
    fm = ["sdd: 1", f"feature: {feature}", "phase: define", f"profile: {profile}",
          "status: done"]
    if upstream:
        fm += ["upstream:", f"  path: {upstream}", "  sha256: __UPSHA__"]
    fm += [
        "hypothesis:",
        "  claim: a feature melhora o fluxo declarado",
        "  prediction: o criterio de aceite passa no gate",
        "  experiment: rodar o criterio verificado",
        "acceptance:",
    ]
    fm += acceptance
    fm += [
        "success:",
        "  - id: SC1",
        "    metric: criterio verificado pelo gate",
        "    source: relatorio do `check` desta fixture",
        "out_of_scope: []",
        "change_kinds: []",
    ]
    if case_id:
        fm.append(f"case_id: {case_id}")
    return "---\n" + "\n".join(fm) + "\n---\n\n# Define\n"


def design(feature, upstream_path, covers, profile="dev"):
    fm = ["sdd: 1", f"feature: {feature}", "phase: design", f"profile: {profile}",
          "status: done", "upstream:", f"  path: {upstream_path}", "  sha256: __UPSHA__",
          "files:",
          "  - path: src/modulo.py", "    action: create", "    reason: novo modulo",
          "decisions:",
          "  - id: D1", "    choice: implementacao direta", "    rejected: []",
          "    rollback: remover o modulo criado", "covers:"]
    for part, acs in covers:
        fm += [f"  - part: {part}", "    acceptance: [" + ", ".join(acs) + "]"]
    return "---\n" + "\n".join(fm) + "\n---\n\n# Design\n"


def plan(feature, upstream_path, tasks, profile="dev"):
    fm = ["sdd: 1", f"feature: {feature}", "phase: plan", f"profile: {profile}",
          "status: done", "upstream:", f"  path: {upstream_path}", "  sha256: __UPSHA__",
          "tasks:"]
    for t in tasks:
        fm += [f"  - id: {t['id']}", "    files: [" + ", ".join(t.get("files", [])) + "]",
               "    covers: [" + ", ".join(t["covers"]) + "]"]
        if "test" in t:
            fm += ["    test:", f"      path: {t['test'][0]}", f"      name: {t['test'][1]}"]
    return "---\n" + "\n".join(fm) + "\n---\n\n# Plan\n"


def build(feature, upstream_path, tasks, change_id=None, profile="dev"):
    fm = ["sdd: 1", f"feature: {feature}", "phase: build_report", f"profile: {profile}",
          "status: done", "upstream:", f"  path: {upstream_path}", "  sha256: __UPSHA__",
          "tasks:"]
    for t in tasks:
        fm += [f"  - id: {t['id']}", f"    status: {t['status']}"]
        if "red" in t:
            fm += ["    red:", f"      command: {t['red'][0]}", f"      exit: {t['red'][1]}"]
        if "green" in t:
            fm += ["    green:", f"      command: {t['green'][0]}", f"      exit: {t['green'][1]}"]
    fm += ["claims:", "  - text: feature concluida conforme o plan",
           "    evidence_ref: tests/"]
    if change_id:
        fm.append(f"change_id: {change_id}")
    return "---\n" + "\n".join(fm) + "\n---\n\n# Build report\n"


def ship(feature, upstream_path):
    fm = ["sdd: 1", f"feature: {feature}", "phase: ship", "profile: dev", "status: done",
          "upstream:", f"  path: {upstream_path}", "  sha256: __UPSHA__",
          "hypothesis_outcome: confirmed", "registries: []", "deviations: []"]
    return "---\n" + "\n".join(fm) + "\n---\n\n# Ship\n"


def stamp(path, new_sha):
    path.write_text(path.read_text(encoding="utf-8").replace("__UPSHA__", new_sha),
                    encoding="utf-8", newline="\n")


# ============ limpo: EXPORTACAO completa ============
base = ROOT / "limpo" / "docs" / "sdd" / "EXPORTACAO"
w(base / "explore.md", explore("EXPORTACAO"))
txt = define("EXPORTACAO", [
    "  - id: AC1", "    statement: exporta o relatorio",
    "    verified_by:", "      kind: test",
    "      ref: tests/test_exportacao.py::test_exporta",
], upstream="docs/sdd/EXPORTACAO/explore.md").replace("__UPSHA__", sha(base / "explore.md"))
w(base / "define.md", txt)
w(base / "design.md", design("EXPORTACAO", "docs/sdd/EXPORTACAO/define.md",
                             [("exportador", ["AC1"])]))
stamp(base / "design.md", sha(base / "define.md"))
w(base / "plan.md", plan("EXPORTACAO", "docs/sdd/EXPORTACAO/design.md",
    [{"id": "T1", "files": ["src/exportador.py"], "covers": ["AC1"],
      "test": ("tests/test_exportacao.py", "test_exporta")}]))
stamp(base / "plan.md", sha(base / "design.md"))
w(base / "build_report.md", build("EXPORTACAO", "docs/sdd/EXPORTACAO/plan.md",
    [{"id": "T1", "status": "done",
      "red": ("pytest tests/test_exportacao.py::test_exporta", "1"),
      "green": ("pytest tests/test_exportacao.py::test_exporta", "0")}]))
stamp(base / "build_report.md", sha(base / "plan.md"))
w(base / "ship.md", ship("EXPORTACAO", "docs/sdd/EXPORTACAO/build_report.md"))
stamp(base / "ship.md", sha(base / "build_report.md"))
w(ROOT / "limpo" / "tests" / "test_exportacao.py",
  "def test_exporta():\n    assert True\n")

# ============ cascata: IMPORTACAO, sha errado no design ============
base = ROOT / "cascata" / "docs" / "sdd" / "IMPORTACAO"
w(base / "define.md", define("IMPORTACAO", [
    "  - id: AC1", "    statement: importa o lote",
    "    verified_by:", "      kind: command", "      ref: pipeline run --check",
]))
w(base / "design.md", design("IMPORTACAO", "docs/sdd/IMPORTACAO/define.md",
                             [("importador", ["AC1"])]).replace("__UPSHA__", "0" * 64))

# ============ cobertura: CADASTRO, design nao cobre AC2 ============
base = ROOT / "cobertura" / "docs" / "sdd" / "CADASTRO"
w(base / "define.md", define("CADASTRO", [
    "  - id: AC1", "    statement: cadastra o cliente",
    "    verified_by:", "      kind: command", "      ref: cadastro check --id",
    "  - id: AC2", "    statement: rejeita duplicado",
    "    verified_by:", "      kind: command", "      ref: cadastro check --dup",
]))
w(base / "design.md", design("CADASTRO", "docs/sdd/CADASTRO/define.md",
                             [("cadastro", ["AC1"])]))
stamp(base / "design.md", sha(base / "define.md"))

# ============ tdd: FATURAMENTO, task done sem red ============
base = ROOT / "tdd" / "docs" / "sdd" / "FATURAMENTO"
w(base / "define.md", define("FATURAMENTO", [
    "  - id: AC1", "    statement: fatura o pedido",
    "    verified_by:", "      kind: test",
    "      ref: tests/test_faturamento.py::test_fatura",
]))
w(base / "design.md", design("FATURAMENTO", "docs/sdd/FATURAMENTO/define.md",
                             [("faturador", ["AC1"])]))
stamp(base / "design.md", sha(base / "define.md"))
w(base / "plan.md", plan("FATURAMENTO", "docs/sdd/FATURAMENTO/design.md",
    [{"id": "T1", "files": ["src/faturador.py"], "covers": ["AC1"],
      "test": ("tests/test_faturamento.py", "test_fatura")}]))
stamp(base / "plan.md", sha(base / "design.md"))
w(base / "build_report.md", build("FATURAMENTO", "docs/sdd/FATURAMENTO/plan.md",
                                  [{"id": "T1", "status": "done"}]))
stamp(base / "build_report.md", sha(base / "plan.md"))
w(ROOT / "tdd" / "tests" / "test_faturamento.py",
  "def test_fatura():\n    assert True\n")

# ============ operador: JOB_VENDAS operator, change_id ausente ============
base = ROOT / "operador"
w(base / ".sparkforge-azure" / "case.yaml", "case_id: case-2026-09-28-job\n")
feat = base / "docs" / "sdd" / "JOB_VENDAS"
w(feat / "define.md", define("JOB_VENDAS", [
    "  - id: AC1", "    statement: o job de vendas roda",
    "    verified_by:", "      kind: command", "      ref: job run --check",
], case_id="case-2026-09-28-job", profile="operator"))
w(feat / "design.md", design("JOB_VENDAS", "docs/sdd/JOB_VENDAS/define.md",
                             [("job", ["AC1"])], profile="operator"))
stamp(feat / "design.md", sha(feat / "define.md"))
w(feat / "plan.md", plan("JOB_VENDAS", "docs/sdd/JOB_VENDAS/design.md",
    [{"id": "T1", "files": ["jobs/vendas.py"], "covers": ["AC1"],
      "test": ("tests/test_job_vendas.py", "test_vendas")}], profile="operator"))
stamp(feat / "plan.md", sha(feat / "design.md"))
w(feat / "build_report.md", build("JOB_VENDAS", "docs/sdd/JOB_VENDAS/plan.md",
    [{"id": "T1", "status": "done",
      "red": ("pytest tests/test_job_vendas.py::test_vendas", "1"),
      "green": ("pytest tests/test_job_vendas.py::test_vendas", "0")}],
    profile="operator"))
stamp(feat / "build_report.md", sha(feat / "plan.md"))
w(base / "tests" / "test_job_vendas.py", "def test_vendas():\n    assert True\n")
print("fixtures escritos")
