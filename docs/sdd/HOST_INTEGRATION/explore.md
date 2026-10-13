---
sdd: 1
feature: HOST_INTEGRATION
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Init escreve arquivos de host por-projeto, todos no ledger:
      `.mcp.json` (merge), bloco delimitado em AGENTS.md/CLAUDE.md
      (markers), mirrors opt-in via --with-mirrors"
    tradeoffs:
      - "cobertura de hosts sem depender de home dir ou checkout"
      - markers são o único modo de texto gerenciado novo (merge/file já
        existiam)
  - id: B
    summary: "Instalar em home-level como o AWS `integrate/` (`~/.claude`,
      `~/.codex/config.toml`)"
    tradeoffs:
      - "rejeitado: escopo do prompt é portabilidade *por projeto*; home
        global é decisão do usuário e mistura estado entre projetos"
  - id: C
    summary: Gerar mirrors sempre (sem flag)
    tradeoffs:
      - "80 arquivos em todo projeto é barulho; opt-in mantém init magro —
        o MCP entry já cobre o canal principal"
chosen: A
---

# HOST_INTEGRATION — explore

§65 pede portabilidade funcionando com Claude Code, Devin, Codex, MCP
clients e generic agents "sem reinventar agent contracts". As fronteiras
reais: `.mcp.json` (MCP clients + Claude + Codex + Devin), `AGENTS.md`
(genérico/Codex/Devin), `CLAUDE.md` (Claude), mirrors `.claude/agents/
custom/` + `.agents/agents/` (§66 — mesma geração do repo).

O AWS `integrate/` (3312 linhas) faz instalação *home-level* com manifesto
próprio em `~/.sparkforge` — modelo diferente do alvo aqui. O que se porta
é a *semântica*: owned keys, drift por hash, remoção só do possuído.
Markers em arquivo editável é o mecanismo que o AWS não tem e o spec exige
(§70): bloco delimitado upsert-able, user content fora intocado.
