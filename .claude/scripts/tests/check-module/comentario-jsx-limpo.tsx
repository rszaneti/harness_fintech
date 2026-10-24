import React from 'react'

/*
 * Caso: padrão proibido em COMENTÁRIO JSX `{/* … *​/}` e em bloco `/* … *​/`.
 * O filtro só-de-linha não cobre nenhum dos dois (AG-018: num .tsx isso dá falso "limpo",
 * e o inverso — acusar o comentário — treina a ignorar o achado).
 */
const ComentarioJsxLimpo: React.FC = () => (
  <div>
    {/* não usar inputProps={{ maxLength: 10 }} — o MUI v7 quer slotProps.htmlInput */}
    {/* nem slots={{ backdrop: Backdrop }} — FE-024 */}
    <input />
  </div>
)

export default ComentarioJsxLimpo
