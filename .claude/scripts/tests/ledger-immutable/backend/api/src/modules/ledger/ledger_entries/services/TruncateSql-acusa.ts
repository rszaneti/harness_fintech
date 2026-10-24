export default async function limpar(manager: any): Promise<void> {
  await manager.query('truncate ledger_entries') // @acusa
  await manager.query('TRUNCATE TABLE ledger_entries CASCADE') // @acusa
}
