import { createHmac, createHash } from 'crypto'

// A forma em DOIS PASSOS da documentação do Node: a variável guarda o Hmac e o `.update(` é dela
// (achado MÉDIA da 1ª auditoria — a 1ª versão só reconhecia a cadeia encadeada).
export default class VerifySignatureTwoStepService {
  public execute(rawBody: string, key: string): string {
    const hmac = createHmac('sha256', key)
    hmac.update(rawBody)
    const digest = createHash('sha256')
    digest.update(rawBody)
    return hmac.digest('hex') + digest.digest('hex')
  }
}
