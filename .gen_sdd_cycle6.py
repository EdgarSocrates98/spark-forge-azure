# Gera os sub-SDDs do Cycle 6 (Agentic Engineering Runtime Hardening).
# Padrao sha-encadeado: explore -> define -> design -> plan, upstream {path, sha256}.
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SDD = ROOT / "docs" / "sdd"

AGENT_MDS = sorted(str(p).replace("\\", "/") for p in (ROOT / "agents").glob("*.md"))

FEATURES = {
    "AGENT_INVENTORY": {
        "files": [
            "sparkforge_azure/agentic/inventory.py",
            "sparkforge_azure/cli/cmd_agents.py",
            "sparkforge_azure/cli/main.py",
            "sparkforge_azure/doctor.py",
            "tests/test_agentic_inventory.py",
        ],
        "explore": [
            ("A1", "Status por heuristica espalhada em cada consumidor", ["duplicacao", "deriva"]),
            ("A2", "Modulo agentic/inventory.py com taxonomia de status fechada", ["fonte unica", "testavel"]),
        ],
        "chosen": "A2 — inventario e produto: funcao pura que todo consumidor chama",
        "claim": "Todo agent da taxonomia recebe status do conjunto fechado ready|partial|manifest_only|broken|unevaluated por regras deterministicas sobre manifest+role_plan+evals, sem LLM e sem rede",
        "prediction": "agents list cobre 100% da taxonomia; status e funcao pura do estado do repo; doctor reporta contagens",
        "acceptance": [
            ("AC1", "todo agent da taxonomia recebe status do conjunto fechado ready|partial|manifest_only|broken|unevaluated", "tests/test_agentic_inventory.py::test_every_agent_has_closed_status"),
            ("AC2", "status e deterministico: mesmo repo, mesmo resultado (sem relogio/rede)", "tests/test_agentic_inventory.py::test_inventory_is_deterministic"),
            ("AC3", "agents list e agents inspect <id> cobrem toda a taxonomia e sao read-only", "tests/test_agentic_inventory.py::test_cli_list_and_inspect_cover_taxonomy"),
            ("AC4", "agent sem manifest/plano/eval nunca vira ready por default", "tests/test_agentic_inventory.py::test_missing_artifacts_never_ready"),
            ("AC5", "doctor agentic_fleet reporta contagens por status sem falhar offline", "tests/test_agentic_inventory.py::test_doctor_agentic_fleet"),
        ],
        "kinds": ["agent_or_skill", "tool_or_verb"],
    },
    "AGENT_CONTRACT_V2": {
        "files": [
            "sparkforge_azure/agentmanifest/model.py",
            *AGENT_MDS,
            "tests/test_agent_manifests.py",
            "tests/test_agent_contract_v2.py",
        ],
        "explore": [
            ("A1", "Schema novo paralelo (agents/v2/)", ["dois schemas pra manter", "deriva garantida"]),
            ("A2", "Evoluir schema no lugar, chaves novas obrigatorias", ["fonte unica", "migracao atomica"]),
        ],
        "chosen": "A2 — fonte canonica unica; v2 endurece contrato sem fork de diretorio",
        "claim": "O manifest v2 declara family/domain/mission/inputs/outputs/denied_tools/spawn/stop/handoffs/review_policy/evals com vocabulario fechado; toda a taxonomia migra preservando invariantes v1",
        "prediction": "validator v2 rejeita manifest sem chaves novas; taxonomia ganha test-engineer e evaluation-specialist",
        "acceptance": [
            ("AC1", "manifest v2 exige family, domain, mission, inputs, outputs, denied_tools, spawn.conditions, stop.conditions, review_policy, evals", "tests/test_agent_contract_v2.py::test_v2_required_keys"),
            ("AC2", "family pertence ao vocabulario fechado dos planos", "tests/test_agent_contract_v2.py::test_family_closed_vocabulary"),
            ("AC3", "denied_tools vence allowed: tool em ambos falha; pedido de tool fora da allow list falha", "tests/test_agent_contract_v2.py::test_denied_tools_win"),
            ("AC4", "spawn.conditions e stop.conditions usam vocabularios declarados", "tests/test_agent_contract_v2.py::test_spawn_stop_vocabularies"),
            ("AC5", "invariantes v1 preservadas: handoff DATA_ONLY, sem cloud_write, sem handoff-para-si", "tests/test_agent_contract_v2.py::test_v1_invariants_preserved"),
            ("AC6", "test-engineer e evaluation-specialist entram na taxonomia com manifests completos", "tests/test_agent_contract_v2.py::test_test_eval_roles_in_taxonomy"),
        ],
        "kinds": ["agent_or_skill"],
    },
    "ROLE_PLANS_SPAWN": {
        "files": [
            "sparkforge_azure/agentic/role_plans.py",
            "sparkforge_azure/agentic/spawn.py",
            "sparkforge_azure/cli/cmd_agents.py",
            "tests/test_agentic_role_plans.py",
            "tests/test_agentic_spawn.py",
        ],
        "explore": [
            ("A1", "Tabela ROLE_PLANS escrita a mao para todos os agents", ["deriva contra o manifest"]),
            ("A2", "RoleContextPlan derivado do manifest (fonte unica) + overrides minimos", ["sem duplicata", "manifest e contrato"]),
        ],
        "chosen": "A2 — o manifest ja declara allowed/required context; o plano deriva dele",
        "claim": "Todo agent tem RoleContextPlan derivado do proprio manifest; spawn decision devolve SPAWN|SKIP|DEFER com reason e information gain estruturado; route explica por que cada agent entrou ou ficou de fora",
        "prediction": "spawn sem sinal de dominio = SKIP; incerteza no dominio do specialist = SPAWN; route expõe razao por candidato",
        "acceptance": [
            ("AC1", "todo agent da taxonomia resolve um RoleContextPlan valido (derivado do manifest)", "tests/test_agentic_role_plans.py::test_every_agent_has_role_plan"),
            ("AC2", "spawn decision retorna SPAWN|SKIP|DEFER + reason estruturada", "tests/test_agentic_spawn.py::test_spawn_decision_closed_vocabulary"),
            ("AC3", "sem dominio/unresolved no dominio do agent -> SKIP; high uncertainty no dominio -> SPAWN", "tests/test_agentic_spawn.py::test_spawn_gate_semantics"),
            ("AC4", "route explica por candidato: matched terms, decision, reason; deterministico", "tests/test_agentic_spawn.py::test_route_explainability"),
            ("AC5", "handoff nunca escala privilegio: receiver plan filtra, taint preservado", "tests/test_agentic_role_plans.py::test_no_privilege_escalation_on_handoff"),
        ],
        "kinds": ["agent_or_skill"],
    },
    "TEST_EVAL_AGENTS": {
        "files": [
            "agents/test-engineer.md",
            "agents/evaluation-specialist.md",
            "sparkforge_azure/agentmanifest/model.py",
            "sparkforge_azure/agentic/evalplane.py",
            "tests/test_agentic_test_eval.py",
        ],
        "explore": [
            ("A1", "Dois specialists dominio-especifico", ["sao transversais — plane, nao dominio"]),
            ("A2", "Dois roles novos no plano test/eval, fora do hot path do usuario", ["spec §98/§190", "trigger por change/release"]),
        ],
        "chosen": "A2 — test/eval e plano transversal: roles com spawn por trigger, nao routing de dominio",
        "claim": "test-engineer e evaluation-specialist existem como roles completos (manifest v2 + role plan + budget + evals) com tool policies distintas do resto do sistema",
        "prediction": "test-engineer recebe artifact/code/finding/receipt; evaluation-specialist recebe eval_result/metric/receipt; nenhum escreve",
        "acceptance": [
            ("AC1", "test-engineer e evaluation-specialist validam contra schema v2", "tests/test_agentic_test_eval.py::test_new_roles_validate_v2"),
            ("AC2", "tool policy do test-engineer permite run tests/inspect coverage, nega cloud mutation", "tests/test_agentic_test_eval.py::test_test_engineer_tool_policy"),
            ("AC3", "evaluation-specialist consome eval_result/metric/claim/finding — nunca artifact cru", "tests/test_agentic_test_eval.py::test_eval_specialist_context_policy"),
            ("AC4", "spawn por trigger (change/review/release) via spawn.conditions — nunca por routing de dominio", "tests/test_agentic_test_eval.py::test_spawn_by_trigger_not_domain"),
        ],
        "kinds": ["agent_or_skill"],
    },
    "AGENT_TEAMS": {
        "files": [
            "agent-teams/databricks.yaml",
            "agent-teams/fabric.yaml",
            "agent-teams/streaming.yaml",
            "agent-teams/migration.yaml",
            "sparkforge_azure/agentic/teams.py",
            "tests/test_agentic_teams.py",
        ],
        "explore": [
            ("A1", "Teams hardcoded em python", ["config deveria ser dado", "spec pede arquivo"]),
            ("A2", "agent-teams/*.yaml: eligible + rules, runtime decide subconjunto", ["declarativo", "auditavel"]),
        ],
        "chosen": "A2 — arquivo define elegibilidade; runtime compoe dinamicamente",
        "claim": "Cada vertical tem agent-teams/<vertical>.yaml com eligible agents; o audit garante que membership nao amplia privilegio (tools/context/budget ⊆ manifest proprio)",
        "prediction": "team elegivel != spawn; audit rejeita membro que amplia privilegio",
        "acceptance": [
            ("AC1", "os 4 team files validam: eligible ⊆ taxonomia, nenhum membro ampliado", "tests/test_agentic_teams.py::test_team_files_validate"),
            ("AC2", "audit detecta ampliacao: membro declarando tool/context que o manifest nao tem", "tests/test_agentic_teams.py::test_team_audit_detects_privilege_enlargement"),
            ("AC3", "composicao dinamica: team lista elegiveis; spawn depende de spawn gate, nao do arquivo", "tests/test_agentic_teams.py::test_eligible_is_not_spawned"),
            ("AC4", "reviewer/critic/referee/test-eval plane nunca entram como eligible de team de dominio", "tests/test_agentic_teams.py::test_control_and_eval_planes_not_in_domain_teams"),
        ],
        "kinds": ["agent_or_skill"],
    },
    "AGENTOPS_AGENT": {
        "files": [
            "sparkforge_azure/agentic/spans.py",
            "sparkforge_azure/observability/agentops.py",
            "tests/test_agentic_spans.py",
        ],
        "explore": [
            ("A1", "Estender spans existentes com campos agent", ["schema confunde stage e agent"]),
            ("A2", "AgentSpan proprio + AgentExecutionReceipt agregando considered/spawned/skipped", ["span por execucao de agent", "receipt por case"]),
        ],
        "chosen": "A2 — §56 exige campos de agent; §156 exige receipt de execucao",
        "claim": "Cada execucao de agent emite AgentSpan com campos §56 (tokens None=unresolved nunca estimado de chars); cada case emite AgentExecutionReceipt com considered/spawned/skipped/reasons/budgets/stop",
        "prediction": "waste detector marca agent spawnado sem ganho; receipt lista skipped com reason",
        "acceptance": [
            ("AC1", "AgentSpan carrega agent_id/family/case_id/spawn_reason/context/tokens/cost/stop_reason; tokens desconhecidos sao None, nunca 0 nem estimativa de chars", "tests/test_agentic_spans.py::test_agent_span_fields_and_unknown_tokens"),
            ("AC2", "AgentExecutionReceipt lista agents considered/spawned/skipped com reasons, handoffs, budgets, stop reason", "tests/test_agentic_spans.py::test_execution_receipt_shape"),
            ("AC3", "waste detector: spawned sem facts/findings/unresolved_resolved e sem decision_changed -> waste", "tests/test_agentic_spans.py::test_waste_detector"),
            ("AC4", "agentops report agrega value vector por agent sem score magico", "tests/test_agentic_spans.py::test_agentops_report_value_vector"),
        ],
        "kinds": ["agent_or_skill", "tool_or_verb"],
    },
    "AGENT_LABS_SECURITY": {
        "files": [
            "evals/agents/",
            "tests/fixtures/agentic/",
            "tests/test_agentic_labs.py",
            "tests/test_agentic_security_lab.py",
        ],
        "explore": [
            ("A1", "Labs como scripts soltos em scripts/", ["sem oraculo", "sem determinismo"]),
            ("A2", "evals/agents/ + fixtures + oraculo expect como os outros labs", ["mesmo contrato do Forge Lab"]),
        ],
        "chosen": "A2 — labs sao suites com expect: deterministico, offline",
        "claim": "Os labs §171-183 existem como casos deterministicos: routing esperado, negative routing, overlap minimo, conflito->referee, critic em risco, budget stop, security deny, taint preservado, memory poison rejeitado",
        "prediction": "routing lab cobre os 6 casos canonicos; security lab recusa tool fora da policy; taint nunca lava",
        "acceptance": [
            ("AC1", "routing lab: cada caso canonico roteia para o specialist esperado e so ele", "tests/test_agentic_labs.py::test_routing_lab_expected_specialists"),
            ("AC2", "negative routing: caso sem dominio nao spawna specialist", "tests/test_agentic_labs.py::test_negative_routing_lab"),
            ("AC3", "security lab: tool fora da policy nega; confused deputy nega; impersonation detecta", "tests/test_agentic_security_lab.py::test_security_lab_denies"),
            ("AC4", "taint lab: output malicioso de specialist chega ao receiver com taint preservado", "tests/test_agentic_security_lab.py::test_handoff_taint_lab"),
            ("AC5", "budget lab: budget insuficiente -> stop graceful com reason nomeada", "tests/test_agentic_labs.py::test_budget_lab_graceful_stop"),
            ("AC6", "memory lab: memoria envenenada e rejeitada/quarentenada, nunca autoridade", "tests/test_agentic_security_lab.py::test_memory_poison_rejected"),
        ],
        "kinds": ["agent_or_skill", "fixture_corpus"],
    },
}


