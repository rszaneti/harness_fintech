import { Router } from 'express'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const ctrl = new ChargesController()

// Formas do Express sem identificador antes do ponto — a reauditoria pegou o detector cego para
// elas. E o `.use` do MESMO router não isenta quem não tem receptor simples.
chargesRouter.use(ensureIdempotency)
chargesRouter.route('/').post(ctrl.create) // @acusa
chargesRouter
  .route('/x')
  .put(ctrl.update) // @acusa
chargesRouter.get('/', ctrl.index).patch('/y', ctrl.update) // @acusa

export default chargesRouter
