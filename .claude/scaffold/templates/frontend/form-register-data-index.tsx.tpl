// src/pages/__contexto__/__Modulo__FormRegisterData/index.tsx
//
// Aba Dados (modelo: `pages/clinics/ClinicFormRegisterData`). Grid de 12 colunas com
// `FormRow`/`FormCol span={n}`; auditoria só em edição; `enableReinitialize` só em edição;
// `innerRef` para quem precisar preencher campos por fora (busca de CEP/CNPJ — ver o canônico).
//
// [FE-025] O payload de create/update espelha o `[Segments.BODY]` da rota — conferir campo a campo.
// [FE-014] Validação Yup erra para o lado PERMISSIVO; quem reprova de verdade é o backend.

import React, {
  useContext,
  useState,
  useRef,
  useCallback,
  useEffect,
} from 'react'
import { useHistory, useParams } from 'react-router-dom'
import { Formik, Form, FormikProps } from 'formik'
import * as Yup from 'yup'
import { toast } from 'react-toastify'
import { parseISO, format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { CircularProgress } from '@mui/material'

// Context
import { ErrorContext } from '../../../context/ErrorContext'

// Services
import {
  fetch__Modulo__ById,
  create__Modulo__,
  update__Modulo__,
} from '../../../services/__modulos__.service'

// Types
import { I__Modulo__ } from '../../../types/__modulos__.types'

// Styles
import {
  FormBody,
  FormCol,
  FormFooter,
  FormRow,
} from '../../../styles/global_v2'
import {
  CssButton,
  CssCheckBox,
  CssFormControlLabel,
  CssTextField,
} from '../../../styles/globalMaterialUi_v2'

interface IValuesForm {
  // __CAMPOS__ — um por campo do formulário. Exemplo declarado:
  name: string
  status: boolean
  user_created: string
  user_updated: string
  created_at: string
  updated_at: string
}

interface IParamTypes {
  register: string
  id: string
}

const schema = Yup.object().shape({
  // __CAMPOS__ — validação Yup, permissiva (FE-014). Exemplo declarado:
  name: Yup.string().required('Nome é obrigatório.'),
})

const __Modulo__FormRegisterData: React.FC = () => {
  const history = useHistory()
  const { register, id } = useParams<IParamTypes>()
  const formikRef = useRef<FormikProps<IValuesForm>>(null)

  const { ErrorMessage } = useContext(ErrorContext)

  const [__modulo__, set__Modulo__] = useState<I__Modulo__>({} as I__Modulo__)
  const [isActive, setIsActive] = useState(true)

  const isEdit = register === 'edit'

  const load__Modulo__ = useCallback(async () => {
    try {
      if (id) {
        const record = await fetch__Modulo__ById(id)
        set__Modulo__({
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
        setIsActive(record.status)
      }
    } catch (err) {
      ErrorMessage(err)
    }
  }, [ErrorMessage, id])

  useEffect(() => {
    load__Modulo__()
  }, [load__Modulo__])

  const handleSubmitInsert = useCallback(
    async (values: IValuesForm) => {
      try {
        const created = await create__Modulo__({
          // __CAMPOS__ — payload de criação, espelhando o Joi da rota (FE-025). Exemplo:
          name: values.name.trim(),
        })

        history.push(`/__modulo__/edit/${created.id}`)

        toast.success('Registro cadastrado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, history],
  )

  const handleSubmitUpdate = useCallback(
    async (values: IValuesForm) => {
      try {
        await update__Modulo__({
          __registro_id__: __modulo__.id,
          // __CAMPOS__ — payload de atualização. Exemplo:
          name: values.name.trim(),
          status: isActive,
        })

        toast.success('Registro atualizado com sucesso.', {
          position: toast.POSITION.TOP_CENTER,
        })
      } catch (err) {
        ErrorMessage(err)
      }
    },
    [ErrorMessage, __modulo__, isActive],
  )

  return (
    <Formik
      innerRef={formikRef}
      enableReinitialize={isEdit}
      initialValues={{
        // __CAMPOS__ — um por campo; em edição vem do registro. Exemplo declarado:
        name: isEdit ? (__modulo__.name ?? '') : '',
        status: isEdit ? (__modulo__.status ?? true) : true,
        user_created: isEdit ? (__modulo__.user_created ?? '') : '',
        user_updated: isEdit ? (__modulo__.user_updated ?? '') : '',
        created_at: isEdit ? (__modulo__.created_at ?? '') : '',
        updated_at: isEdit ? (__modulo__.updated_at ?? '') : '',
      }}
      validationSchema={() => schema}
      onSubmit={async (values: IValuesForm, { setSubmitting }) => {
        setSubmitting(true)

        if (isEdit) {
          const decision = window.confirm(
            'Tem certeza que deseja atualizar o cadastro?',
          )
          if (!decision) {
            setSubmitting(false)
            return
          }
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
          <FormBody>
            {/* __CAMPOS__ — uma FormRow por linha do layout (12 colunas). Exemplo declarado: */}
            <FormRow>
              <FormCol span={9}>
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
              {isEdit && (
                <FormCol span={3} alignself="end">
                  <CssFormControlLabel
                    control={
                      <CssCheckBox
                        checked={isActive}
                        onChange={(e) => setIsActive(e.target.checked)}
                        name="status"
                      />
                    }
                    label="Ativo"
                  />
                </FormCol>
              )}
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

export default __Modulo__FormRegisterData
