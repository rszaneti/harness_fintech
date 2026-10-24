import { MigrationInterface, QueryRunner, Table } from 'typeorm'

// Cada tipo fracionário que a RN-11 nomeia, um por linha (achado MÉDIA da 1ª auditoria: sem
// fixture, uma regressão em qualquer um deles passava verde).
export class CreateTablePayoutFees1000000000006 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'payout_fees',
        columns: [
          { name: 'id', type: 'uuid', isPrimary: true },
          { name: 'a', type: 'float' }, // @acusa
          { name: 'b', type: 'float4' }, // @acusa
          { name: 'c', type: 'float8' }, // @acusa
          { name: 'd', type: 'double precision' }, // @acusa
          { name: 'e', type: 'real' }, // @acusa
          { name: 'f', type: 'money' }, // @acusa
          { name: 'g_cents', type: 'int8' },
        ],
      }),
    )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('payout_fees')
  }
}
