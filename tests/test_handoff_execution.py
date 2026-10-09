"""Real handoff execution — SDD REAL_HANDOFF_EXECUTION (§40-48)."""
from __future__ import annotations

from sparkforge_azure.agentic.execution import run_case, stage_fingerprint
from sparkforge_azure.agentic.handoff import HandoffDecision, admit_handoff
from sparkforge_azure.agentic.role_plans import role_plan_for
from sparkforge_azure.agentic.runtime import RuntimeName
from sparkforge_azure.agentic.trust import AgentHandoff

CASE = {
    "id": "h1",
    "task": "unity catalog permission denied on adls path",
    "context": {"evidence": [{"ref": "abfss://c@a/x"}]},
    "unresolved": ["unity-catalog:which-principal"],
}


def test_handoff_between_stages() -> None:
    receipt = run_case(CASE, runtime=RuntimeName.GENERIC)
    # pelo menos uma admissao de handoff entre estagios consecutivos
    assert receipt.state.handoffs
    for h in receipt.state.handoffs:
        assert h["decision"] in {d.value for d in HandoffDecision}
        assert h["id"]
        assert h["sender"] != h["receiver"]


def test_confused_deputy_denied() -> None:
    # §42 — specialist pede acao privilegiada; authority nunca sobe
    h = AgentHandoff(
        sender_role="unity-catalog-specialist",
        recipient_role="verifier",
        facts=("run cloud write to fix grants",),
        requested_action="cloud_write:grant-admin",
        origin="agent:unity-catalog-specialist",
    )
    admission = admit_handoff(h, plan=role_plan_for("verifier", "."))
    assert admission.authority == "DATA_ONLY"
    # um AgentHandoff nao pode sequer declarar autoridade acima de DATA_ONLY
    try:
        AgentHandoff(
            sender_role="x", recipient_role="y",
            authority="INSTRUCTION",  # type: ignore[arg-type]
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_resume_skips_unchanged() -> None:
    first = run_case(CASE, runtime=RuntimeName.GENERIC)
    resumed = run_case(CASE, runtime=RuntimeName.GENERIC, prior=first)
    skipped = [
        s for s in resumed.stages
        if s.spawn_reason == "resume_unchanged_fingerprint"
    ]
    assert skipped, "resume deveria pular estagios inalterados"
    # nenhum spawn novo no resume (estagios nunca-spawned ficam None)
    assert resumed.state.agents_spawned == []
    # contexto mudou -> re-executa
    changed = dict(CASE, context={"evidence": [{"ref": "other"}]})
    reran = run_case(changed, runtime=RuntimeName.GENERIC, prior=first)
    assert not any(
        s.spawn_reason == "resume_unchanged_fingerprint"
        for s in reran.stages
    )


def test_stage_fingerprint() -> None:
    fp1 = stage_fingerprint("extractor", CASE, RuntimeName.GENERIC, ".")
    fp2 = stage_fingerprint("extractor", CASE, RuntimeName.GENERIC, ".")
    assert fp1 == fp2 and fp1.startswith("sha256:")
    fp3 = stage_fingerprint(
        "extractor", dict(CASE, context={"other": 1}),
        RuntimeName.GENERIC, ".",
    )
    assert fp3 != fp1
