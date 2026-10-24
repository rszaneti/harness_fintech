// src/types/__modulos__.types.ts
//
// Espelho do contrato de API do backend (§ Contrato de API do plan.md). Regras: sem `any`;
// datas como string (formatação no componente, com date-fns); opcional como `campo: string | null`.
// [AG-022] Tipo do frontend é AFIRMAÇÃO sobre a resposta, não verificação: ao mudar um DTO no
// backend, abrir este arquivo na mesma passada.

export interface I__Modulo__ {
  id: string
  // __CAMPOS__ — um por campo do DTO do backend. Exemplo declarado (multiplicar e ajustar):
  name: string
  status: boolean
  user_created: string | null
  user_updated: string | null
  created_at: string
  updated_at: string
}
// @if filho

export interface I__ModuloFilho__ {
  id: string
  __registro_id__: string
  // __CAMPOS_FILHO__ — campos do filho. Exemplo declarado:
  name: string
  user_created: string | null
  user_updated: string | null
  created_at: string
  updated_at: string
}
// @endif
