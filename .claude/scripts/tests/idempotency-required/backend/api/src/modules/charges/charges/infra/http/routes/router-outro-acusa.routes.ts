import { Router } from 'express'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'

const adminRouter = Router()
const chargesRouter = Router()

// O `.use` de OUTRO router não protege este (achado BAIXA da 1ª auditoria).
adminRouter.use(ensureIdempotency)

chargesRouter.post('/', (q: any, s: any) => s.json()) // @acusa

export { adminRouter, chargesRouter }
