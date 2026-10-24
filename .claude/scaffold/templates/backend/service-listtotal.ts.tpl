// Service – contagem total de __Entities__ para paginação
import { injectable, inject } from 'tsyringe'

import I__Entity__Repository from '../repositories/I__Entity__Repository'
import IFind__Entity__DTO from '../dtos/IFind__Entity__DTO'

type IRequest = Omit<IFind__Entity__DTO, 'sort_field' | 'sort_order' | 'page' | 'rowsperpage'>

@injectable()
class ListTotal__Entities__Service {
  constructor(
    @inject('__Entity__Repository')
    private __entity__Repository: I__Entity__Repository,
  ) {}

  public async execute(data: IRequest): Promise<number> {
    return this.__entity__Repository.findTotal(data)
  }
}

export default ListTotal__Entities__Service
