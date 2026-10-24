// Service – busca um __Entity__ por ID com relações
import { injectable, inject } from 'tsyringe'
import AppError from '@shared/errors/AppError'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import __Entity__ from '../infra/typeorm/entities/__Entity__'

interface IRequest {
  __registro_id__: string
}

@injectable()
class Show__Entity__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute({ __registro_id__ }: IRequest): Promise<__Entity__> {
    const reg = await this.__entity__Repository.findByIdRelations(__registro_id__)

    if (!reg) {
      throw new AppError('Registro não encontrado.', 400)
    }

    return reg
  }
}

export default Show__Entity__Service
