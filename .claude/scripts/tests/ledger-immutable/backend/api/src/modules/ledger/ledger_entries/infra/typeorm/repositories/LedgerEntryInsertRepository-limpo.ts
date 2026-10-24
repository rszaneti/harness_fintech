import { EntityManager, Repository } from 'typeorm'
import { v4 as uuidv4 } from 'uuid'
import LedgerEntry from '../entities/LedgerEntry'

// Append-only: sem save(), sem update(), sem delete() — inserção explícita (AG-013: o comentário
// cita o que é proibido e não acusa).
class LedgerEntryInsertRepository {
  private ormRepository: Repository<LedgerEntry>

  public async create(data: Partial<LedgerEntry>, manager?: EntityManager): Promise<LedgerEntry> {
    const qb = manager
      ? manager.createQueryBuilder()
      : this.ormRepository.createQueryBuilder()
    const result = await qb
      .insert()
      .into(LedgerEntry)
      .values({ id: uuidv4(), ...data })
      .returning('*')
      .execute()
    return result.generatedMaps[0] as LedgerEntry
  }
}

export default LedgerEntryInsertRepository