def _sha(path: Path) -> str:
    from sparkforge_azure.receipt._hash import text_sha256
    return text_sha256(path)


def _fm(**kw) -> str:
    import yaml
    return "---\n" + yaml.safe_dump(kw, sort_keys=False, allow_unicode=True, width=100) + "---\n"


def build() -> None:
    for feat, spec in FEATURES.items():
        d = SDD / feat
        d.mkdir(parents=True, exist_ok=True)

        (d / "explore.md").write_text(
            _fm(sdd=1, feature=feat, phase="explore", profile="dev", status="done",
                approaches=[{"id": a, "summary": s, "tradeoffs": t}
                            for a, s, t in spec["explore"]],
                chosen=spec["chosen"])
            + f"\n# Explore — {feat}\n\nAlternativas avaliadas; prompt_evo_agentic_enginner.md e a autoridade.\n",
            encoding="utf-8",
        )

        (d / "define.md").write_text(
            _fm(sdd=1, feature=feat, phase="define", profile="dev", status="done",
                upstream={"path": f"docs/sdd/{feat}/explore.md", "sha256": _sha(d / "explore.md")},
                hypothesis={"claim": spec["claim"], "prediction": spec["prediction"],
                            "experiment": "pytest " + spec["acceptance"][0][2].split("::")[0]},
                acceptance=[{"id": a, "statement": s,
                             "verified_by": {"kind": "test", "ref": r}}
                            for a, s, r in spec["acceptance"]],
                success=[{"id": "SC1", "metric": "feature verde offline com ACs cobertos",
                          "source": "pytest " + spec["acceptance"][0][2].split("::")[0]}],
                out_of_scope=["o que nao esta na secao do prompt"],
                unknowns=[],
                change_kinds=spec["kinds"])
            + f"\n# Define — {feat}\n\nArtefato do Cycle 6 (agentic engineering runtime); ver prompt_evo_agentic_enginner.md.\n",
            encoding="utf-8",
        )

        (d / "design.md").write_text(
            _fm(sdd=1, feature=feat, phase="design", profile="dev", status="done",
                upstream={"path": f"docs/sdd/{feat}/define.md", "sha256": _sha(d / "define.md")},
                files=[{"path": f, "action": "create" if "*" not in f else "modify",
                        "reason": "cycle 6"} for f in spec["files"]],
                decisions=[{"id": "D1", "choice": spec["chosen"],
                            "rejected": [s for _, s, _ in spec["explore"] if _ != spec["chosen"][:2]],
                            "rollback": "reverter o commit da feature"}],
                covers=[{"part": feat.lower(), "acceptance": [a for a, _, _ in spec["acceptance"]]}])
            + f"\n# Design — {feat}\n",
            encoding="utf-8",
        )

        tasks = [
            {"id": f"T{i+1}", "files": spec["files"], "covers": [a],
             "test": {"path": ref.split("::")[0], "name": ref.split("::")[1]}}
            for i, (a, _, ref) in enumerate(spec["acceptance"])
        ]
        (d / "plan.md").write_text(
            _fm(sdd=1, feature=feat, phase="plan", profile="dev", status="done",
                upstream={"path": f"docs/sdd/{feat}/design.md", "sha256": _sha(d / "design.md")},
                tasks=tasks)
            + f"\n# Plan — {feat}\n",
            encoding="utf-8",
        )
        print(f"{feat}: ok")


if __name__ == "__main__":
    build()
