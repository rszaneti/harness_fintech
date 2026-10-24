# Plataforma de Pagamentos (BTG BaaS) — Harness de Desenvolvimento

> Leia este arquivo antes de qualquer ação no monorepo.
> Para contexto profundo de cada workspace, consulte o `CLAUDE.md` dentro dele — que **nasce com o
> workspace**. Hoje nenhum workspace existe: este checkout tem só o harness e a documentação.

---

## Visão Geral

**Produto**: plataforma de pagamentos em cima do **BaaS do BTG** (modelo 2). Plataformas SaaS
abrem, por API, uma conta de pagamento no BTG **em nome do cliente delas**, cobram por Pix, fazem
split e saque — e a plataforma **nunca toca no dinheiro**: o BTG é o custodiante, a plataforma é
software que lê, calcula e ordena (`documentacao/03`). Primeira plataforma cliente: o SaaS de
vendas com IA da Bora Fazer (`documentacao/01`); a demo é a cobrança Pix dentro da conversa do
WhatsApp (`documentacao/02`).

**Arquitetura**: monorepo. A raiz versiona o harness (`.claude/`), este arquivo e `documentacao/`;
cada workspace tem `.git` próprio. **A lista de workspaces mora em `.claude/workspaces.json`** —
gate, hooks e scaffold leem de lá, e o `verify.sh harness` reprova executável do harness que cite
workspace fora dela.

**Um frontend por papel.** `operador` e `cliente` são SPAs separados porque têm **papéis e domínios
diferentes** — quem aprova payout tem MFA e outro domínio; quem só consulta, não (`documentacao/04`
§3). Não é por causa de token: a sessão vai em cookie `HttpOnly` com JWT assimétrico (spec 002),
nunca em `localStorage`.

| Workspace | Pasta | Chave | Público | Tecnologia | Estado |
|---|---|---|---|---|---|
| Backend API | `backend/api/` | `backend` | Plataformas (API máquina-a-máquina) e os dois painéis | Node.js + TypeScript + Express + TypeORM + tsyringe + celebrate/Joi + Jest, DDD | planejado — spec 002 (provisório: questão aberta na própria 002) |
| Frontend Operador | `frontend/operador/` | `operador` | Equipe da plataforma e da V-Corp — aprova payouts, vê conciliação, MFA obrigatório | React 18 + TypeScript + MUI v7 + Formik + axios | planejado — spec 010 |
| Frontend Cliente | `frontend/cliente/` | `cliente` | Cliente final (PME) — saldo, extrato, cobranças, saque | React 18 + TypeScript + MUI v7 + Formik + axios | planejado — spec 011 |
| Simulador BTG | `tools/btg-simulator/` | `simulator` | — (desenvolvimento, teste e demo sem depender do sandbox) | Node.js + TypeScript | planejado — spec 004 |

Porta de cada workspace em dev: definida pela spec que o cria. Workspace ausente vira **aviso** no
resumo do gate, sem reprovar.

---

## Navegação Rápida

```
fintech/
├── backend/api/            → API (planejado — spec 002)
├── frontend/operador/      → painel do operador (planejado — spec 010)
├── frontend/cliente/       → painel do cliente (planejado — spec 011)
├── tools/btg-simulator/    → simulador do BTG (planejado — spec 004)
├── documentacao/           → contexto de NEGÓCIO (00-README é o índice) + HARNESS.md (memória do processo)
└── .claude/
    ├── workspaces.json     → a lista dos workspaces — fonte única
    ├── commands/           → comandos customizados (orquestradores)
    ├── skills/             → conhecimento de construção (backend-module, frontend-module, ui-v2)
    ├── scaffold/           → scaffold.py + templates: gera módulo/migration
    ├── agents/             → subagentes (leads, builders, test-author, ui-*, verifier)
    ├── hooks/              → verificação automática a cada edição (NÃO desativar)
    │   └── financial_rules.py → as regras financeiras, num lugar só
    ├── scripts/verify.sh   → GATE único de conclusão
    ├── verifier-checks/    → o que o verifier julga, por etiqueta do diff
    ├── lessons/            → lições aprendidas + política de promoção
    └── specs/              → features em SDD (spec → plan → tasks)
```

---

## O Harness — como a qualidade é garantida

Este projeto opera com verificação mecânica em camadas. **Instrução não garante qualidade; verificação garante.**

