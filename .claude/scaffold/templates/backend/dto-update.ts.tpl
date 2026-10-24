// DTO – contrato de entrada para atualização de __Entity__
export default interface IUpdate__Entity__DTO {
  __registro_id__: string
  // __CAMPOS__ — campos editáveis. Exemplo declarado:
  // description?: string | null
  name: string
  status?: boolean
  user_updated: string | null
}
