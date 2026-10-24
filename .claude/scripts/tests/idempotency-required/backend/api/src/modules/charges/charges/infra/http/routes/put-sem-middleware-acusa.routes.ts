import { Router } from 'express'
import ChargesController from '../controllers/ChargesController'

const chargesRouter = Router()
const chargesController = new ChargesController()

chargesRouter.put('/', chargesController.update) // @acusa

export default chargesRouter
