import { Repository } from 'typeorm'
import LedgerEntry from '../entities/LedgerEntry'

class LedgerEntryRepository {
  private ormRepository: Repository<LedgerEntry>

  public async create(data: Partial<LedgerEntry>): Promise<LedgerEntry> {
    const reg = this.ormRepository.create(data)
    return this.ormRepository.save(reg) // @acusa
  }
}

export default LedgerEntryRepository
