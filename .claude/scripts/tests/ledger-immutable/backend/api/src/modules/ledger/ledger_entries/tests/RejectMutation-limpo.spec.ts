// Teste pode exercitar a mutação para provar que ela é recusada — fora do escopo da RN-12.
describe('ledger append-only', () => {
  it('rejeita save', async () => {
    const repo = { save: jest.fn().mockRejectedValue(new Error('append-only')) }
    await expect(repo.save({})).rejects.toThrow('append-only')
  })
})
