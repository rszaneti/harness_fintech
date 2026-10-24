import { MigrationInterface, QueryRunner } from 'typeorm'

export class AlterTableChargesAddRates1000000000007 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE charges ADD COLUMN IF NOT EXISTS rate float4`) // @acusa
    await queryRunner.query(`ALTER TABLE charges ADD COLUMN IF NOT EXISTS rate2 float8`) // @acusa
    await queryRunner.query(`ALTER TABLE charges ADD COLUMN IF NOT EXISTS total_cents bigint`)
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE charges DROP COLUMN IF EXISTS rate`)
  }
}
