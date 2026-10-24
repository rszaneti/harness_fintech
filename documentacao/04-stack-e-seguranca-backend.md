# Stack e segurança — decisões para a plataforma de pagamentos

> **Decisão registrada em 23/10/2026**: a stack é a do harness — **Node.js + TypeScript + Express +
> TypeORM + tsyringe + celebrate/Joi + Jest** no backend; **React 18 + TypeScript + MUI v7 + Formik +
> axios** no frontend. Não se troca de framework. O que muda é **como** cada peça é usada, e isso
> está na tabela abaixo. Cada linha marcada **[spec]** vira regra de spec; cada linha marcada
> **[hook]** vira verificação mecânica (ver `05-analise-harness`).

---

## 1. Por que manter a stack do harness

A segurança de um sistema de pagamentos não vem da linguagem; vem de meia dúzia de decisões de
desenho. O harness Vida Fértil carrega 79 lessons, 36 templates, 6 hooks e um `verifier` que
codificam anos de erro corrigido **nesta** stack. Trocar para NestJS, Go ou Java jogaria isso fora
e começaria o MVP com um harness que não sabe nada. O gargalo dos próximos 12 meses é homologação
com o BTG, corretude do ledger e velocidade de entrega — e nisso a stack dominada ganha de
qualquer outra.

O que o harness já tem e serve direto:

- `CryptoProvider` (AES-256-GCM) para campos sensíveis — BE-010 exige no Create **e** no Update.
- Transação no **repositório** com `manager` opcional (BE-017/018) — é exatamente como o ledger
  deve escrever.
- `celebrate`/Joi inline em toda rota; `ensureAuthenticated` + `accessControl` por permissão.
- Rota pública/webhook registrada **antes** do `ensureAuthenticated` (BE-003).
- `protect-migrations.sh` bloqueando edição de migration versionada; guarda de existência por
  operação em `ALTER` (BE-022).

Não precisamos de PCI DSS: a plataforma não toca cartão — o BTG Pay toca.

## 2. Backend — o que endurecer

| Camada | Como o harness faz hoje | Para pagamentos | Por quê | Promoção |
|---|---|---|---|---|
| Autenticação | JWT **HS256** com um secret por público (`jwt`, `jwtTentant`, `jwtProfessional` em `config/auth.ts`) | **RS256/ES256 com JWKS**; access token de 5–15 min; refresh com rotação e revogação (tabela `refresh_tokens`) | Secret compartilhado é o erro clássico; com JWKS, plataformas clientes validam o token sem conhecer a chave privada | **[spec 002]** |
| API máquina-a-máquina (plataformas) | — | **Chave de API + assinatura HMAC-SHA256** do corpo + timestamp (janela de 5 min), padrão Stripe; mTLS quando o BTG exigir | Autentica a chamada, não só o chamador; replay fica inviável | **[spec 002]** |
| Webhooks que emitimos | — | Assinados com HMAC; `event_id` único; retry exponencial; receptor deduplica | O mesmo padrão que exigimos do BTG | **[spec]** |
| Webhooks que recebemos (BTG) | — | Validar assinatura **antes** de qualquer parse; responder 200 em < 200 ms; processar em fila | Webhook não validado é entrada arbitrária no ledger | **[spec]** + **[hook]** |
| Validação de entrada | Joi inline (celebrate) | Joi inline, **sem `unknown(true)`**, em body, query e params de **toda** rota, inclusive webhooks | Um campo a mais numa chamada de payout é incidente | **[hook]** |
| Dinheiro | skill mapeia decimal → `numeric(p,s)` | **`BIGINT` em centavos** em toda coluna monetária; nunca `numeric`, `float`, `number` com decimais | `float`/`numeric` + arredondamento é a fonte nº 1 de "sumiu dinheiro" | **[hook]** |
| Ledger | entity padrão com Create/Update/Delete | **Partidas dobradas**, lançamentos **imutáveis** (append-only), saldo **derivado**; trigger no Postgres rejeitando `UPDATE`/`DELETE`; `SELECT … FOR UPDATE` na conta ao lançar | Auditoria e conciliação exigem histórico; saldo "editado" é o erro clássico | **[scaffold `--append-only`]** + **[hook]** |
| Idempotência | — | Header `Idempotency-Key` obrigatório em todo `POST`/`PUT` de escrita; resposta guardada por 24 h; middleware compartilhado | Retry de rede não pode cobrar nem pagar duas vezes | **[hook]**: rota de escrita sem o middleware reprova |
| Filas | — | **BullMQ + Redis**: webhooks, splits, payouts, conciliação como jobs idempotentes com retry e dead-letter | O banco não espera; a resposta ao webhook tem que ser imediata | **[spec]** |
| Segredos | `.env` | **Cofre** (AWS Secrets Manager / Vault) com rotação; `.env` só em dev; nenhum segredo em código ou log | Primeiro item do checklist de homologação do BTG | **[hook]**: regex de chave/secret em `src/` reprova |
| Criptografia em repouso | `CryptoProvider` para senha/api_key | Disco criptografado **+** campos sensíveis (CPF/CNPJ de sócios, documentos) com `CryptoProvider`; chave em KMS | LGPD; dump vazado não expõe dados pessoais | **[spec]** |
| Auditoria | `user_created`/`user_updated` | Tabela `audit_log` imutável (quem, o quê, quando, de onde, antes/depois) **+** log estruturado (Pino) com `correlation_id` por transação | "O que vocês mandaram ao BTG e quando" é a pergunta de todo incidente | **[spec]** |
| Rate limit e abuso | — | Rate limit por chave de API e por IP (Redis); **limite diário de payout por cliente**; **dupla aprovação** acima de um valor; bloqueio de saque com disputa aberta | Controle de dano, não só prevenção | **[spec]** |
| Dependências | `yarn` | `yarn audit` no CI; Socket.dev ou Snyk; lockfile travado; Renovate | Supply chain é o vetor nº 1 em Node | **[CI]** |
| Runtime | — | Node LTS em container distroless, usuário não-root, egress restrito aos domínios do BTG | Reduz superfície se alguém executar código | **[infra]** |
| ORM | TypeORM | TypeORM mantido. No ledger: `createQueryBuilder` + transação no repositório (regra já existente); **zero `save()` em entidade de ledger**; inserts explícitos | O harness já proíbe `find()`/`findOne()`; o ledger só acrescenta "nunca atualiza" | **[hook]** |

