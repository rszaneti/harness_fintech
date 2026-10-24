// Service – regra de negócio para atualização de __Entity__
import { injectable, inject } from 'tsyringe'
import AppError from '@shared/errors/AppError'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import __Entity__ from '../infra/typeorm/entities/__Entity__'
import IUpdate__Entity__DTO from '../dtos/IUpdate__Entity__DTO'

@injectable()
class Update__Entity__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute({
    __registro_id__,
    // __CAMPOS__ — os mesmos do IUpdate DTO. Exemplo declarado:
    name,
    status,
    user_updated,
  }: IUpdate__Entity__DTO): Promise<__Entity__> {
    const reg = await this.__entity__Repository.findById(__registro_id__)

    if (!reg) {
      throw new AppError('Registro não encontrado.', 400)
    }

    // __ATRIBUICOES__ — uma por campo editável. Exemplo declarado:
    // reg.description = description ?? reg.description
    // [BE-010] sensível: só re-criptografar se fornecido e não vazio:
    // if (api_key !== undefined && api_key !== '') reg.api_key = this.cryptoProvider.encrypt(api_key)
    reg.name = name
    reg.status = status ?? reg.status
    reg.user_updated = user_updated

    return this.__entity__Repository.save(reg)
  }
}

export default Update__Entity__Service
