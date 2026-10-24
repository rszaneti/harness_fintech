// src/pages/__contexto__/__Modulos__List/index.tsx
//
// Listagem no padrão v2 (modelo: `pages/clinics/ClinicsList`). A casca vem do `global_v2`
// (containers, cartão, filtro) e os componentes MUI do `globalMaterialUi_v2`. Nada de estilo
// mora neste arquivo e a pasta não tem `styles.ts`.
//
// Paginação e ordenação SERVER-SIDE (FE-016): `rowCount` sozinho só desenha o rodapé; sem
// `paginationMode` e o par paginationModel/onPaginationModelChange a 2ª página é inalcançável.
// Métricas (`StatGrid`) e edição inline de coluna são de domínio: copiar do canônico se precisar.

import React, { useEffect, useState, useCallback, useContext } from 'react'
import { useHistory } from 'react-router-dom'
import { toast } from 'react-toastify'
import {
  GridActionsCellItem,
  GridColDef,
  GridSortModel,
} from '@mui/x-data-grid-pro'
import { Formik, Form } from 'formik'
import {
  MdEdit,
  MdDelete,
  MdAddCircle,
  MdSearch,
  MdClear,
} from 'react-icons/md'

// Context
import { ErrorContext } from '../../../context/ErrorContext'

// Services
import {
  fetch__Modulos__,
  delete__Modulo__,
} from '../../../services/__modulos__.service'

// Types
import { I__Modulo__ } from '../../../types/__modulos__.types'

// Constants
import { STATUS_BOOLEAN_OPTIONS } from '../../../constants/FilterStatus'

// Styles
import {
  ContainerList,
  ContentHeader,
  TitleH1,
  ListSurface,
  ListFilterBar,
  FilterGrid,
  FilterActions,
} from '../../../styles/global_v2'
import {
  CssAutocomplete,
  CssButton,
  CssDataGrid,
  CssTextField,
  ISelectOption,
} from '../../../styles/globalMaterialUi_v2'

interface IValuesForm {
  // __FILTROS__ — um `search_*` por campo de pesquisa, espelhando o Joi da rota (FE-025). Exemplo:
  search_name: string
  search_status: string
}

const EMPTY_FILTER: IValuesForm = {
  search_name: '',
  search_status: '',
}

