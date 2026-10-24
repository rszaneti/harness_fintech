# Spec: Ledger de partidas dobradas

> **Camada 1 de 3 (SDD)** — esta spec descreve **O QUÊ** e **POR QUÊ**. Nada de "como".
> Design técnico vai em `plan.md`. Passos de execução vão em `tasks.md`.
> **Status**: `rascunho`
> **Contexto de negócio**: `ledger` (ledger_entries, ledger_accounts, reconciliations)
> **Data**: 2026-10-23
> **Aprovada pelo usuário em**: pendente ← gate humano obrigatório
>
> ⚠️ **Rascunho aberto pela spec 001 (RN-19)** a partir de `documentacao/04` §2 e §5 e de
> `documentacao/03` §4, **sem a entrevista do `/spec-new`**. Não é aprovável como está: rodar
> `/spec-new 003-ledger-core` com o usuário, que revisa as RN e responde as questões em aberto.

---

## 1. Objetivo

Registrar todo movimento de dinheiro dos clientes como lançamentos imutáveis de partidas dobradas,
dos quais o saldo é **derivado** e conferido todo dia contra o saldo da conta no BTG. O ledger não
guarda dinheiro (o BTG guarda): ele é a memória auditável do que a plataforma viu e ordenou.

## 2. Contexto do domínio

- Modelo 2 (`documentacao/03`): o dinheiro está nas contas BTG dos clientes. Um saldo
  "editado" na plataforma é o erro clássico — e aqui seria também a definição de conta de pagamento,
  proibida sem licença (RN-REG-01, RN-REG-06).
- Todo lançamento tem contrapartida no banco: um evento recebido do BTG ou uma ordem enviada a ele
  (RN-REG-02).
- O harness já tem o perfil `--append-only` (spec 001): tabela com trigger que rejeita
  `UPDATE`/`DELETE`/`TRUNCATE`, repositório que só insere, hook que reprova mutação no código.

## 3. Regras de Negócio

> Rascunho a partir de `documentacao/04` §2/§5 e `03` §4. A entrevista do `/spec-new` confirma.

- [RN-01] Lançamento em **partidas dobradas**: toda transação tem débitos e créditos que somam igual.
- [RN-02] Saldo de uma conta é a **soma dos lançamentos** — nunca lido de coluna (RN-REG-01).
- [RN-03] Lançamento nunca é alterado nem apagado; **estorno é lançamento novo** com referência ao
  original.
- [RN-04] Todo lançamento referencia um **evento do BTG** (webhook ou extrato) **ou** uma **ordem
  enviada ao BTG** (Pix envio, transferência). Lançamento sem contrapartida é divergência, nunca
  ajuste manual (RN-REG-02).
- [RN-05] Valores em `bigint` **centavos** (`*_cents`).
- [RN-06] Ao lançar, a conta é travada (`SELECT … FOR UPDATE`) dentro da transação.
- [RN-07] **Conciliação diária**: saldo derivado × saldo da conta BTG lido por API; divergência gera
  **alerta**, nunca ajuste automático.

## 4. Escopo

**Dentro do escopo:**
- Contas do ledger, lançamentos, estorno, saldo derivado, conciliação diária.

**Fora do escopo (explicitamente NÃO fazer):**
- O adaptador do BTG e o recebimento de webhooks (spec 004) — a 003 consome eventos já recebidos.
- Split e payout (specs 008 e 009), que **produzem** lançamentos por esta API.

## 5. Dependências

- Spec 001 (perfil `--append-only`, hooks financeiros).
- Spec 002 (workspace `backend/api`, se for ela que o criar).
- Spec 004 para os eventos reais; até lá, o simulador.

## 6. Critérios de Aceite

> As 8 invariantes de `documentacao/04` §5, cada uma um teste de propriedade — verdadeiras **em
> qualquer sequência de eventos**, não só nos casos escolhidos.

- [ ] [CA-01] Em toda transação, soma dos débitos = soma dos créditos. `[auto]`
- [ ] [CA-02] Saldo de uma conta = soma dos lançamentos; nunca lido de coluna. `[auto]`
- [ ] [CA-03] Lançamento nunca é alterado nem apagado; estorno é lançamento novo com referência ao original. `[auto]`
- [ ] [CA-04] Webhook duplicado (mesmo `event_id`) não gera segundo lançamento. `[auto]`
- [ ] [CA-05] Webhooks fora de ordem convergem para o mesmo saldo final. `[auto]`
- [ ] [CA-06] Conciliação diária: saldo derivado = saldo da conta BTG lido por API; divergência gera alerta, nunca ajuste automático. `[auto]`
- [ ] [CA-07] Payout acima do limite exige segunda aprovação de usuário diferente do solicitante. `[auto]`
- [ ] [CA-08] Nenhuma operação de escrita sem `Idempotency-Key`; chave repetida devolve a resposta original. `[auto]`

## 7. Questões em aberto

> Dúvidas que precisam de resposta do usuário ANTES de gerar o plan.
> O `/spec-plan` não roda enquanto houver questão aberta.

- [ ] **Representação em TypeScript do `bigint`**: o driver `pg` devolve `bigint` como `string`.
      Entity e contrato de API usam `string`, `bigint` nativo (que não serializa em JSON) ou um
      transformer para `number` (seguro até 2^53 centavos)? Afeta o contrato de API de todo
      contexto financeiro (spec 001, plan 2.8.6).
- [ ] **`audit_log` entra nesta spec?** A sequência de `documentacao/05` §5 não atribui o contexto
      `audit` a nenhuma spec; o `CLAUDE.md` raiz o marca como "planejado — spec 003" até esta
      resposta.
- [ ] **CA-07 (dupla aprovação de payout) e CA-08 (idempotência)** são invariantes do ledger em
      `documentacao/04` §5, mas o comportamento é das specs 009 e 002. A 003 prova as duas no
      ledger, ou só as registra e as delega?
