import { MigrationInterface, QueryRunner, Table } from 'typeorm'

// Tabela sem entity = tratada como financeira (falha fechada). Aqui ela cumpre a regra.
export class CreateTableSplitRules1000000000004 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'split_rules',
        columns: [
          { name: 'id', type: 'uuid', isPrimary: true },
          {
            name: 'fee_cents',
            type: 'bigint',
          },
          { name: 'percent_bps', type: 'int4' },
        ],
      }),
    )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('split_rules')
  }
}
