import { Router } from 'express'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const chargesController = new ChargesController()

chargesRouter.use(ensureIdempotency)

chargesRouter.post('/', chargesController.create)
chargesRouter.patch('/:id/cancel', chargesController.update)

export default chargesRouter
