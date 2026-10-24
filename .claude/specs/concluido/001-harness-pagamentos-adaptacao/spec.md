# Spec: Adaptação do harness para a plataforma de pagamentos

> **Camada 1 de 3 (SDD)** — esta spec descreve **O QUÊ** e **POR QUÊ**. Nada de "como".
> Design técnico vai em `plan.md`. Passos de execução vão em `tasks.md`.
> **Status**: `aprovada`
> **Contexto de negócio**: harness (transversal — nenhum contexto de produto)
> **Data**: 2026-10-23
> **Aprovada pelo usuário em**: 2026-10-23
> **Emenda**: 2026-10-23 — RN-13 passa a cobrir `PATCH` (decisão do usuário no `/spec-plan`). Reaprovada pelo usuário em 2026-10-23

---

## 1. Objetivo

Transformar o harness herdado do ERP Vida Fértil no harness da plataforma de pagamentos sobre o
BaaS do BTG, **antes de qualquer linha de código de produto**. O processo (SDD, hooks, gate,
`verifier`, hierarquia de fontes, lessons) fica intacto; o que muda é o domínio que ele descreve e
as regras financeiras que ele passa a verificar mecanicamente — dinheiro em `BIGINT`, ledger
imutável, idempotência em toda escrita e nenhum segredo no código.

## 2. Contexto do domínio

- O repositório é um fork do harness do ERP (`rszaneti/harness_vidafertil`, commit `0c878b7`).
  Contém só a camada de harness; **não existe nenhum workspace de produto neste checkout**.
- O produto opera no **modelo 2 (BaaS do BTG)**: a plataforma é software e API, o BTG é o
  custodiante, e a plataforma nunca guarda saldo de terceiros (`documentacao/03` §1–§4, RN-REG-01
  a 06).
- A stack é a do harness; o que muda é como cada peça é usada (`documentacao/04` §1–§3). Os três
  conflitos do harness com pagamentos — JWT HS256 com token em `localStorage`, entity padrão com
  Update/Delete, dinheiro em `numeric` — estão em `documentacao/05` §2. Esta spec resolve os dois
  últimos no harness; o primeiro é a spec 002.
- O harness atual tem os caminhos `backend/admin`, `frontend/admin`, `frontend/portal` e
  `frontend/professional` fixos no gate, no hook pós-edição, no scaffold e em ~30 arquivos de
  agentes, comandos, skills e lessons. Os workspaces do produto passam a ser os de
  `documentacao/04` §4.
- Fonte desta spec: `documentacao/05` §4 (entregas 1–8), com as decisões tomadas pelo usuário em
  23/10/2026 durante o `/spec-new` (RN-04, RN-08, RN-10, RN-15).

## 3. Regras de Negócio

**Documentação e memória do projeto**

- [RN-01] O `CLAUDE.md` raiz descreve o produto de pagamentos, não o ERP. Contém: produto e modelo
  de custódia; os workspaces `backend/api`, `frontend/operador`, `frontend/cliente` e
  `tools/btg-simulator`; os contextos e módulos de `documentacao/04` §4; os providers
  compartilhados; e as regras críticas do monorepo **acrescidas** de: "nenhuma coluna monetária
  fora de `BIGINT` em centavos", "ledger é append-only" e "`Idempotency-Key` em toda escrita".
- [RN-02] O `CLAUDE.md` raiz nunca chama de "existente" um workspace, módulo ou provider sem código
  no checkout. O que ainda não existe aparece como **planejado**, com a spec que o cria. Workspace
  ausente continua sendo o caso normal, como o `portal`/`professional` eram no ERP.
- [RN-03] A justificativa "um SPA por público por causa do token" sai do `CLAUDE.md`. A separação
  entre `operador` e `cliente` passa a valer por **papel e domínio**, não por token
  (`documentacao/04` §3).
- [RN-04] `documentacao/` contém só a documentação de pagamentos indexada no `00-README.md`. Saem:
  `Roteiro-MVP-Plataforma-de-Pagamentos-BTG-BaaS.md` (versão anterior do `02`),
  `Ui_Ux/PADRAO-UI-V2.md` (padrão visual do ERP) e `HARNESS.md:Zone.Identifier`.
