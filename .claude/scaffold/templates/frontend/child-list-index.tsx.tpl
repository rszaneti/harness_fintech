// src/pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filhos__List/index.tsx
//
// Aba filha: grade + modal (modelo: `pages/clinics/ClinicFormContact/ClinicFormContactsList`).
// A lista recarrega ouvindo `open__Filho__Modal`: fechar o modal depois de salvar é o gatilho.
//
// [FE-024] Sem `slots={{ backdrop: Backdrop }}`: o `Backdrop` cru não tem o `z-index: -1` do slot
// padrão do Modal e o escurecimento pintaria NA FRENTE do cartão. O `CssModalForm` já resolve.
// [FE-020] Se esta grade for parar DENTRO de um `<Form>` (aba Dados), o modal precisa sair para
// fora dele e o `id` sobe para o contexto — ver `ClinicFormSampleEmailModal`.

import React, { useEffect, useState, useCallback, useContext } from 'react'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import { Fade } from '@mui/material'
import { GridActionsCellItem, GridColDef } from '@mui/x-data-grid-pro'
import { MdAddCircle, MdEdit, MdDelete } from 'react-icons/md'

// Context
import { ErrorContext } from '../../../../context/ErrorContext'
import { use__Modulo__Modal } from '../../../../context/__Modulo__ModalContext'

// Services
import {
  fetch__Modulo____Filhos__,
  delete__ModuloFilho__,
} from '../../../../services/__modulos__.service'

// Types
import { I__ModuloFilho__ } from '../../../../types/__modulos__.types'

// Components
import __Modulo__Form__Filho__Register from '../__Modulo__Form__Filho__Register'

// Styles
import {
  ButtonsDiv,
  ContainerSection,
  FormBody,
  ListSurface,
  ModalSurface,
} from '../../../../styles/global_v2'
import {
  CssButton,
  CssDataGrid,
  CssModalForm,
  GridEmptyStateNoRecords,
} from '../../../../styles/globalMaterialUi_v2'

interface IParamTypes {
  id: string
}

const __Modulo__Form__Filhos__List: React.FC = () => {
  const { id } = useParams<IParamTypes>()

  const { ErrorMessage } = useContext(ErrorContext)
  const {
    open__Filho__Modal,
    handleOpen__Filho__Modal,
    handleClose__Filho__Modal,
  } = use__Modulo__Modal()

  const [__filho__Id, set__Filho__Id] = useState('')
  const [__filhos__, set__Filhos__] = useState<I__ModuloFilho__[]>([])

  const load__Filhos__ = useCallback(async () => {
    try {
      if (id) {
        const response = await fetch__Modulo____Filhos__(id)
        set__Filhos__(response.__modulos____filhos__)
      }
    } catch (err) {
      ErrorMessage(err)
    }
  }, [ErrorMessage, id])

  useEffect(() => {
    load__Filhos__()
  }, [load__Filhos__, open__Filho__Modal])

  const handleOpenEditModal = useCallback(
    (rowId: string) => {
      set__Filho__Id(rowId)
      handleOpen__Filho__Modal()
    },
    [handleOpen__Filho__Modal],
  )

  const handleDelete = useCallback(
    async (rowId: string) => {
      const confirmed = window.confirm(
        'Deseja realmente deletar este registro?',
      )
      if (!confirmed) return

      try {
        await delete__ModuloFilho__(rowId)

        toast.success('Registro deletado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })

        load__Filhos__()
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, load__Filhos__],
  )

  const columns: GridColDef[] = [
    {
      field: 'action',
      type: 'actions',
      headerName: 'AÇÕES',
      width: 100,
      cellClassName: 'actions',
      getActions: ({ id: rowId }) => [
        <GridActionsCellItem
          key={`edit-${rowId}`}
          icon={<MdEdit size="18" />}
          title="EDITAR __FILHO_LABEL__"
          label="EDITAR __FILHO_LABEL__"
          showInMenu={false}
          className="action-edit"
          onClick={() => handleOpenEditModal(String(rowId))}
        />,
        <GridActionsCellItem
          key={`delete-${rowId}`}
          icon={<MdDelete size="18" />}
          title="DELETAR __FILHO_LABEL__"
          label="DELETAR __FILHO_LABEL__"
          showInMenu={false}
          className="action-delete"
          onClick={() => handleDelete(String(rowId))}
        />,
      ],
    },
    // __COLUNAS__ — uma por campo do filho. Exemplo declarado:
    {
      field: 'name',
      headerName: 'NOME',
      flex: 1,
      minWidth: 200,
    },
  ]

  return (
    <ContainerSection>
      {/* `FormBody` como corpo da aba: o respiro é o MESMO da aba Dados. */}
      <FormBody>
        <ButtonsDiv margintop="0px" marginbottom="0px" align="left">
          <CssButton
            variant="contained"
            startIcon={<MdAddCircle size="18" />}
            onClick={() => handleOpenEditModal('')}
          >
            Cadastrar __FILHO_LABEL__
          </CssButton>
        </ButtonsDiv>

        {/* A grade não tem borda nem raio próprios: quem os dá é o `ListSurface`. */}
        <ListSurface>
          <CssDataGrid
            rows={__filhos__}
            columns={columns}
            slots={{ noRowsOverlay: GridEmptyStateNoRecords }}
          />
        </ListSurface>
      </FormBody>

      <CssModalForm
        aria-labelledby="transition-modal-__filho__"
        aria-describedby="transition-modal-__filho__-desc"
        open={open__Filho__Modal}
        onClose={handleClose__Filho__Modal}
        closeAfterTransition
        slotProps={{ backdrop: { timeout: 500 } }}
      >
        <Fade in={open__Filho__Modal}>
          <ModalSurface>
            {open__Filho__Modal ? (
              <__Modulo__Form__Filho__Register __modulo____filho__id={__filho__Id} />
            ) : null}
          </ModalSurface>
        </Fade>
      </CssModalForm>
    </ContainerSection>
  )
}

export default __Modulo__Form__Filhos__List
