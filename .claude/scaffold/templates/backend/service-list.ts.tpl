// Service – lista __Entities__ com filtros e paginação
import { injectable, inject } from 'tsyringe'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import __Entity__ from '../infra/typeorm/entities/__Entity__'
import IFind__Entity__DTO from '../dtos/IFind__Entity__DTO'

@injectable()
class List__Entities__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute(data: IFind__Entity__DTO): Promise<__Entity__[]> {
    return this.__entity__Repository.findAll(data)
  }
}

export default List__Entities__Service
