# check `financeiro` — dinheiro, imutabilidade e idempotência [spec 001, RN-11 a RN-15]

> Acende quando o diff toca um módulo de contexto financeiro do backend (`ledger`, `accounts`,
> `charges`, `payouts`, `splits`, `btg`, `platforms`), um módulo append-only, ou quando uma linha
> adicionada traz o marcador `idempotency-exempt`. A lista de contextos mora em
> `.claude/hooks/financial_rules.py` — não aqui.

## O passo 2 já rodou as regras — o que sobra é julgamento

O `check-module.py` (check `financeiro`) roda as **mesmas** quatro regras dos hooks pós-edição:
achado ali é ALTA, sem discussão. Este check é sobre o que a regra mecânica **não decide**.

## 1. Cada isenção de idempotência (RN-15)

Liste **toda** linha `idempotency-exempt: <motivo>` do diff, uma por uma. Para cada uma:

- O motivo procede? Os legítimos conhecidos: webhook recebido que **deduplica por `event_id`**
  (o BTG reenvia; a dedup é do evento, não do header), login e refresh de sessão (spec 002).
- "Rota interna", "só o operador chama", "o frontend não manda o header" **não** são motivos:
  retry de rede acontece em qualquer chamador, e é exatamente o caso que a invariante 8 protege.
- A rota isenta **escreve dinheiro**? Então a dedup alternativa tem de estar provada por teste
  (mesmo `event_id` duas vezes → um lançamento — invariante 4 de `documentacao/04` §5).

Isenção sem motivo que proceda é **REPROVADO**, mesmo com o hook verde.

## 2. `--append-only` onde a lista manda

Módulo de `APPEND_ONLY_MODULES` gerado sem o perfil é barrado pelo scaffold e pelo
`check-module.py` (completude `RN-09`). O que sobra para julgar: **módulo novo que deveria estar na
lista e não está**. Registro que é fato consumado — evento recebido, lançamento, execução de
ordem, trilha de auditoria — é append-only. Se a feature cria um assim, a lista em
`financial_rules.py` cresce **na mesma feature**, e o verifier reprova se não crescer.

## 3. Saldo, ajuste e conta de passagem (`documentacao/03` §4)

O hook não sabe o que é "saldo". Confira à mão:

- Nenhuma coluna `balance`/`saldo` editável (RN-REG-01): saldo é **derivado** do ledger.
- Lançamento sem contrapartida no BTG (evento recebido ou ordem enviada) é divergência, nunca
  "ajuste manual" (RN-REG-02).
- Split é transferência entre contas BTG; saque sai da conta do cliente (RN-REG-03/04). Qualquer
  desenho com "conta transitória", "carteira" ou "repasse" é contestado com referência ao `03`
  (RN-REG-06).

## 4. Falso positivo aceito, não contornado

O `ledger-immutable` acusa `.delete(` de `Map`/`Set` e o `money-bigint` acusa `.toFixed(` de log.
A saída é **reescrever a linha**, não pedir exceção. Se o mesmo falso positivo aparecer em duas
features, é candidato a lesson e a ajuste da regra em `financial_rules.py` (com fixture `-limpo`
nova), nunca a marcador.
