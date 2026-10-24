# Comando: /new-migration

Cria uma migration TypeORM com nome e estrutura corretos, **pelo scaffold** — nunca de cabeça,
nunca por `migration:create` (gera esqueleto vazio, fora do padrão).

## Uso

```
/new-migration create <Tabela>                       → CreateTable<Tabela>
/new-migration alter  <Tabela> <Mudanca> [coluna]    → AlterTable<Tabela><Mudanca>
```

**Exemplos:**
- `/new-migration create ContractAnnexes`
- `/new-migration alter Customers AddFiscalCode fiscal_code`

## Execução

1. Escolher o timestamp pelo **estado do banco**: `cd backend/api && yarn migration:show` e pegar
   acima da última aplicada. `ls` da pasta não basta — mostra pendentes de outras frentes e não
   diz o que já rodou.
2. Gerar:
   ```bash
   python3 .claude/scaffold/scaffold.py migration create <Tabela> --timestamp <ms>
   python3 .claude/scaffold/scaffold.py migration alter  <Tabela> --mudanca <Mudanca> [--coluna <c>] [--ref <tabela_referenciada>] --timestamp <ms>
   ```
   O script copia `.claude/scaffold/templates/backend/migration.ts.tpl` ou `migration-alter.ts.tpl`,
   substitui os placeholders de identidade, formata com o Prettier e lista os **marcadores de bloco**
   (colunas, FKs — a lista fechada está em `.claude/scaffold/README.md`) que ficaram para preencher,
   com `arquivo:linha`.
   `create` para tabela que já tem `CreateTable<Tabela>` no repositório → **exit 4** (use `alter`).
3. Preencher os blocos com Edit/Write (o hook pós-edição valida BE-007 e BE-022 a cada salvamento).
4. `cd backend/api && yarn migration:run` — se falhar, corrigir e rodar até aplicar.
5. Confirmar com `yarn migration:show`.

## Regras críticas (o template já as encarna — estão aqui para o julgamento)

- Uma tabela por arquivo de migration. Tabelas no **plural snake_case**.
- FKs criadas **separadas** da tabela (não inline em `columns`), com `onDelete` explícito
  (`SET NULL`, `CASCADE` ou `RESTRICT`) e **nome** (`name:` explícito — sem nome não há como
  guardar nem derrubar).
- `created_at` e `updated_at` com `default: now()`.
- O `down()` reverte **completamente** o `up()` — com as mesmas guardas, na ordem inversa
  (índice → FK → coluna).
- **[BE-007]** PK uuid sem `default` e sem `generationStrategy` — o id vem do `uuidv4()` da
  aplicação. O hook pós-edição bloqueia.
- **[BE-022]** Guarda de existência **por operação**, nunca `return` no topo: `addColumn` →
  `hasColumn`; `createForeignKey` → `table.foreignKeys.some((f) => f.name === …)`; `createIndex` →
  `table.indices.some((i) => i.name === …)`; SQL cru → `IF NOT EXISTS`; seed → `WHERE NOT EXISTS` com
  casts explícitos (`$1::uuid`). `migration:run` é sequencial: uma que estoure ao reprocessar trava
  a fila para todas as features seguintes (foi assim que a 049 parou a 032).
- **[BE-022]** Timestamp colidiu com migration **já aplicada**? Deixe como está. O TypeORM rastreia
  pelo nome da classe; renumerar faz o ORM tentar aplicá-la de novo.
- Coluna nova em tabela com dados é `isNullable` ou traz `default`.
