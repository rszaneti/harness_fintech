---
name: backend-module
description: Conhecimento de construção de módulo DDD no backend — regras por camada, nomenclatura, guarda de migration e as decisões que o scaffold não toma por você. O módulo é GERADO por `.claude/scaffold/scaffold.py backend`; esta skill diz o que preencher e por quê. Usar ao criar ou auditar módulo backend na plataforma de pagamentos (comando /new-backend-module).
---

# Skill: backend-module

Scaffold de módulo DDD no backend (`backend/api/`). **Regra central: NUNCA gerar arquivo de
estrutura do zero nem copiar de outro módulo — rodar o scaffold, que copia os templates de
`.claude/scaffold/templates/backend/`, e preencher só os marcadores de bloco.** Gerar do zero erra;
gerar e preencher não.

```bash
python3 .claude/scaffold/scaffold.py backend <contexto> <modulo> <Entity> [--enum <Tipo>] [--timestamp <ms>] [--no-table] [--sem-migration] [--append-only]
```

## Placeholders (spec 085 — o script deriva; você não substitui nada à mão)

Exemplo: contexto=`contracts`, modulo=`annexes`, Entity=`ContractAnnex`

| Placeholder | Significado | Exemplo |
|-------------|-------------|---------|
| `__Entity__` | Entity singular PascalCase (argumento) | `ContractAnnex` |
| `__Entities__` | Plural PascalCase (`--plural` sobrescreve) | `ContractAnnexes` |
| `__entity__` | Alias QueryBuilder: minúsculas sem underscore, singular | `contractannex` |
| `__entities__` | Chave de resposta de lista (plural minúsculas) | `contractannexes` |
| `__contexto__` / `__modulo__` | Pastas (argumentos) | `contracts` / `annexes` |
| `__tabela__` | Tabela: snake_case do plural (`--tabela` sobrescreve) | `contract_annexes` |
| `__registro_id__` | `__tabela__` + `_id` — id no body/DTO de update | `contract_annexes_id` |
| `__endpoint__` | kebab de `__tabela__` (`--endpoint` sobrescreve) | `contract-annexes` |
| `__permissao__` | = `__tabela__`; sufixos `_view/_create/_update/_delete` já estão no template | `contract_annexes` |
| `__timestamp__` | `--timestamp` ou agora (ms) | `1781092290836` |
| `__Mudanca__` / `__coluna__` / `__tabela_referenciada__` | só `migration alter` | `AddFiscalCode` / `fiscal_code` / `customers` |

**Marcadores de bloco — lista fechada, ficam no arquivo gerado para você preencher** (sempre em
linha de comentário, com um exemplo **declarado** logo abaixo que compila): `__CAMPOS__ __FILTROS__
__WHERES__ __FKS__ __VALORES__ __REGRAS__ __ATRIBUICOES__ __TESTES_DE_ERRO__ __IMPORTS_RELACIONAMENTOS__`.
Qualquer outro `__X__` num template faz o script falhar (exit 2) — é o que impede placeholder
não documentado. O módulo gerado com os blocos ainda vazios **compila, passa lint e testes**
(`--self-test`); o exemplo `name`/`status` é para multiplicar e ajustar, não para deixar.

## Pré-requisitos — perguntar ANTES de gerar qualquer arquivo

1. **Campos da entidade**: nome, tipo TS, tipo TypeORM, nullable? (auditoria é automática — não perguntar)
2. **Relacionamentos**: FKs (`ManyToOne` com qual Entity? nullable? onDelete?)
3. **Workflow?** (estados/transições — se sim, services e rotas PATCH adicionais)
4. **Upload de arquivos?** (módulo de files separado?)
5. **Permissões**: **módulo novo = `<tabela>_view/create/update/delete`** (`_update`, como o
   template gera e como os módulos gerados desde junho estão seedados); **módulo legado = o sufixo
   que as rotas dele já usam** (`_edit` em 77 módulos) — nunca inventar; copiar do `accessControl`
   existente (decisão da spec 085, RN-10)
