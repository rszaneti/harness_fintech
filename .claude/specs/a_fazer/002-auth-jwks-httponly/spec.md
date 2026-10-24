# Spec: Autenticação com JWKS, sessão em cookie HttpOnly e API máquina-a-máquina

> **Camada 1 de 3 (SDD)** — esta spec descreve **O QUÊ** e **POR QUÊ**. Nada de "como".
> Design técnico vai em `plan.md`. Passos de execução vão em `tasks.md`.
> **Status**: `rascunho`
> **Contexto de negócio**: `users`, `platforms` (api_keys)
> **Data**: 2026-10-23
> **Aprovada pelo usuário em**: pendente ← gate humano obrigatório
>
> ⚠️ **Rascunho aberto pela spec 001 (RN-19)** a partir de `documentacao/04` §2–§3, **sem a
> entrevista do `/spec-new`**. Não é aprovável como está: rodar `/spec-new 002-auth-jwks-httponly`
> com o usuário, que revisa as RN abaixo e responde as questões em aberto.

---

## 1. Objetivo

Dar à plataforma uma autenticação à altura de um sistema que ordena movimentação de dinheiro:
pessoas (operador e cliente) entram por sessão em cookie `HttpOnly` com token assinado por chave
assimétrica, e plataformas clientes chamam a API com chave de API e assinatura de cada requisição.
É o primeiro dos três conflitos do harness herdado com pagamentos (`documentacao/05` §2, item 1).

## 2. Contexto do domínio

- O harness herdado usava JWT **HS256** com um secret por público e token em `localStorage`. Secret
  compartilhado é o erro clássico; `localStorage` é o ponto que mais derruba painel financeiro em
  pentest (`documentacao/04` §2–§3).
- Com **JWKS**, as plataformas clientes validam o token sem conhecer a chave privada.
- Chamada máquina-a-máquina autentica **a chamada**, não só o chamador: assinatura do corpo +
  timestamp torna o replay inviável (padrão Stripe).
- Segredos são o primeiro item do checklist de homologação do BTG.

## 3. Regras de Negócio

> Rascunho a partir de `documentacao/04`. A entrevista do `/spec-new` confirma, corta ou detalha.

- [RN-01] Token de acesso assinado com chave **assimétrica** (RS256 ou ES256), com chaves públicas
  publicadas em **JWKS**. Validade do token de acesso: **5 a 15 minutos**.
- [RN-02] Refresh token com **rotação** a cada uso e **revogação**; refresh reutilizado invalida a
  família inteira.
- [RN-03] Nos painéis, a sessão vai em cookie **`HttpOnly` + `SameSite=Strict`**, com token
  **CSRF**. Nunca em `localStorage`.
- [RN-04] O frontend renova a sessão em silêncio e anexa um `Idempotency-Key` **por ação do
  usuário**, não por requisição — duplo clique não gera duas cobranças.
- [RN-05] Plataforma cliente chama a API com **chave de API + assinatura HMAC-SHA256** do corpo e de
  um timestamp; requisição fora da **janela de 5 minutos** é recusada. mTLS quando o BTG exigir.
- [RN-06] Chave de API é guardada **cifrada** (`CryptoProvider`) e nunca é exibida de novo depois
  de criada.
- [RN-07] Segredos vêm de **cofre** (AWS Secrets Manager / Vault) com rotação; `.env` só em
  desenvolvimento; nenhum segredo em código ou log.

## 4. Escopo

**Dentro do escopo:**
- Autenticação de pessoas (operador e cliente) e de plataformas (chave de API + HMAC).
- Rotação/revogação de refresh; publicação de JWKS.

**Fora do escopo (explicitamente NÃO fazer):**
- MFA do operador (spec 010) — a 002 deixa o fluxo preparado, não o implementa.
- Webhooks que **emitimos** (spec 005) e validação dos que **recebemos** do BTG (spec 004).
- Rate limit, limite de payout e dupla aprovação (specs 009/010).

## 5. Dependências

- Spec 001 (harness adaptado): hooks financeiros, perfil `--append-only`, `workspaces.json`.
- Workspace `backend/api` — ver questão 1.

## 6. Critérios de Aceite

> A detalhar no `/spec-new`. Esboço:

- [ ] [CA-01] Token assinado com chave assimétrica e validável só pela JWKS pública. `[auto]`
- [ ] [CA-02] Refresh reutilizado revoga a família de tokens. `[auto]`
- [ ] [CA-03] Requisição de plataforma com assinatura inválida ou timestamp fora da janela é recusada. `[auto]`
- [ ] [CA-04] Nenhum token de sessão é legível por JavaScript nos painéis. `[humano]`

## 7. Questões em aberto

> Dúvidas que precisam de resposta do usuário ANTES de gerar o plan.
> O `/spec-plan` não roda enquanto houver questão aberta.

- [ ] **É a 002 que cria o workspace `backend/api`** (package.json, tsconfig, ESLint, Jest, infra
      compartilhada: `AppError`, IoC, `ensureAuthenticated`)? Se for, ela carrega também o
      **`--self-test` completo do perfil `--append-only`** (compilar, lint e jest dentro do
      workspace), que a spec 001 deixou pendente (spec 001, RN-10).
- [ ] **Quem cria o middleware `ensureIdempotency`?** Todo módulo gerado pelo scaffold desde a 001
      importa `@shared/infra/http/middlewares/ensureIdempotency`; sem ele, nenhum módulo compila.
      A invariante 8 (`documentacao/04` §5) diz o comportamento: chave repetida devolve a resposta
      original, guardada por 24 h.
- [ ] **Hooks `[hook]` do `documentacao/04` §2 que ficaram fora da 001**: Joi **sem
      `unknown(true)`** em body, query e params de toda rota. Entra como hook nesta spec, quando
      as primeiras rotas existirem?
- [ ] Login e refresh são rotas `POST` isentas de `Idempotency-Key` (marcador
      `idempotency-exempt` com motivo)? A isenção é julgada pelo `verifier` (spec 001, RN-15).
