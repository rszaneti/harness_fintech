// Caso: import do padrão visual v1 e placeholder de identidade vazado, ambos em CÓDIGO.
// Os dois têm de acusar: o v1 porque tela nova é v2 (spec 086), o placeholder porque passa
// em lint e typecheck sem erro nenhum (spec 085).
import React from 'react'
import { CssTextField } from '../../styles/globalMaterialUi'

const CodigoV1EPlaceholderAcusa: React.FC = () => (
  <CssTextField name="__Modulo__" label="zz" />
)

export default CodigoV1EPlaceholderAcusa
