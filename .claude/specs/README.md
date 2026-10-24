# Specs — Spec-Driven Development (SDD)

> Fluxo de desenvolvimento orientado por especificação, com gates de verificação.

## Modelo em 3 camadas

Cada feature é uma **pasta** com 3 arquivos, cada um derivado do anterior:

```
.claude/specs/<estado>/<NNN>-<feature>/
├── spec.md    # O QUÊ + POR QUÊ — regras de negócio, critérios de aceite (contrato estável)
├── plan.md    # COMO — design técnico derivado da spec + documentacao/
└── tasks.md   # PASSOS — execução derivada do plan (descartável/regenerável)
```

**Nomenclatura:** cada pasta de spec recebe um prefixo numérico sequencial de 3 dígitos
(`001-`, `002-`, ...) na ordem de criação, considerando as pastas de TODOS os estados
(`a_fazer/`, `em_andamento/`, `concluido/`) para nunca repetir número. O prefixo acompanha
a pasta ao mover entre estados. Ex.: `001-refactor-donors-workflow-kanban-layout`.

**Por que separado:** a spec é o contrato com o usuário e muda raramente. O plan é derivado
dela e dos padrões de arquitetura. As tasks são derivadas do plan e podem ser regeneradas a
qualquer momento. Misturar os três (como nas TASK_*.md antigas) impede revisar o "o quê"
sem se afogar no "como".

## Ciclo de vida (pastas)

```
a_fazer/ → em_andamento/ → concluido/
```

- Mover a **pasta inteira** da feature entre os estados (`git mv` quando aplicável).
- **Antes do primeiro passo de execução**: mover de `a_fazer/` para `em_andamento/` (evita
  que outra sessão pegue a mesma feature).
- Pausada/incompleta: permanece em `em_andamento/` — nunca volta para `a_fazer/`.
- Caminhos sempre relativos à raiz do monorepo, mesmo em sessões abertas dentro de
  um workspace (`backend/api/`, `frontend/operador/`…).

## Pipeline com gates

| Etapa | Comando | Gate para avançar |
|-------|---------|-------------------|
| 1. Especificar | `/spec-new` | Usuário aprova a spec (status `aprovada`) |
| 2. Planejar | `/spec-plan` | Usuário aprova o plan (status `aprovado`) |
| 3. Detalhar | `/spec-tasks` | tasks.md gerado com verificação por task |
| 4. Executar | (sessão ou comandos de scaffold) | Hooks pós-edição passando em cada arquivo |
| 5. Verificar | `bash .claude/scripts/verify.sh <ws> [modulo] --feature <feature>` | Lint + typecheck + testes ✅ — gera a evidência em `.claude/gate/` que as etapas 6 e 7 conferem |
| 6. Auditar | subagente `verifier` | Auditoria independente aprovada |
| 7. Concluir | `/finish-task` | Confirmação explícita do usuário |

**Regra de ouro:** nenhuma etapa avança sem o gate da anterior. Nenhuma task é marcada
`[x]` sem sua verificação passando.

## Templates

- `_templates/spec.md` — usado por `/spec-new`
- `_templates/plan.md` — usado por `/spec-plan`
- `_templates/tasks.md` — usado por `/spec-tasks`

## Compatibilidade com tasks antigas (formato TASK_*.md)

As tasks em arquivo único que já estão em `em_andamento/` seguem o fluxo antigo até serem
concluídas. Toda feature **nova** usa o formato de pasta em 3 camadas.
