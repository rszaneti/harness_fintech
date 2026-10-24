// DTO – contrato de entrada para criação de __Entity__
export default interface ICreate__Entity__DTO {
  // __CAMPOS__ — espelhar a entity (sem id, sem updated/created_at). Exemplo declarado:
  // contracts_id: string
  // description?: string | null
  name: string
  user_created: string | null
}
