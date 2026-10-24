import { MigrationInterface, QueryRunner, Table } from 'typeorm'

export class CreateTablePayouts1000000000001 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'payouts',
        columns: [
          { name: 'id', type: 'uuid', isPrimary: true },
          { name: 'amount', type: 'decimal', precision: 12, scale: 2 }, // @acusa
        ],
      }),
    )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('payouts')
  }
}
