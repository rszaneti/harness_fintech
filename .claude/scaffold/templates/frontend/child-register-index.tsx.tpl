// src/pages/__contexto__/__Modulo__Form__Filho__/__Modulo__Form__Filho__Register/index.tsx
//
// Conteúdo do modal do filho: cabeçalho, campos e rodapé (modelo:
// `pages/clinics/ClinicFormContact/ClinicFormContactRegister`). A SUPERFÍCIE (o cartão) é do
// pai — `ModalSurface` na lista. O rodapé fica dentro do <Formik> para submeter sem levantar estado.
// Fechar o modal depois de salvar é o que faz a lista recarregar.

import React, {
  useContext,
  useState,
  useRef,
  useCallback,
  useEffect,
} from 'react'
import { useParams } from 'react-router-dom'
import { Formik, Form, FormikProps } from 'formik'
import { CircularProgress } from '@mui/material'
import * as Yup from 'yup'
import { toast } from 'react-toastify'
import { parseISO, format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { MdClose } from 'react-icons/md'

// Context
import { ErrorContext } from '../../../../context/ErrorContext'
import { use__Modulo__Modal } from '../../../../context/__Modulo__ModalContext'

// Services
import {
  fetch__ModuloFilho__ById,
  create__ModuloFilho__,
  update__ModuloFilho__,
} from '../../../../services/__modulos__.service'

// Types
import { I__ModuloFilho__ } from '../../../../types/__modulos__.types'

// Styles
import {
  FormBody,
  FormCol,
  FormFooter,
  FormRow,
  ModalCloseButton,
  ModalHeader,
  TitleH3,
} from '../../../../styles/global_v2'
import {
  CssButton,
  CssTextField,
} from '../../../../styles/globalMaterialUi_v2'

interface IValuesForm {
  // __CAMPOS_FILHO__ — um por campo do filho. Exemplo declarado:
  name: string
  user_created: string
  user_updated: string
  created_at: string
  updated_at: string
}

interface IParamTypes {
  id: string
}

interface IParamProps {
  __modulo____filho__id: string
}

const schema = Yup.object().shape({
  // __CAMPOS_FILHO__ — validação permissiva (FE-014). Exemplo declarado:
  name: Yup.string().required('Nome é obrigatório.'),
})

const __Modulo__Form__Filho__Register: React.FC<IParamProps> = ({
  __modulo____filho__id,
}) => {
  const { id } = useParams<IParamTypes>()
  const formikRef = useRef<FormikProps<IValuesForm>>(null)

  const { ErrorMessage } = useContext(ErrorContext)
  const { handleClose__Filho__Modal } = use__Modulo__Modal()

  const [__filho__, set__Filho__] = useState<I__ModuloFilho__>(
    {} as I__ModuloFilho__,
  )

  const load__Filho__ = useCallback(async () => {
    try {
      if (__modulo____filho__id) {
        const record = await fetch__ModuloFilho__ById(__modulo____filho__id)
        set__Filho__({
          ...record,
          created_at: record.created_at
            ? format(parseISO(record.created_at), `yyyy-MM-dd'T'HH:mm`, {
                locale: ptBR,
              })
            : '',
          updated_at: record.updated_at
            ? format(parseISO(record.updated_at), `yyyy-MM-dd'T'HH:mm`, {
                locale: ptBR,
              })
            : '',
        })
      }
    } catch (err) {
      ErrorMessage(err)
    }
  }, [ErrorMessage, __modulo____filho__id])

  useEffect(() => {
    load__Filho__()
  }, [load__Filho__])

  const handleSubmitInsert = useCallback(
    async (values: IValuesForm) => {
      try {
        await create__ModuloFilho__({
          __registro_id__: id,
          // __CAMPOS_FILHO__ — payload espelhando o Joi da rota (FE-025). Exemplo:
          name: values.name.trim(),
        })

        toast.success('Registro cadastrado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })

        handleClose__Filho__Modal()
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, id, handleClose__Filho__Modal],
  )

  const handleSubmitUpdate = useCallback(
    async (values: IValuesForm) => {
      try {
        await update__ModuloFilho__({
          __registro_filho_id__: __filho__.id,
          // __CAMPOS_FILHO__ — payload de atualização. Exemplo:
          name: values.name.trim(),
        })

        toast.success('Registro atualizado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })

        handleClose__Filho__Modal()
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, __filho__, handleClose__Filho__Modal],
  )

  const isEdit = !!__modulo____filho__id

  return (
    <Formik
      innerRef={formikRef}
      enableReinitialize={isEdit}
      initialValues={{
        // __CAMPOS_FILHO__ — em edição vem do registro. Exemplo declarado:
        name: isEdit ? (__filho__.name ?? '') : '',
        user_created: isEdit ? (__filho__.user_created ?? '') : '',
        user_updated: isEdit ? (__filho__.user_updated ?? '') : '',
        created_at: isEdit ? (__filho__.created_at ?? '') : '',
        updated_at: isEdit ? (__filho__.updated_at ?? '') : '',
      }}
      validationSchema={() => schema}
      onSubmit={async (values: IValuesForm, { setSubmitting }) => {
        setSubmitting(true)
        if (isEdit) {
          await handleSubmitUpdate(values)
        } else {
          await handleSubmitInsert(values)
        }
        setSubmitting(false)
      }}
    >
      {({
        values,
        errors,
        touched,
        handleChange,
        handleBlur,
        handleSubmit,
        isSubmitting,
      }) => (
        <Form onSubmit={handleSubmit}>
          <ModalHeader>
            <TitleH3>
              {isEdit ? 'Atualizar __FILHO_LABEL__' : 'Cadastrar __FILHO_LABEL__'}
            </TitleH3>
            <ModalCloseButton
              type="button"
              aria-label="Fechar"
              onClick={handleClose__Filho__Modal}
            >
              <MdClose size={18} />
            </ModalCloseButton>
          </ModalHeader>

          <FormBody>
            {/* __CAMPOS_FILHO__ — uma FormRow por linha (12 colunas). Exemplo declarado: */}
            <FormRow>
              <FormCol span={12}>
                <CssTextField
                  id="input-name"
                  name="name"
                  label="Nome"
                  required
                  value={values.name}
                  autoComplete="name"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  helperText={
                    touched.name &&
                    typeof errors.name === 'string' &&
                    errors.name
                  }
                  error={Boolean(errors.name && touched.name)}
                />
              </FormCol>
            </FormRow>

            {/* Auditoria: só existe depois que o registro foi criado. */}
            {isEdit && (
              <FormRow>
                <FormCol span={3}>
                  <CssTextField
                    id="input-user-created"
                    name="user_created"
                    label="Usuário Criação"
                    value={values.user_created}
                    disabled
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </FormCol>
                <FormCol span={3}>
                  <CssTextField
                    id="input-created-at"
                    name="created_at"
                    label="Data Criação"
                    type="datetime-local"
                    value={values.created_at}
                    disabled
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </FormCol>
                <FormCol span={3}>
                  <CssTextField
                    id="input-user-updated"
                    name="user_updated"
                    label="Usuário Alteração"
                    value={values.user_updated}
                    disabled
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </FormCol>
                <FormCol span={3}>
                  <CssTextField
                    id="input-updated-at"
                    name="updated_at"
                    label="Data Alteração"
                    type="datetime-local"
                    value={values.updated_at}
                    disabled
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </FormCol>
              </FormRow>
            )}
          </FormBody>

          <FormFooter>
            <CssButton
              variant="contained"
              type="submit"
              sx={{ marginLeft: 'auto' }}
              disabled={isSubmitting}
              startIcon={
                isSubmitting ? (
                  <CircularProgress size={16} color="inherit" />
                ) : undefined
              }
            >
              {isSubmitting ? 'Salvando' : 'Salvar'}
            </CssButton>
          </FormFooter>
        </Form>
      )}
    </Formik>
  )
}

export default __Modulo__Form__Filho__Register
