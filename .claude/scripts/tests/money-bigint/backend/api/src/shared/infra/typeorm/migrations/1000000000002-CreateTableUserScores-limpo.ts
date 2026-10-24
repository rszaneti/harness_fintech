import { MigrationInterface, QueryRunner, Table } from 'typeorm'

// A tabela tem entity em `modules/users/` — contexto não financeiro, numeric permitido.
export class CreateTableUserScores1000000000002 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'user_scores',
        columns: [
          { name: 'id', type: 'uuid', isPrimary: true },
          { name: 'score', type: 'numeric', precision: 5, scale: 2 },
        ],
      }),
    )
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('user_scores')
  }
}
