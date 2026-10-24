// Cada forma de mutação que a RN-12 nomeia, uma por linha (achado MÉDIA da 1ª auditoria).
export default async function mutacoes(repo: any, qb: any, manager: any): Promise<void> {
  await repo.delete(['id']) // @acusa
  await repo.remove({}) // @acusa
  await repo.softDelete('id') // @acusa
  await repo.softRemove({}) // @acusa
  await repo.restore('id') // @acusa
  await repo.upsert({}, ['id']) // @acusa
  await repo.increment({}, 'amount_cents', 1) // @acusa
  await repo.decrement({}, 'amount_cents', 1) // @acusa
  await repo.clear() // @acusa
  await qb.insert().values({}).orUpdate(['amount_cents'], ['id']).execute() // @acusa
  await manager.query('update ledger_entries set amount_cents = 0') // @acusa
  await manager.query(`delete from ledger_entries`) // @acusa
}
