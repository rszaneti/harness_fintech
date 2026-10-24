import { Router } from 'express'

const sessionsRouter = Router()

// idempotency-exempt login deduplicado pela sessão, sem os dois-pontos @acusa
sessionsRouter.post('/', (q: any, s: any) => s.json()) // @acusa

export default sessionsRouter
