import { randomBytes } from 'crypto'

// O segredo vem do cofre/env — nunca literal no código, nem em comentário (RN-14).
export default {
  clientSecret: process.env.BTG_CLIENT_SECRET,
  secretName: 'BTG_CLIENT_SECRET_NAME',
  tokenUrl: 'https://api.btgpactual.com/oauth2/token',
  tokenHeader: 'x-idempotency-key-header',
  passwordMinLength: 12,
}

export const testHmacKey = (): string => randomBytes(32).toString('hex')
export const fakeSecret = 's'.repeat(32)
