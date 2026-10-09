---
sdd: 1
feature: RELOCATABLE_IDENTITY
phase: explore
profile: dev
status: done
approaches:
  - id: A
    summary: "Id gerado persistido (`sfa-*`/`sfw-*` em project.yaml/
      workspace.yaml) + namespaces lógicos para state/cache/index; colisão de
      cópia é recusa, relocação com path antigo sumido é `relocated`"
    tradeoffs:
      - estado local sobrevive à relocação junto com o diretório
  - id: B
    summary: Id derivado de path (modelo api-forge — `sha256(root)`)
    tradeoffs:
      - "rejeitado no audit: mover o repo muda o id — exatamente o que §38
        proíbe"
  - id: C
    summary: Id derivado do remote git (`git config --get remote.origin.url`)
    tradeoffs:
      - "repo sem remote fica sem id; trocar o remote muda a identidade;
        monorepo compartilha remote entre projetos"
chosen: A
---

# RELOCATABLE_IDENTITY — explore

§37–§43 pedem `identity` separada de `location`: o mesmo projeto mantém o id
ao mover de `/tmp/a` para `/tmp/b`, e uma cópia deliberada precisa de um meio
explícito de cunhar identidade nova. O modelo api-forge (path→hash) resolve
errado nos dois sentidos; remote git não cobre repos locais e monorepos.

O desenho da W1/W2 já entrega a maior parte: ids `sfa-*`/`sfw-*` gerados,
paths relativos dentro do root, resolução contra a raiz atual. O que falta é
o *contrato de cópia*: dois diretórios vivos com o mesmo `project.yaml`
devem ser detectados como colisão — nunca fundidos em silêncio — e uma
relocação real (path antigo sumiu) deve ser registrada como `relocated`,
não como projeto novo.

Namespaces: com `SPARKFORGE_AZURE_STATE_DIR` compartilhado, dois projetos
colidem se o estado for chaveado por path; a saída é namespacing por id
lógico (`state/projects/<id>`) preservando o layout clássico quando o state
já ancora no projeto.