## 3. Frontend — três ajustes

| Hoje | Para pagamentos | Por quê |
|---|---|---|
| Token em `localStorage`; um SPA por público para não misturar tokens | **Cookie `HttpOnly` + `SameSite=Strict`** com CSRF token; nunca `localStorage` | É o ponto que mais derruba painéis financeiros em pentest. E remove o motivo técnico de separar SPAs por público (a separação continua valendo por **papel**, não por token) |
| axios com interceptor de token | Interceptor faz refresh silencioso e anexa `Idempotency-Key` (um `uuid` por **ação do usuário**, não por request) | Duplo clique não gera duas cobranças |
| Um painel admin | **Painel do operador em domínio separado** do painel do cliente; **MFA obrigatório** (TOTP ou passkey) para quem aprova payouts; CSP rígida nos dois | Quem move dinheiro tem segundo fator; quem só consulta, não |

O harness já tem a spec `057-admin-login-two-factor-auth` concluída no ERP — serve de referência
de forma para o MFA.

## 4. Workspaces propostos

| Workspace | Pasta | Público | Observação |
|---|---|---|---|
| Backend API | `backend/api/` | — | Express + TypeORM + DDD; módulos abaixo |
| Frontend Operador | `frontend/operador/` | Equipe da plataforma e da V-Corp | MFA obrigatório; aprova payouts, vê conciliação |
| Frontend Cliente | `frontend/cliente/` | Cliente final (PME) | Saldo, extrato, cobranças, saque |
| Simulador BTG | `tools/btg-simulator/` | — | Servidor fake que imita as respostas do BTG; usado em dev, teste e demo |

Módulos iniciais do backend (contexto → módulos):

| Contexto | Módulos | Perfil de scaffold |
|---|---|---|
| `platforms` | platforms, api_keys, webhook_endpoints | padrão |
| `accounts` | accounts (conta de pagamento BTG por cliente), onboarding_documents | padrão + `CryptoProvider` |
| `ledger` | ledger_entries, ledger_accounts, reconciliations | **`--append-only`** |
| `charges` | charges (cobranças Pix) | padrão sem Delete |
| `payouts` | payouts, payout_approvals | padrão sem Delete |
| `splits` | split_rules, split_executions | regras padrão; execuções `--append-only` |
| `btg` | btg_adapter (interface + real + simulador), btg_events (webhooks recebidos, `--append-only`) | `--no-table` para o adapter |
| `audit` | audit_log | **`--append-only`** |
| `users` | users, profiles, permissions, users_groups (reaproveitado do ERP) | padrão |

## 5. Invariantes do ledger (viram testes de propriedade na spec 003)

1. Em toda transação, soma dos débitos = soma dos créditos.
2. Saldo de uma conta = soma dos lançamentos; nunca lido de coluna.
3. Lançamento nunca é alterado nem apagado; estorno é lançamento novo com referência ao original.
4. Webhook duplicado (mesmo `event_id`) não gera segundo lançamento.
5. Webhooks fora de ordem convergem para o mesmo saldo final.
6. Conciliação diária: saldo derivado = saldo da conta BTG lido por API; divergência gera alerta,
   nunca ajuste automático.
7. Payout acima do limite exige segunda aprovação de usuário diferente do solicitante.
8. Nenhuma operação de escrita sem `Idempotency-Key`; chave repetida devolve a resposta original.

## 6. O que vale mais que qualquer item acima

- Pentest externo antes da homologação com o BTG.
- Testes que provam as invariantes do ledger em qualquer sequência de eventos.
- Produção em que **nenhum desenvolvedor acessa o banco diretamente**.
