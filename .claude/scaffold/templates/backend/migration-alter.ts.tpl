// Migration – altera a tabela __tabela__ (__Mudanca__)
//
// ⚠️ POR QUE ESTE TEMPLATE EXISTE SEPARADO DO `migration.ts.tpl`: até 2026-08-20 a
// skill só tinha o template de `createTable`, e toda migration de ALTER nascia
// improvisada — sem a guarda de existência que a [BE-022] exige. Resultado
// medido na data: 27 dos 41 arquivos `AlterTable*` com `addColumn` estavam sem
// qualquer guarda. Não é preciosismo: `migration:run` é SEQUENCIAL, então uma
// única migration de alter que estoure ao reprocessar TRAVA A FILA INTEIRA para
// todas as features seguintes, não só para a sua.
//
// ⚠️ A GUARDA É POR OPERAÇÃO, NUNCA UM `return` NO TOPO. O atalho
//
//     if (table?.findColumnByName('x')) return   // ❌ NÃO COPIAR
//
// aparece em migrations deste repositório e é uma armadilha: se a coluna existir
// mas a FK ou o índice NÃO existirem (reprocessamento parcial, ambiente que
// recebeu a coluna por outro caminho), a migration termina "com sucesso" e o
// schema fica incompleto em silêncio. Cada `addColumn` / `createForeignKey` /
// `createIndex` carrega a SUA própria guarda. Referência correta no repositório:
// `1785948040584-AlterTableStorageStockPatientLink.ts`.
//
// ⚠️ O `down()` TAMBÉM É GUARDADO, e na ordem inversa: índice → FK → coluna.
// Derrubar índice/FK inexistente aborta o rollback no meio e deixa o banco num
// estado que nem o `up` nem o `down` reconhecem.
//
// ⚠️ TIMESTAMP: sempre ACIMA do maior já aplicado — conferir com
// `yarn migration:show` (o estado do BANCO), não com `ls` da pasta. Colidiu com
// uma migration que JÁ RODOU? Deixe como está. [BE-022] regra 1: o TypeORM
// rastreia pelo NOME DA CLASSE, e renumerar migration aplicada faz o ORM
// tratá-la como nova e tentar aplicá-la de novo.
//
// __CAMPOS__ — Documentar aqui o PORQUÊ desta alteração: RN da spec, motivo do
// `isNullable`, motivo do `onDelete` escolhido. O "o quê" o código abaixo já diz.

import {
  MigrationInterface,
  QueryRunner,
  TableColumn,
  TableForeignKey,
  TableIndex,
} from 'typeorm'

const TABLE = '__tabela__'

// Uma entrada por coluna adicionada. Tipos: string→varchar(255), texto longo→text,
// int→int4, decimal→numeric(precision,scale), bool→bool, Date→timestamp, FK→uuid.
const COLUMNS: TableColumn[] = [
  new TableColumn({
    name: '__coluna__',
    type: 'uuid',
    // ⚠️ Coluna adicionada em tabela COM DADOS é nullable, ou traz `default`.
    // NOT NULL sem default falha em toda linha já existente.
    isNullable: true,
  }),
]

// Uma entrada por FK. onDelete explícito e consciente:
// CASCADE (filho não existe sem o pai) | SET NULL (vínculo opcional; apaga
// rastreabilidade — não usar em material biológico/documento clínico) |
// RESTRICT (bloqueia a exclusão do pai).
const FOREIGN_KEYS = [
  {
    name: 'FK___tabela_____coluna__',
    column: '__coluna__',
    referencedTable: '__tabela_referenciada__',
    onDelete: 'RESTRICT',
  },
]

// Uma entrada por índice. Nomear sempre — índice anônimo não tem como ser
// guardado nem derrubado no `down`.
const INDICES = [
  {
    name: 'ix___tabela_____coluna__',
    columnNames: ['__coluna__'],
  },
]

export class AlterTable__Entities____Mudanca____timestamp__ implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // A tabela pode não existir no ambiente (migration anterior ainda não
    // aplicada). Sair em silêncio é melhor que travar a fila — [BE-006].
    const table = await queryRunner.getTable(TABLE)

    if (!table) return

    // [BE-022] Guarda por coluna.
    for (const column of COLUMNS) {
      const hasColumn = await queryRunner.hasColumn(TABLE, column.name)

      if (!hasColumn) {
        await queryRunner.addColumn(TABLE, column)
      }
    }

    // Reler a tabela: o snapshot acima é anterior às colunas recém-criadas.
    const current = await queryRunner.getTable(TABLE)

    // [BE-022] Guarda por FK.
    for (const fk of FOREIGN_KEYS) {
      const exists = current?.foreignKeys.some((f) => f.name === fk.name)

      if (!exists) {
        await queryRunner.createForeignKey(
          TABLE,
          new TableForeignKey({
            name: fk.name,
            columnNames: [fk.column],
            referencedTableName: fk.referencedTable,
            referencedColumnNames: ['id'],
            onDelete: fk.onDelete,
            onUpdate: 'CASCADE',
          }),
        )
      }
    }

    // [BE-022] Guarda por índice.
    for (const index of INDICES) {
      const exists = current?.indices.some((i) => i.name === index.name)

      if (!exists) {
        await queryRunner.createIndex(
          TABLE,
          new TableIndex({
            name: index.name,
            columnNames: index.columnNames,
          }),
        )
      }
    }

    // ÍNDICE PARCIAL / UNIQUE CONDICIONAL não existe na API do TableIndex —
    // vai por SQL cru, e aí a guarda é o próprio `IF NOT EXISTS`:
    // await queryRunner.query(
    //   `CREATE UNIQUE INDEX IF NOT EXISTS "uq___tabela_____coluna__"
    //      ON "__tabela__" ("__coluna__")
    //    WHERE "__coluna__" IS NOT NULL`,
    // )

    // BACKFILL de dado existente, quando houver — sempre idempotente
    // (`WHERE <coluna> IS NULL`), nunca um UPDATE incondicional:
    // await queryRunner.query(
    //   `UPDATE "__tabela__" SET "__coluna__" = $1 WHERE "__coluna__" IS NULL`,
    //   ['<valor>'],
    // )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    const table = await queryRunner.getTable(TABLE)

    if (!table) return

    // Ordem inversa do `up`: índice → FK → coluna.
    for (const index of INDICES) {
      const exists = table.indices.some((i) => i.name === index.name)

      if (exists) {
        await queryRunner.dropIndex(TABLE, index.name)
      }
    }

    // Índice parcial criado por SQL cru some por SQL cru:
    // await queryRunner.query(`DROP INDEX IF EXISTS "uq___tabela_____coluna__"`)

    for (const fk of FOREIGN_KEYS) {
      const exists = table.foreignKeys.find((f) => f.name === fk.name)

      if (exists) {
        await queryRunner.dropForeignKey(TABLE, exists)
      }
    }

    for (const column of COLUMNS) {
      const hasColumn = await queryRunner.hasColumn(TABLE, column.name)

      if (hasColumn) {
        await queryRunner.dropColumn(TABLE, column.name)
      }
    }
  }
}
