"""`sparkforge-azure lab <op>` CLI wiring (CI contract: ci.yml + scheduled.yml).

The dispatch lives in `sparkforge_azure.lab.cli`; these tests assert the
argparse bridge: leafs exist, `verify` maps `valid` to the CLI status/exit
contract, `run --all` iterates the Golden suite as dry-run plans, and the
mutation guard refuses `--execute` without `--confirm` before any command is
built.
"""

from __future__ import annotations

import json

from sparkforge_azure.cli.main import command_paths, main


def _payload(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_lab_leafs_are_registered():
    paths = command_paths()
    for leaf in (
        "lab doctor",
        "lab verify",
        "lab scenarios",
        "lab describe",
        "lab plan",
        "lab run",
        "lab inspect",
        "lab compare",
        "lab promote-fixture",
        "lab reproduce",
        "lab up",
        "lab down",
        "lab shell",
        "lab gc",
    ):
        assert leaf in paths, f"missing CLI leaf: {leaf}"


def test_lab_verify_passes_with_contract_artifacts(capsys):
    assert main(["lab", "verify"]) == 0
    payload = _payload(capsys)
    assert payload["valid"] is True
    assert payload["status"] == "pass"
    assert payload["scenario_count"] == 20
    assert payload["missing"] == []


def test_lab_run_all_emits_dry_run_plans(capsys):
    assert main(["lab", "run", "--all"]) == 0
    payload = _payload(capsys)
    assert payload["count"] == 20
    assert len(payload["scenarios"]) == 20
    assert all(
        item["execution"]["status"] == "planned" for item in payload["scenarios"]
    )


def test_lab_run_requires_scenario_or_all(capsys):
    assert main(["lab", "run"]) == 2
    payload = _payload(capsys)
    assert payload["status"] == "refused"
    assert "scenario" in payload["error"]


def test_lab_execute_without_confirm_is_refused(capsys):
    assert (
        main(["lab", "up", "--profile", "core", "--execute"]) == 2
    )
    payload = _payload(capsys)
    assert payload["status"] == "refused"
    assert "confirm" in payload["error"]


def test_lab_up_without_execute_is_a_plan(capsys):
    assert main(["lab", "up", "--profile", "core"]) == 0
    payload = _payload(capsys)
    assert payload["status"] == "ok"
    assert payload["lab_status"] == "planned"
    assert payload["execute"] is False
    assert "compose.yaml" in " ".join(payload["command"])
