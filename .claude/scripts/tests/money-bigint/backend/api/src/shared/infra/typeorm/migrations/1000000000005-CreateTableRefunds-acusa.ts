import { MigrationInterface, QueryRunner, Table } from 'typeorm'

export class CreateTableRefunds1000000000005 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'refunds',
        columns: [
          { name: 'id', type: 'uuid', isPrimary: true },
          {
            name: 'amount_cents', // @acusa
            type: 'int4',
          },
        ],
      }),
    )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('refunds')
  }
}