6. **Regras de negócio**: unicidade? criptografia (CryptoProvider)? cálculos?

> Se a feature tem `plan.md` (SDD), TODAS essas respostas já estão lá — usar o plan, não perguntar de novo.

## Ordem de geração (template → destino) — é o que o scaffold produz

A tabela de destinos vive **no script** (`BACKEND_DEST` em `.claude/scaffold/scaffold.py`); esta
cópia é referência de leitura e de auditoria (AG-009: `find` do módulo tem de bater com ela).
Templates em `.claude/scaffold/templates/backend/`.

| # | Template | Destino em `backend/api/src/` |
|---|----------|--------------------------------|
| 1 | `migration.ts.tpl` | `shared/infra/typeorm/migrations/__timestamp__-CreateTable__Entities__.ts` |
| 1b | `migration-alter.ts.tpl` *(só `migration alter`)* | `shared/infra/typeorm/migrations/__timestamp__-AlterTable__Entities____Mudanca__.ts` |
| 2 | `enum.ts.tpl` *(só `--enum <Tipo>`)* | `modules/__contexto__/__modulo__/enums/__Entity__<Tipo>.ts` |
| 3 | `entity.ts.tpl` | `modules/__contexto__/__modulo__/infra/typeorm/entities/__Entity__.ts` |
| 4 | `dto-create.ts.tpl` / `dto-update.ts.tpl` / `dto-find.ts.tpl` | `modules/__contexto__/__modulo__/dtos/` |
| 5 | `repository-interface.ts.tpl` | `modules/__contexto__/__modulo__/repositories/I__Entity__Repository.ts` |
| 6 | `repository.ts.tpl` | `modules/__contexto__/__modulo__/infra/typeorm/repositories/__Entity__Repository.ts` |
| 7 | `providers-index.ts.tpl` | `modules/__contexto__/__modulo__/providers/index.ts` |
| 8 | `service-*.ts.tpl` (6) | `modules/__contexto__/__modulo__/services/` |
| 9 | `controller.ts.tpl` | `modules/__contexto__/__modulo__/infra/http/controllers/__Entities__Controller.ts` |
| 10 | `routes.ts.tpl` | `modules/__contexto__/__modulo__/infra/http/routes/__entities__.routes.ts` |
| 11 | `test-*.spec.ts.tpl` (6) | `modules/__contexto__/__modulo__/tests/` |

> ⚠️ **Módulo SEM tabela** (`--no-table`). Esta ordem pressupõe módulo com entity, migration,
> controller e rotas. Existe um segundo formato legítimo: o módulo que só publica uma **abstração
> compartilhada** — contrato + implementação + testes, sem entity, sem migration e sem HTTP.
> Nesse caso valem os passos **4, 5, 6, 7, 8 e 11** — DTOs, interface do contrato, implementação
> em `infra/typeorm/repositories/`, providers, services e testes —, pulando **1, 2, 3, 9 e 10**
> (migration, enum, entity, controller e rotas); o repositório gerado referencia a entity e precisa
> ser adaptado à mão. Precedente: `donors/donors_exams_rounds` (spec 056),
> que resolve a rodada da fase de exames sem tabela própria — a rodada é materializada noutro
> módulo (spec 038) ou derivada do histórico, e criar tabela exigiria fabricar rodada retroativa
> para todo dado já existente.
>
> Registrado em 2026-08-20 porque a auditoria da 056 apontou a **lacuna**: sem este parágrafo,
> cada auditor decide de novo se módulo entity-less está fora do padrão ou é caso previsto.

## Decisões — o que o scaffold NÃO decide por você

O template dá a forma; estas são as escolhas que erram calado e já erraram. Cada uma traz o código
da lesson (o detalhe está em `.claude/lessons/backend.md`).

