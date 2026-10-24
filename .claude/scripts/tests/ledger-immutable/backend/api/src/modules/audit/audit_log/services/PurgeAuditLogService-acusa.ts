import { EntityManager } from 'typeorm'

export default class PurgeAuditLogService {
  public async execute(manager: EntityManager): Promise<void> {
    await manager.query(`DELETE FROM audit_log WHERE created_at < now() - interval '1 year'`) // @acusa
  }
}
