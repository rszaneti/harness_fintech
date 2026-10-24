# Plan: Adaptação do harness para a plataforma de pagamentos

> **Camada 2 de 3 (SDD)** — design técnico derivado de `spec.md` + `documentacao/03`, `04`, `05`.
> Se a spec mudar, este plan deve ser regenerado/revisado — nunca o contrário.
> **Spec de origem**: `./spec.md` (status `aprovada`; emenda da RN-13 reaprovada em 2026-10-23)
> **Status**: `aprovado`
> **Aprovado pelo usuário em**: 2026-10-23

---

## 1. Abordagem

Feature **só de harness**: nenhum `.ts` de produto, nenhum workspace. Quatro movimentos, nesta
ordem de dependência:

1. **Uma fonte para os workspaces** — `.claude/workspaces.json` passa a ser o único lugar que diz
   quais workspaces existem e onde. Gate, hook, scaffold, `check-module.py`, `diff-classify.py`,
   `check-ui-v2-refs.py` e `block-shell-write-ts.py` leem dele. Hoje são 7 listas fixas que já
   divergem (`portal`/`professional` estão no gate e no hook, mas não no scaffold).
2. **Uma fonte para as regras financeiras** — `.claude/hooks/financial_rules.py` é a biblioteca. Os
   4 hooks são pontos de entrada finos sobre ela, e o `check-module.py` a importa. É o mesmo
   princípio da spec 087 (RN-03): a regra mora num lugar só, e o markdown só manda rodar o script.
3. **Perfil append-only por diretiva**, não por template novo: os templates existentes ganham
   blocos `// @if append_only` / `// @if !append_only`. Um template por papel continua sendo o
   contrato, e o perfil não diverge do padrão em silêncio.
4. **`verify.sh harness`** — o "comando único" da RN-16 vira alvo do gate. Ele roda as provas que
   substituem lint/tsc/jest para `.py`/`.sh` (o que o `verifier-checks/harness.md` pergunta 4 já
   exige) e grava evidência em `.claude/gate/`. Isso fecha, para o harness, parte da dívida
   "`verify.sh` não alcança o harness" registrada no `HARNESS.md`.

Documentação (`CLAUDE.md`, `HARNESS.md`, `documentacao/`, lessons, specs 002/003) vem por último,
porque descreve o que os passos 1–4 deixaram no lugar.

## 2. Backend

### 2.1 Entidades / Tabelas

Não se aplica — nenhuma tabela de produto. A forma da tabela append-only gerada pelo scaffold está
em 2.8.3.

### 2.2 Enums

Não se aplica.

### 2.3 Contrato de API

Não se aplica — nenhuma rota de produto, nenhuma tela. As rotas que o **perfil append-only gera**
são `GET /`, `GET /show/:id` e `POST /` (2.8.3), na mesma forma das do perfil padrão.

### 2.4 Validações (Joi)

Não se aplica.

### 2.5 Services

Não se aplica. O perfil append-only gera `Create`, `Show`, `List` e `ListTotal` (2.8.3).

### 2.6 Migration

Nenhuma migration de produto. O template `migration.ts.tpl` ganha o bloco `@if append_only` com a
trigger (2.8.3).

### 2.7 Mapeamento RN → implementação