- [RN-05] O `documentacao/HARNESS.md` é reiniciado: o histórico começa na **v1.0 do clone**
  (23/10/2026, esta spec) e o roteiro F0–F7 do ERP sai do arquivo. Uma nota de origem aponta para
  o repositório e o commit de onde o histórico anterior pode ser lido. As **dívidas abertas** do ERP
  que ainda valem para o harness (ex.: "`verify.sh` não alcança `.py`/`.sh`/`.md` do harness")
  continuam registradas.
- [RN-06] As lessons ficam **inteiras**: códigos BE/FE/AG, textos e caminhos originais. O
  `lessons/README.md` ganha a nota de origem ("lessons herdadas do ERP Vida Fértil em 23/10/2026;
  códigos BE/FE/AG mantidos") e a correspondência dos caminhos citados (`backend/admin` →
  `backend/api` etc.). Lesson é registro de erro real; reescrever o caminho reescreveria a
  evidência.

**Workspaces no harness**

- [RN-07] Gate (`verify.sh`), hook pós-edição e scaffold reconhecem os quatro workspaces novos e
  deixam de reconhecer os do ERP. Workspace ausente vira **aviso** no resumo do gate, sem reprovar
  — o mesmo comportamento que `portal`/`professional` tinham.
- [RN-08] As menções em prosa aos workspaces do ERP em agentes, comandos, skills, `verifier-checks`,
  `specs/README.md` e `sprints/_template.md` passam a citar os workspaces novos. O conteúdo de
  domínio dessas peças não muda nesta spec (ver Fora do escopo).

**Scaffold append-only**

- [RN-09] Existe um perfil de scaffold **append-only** para registros que nunca se alteram nem se
  apagam. O módulo gerado tem: entity sem campos de atualização (`user_updated`/`updated_at`),
  repositório sem operação de alterar ou apagar, só os services de criar, exibir, listar e contar,
  controller de 3 métodos, as rotas listar / exibir por id / criar, migration com uma trigger que
  rejeita `UPDATE` e `DELETE` no banco, e 4 testes.
- [RN-10] Na 001 o perfil append-only é verificado **sem workspace**: o que ele gera (lista de
  arquivos, ausência de alterar/apagar, trigger presente, 3 rotas, 4 testes) é conferido por
  checagem automática sobre a saída do gerador. A verificação completa — compilar, passar lint e
  testes dentro de `backend/api` — vira critério de aceite da **primeira spec que criar o
  workspace `backend/api`**, e a spec 002 em rascunho registra isso.

**Hooks financeiros**

- [RN-11] **Dinheiro**: migration ou entity de contexto financeiro com coluna `numeric`, `decimal`,
  `float`/`double`/`real` ou propriedade TypeScript monetária fracionária é reprovada no momento da
  edição. Contextos financeiros: `ledger`, `accounts`, `charges`, `payouts`, `splits`, `btg` e
  `platforms`. Proporções (taxas, percentuais de split) também não usam decimal; a unidade inteira é
  definida pela spec da feature.
- [RN-12] **Imutabilidade**: código dos módulos append-only de `documentacao/04` §4 — `ledger/*`,
  `audit/*`, `btg/btg_events` e `splits/split_executions` — que altere, apague ou use `save(` em
  entidade é reprovado no momento da edição.
- [RN-13] **Idempotência**: toda rota `POST`/`PUT`/`PATCH` em arquivo de rotas do backend exige o
  middleware de idempotência, salvo isenção declarada (RN-15). `PATCH` entra porque é o verbo das
  ações de workflow (aprovar, cancelar), e a aprovação de payout é uma delas; `DELETE` fica fora
  porque repetir um `DELETE` já é idempotente (invariante 8 de `documentacao/04` §5).
- [RN-14] **Segredos**: literal com forma de chave, secret ou token em `src/` de qualquer workspace é
  reprovado no momento da edição. Este hook **não** aceita marcador de isenção; o plan define como
  testes obtêm valores sintéticos sem disparar o hook.
