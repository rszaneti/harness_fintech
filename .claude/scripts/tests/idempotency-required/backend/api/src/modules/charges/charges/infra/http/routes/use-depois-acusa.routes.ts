import { Router } from 'express'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const chargesController = new ChargesController()

chargesRouter.post('/', chargesController.create) // @acusa

// registrado DEPOIS da rota: o Express não aplica a quem já foi registrado
chargesRouter.use(ensureIdempotency)

export default chargesRouter
