# Análise do harness Vida Fértil e plano de adaptação para pagamentos

> Análise feita em 23/10/2026 sobre `rszaneti/harness_vidafertil` (commit `0c878b7`, "V1.0",
> 624 arquivos: 419 em `.claude/`, 202 em `documentacao/`). O repositório contém o **harness**
> (processo, skills, scaffold, hooks, specs, lessons), não o código do ERP — os workspaces têm
> `.git` próprio. É exatamente a camada que o projeto de pagamentos reaproveita.

---

## 1. O que o harness é

Um sistema de produção de software por agentes com **verificação mecânica em camadas**, versão
v2.3 (seis fases de evolução executadas, specs 084–090), pilotado no projeto V-Corp. Princípio
central, que vale integralmente aqui: *instrução não garante qualidade; verificação garante.*

| Camada | O que tem | Veredito |
|---|---|---|
| **Processo SDD** — `spec → plan → tasks`, gate humano em cada camada, pastas `a_fazer / em_andamento / concluido / canceladas` | 108 specs, templates das 3 camadas, `/spec-new`, `/spec-plan`, `/spec-tasks`, `/finish-task`, `/sprint-close` | **Manter intacto** |
| **Verificação** — `verify.sh` com evidência em `.claude/gate/`, 6 hooks, `check-module.py`, `verifier` independente | Gate incremental por escopo, hash do diff, `rc` acumulado (pior rodada vence), bloqueio de edição de migration versionada, bloqueio de escrita `.ts` via shell | **Manter e estender** com hooks financeiros |
| **Agentes** — lead sem Edit/Write por workspace; `test-author` **antes** do `builder`; `verifier` nunca é filho de quem audita | 8 agentes: `backend-lead`, `backend-test-author`, `backend-builder`, `frontend-lead`, `frontend-builder`, `ui-planner`, `ui-reviewer`, `verifier` | **Manter** — testes antes do código é o que o ledger precisa |
| **Scaffold** — `scaffold.py` + 24 templates backend + 12 frontend | Gera módulo DDD completo: migration, entity, DTOs, repository, 6 services, controller de 5 métodos, routes, 6 testes; placeholders fechados (exit 2 se houver não documentado); `--self-test` | **Manter; criar perfil `--append-only`** |
| **Lessons** — 79 lições (31 BE + 26 FE + 22 AG), 12 promovidas a hook | Erros reais de TypeORM, Express, Jest, celebrate, agentes | **Manter 100%** — são da stack, não do domínio |
| **Skills** — `backend-module`, `frontend-module`, `ui-v2` | Contrato de forma de arquivo; decisões que o scaffold não toma | **Manter; acrescentar seção "Regras financeiras"** |
| **Documentação de negócio** — `documentacao/` (42 MB) | Processo doador, tentante, paciente, CRM, exemplos de frontend | **Substituir** por esta pasta |

## 2. Três conflitos com pagamentos que viram spec antes de qualquer módulo

1. **JWT HS256 com secret por público e token em `localStorage`.** A arquitetura "um SPA por
   público" existe por causa disso (`CLAUDE.md`, seção Visão Geral). Para pagamentos: RS256/ES256
   com JWKS, access token curto, refresh em cookie `HttpOnly`. Muda `ensureAuthenticated`, o
   interceptor do axios, e remove o motivo técnico de separar SPAs por token.
2. **Entity padrão tem Update e Delete.** O scaffold gera 6 services e controller de 5 métodos
   para tudo. Lançamento de ledger, evento do BTG e linha de auditoria não se atualizam nem se
   apagam. Precisa de perfil `--append-only`: só `Create/Show/List/ListTotal`, controller de 3
   métodos, migration com trigger que rejeita `UPDATE`/`DELETE`.
3. **Dinheiro mapeado como `numeric(p,s)`** na skill `backend-module`. Para o ledger a regra é
   `BIGINT` em centavos, com hook que bloqueia `numeric`/`float`/`number` decimal em módulos
   financeiros — mesmo mecanismo do `protect-migrations.sh`.

## 3. Pontos de atenção que o próprio harness documenta (`documentacao/HARNESS.md`)

- **56 specs em `em_andamento` × 51 concluídas × 1 a fazer.** Diagnóstico do próprio documento:
  "feature que não fecha", travando em critérios `[humano]` e cadastro manual de permissões. No
  clone: zerar specs, numeração a partir de `001`, e usar `/sprint-close` como ritual desde a
  primeira sprint.
- **Gate lento e sensível a concorrência** (lint do backend 74 s; 314 s com sessão paralela). Em
  projeto novo isso some, mas a regra "um lead por workspace, nunca dois gates em paralelo" fica.
- **Dois níveis de `.git`**: raiz (harness) e cada workspace. Manter — versiona o harness separado
  do produto, que é o que faltava no ERP até setembro/2026.
- **Hooks dependem de `$CLAUDE_PROJECT_DIR`** apontando para a raiz do monorepo. Abrir o Claude
  Code dentro de um workspace exige que o `CLAUDE.md` do workspace aponte para `../../.claude/`.

## 4. Spec 001 — `harness-pagamentos-adaptacao`

Primeira spec do clone, no formato SDD do harness (`.claude/specs/_templates/spec.md`), criada via
`/spec-new`. Entregas:

