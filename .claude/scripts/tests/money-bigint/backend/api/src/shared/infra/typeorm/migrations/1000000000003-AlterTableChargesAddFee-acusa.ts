import { MigrationInterface, QueryRunner } from 'typeorm'

export class AlterTableChargesAddFee1000000000003 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE charges ADD COLUMN IF NOT EXISTS fee numeric(10,2)`) // @acusa
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE charges DROP COLUMN IF EXISTS fee`)
  }
}
