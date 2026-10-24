// Service – remoção de __Entity__(s) por ID(s)
import { injectable, inject } from 'tsyringe'

import I__Entity__Repository from '../repositories/I__Entity__Repository'

interface IRequest {
  __registro_id__: string[]
}

@injectable()
class Delete__Entity__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute({ __registro_id__ }: IRequest): Promise<void> {
    await this.__entity__Repository.delete(__registro_id__)
  }
}

export default Delete__Entity__Service