1. **Hooks automáticos** (`.claude/hooks/`): a cada Edit/Write de `.ts/.tsx` de workspace, rodam o
   ESLint do arquivo, as checagens das lessons promovidas e os **quatro hooks financeiros**
   (`money-bigint`, `ledger-immutable`, `idempotency-required`, `no-secret-in-code`). Erro retorna
   imediatamente para correção. `protect-migrations.sh` bloqueia edição de migration versionada;
   `block-shell-write-ts.py` bloqueia gravação de `.ts/.tsx` por shell (onde nenhum hook roda).
2. **Gate de conclusão** (`.claude/scripts/verify.sh`): lint + typecheck + testes do workspace, com
   evidência em `.claude/gate/`. **Nenhuma task/feature é concluída sem este gate aprovado.** Uso:
   `bash .claude/scripts/verify.sh backend src/modules/<contexto>/<modulo> --feature <feature>`,
   `bash .claude/scripts/verify.sh <operador|cliente> --feature <feature>` e — para feature que muda
   `.claude/`, este arquivo ou `documentacao/` — `bash .claude/scripts/verify.sh harness --feature <feature>`
   (`bash -n`, compilação dos `.py` e todos os `--self-test` do harness). `--scope` por padrão;
   `--full` no fechamento de sprint.
3. **Auditoria independente** (subagente `verifier`): quem implementa não se auto-aprova.
   Rodar o verifier após implementar e sempre antes de `/finish-task`.
4. **Gate humano** (`/finish-task`): só o usuário move uma feature para `concluido`.

### Hierarquia de Fontes (vale para gerar E para auditar)

Quando duas fontes divergem, vence a de **menor número**. Divergência encontrada não é ignorada:
segue-se a fonte de menor número e **reporta-se ao usuário**.

| # | Fonte | Papel |
|---|-------|-------|
| 1 | `.claude/hooks/` (inclui `financial_rules.py`) + `.claude/scripts/verify.sh` | Verificação mecânica — é o que efetivamente bloqueia. Nenhuma outra fonte autoriza o que ela reprova. |
| 2 | `.claude/lessons/backend.md`, `frontend.md`, `agents.md` | Correções registradas depois de erro real |
| 3 | **`.claude/skills/{backend,frontend}-module/`** (SKILL.md) + **`.claude/scaffold/`** (script + templates) | **Forma de arquivo** — o contrato que o scaffold gera e o `verifier` audita |
| 4 | `CLAUDE.md` de cada workspace | **Estado do workspace**: stack, contextos, dívida técnica conhecida. **Nasce com o workspace** — até lá, este nível está vazio |
| 5 | `spec.md` / `plan.md` da feature | Contrato específico da entrega (RN, CA) — soma-se, não substitui |

> No frontend, o **padrão visual** tem cadeia própria dentro do nível 3:
> `código (*_v2 + theme.ts) > skill ui-v2 > frontend/<ws>/CLAUDE.md`. O que compila é o que vale.
> ⚠️ O padrão v2 foi **herdado do ERP de origem** e é revisto nas specs 010/011.

**Por que a skill não fica no topo**: ela é escrita ANTES de os erros serem descobertos; lessons e
hooks são a correção aplicada DEPOIS. Skill no topo aprovaria código que o hook reprova.

**Por que `documentacao/` não está na tabela**: ela é contexto de **negócio**, não padrão de
código. A origem do harness e o histórico das mudanças nele estão em `documentacao/HARNESS.md`.

---

## Regras Críticas do Monorepo

1. **Cada workspace tem `.git` próprio** — commits são feitos separadamente em cada workspace; a raiz versiona só o harness e a documentação.
2. **Nunca misturar código** entre workspaces.
3. **Idioma do código**: inglês. **Idioma da UI e mensagens de erro**: português brasileiro.
4. **Gerenciador de pacotes**: `yarn` em todos os workspaces. Nunca usar `npm`.
5. **Módulo novo se gera, não se escreve**: `python3 .claude/scaffold/scaffold.py backend …` (com
   `--append-only` para registro imutável) ou `… frontend … --ws <operador|cliente>`, e preencher os
   marcadores de bloco. `documentacao/` é contexto de **negócio**, não padrão de código.
6. **Toda feature nova nasce como spec SDD** em `.claude/specs/a_fazer/<feature>/` via `/spec-new` (ver seção Fluxo SDD).
7. **Nunca desativar/contornar hooks ou gates.** Se um gate falhar por problema pré-existente não relacionado à task, reportar ao usuário e pedir orientação (escape: `SKIP_TSC=1`, só com autorização explícita).
8. **Nenhuma coluna monetária fora de `BIGINT` em centavos** (nome `*_cents`). Nunca `numeric`,
   `decimal`, `float` nem `money`; proporção é inteiro numa unidade declarada pela spec. Hook `money-bigint`.