| Situação | Decisão |
|---|---|
| **Enum que espelha outro** (mesmo conceito, recorte diferente) — BE-015 | Escrever **função de travessia explícita** entre os dois e usá-la em TODOS os pontos de cruzamento, inclusive no backfill da migration. Testar o valor que **diverge**: testar só o que coincide não prova nada. Na fronteira os dois são `string`, então typecheck e lint não pegam |
| **Operação que toca duas tabelas** — BE-017/BE-018 | A transação vive no **repositório**, com `manager` opcional. `AppDataSource.transaction` dentro do service torna o módulo inteiro intestável. E o `create` do TypeORM **não persiste** — quem persiste é o `save` |
| **Service de lote** — AG-010 | Responder **objeto com metadados** (`{ created, updated, errors }`), nunca array cru: quem consome precisa distinguir "nada a fazer" de "tudo falhou" |
| **Campo sensível** (senha, api_key, documento) — BE-010 | `CryptoProvider` no Create **e** no Update. No Update, só re-criptografar se veio preenchido: `if (x !== undefined && x !== '')` |
| **Filtro booleano na query string** — BE-016 | `Joi.boolean()` no `Segments.QUERY` entrega **boolean** ao controller. Comparar com `'true'` inverte o filtro em silêncio |
| **`leftJoinAndSelect` de entity com `@Exclude()`** — BE-021 | O controller tem de responder com `classToClass`, senão o dado sensível vaza pelo join |
| **Ordenar por expressão SQL** — BE-031 | `orderBy` com expressão quebra em query paginada com join: usar `addSelect` + alias |
| **`take`/`skip` com `orderBy` em coluna de relação `OneToMany`** — BE-020 | Some com registros. Ordenar por coluna da própria entidade, ou paginar em duas etapas |
| **Onde colocar a guarda de uma regra** — BE-028 | Guarda na camada errada é regra que não existe. Se a regra vale para todo caminho de escrita, ela é do service — não do controller nem da tela |
| **Rota de upload** — BE-024 | `celebrate` **depois** do `multer`, senão a rota devolve 400 sempre (o body ainda não foi parseado quando o Joi roda) |
| **Rota pública / webhook** — BE-003 | Registrar **antes** do `ensureAuthenticated` em `routes/index.ts`. Rota de caminho literal vem antes de `/:param` do mesmo verbo — o Express casa na ordem (BE-014, o hook pega dentro do arquivo) |
| **Pediram um stub de entity** — BE-004 | Stub é stub: entity + migration, e só. Gerar o módulo completo cria services que ninguém chamou e rotas que ninguém registrou |
| **FK para tabela que ainda não existe** — BE-006 | Criar a FK normalmente e **documentar a dependência** no comentário da migration |
| **Relação nova num agregado** — AG-023 ("relação nova só no repositório do dono") | Acrescentar em **todo** repositório que lê aquele agregado por outra porta, não só no dono. O que não for atualizado devolve o objeto sem a relação, e a tela mostra vazio |
| **Corrigindo um defeito** — AG-011 | Três perguntas: o estado que a correção trata é **alcançável** pelo fluxo que gerou o bug? Quem **escreve** o dado que a correção lê, e a UI percorre esse caminho? Se a correção fosse revertida, **qual asserção falharia**? Se a resposta for "nenhuma", o teste acompanha a correção sem prová-la |

## Regras financeiras (spec 001) — o que muda num sistema que move dinheiro

> As regras mecânicas abaixo **não são repetidas aqui**: moram em `.claude/hooks/financial_rules.py`
> e reprovam no hook pós-edição e no `check-module.py`. Esta seção diz **o que fazer**; o hook diz
> se foi feito. Contextos financeiros, módulos append-only e os padrões de cada regra: no próprio
> `financial_rules.py`.

