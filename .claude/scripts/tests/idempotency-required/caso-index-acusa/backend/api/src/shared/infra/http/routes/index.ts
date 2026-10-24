import { Router } from 'express'

const routes = Router()

// `routes/index.ts` está no escopo da RN-13 (BAIXA da 1ª auditoria; caso como diretório porque o
// nome do arquivo é fixo).
routes.post('/health-check', (q: any, s: any) => s.json()) // @acusa

export default routes
