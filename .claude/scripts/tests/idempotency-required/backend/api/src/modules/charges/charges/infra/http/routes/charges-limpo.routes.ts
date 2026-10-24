import { Router } from 'express'
import { celebrate, Joi, Segments } from 'celebrate'

import ensureAuthenticated from '@shared/infra/http/middlewares/ensureAuthenticated'
import ensureIdempotency from '@shared/infra/http/middlewares/ensureIdempotency'
import accessControl from '@shared/infra/http/middlewares/permissions'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const chargesController = new ChargesController()

chargesRouter.use(ensureAuthenticated)

chargesRouter.get(
  '/',
  accessControl(['charges_view']),
  chargesController.index,
)

chargesRouter.post(
  '/',
  accessControl(['charges_create']),
  ensureIdempotency,
  celebrate({
    [Segments.BODY]: Joi.object().keys({
      amount_cents: Joi.number().integer().min(1).required(),
    }),
  }),
  chargesController.create,
)

chargesRouter.put(
  '/',
  accessControl(['charges_update']),
  ensureIdempotency,
  celebrate({
    [Segments.BODY]: Joi.object().keys({
      charges_id: Joi.string().uuid().required(),
    }),
  }),
  chargesController.update,
)

export default chargesRouter