- [RN-15] A isenção do hook de idempotência é **declarada na própria rota**, com marcador que exige
  o motivo por escrito (ex.: webhook recebido do BTG, que deduplica pelo `event_id`; login e refresh
  da spec 002). Marcador sem motivo é reprovado. O `verifier` audita toda isenção presente no diff.
- [RN-16] Cada hook novo tem, em `.claude/scripts/tests/`, pelo menos um caso que reprova e um caso
  que passa, e existe um comando único que roda todos esses casos. Isso mitiga, para os hooks desta
  spec, a dívida "o gate não alcança o harness" (RN-05).

**Skill e auditoria**

- [RN-17] A skill `backend-module` ganha a seção **"Regras financeiras"**: dinheiro em `BIGINT`
  centavos, append-only, transação no repositório, idempotência e HMAC. O mapeamento atual
  "decimal → `numeric(p,s)`" deixa de valer para colunas monetárias.
- [RN-18] O `check-module.py` reprova módulo de contexto financeiro que viole as regras da RN-17,
  com a mesma régua dos hooks (RN-11 a RN-13).

**Specs seguintes e estado inicial**

- [RN-19] As specs `002-auth-jwks-httponly` e `003-ledger-core` são abertas em `a_fazer/`, só com
  `spec.md` em `rascunho` (sem plan nem tasks). A 003 traz as 8 invariantes do ledger de
  `documentacao/04` §5 como critérios `[auto]`. A 002 traz, em "Questões em aberto", se é ela que
  cria o workspace `backend/api` (RN-10).
- [RN-20] O estado herdado do ERP é zerado: `.claude/specs/{a_fazer,em_andamento,concluido,canceladas}/`
  sem specs do ERP (só 001, 002 e 003) e `.claude/gate/` sem evidência do ERP (65 arquivos hoje).
  `lessons/` e `settings.json` ficam como estão.
- [RN-21] O repositório raiz termina com o **commit inicial** e `git status` limpo. O commit só é
  feito com autorização explícita do usuário.

## 4. Escopo

**Dentro do escopo:**
- `CLAUDE.md` raiz reescrito (RN-01 a RN-03).
- Limpeza de `documentacao/` e `HARNESS.md` reiniciado (RN-04, RN-05).
- Nota de origem nas lessons (RN-06).
- Troca dos workspaces no gate, no hook, no scaffold e nas menções em prosa (RN-07, RN-08).
- Perfil de scaffold append-only com verificação estática (RN-09, RN-10).
- Quatro hooks financeiros, a isenção declarada e os casos de teste (RN-11 a RN-16).
- Seção "Regras financeiras" na skill e checagem no `check-module.py` (RN-17, RN-18).
- Specs 002 e 003 em rascunho; estado do ERP zerado; commit inicial (RN-19 a RN-21).

**Fora do escopo (explicitamente NÃO fazer):**
- **Qualquer código de produto**: workspaces, módulos, migrations, telas, simulador do BTG.
- Criar o workspace `backend/api` ou rodar o `--self-test` completo do perfil append-only (RN-10).
- Reescrever o conteúdo das skills `ui-v2` e `frontend-module` e das telas canônicas, que continuam
  descrevendo o ERP — isso é das specs 010/011. Só os caminhos mudam (RN-08).
- Hooks marcados `[hook]` em `documentacao/04` §2 que não estão na §4 do `05`: Joi sem
  `unknown(true)` e validação de assinatura do webhook antes do parse. Ficam para as specs que
  criarem rotas e webhooks (002 e 004).
- Plan e tasks das specs 002 e 003, ou aprovar essas specs.
- Mudar o `settings.json` (o `Bash(redis-cli:*)` só entra se o simulador precisar, na spec 004).
- Reabrir as decisões de `documentacao/00-README.md` ou responder as perguntas em aberto sobre o BTG.
- Mexer em `.claude/_backup_pre_harness_*` (ignorado pelo `.gitignore`).

## 5. Dependências

- `documentacao/00`, `03`, `04`, `05` e `06` — fonte de negócio desta spec.
- Harness herdado: `.claude/scripts/verify.sh`, `.claude/hooks/`, `.claude/scaffold/`,
  `.claude/scripts/check-module.py`, `.claude/skills/backend-module/`.
