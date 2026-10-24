# Comando: /new-backend-module

Cria o scaffold completo de um módulo DDD no backend usando a skill **`backend-module`**.

## Uso

```
/new-backend-module <contexto> <modulo> <Entity>
```

**Exemplos:**
- `/new-backend-module contracts annexes ContractAnnex`
- `/new-backend-module donors collections_vitalities DonorCollectionVitality`

## Execução

1. **Ler** `.claude/skills/backend-module/SKILL.md` por completo.
2. **Coletar os pré-requisitos** listados na skill (campos, FKs, workflow, upload, permissões,
   regras de negócio). Se a feature tem `plan.md` (SDD), usar o plan — não perguntar de novo.
3. **Rodar o scaffold** — ele copia os templates de `.claude/scaffold/templates/backend/`, deriva
   os placeholders de identidade, formata e lista os blocos que ficaram para preencher:
   ```bash
   python3 .claude/scaffold/scaffold.py backend <contexto> <modulo> <Entity> [--enum <Tipo>] [--timestamp <ms>]
   ```
   Depois, **preencher os marcadores de bloco** (`__CAMPOS__`, `__FILTROS__`, `__WHERES__`, `__FKS__`,
   `__REGRAS__`, `__ATRIBUICOES__`, `__TESTES_DE_ERRO__`…) com Edit/Write, seguindo o plan. **Nunca
   gerar de cabeça, nunca copiar de outro módulo.** (Módulo sem tabela: `--no-table`.)
4. **RODAR a migration** gerada (`yarn migration:run` até aplicar com sucesso; confirmar com
   `yarn migration:show` — o timestamp tem de ficar acima da última aplicada).
5. **Verificação final** da skill: `find` (AG-009), `yarn test src/modules/<contexto>/<modulo>`,
   gate `bash .claude/scripts/verify.sh backend src/modules/<contexto>/<modulo> --feature <feature>`.
6. **Informar o checklist manual** (registro de rota, provider, permissões, lint).

## Regras

- Os hooks pós-edição vão validar cada arquivo salvo — corrigir imediatamente qualquer erro retornado.
- Consultar `.claude/lessons/backend.md` e `agents.md` antes de iniciar (lessons não-automatizadas).
- Fonte dos padrões, em **ordem de precedência** (vence a de menor número):
  1. hooks (`.claude/hooks/`) e `.claude/scripts/verify.sh` — verificação mecânica
  2. `.claude/lessons/backend.md`, `agents.md`
  3. **a skill** (`.claude/skills/backend-module/`) — o contrato de forma de arquivo
  4. `backend/api/CLAUDE.md` — estado do workspace (stack, contratos, dívida), **não** forma de
     arquivo. O que o gerador produz está em `.claude/scaffold/`

  Divergência entre fontes: seguir a de menor número e **reportar ao usuário**. É a mesma
  hierarquia que o subagente `verifier` aplica na auditoria — gerador e auditor não podem
  discordar sobre qual fonte vence.