| RN | Onde | Como |
|----|------|------|
| RN-01 | `CLAUDE.md` raiz | Reescrito (2.8.7): produto, modelo 2, 4 workspaces, contextos/módulos de `04` §4, providers, regras críticas + as 3 novas |
| RN-02 | `CLAUDE.md` raiz | Toda tabela de workspace/módulo/provider ganha a coluna **Estado** (`existe` / `planejado — spec NNN`). Hoje tudo é `planejado` |
| RN-03 | `CLAUDE.md` raiz | Seção "Um SPA por público" substituída: separação por **papel e domínio**, com referência a `04` §3 |
| RN-04 | `documentacao/` | `git rm` não se aplica (raiz sem commit) → remoção dos 3 arquivos; `00-README.md` ganha a linha do `HARNESS.md` |
| RN-05 | `documentacao/HARNESS.md` | Reescrito (2.8.7): nota de origem, dívidas vigentes, histórico a partir de `v1.0-clone` |
| RN-06 | `.claude/lessons/README.md` | Seção "Origem" com a nota e a tabela de correspondência de caminhos. `backend.md`/`frontend.md`/`agents.md` intocados |
| RN-07 | `workspaces.json` + leitores | 2.8.1 |
| RN-08 | agentes, comandos, skills, `verifier-checks`, `specs/README.md`, `sprints/_template.md` | Troca de caminhos na prosa, arquivo a arquivo (inventário em 2.8.1) |
| RN-09 | `scaffold.py` + templates backend | Flag `--append-only`, diretivas, destinos com condição negada (2.8.3) |
| RN-10 | `scaffold.py --self-test static` | Renderiza em diretório temporário, sem workspace e sem prettier, e confere invariantes (2.8.3) |
| RN-11 | `financial_rules.money_violations` → `hooks/money-bigint.py` | 2.8.4 |
| RN-12 | `financial_rules.immutable_violations` → `hooks/ledger-immutable.py` | 2.8.4 |
| RN-13 | `financial_rules.idempotency_violations` → `hooks/idempotency-required.py` | 2.8.4; `POST`/`PUT`/`PATCH` |
| RN-14 | `financial_rules.secret_violations` → `hooks/no-secret-in-code.py` | 2.8.4; sem marcador |
| RN-15 | `financial_rules.idempotency_violations` + `verifier-checks/financeiro.md` | Marcador `idempotency-exempt: <motivo>` (2.8.4); o check novo do verifier lista as isenções do diff |
| RN-16 | `.claude/scripts/tests/<hook>/` + `verify.sh harness` | Fixtures `*-acusa.*` / `*-limpo.*`, `--self-test` em cada hook, alvo `harness` no gate (2.8.5) |
| RN-17 | `.claude/skills/backend-module/SKILL.md` | Seção "Regras financeiras"; linha de tipos sem `decimal→numeric` para dinheiro (2.8.6) |
| RN-18 | `.claude/scripts/check-module.py` | Check novo `financeiro`, que chama a mesma `financial_rules` + completude do perfil append-only (2.8.6) |
| RN-19 | `.claude/specs/a_fazer/002-…/spec.md`, `003-…/spec.md` | Do template `_templates/spec.md`, status `rascunho` (2.8.8) |
| RN-20 | `.claude/gate/`, `.claude/specs/*` | Remover os 65 `.json` do ERP; `specs/*` já estão vazios (conferido) |
| RN-21 | raiz do monorepo | `.gitignore` ganha `tools/`; commit inicial em `master` **só com autorização** do usuário |

### 2.8 Design do harness

#### 2.8.1 `.claude/workspaces.json` — a fonte única dos workspaces

```json
{
  "backend":   { "path": "backend/api",          "kind": "backend",  "spec": "002" },
  "operador":  { "path": "frontend/operador",    "kind": "frontend", "spec": "010" },
  "cliente":   { "path": "frontend/cliente",     "kind": "frontend", "spec": "011" },
  "simulator": { "path": "tools/btg-simulator",  "kind": "backend",  "spec": "004" }
}
```

- `kind` diz quais etapas o gate roda (`backend` = eslint + tsc + jest; `frontend` = eslint + tsc) e
  quais templates o scaffold usa. `spec` é a spec prevista para criar o workspace, e é o que o
  `CLAUDE.md` cita como "planejado". Para o `backend/api` a 002 é provisória: a pergunta fica em
  aberto na própria 002 (RN-19).
- **Leitor Python** (`.claude/scripts/workspaces.py`, 1 função `load() -> dict`): importado por
  `scaffold.py`, `check-module.py`, `diff-classify.py`, `check-ui-v2-refs.py` e
  `block-shell-write-ts.py`. O `WS = {...}` fixo de cada um sai.
- **Leitor Bash**: `verify.sh` e `post-edit-check.sh` chamam `python3 .claude/scripts/workspaces.py
  --path <ws>` e `--which <arquivo>`, que devolve a chave do workspace que contém o arquivo. Os
  `case` com caminhos fixos saem.

**Alvos do `verify.sh`** (os nomes `backend` e `frontend` continuam valendo, para a prosa dos
agentes não precisar mudar de forma):

| Alvo | Roda |
|---|---|
| `backend` | `backend` |
| `frontend` | `operador` + `cliente` |
| `operador`, `cliente`, `simulator` | o próprio |
| `harness` | 2.8.5 |
| `all` | os quatro workspaces + `harness` |

Workspace ausente continua no ramo que já existe (`verify_workspace`, linha 443): aviso, sem
reprovar. A mensagem perde a referência à "spec 032" e passa a citar o campo `spec` do JSON.

**Scaffold e `check-module.py`**: o argumento deixa de ser `backend|frontend` e passa a ser a chave
do workspace (`backend`, `operador`, `cliente`, `simulator`). Para `frontend`, o scaffold exige
`--ws operador|cliente`, porque agora são dois.

**Inventário da troca em prosa (RN-08)** — contagem de hoje de menções a `backend/admin`,
`frontend/admin`, `frontend/portal` e `frontend/professional`:

| Arquivos | Menções |
|---|---|
| executáveis: `block-shell-write-ts.py` (35), `post-edit-check.sh` (9), `verify.sh` (5), `check-ui-v2-refs.py` (2), `diff-classify.py`, `check-module.py`, `scaffold.py` (1 cada) | 54 |
| agentes: `backend-lead` (6), `frontend-lead` (5), `backend-builder` (5), `ui-reviewer` (3), `backend-test-author` (3), `verifier`, `ui-planner`, `frontend-builder` (2 cada) | 28 |
| skills: `ui-v2/SKILL.md` (5), `backend-module` (5), `frontend-module` (3), `ui-v2/references/*` (5) | 18 |
| comandos: `sprint-close` (3), `new-migration`, `new-frontend-module` (2 cada), `spec-plan`, `new-backend-module` (1 cada) | 9 |
| `sprints/_template.md` (4), `verifier-checks/tela.md` (1), `specs/README.md` (1) | 6 |
| **fora da troca**: `lessons/backend.md` (3), `lessons/frontend.md` (5) — RN-06 | 8 |

A `ui-v2` e suas referências trocam o caminho e ganham, no topo, uma linha dizendo que o padrão é
herdado do ERP e será revisto nas specs 010/011. Nada além disso muda no conteúdo delas.

#### 2.8.2 `.gitignore`

`tools/` entra ao lado de `backend/` e `frontend/` (o simulador terá `.git` próprio, regra 1). O
comentário do topo deixa de citar o ERP.

#### 2.8.3 Perfil `--append-only` no scaffold

**CLI**: `scaffold.py backend <contexto> <modulo> <Entity> --append-only [...]`. É incompatível com
`--no-table` (exit 64): registro imutável sem tabela não tem o que proteger.

**Guarda**: o scaffold **recusa** gerar sem `--append-only` um módulo que está em
`financial_rules.APPEND_ONLY_MODULES` (`ledger/*`, `audit/*`, `btg/btg_events`,
`splits/split_executions`), com exit 64. Prevenir na geração custa uma linha e evita que o hook da
RN-12 reprove 6 arquivos logo depois.

**Mecânica**:
- `append_only` entra em `DIRECTIVE_FLAGS` e em `backend_values().flags`.
- A condição de `BACKEND_DEST` passa a aceitar negação (`"!append_only"`), com a mesma semântica do
  `apply_directives`. Ganham essa condição: `dto-update`, `service-update`, `service-delete`,
  `test-update` e `test-delete`.
- O inventário (`--list-placeholders`) e o `check_completude` usam a mesma função de avaliação de
  condição. Hoje cada um faz `cond and not flags.get(cond)`, que trataria `"!append_only"` como
  flag desconhecida.

**O que muda em cada template (blocos de diretiva)**:

| Template | Padrão (`!append_only`) | Append-only |
|---|---|---|
| `entity.ts.tpl` | como hoje | sem `UpdateDateColumn` no import, sem `user_updated`, sem `updated_at` |
| `migration.ts.tpl` | como hoje | sem `user_updated`/`updated_at`; depois do `createTable`, a função `reject_mutation()` (`CREATE OR REPLACE`) e duas triggers: `BEFORE UPDATE OR DELETE … FOR EACH ROW` e `BEFORE TRUNCATE … FOR EACH STATEMENT`. O `down` só faz `dropTable`; a função é compartilhada entre tabelas e fica |
| `repository-interface.ts.tpl` | como hoje | sem `save` e sem `delete`; `create(data, manager?: EntityManager)` |
| `repository.ts.tpl` | como hoje | `create` com `createQueryBuilder().insert().values({ id: uuidv4(), ...data }).returning('*')`, sem `save()`, usando o `manager` quando houver (BE-017); sem `save` e sem `delete` |
| `controller.ts.tpl` | como hoje | 3 métodos (`index`, `show`, `create`); sem `IRequestDelete` e sem os imports de Update/Delete |
| `routes.ts.tpl` | `POST` e `PUT` com `ensureIdempotency` | `GET /`, `GET /show/:id`, `POST /` (com `ensureIdempotency`); sem `PUT` e sem `DELETE` |
| `test-{create,show,list,listtotal}.spec.ts.tpl` | mock com `save`/`delete` | mock sem `save`/`delete` (o objeto literal tipado pela interface não aceita chave a mais) |

Texto da trigger (dentro de `queryRunner.query`, com `__tabela__` substituído):

