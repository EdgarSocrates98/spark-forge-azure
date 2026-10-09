"""Run REAL host evals — 1 specialist spawn per vertical (§50-75, config B).

    SPARKFORGE_AZURE_HOST_EXECUTION=1 python scripts/run_agent_host_eval.py

Cada case faz UM spawn real via o adapter host (default claude_code) e
grava ``evals/agent_runtime/reports/<case>.host.json`` com custo/tokens
medidos do envelope. Exige opt-in explicito — nunca roda em silencio.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from sparkforge_azure.agentic.agent_eval import (  # noqa: E402
    EVAL_DIR,
    evaluate_case_host,
)
from sparkforge_azure.agentic.runtime import RuntimeName  # noqa: E402


def main() -> int:
    if os.environ.get("SPARKFORGE_AZURE_HOST_EXECUTION") != "1":
        print("refused: SPARKFORGE_AZURE_HOST_EXECUTION=1 required (§199)")
        return 2
    cases_dir = REPO / EVAL_DIR / "cases"
    reports = REPO / EVAL_DIR / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    total_usd = 0.0
    for case_path in sorted(cases_dir.glob("*.yaml")):
        out = evaluate_case_host(
            case_path, root=REPO, runtime=RuntimeName.CLAUDE_CODE)
        dest = reports / f"{out['case_id']}.host.json"
        dest.write_text(
            json.dumps(out, indent=2, ensure_ascii=False, default=str)
            + "\n",
            encoding="utf-8", newline="\n",
        )
        usd = out["result"]["cost"].get("usd") or 0.0
        total_usd += float(usd)
        print(
            f"{out['case_id']}: {out['specialist']} -> "
            f"{out['spawn']['status']} | cost=${usd:.4f} | "
            f"necessity={out['necessity']} | "
            f"violations={len(out['schema_violations'])}"
        )
    print(f"total_cost_usd={total_usd:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
