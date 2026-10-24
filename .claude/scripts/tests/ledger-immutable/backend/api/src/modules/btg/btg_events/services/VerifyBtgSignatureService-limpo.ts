import { createHmac, timingSafeEqual } from 'crypto'

// A verificação de assinatura mora no módulo append-only dos eventos — e o `.update(` do crypto
// não é escrita em banco (idioma real: a cadeia em várias linhas).
export default class VerifyBtgSignatureService {
  public execute(rawBody: string, signature: string, key: string): boolean {
    const expected = createHmac('sha256', key)
      .update(rawBody)
      .digest('hex')
    const inline = createHmac('sha256', key).update(rawBody).digest('hex')
    return timingSafeEqual(Buffer.from(expected), Buffer.from(signature)) && inline === expected
  }
}
