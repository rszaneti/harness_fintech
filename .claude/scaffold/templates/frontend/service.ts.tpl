// src/services/__modulos__.service.ts
//
// Chaves de resposta seguem o backend: lista `{ __modulos__: [...], __modulos__total: N }`,
// item `{ __modulo__: {...} }` (§ Contrato de API do plan.md). Delete envia `id` por query string
// (array), como toda rota gerada pelo scaffold.

import api from './api'
// @if filho
import { I__Modulo__, I__ModuloFilho__ } from '../types/__modulos__.types'
// @endif
// @if !filho
import { I__Modulo__ } from '../types/__modulos__.types'
// @endif

// ---- __Modulo__ ----
interface IFetch__Modulos__Response {
  __modulos__: I__Modulo__[]
  __modulos__total: number
}

interface IFetch__Modulo__Response {
  __modulo__: I__Modulo__
}

export async function fetch__Modulos__(
  params: object,
): Promise<IFetch__Modulos__Response> {
  const { data } = await api.get<IFetch__Modulos__Response>('/__endpoint__', {
    params,
  })
  return data
}

export async function fetch__Modulo__ById(id: string): Promise<I__Modulo__> {
  const { data } = await api.get<IFetch__Modulo__Response>(
    `/__endpoint__/show/${id}`,
  )
  return data.__modulo__
}

export async function create__Modulo__(payload: object): Promise<I__Modulo__> {
  const { data } = await api.post<IFetch__Modulo__Response>('/__endpoint__', payload)
  return data.__modulo__
}

export async function update__Modulo__(payload: object): Promise<I__Modulo__> {
  const { data } = await api.put<IFetch__Modulo__Response>('/__endpoint__', payload)
  return data.__modulo__
}

export async function delete__Modulo__(id: string): Promise<void> {
  await api.delete('/__endpoint__', { params: { id: [id] } })
}
// @if filho

// ---- __ModuloFilho__ ----
interface IFetch__ModuloFilho__sResponse {
  __modulos____filhos__: I__ModuloFilho__[]
  __modulos____filhos__total: number
}

interface IFetch__ModuloFilho__Response {
  __modulo____filho__: I__ModuloFilho__
}

export async function fetch__Modulo____Filhos__(
  __modulo__Id: string,
): Promise<IFetch__ModuloFilho__sResponse> {
  const { data } = await api.get<IFetch__ModuloFilho__sResponse>(
    '/__endpoint__/__filho__',
    { params: { search___registro_id__: __modulo__Id } },
  )
  return data
}

export async function fetch__ModuloFilho__ById(
  id: string,
): Promise<I__ModuloFilho__> {
  const { data } = await api.get<IFetch__ModuloFilho__Response>(
    `/__endpoint__/__filho__/show/${id}`,
  )
  return data.__modulo____filho__
}

export async function create__ModuloFilho__(
  payload: object,
): Promise<I__ModuloFilho__> {
  const { data } = await api.post<IFetch__ModuloFilho__Response>(
    '/__endpoint__/__filho__',
    payload,
  )
  return data.__modulo____filho__
}

export async function update__ModuloFilho__(
  payload: object,
): Promise<I__ModuloFilho__> {
  const { data } = await api.put<IFetch__ModuloFilho__Response>(
    '/__endpoint__/__filho__',
    payload,
  )
  return data.__modulo____filho__
}

export async function delete__ModuloFilho__(id: string): Promise<void> {
  await api.delete('/__endpoint__/__filho__', { params: { id: [id] } })
}
// @endif