```sql
CREATE OR REPLACE FUNCTION reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'tabela % é append-only: % rejeitado', TG_TABLE_NAME, TG_OP;
END;
$$;
CREATE TRIGGER __tabela___reject_mutation BEFORE UPDATE OR DELETE ON __tabela__
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();
CREATE TRIGGER __tabela___reject_truncate BEFORE TRUNCATE ON __tabela__
  FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation();
```

> `TRUNCATE` não está escrito na RN-09, que fala só de `UPDATE` e `DELETE`. Entra porque é um
> `DELETE` em massa que as triggers de linha não pegam. Se for preciso, vira emenda da spec.

**`ensureIdempotency` no template padrão também**: sem isso, todo módulo gerado nasce reprovado
pelo hook da RN-13. O import aponta para `@shared/infra/http/middlewares/ensureIdempotency`, que
ainda não existe. Isso não pesa na 001, que não compila nada (RN-10), e a spec 002 registra quem cria
o middleware (2.8.8).

**`--self-test static`** (RN-10, CA-09) — novo modo, sem workspace, sem toolchain e sem prettier:
- `Generator` aceita um `ws` alternativo; o self-test estático gera em `tempfile.mkdtemp()`, e o
  `finally` apaga.
- Gera 4 variações: backend padrão com `--enum`, backend `--no-table`, backend `--append-only` e
  frontend com `--filho` + `--constants`. Além delas, `migration create` e `migration alter` em
  `--dry-run`.
- Invariantes comuns a todas: nenhum placeholder fora de `BLOCK_MARKERS`, nenhum nome de arquivo
  com `__`, diretivas balanceadas.
- Invariantes do append-only: (a) exatamente os 17 destinos esperados sem `--enum` (o padrão gera 22); (b) nenhuma
  ocorrência de `save(`, `.update(`, `.delete(`, `user_updated`, `updated_at`, `UpdateDateColumn`
  no código gerado (código **sem comentário** — AG-013); (c) a migration contém `reject_mutation`,
  `BEFORE UPDATE OR DELETE` e `BEFORE TRUNCATE`; (d) a rota tem exatamente 3 registros (`get`,
  `get`, `post`); (e) 4 arquivos `*.spec.ts`; (f) o controller tem 3 métodos públicos; (g) **os 4
  hooks financeiros, rodados sobre o módulo gerado sob o caminho virtual
  `backend/api/src/modules/ledger/zz_items/`, não acusam nada**. A (g) prova que o gerador e os hooks
  concordam.
- `--self-test` sem argumento continua sendo o completo (backend + frontend com toolchain); sem
  workspace ele já sai com "toolchain ausente". O estático é `--self-test static`.

#### 2.8.4 Hooks financeiros

**Biblioteca** `.claude/hooks/financial_rules.py`, com constantes e funções puras
`(caminho_virtual, texto) -> list[(linha, mensagem)]`. Cada uma decide **sozinha** se o caminho
está no escopo dela, para que o teste por fixture cubra também a regra de escopo. Comentário é
removido com o `strip_comments_keep_lines` do `scaffold.py` (AG-013), salvo quando a regra lê o
marcador — **e salvo a RN-14 inteira**, que lê o texto cru: segredo comentado é segredo vazado, e
a spec (RN-14) não abre exceção para comentário. *(Correção de 24/10/2026, achado ALTA da 1ª
auditoria: esta frase dizia "toda regra" e contradizia a spec; pela hierarquia de fontes, vence a
spec.)*

```python
FINANCIAL_CONTEXTS = {"ledger", "accounts", "charges", "payouts", "splits", "btg", "platforms"}
APPEND_ONLY_MODULES = {"ledger/*", "audit/*", "btg/btg_events", "splits/split_executions"}
```

**Pontos de entrada** em `.claude/hooks/`, um por regra (CA-10): `money-bigint.py`,
`ledger-immutable.py`, `idempotency-required.py` e `no-secret-in-code.py`. Interface igual à do
`jest-mock-factory.py`: `<arquivo> [--as <caminho-virtual>]` imprime os achados e sai com 1 se
houver algum; `--self-test` roda as fixtures de `.claude/scripts/tests/<nome-do-hook>/`. São
chamados pelo `post-edit-check.sh` para todo `.ts` de workspace, cada achado vira um `ERRORS` com o
código da regra, e o hook pós-edição sai com 2, como as regras que ele já roda. O `settings.json`
não muda.

> §4 do `05` chama o segundo hook de `ledger-immutable.sh`. Aqui ele é `.py`, porque precisa do
> autômato de comentário e da biblioteca comum. Em shell, a regra seria um terceiro filtro de
> comentário, que é o defeito que a 087 removeu.

