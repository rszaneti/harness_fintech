export default class UpdateSplitExecutionService {
  constructor(private repository: { update(id: string, data: object): Promise<void> }) {}

  public async execute(id: string): Promise<void> {
    await this.repository.update(id, { status: 'done' }) // @acusa
  }
}
