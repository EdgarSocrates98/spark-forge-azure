# Spark Forge Azure — Portable Quickstart

Run the full lifecycle from an **installed** `sparkforge-azure` — no
source checkout required.

## Install

```text
pip install sparkforge-azure          # or: pipx install sparkforge-azure
sparkforge-azure distribution inspect # package, assets, hosts — no writes
```

## Single project

```text
cd your-repo
sparkforge-azure distribution init    # writes .sparkforge-azure/, .mcp.json, AGENTS.md block
sparkforge-azure distribution status  # drift? managed assets intact?
sparkforge-azure distribution doctor  # offline preflight
```

`init` is idempotent — rerun it to *repair* managed assets. Secrets never
go into manifests or `.mcp.json`; the MCP entry invokes the installed
binary, not a checkout path.

## Workspace (monorepo / multi-repo)

```text
sparkforge-azure workspace init                 # at the shared root — sfw-<id>
sparkforge-azure workspace add app              # child inside root → relative path
sparkforge-azure workspace add ../shared-lib    # outside root → absolute, declared
sparkforge-azure workspace status               # members, cycles, drift
```

Dependencies are declared, never inferred:

```text
sparkforge-azure workspace add app --depends-on <project-id-of-lib>
```

## Bounded context

```text
sparkforge-azure context resolve --target app --scope target       # default
sparkforge-azure context resolve --target app --scope direct       # + direct deps
sparkforge-azure context resolve --target app --scope transitive   # the closure
sparkforge-azure context resolve --scope all                       # explicit only
```

Every resolve writes a receipt (bytes read/avoided, projects selected,
stop reason) — nothing outside the declared roots is ever read.

## Move / copy

```text
mv repo ../elsewhere && sparkforge-azure workspace add ../elsewhere/repo
# same project_id — the old path is gone → relocation recorded

cp -r repo clone && cd clone && sparkforge-azure distribution init --regen-id
# copy must mint its own sfa-<id> before `workspace add` accepts it
```

## Detach

```text
sparkforge-azure distribution detach                 # integration out, state kept
sparkforge-azure distribution detach --purge-state   # .sparkforge-azure gone
sparkforge-azure distribution detach --purge-cache   # cache only
sparkforge-azure distribution detach --dry-run       # report only, no writes
sparkforge-azure distribution init                   # reattach — same project_id
```

Anything you edited stays yours: modified managed files and marker blocks
are preserved with a warning, never reverted.

## Economy

Bounded everywhere: TokenSave per project (confined to its root), scope
`target` by default, receipts account every byte. Cheap *and* honest —
`bytes_avoided` is in the receipt, `unresolved` never silently zero.