| Hook | Escopo | Reprova |
|---|---|---|
| `money-bigint` (RN-11) | **entity**: `backend/api/src/modules/<ctx>/**/entities/*.ts` com `ctx ∈ FINANCIAL_CONTEXTS`. **migration**: `backend/api/src/shared/infra/typeorm/migrations/*.ts`, cujo contexto é resolvido pelo `@Entity('<tabela>')` correspondente em `src/modules/*/`. **Tabela sem entity → tratada como financeira** (falha fechada). **demais**: `.ts` de `modules/<ctx financeiro>/` | tipo `numeric`, `decimal`, `float`, `float4`, `float8`, `double precision`, `real` ou `money` em `type:` / `@Column(...)` / SQL cru; coluna `*_cents` com tipo diferente de `bigint`; `parseFloat(` e `.toFixed(` |
| `ledger-immutable` (RN-12) | `.ts` de `backend/api/src/modules/<m>/` com `m ∈ APPEND_ONLY_MODULES`, exceto `tests/*.spec.ts` | `.save(`, `.update(`, `.delete(`, `.remove(`, `.softDelete(`, `.softRemove(`, `.restore(`, `.upsert(`, `.increment(`, `.decrement(`; `UPDATE `, `DELETE FROM` ou `TRUNCATE` dentro de string |
| `idempotency-required` (RN-13, RN-15) | `backend/api/src/**/*.routes.ts` | chamada `.post(`, `.put(` ou `.patch(` cujo span (do parêntese de abertura ao de fechamento, com string respeitada) não contém `ensureIdempotency`, quando não há `<router>.use(ensureIdempotency)` antes dela no arquivo **e** não há marcador válido |
| `no-secret-in-code` (RN-14) | `src/**/*.{ts,tsx}` de **qualquer** workspace do `workspaces.json` | `-----BEGIN … PRIVATE KEY-----`; `AKIA[0-9A-Z]{16}`; JWT literal (`eyJ….….…`); literal de string com 16 ou mais caracteres sem espaço atribuído a nome que casa `secret`, `password`, `passwd`, `api_?key`, `token`, `private_?key`, `client_?secret` ou `hmac` |

**Marcador de isenção** (RN-15), lido no **texto cru**, na linha imediatamente acima da chamada
`.post/.put/.patch` ou dentro do span dela:

```ts
// idempotency-exempt: webhook do BTG — deduplicado por event_id (RN-REG-02)
```

Motivo válido = 10 ou mais caracteres não brancos depois dos dois-pontos. `idempotency-exempt` sem
motivo, ou com motivo curto, é **reprovado** e não vale como isenção (CA-11).

**Segredo em teste** (RN-14): o teste monta o valor em tempo de execução, com
`crypto.randomBytes(32).toString('hex')` ou `'s'.repeat(32)`. Os dois não são literais com 16 ou mais
caracteres, e o hook não tem marcador de isenção. A skill registra isso na seção "Regras
financeiras".

#### 2.8.5 `verify.sh harness` — o comando único (RN-16)

Etapas, cada uma um `step` do mecanismo que já existe (status por etapa na evidência):

1. `bash -n` em todo `.claude/**/*.sh`
2. `python3 -m py_compile` em todo `.claude/**/*.py`
3. `scaffold.py --list-placeholders`
4. `scaffold.py --self-test static`
5. `check-module.py --self-test` (com os casos novos de 2.8.6)
6. `--self-test` de cada hook que o tem: `jest-mock-factory.py`, `block-shell-write-ts.py` e os 4
   financeiros
7. `workspaces.py --self-test`: o JSON é válido, os leitores Bash e Python dão a mesma resposta
   para os 4 caminhos, e nenhum arquivo executável de `.claude/` cita caminho de workspace fora do
   JSON (essa é a guarda permanente do CA-06)

**Evidência**: `.claude/gate/<feature>.harness.json`, mesmo formato e mesma regra de acumulação
(`rc` = o pior) dos workspaces. O hash cobre `git diff` + untracked de `.claude/`, `CLAUDE.md`,
`documentacao/` e `.gitignore`, **excluindo** `.claude/gate/`, `.claude/projects/` e
`.claude/settings.local.json` (sem a exclusão, gravar a evidência mudaria o próprio hash).
`diff_hash` passa a receber a lista de caminhos por variável em vez do `src` fixo.

**Raiz sem commit**: hoje `git rev-parse HEAD` falha na raiz. Quando a base é `HEAD` e não há
nenhum commit, a base passa a ser a árvore vazia (`git hash-object -t tree /dev/null`) e o resumo
diz isso. Sem isso, o gate da 001 só rodaria depois do commit inicial, que é a última coisa da
spec.

