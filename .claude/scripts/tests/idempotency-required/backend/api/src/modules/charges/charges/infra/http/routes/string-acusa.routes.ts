import { Router } from 'express'

const chargesRouter = Router()

// A STRING 'ensureIdempotency' não é o middleware (achado BAIXA da 1ª auditoria).
chargesRouter.post('/', 'ensureIdempotency' as any, (q: any, s: any) => s.json()) // @acusa

export default chargesRouter