| Situação | Decisão | Quem verifica |
|---|---|---|
| **Coluna de dinheiro** | `bigint` em **centavos**, nome com sufixo **`_cents`** (`amount_cents`, `fee_cents`). Nunca `numeric`, `decimal`, `float`, `real` nem `money`, e nunca `parseFloat`/`toFixed` para fazer conta — aritmética de dinheiro é inteira; formatar é do frontend | hook `money-bigint` (RN-11) |
| **Proporção** (taxa, percentual de split) | Inteiro numa unidade que a spec da feature declara (ex.: pontos-base, `*_bps`). Decimal flutuante, nunca | hook `money-bigint` (RN-11) |
| **Representação em TypeScript do `bigint`** | **Decisão da spec 003** (o driver `pg` devolve `bigint` como `string`, e isso afeta o contrato de API). Até lá, não inventar: seguir o que a 003 aprovar | spec 003 |
| **Registro que é fato consumado** (lançamento, evento recebido, execução de ordem, auditoria) | Gerar com **`--append-only`**: só Create/Show/List/ListTotal, entity sem campos de atualização, repositório que **insere** com `createQueryBuilder().insert()` (nunca `save()`), migration com a trigger `reject_mutation()`. Estorno é **lançamento novo** com referência ao original. Módulo novo desse tipo entra em `APPEND_ONLY_MODULES` na mesma feature | scaffold (recusa sem a flag), hook `ledger-immutable` (RN-12), `check-module.py` (RN-09), trigger no banco |
| **Coluna nova em tabela append-only** | Nasce `nullable` ou com `default` — `ADD COLUMN … DEFAULT` não dispara a trigger de linha (Postgres 11+). **Backfill por `UPDATE` não existe** nessas tabelas; a guarda de existência da BE-022 continua valendo | trigger no banco |
| **Lançamento que toca duas contas** | Partidas dobradas na **mesma transação**, aberta no **repositório** com `manager` opcional (BE-017/018); `SELECT … FOR UPDATE` na conta antes de lançar | `verifier` (check `financeiro`) + testes de invariante da spec 003 |
| **Rota de escrita** (`POST`/`PUT`/`PATCH`) | `ensureIdempotency` na cadeia da rota (o template já traz). Isenção só para quem deduplica por outro meio (webhook do BTG por `event_id`; login/refresh), com `// idempotency-exempt: <motivo>` na linha de cima — o motivo é obrigatório e o `verifier` julga cada um | hook `idempotency-required` (RN-13/RN-15) + `verifier` |
| **Chamada máquina-a-máquina e webhook** | Assinatura **HMAC-SHA256** do corpo + timestamp (janela de 5 min), validada **antes** de qualquer parse. A forma concreta (headers, rotação de chave) é da spec 002 | spec 002 |
| **Segredo** (chave, token, senha, certificado) | Vem do cofre/env, nunca de literal no código. Em **teste**, montar o valor em tempo de execução: `randomBytes(32).toString('hex')` ou `'s'.repeat(32)` — o hook não tem marcador de isenção | hook `no-secret-in-code` (RN-14) |

## Regras por camada (resumo — detalhe está nos comentários dos templates)

- **Migration (create)**: PK uuid **sem `default` de geração no banco** — o id vem do `uuidv4()` da
  aplicação, no `create` do repository. Nem `uuid_generate_v4()`, nem `gen_random_uuid()`
  (BE-007, o hook bloqueia; `gen_random_uuid()` não existe neste PostgreSQL).
  FK: `CASCADE` (filho não existe sem pai) | `SET NULL` (opcional, coluna nullable) | `RESTRICT` (bloquear exclusão do pai).
  Tipos: string→`varchar` 255, texto longo→`text`, int→`int4`, **dinheiro→`bigint` (centavos, `*_cents`) —
  `numeric`/`float` proibidos em contexto financeiro** (ver "Regras financeiras"), bool→`bool`, Date→`timestamp`, FK→`uuid`.
- **Migration (alter)**: `migration-alter.ts.tpl`, e **guarda de existência por operação**
  (BE-022 — o hook bloqueia). Coluna nova em tabela com dados é `isNullable` ou traz `default`.
  Ver a seção "Migration de ALTER" abaixo.
