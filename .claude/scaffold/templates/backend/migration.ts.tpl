// Migration – cria tabela __tabela__
// Com FK: acrescentar `TableForeignKey` ao import (fora daqui o ESLint acusa import sem uso).
import { MigrationInterface, QueryRunner, Table } from 'typeorm'

export class CreateTable__Entities____timestamp__ implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: '__tabela__',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            // [BE-007] SEM 'default' de geracao no banco. O id vem do uuidv4() da
            // APLICACAO, no create do repositorio. Nenhuma funcao do Postgres entra
            // aqui: nem uuid_generate_v4(), nem gen_random_uuid() -- esta ultima nao
            // existe neste banco e travou a fila de migrations na spec 049.
          },
          // __CAMPOS__ — colunas do domínio (espelham a entity). Exemplo declarado:
          // FK exemplo:
          // {
          //   name: '<fks>_id',
          //   type: 'uuid',
          // },
          {
            name: 'name',
            type: 'varchar',
            length: '255',
          },
          {
            name: 'status',
            type: 'bool',
            default: true,
          },
          {
            name: 'user_created',
            type: 'varchar',
            length: '255',
            isNullable: true,
          },
// @if !append_only
          {
            name: 'user_updated',
            type: 'varchar',
            length: '255',
            isNullable: true,
          },
// @endif
          {
            name: 'created_at',
            type: 'timestamp',
            default: 'now()',
          },
// @if !append_only
          {
            name: 'updated_at',
            type: 'timestamp',
            default: 'now()',
          },
// @endif
        ],
      }),
    )
// @if append_only

    // Append-only (spec 001, RN-09): o BANCO rejeita UPDATE, DELETE e TRUNCATE nesta tabela — o
    // hook `ledger-immutable` cobre o código; a trigger cobre o resto (psql, script, outro serviço).
    // `reject_mutation()` é COMPARTILHADA entre as tabelas append-only: CREATE OR REPLACE aqui, e o
    // `down` não a remove. Backfill (UPDATE) nesta tabela não existe: coluna nova nasce nullable
    // ou com default (ADD COLUMN ... DEFAULT não dispara trigger de linha no Postgres 11+).
    await queryRunner.query(`
      CREATE OR REPLACE FUNCTION reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        RAISE EXCEPTION 'tabela % é append-only: % rejeitado', TG_TABLE_NAME, TG_OP;
      END;
      $$
    `)
    await queryRunner.query(
      `CREATE TRIGGER __tabela___reject_mutation BEFORE UPDATE OR DELETE ON __tabela__ FOR EACH ROW EXECUTE FUNCTION reject_mutation()`,
    )
    await queryRunner.query(
      `CREATE TRIGGER __tabela___reject_truncate BEFORE TRUNCATE ON __tabela__ FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation()`,
    )
// @endif

    // __FKS__ — uma chamada por FK. onDelete: CASCADE | SET NULL | RESTRICT conforme regra.
// @if append_only
    // ⚠️ Append-only: FK com onDelete RESTRICT. CASCADE apagaria o registro imutável junto com o
    // pai — e a trigger `reject_mutation()` recusaria, travando a exclusão do pai com erro obscuro.
// @endif
    // Se a tabela referenciada ainda não existir (outro programador), criar a FK normalmente
    // e documentar a dependência com comentário [BE-006].
    // await queryRunner.createForeignKey(
    //   '__tabela__',
    //   new TableForeignKey({
    //     columnNames: ['<fks>_id'],
    //     referencedTableName: '<fks>',
    //     referencedColumnNames: ['id'],
// @if !append_only
    //     onDelete: 'CASCADE',
    //     onUpdate: 'CASCADE',
// @endif
// @if append_only
    //     onDelete: 'RESTRICT',
    //     onUpdate: 'RESTRICT',
// @endif
    //   }),
    // )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('__tabela__')
  }
}