9. **Ledger é append-only**: lançamento nunca é alterado nem apagado; estorno é lançamento **novo**
   com referência ao original; saldo é **derivado**, nunca coluna. Perfil `--append-only` do
   scaffold, trigger `reject_mutation()` no banco, hook `ledger-immutable`.
10. **`Idempotency-Key` em toda escrita**: toda rota `POST`/`PUT`/`PATCH` passa por
    `ensureIdempotency`; isenção só com `// idempotency-exempt: <motivo>`, que o `verifier` julga.
    Hook `idempotency-required`.
11. **Nenhum segredo no código**: chave, token e certificado vêm do cofre/env; em teste, o valor é
    montado em tempo de execução. Hook `no-secret-in-code`.
12. **A plataforma nunca guarda saldo de terceiros** (modelo 2): nada de "conta transitória",
    "carteira", "saldo interno" ou "repasse". Spec que propuser isso é devolvida com referência a
    `documentacao/03` §4 (RN-REG-01 a 06).

---

## Contextos e Módulos do Backend (planejados)

> Nenhum módulo existe ainda. A tabela é de `documentacao/04` §4; o **Estado** diz qual spec cria
> cada um (sequência em `documentacao/05` §5). Módulo que entra no código troca o estado para `existe`.

| Contexto | Módulos | Perfil de scaffold | Estado |
|---|---|---|---|
| `users` | users, profiles, permissions, users_groups | padrão | planejado — spec 002 |
| `platforms` | api_keys | padrão + `CryptoProvider` | planejado — spec 002 |
| `platforms` | platforms, webhook_endpoints | padrão | planejado — spec 005 |
| `ledger` | ledger_entries, ledger_accounts, reconciliations | **`--append-only`** | planejado — spec 003 |
| `audit` | audit_log | **`--append-only`** | planejado — spec 003 (questão aberta na 003: a sequência do `05` não o atribui) |
| `btg` | btg_adapter (interface + real + simulador) · btg_events (webhooks recebidos) | `--no-table` · **`--append-only`** | planejado — spec 004 |
| `accounts` | accounts, onboarding_documents | padrão + `CryptoProvider` | planejado — spec 006 |
| `charges` | charges (cobranças Pix) | padrão, com o Delete removido depois de gerar¹ | planejado — spec 007 |
| `splits` | split_rules · split_executions | padrão · **`--append-only`** | planejado — spec 008 |
| `payouts` | payouts, payout_approvals | padrão, com o Delete removido depois de gerar¹ | planejado — spec 009 |

Os módulos que exigem `--append-only` estão em `financial_rules.APPEND_ONLY_MODULES`; o scaffold
recusa gerá-los sem a flag.

¹ `documentacao/04` §4 fala em perfil "padrão sem Delete", mas o scaffold **não tem** esse perfil: o
módulo nasce no padrão e a spec da feature remove service, teste e rota de Delete (com o check
`removal` do verifier). Se o caso se repetir, vira perfil — decisão da spec 007.

---

## Providers Compartilhados (Backend — NÃO recriar quando existirem)

| Token DI | Finalidade | Estado |
|---|---|---|
| `CryptoProvider` | Criptografia AES-256-GCM de campo sensível (CNPJ/CPF de sócios, documentos, chaves de API) | planejado — nasce com o `backend/api` (spec 002) |
| `MailProvider` | Envio de e-mail (template) | planejado — nasce com o `backend/api` (spec 002) |
| `StorageProvider` | Upload de arquivos (documentos de onboarding) | planejado — nasce com o `backend/api` (spec 002) |

O adaptador do BTG **não** é provider compartilhado: é o módulo `btg/btg_adapter` (spec 004), a
única peça que fala com o banco — e por isso troca entre real e simulador sem mudar o resto.

---

## Lições Aprendidas (Erros Conhecidos)

> Antes de gerar código, consulte `.claude/lessons/` para evitar erros já cometidos. As lessons
> foram **herdadas inteiras do ERP Vida Fértil** — os caminhos citados nelas são os de lá; a
> correspondência está em `.claude/lessons/README.md`, seção "Origem".

| Arquivo | Conteúdo |
|---------|----------|
| `.claude/lessons/backend.md` | Erros em services, entities, migrations, routes |
| `.claude/lessons/frontend.md` | Erros em contexts, hooks, components, types |
| `.claude/lessons/agents.md` | Erros específicos de agentes gerando múltiplos arquivos |

