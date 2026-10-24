// Caso: o MESMO padrão dos arquivos "limpo", agora em CÓDIGO — tem de acusar.
// Se este arquivo passar, o filtro de comentário está comendo código.
import React from 'react'
import { CssTextField } from '../../styles/globalMaterialUi_v2'

const CodigoAcusa: React.FC = () => (
  <CssTextField name="zz" inputProps={{ maxLength: 10 }} />
)

export default CodigoAcusa
