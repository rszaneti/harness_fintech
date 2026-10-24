import { Repository } from 'typeorm'
import SplitRule from '../entities/SplitRule'

// `split_rules` NÃO é append-only (só `split_executions`) — save é legítimo aqui (escopo da RN-12).
class SplitRuleRepository {
  private ormRepository: Repository<SplitRule>

  public async save(reg: SplitRule): Promise<SplitRule> {
    return this.ormRepository.save(reg)
  }
}

export default SplitRuleRepository
