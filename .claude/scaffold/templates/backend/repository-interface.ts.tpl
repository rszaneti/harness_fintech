// Interface – contrato do repositório de __Entity__
// @if append_only
import { EntityManager } from 'typeorm'
// @endif
import __Entity__ from '../infra/typeorm/entities/__Entity__'
import ICreate__Entity__DTO from '../dtos/ICreate__Entity__DTO'
import IFind__Entity__DTO from '../dtos/IFind__Entity__DTO'

export default interface I__Entity__Repository {
  findAll(data: IFind__Entity__DTO): Promise<__Entity__[]>
  findTotal(
    data: Omit<
      IFind__Entity__DTO,
      'sort_field' | 'sort_order' | 'page' | 'rowsperpage'
    >,
  ): Promise<number>
  findById(id: string): Promise<__Entity__ | null>
  findByIdRelations(id: string): Promise<__Entity__ | null>
// @if !append_only
  create(data: ICreate__Entity__DTO): Promise<__Entity__>
  // `save` recebe a ENTITY já carregada e alterada pelo service (padrão de `IClinicRepository`),
  // não o DTO de update — o DTO carrega `__registro_id__`, que não é coluna.
  save(reg: __Entity__): Promise<__Entity__>
  delete(ids: string[]): Promise<void>
// @endif
// @if append_only
  // Append-only (spec 001, RN-09): sem save/delete — o registro não muda nem some. `manager`
  // opcional para inserir dentro da transação de quem chama (BE-017/018).
  create(data: ICreate__Entity__DTO, manager?: EntityManager): Promise<__Entity__>
// @endif
}