`/finish-task` e `verifier.md` passam a aceitar `--check-evidence <feature> harness`, e o
`/sprint-close` inclui `harness` no `--full`.

#### 2.8.6 Skill `backend-module` e `check-module.py` (RN-17, RN-18)

**Skill**: a seção nova **"Regras financeiras"** fica entre "Decisões" e "Regras por camada". Ela
cobre: dinheiro em `bigint` com nome `*_cents`; proporções inteiras com a unidade definida na spec
da feature; perfil `--append-only` e quais módulos o exigem; inserção explícita, sem `save()`, com
transação no repositório (BE-017/018); `ensureIdempotency` e o marcador de isenção; HMAC na
API máquina-a-máquina e nos webhooks (a forma concreta é a spec 002); segredos montados em tempo de
execução nos testes. Toda regra mecânica cita o hook que a verifica, sem repetir a lista de padrões.
A linha "Tipos" de "Regras por camada" troca `decimal→numeric(precision,scale)` por
`dinheiro→bigint (centavos, *_cents) — numeric/float proibidos em contexto financeiro`. A
**representação em TypeScript** do `bigint` (string, `bigint` ou transformer) fica marcada como
decisão da spec 003, porque o driver `pg` devolve `bigint` como `string` e isso afeta o contrato de
API.

**`check-module.py`** ganha o check `financeiro` (sempre que a pasta está num contexto financeiro):
- roda as 4 funções de `financial_rules` sobre os arquivos do módulo; achado = ALTA;
- módulo em `APPEND_ONLY_MODULES`: a completude é medida com `flags["append_only"] = True`. Ter
  service/teste de Update ou Delete é ALTA (`completude-append-only`), e a migration da tabela sem
  `reject_mutation` também é ALTA.
- self-test: `.claude/scripts/tests/check-module-financeiro/` com um módulo de exemplo **violador**
  (`numeric` na entity, `save(` no repositório, `POST` sem `ensureIdempotency`, service de Update)
  e a versão **corrigida**. O esperado é `acusa` e `limpo`, respectivamente (CA-12).

`verifier-checks/financeiro.md` (etiqueta nova em `diff-classify.py`, acesa por diff que toca
contexto financeiro ou contém `idempotency-exempt`): o verifier lista cada isenção do diff, julga
se o motivo procede e confere que o `--append-only` foi usado onde a lista manda.

#### 2.8.7 Documentos

**`CLAUDE.md` raiz** — mesmo esqueleto de seções do atual (o harness, a hierarquia de fontes e o
fluxo SDD são processo e ficam). O que muda:

| Seção | Conteúdo novo |
|---|---|
| Visão Geral | Plataforma de pagamentos sobre BaaS do BTG, modelo 2 (`documentacao/03`); tabela dos 4 workspaces com porta, público, tecnologia e **Estado** |
| Navegação Rápida | Árvore com `backend/api`, `frontend/operador`, `frontend/cliente` e `tools/btg-simulator` marcados como planejados; `.claude/workspaces.json` |
| O Harness | Igual, mais o alvo `verify.sh harness` e os 4 hooks financeiros |
| Hierarquia de Fontes | Nível 4 = `CLAUDE.md` do workspace, **que nasce com o workspace**; até lá, o nível 4 está vazio |
| Regras Críticas | As 7 de hoje, com os caminhos novos, e mais 8 (BIGINT centavos), 9 (ledger append-only) e 10 (`Idempotency-Key` em toda escrita) |
| Módulos | Tabela de `04` §4: contexto, módulos, perfil de scaffold, **Estado** (`planejado — spec NNN`) |
| Providers | `CryptoProvider`, `MailProvider` e `StorageProvider` herdados como **planejado — nasce com o `backend/api`**; `GetPostalCodeProvider` sai (não há uso previsto no MVP) |
| Lições | Igual, mais a nota de origem |
| Documentação de contexto | Índice `documentacao/00`–`06` no lugar dos documentos do doador |

A verificação do CA-01 é por `grep -niE "clínica|clinica|doador|donor|tentante|especialista|backend/admin|frontend/admin|portal|professional"`
no arquivo, que tem de sair vazio. O CA-02 é por um script de 10 linhas, nas tasks, que extrai as
linhas `planejado — spec NNN` e confere que a pasta da spec existe ou que a spec está na sequência
de `05` §5.

**`HARNESS.md`** — reescrito com: (1) cabeçalho e nota de origem
(`rszaneti/harness_vidafertil` @ `0c878b7`, roteiro F0–F7 e histórico até v2.3-F7 legíveis lá);
(2) "Dívidas vigentes", que traz as três dívidas da F7 que continuam no código e marca a terceira
("`verify.sh` não alcança o harness") como **parcialmente fechada** pelo alvo `harness`; (3)
histórico com a primeira linha `23/10/2026 · v1.0-clone · spec 001`.

