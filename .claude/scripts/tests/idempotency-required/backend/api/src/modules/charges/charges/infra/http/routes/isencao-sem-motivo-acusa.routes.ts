import { Router } from 'express'
import SessionsController from '../controllers/SessionsController'

const sessionsRouter = Router()
const sessionsController = new SessionsController()

// @acusa-abaixo
// idempotency-exempt:
sessionsRouter.post('/', sessionsController.create)

export default sessionsRouter
