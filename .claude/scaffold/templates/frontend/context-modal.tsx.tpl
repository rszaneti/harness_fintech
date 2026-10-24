// src/context/__Modulo__ModalContext.tsx
//
// Estado de abertura dos modais das abas filhas de __Modulo__. O `id` do registro em edição fica
// num `useState` LOCAL da lista (há um pai por onde descer). Só sobe para cá quando a grade fica
// dentro do `<Form>` da aba Dados e o modal precisa ficar fora dele (ver
// `ClinicModalContext.sampleEmailId` — o submit do modal atravessa o portal pela árvore do React).

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react'

interface I__Modulo__ModalContext {
  open__Filho__Modal: boolean
  handleOpen__Filho__Modal: () => void
  handleClose__Filho__Modal: () => void
}

const __Modulo__ModalContext = createContext<I__Modulo__ModalContext>(
  {} as I__Modulo__ModalContext,
)

interface Props {
  children: ReactNode
}

const __Modulo__ModalProvider: React.FC<Props> = ({ children }) => {
  const [open__Filho__Modal, setOpen__Filho__Modal] = useState(false)

  const handleOpen__Filho__Modal = useCallback(() => {
    setOpen__Filho__Modal(true)
  }, [])

  const handleClose__Filho__Modal = useCallback(() => {
    setOpen__Filho__Modal(false)
  }, [])

  return (
    <__Modulo__ModalContext.Provider
      value={{
        open__Filho__Modal,
        handleOpen__Filho__Modal,
        handleClose__Filho__Modal,
      }}
    >
      {children}
    </__Modulo__ModalContext.Provider>
  )
}

function use__Modulo__Modal(): I__Modulo__ModalContext {
  const context = useContext(__Modulo__ModalContext)

  if (!context) {
    throw new Error(
      'use__Modulo__Modal must be used within a __Modulo__ModalProvider',
    )
  }

  return context
}

export { __Modulo__ModalProvider, use__Modulo__Modal }