- Nenhuma spec anterior. É a primeira do clone.

## 6. Critérios de Aceite

- [x] [CA-01] O `CLAUDE.md` raiz não menciona clínica, doador, tentante, especialista nem os
  workspaces do ERP, e contém as três regras críticas novas da RN-01. `[auto]`
- [x] [CA-02] Todo workspace, módulo e provider citado no `CLAUDE.md` raiz existe no checkout **ou**
  está marcado como planejado, com a spec que o cria (RN-02). `[auto]` — conferido pelo `verifier`
- [x] [CA-03] `ls documentacao/` lista só os documentos do índice do `00-README.md` mais o
  `HARNESS.md`; os três arquivos da RN-04 não existem. `[auto]`
- [x] [CA-04] O `HARNESS.md` tem o histórico a partir da v1.0 do clone, a nota de origem e as dívidas
  que ainda valem; não tem mais o roteiro F0–F7 do ERP. `[humano]`
- [x] [CA-05] As lessons (`backend.md`, `frontend.md`, `agents.md`) são idênticas às herdadas, e o
  `lessons/README.md` tem a nota de origem e a correspondência de caminhos. `[auto]`
- [x] [CA-06] Nenhum arquivo executável do harness (`.py`, `.sh`, `.json`) referencia
  `backend/admin`, `frontend/admin`, `frontend/portal` ou `frontend/professional`. `[auto]`
- [x] [CA-07] O gate rodado sem nenhum workspace presente termina sem reprovar e lista os quatro
  workspaces novos como ausentes. `[auto]`
- [x] [CA-08] Agentes, comandos, skills, `verifier-checks`, `specs/README.md` e
  `sprints/_template.md` citam só os workspaces novos (lessons ficam fora, RN-06). `[auto]`
- [x] [CA-09] O perfil append-only, rodado em modo de simulação, produz exatamente os arquivos da
  RN-09, e uma checagem automática confirma: sem alterar/apagar, trigger presente, 3 rotas, 4
  testes. Os self-tests dos perfis existentes continuam aprovando a parte que não depende de
  workspace. `[auto]`
- [x] [CA-10] Cada um dos 4 hooks novos reprova o seu caso inválido e aprova o seu caso válido, e o
  comando único da RN-16 roda todos os casos e sai com código 0. `[auto]`
- [x] [CA-11] Rota `PATCH` sem o middleware é reprovada pelo hook de idempotência. Rota `POST` com marcador de isenção **e** motivo passa no hook de idempotência; a
  mesma rota com marcador **sem** motivo é reprovada. `[auto]`
- [x] [CA-12] O `check-module.py` reprova um módulo de exemplo de contexto financeiro que viola as
  regras financeiras e aprova a versão corrigida. `[auto]`
- [x] [CA-13] A skill `backend-module` tem a seção "Regras financeiras" e não mapeia mais coluna
  monetária para `numeric`. `[humano]`
- [x] [CA-14] Existem `.claude/specs/a_fazer/002-auth-jwks-httponly/spec.md` e
  `.claude/specs/a_fazer/003-ledger-core/spec.md` em `rascunho`, só com `spec.md`; a 003 tem as 8
  invariantes como CA `[auto]`; a 002 tem a questão em aberto sobre o workspace. `[auto]`
- [x] [CA-15] `.claude/specs/` só contém as specs 001, 002 e 003 (fora templates e README), e
  `.claude/gate/` só contém o `.gitkeep` e a evidência desta spec. `[auto]`
- [x] [CA-16] Depois do commit inicial autorizado pelo usuário, `git status` da raiz está limpo.
  `[humano]`
- [x] [CA-17] O usuário lê o `CLAUDE.md` raiz novo e confirma que ele descreve a plataforma de
  pagamentos como o harness deve vê-la. `[humano]`

## 7. Questões em aberto

> Dúvidas que precisam de resposta do usuário ANTES de gerar o plan.
> O `/spec-plan` não roda enquanto houver questão aberta.

Nenhuma. As quatro questões levantadas durante o `/spec-new` foram respondidas pelo usuário em
23/10/2026 e estão incorporadas em RN-04, RN-07/RN-08, RN-10 e RN-15.
