"""data_persistence (Onda 3D): checklist de dominio respondido no design/plan.

O gate dispara por declaracao (define com `change_kinds: [data_persistence]`)
ou, so no perfil operator, por deteccao de caminho persistente. Item sem
tratamento vira lacuna `persistence_undeclared`, nunca recusa.
"""

from __future__ import annotations

from pathlib import Path

from sparkforge_azure.sdd.checks import check
from sparkforge_azure.sdd.stamp import stamp

_ITEMS = (
    "atomicity", "isolation", "consistency", "idempotency", "concurrency",
    "versioning", "schema_evolution", "business_key", "reprocessing",
    "retry", "snapshot_commit_rollback", "recovery", "partial_update",
    "negative_tests", "functional_metrics",
)


def _escreve(repo: Path, feature: str, nome: str, meta: str, upstream: str | None) -> Path:
    pasta = repo / "docs" / "sdd" / feature
    pasta.mkdir(parents=True, exist_ok=True)
    up = f"upstream:\n  path: {upstream}\n  sha256: vazio\n" if upstream else ""
    (pasta / f"{nome}.md").write_text(
        f"---\nsdd: 1\nfeature: {feature}\nphase: {nome}\n{meta}\n{up}---\n\n# {nome}\n",
        encoding="utf-8",
    )
    alvo = pasta / f"{nome}.md"
    if upstream:
        stamp(repo, f"docs/sdd/{feature}/{nome}.md")
    return alvo


def _lacunas(repo: Path) -> list[str]:
    return [u["code"] for u in check(repo)["unresolved"]]


def _tratamento() -> str:
    linhas = "\n".join(f"  {i}: tratado ({i})" for i in _ITEMS)
    return "persistence:\n" + linhas + "\n"


def _feature(repo: Path, *, profile: str = "dev", change_kinds: str = "[]") -> None:
    feature = "PERSISTE"
    _escreve(
        repo, feature, "explore",
        f"profile: {profile}\nstatus: done\n"
        "approaches:\n  - id: A1\n    summary: direta\n    tradeoffs: []\n"
        "chosen: A1\n",
        upstream=None,
    )
    _escreve(
        repo, feature, "define",
        f"profile: {profile}\nstatus: done\n"
        "hypothesis:\n  claim: c\n  prediction: p\n  experiment: e\n"
        "acceptance:\n  - id: AC1\n    statement: s\n    verified_by:\n"
        "      kind: test\n      ref: tests/test_x.py::test_x\n"
        "success:\n  - id: SC1\n    metric: m\n    source: relatorio do check\n"
        "out_of_scope: []\n"
        f"change_kinds: {change_kinds}\n",
        upstream="docs/sdd/PERSISTE/explore.md",
    )
    _escreve(
        repo, feature, "design",
        f"profile: {profile}\nstatus: done\n"
        "files:\n  - path: src/writer.py\n    action: create\n    reason: r\n"
        "decisions:\n  - id: D1\n    choice: c\n    rejected: []\n    rollback: rb\n"
        "covers:\n  - part: p\n    acceptance: [AC1]\n",
        upstream="docs/sdd/PERSISTE/define.md",
    )
    _escreve(
        repo, feature, "plan",
        f"profile: {profile}\nstatus: done\n"
        "tasks:\n  - id: T1\n    files: [src/writer.py]\n    covers: [AC1]\n"
        "    test:\n      path: tests/test_x.py\n      name: test_x\n",
        upstream="docs/sdd/PERSISTE/design.md",
    )


def test_persistence_declarada_cobre_o_checklist(tmp_path: Path) -> None:
    _feature(tmp_path, change_kinds="[data_persistence]")
    lacunas = _lacunas(tmp_path)
    # 15 itens por artefato (design e plan), sem tratamento declarado
    assert lacunas.count("persistence_undeclared") == 15 * 2


def test_persistence_respondida_fecha(tmp_path: Path) -> None:
    _feature(tmp_path, change_kinds="[data_persistence]")
    for nome in ("design", "plan"):
        alvo = tmp_path / "docs" / "sdd" / "PERSISTE" / f"{nome}.md"
        texto = alvo.read_text(encoding="utf-8")
        texto = texto.replace("status: done\n", "status: done\n" + _tratamento())
        alvo.write_text(texto, encoding="utf-8")
        stamp(tmp_path, f"docs/sdd/PERSISTE/{nome}.md")
        # reestampa o downstream se for o design
        if nome == "design":
            stamp(tmp_path, "docs/sdd/PERSISTE/plan.md")
    assert "persistence_undeclared" not in _lacunas(tmp_path)


def test_persistence_detectada_so_no_operator(tmp_path: Path) -> None:
    _feature(tmp_path, profile="dev")
    design = tmp_path / "docs" / "sdd" / "PERSISTE" / "design.md"
    texto = design.read_text(encoding="utf-8").replace(
        "src/writer.py", "etl/delta_lake_writer.py")
    design.write_text(texto, encoding="utf-8")
    stamp(tmp_path, "docs/sdd/PERSISTE/design.md")
    stamp(tmp_path, "docs/sdd/PERSISTE/plan.md")
    # dev: caminho com "delta" e codigo de ferramenta, nao escrita de dados
    assert "persistence_undeclared" not in _lacunas(tmp_path)


def test_persistence_operator_detecta_caminho(tmp_path: Path) -> None:
    _feature(tmp_path, profile="operator")
    design = tmp_path / "docs" / "sdd" / "PERSISTE" / "design.md"
    texto = design.read_text(encoding="utf-8").replace(
        "src/writer.py", "etl/onelake_table_writer.py")
    design.write_text(texto, encoding="utf-8")
    stamp(tmp_path, "docs/sdd/PERSISTE/design.md")
    stamp(tmp_path, "docs/sdd/PERSISTE/plan.md")
    lacunas = _lacunas(tmp_path)
    assert "persistence_undeclared" in lacunas