**`lessons/README.md`** — o título deixa de dizer "ERP Vida Fertil" e ganha a seção **"Origem"**,
com a nota da RN-06 e a tabela `backend/admin → backend/api`, `frontend/admin → frontend/operador`
e `frontend/portal`/`frontend/professional` → sem correspondente (os públicos eram outros).

#### 2.8.8 Specs 002 e 003 em rascunho (RN-19)

Ambas usam o `_templates/spec.md`, com status `rascunho`, só o `spec.md` e "Questões em aberto"
preenchidas — e por isso **não aprováveis** até o `/spec-new` delas rodar com o usuário.

- **002-auth-jwks-httponly**: objetivo e RN a partir de `04` §2 (linhas Autenticação, API máquina-a-máquina
  e Segredos) e §3. Questões em aberto: (1) é a 002 que cria o `backend/api` e, portanto, carrega
  o `--self-test` completo do perfil append-only (RN-10)? (2) quem cria o middleware
  `ensureIdempotency`, que todo módulo gerado importa (2.8.3)? (3) hooks `[hook]` de `04` §2 que
  ficaram fora da 001 (Joi sem `unknown(true)`).
- **003-ledger-core**: objetivo a partir de `04` §2 (linha Ledger) e §5; RN-REG-01/02 de `03` §4;
  as **8 invariantes como CA `[auto]`**, uma por CA, com o texto de `04` §5. Questão em aberto: a
  representação em TypeScript do `bigint` (2.8.6).

### 2.9 Verificação dos critérios de aceite

| CA | Verificação prevista |
|---|---|
| CA-01 | `grep` da 2.8.7 sobre `CLAUDE.md`: saída vazia; `grep` das 3 regras novas: 3 linhas |
| CA-02 | script da 2.8.7 nas tasks + `verifier` |
| CA-03 | `ls documentacao/` comparado com os links do `00-README.md` + `HARNESS.md` |
| CA-04 | `[humano]` |
| CA-05 | `sha256sum` de `backend.md`/`frontend.md`/`agents.md` antes e depois (registrado na 1ª task); `grep` da seção "Origem" |
| CA-06 | `verify.sh harness` etapa 7 + `grep -rn` dos 4 caminhos sobre `.claude/**/*.{py,sh,json}` (exceto `gate/`, `_backup_*`): vazio |
| CA-07 | `verify.sh all` sem workspaces: exit 0 e 4 linhas `⚠️ … não existe neste checkout` |
| CA-08 | `grep -rn` dos 4 caminhos sobre `.claude/**/*.md` excluindo `lessons/` e `specs/a_fazer/001-*`: vazio (AG-017: procurar o texto **velho**) |
| CA-09 | `verify.sh harness` etapas 3 e 4 |
| CA-10 | `verify.sh harness` etapa 6; cada hook com ao menos um `-acusa` e um `-limpo` |
| CA-11 | fixtures `idempotency-required/patch-sem-middleware-acusa.routes.ts`, `isencao-com-motivo-limpo.routes.ts`, `isencao-sem-motivo-acusa.routes.ts` |
| CA-12 | `verify.sh harness` etapa 5 |
| CA-13 | `[humano]` (+ `grep "decimal→numeric"` vazio na skill) |
| CA-14 | `ls` das duas pastas (só `spec.md`); `grep -c "^- \[ \] \[CA-" 003/spec.md` ≥ 8 com `[auto]`; `grep` da questão na 002 |
| CA-15 | `ls .claude/specs/*/` e `ls -a .claude/gate/` |
| CA-16, CA-17 | `[humano]` |

## 3. Frontend

### 3.1 Onde aparece na UI

Não se aplica — feature sem tela.

### 3.2 Campos do formulário

Não se aplica.

### 3.3 Comportamento

Não se aplica.

### 3.4 Telas

Não se aplica — feature sem tela; `ui-planner` não despachado.

### 3.5 Arquivos a criar/alterar

**Criar**: `.claude/workspaces.json`, `.claude/scripts/workspaces.py`,
`.claude/hooks/financial_rules.py`, os 4 hooks, `.claude/scripts/tests/{money-bigint,ledger-immutable,idempotency-required,no-secret-in-code,check-module-financeiro}/`,
`.claude/verifier-checks/financeiro.md`, `.claude/specs/a_fazer/{002,003}-*/spec.md`.

