# Comando: /spec-tasks

> **Título**: Gerar Tasks de Execução (Camada 3 — SDD)
> **Descrição**: A partir de um `plan.md` aprovado, gera o `tasks.md` (passos atômicos com
> verificação) na mesma pasta da feature. Pode iniciar a execução se o usuário pedir.

## Uso

```
/spec-tasks <nome-da-feature> [--executar]
```

## Pré-condições

1. `plan.md` existe na pasta da feature com `Status: aprovado` — senão, PARAR e indicar `/spec-plan`
2. Se `tasks.md` já existe: perguntar se é para regenerar (perde marcações `[x]`) ou retomar

## Passo a passo

1. **Gerar o arquivo** usando `.claude/specs/_templates/tasks.md`:
   - Quebrar o plan em tasks atômicas (T-01, T-02...) — cada uma concluível e verificável isoladamente
   - **Toda task tem uma linha "Verificação:"** com comando ou critério objetivo
   - Manter as fases: Backend → Frontend → Gate de conclusão
   - As tasks de gate (verify.sh, verifier, validação humana) são SEMPRE as últimas e não podem ser removidas

2. **Se `--executar`** (ou o usuário pedir para começar):
   - Mover a pasta da feature de `a_fazer/` para `em_andamento/` ANTES da primeira task
   - Executar na ordem, marcando `[x]` imediatamente após cada verificação passar
   - Em caso de erro novo: corrigir, anotar no "Registro de execução" e avaliar candidata a lesson

### 2.1 Quem executa o quê (spec 088)

Você — a **sessão principal** — orquestra e não escreve o código dos módulos. A sequência:

| # | Quem | O quê |
|---|------|-------|
| 1 | `backend-lead` | despacha `backend-test-author` → `backend-builder`, roda o gate `--scope --feature` e o `check-module.py backend --diff --contract`, devolve relatório |
| 2 | **sessão principal** | edita os **arquivos de registro** que o lead relatou: `src/shared/infra/http/routes/index.ts`, `src/shared/container/index.ts`, permissões — e roda a migration |
| 3 | `frontend-lead` | despacha `frontend-builder` → `ui-reviewer`, roda o gate e o `check-module.py <operador|cliente> --diff --contract`, devolve relatório |
| 4 | **sessão principal** | edita `src/routes/index.tsx`, `src/App.tsx`, `src/components/Header/menuItens.tsx` conforme o relatório |
| 5 | **sessão principal** | `verifier` — auditoria independente. **Nunca** é filho de um lead: auditor não pode ser despachado por quem ele audita |
| 6 | usuário | `/finish-task` |

**Por que o registro é da sessão principal**: `routes/index.ts`, `container/index.ts`,
`src/App.tsx` e o menu são tocados por **toda** feature. Um só escritor neles evita conflito entre
workspaces e entre agentes — e os leads não têm `Edit`/`Write` de propósito.

- **Paralelismo** só entre módulos que o `plan.md` declara independentes, e nunca duas features ao
  mesmo tempo no mesmo workspace: o `--scope` do gate é o diff do workspace, e dois `jest`
  simultâneos disputam CPU até nenhum ser confiável (AG-021).
- **O `--contract` que vale é o do passo 3.** Rodado só no passo 1, ele compara os tipos do
  frontend **antes** de a tela existir — e é justamente a checagem AG-022 (tipo do frontend ×
  resposta do backend) que dá razão de ser a esta fase. Roda nos dois: no 1 pega o que já está no
  repositório, no 3 pega o que a feature acabou de escrever.
- **Achado do verifier** volta ao builder **de origem**, com o achado como entrada, e a
  reauditoria é obrigatória — a correção nasce sem auditoria (AG-016).
- **Feature de harness** (trabalho em `.claude/`): executada pela própria sessão principal, sem
  leads — não há workspace nem gate que alcance `.md`/`.py`/`.sh`.
- Módulo novo nasce do scaffold, nunca de cópia manual: `/new-backend-module`,
  `/new-frontend-module`, `/new-migration` (é o que os builders usam).

## Regras críticas

- Task sem verificação aprovada **não** é marcada `[x]`.
- Nunca pular as tasks de gate (verify.sh + verifier + validação humana).
- Se o plan mudar no meio da execução: atualizar plan (com aprovação), regenerar as tasks
  pendentes e preservar as já concluídas.
- A conclusão final é SEMPRE via `/finish-task` — nunca mover para `concluido/` diretamente.
