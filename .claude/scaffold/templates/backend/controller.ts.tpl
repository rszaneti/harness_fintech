// Controller – entrada HTTP para o módulo __Entity__
// @if !append_only
// Regras: exatamente 5 métodos (index, show, create, update, delete); sem lógica de negócio;
// user_created/user_updated preenchidos AQUI via ShowUserService.
// @endif
// @if append_only
// Regras (append-only, spec 001): exatamente 3 métodos (index, show, create) — o registro não muda
// nem some; sem lógica de negócio; user_created preenchido AQUI via ShowUserService.
// @endif
// Métodos adicionais → novo arquivo __Entity__<Servico>Controller.ts
import { Request, Response } from 'express'
import { container } from 'tsyringe'
import { classToClass } from 'class-transformer'

import Create__Entity__Service from '@modules/__contexto__/__modulo__/services/Create__Entity__Service'
// @if !append_only
import Update__Entity__Service from '@modules/__contexto__/__modulo__/services/Update__Entity__Service'
// @endif
import Show__Entity__Service from '@modules/__contexto__/__modulo__/services/Show__Entity__Service'
import List__Entities__Service from '@modules/__contexto__/__modulo__/services/List__Entities__Service'
import ListTotal__Entities__Service from '@modules/__contexto__/__modulo__/services/ListTotal__Entities__Service'
// @if !append_only
import Delete__Entity__Service from '@modules/__contexto__/__modulo__/services/Delete__Entity__Service'
// @endif

import ShowUserService from '@modules/users/users/services/ShowUserService'

type IRequestSearch = {
  // __FILTROS__ — os mesmos do IFind DTO. Exemplo declarado:
  search_name?: string
  sort_field: string
  sort_order: 'ASC' | 'DESC'
  page: string
  rowsperpage: string
}

// @if !append_only
type IRequestDelete = {
  id: string[]
}
// @endif

export default class __Entities__Controller {
  public async index(request: Request, response: Response): Promise<Response> {
    const {
      // __FILTROS__ — exemplo declarado:
      search_name,
      sort_field,
      sort_order = 'ASC',
      page = '1',
      rowsperpage = '25',
    } = request.query as IRequestSearch

    const list = container.resolve(List__Entities__Service)
    const listTotal = container.resolve(ListTotal__Entities__Service)

    const regs = await list.execute({
      // __FILTROS__
      search_name,
      sort_field,
      sort_order,
      page: Number(page),
      rowsperpage: Number(rowsperpage),
    })

    const totalReg = await listTotal.execute({
      // __FILTROS__
      search_name,
    })

    return response.json({
      __entities__: classToClass(regs),
      __entities__total: totalReg,
    })
  }

  public async show(request: Request, response: Response): Promise<Response> {
    const { id } = request.params

    const showService = container.resolve(Show__Entity__Service)
    const reg = await showService.execute({ __registro_id__: id })

    return response.json({ __entity__: classToClass(reg) })
  }

  public async create(request: Request, response: Response): Promise<Response> {
    // __CAMPOS__ — os mesmos do ICreate DTO / Joi da rota. Exemplo declarado:
    const { name } = request.body
    const users_id = request.user.id

    const createService = container.resolve(Create__Entity__Service)
    const showUser = container.resolve(ShowUserService)
    const user = await showUser.execute({ users_id })

    const reg = await createService.execute({
      // __CAMPOS__
      name,
      user_created: user.user_name,
    })

    return response.json({ __entity__: classToClass(reg) })
  }
// @if !append_only

  public async update(request: Request, response: Response): Promise<Response> {
    // __CAMPOS__ — os mesmos do IUpdate DTO / Joi da rota. Exemplo declarado:
    const { __registro_id__, name, status } = request.body
    const users_id = request.user.id

    const updateService = container.resolve(Update__Entity__Service)
    const showUser = container.resolve(ShowUserService)
    const user = await showUser.execute({ users_id })

    const reg = await updateService.execute({
      __registro_id__,
      // __CAMPOS__
      name,
      status,
      user_updated: user.user_name,
    })

    return response.json({ __entity__: classToClass(reg) })
  }

  public async delete(request: Request, response: Response): Promise<Response> {
    const { id } = request.query as IRequestDelete

    const deleteService = container.resolve(Delete__Entity__Service)
    await deleteService.execute({ __registro_id__: id })

    return response.status(204).json()
  }
// @endif
}
