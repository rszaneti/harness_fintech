// src/pages/__contexto__/__Modulo__Form/index.tsx
//
// Página do formulário com abas (modelo: `pages/clinics/ClinicForm`). Sem caixa nem padding
// próprios: o respiro de cada aba é do conteúdo dela (`FormBody` na aba Dados,
// `ContainerSection` nas demais). Aba filha só habilita em edição — o registro precisa existir.

import React, { useState, useCallback, ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { MdNavigateBefore } from 'react-icons/md'
// @if filho

// Context
import { __Modulo__ModalProvider } from '../../../context/__Modulo__ModalContext'
// @endif

// Styles
import {
  ContainerForm,
  ContentHeader,
  FormSurface,
  FormTabsBar,
  TitleH1,
} from '../../../styles/global_v2'
import { CssButton, CssTab, CssTabs } from '../../../styles/globalMaterialUi_v2'

// Components
import __Modulo__FormRegisterData from '../__Modulo__FormRegisterData'
// @if filho
import __Modulo__Form__Filhos__List from '../__Modulo__Form__Filho__/__Modulo__Form__Filhos__List'
// @endif

interface ITabPanelProps {
  children: ReactNode
  index: number
  value: number
}

interface IParamTypes {
  register: string
  id: string
}

function TabPanel(props: ITabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`scrollable-auto-tabpanel-${index}`}
      aria-labelledby={`scrollable-auto-tab-${index}`}
      {...other}
    >
      {value === index && children}
    </div>
  )
}

function a11yProps(index: number) {
  return {
    id: `scrollable-auto-tab-${index}`,
    'aria-controls': `scrollable-auto-tabpanel-${index}`,
  }
}

const __Modulo__Form: React.FC = () => {
  const { register } = useParams<IParamTypes>()

  const [value, setValue] = useState(0)

  const isEdit = register === 'edit'

  const handleChange = useCallback(
    (_event: React.ChangeEvent<any>, newValue: number) => {
      setValue(newValue)
    },
    [],
  )

  const page = (
    <ContainerForm>
      {/* "Voltar" é ação DA PÁGINA, não da aba: vale em todas. */}
      <ContentHeader>
        <TitleH1>
          {isEdit ? 'Atualizar __MODULO_LABEL__' : 'Cadastrar __MODULO_LABEL__'}
        </TitleH1>
        {/* O Link envolve o botão: `styled()` apaga a tipagem polimórfica do Button. */}
        <Link to="/__modulos__">
          <CssButton
            variant="outlined"
            startIcon={<MdNavigateBefore size={20} />}
          >
            Voltar
          </CssButton>
        </Link>
      </ContentHeader>

      <FormSurface>
        <FormTabsBar>
          <CssTabs
            value={value}
            onChange={handleChange}
            variant="scrollable"
            scrollButtons="auto"
            aria-label="Abas do cadastro"
          >
            <CssTab label="Dados" {...a11yProps(0)} />
            // @if filho
            <CssTab
              label="__FILHO_LABEL__"
              disabled={!isEdit}
              {...a11yProps(1)}
            />
            // @endif
          </CssTabs>
        </FormTabsBar>

        <TabPanel value={value} index={0}>
          <__Modulo__FormRegisterData />
        </TabPanel>
        // @if filho
        <TabPanel value={value} index={1}>
          <__Modulo__Form__Filhos__List />
        </TabPanel>
        // @endif
      </FormSurface>
    </ContainerForm>
  )
  // @if filho

  return <__Modulo__ModalProvider>{page}</__Modulo__ModalProvider>
  // @endif
  // @if !filho

  return page
  // @endif
}

export default __Modulo__Form
