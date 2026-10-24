// Nome de header e caminho de rota não são segredo, mesmo com dígito (achado BAIXA da 1ª auditoria).
export const HMAC_HEADER = 'x-btg-signature-sha256'
export const resetTokenPath = '/auth/reset-token/v2/confirm'
