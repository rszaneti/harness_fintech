import { Router } from 'express'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const chargesController = new ChargesController()

// Nunca: chargesRouter.post('/', chargesController.create) sem ensureIdempotency.
/* Nem: chargesRouter.patch('/:id', chargesController.update) */
chargesRouter.get('/', chargesController.index)

export default chargesRouter
