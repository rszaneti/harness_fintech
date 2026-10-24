import { Router } from 'express'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const ctrl = new ChargesController()

// O middleware NA CHAMADA vale em qualquer forma; e a prosa que só fala do idempotency-exempt
// (sem abrir o comentário com ele) não é marcador.
chargesRouter.route('/').post(ensureIdempotency, ctrl.create)
chargesRouter.post('/z', ensureIdempotency, ctrl.create)

export default chargesRouter
