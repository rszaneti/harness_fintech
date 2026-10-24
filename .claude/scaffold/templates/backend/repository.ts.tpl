// Repository – implementação TypeORM do I__Entity__Repository
// Regras: sempre createQueryBuilder (nunca find/findOne soltos); ILIKE para texto;
// leftJoinAndSelect explícito (nunca eager:true); create com id: uuidv4();
// @if !append_only
// delete direto via this.ormRepository.delete(ids) — NÃO existe util `auditDelete` [BE-023].
// @endif
// @if append_only
// Append-only: sem save, sem update, sem delete — só inserção (spec 001, RN-09).
// @endif
import { AppDataSource } from '@shared/infra/typeorm/dataSource'
// @if !append_only
import { Repository } from 'typeorm'
// @endif
// @if append_only
import { EntityManager, Repository } from 'typeorm'
// @endif
import { v4 as uuidv4 } from 'uuid'

import I__Entity__Repository from '@modules/__contexto__/__modulo__/repositories/I__Entity__Repository'
import ICreate__Entity__DTO from '@modules/__contexto__/__modulo__/dtos/ICreate__Entity__DTO'
import IFind__Entity__DTO from '@modules/__contexto__/__modulo__/dtos/IFind__Entity__DTO'
import __Entity__ from '../entities/__Entity__'

class __Entity__Repository implements I__Entity__Repository {
  private ormRepository: Repository<__Entity__>

  constructor() {
    this.ormRepository = AppDataSource.getRepository(__Entity__)
  }

  public async findAll({
    // __FILTROS__ — os mesmos do IFind DTO. Exemplo declarado:
    search_name,
    sort_field = 'name', // ← ajustar campo de ordenação padrão
    sort_order = 'ASC',
    page = 1,
    rowsperpage = 25,
  }: IFind__Entity__DTO): Promise<__Entity__[]> {
    const query = this.ormRepository.createQueryBuilder('__entity__')
    // .leftJoinAndSelect('__entity__.<relacao>', '<relacao>') // ← joins explícitos

    // __WHERES__ — um por filtro. Exemplo declarado (texto: ILIKE; boolean vindo da query
    // chega como STRING — comparar com 'true', BE-016):
    if (search_name) {
      query.andWhere('__entity__.name ILIKE :search_name', {
        search_name: `%${search_name}%`,
      })
    }

    query
      .orderBy(`__entity__.${sort_field}`, sort_order)
      .skip((page - 1) * rowsperpage)
      .take(rowsperpage)

    return query.getMany()
  }

  public async findTotal({
    // __FILTROS__ — os mesmos do findAll, sem paginação. Exemplo declarado:
    search_name,
  }: Omit<
    IFind__Entity__DTO,
    'sort_field' | 'sort_order' | 'page' | 'rowsperpage'
  >): Promise<number> {
    const query = this.ormRepository.createQueryBuilder('__entity__')

    // __WHERES__ — os mesmos do findAll:
    if (search_name) {
      query.andWhere('__entity__.name ILIKE :search_name', {
        search_name: `%${search_name}%`,
      })
    }

    return query.getCount()
  }

  public async findById(id: string): Promise<__Entity__ | null> {
    return this.ormRepository
      .createQueryBuilder('__entity__')
      .where('__entity__.id = :id', { id })
      .getOne()
  }

  public async findByIdRelations(id: string): Promise<__Entity__ | null> {
    return this.ormRepository
      .createQueryBuilder('__entity__')
      // .leftJoinAndSelect('__entity__.<relacao>', '<relacao>')
      .where('__entity__.id = :id', { id })
      .getOne()
  }

// @if !append_only
  public async create(data: ICreate__Entity__DTO): Promise<__Entity__> {
    const reg = this.ormRepository.create({
      id: uuidv4(), // ← obrigatório: o Postgres não gera o UUID pelo ORM
      ...data,
    })
    return this.ormRepository.save(reg)
  }

  public async save(reg: __Entity__): Promise<__Entity__> {
    return this.ormRepository.save(reg)
  }

  public async delete(ids: string[]): Promise<void> {
    await this.ormRepository.delete(ids) // ← [BE-023] padrão real; não existe `auditDelete`
  }
// @endif
// @if append_only
  // Append-only (spec 001, RN-09): inserção EXPLÍCITA, nunca save() — o hook `ledger-immutable`
  // reprova save()/update()/delete() neste módulo e a trigger `reject_mutation()` recusaria a
  // mutação no banco. Com `manager`, a inserção entra na transação de quem chamou (BE-017/018).
  public async create(
    data: ICreate__Entity__DTO,
    manager?: EntityManager,
  ): Promise<__Entity__> {
    const qb = manager
      ? manager.createQueryBuilder(__Entity__, '__entity__')
      : this.ormRepository.createQueryBuilder('__entity__')
    const result = await qb
      .insert()
      .into(__Entity__)
      .values({ id: uuidv4(), ...data }) // ← id da APLICAÇÃO (BE-007)
      .returning('*')
      .execute()
    return this.ormRepository.create(result.raw[0] as __Entity__)
  }
// @endif
}

export default __Entity__Repository
