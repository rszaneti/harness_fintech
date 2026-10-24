// Caso: padrão proibido em COMENTÁRIO DE LINHA INTEIRA — não pode acusar.
// O comentário que ADVERTE contra a regra não pode ser reprovado por exibi-la (AG-013).
//
// inputProps={{ maxLength: 10 }}   ← proibido no MUI v7, usar slotProps.htmlInput
// slots={{ backdrop: Backdrop }}   ← FE-024
// __CAMPOS__                        ← marcador em comentário é o estado normal do gerado
import React from 'react'

const ComentarioLinhaLimpo: React.FC = () => <input />

export default ComentarioLinhaLimpo
