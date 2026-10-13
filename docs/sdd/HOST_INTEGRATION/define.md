---
sdd: 1
feature: HOST_INTEGRATION
phase: define
profile: dev
status: ready
upstream:
  path: docs/sdd/HOST_INTEGRATION/explore.md
  sha256: "ea257e66d4b03365a1d741ab057789813de5a0d3d12581c0ad4a6f3375a05710"
hypothesis:
  claim: "Init projeta a integração de hosts em arquivos do projeto —
    `.mcp.json` merge, bloco delimitado em AGENTS.md/CLAUDE.md, mirrors
    opt-in — tudo ledgered e reversível, sem tocar home ou checkout"
  prediction: "init cria o bloco em AGENTS.md preservando conteúdo prévio;
    --with-mirrors materializa os dois roots canônicos; detach stripa o
    bloco e remove mirrors, preservando texto de usuário"
  experiment: pytest tests/test_host_integration.py — markers, mirrors,
    detach, drift
acceptance:
  - id: AC1
    statement: "init escreve bloco gerenciado em AGENTS.md gravado como
      mode=markers no ledger"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_init_writes_managed_marker_block
  - id: AC2
    statement: "bloco coexiste com conteúdo prévio e re-init só atualiza a
      região delimitada (idem potência de init)"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_marker_block_coexists_with_user_content
  - id: AC3
    statement: "CLAUDE.md só recebe bloco quando o arquivo já existe ou o
      host claude foi detectado — nada de arquivo de host nunca visto"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_claude_md_only_when_host_seen
  - id: AC4
    statement: "--with-mirrors materializa mirrors renderizados pelo
      gerador canônico nos dois roots, todos ledgered"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_mirrors_opt_in_and_ledgered
  - id: AC5
    statement: "detach stripa só o bloco de markers, preserva texto do
      usuário e remove mirrors ledgered; state sobrevive por default"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_detach_strips_block_preserves_user_text
  - id: AC6
    statement: "mirror ou bloco modificado pelo usuário é preservado e
      reportado — nunca revertido nem deletado"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_detach_modified_managed_file_preserved
  - id: AC7
    statement: "bloco removido/alterado é drift `modified` — reportado,
      não reconquistado em silêncio"
    verified_by:
      kind: test
      ref: tests/test_host_integration.py::test_marker_drift_reported_not_silent
success:
  - id: SC1
    metric: "0 writes fora do project root; 0 writes em home dirs"
    source: sparkforge_azure/distribution/hostfiles.py + detach.py
out_of_scope:
  - instalação home-level (`~/.claude`, `~/.codex/config.toml`) — por
    projeto apenas; global é decisão do usuário
  - "`.devin/` dedicado — Devin carrega AGENTS.md nativamente (audit §67)"
  - probing live de hosts — detecção é PATH-only, `unproven` já é estado
change_kinds:
  - tool_or_verb
---

# HOST_INTEGRATION — define

## Contrato

`distribution init [--with-mirrors]`:

1. `.mcp.json` merge key (W1) — `sparkforge-azure mcp serve`.
2. Bloco `<!-- sparkforge-azure:begin/end -->` em `AGENTS.md` (sempre) e
   `CLAUDE.md` (arquivo existe ou host detectado).
3. Mirrors: `--with-mirrors` renderiza `agents/*.md` packaged via
   `agentmanifest.mirrors.render_agent_mirror` em `.claude/agents/custom/`
   e `.agents/agents/` — `mode=file`, `kind=agent_mirror`.

## Não-objetivos deliberados

Home-level install fica fora — portabilidade é por projeto; mistura de
estado global quebraria isolamento (§62–§63).
