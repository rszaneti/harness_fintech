# Comando: /spec-plan

> **Título**: Gerar Plano Técnico (Camada 2 — SDD)
> **Descrição**: A partir de uma `spec.md` aprovada, gera o `plan.md` (design técnico) na mesma
> pasta da feature. Não gera tasks, não gera código.

## Uso

```
/spec-plan <nome-da-feature>
```

## Pré-condições (verificar antes de qualquer coisa)

1. `spec.md` existe em `.claude/specs/a_fazer/<feature>/` (ou `em_andamento/`)
2. `Status: aprovada` na spec — **se não estiver aprovada, PARAR** e pedir aprovação via `/spec-new`
3. Seção "Questões em aberto" vazia ou toda resolvida

## Passo a passo

1. **Ler as fontes da verdade** (nesta ordem):
   - `spec.md` da feature
   - `.claude/skills/backend-module/SKILL.md` e/ou `frontend-module/SKILL.md` (+ `ui-v2` se houver tela)
   - `backend/api/CLAUDE.md` e/ou `frontend/<ws>/CLAUDE.md` — estado do workspace e dívida
   - O módulo de referência mais similar já implementado (ex.: `donors_collections_motilities`)
   - `.claude/lessons/backend.md`, `frontend.md`, `agents.md` — listar as lessons relevantes na seção "Riscos"

2. **Gerar o arquivo** usando `.claude/specs/_templates/plan.md`:
   - Criar `.claude/specs/<estado>/<feature>/plan.md`
   - Preencher TODAS as seções: tabelas, enums, endpoints, Joi, services, migration, frontend
   - **Obrigatório**: tabela "Mapeamento RN → implementação" cobrindo TODAS as RN-xx da spec.
     RN sem mapeamento = plan incompleto.
   - Status inicial: `rascunho`

3. **Se a feature tem tela — despachar o `ui-planner`** (spec 088):
   - Subagente `ui-planner`, com a `spec.md` e o `plan.md` em rascunho como entrada. Ele preenche
     **§ 3.4 Telas** (família v2, componentes, tela canônica de referência) e a tabela
     **"Onde vive o estado"** (FE-020). Ele é o único que escreve essa seção, e não escreve `.tsx`.
   - Acontece **antes** de apresentar o plan ao usuário: a tela aprovada no papel é o que o
     `frontend-builder` recebe, e é contra ela que o `ui-reviewer` revisa depois.
   - `ui-planner` que devolve **CONTESTADO** (ex.: a § 2.3 não declara os campos que a tela lê)
     é para resolver agora, no plan — não para contornar.
   - **Confira o escopo dele ao voltar**: `git status --short -uall` deve mostrar **só** o
     `plan.md` da feature. O `Edit` do `ui-planner` alcança qualquer arquivo — a restrição "só a
     § 3.4" vive no texto do agente, e quem a verifica é este passo. (`-uall`: sem ele o git
     colapsa diretório novo numa linha só.)
   - Feature sem tela: pular este passo e escrever "não se aplica" na § 3.4.

4. **Auto-conferência antes de apresentar**:
   - Toda RN da spec aparece no mapeamento?
   - Todo critério de aceite `[auto]` tem teste/verificação prevista?
   - Nomenclatura segue a "Referência de nomenclatura rápida" do `/new-backend-module`?
   - FKs com onDelete definido?
   - A **§ 2.3 Contrato de API** declara a coluna **Resposta** e a lista de campos que a tela lê?
     Sem isso os leads devolvem CONTESTADO na execução (AG-022).
   - A **§ 3.4 Telas** está preenchida (ou marcada "não se aplica")?

5. **Apresentar ao usuário** com resumo das decisões de design e perguntar:
   **"O plano técnico está correto? Posso marcá-lo como aprovado?"**
   - Só marcar `Status: aprovado` + data após o "sim".

## Regras críticas

- O plan **deriva** da spec — se durante o planejamento surgir uma regra de negócio nova,
  ela vai PRIMEIRO para a spec (com aprovação do usuário), depois para o plan.
- Preferir o que está em `documentacao/` sobre inferências do código.
- Não gerar código nem tasks neste comando.