const __Modulos__List: React.FC = () => {
  // Context
  const { ErrorMessage } = useContext(ErrorContext)
  const history = useHistory()

  // States
  const [__modulos__, set__Modulos__] = useState<I__Modulo__[]>([])
  const [__modulos__Total, set__Modulos__Total] = useState(0)
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  })
  const [sortModel, setSortModel] = useState<GridSortModel>([
    { field: 'name', sort: 'asc' },
  ])
  const [search, setSearch] = useState<IValuesForm>(EMPTY_FILTER)

  const columns: GridColDef[] = [
    {
      field: 'action',
      type: 'actions',
      headerName: 'AÇÕES',
      width: 100,
      cellClassName: 'actions',
      // Ícone sem cor: quem pinta é a tabela de tons da grade, pelo `className="action-*"`.
      getActions: ({ id }) => [
        <GridActionsCellItem
          key={`edit-${id}`}
          icon={<MdEdit size="18" />}
          title="EDITAR __MODULO_LABEL__"
          label="EDITAR __MODULO_LABEL__"
          showInMenu={false}
          className="action-edit"
          onClick={() => handleEdit(String(id))}
        />,
        <GridActionsCellItem
          key={`delete-${id}`}
          icon={<MdDelete size="18" />}
          title="DELETAR __MODULO_LABEL__"
          label="DELETAR __MODULO_LABEL__"
          showInMenu={false}
          className="action-delete"
          onClick={() => handleDelete(String(id))}
        />,
      ],
    },
    // __COLUNAS__ — uma por campo exibido. Exemplo declarado:
    {
      field: 'name',
      headerName: 'NOME',
      flex: 1,
      minWidth: 250,
    },
    {
      field: 'status',
      headerName: 'ATIVO',
      type: 'boolean',
      width: 120,
    },
  ]

  const load__Modulos__ = useCallback(async () => {
    try {
      const response = await fetch__Modulos__({
        // __FILTROS__ — os mesmos do IValuesForm:
        search_name: search.search_name,
        search_status: search.search_status || undefined,
        page: paginationModel.page + 1,
        rowsperpage: paginationModel.pageSize,
        sort_order: sortModel[0]?.sort === 'desc' ? 'DESC' : 'ASC',
        sort_field: sortModel[0]?.field ?? 'name',
      })

      set__Modulos__(response.__modulos__)
      set__Modulos__Total(response.__modulos__total)
    } catch (err) {
      ErrorMessage(err)
    }
  }, [ErrorMessage, search, paginationModel, sortModel])

  useEffect(() => {
    load__Modulos__()
  }, [load__Modulos__])

  const handleEdit = useCallback(
    (id: string) => {
      history.push(`/__modulo__/edit/${id}`)
    },
    [history],
  )

  const handleDelete = useCallback(
    async (id: string) => {
      const confirmed = window.confirm(
        'Deseja realmente deletar este registro?',
      )
      if (!confirmed) return

      try {
        await delete__Modulo__(id)

        toast.success('Registro deletado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })

        load__Modulos__()
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, load__Modulos__],
  )

  const handleSearch = useCallback((search_value: IValuesForm) => {
    // Volta à primeira página: filtrar estando na página 3 cairia numa faixa que o novo
    // resultado provavelmente não tem.
    setPaginationModel((prev) => ({ ...prev, page: 0 }))
    setSearch(search_value)
  }, [])

  return (
    <ContainerList>
      <ContentHeader>
        <TitleH1>__TITULO_PT_BR__</TitleH1>

        <CssButton
          variant="contained"
          startIcon={<MdAddCircle size="18" />}
          onClick={() => history.push('/__modulo__/add')}
        >
          Cadastrar __MODULO_LABEL__
        </CssButton>
      </ContentHeader>

      <ListSurface>
        <ListFilterBar>
          <Formik
            initialValues={EMPTY_FILTER}
            onSubmit={async (values, { setSubmitting }) => {
              setSubmitting(true)
              handleSearch(values)
              setSubmitting(false)
            }}
          >
            {({
              values,
              setFieldValue,
              handleChange,
              handleBlur,
              handleSubmit,
              resetForm,
              isSubmitting,
            }) => (
              <Form onSubmit={handleSubmit}>
                <FilterGrid>
                  {/* __FILTROS__ — um campo por filtro. Exemplo declarado: */}
                  <CssTextField
                    id="input-search-name"
                    label="Nome"
                    placeholder="Buscar"
                    variant="outlined"
                    name="search_name"
                    value={values.search_name}
                    autoComplete="search_name"
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <CssAutocomplete
                    id="select-search-status"
                    options={STATUS_BOOLEAN_OPTIONS}
                    value={
                      STATUS_BOOLEAN_OPTIONS.find(
                        (o: ISelectOption) => o.value === values.search_status,
                      ) ?? null
                    }
                    onChange={(_: unknown, opt: ISelectOption | null) =>
                      setFieldValue('search_status', opt?.value ?? '')
                    }
                    onBlur={handleBlur}
                    renderInput={(params: object) => (
                      <CssTextField
                        {...params}
                        name="search_status"
                        label="Situação"
                        placeholder="Todas"
                      />
                    )}
                  />
                </FilterGrid>

                <FilterActions>
                  {/* Limpar reseta o Formik E recarrega — `type="reset"` só limpava o DOM. */}
                  <CssButton
                    variant="outlined"
                    startIcon={<MdClear size="16" />}
                    onClick={() => {
                      resetForm()
                      handleSearch(EMPTY_FILTER)
                    }}
                  >
                    Limpar filtros
                  </CssButton>
                  <CssButton
                    variant="contained"
                    type="submit"
                    disabled={isSubmitting}
                    startIcon={<MdSearch size="16" />}
                  >
                    {isSubmitting ? 'Pesquisando...' : 'Pesquisar'}
                  </CssButton>
                </FilterActions>
              </Form>
            )}
          </Formik>
        </ListFilterBar>

        <CssDataGrid
          rows={__modulos__}
          columns={columns}
          paginationMode="server"
          rowCount={__modulos__Total}
          pagination
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          // Ordenação também no servidor: ordenar só a página carregada mentiria sobre o conjunto.
          sortingMode="server"
          sortModel={sortModel}
          onSortModelChange={setSortModel}
        />
      </ListSurface>
    </ContainerList>
  )
}

export default __Modulos__List
