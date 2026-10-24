// Service – regra de negócio para criação de __Entity__
// [BE-001] Só importar AppError se este arquivo contiver 'throw new AppError(...)'.
// [BE-010] Campo sensível (api_key, senha): injetar CryptoProvider e criptografar antes de salvar.
import { injectable, inject } from 'tsyringe'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import __Entity__ from '../infra/typeorm/entities/__Entity__'
import ICreate__Entity__DTO from '../dtos/ICreate__Entity__DTO'

@injectable()
class Create__Entity__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute(data: ICreate__Entity__DTO): Promise<__Entity__> {
    // __REGRAS__ — regras de negócio aqui (ex.: verificar unicidade → throw new AppError)
    const reg = await this.__entity__Repository.create(data)
    return reg
  }
}

export default Create__Entity__Service