- **Entity**: sem lógica de negócio; auditoria obrigatória; campos sensíveis com `@Exclude()`;
  relacionamento em camelCase sem underscore; tabela plural snake_case; FK column `<plural>_id`.
- **Repository**: sempre `createQueryBuilder` (nunca `find()`/`findOne()`); `ILIKE` para texto;
  `leftJoinAndSelect` explícito (nunca `eager: true`); `create` com `id: uuidv4()`; `delete` direto via `this.ormRepository.delete(ids)`
  (**não** existe util `auditDelete`, apesar do que diz a documentação — BE-023).
- **Services**: `@injectable()` + `@inject('Token')`; só importar `AppError` se houver `throw new AppError` (BE-001 — hook verifica);
  campos sensíveis criptografados com `CryptoProvider` no Create E no Update (BE-010).
- **Controller**: exatamente 5 métodos (index, show, create, update, delete) — **3** no perfil
  `--append-only` (index, show, create); `user_created`/`user_updated`
  via `ShowUserService`; resposta lista `{ __entities__: [...], __entities__total: N }`; delete `204`.
- **Routes**: Joi inline; `ensureAuthenticated` + `accessControl`; `ensureIdempotency` em `POST`/`PUT`/`PATCH`
  (RN-13); show é `GET /show/:id`; delete via query `id` (array);
  webhooks públicos registrados ANTES de `ensureAuthenticated` em `routes/index.ts` (BE-003).
- **Testes**: `jest.fn()` para todos os métodos do repository; NUNCA importar a Entity; caminho feliz + erros.
  Mock com **cara de dado real** mascara o defeito que o teste deveria pegar (AG-015): o mock existe
  para isolar, não para parecer produção.

## Tratamento de erros e restrições gerais

Absorvido do `BACKEND-ARCHITECTURE.md` §14/§15 (removido na spec 086) e conferido contra o código.

- **Erro de negócio / validação manual**: `throw new AppError('Mensagem em pt-BR.', statusCode)`.
  Erro de payload é do `celebrate`, não seu.
- **Códigos**: `400` regra violada ou dado inválido · `401` não autenticado/autorizado · `404`
  recurso inexistente (400 com mensagem específica também é aceito no padrão atual).
- **Um verbo, um service.** Não duplicar service; não pôr lógica de negócio no controller; não
  acessar TypeORM fora do repositório.
- **Sem `any`** fora de mock de teste.
- **Todo arquivo abre com um comentário de cabeçalho** dizendo a responsabilidade dele — os
  templates já vêm assim.
- Variáveis de ambiente: a fonte é `backend/api/.env.example`, **não** documentação.

## Migration — criar e RODAR (não é checklist manual)

1. Escolher o timestamp pelo **estado do banco**: `yarn migration:show` e pegar acima da última
   aplicada. `ls` da pasta não basta — mostra pendentes de outras frentes e esconde o que já rodou.
2. Gerar pelo scaffold (não usar `migration:create`): o `backend` já cria a de `createTable`;
   tabela existente → `python3 .claude/scaffold/scaffold.py migration alter <Tabela> --mudanca <X> --timestamp <ms>`.
   Tabela que já tem `CreateTable<Tabela>` no repositório → o script recusa `create` (exit 4).
3. `cd backend/api && yarn migration:run` — se falhar, corrigir e rodar de novo até aplicar.
4. Confirmar com `yarn migration:show`.

## Migration de ALTER — guarda de existência é obrigatória [BE-022]

**O `migration.ts.tpl` cobre só `createTable`.** Enquanto foi o único template, toda migration de
alter nasceu improvisada e sem guarda: em 2026-08-20, **27 dos 41 arquivos `AlterTable*` com
`addColumn` no repositório não tinham nenhuma**. Daí o `migration-alter.ts.tpl`.

