// src/constants/__Modulo__Type.ts
//
// ⚠️ Espelho do enum do backend (`@modules/__contexto__/…/enums/`): os valores crus têm de bater
// exatamente com o enum de lá, porque é ele que o Joi das rotas usa em `.valid(...)`. Aqui moram só
// os rótulos de tela, que o backend não guarda. Mesmo arranjo de `ClinicType.ts`.
//
// Sem opção "Não informado": ausência já é ausência, e um valor sentinela obrigaria todo
// consumidor a tratar dois "vazios" diferentes.

// __VALORES__ — um por valor do enum do backend. Exemplo declarado:
export type T__Modulo__Type = 'ATIVO' | 'INATIVO'

export const __MODULO___TYPES: T__Modulo__Type[] = ['ATIVO', 'INATIVO']

export const __MODULO___TYPE_LABELS: Record<T__Modulo__Type, string> = {
  ATIVO: 'Ativo',
  INATIVO: 'Inativo',
}
