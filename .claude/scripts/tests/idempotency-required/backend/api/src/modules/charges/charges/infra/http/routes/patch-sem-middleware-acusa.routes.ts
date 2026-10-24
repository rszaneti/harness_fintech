import { Router } from 'express'
import { celebrate, Joi, Segments } from 'celebrate'
import accessControl from '@shared/infra/http/middlewares/permissions'
import PayoutsApproveController from '../controllers/PayoutsApproveController'

const payoutsRouter = Router()
const approveController = new PayoutsApproveController()

payoutsRouter.patch( // @acusa
  '/:id/approve',
  accessControl(['payouts_update']),
  celebrate({
    [Segments.PARAMS]: { id: Joi.string().uuid().required() },
  }),
  approveController.update,
)

export default payoutsRouter