Por que importa: `migration:run` é **sequencial**. Uma migration de alter que estoure ao
reprocessar (coluna/FK/índice que já existe) **trava a fila para todas as features seguintes**,
não só para a sua. Foi exatamente assim que, no ERP de origem, a spec 049 parou a spec 032.

| Operação | Guarda |
|----------|--------|
| `addColumn` | `await queryRunner.hasColumn(tabela, coluna)` |
| `createForeignKey` | `table.foreignKeys.some((f) => f.name === '<nome>')` |
| `createIndex` | `table.indices.some((i) => i.name === '<nome>')` |
| índice parcial / unique condicional (SQL cru) | `CREATE UNIQUE INDEX IF NOT EXISTS` |
| `dropIndex` / `dropForeignKey` / `dropColumn` no `down` | a mesma guarda, invertida |
| backfill (`UPDATE`) | `WHERE <coluna> IS NULL` — nunca `UPDATE` incondicional |
| `INSERT` de seed | `WHERE NOT EXISTS` + casts explícitos (`$1::uuid`, `$2::varchar`) |

⚠️ **A guarda é POR OPERAÇÃO — `return` no topo não conta.** O atalho
`if (table?.findColumnByName('x')) return` existe em migrations deste repositório e é armadilha:
com a coluna presente mas a FK/índice ausentes (reprocessamento parcial), a migration termina "com
sucesso" e deixa o schema incompleto em silêncio. O hook rejeita esse padrão. Referência correta:
`1785948040584-AlterTableStorageStockPatientLink.ts`.

⚠️ **FK e índice sempre NOMEADOS** (`name:` explícito). Sem nome não há como guardar a criação nem
derrubar no `down`.

⚠️ **Colisão de timestamp com migration JÁ APLICADA: deixe como está.** O TypeORM rastreia pelo
**nome da classe**, não pelo arquivo — renumerar faz o ORM ver uma migration nova e aplicá-la de
novo (BE-022, regra 1). Renumerar só é permitido enquanto a migration não rodou em lugar nenhum.

## Checklist manual pós-geração (informar ao desenvolvedor)

1. Registrar rota em `src/shared/infra/http/routes/index.ts`:
   `routes.use('/__endpoint__', __entities__Router)`
2. Importar provider em `src/shared/container/index.ts`: `import '@modules/__contexto__/__modulo__/providers'`
   ⚠️ É o `index.ts` do container, NÃO `container/providers/index.ts` — este último registra só os
   providers COMPARTILHADOS (Crypto, Mail, Storage…). A instrução errada esteve aqui até 2026-08-25,
   quando a auditoria da spec 071 a pegou.
3. Permissões na tabela `permissions`: `__permissao___view/create/update/delete` + associação em `usergroups_permissions`
4. `cd backend/api && yarn lint:fix` (erro de lockfile → `yarn install` antes — BE-005)

## Verificação final obrigatória

1. `find src/modules/__contexto__/__modulo__ -type f | sort` — todos os arquivos criados (AG-009)
2. `yarn test src/modules/__contexto__/__modulo__` ✅
3. Gate: `bash .claude/scripts/verify.sh backend src/modules/__contexto__/__modulo__ --feature <feature>`

## Referência de nomenclatura rápida

| Item | Padrão | Exemplo |
|------|--------|---------|
| Entity (classe) | Singular PascalCase | `ContractAnnex` |
| Tabela DB | Plural snake_case | `contract_annexes` |
| FK column | Plural snake_case + `_id` | `contracts_id` |
| Repository | `I<Entity>Repository` / `<Entity>Repository` | — |
| Service | `<Verbo><Entity>Service` | `CreateContractAnnexService` |
| Controller | `<Entidades>Controller` (plural) | `ContractAnnexesController` |
| Permissão | `<modulo>_<acao>` | `contract_annexes_view` |
| Alias QueryBuilder | camelCase sem underscore | `contractannex` |
