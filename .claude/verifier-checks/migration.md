# check `migration` — schema mudou [BE-022, BE-007, AG-024]

> Acende quando o diff toca `typeorm/migrations/` ou `typeorm/entities/`.
> `migration:run` é **sequencial**: uma migration que estoure ao reprocessar trava a fila para
> TODAS as features seguintes, não só para a sua (foi assim que a 049 parou a 032).

## BE-022 — guarda de existência POR OPERAÇÃO

| Operação | Guarda |
|---|---|
| `addColumn` | `await queryRunner.hasColumn(tabela, coluna)` |
| `createForeignKey` | `table.foreignKeys.some((f) => f.name === '<nome>')` |
| `createIndex` | `table.indices.some((i) => i.name === '<nome>')` |
| SQL cru | `IF NOT EXISTS` |
| seed (`INSERT`) | `WHERE NOT EXISTS` + casts explícitos (`$1::uuid`) |
| `down` | a mesma guarda, invertida, na ordem inversa (índice → FK → coluna) |

⚠️ **`return` no topo NÃO conta.** Com a coluna presente mas FK/índice ausentes (reprocessamento
parcial), a migration termina "com sucesso" e deixa o schema incompleto **em silêncio**.

⚠️ FK e índice sempre **nomeados**: sem nome não há como guardar nem derrubar.

⚠️ Timestamp que colidiu com migration **já aplicada**: deixe como está. O TypeORM rastreia pelo
nome da classe; renumerar faz o ORM tratá-la como nova e aplicá-la de novo.

## BE-007 — PK uuid

Sem `default` e sem `generationStrategy`. O id vem do `uuidv4()` da **aplicação**, no `create` do
repositório. Nem `uuid_generate_v4()`, nem `gen_random_uuid()` — esta última **não existe** neste
PostgreSQL. O hook bloqueia, mas confira o backfill e o seed, que passam por SQL cru.

## AG-024 — renomeação em lote atropelou identificador que não é do domínio

O grep do AG-002 procura o nome do MOLDE; aqui o defeito é o nome do molde ter **sumido de onde
devia ficar**. Faça o grep **inverso**: procure o nome NOVO onde ele não deveria aparecer. O caso a
auditar sempre: **`@Entity('X')` cujo `X` não é a tabela que a migration da feature cria**.

⚠️ Não use "nome da pasta do módulo" como critério: 31% das entities divergem legitimamente
(entity-filha mora na pasta do pai) e 17% são tabelas legadas sem migration.

**Veredito**: operação sem guarda, `return` no topo, PK com default de banco, ou `@Entity` × tabela
divergente = bloqueante.
