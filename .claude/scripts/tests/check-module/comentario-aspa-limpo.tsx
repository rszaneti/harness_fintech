// Caso: comentário COM ASPA dentro — o que derrubou o filtro por regex no V-Corp.
// A aspa parava o casamento e o falso positivo passava:
//
//   from '../../styles/global' era o import antigo, antes da migração v2
//   auditDelete não existe neste repositório (BE-023)
//
// Um autômato que rastreia estado de string não se perde nisso; um regex, sim.
import React from 'react'
import { CssTextField } from '../../styles/globalMaterialUi_v2'

const ComentarioAspaLimpo: React.FC = () => <CssTextField name="zz" />

export default ComentarioAspaLimpo