**Política de promoção** (ver `.claude/lessons/README.md`): lesson automatizável vira regra no
hook pós-edição, no ESLint ou na auditoria do `verifier` — o texto fica só para o que exige
julgamento. Ao registrar uma lesson nova, SEMPRE avaliar se ela é promovível.

---

## Comandos Customizados Disponíveis

| Comando                      | O que faz                                                    |
|------------------------------|--------------------------------------------------------------|
| `/spec-new`                  | Cria a spec (camada 1 SDD) de uma feature — só o "o quê"     |
| `/spec-plan`                 | Gera o plano técnico (camada 2) a partir da spec aprovada    |
| `/spec-tasks`                | Gera as tasks de execução (camada 3) a partir do plan aprovado |
| `/new-backend-module`        | Scaffold DDD backend: `scaffold.py backend` (+ `--append-only`) + skill `backend-module` |
| `/new-frontend-module`       | Scaffold frontend v2: `scaffold.py frontend --ws …` + skill `frontend-module` |
| `/new-migration`             | Migration pelo `scaffold.py migration create\|alter`         |
| `/check-module`              | Audita um módulo contra os padrões (usado pelo verifier)     |
| `/finish-task`               | Conclui feature: confere gates, pede confirmação do usuário e move para `concluido` (`--lote` percorre vários, com confirmação por feature) |
| `/sprint-close`              | Fecha a sprint: gate `--full` nos workspaces e no harness, contrato cruzado desde o merge do ciclo anterior, e a medição do que falta em cada feature. **Não move nada** |

---

## Fluxo SDD — Tarefas para executar

> Antes de gerar código, consulte `.claude/specs/a_fazer/` para verificar se há features para executar.
> Documentação completa do fluxo: `.claude/specs/README.md`.

Cada feature é uma **pasta** com 3 camadas: `spec.md` (o quê — contrato com o usuário),
`plan.md` (como — design técnico) e `tasks.md` (passos com verificação). Pipeline:

```
/spec-new → [usuário aprova spec] → /spec-plan → [usuário aprova plan] → /spec-tasks
→ execução (hooks verificam cada edição) → verify.sh ✅ → verifier ✅ → /finish-task [usuário confirma]
```

⚠️ **REGRA OBRIGATÓRIA — vale para QUALQUER forma de execução** (comando customizado, prompt direto, a partir da raiz ou de dentro dos workspaces):

- **Antes do primeiro passo de execução**: mover a pasta da feature de `.claude/specs/a_fazer/` para `.claude/specs/em_andamento/` (evita reexecução por outra sessão).
- **Ao concluir** (todos os gates aprovados + confirmação do usuário via `/finish-task`): mover para `.claude/specs/concluido/`.
- Incompleta/pausada: permanece em `em_andamento/` — não devolver para `a_fazer/`.
- Caminhos de `.claude/specs/` sempre relativos à raiz do monorepo (`../../.claude/specs/...` a partir de cada workspace).
- **Marcar cada task `[x]` no `tasks.md` IMEDIATAMENTE ao concluí-la** — nunca em lote no final. Ao retomar trabalho pausado, ler o `tasks.md` primeiro e não refazer o que está `[x]`.

---

## Como Trabalhar com a IA

- **Tarefa de backend**: abra o Claude Code dentro de `backend/api/` (quando existir) ou mencione que está no contexto backend.
- **Tarefa de frontend**: abra dentro de `frontend/operador/` ou `frontend/cliente/`, ou mencione qual.
- **Tasks que cruzam workspaces, ou que mexem no harness**: trabalhe neste nível de raiz. Trabalho em
  `.claude/` é executado pela sessão principal, sem leads.
- **Documentação de contexto** (`documentacao/`, índice em `00-README.md`): `01` o primeiro cliente
  (Bora Fazer); `02` o roteiro do MVP — documento mestre; `03` custódia e regulatório (as RN-REG que
  toda spec respeita); `04` stack, segurança e invariantes do ledger; `05` a adaptação do harness e a
  sequência de specs; `06` glossário. As **decisões já tomadas** estão no `00-README.md` e não se
  reabrem em spec.
- **Padrões de código**: as skills. `backend-module` e `frontend-module` para contrato, dados e
  decisões (inclusive as **Regras financeiras** da `backend-module`); **`ui-v2`** para o padrão
  visual do frontend. O que o gerador produz está em `.claude/scaffold/`. Estado de cada workspace
  fica no `CLAUDE.md` dele. Ver "Hierarquia de Fontes" na seção O Harness — vale para gerar e para
  auditar.
