// DTO – parâmetros de busca/filtragem de __Entity__
// Regras: filtros sempre com prefixo search_*; nomes fixos só para paginação/ordenação.
export default interface IFind__Entity__DTO {
  // __FILTROS__ — um por filtro. Exemplo declarado:
  // search_status?: string
  search_name?: string
  sort_field?: string
  sort_order?: 'ASC' | 'DESC'
  page?: number
  rowsperpage?: number
}
