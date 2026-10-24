import { Router } from 'express'
import PixController from '../controllers/PixController'

// O simulador imita o BTG e não move dinheiro: fora do escopo da RN-13.
const pixRouter = Router()
const pixController = new PixController()

pixRouter.post('/cob', pixController.create)

export default pixRouter
