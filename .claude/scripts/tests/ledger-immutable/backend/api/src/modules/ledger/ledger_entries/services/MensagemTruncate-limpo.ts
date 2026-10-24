import AppError from '@shared/errors/AppError'

export default function recusar(): never {
  throw new AppError('Lançamento é imutável: UPDATE, DELETE e TRUNCATE são rejeitados')
}

export const nota = 'truncate do texto acontece só na exibição'
