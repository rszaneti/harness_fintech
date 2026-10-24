# Comando: /new-frontend-module

Cria o scaffold completo de um módulo frontend usando a skill **`frontend-module`**.

## Uso

```
/new-frontend-module <contexto> <Modulo> <endpoint-api>
```

**Exemplos:**
- `/new-frontend-module laboratories Laboratory laboratory` → módulo pai simples (tipo A)
- `/new-frontend-module contracts ContractAnnex contract_annexes` → com tab filha (tipo B/C)

## Execução

1. **Ler** `.claude/skills/frontend-module/SKILL.md` por completo.
2. **Coletar os pré-requisitos** da skill (identidade, campos, tipo de módulo A/B/C/D, tabs filhas,
   constants, ordenação). Se a feature tem `plan.md` (SDD), usar o plan — não perguntar de novo.
3. **Rodar o scaffold** — ele copia os templates v2 de `.claude/scaffold/templates/frontend/`
   (modelados nas telas canônicas de Clínicas), deriva os placeholders, formata e lista os blocos
   que ficaram para preencher:
   ```bash
   python3 .claude/scaffold/scaffold.py frontend <contexto> <modulo> <Modulo> --ws <operador|cliente> --label "<Rótulo>" \
       [--endpoint <endpoint-api>] [--filho <Filho> --filho-label "<Rótulo>"] [--constants]
   ```
   Depois, **preencher os marcadores de bloco** (`__CAMPOS__`, `__FILTROS__`, `__COLUNAS__`,
   `__CAMPOS_FILHO__`, `__VALORES__`) com Edit/Write, seguindo o § Telas e o § Contrato de API do
   plan. **Nunca copiar de outro módulo existente** (AG-002/FE-001..7) e nunca gerar de cabeça.
   Layout é sempre o **v2** (`styles/global_v2`, `styles/globalMaterialUi_v2`, tema de `src/theme.ts`).
4. **Verificação final** da skill: `grep` de vazamento do módulo de referência, checklist de
   qualidade, gate `bash .claude/scripts/verify.sh frontend --feature <feature>`.
5. **Informar os avisos manuais** (rotas, menu, provider no App.tsx, lint).

## Regras

- Os hooks pós-edição vão validar cada arquivo salvo (incluindo FE-008/FE-009 do MUI v7) —
  corrigir imediatamente qualquer erro retornado.
- Consultar `.claude/lessons/frontend.md` e `agents.md` antes de iniciar.
- Fonte dos padrões, em **ordem de precedência** (vence a de menor número):
  1. hooks (`.claude/hooks/`) e `.claude/scripts/verify.sh` — verificação mecânica
  2. `.claude/lessons/frontend.md`, `agents.md`
  3. **a skill** (`.claude/skills/frontend-module/`) — o contrato de forma de arquivo
  4. `frontend/<ws>/CLAUDE.md` — estado do workspace (stack, migração visual, dívida), **não**
     forma de arquivo. O padrão visual tem cadeia própria: código (`*_v2` + `theme.ts`) > skill
     `ui-v2` > `frontend/<ws>/CLAUDE.md`

  Divergência entre fontes: seguir a de menor número e **reportar ao usuário**. É a mesma
  hierarquia que o subagente `verifier` aplica na auditoria — gerador e auditor não podem
  discordar sobre qual fonte vence.
