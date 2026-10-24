// Caso: padrão proibido em COMENTÁRIO DE FIM DE LINHA — não pode acusar.
// Filtrar só linha inteira de comentário não basta: foi o segundo modo de falha confirmado
// ao promover a BE-023 ao hook.
import React from 'react'

const ComentarioFimLinhaLimpo: React.FC = () => (
  <input slotProps={{ htmlInput: { maxLength: 10 } }} /> // nunca inputProps={{ … }}
)

export default ComentarioFimLinhaLimpo
