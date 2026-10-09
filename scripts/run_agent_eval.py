"""Run the agent-runtime A/B eval harness and write reports (§74).

    python scripts/run_agent_eval.py

Deterministico e offline: escreve evals/agent_runtime/reports/<case>.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from sparkforge_azure.agentic.agent_eval import EVAL_DIR, evaluate_case  # noqa: E402


def main() -> int:
    cases_dir = REPO / EVAL_DIR / "cases"
    reports = REPO / EVAL_DIR / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    for case_path in sorted(cases_dir.glob("*.yaml")):
        out = evaluate_case(case_path, root=REPO)
        dest = reports / f"{out['case_id']}.json"
        dest.write_text(
            json.dumps(out, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8", newline="\n",
        )
        print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