| # | Entrega | Verificação |
|---|---|---|
| 1 | `CLAUDE.md` raiz reescrito: produto, workspaces (`backend/api`, `frontend/operador`, `frontend/cliente`, `tools/btg-simulator`), módulos (ver `04-stack-e-seguranca` §4), providers compartilhados, regras críticas (acrescentar: "nenhuma coluna monetária fora de `BIGINT`", "ledger é append-only", "`Idempotency-Key` em toda escrita") | Leitura; `verifier` confere que módulos citados existem ou têm spec |
| 2 | `documentacao/` substituída por esta pasta; `HARNESS.md` reiniciado com histórico a partir da v1.0 do clone | `ls documentacao/` |
| 3 | `scaffold.py --append-only`: gera entity sem `user_updated`/`updated_at`, repository sem `update`/`delete`, services `Create/Show/List/ListTotal`, controller de 3 métodos, routes `GET /`, `GET /show/:id`, `POST /`, migration com trigger `reject_mutation()`, 4 testes | `--self-test` do perfil novo compila, passa lint e testes |
| 4 | Hooks novos em `.claude/hooks/`: `money-bigint.py` (bloqueia `numeric`/`float`/`decimal` em migration/entity de contexto financeiro), `ledger-immutable.sh` (bloqueia `update`/`delete`/`save(` em `modules/ledger`, `modules/audit`, `btg_events`), `idempotency-required.py` (toda rota `post`/`put` em `routes/*.ts` precisa de `ensureIdempotency`), `no-secret-in-code.py` (regex de chave/secret/token literal em `src/`) | Cada hook com caso que reprova e caso que passa em `.claude/scripts/tests/` |
| 5 | Seção "Regras financeiras" na skill `backend-module` (BIGINT, append-only, transação no repositório, idempotência, HMAC) e checagem correspondente em `check-module.py` | `check-module.py` reprova módulo de exemplo que viola |
| 6 | Specs `002-auth-jwks-httponly` e `003-ledger-core` abertas em `a_fazer/`; a 003 traz as 8 invariantes de `04-stack-e-seguranca` §5 como critérios `[auto]` | Pastas existem com `spec.md` em `rascunho` |
| 7 | `.claude/specs/{a_fazer,em_andamento,concluido,canceladas}/*` e `.claude/gate/*` zerados; `lessons/` mantido inteiro; `settings.json` mantido (adicionar `Bash(redis-cli:*)` ao allow se o simulador precisar) | `git status` limpo após commit inicial |
| 8 | `.claude/lessons/README.md`: nota de origem ("lessons herdadas do ERP Vida Fértil em 23/10/2026; códigos BE/FE/AG mantidos") | Leitura |

**Fora do escopo da 001**: qualquer código de produto. A 001 só prepara o harness.

## 5. Sequência de specs do MVP (proposta)

| Spec | Entrega | Fase do roteiro |
|---|---|---|
| `001-harness-pagamentos-adaptacao` | Harness pronto | Fase 0 |
| `002-auth-jwks-httponly` | Autenticação, chaves de API, HMAC, refresh | Fase 0–1 |
| `003-ledger-core` | Ledger de partidas dobradas, invariantes, conciliação | Fase 1 |
| `004-btg-adapter-e-simulador` | Interface do adaptador, simulador, eventos recebidos | Fase 1 |
| `005-platforms-e-webhooks` | Cadastro de plataformas, endpoints de webhook, emissão assinada | Fase 1 |
| `006-accounts-onboarding` | Abertura de conta via API (BaaS), documentos, status | Fase 1–2 |
| `007-charges-pix` | Cobrança Pix QR dinâmico, webhook de pagamento, `charge.paid` | Fase 1–2 |
| `008-splits` | Regras e execução de split por transferência entre contas | Fase 2 |
| `009-payouts` | Saque com limites, dupla aprovação, bloqueio por disputa | Fase 2 |
| `010-painel-operador` | Frontend operador com MFA | Fase 2 |
| `011-painel-cliente` | Frontend cliente | Fase 2 |
| `012-plugin-bora-fazer` | Botão "cobrar" na conversa, movimento no pipeline | Fase 3 |
| `013-demo-v-corp` | Roteiro, dados de demo, ensaio | Fase 3 |

## 6. Como continuar no VS Code

1. Criar o repositório novo (sugestão: `harness_pagamentos`) a partir do `harness_vidafertil`:
   fork, ou `git clone` + `git remote set-url`. Manter a raiz como repositório do harness; cada
   workspace nasce com `.git` próprio quando for criado.
2. Copiar esta pasta `documentacao/` por cima da existente (a do ERP sai).
3. Abrir a raiz no VS Code com o Claude Code e dar o primeiro comando:

   ```
   /spec-new 001-harness-pagamentos-adaptacao
   ```

   com o contexto: "Leia `documentacao/05-analise-harness-e-plano-de-adaptacao.md` §4 e
   `documentacao/04-stack-e-seguranca-backend.md`. A spec é a adaptação do harness descrita na §4;
   fora do escopo: código de produto."
4. Aprovar a spec → `/spec-plan` → aprovar → `/spec-tasks` → executar → `verify.sh` → `verifier`
   → `/finish-task`. O próprio processo do harness.
