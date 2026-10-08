---
sdd: 1
feature: STRUCTURED_STREAMING
phase: build_report
profile: dev
status: done
upstream:
  path: docs/sdd/STRUCTURED_STREAMING/plan.md
  sha256: "b97302bd137834e21084a37027a25d362bdecca6b3a7eec1c67a2a952821728c"
tasks:
  - id: T1
    status: done
    red: {command: "cd .tmp-red-c4 && python -m pytest tests/test_stream_progress.py -q", exit: 2}
    green: {command: "python -m pytest tests/test_stream_progress.py -q", exit: 0}
claims:
  - text: "query_progress vira serie temporal de facts stream.progress"
    evidence_ref: "tests/test_stream_progress.py::test_progress_events_become_facts"
  - text: "single-batch dip nao e lag sustentado"
    evidence_ref: "tests/test_stream_progress.py::test_single_batch_dip_not_lag"
  - text: "checkpoint ausente + start latest cai na camada checkpoint como risco"
    evidence_ref: "tests/test_stream_progress.py::test_checkpoint_deleted_latest_risk"
  - text: "crescimento de estado exige serie de progresso"
    evidence_ref: "tests/test_stream_progress.py::test_state_growth_needs_series"
---

# Build Report — STRUCTURED_STREAMING

Red em worktree `.tmp-red-c4` @ `86b1910` (pre-Streaming/RTI): testes copiados para o worktree falham com ModuleNotFoundError (exit 2); green em `feat/cycle4-streaming`.