**Alterar**: `scaffold.py` e 10 templates backend (`entity`, `migration`, `repository-interface`,
`repository`, `controller`, `routes` e os 4 `test-*` de Create/Show/List/ListTotal), `verify.sh`, `post-edit-check.sh`, `block-shell-write-ts.py`, `check-module.py`,
`diff-classify.py`, `check-ui-v2-refs.py`, a prosa da 2.8.1, `skills/backend-module/SKILL.md`,
`lessons/README.md`, `commands/finish-task.md`, `commands/sprint-close.md`, `agents/verifier.md`,
`CLAUDE.md`, `documentacao/HARNESS.md`, `documentacao/00-README.md` e `.gitignore`.

**Remover**: `.claude/gate/*.json` (65), `documentacao/Roteiro-MVP-Plataforma-de-Pagamentos-BTG-BaaS.md`,
`documentacao/Ui_Ux/`, `documentacao/HARNESS.md:Zone.Identifier`.

## 4. Riscos e pontos de atenção

- **O gate não lê o que esta feature muda** — `.py`, `.sh` e `.md` passam pelo hook pós-edição sem
  nenhuma checagem (ele só olha `.ts/.tsx` e plans). Até a etapa de 2.8.5 existir, a prova é manual
  (`bash -n`, `py_compile`, `--self-test`). Por isso o `verify.sh harness` é a **primeira** coisa a
  ficar de pé nas tasks, logo depois do `workspaces.json`. Lessons: AG-019, AG-025, e a pergunta 4
  do `verifier-checks/harness.md`.
- **Detector validado só no caso do autor** (AG-020; os 4 ALTA da 087). Cada hook precisa de
  fixture no **idioma dominante** do template real: o `routes.ts.tpl` usa `xRouter.post(\n  '/',\n
  accessControl(...),\n  celebrate({...}),\n  controller.create,\n)`, em várias linhas, com
  `celebrate` aninhado. A fixture que passa numa linha só não prova nada. A invariante (g) do
  self-test estático (hooks sobre o módulo gerado) é a amostra real que existe hoje.
- **Comentário que adverte dispara a regra** (AG-013/AG-018). A skill e os templates vão **citar**
  `save(`, `numeric` e `idempotency-exempt` em comentário. As regras 11–13 rodam sobre código sem
  comentário, exceto a leitura do marcador; a **RN-14 roda sobre o texto cru** (ver 2.8.4 — um
  aviso legítimo não contém uma chave de verdade).
- **Falso positivo do `ledger-immutable` em `.delete(` de `Map`/`Set`** e do `money-bigint` em
  `.toFixed(` usado só para log. Os dois são aceitos: em módulo de ledger, o custo de reescrever
  uma linha é menor que o de uma regra com exceção. Se a medição no primeiro módulo real mostrar
  ruído, vira lesson.
- **Trigger x migration de alter com backfill**: depois da trigger, um `UPDATE` de backfill numa
  tabela append-only é rejeitado pelo banco. `ADD COLUMN … DEFAULT` não dispara trigger de linha
  (Postgres 11+). Fica registrado na skill (seção "Regras financeiras") como "backfill em tabela
  append-only não existe; coluna nova nasce `nullable` ou com `default`". O BE-022 continua valendo.
- **`ensureIdempotency` importado e inexistente**: todo módulo gerado depois da 001 deixa de
  compilar até alguém criar o middleware. É intencional (falha alta e cedo), e a questão está
  registrada na 002.
- **`save()` com `manager`** (BE-017): o repositório append-only não usa `save`. A inserção é por
  query builder com `returning('*')`, e o teste do Create precisa mockar a cadeia do query builder.
  Isso fica para o self-test completo da spec que criar o `backend/api`.
- **Remoção conferida pelo texto novo** (AG-017): CA-06 e CA-08 procuram os caminhos **velhos**, nunca
  os novos.
- **Hook de plan (BE-007)**: o `post-edit-check.sh` reprova `plan.md`/`tasks.md` com nome de função
  de geração de uuid do Postgres fora de uma linha que cite BE-007. Este plan não cita nenhuma; as
  tasks não podem citar.
- **Segredo sintético nas fixtures** do `no-secret-in-code`: as fixtures vão para o git do harness.
  Usar só valores públicos de exemplo (`AKIAIOSFODNN7EXAMPLE`, chave PEM truncada e marcada
  `EXAMPLE`), para não disparar o secret scanning do GitHub nem treinar alguém a ignorá-lo.
- **Commit inicial** (RN-21): `git add` de 400+ arquivos de `.claude/`. Antes de commitar, conferir
  com `git status --short -uall` que `gate/*.json`, `settings.local.json`, `projects/` e
  `_backup_*` estão fora, conforme o `.gitignore`.
